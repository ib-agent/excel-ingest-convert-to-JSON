import json
import os
import tempfile
import unittest
from fastapi.testclient import TestClient
from fastapi_service.main import app


class StorageServiceEndpointsTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
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
        resp = self.client.post('/api/storage/store-json/', json=payload)
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
        self.assertIn('application/json', resp.headers.get('content-type', ''))

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
        files = {'file': ('example.bin', content, 'application/octet-stream')}
        resp = self.client.post('/api/storage/store-file/?storage_type=original', files=files)
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        key = body['reference']['key']

        # Download via get
        resp = self.client.get(f'/api/storage/get/?key={key}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, content)


