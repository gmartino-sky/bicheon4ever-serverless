#!/usr/bin/env python3
"""
Script de prueba standalone de la función mejorada de extracción.
No requiere importar main.py completo.
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs de prueba reales del foro MIR4
test_urls = [
    ("Patch Note", "https://forum.mir4global.com/board/patchnote"),
    ("Notice", "https://forum.mir4global.com/board/notice"),
    ("Event", "https://forum.mir4global.com/board/newevent?category_id=1"),
]

def extract_article(url):
    """Función de extracción mejorada - copia de la nueva implementación."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Selectores del foro MIR4
        content_selectors = [
            'div.article_content',
            'div.article-content',
            'div.board_content',
            'div.post_content',
        ]
        
        content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                logger.debug(f"✅ Contenido encontrado con: {selector}")
                break
        
        if not content:
            # Fallback: buscar div con mucho texto
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True)
                if len(text) > 200:
                    content = div
                    break
        
        if content:
            # Limpiar
            for unwanted in content(['script', 'style', 'meta', 'link']):
                unwanted.decompose()
            
            text = content.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            if text and len(text) > 50:
                # Crear resumen
                paragraphs = text.split('\n\n')
                summary_parts = []
                total_length = 0
                
                for para in paragraphs[:5]:
                    if total_length + len(para) > 600:
                        break
                    summary_parts.append(para)
                    total_length += len(para)
                
                if summary_parts:
                    summary = '\n\n'.join(summary_parts)
                    if len(summary) < len(text):
                        summary += "..."
                    return summary
                else:
                    return text[:600] + ("..." if len(text) > 600 else "")
        
        return "No se pudo extraer contenido"
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {str(e)}"

def get_latest_url(board_url):
    """Obtiene la URL del primer artículo."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    try:
        response = requests.get(board_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        first_article = soup.select_one('article.article a.article_subject')
        if first_article:
            href = first_article.get('href')
            if not href.startswith('http'):
                href = f"https://forum.mir4global.com{href}"
            return href
    except:
        pass
    return None

if __name__ == "__main__":
    print("=" * 70)
    print("TEST DE EXTRACCIÓN MEJORADA")
    print("=" * 70)
    
    for category, board_url in test_urls:
        print(f"\n{'=' * 70}")
        print(f"📂 {category}")
        print("=" * 70)
        
        # Obtener URL del último artículo
        article_url = get_latest_url(board_url)
        
        if not article_url:
            print("❌ No se pudo obtener URL del artículo")
            continue
        
        print(f"🔗 URL: {article_url}")
        print()
        
        # Extraer contenido
        resumen = extract_article(article_url)
        
        print("📄 RESUMEN:")
        print("-" * 70)
        print(resumen)
        print("-" * 70)
        print(f"📊 {len(resumen)} caracteres")
        
        if "no se pudo" in resumen.lower() or len(resumen) < 100:
            print("⚠️ Resultado corto o error")
        else:
            print("✅ Extracción exitosa")
    
    print("\n" + "=" * 70)
    print("Si ves contenido real, la solución funciona")
    print("Aplica reiniciando el bot después de confirmar")
    print("=" * 70)
