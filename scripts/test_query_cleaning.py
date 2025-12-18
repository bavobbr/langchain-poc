
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag_engine import FIHRulesEngine
import config

class TestQueryCleaning(unittest.TestCase):
    def setUp(self):
        # Mock dependencies to avoid actual API calls
        self.mock_embeddings = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_db = MagicMock()
        
        # Patch the heavy imports and init
        with patch('rag_engine.PostgresVectorDB', return_value=self.mock_db), \
             patch('langchain_google_vertexai.VertexAIEmbeddings', return_value=self.mock_embeddings), \
             patch('langchain_google_vertexai.VertexAI', return_value=self.mock_llm):
            self.engine = FIHRulesEngine()
            
    def test_query_strips_variant_prefix(self):
        # Setup
        # 1. contextualize returns a query WITH prefix
        self.engine._contextualize_query = MagicMock(return_value="[VARIANT: indoor] can I hit a ball?")
        
        # 2. route_query returns a valid variant
        self.engine._route_query = MagicMock(return_value="indoor")
        
        # 3. db search returns empty list to avoid processing
        self.engine.db.search.return_value = []
        
        # Act
        self.engine.query("can I hit a ball?")
        
        # Assert
        # Check what was passed to embed_query
        # It SHOULD be "can I hit a ball?" (stripped)
        
        self.mock_embeddings.embed_query.assert_called_once()
        call_args = self.mock_embeddings.embed_query.call_args
        embedded_text = call_args[0][0]
        
        print(f"\nDEBUG: Contextualized Query: '[VARIANT: indoor] can I hit a ball?'")
        print(f"DEBUG: Embedded Text:      '{embedded_text}'")
        
        self.assertEqual(embedded_text.strip(), "can I hit a ball?")
        self.assertNotIn("indoor:", embedded_text.lower())

if __name__ == '__main__':
    unittest.main()
