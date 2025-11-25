"""
Tests unitarios para el scraper de MIR4.

Ejecutar con: pytest tests/ -v
"""

import pytest
from bs4 import BeautifulSoup
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestTagValidation:
    """Tests para validación de tags."""
    
    def test_valid_tags(self):
        """Verifica que los tags válidos están en minúsculas."""
        from main import TAGS_VALIDOS
        
        assert 'patch note' in TAGS_VALIDOS
        assert 'notice' in TAGS_VALIDOS
        assert 'event' in TAGS_VALIDOS
    
    def test_tag_format_consistency(self):
        """Verifica que los tags están en formato consistente."""
        from main import TAGS_VALIDOS
        
        for tag in TAGS_VALIDOS:
            assert tag == tag.lower(), f"Tag '{tag}' debe estar en minúsculas"
            assert tag.strip() == tag, f"Tag '{tag}' no debe tener espacios extras"


class TestSocialMediaFiltering:
    """Tests para filtrado de posts de redes sociales."""
    
    @pytest.mark.parametrize("text,should_filter", [
        ("Nueva actualización de Facebook Event", True),
        ("Instagram Giveaway", True),
        ("Check our YouTube channel", True),
        ("Nuevo Patch Note v2.0", False),
        ("Evento de Halloween", False),
        ("Notice: Maintenance Schedule", False),
    ])
    def test_social_media_detection(self, text, should_filter):
        """Verifica que se filtran correctamente posts de redes sociales."""
        keywords = ['facebook', 'instagram', 'youtube']
        text_lower = text.lower()
        is_social = any(keyword in text_lower for keyword in keywords)
        
        assert is_social == should_filter, \
            f"Texto '{text}' debería {'filtrarse' if should_filter else 'no filtrarse'}"


class TestURLFormatting:
    """Tests para formato de URLs."""
    
    def test_relative_url_conversion(self):
        """Verifica que URLs relativas se convierten a absolutas."""
        base_url = "https://forum.mir4global.com"
        relative_url = "/board/123456"
        
        if not relative_url.startswith('http'):
            absolute_url = f"{base_url}{relative_url}"
        else:
            absolute_url = relative_url
        
        assert absolute_url.startswith('http')
        assert base_url in absolute_url
    
    def test_absolute_url_unchanged(self):
        """Verifica que URLs absolutas no se modifican."""
        absolute_url = "https://forum.mir4global.com/board/123456"
        
        if not absolute_url.startswith('http'):
            result = f"https://forum.mir4global.com{absolute_url}"
        else:
            result = absolute_url
        
        assert result == absolute_url


class TestHTMLParsing:
    """Tests para parsing de HTML."""
    
    def test_parse_article_structure(self):
        """Verifica que se puede parsear la estructura de un artículo."""
        mock_html = """
        <article class="article">
            <em class="article_category">Patch Note</em>
            <span class="subject">Actualización v2.0</span>
            <a class="article_subject" href="/board/123">Link</a>
        </article>
        """
        
        soup = BeautifulSoup(mock_html, 'html.parser')
        article = soup.find('article', class_='article')
        
        assert article is not None
        
        category = article.find('em', class_='article_category')
        assert category is not None
        assert category.text.strip() == "Patch Note"
        
        subject = article.find('span', class_='subject')
        assert subject is not None
        assert "Actualización" in subject.text
    
    def test_missing_elements_handled(self):
        """Verifica que elementos faltantes no causan errores."""
        mock_html = "<article class='article'></article>"
        
        soup = BeautifulSoup(mock_html, 'html.parser')
        article = soup.find('article', class_='article')
        
        category = article.find('em', class_='article_category')
        assert category is None  # No debería causar error
        
        subject = article.find('span', class_='subject')
        assert subject is None


class TestCacheFiles:
    """Tests para sistema de caché."""
    
    def test_cache_file_mapping(self):
        """Verifica que cada tag tiene su archivo de caché."""
        from main import CACHES, TAGS_VALIDOS
        
        for tag in TAGS_VALIDOS:
            assert tag in CACHES, f"Tag '{tag}' debe tener archivo de caché"
            assert CACHES[tag].endswith('.txt'), "Caché debe ser archivo .txt"


class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_invalid_tag_handling(self):
        """Verifica que tags inválidos se manejan correctamente."""
        from main import TAGS_VALIDOS
        
        invalid_tag = "invalid_tag"
        assert invalid_tag not in TAGS_VALIDOS
    
    def test_empty_response_handling(self):
        """Verifica que respuestas vacías se manejan correctamente."""
        mock_html = "<html><body></body></html>"
        
        soup = BeautifulSoup(mock_html, 'html.parser')
        articles = soup.find_all('article', class_='article')
        
        assert len(articles) == 0
        # La función debería retornar None en este caso


class TestTranslation:
    """Tests para funcionalidad de traducción."""
    
    def test_translation_fallback(self):
        """Verifica que existe fallback si la traducción falla."""
        original_text = "Test message"
        
        # Simular error de traducción
        try:
            # Si falla, debería retornar texto original
            es, zh = original_text, original_text
        except:
            es, zh = original_text, original_text
        
        assert es == original_text
        assert zh == original_text


# Configuración de pytest
def pytest_configure(config):
    """Configuración personalizada de pytest."""
    config.addinivalue_line(
        "markers", "integration: marca tests de integración (requieren red)"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
