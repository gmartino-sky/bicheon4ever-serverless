#!/usr/bin/env python3
"""
Test script para verificar las funciones Lambda localmente.
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import os

# Mock environment variables BEFORE importing lambda_function
os.environ['DISCORD_PUBLIC_KEY'] = '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
os.environ['DISCORD_TOKEN'] = 'mock_token'
os.environ['TABLE_CONFIG'] = 'MockConfig'
os.environ['TABLE_STATE'] = 'MockState'

# Mock boto3
with patch('boto3.resource') as mock_dynamodb:
    import lambda_function
    from database import DatabaseAdapter

class TestServerless(unittest.TestCase):
    
    def setUp(self):
        # Reset mocks
        lambda_function.db.dynamodb = MagicMock()
        lambda_function.db.table_config = MagicMock()
        lambda_function.db.table_state = MagicMock()
        
    @patch('lambda_function.verify_signature')
    def test_interaction_ping(self, mock_verify):
        """Test que el handler responde correctamente al PING de Discord."""
        mock_verify.return_value = True
        event = {
            'headers': {'x-signature-ed25519': 'sig', 'x-signature-timestamp': 'ts'},
            'body': json.dumps({'type': 1})
        }
        response = lambda_function.lambda_handler_interactions(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['type'], 1)
        print("✅ Test PING passed")

    @patch('lambda_function.verify_signature')
    def test_interaction_command_usar(self, mock_verify):
        """Test comando /usar para configurar canal."""
        mock_verify.return_value = True
        event = {
            'headers': {'x-signature-ed25519': 'sig', 'x-signature-timestamp': 'ts'},
            'body': json.dumps({
                'type': 2,
                'guild_id': '123',
                'data': {
                    'name': 'usar',
                    'options': [{'value': '999'}]
                }
            })
        }
        response = lambda_function.lambda_handler_interactions(event, None)
        self.assertEqual(response['statusCode'], 200)
        
        # Verificar que se llamó a DynamoDB
        lambda_function.db.table_config.put_item.assert_called()
        print("✅ Test comando /usar passed")

    @patch('lambda_function.get_latest_post_by_tag')
    @patch('lambda_function.extract_and_summarize_article')
    @patch('lambda_function.traducir')
    @patch('lambda_function.send_discord_message')
    def test_scraper_job(self, mock_send, mock_traducir, mock_extract, mock_get_post):
        """Test que el scraper detecta y envía nuevos posts."""
        # Setup Mocks
        lambda_function.db.table_config.scan.return_value = {
            'Items': [{'guild_id': '123', 'channel_id': 999}]
        }
        lambda_function.db.table_state.get_item.return_value = {} # No previous state
        
        mock_get_post.return_value = ('Titulo Test', 'http://test.com')
        mock_extract.return_value = 'Resumen Test'
        mock_traducir.return_value = ('Resumen ES', 'Resumen ZH')
        
        # Run
        result = lambda_function.lambda_handler_scraper({}, None)
        
        # Verify
        self.assertEqual(result['statusCode'], 200)
        mock_send.assert_called() # Should send message
        lambda_function.db.table_state.put_item.assert_called() # Should update state
        print("✅ Test Scraper Job passed")

    def test_database_adapter(self):
        """Test que el DatabaseAdapter maneja errores correctamente."""
        # Este test verifica que no se rompa si DynamoDB no está disponible
        with patch('boto3.resource', side_effect=Exception("No AWS credentials")):
            db = DatabaseAdapter()
            # No debería lanzar excepción
            config = db.get_config()
            self.assertEqual(config, {})
        print("✅ Test Database Adapter resilience passed")

if __name__ == '__main__':
    print("=" * 70)
    print("🧪 TESTS SERVERLESS - LAMBDA FUNCTIONS")
    print("=" * 70)
    unittest.main(verbosity=2)
