import json
import os
import logging
import requests
from datetime import datetime
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from core_logic import get_latest_post_by_tag, extract_and_summarize_article, traducir
from database import DatabaseAdapter

# Configuración de Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar DB
db = DatabaseAdapter()

# -------- UTILIDADES --------
def verify_signature(event):
    """Verifica la firma criptográfica de Discord."""
    public_key = os.environ.get('DISCORD_PUBLIC_KEY')
    if not public_key:
        logger.error("DISCORD_PUBLIC_KEY no configurada")
        return False

    verify_key = VerifyKey(bytes.fromhex(public_key))
    
    # Normalizar headers a minúsculas (API Gateway V2 puede enviar headers en formato mixto)
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    
    signature = headers.get('x-signature-ed25519')
    timestamp = headers.get('x-signature-timestamp')
    body = event.get('body')

    if not signature or not timestamp or not body:
        logger.error(f"Missing required headers or body. Signature: {bool(signature)}, Timestamp: {bool(timestamp)}, Body: {bool(body)}")
        return False

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        logger.info("✅ Firma verificada correctamente")
        return True
    except BadSignatureError as e:
        logger.error(f"❌ Firma inválida: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando firma: {e}")
        return False

def send_discord_message(channel_id, content):
    """Envía mensaje a Discord vía REST API."""
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN no configurado")
        return

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {"content": content}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a canal {channel_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a {channel_id}: {e}")

# -------- HANDLER 1: INTERACTIONS (WEBHOOKS) --------
def lambda_handler_interactions(event, context):
    """Maneja comandos Slash de Discord."""
    logger.info(f"Evento recibido: {json.dumps(event)}")
    
    # 0. Verificar si es invocación asíncrona (Worker)
    if event.get('type') == 'async_worker':
        logger.info("👷 Worker asíncrono iniciado")
        return handle_async_worker(event)

    # 1. Verificar firma
    if not verify_signature(event):
        logger.error("❌ Verificación de firma falló")
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'invalid request signature'})
        }

    # 2. Parsear body
    body = json.loads(event['body'])
    t = body.get('type')
    logger.info(f"Tipo de interacción: {t}")

    # 3. Manejar PING (Type 1)
    if t == 1:
        logger.info("📍 PING recibido, respondiendo...")
        response = {'type': 1}
        logger.info(f"Respuesta PING: {response}")
        return response

    # 3. Manejar MESSAGE_COMPONENT (Type 3 - Botones)
    if t == 3:
        logger.info("🔘 Botón presionado, procesando...")
        return handle_button_click(body, context)

    # 4. Manejar COMANDOS (Type 2)
    if t == 2:
        logger.info("⚡ Comando recibido, procesando...")
        response = handle_command(body, context)
        logger.info(f"Respuesta comando: {json.dumps(response)}")
        return response

    logger.warning(f"⚠️ Tipo de interacción desconocido: {t}")
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'unknown interaction type'})
    }

def handle_button_click(interaction, context):
    """Maneja clics en botones de traducción."""
    data = interaction.get('data', {})
    custom_id = data.get('custom_id', '')
    
    if not custom_id.startswith('translate_'):
        return {
            'type': 4,
            'data': {'content': "❌ Botón no reconocido", 'flags': 64}
        }
    
    # Extraer idioma e ID del mensaje
    parts = custom_id.split('_')
    if len(parts) < 3:
        return {
            'type': 4,
            'data': {'content': "❌ ID inválido", 'flags': 64}
        }
    
    lang = parts[1]  # es, pt, zh
    message_id = '_'.join(parts[2:])
    
    # Mapeo de idiomas
    lang_map = {
        'es': ('es', '🇪🇸 Español'),
        'pt': ('pt', '🇵🇹 Português'),
        'zh': ('zh-cn', '🇨🇳 中文')
    }
    
    if lang not in lang_map:
        return {
            'type': 4,
            'data': {'content': "❌ Idioma no soportado", 'flags': 64}
        }
    
    try:
        from core_logic import traducir
        from googletrans import Translator
        import boto3
        
        # Obtener contenido cacheado
        cached = db.get_cached_translation(message_id)
        if not cached:
            return {
                'type': 4,
                'data': {'content': "❌ Traducción expirada. Ejecuta el comando nuevamente.", 'flags': 64}
            }
        
        original_content = cached.get('original')
        translations = cached.get('translations', {})
        metadata = cached.get('metadata', {})
        
        # Si ya tenemos la traducción, responder rápido
        if lang in translations:
            translated = translations[lang]
            
            # Reconstruir mensaje con link si existe
            content = f"**Traducción {lang_map[lang][1]}:**\n{translated}"
            if metadata and 'link' in metadata:
                content += f"\n\n🔗 {metadata['link']}"
                
            return {
                'type': 7,  # UPDATE_MESSAGE
                'data': {
                    'content': content,
                    'components': []  # Remover botones
                }
            }
        
        # Si NO tenemos la traducción, usar Worker Asíncrono
        # 1. Invocar lambda async
        lambda_client = boto3.client('lambda')
        function_name = context.function_name
        
        payload = {
            'type': 'async_worker',
            'action': 'translate',
            'lang': lang,
            'message_id': message_id,
            'application_id': interaction.get('application_id'),
            'token': interaction.get('token'),
            'original_content': original_content
        }
        
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        
        # 2. Responder con DEFERRED_UPDATE_MESSAGE (type 6)
        return {
            'type': 6  # DEFERRED_UPDATE_MESSAGE
        }
        
    except Exception as e:
        logger.error(f"Error traduciendo: {e}", exc_info=True)
        return {
            'type': 4,
            'data': {'content': "❌ Error al procesar botón", 'flags': 64}
        }

def handle_command(interaction, context):
    """Procesa comandos slash."""
    data = interaction.get('data', {})
    command_name = data.get('name')
    guild_id = interaction.get('guild_id')
    
    if command_name == 'usar':
        # Configurar canal
        options = data.get('options', [])
        channel_id = options[0]['value']
        
        db.set_channel(guild_id, channel_id)
        
        return {
            'type': 4,
            'data': {
                'content': f"✅ Canal configurado: <#{channel_id}>. Las noticias saldrán ahí.",
                'flags': 64
            }
        }

    elif command_name in ['verificar-parche', 'verificar-evento', 'verificar-noticia']:
        # Mapeo de comandos a tags
        tag_map = {
            'verificar-parche': 'patch note',
            'verificar-evento': 'event',
            'verificar-noticia': 'notice'
        }
        tag = tag_map.get(command_name)
        
        # NO procesamos aquí para evitar timeout de 3 segundos
        # Invocamos asíncronamente a la misma Lambda para procesar
        import boto3
        
        lambda_client = boto3.client('lambda')
        function_name = context.function_name
        
        payload = {
            'type': 'async_worker',
            'command': command_name,
            'tag': tag,
            'application_id': interaction.get('application_id'),
            'token': interaction.get('token'),
            'interaction_id': interaction.get('id')
        }
        
        try:
            lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='Event',  # Asíncrono
                Payload=json.dumps(payload)
            )
            logger.info(f"🚀 Invocación asíncrona enviada para {command_name}")
        except Exception as e:
            logger.error(f"❌ Error invocando lambda async: {e}")
        
        # Responder type 5 inmediatamente
        return {
            'type': 5,
            'data': {'flags': 64}
        }

    elif command_name == 'estado-bot':
        import datetime
        config = db.get_config()
        canal_id = config.get(str(guild_id))
        
        estado = f"🐉 **Bicheon4ever Serverless**\n"
        estado += f"💬 Canal configurado: <#{canal_id}>\n" if canal_id else "❌ Sin canal configurado\n"
        
        estado += "\n**Últimas actualizaciones automáticas:**\n"
        tags = {'patch note': 'Parche', 'event': 'Evento', 'notice': 'Noticia'}
        
        for tag_key, tag_label in tags.items():
            info = db.get_last_post_info(tag_key)
            if info and info.get('updated_at'):
                # Formatear fecha (ISO a legible)
                try:
                    dt = datetime.datetime.fromisoformat(info['updated_at'])
                    fecha_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    estado += f"• **{tag_label}:** {fecha_str}\n"
                except:
                    estado += f"• **{tag_label}:** {info['updated_at']}\n"
            else:
                estado += f"• **{tag_label}:** Sin registros recientes\n"
        
        return {
            'type': 4,
            'data': {'content': estado, 'flags': 64}
        }

    return {
        'type': 4,
        'data': {'content': "Comando no reconocido"}
    }


# -------- HANDLER 2: SCRAPER (SCHEDULED) --------
def lambda_handler_scraper(event, context):
    """Ejecuta el scraping periódico."""
    logger.info("Iniciando Scraper Job")
    
    tags = ['patch note', 'notice', 'event']
    config = db.get_config()
    
    if not config:
        logger.warning("No hay canales configurados. Saltando scraping.")
        return {'statusCode': 200, 'body': 'No channels configured'}
    
    for tag in tags:
        try:
            from core_logic import format_as_bullets
            import hashlib
            
            # 1. Buscar último post
            post = get_latest_post_by_tag(tag)
            if not post:
                continue
                
            titulo, link = post
            
            # 2. Verificar si ya lo vimos
            last_link = db.get_last_post(tag)
            if last_link == link:
                logger.info(f"Sin novedades para {tag}")
                continue
                
            # 3. Es nuevo! Procesar
            logger.info(f"Nuevo post encontrado: {titulo}")
            resumen_texto = extract_and_summarize_article(link)
            resumen_bullets = format_as_bullets(resumen_texto)
            
            # Crear ID único para este mensaje basado en link
            message_id = hashlib.md5(link.encode()).hexdigest()
            
            # Formatear contenido
            content = f"🐉 **Nuevo {tag.title()} Detectado**\n**{titulo}**\n\n**Resumen:**\n{resumen_bullets}\n\n🔗 {link}"
            
            # Crear botones de traducción (mismo formato que comandos)
            components = [{
                "type": 1,
                "components": [
                    {"type": 2, "style": 1, "label": "🇪🇸 Español", "custom_id": f"translate_es_{message_id}"},
                    {"type": 2, "style": 1, "label": "🇵🇹 Português", "custom_id": f"translate_pt_{message_id}"},
                    {"type": 2, "style": 1, "label": "🇨🇳 中文", "custom_id": f"translate_zh_{message_id}"}
                ]
            }]
            
            # Cachear para traducciones
            db.cache_translation(message_id, resumen_bullets, {})
            
            # 4. Enviar a todos los canales
            for guild_id, channel_id in config.items():
                send_discord_message_with_components(channel_id, content, components)
                
            # 5. Actualizar estado
            db.set_last_post(tag, link)
            
        except Exception as e:
            logger.error(f"Error procesando tag {tag}: {e}", exc_info=True)
            
    return {'statusCode': 200, 'body': 'Scraper completed'}

def send_discord_message_with_components(channel_id, content, components):
    """Envía mensaje con botones a Discord."""
    import os
    import requests

    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN no configurado")
        return

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "content": content,
        "components": components
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje con botones enviado a canal {channel_id}")
    except Exception as e:
        logger.error(f"Error enviando mensaje a {channel_id}: {e}")

def handle_async_worker(payload):
    """Procesa tareas pesadas en segundo plano."""
    try:
        from core_logic import format_as_bullets
        import requests
        
        action = payload.get('action')
        
        # --- CASO 1: TRADUCCIÓN (Botones) ---
        if action == 'translate':
            lang = payload.get('lang')
            message_id = payload.get('message_id')
            app_id = payload.get('application_id')
            token = payload.get('token')
            original_content = payload.get('original_content')
            
            logger.info(f"👷 Worker: Traduciendo a {lang}")
            
            lang_map = {
                'es': ('es', '🇪🇸 Español'),
                'pt': ('pt', '🇵🇹 Português'),
                'zh': ('zh-cn', '🇨🇳 中文')
            }
            
            from googletrans import Translator
            translator = Translator()
            dest_lang, lang_name = lang_map[lang]
            
            # Traducir
            translated = translator.translate(original_content, dest=dest_lang).text
            
            # Actualizar cache
            # Nota: Esto es una condición de carrera potencial si múltiples traducciones ocurren a la vez,
            # pero para este caso de uso es aceptable.
            cached = db.get_cached_translation(message_id)
            if cached:
                translations = cached.get('translations', {})
                metadata = cached.get('metadata', {})
                translations[lang] = translated
                db.cache_translation(message_id, original_content, translations, metadata=metadata)
            
            # Editar mensaje original vía webhook
            header = f"**Traducción {lang_name}:**\n"
            max_len = 2000 - len(header)
            
            # Si hay link, reservamos espacio
            cached = db.get_cached_translation(message_id)
            metadata = cached.get('metadata', {}) if cached else {}
            link_suffix = ""
            if metadata and 'link' in metadata:
                link_suffix = f"\n\n🔗 {metadata['link']}"
                max_len -= len(link_suffix)
            
            if len(translated) > max_len:
                translated = translated[:max_len-3] + "..."
                
            content = header + translated + link_suffix
            webhook_url = f"https://discord.com/api/v10/webhooks/{app_id}/{token}/messages/@original"
            
            resp = requests.patch(webhook_url, json={"content": content, "components": []}, timeout=10)
            resp.raise_for_status()
            logger.info("✅ Traducción enviada exitosamente")
            return {'statusCode': 200, 'body': 'Translation success'}

        # --- CASO 2: COMANDOS (Verificación) ---
        else:
            command_name = payload.get('command')
            tag = payload.get('tag')
            app_id = payload.get('application_id')
            token = payload.get('token')
            interaction_id = payload.get('interaction_id')
            
            logger.info(f"👷 Procesando {command_name} para {tag}")
            
            post = get_latest_post_by_tag(tag)
            if not post:
                content = f"❌ No se encontró ningún {tag}."
                components = []
            else:
                titulo, link = post
                resumen_texto = extract_and_summarize_article(link)
                resumen_bullets = format_as_bullets(resumen_texto)
                content = f"🐉 **{tag.title()}**\n**{titulo}**\n\n**Resumen:**\n{resumen_bullets}\n\n🔗 {link}"
                
                components = [{
                    "type": 1,
                    "components": [
                        {"type": 2, "style": 1, "label": "🇪🇸 Español", "custom_id": f"translate_es_{interaction_id}"},
                        {"type": 2, "style": 1, "label": "🇵🇹 Português", "custom_id": f"translate_pt_{interaction_id}"},
                        {"type": 2, "style": 1, "label": "🇨🇳 中文", "custom_id": f"translate_zh_{interaction_id}"}
                    ]
                }]
                
                db.cache_translation(interaction_id, resumen_bullets, {}, metadata={'title': titulo, 'link': link})
            
            # Editar mensaje vía webhook
            webhook_url = f"https://discord.com/api/v10/webhooks/{app_id}/{token}/messages/@original"
            resp = requests.patch(webhook_url, json={"content": content, "components": components}, timeout=10)
            resp.raise_for_status()
            logger.info(f"✅ Mensaje actualizado exitosamente para {command_name}")
            return {'statusCode': 200, 'body': 'Worker success'}
        
    except Exception as e:
        logger.error(f"❌ Error en worker: {e}", exc_info=True)
        # Intentar enviar error
        try:
            webhook_url = f"https://discord.com/api/v10/webhooks/{payload.get('application_id')}/{payload.get('token')}/messages/@original"
            requests.patch(webhook_url, json={"content": "❌ Error procesando solicitud."}, timeout=10)
        except:
            pass
        return {'statusCode': 500, 'body': str(e)}
