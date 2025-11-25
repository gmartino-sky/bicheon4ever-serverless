import boto3
import os
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('BicheonDB')
logger.setLevel(logging.INFO)

class DatabaseAdapter:
    def __init__(self):
        # Si estamos en local (sin AWS), usamos mocks o archivos? 
        # Por ahora asumimos que si hay variables de entorno, usamos DynamoDB.
        self.table_config_name = os.environ.get('TABLE_CONFIG', 'BicheonConfig')
        self.table_state_name = os.environ.get('TABLE_STATE', 'BicheonState')
        
        # Inicializar cliente DynamoDB
        # Si estamos corriendo localmente con SAM, esto se conecta a Docker si se configura,
        # o a AWS real si hay credenciales.
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.table_config = self.dynamodb.Table(self.table_config_name)
            self.table_state = self.dynamodb.Table(self.table_state_name)
        except Exception as e:
            logger.warning(f"No se pudo conectar a DynamoDB: {e}. Modo offline/local limitado.")
            self.dynamodb = None

    def get_config(self):
        """Obtiene la configuración de canales (guild_id -> channel_id)."""
        if not self.dynamodb:
            return {}
            
        try:
            # Scan es costoso, pero para pocos servers (<100) está bien.
            response = self.table_config.scan()
            items = response.get('Items', [])
            config = {}
            for item in items:
                config[item['guild_id']] = int(item['channel_id'])
            return config
        except Exception as e:
            logger.error(f"Error leyendo config de DynamoDB: {e}")
            return {}

    def set_channel(self, guild_id, channel_id):
        """Guarda el canal para un servidor."""
        if not self.dynamodb:
            return
            
        try:
            self.table_config.put_item(
                Item={
                    'guild_id': str(guild_id),
                    'channel_id': int(channel_id),
                    'updated_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error guardando config en DynamoDB: {e}")

    def get_last_post_info(self, tag):
        """Obtiene información completa del último post (link y fecha)."""
        if not self.dynamodb:
            return None
            
        try:
            response = self.table_state.get_item(Key={'key': f"last_post_{tag}"})
            item = response.get('Item')
            if item:
                return {
                    'link': item.get('value'),
                    'updated_at': item.get('updated_at')
                }
            return None
        except Exception as e:
            logger.error(f"Error leyendo estado de DynamoDB: {e}")
            return None

    def get_last_post(self, tag):
        """Obtiene el link del último post visto para un tag."""
        info = self.get_last_post_info(tag)
        return info['link'] if info else None

    def set_last_post(self, tag, link):
        """Actualiza el último post visto."""
        if not self.dynamodb:
            return
            
        try:
            self.table_state.put_item(
                Item={
                    'key': f"last_post_{tag}",
                    'value': link,
                    'updated_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error guardando estado en DynamoDB: {e}")
    
    def cache_translation(self, message_id, original_content, translations, metadata=None):
        """Guarda traducciones en cache con TTL de 1 hora."""
        if not self.dynamodb:
            return
        
        try:
            ttl = int((datetime.now() + timedelta(hours=1)).timestamp())
            item = {
                'key': f"cache_{message_id}",
                'original_content': original_content,
                'translations': translations,
                'ttl': ttl
            }
            if metadata:
                item['metadata'] = metadata
                
            self.table_state.put_item(Item=item)
        except Exception as e:
            logger.error(f"Error guardando cache: {e}")
    
    def get_cached_translation(self, message_id):
        """Obtiene traducciones cacheadas."""
        if not self.dynamodb:
            return None
        
        try:
            response = self.table_state.get_item(Key={'key': f"cache_{message_id}"})
            item = response.get('Item')
            if item:
                return {
                    'original': item.get('original_content'),
                    'translations': item.get('translations', {}),
                    'metadata': item.get('metadata', {})
                }
            return None
        except Exception as e:
            logger.error(f"Error leyendo cache: {e}")
            return None
