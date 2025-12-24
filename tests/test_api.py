"""
Tests for Chatterbox API
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestHealthEndpoint(unittest.TestCase):
    """Tests for /api/health endpoint."""
    
    def test_health_returns_200(self):
        """Health check should return 200."""
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
    
    def test_health_has_required_fields(self):
        """Health response should have status, model_loaded, device, version."""
        response = client.get("/api/health")
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("model_loaded", data)
        self.assertIn("device", data)
        self.assertIn("version", data)


class TestGenerateEndpoint(unittest.TestCase):
    """Tests for /api/generate endpoint."""
    
    def test_missing_text_returns_422(self):
        """Missing required 'text' field should return 422."""
        response = client.post("/api/generate", data={})
        self.assertEqual(response.status_code, 422)
    
    def test_empty_text_returns_400(self):
        """Empty text should return 422 (validation error) or 400."""
        response = client.post("/api/generate", data={"text": ""})
        self.assertIn(response.status_code, [400, 422])
    
    def test_whitespace_only_returns_400(self):
        """Whitespace-only text should return 400."""
        response = client.post("/api/generate", data={"text": "   "})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
