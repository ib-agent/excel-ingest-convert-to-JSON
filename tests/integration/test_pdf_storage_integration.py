import json
import os
import tempfile
import unittest
from fastapi.testclient import TestClient
from fastapi_service.main import app


class PDFStorageIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ['STORAGE_BACKEND'] = 'local'
        os.environ['LOCAL_STORAGE_PATH'] = self.tmpdir.name
        os.environ['USE_STORAGE_SERVICE'] = 'true'

    def tearDown(self):
        try:
            self.tmpdir.cleanup()
        except Exception:
            pass

    def _load_fixture_pdf(self) -> bytes:
        # Load an existing small test PDF from repository fixtures
        repo_tests_dir = os.path.dirname(os.path.dirname(__file__))
        pdf_path = os.path.join(repo_tests_dir, 'fixtures', 'pdfs', 'Test_PDF_Table_9_numbers.pdf')
        if not os.path.exists(pdf_path):
            # Fallback to another known fixture
            pdf_path = os.path.join(repo_tests_dir, 'fixtures', 'pdfs', 'Test_PDF_Table_9_numbers_with_before_and_after_paragraphs.pdf')
        with open(pdf_path, 'rb') as f:
            return f.read()

    def test_upload_and_process_pdf_stores_artifacts(self):
        pdf_bytes = self._load_fixture_pdf()
        files = {'file': ('test.pdf', pdf_bytes, 'application/pdf')}
        resp = self.client.post('/api/pdf/upload/', files=files)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn('storage', body)
        storage = body['storage']
        self.assertIsNotNone(storage)
        self.assertIn('processed_json', storage)
        self.assertIn('download_urls', storage)

        pid = storage['processing_id']
        resp = self.client.get(f'/api/status/{pid}/')
        self.assertIn(resp.status_code, (200, 404))
        if resp.status_code == 200:
            record = resp.json()
            self.assertEqual(record['processing_id'], pid)
            self.assertEqual(record['type'], 'pdf')

    def test_upload_and_process_pdf_table_removal_stores_artifacts(self):
        pdf_bytes = self._load_fixture_pdf()
        files = {'file': ('test.pdf', pdf_bytes, 'application/pdf')}
        resp = self.client.post('/api/pdf/table-removal/', files=files)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn('storage', body)
        storage = body['storage']
        self.assertIsNotNone(storage)
        self.assertIn('processed_json', storage)
        self.assertIn('download_urls', storage)


