import requests
from bs4 import BeautifulSoup
from newspaper import Article
from googletrans import Translator
import logging

# Configuración de logging
logger = logging.getLogger('BicheonCore')
logger.setLevel(logging.INFO)

translator = Translator()

def get_latest_post_by_tag(tag_buscado):
    """Obtiene el último post del foro MIR4 para un tag específico."""
    url_map = {
        'patch note': "https://forum.mir4global.com/board/patchnote",
        'notice': "https://forum.mir4global.com/board/notice",
        'event': "https://forum.mir4global.com/board/newevent?category_id=1"
    }
    
    url = url_map.get(tag_buscado)
    if not url:
        logger.error(f"❌ Tag inválido: {tag_buscado}")
        return None
    
    try:
        logger.debug(f"📡 Scrapeando {url} para tag '{tag_buscado}'")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = soup.select('article.article')
        
        if not posts:
            logger.warning(f"⚠️ No se encontraron posts en {url}")
            return None

        for post in posts:
            tag = post.select_one('em.article_category')
            if not tag:
                continue

            tag_text = tag.text.strip().lower()
            if tag_text != tag_buscado:
                continue

            # Filtrar posts de redes sociales
            title = post.get_text(strip=True).lower()
            if any(s in title for s in ['facebook', 'instagram', 'youtube']):
                continue

            href = post.find('a')['href']
            if not href.startswith('http'):
                href = f"https://forum.mir4global.com{href}"

            full_title = post.find('span', class_='subject').text.strip()
            return full_title, href

        return None
        
    except Exception as e:
        logger.error(f"❌ Error en scraping de '{tag_buscado}': {e}")
        return None

def extract_and_summarize_article(url):
    """Extrae y resume el contenido de un artículo del foro MIR4."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_selectors = [
            'div.article_content', 'div.article-content', 
            'div.board_content', 'div.post_content', 'article.article'
        ]
        
        content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content: break
        
        if not content:
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True)
                if len(text) > 200:
                    content = div
                    break
        
        if content:
            for unwanted in content(['script', 'style', 'meta', 'link']):
                unwanted.decompose()
            
            # Usar doble salto de línea para separar bloques (párrafos)
            text = content.get_text(separator='\n\n', strip=True)
            
            # Limpiar líneas vacías pero preservar la estructura de párrafos
            lines = [line.strip() for line in text.split('\n\n') if line.strip()]
            
            # Filtrar boilerplate común
            boilerplate_phrases = [
                "from my battle to our war",
                "greetings, this is mir4",
                "thank you",
                "please refer to the details below",
                "we look forward to",
                "go to"
            ]
            
            cleaned_lines = []
            for line in lines:
                lower_line = line.lower()
                if any(phrase in lower_line for phrase in boilerplate_phrases):
                    continue
                cleaned_lines.append(line)
                
            text = '\n\n'.join(cleaned_lines)
            
            if text and len(text) > 50:
                # Lógica mejorada de resumen (1800 chars)
                paragraphs = text.split('\n\n')
                summary_parts = []
                total_length = 0
                max_length = 1800
                
                for para in paragraphs:
                    if len(para) > max_length:
                        if total_length == 0:
                            summary_parts.append(para[:max_length] + "...")
                        break
                    
                    if total_length + len(para) > max_length:
                        break
                        
                    summary_parts.append(para)
                    total_length += len(para) + 2
                
                if summary_parts:
                    return '\n\n'.join(summary_parts)
                else:
                    return text[:max_length] + ("..." if len(text) > max_length else "")
        
        # Fallback newspaper3k
        try:
            article = Article(url)
            article.download()
            article.parse()
            if article.text:
                return article.text[:1800] + "..."
        except:
            pass
            
        return "No se pudo extraer el contenido."
        
    except Exception as e:
        logger.error(f"Error extrayendo artículo: {e}")
        return "Error al procesar el artículo."

def format_as_bullets(text):
    """Formatea el texto como bullets interpretados."""
    if not text or len(text) < 50:
        return text
    
    # Dividir en párrafos iniciales
    raw_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    # Si no hay suficientes dobles saltos, intentar dividir por saltos simples
    if len(raw_paragraphs) < 3:
        raw_paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    # Lógica de fusión inteligente
    paragraphs = []
    current_para = ""
    
    for line in raw_paragraphs:
        if not current_para:
            current_para = line
            continue
            
        # Decisiones de fusión
        should_merge = False
        
        # 1. Si la línea anterior termina en conectores o indicadores de rango
        if current_para.endswith(('~', '-', ':', ',')):
            should_merge = True
        # 2. Si la línea actual empieza con minúscula (continuación probable)
        elif line[0].islower():
            should_merge = True
        # 3. Si la línea anterior no termina en puntuación fuerte
        elif not current_para.endswith(('.', '!', '?')):
            # EXCEPCIÓN: Si termina en "am" o "pm" (horarios), NO unir
            if current_para.lower().endswith((' am', ' pm')):
                should_merge = False
            # EXCEPCIÓN: Si la nueva línea empieza con una Región conocida, NO unir
            elif line.split('(')[0].strip() in ['ASIA', 'INMENA', 'EU', 'SA', 'NA']:
                should_merge = False
            else:
                should_merge = True
            
        if should_merge:
            current_para += " " + line
        else:
            paragraphs.append(current_para)
            current_para = line
            
    if current_para:
        paragraphs.append(current_para)
    
    # Tomar más puntos clave (hasta 15) y permitir más texto (hasta 1800 chars total)
    bullets = []
    current_length = 0
    max_total_length = 1800
    
    for para in paragraphs[:15]:
        # Limpiar espacios extra
        para = para.strip()
        if not para: continue
        
        # Calcular longitud si añadimos este párrafo
        # 3 chars para "• " + 2 chars para "\n\n" = 5 chars extra por bullet
        added_len = len(para) + 5
        
        if current_length + added_len > max_total_length:
            # Si es el último que cabe, intentar truncarlo para que entre algo
            remaining = max_total_length - current_length - 5
            if remaining > 50:
                para = para[:remaining-3] + "..."
                bullets.append(f"• {para}")
            break
            
        bullets.append(f"• {para}")
        current_length += added_len
    
    return '\n\n'.join(bullets)

def traducir(texto):
    """Traduce texto a español y chino."""
    try:
        es = translator.translate(texto, dest='es').text
        zh = translator.translate(texto, dest='zh-cn').text
        return es, zh
    except Exception as e:
        logger.warning(f"Error traducción: {e}")
        return texto, texto
