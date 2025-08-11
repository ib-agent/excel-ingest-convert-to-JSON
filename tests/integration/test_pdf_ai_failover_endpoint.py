from __future__ import annotations

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile


class TestPDFAIFailoverEndpoint(TestCase):
    def test_ai_failover_endpoint_basic(self):
        # Provide minimal PDF-like bytes; pipeline has safe fallback
        fake_pdf = b"%PDF-1.4 minimal"
        upload = SimpleUploadedFile("sample.pdf", fake_pdf, content_type="application/pdf")
        resp = self.client.post('/api/pdf/ai-failover/', data={'file': upload})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('processing_mode'), 'ai_failover_routing')
        self.assertIn('result', data)


