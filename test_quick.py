#!/usr/bin/env python3
"""
Script de prueba rápida para verificar la extracción sin ejecutar el bot completo.
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_scraping():
    """Prueba solo el scraping, sin conectar a Discord."""
    from main import get_latest_post_by_tag, extract_and_summarize_article, TAGS_VALIDOS
    
    print("=" * 70)
    print("🧪 PRUEBA RÁPIDA DE SCRAPING Y EXTRACCIÓN")
    print("=" * 70)
    
    for tag in TAGS_VALIDOS:
        print(f"\n{'=' * 70}")
        print(f"📝 Probando tag: {tag}")
        print("=" * 70)
        
        # Obtener último post
        result = get_latest_post_by_tag(tag)
        
        if not result:
            print(f"❌ No se encontró post para '{tag}'")
            continue
        
        titulo, url = result
        print(f"✅ Título: {titulo}")
        print(f"🔗 URL: {url}")
        
        # Extraer y resumir
        print(f"\n📄 Extrayendo contenido...")
        resumen = extract_and_summarize_article(url)
        
        print(f"\n{'─' * 70}")
        print("RESUMEN:")
        print(f"{'─' * 70}")
        print(resumen)
        print(f"{'─' * 70}")
        print(f"📊 Longitud: {len(resumen)} caracteres")
        
        # Verificar resultado
        if "no se pudo" in resumen.lower() or "error" in resumen.lower():
            print("⚠️  Obtuvo mensaje de fallback/error")
        elif len(resumen) > 200:
            print("✅ Extracción exitosa")
        else:
            print("⚠️  Resumen muy corto")
    
    print("\n" + "=" * 70)
    print("✅ Prueba completada")
    print("Si ves contenido real, todo está funcionando correctamente")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_scraping()
    except KeyboardInterrupt:
        print("\n\n❌ Prueba cancelada")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
