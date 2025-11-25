#!/usr/bin/env python3
"""
Script de diagnóstico para probar extracción de artículos del foro MIR4.
Prueba diferentes métodos para extraer contenido.
"""

import requests
from bs4 import BeautifulSoup
from newspaper import Article
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL de ejemplo (la que obtuviste en el test)
TEST_URL = "https://forum.mir4global.com/board/patchnote/2040383"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def test_newspaper3k():
    """Prueba extracción con newspaper3k."""
    print("\n" + "="*60)
    print("MÉTODO 1: newspaper3k")
    print("="*60)
    
    try:
        article = Article(TEST_URL)
        logger.info("📥 Descargando artículo...")
        article.download()
        
        logger.info("📝 Parseando artículo...")
        article.parse()
        
        logger.info(f"✅ Título: {article.title}")
        logger.info(f"✅ Texto extraído: {len(article.text)} caracteres")
        
        if article.text:
            print("\n📄 Primeros 500 caracteres:")
            print(article.text[:500])
        
        # Intentar NLP
        try:
            logger.info("🧠 Generando resumen con NLP...")
            article.nlp()
            logger.info(f"✅ Resumen: {len(article.summary)} caracteres")
            print("\n📋 Resumen:")
            print(article.summary)
            return True
        except Exception as e:
            logger.warning(f"⚠️ NLP falló: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en newspaper3k: {e}")
        return False

def test_beautifulsoup():
    """Prueba extracción con BeautifulSoup directo."""
    print("\n" + "="*60)
    print("MÉTODO 2: BeautifulSoup directo")
    print("="*60)
    
    try:
        logger.info("📥 Descargando página...")
        response = requests.get(TEST_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar el contenido principal
        # El foro MIR4 usa diferentes selectores
        content_selectors = [
            'div.article_content',
            'div.board_content', 
            'div.post-content',
            'article.article',
            'div.content',
        ]
        
        content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                logger.info(f"✅ Contenido encontrado con selector: {selector}")
                break
        
        if content:
            # Extraer solo texto, sin scripts ni estilos
            for script in content(["script", "style"]):
                script.decompose()
            
            text = content.get_text(separator='\n', strip=True)
            logger.info(f"✅ Texto extraído: {len(text)} caracteres")
            
            print("\n📄 Primeros 500 caracteres:")
            print(text[:500])
            
            return text
        else:
            logger.warning("⚠️ No se encontró contenido con los selectores")
            # Guardar HTML para inspección
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("💾 HTML guardado en debug_page.html para inspección")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error en BeautifulSoup: {e}")
        return None

def test_requests_with_headers():
    """Prueba descarga con headers específicos."""
    print("\n" + "="*60)
    print("MÉTODO 3: Requests con headers completos")
    print("="*60)
    
    try:
        logger.info("📥 Descargando con headers completos...")
        response = requests.get(TEST_URL, headers=HEADERS, timeout=10)
        logger.info(f"✅ Status code: {response.status_code}")
        logger.info(f"✅ Content-Type: {response.headers.get('content-type')}")
        logger.info(f"✅ Tamaño: {len(response.text)} bytes")
        
        # Verificar si hay contenido
        if 'text/html' in response.headers.get('content-type', ''):
            logger.info("✅ Es HTML válido")
            return True
        else:
            logger.warning("⚠️ No es HTML")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DE EXTRACCIÓN DE ARTÍCULOS MIR4")
    print("URL de prueba:", TEST_URL)
    print("\nNOTA: Cambia TEST_URL a una URL real del foro si es necesario\n")
    
    # Ejecutar tests
    test_requests_with_headers()
    test_newspaper3k()
    text = test_beautifulsoup()
    
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print("Si newspaper3k falla pero BeautifulSoup funciona,")
    print("necesitamos cambiar la función extract_and_summarize_article")
    print("para usar BeautifulSoup directamente.")
