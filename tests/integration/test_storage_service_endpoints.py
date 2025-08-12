import json
import os
import tempfile
import django
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_converter.settings')
django.setup()


class StorageServiceEndpointsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ['STORAGE_BACKEND'] = 'local'
        os.environ['LOCAL_STORAGE_PATH'] = self.tmpdir.name

    def tearDown(self):
        try:
            self.tmpdir.cleanup()
        except Exception:
            pass

    def test_store_json_get_list_delete(self):
        # Store JSON
        payload = {
            'storage_type': 'processed',
            'key_prefix': 'test_prefix',
            'data': {'hello': 'world'},
        }
        resp = self.client.post('/api/storage/store-json/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        key = body['reference']['key']

        # Get JSON
        resp = self.client.get(f'/api/storage/get-json/?key={key}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['data'], {'hello': 'world'})

        # Get bytes
        resp = self.client.get(f'/api/storage/get/?key={key}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/json', resp['Content-Type'])

        # List
        prefix = key.split('/')[0]
        resp = self.client.get(f'/api/storage/list/?prefix={prefix}')
        self.assertEqual(resp.status_code, 200)
        items = resp.json()['items']
        self.assertTrue(any(i['key'] == key for i in items))

        # Delete
        resp = self.client.delete(f'/api/storage/delete/?key={key}')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['deleted'])

    def test_store_file(self):
        content = b'example-bytes'
        upload = SimpleUploadedFile('example.bin', content, content_type='application/octet-stream')
        resp = self.client.post('/api/storage/store-file/', data={'file': upload, 'storage_type': 'original'})
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        key = body['reference']['key']

        # Download via get
        resp = self.client.get(f'/api/storage/get/?key={key}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, content)


