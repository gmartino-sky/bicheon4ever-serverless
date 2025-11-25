import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime

# -------- CONFIGURACION DE LOGGING --------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# -------- CONFIGURACION --------
BASE_URL = "https://forum.mir4global.com"
# Tags unificados con main.py (siempre en minúsculas)
TAGS = ["patch note", "notice", "event"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}


def get_latest_post_by_tag(tag):
    """Obtiene el último post del foro MIR4 para un tag específico.
    
    Args:
        tag: Tag a buscar ('patch note', 'notice', o 'event')
        
    Returns:
        Diccionario con información del post o None si no se encuentra
    """
    # Mapa de URLs según el tag
    url_map = {
        "patch note": f"{BASE_URL}/board/patchnote",
        "notice": f"{BASE_URL}/board/notice",
        "event": f"{BASE_URL}/board/newevent?category_id=1"
    }
    
    url = url_map.get(tag.lower())
    if not url:
        logger.error(f"❌ Tag inválido: {tag}")
        return None

    try:
        logger.info(f"🔍 Scrapeando {tag}...")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        articles = soup.find_all("article", class_="article")
        
        if not articles:
            logger.warning(f"⚠️ No se encontraron artículos para {tag}")
            return None
        
        for article in articles:
            category_tag = article.find("em", class_="article_category")
            
            # Comparación en minúsculas para consistencia
            if category_tag and category_tag.text.strip().lower() == tag.lower():
                # Filtrar posts de redes sociales
                full_text = article.get_text(strip=True).lower()
                if any(s in full_text for s in ['facebook', 'instagram', 'youtube']):
                    logger.debug(f"⏭️ Saltando post de redes sociales")
                    continue
                
                title_tag = article.find("span", class_="subject")
                link_tag = article.find("a", class_="article_subject")

                post_data = {
                    "tag": tag,
                    "title": title_tag.text.strip() if title_tag else "(Sin título)",
                    "url": link_tag.get("href") if link_tag else ""
                }
                
                logger.info(f"✅ Post encontrado: {post_data['title']}")
                return post_data

        logger.info(f"ℹ️ No se encontró ningún post válido para '{tag}'")
        return None
        
    except requests.RequestException as e:
        logger.error(f"❌ Error de red al obtener {tag}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}", exc_info=True)
        return None


def main():
    """Función principal que obtiene los últimos posts y los guarda en JSON."""
    logger.info("🚀 Iniciando scraper de prueba...")
    posts = {}
    
    for tag in TAGS:
        post = get_latest_post_by_tag(tag)
        if post:
            posts[tag] = post

    if posts:
        with open("ultimas_noticias.json", "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Archivo 'ultimas_noticias.json' actualizado con {len(posts)} posts")
        logger.info(f"📊 Tags obtenidos: {list(posts.keys())}")
    else:
        logger.warning("⚠️ No se obtuvieron posts")


if __name__ == "__main__":
    main()

