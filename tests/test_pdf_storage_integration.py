import json
import os
import tempfile
import django
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_converter.settings')
django.setup()


class PDFStorageIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
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
        repo_root = os.path.dirname(os.path.dirname(__file__))
        pdf_path = os.path.join(repo_root, 'tests', 'test_pdfs', 'Test_PDF_Table_9_numbers.pdf')
        if not os.path.exists(pdf_path):
            # Fallback to another known fixture
            pdf_path = os.path.join(repo_root, 'tests', 'test_pdfs', 'Test_PDF_Table_9_numbers_with_before_and_after_paragraphs.pdf')
        with open(pdf_path, 'rb') as f:
            return f.read()

    def test_upload_and_process_pdf_stores_artifacts(self):
        pdf_bytes = self._load_fixture_pdf()
        upload = SimpleUploadedFile('test.pdf', pdf_bytes, content_type='application/pdf')
        resp = self.client.post('/api/pdf/upload/', data={'file': upload})
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
        upload = SimpleUploadedFile('test.pdf', pdf_bytes, content_type='application/pdf')
        resp = self.client.post('/api/pdf/table-removal/', data={'file': upload})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn('storage', body)
        storage = body['storage']
        self.assertIsNotNone(storage)
        self.assertIn('processed_json', storage)
        self.assertIn('download_urls', storage)


