from __future__ import annotations

import unittest
from fastapi.testclient import TestClient
from fastapi_service.main import app


class TestPDFAIFailoverEndpoint(unittest.TestCase):
    def test_ai_failover_endpoint_basic(self):
        # Provide minimal PDF-like bytes; pipeline has safe fallback
        fake_pdf = b"%PDF-1.4 minimal"
        client = TestClient(app)
        files = {"file": ("sample.pdf", fake_pdf, "application/pdf")}
        resp = client.post('/api/pdf/ai-failover/', files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('processing_mode'), 'ai_failover_routing')
        self.assertIn('result', data)


