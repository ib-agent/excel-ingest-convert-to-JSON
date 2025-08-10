# Storage Service Endpoints

Microservice-style endpoints that abstract storage for local filesystem and AWS S3. Controlled by environment variables:

- `STORAGE_BACKEND`: `local` (default) or `s3`
- `LOCAL_STORAGE_PATH`: base path for local storage (default: `<MEDIA_ROOT>/storage`)
- `S3_BUCKET_NAME`: bucket name when using `s3`
- `AWS_REGION`: region (default: `us-east-1`)
- `AWS_ENDPOINT_URL`: optional; use LocalStack like `http://localhost:4566`
- `USE_STORAGE_SERVICE`: `true` to enable storing artifacts from processing endpoints

## Endpoints

### POST /api/storage/store-file/
Multipart form-data
- `file`: binary file
- `storage_type`: one of `original|processed|ai_analysis|table_data|complexity`
- `metadata` (optional): JSON string

Response 201
```json
{
  "reference": {
    "key": "original/uuid/file.xlsx",
    "storage_type": "original",
    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "size_bytes": 123,
    "created_at": "2025-01-08T10:00:00+00:00",
    "metadata": {"processing_id": "..."}
  },
  "download_url": "/api/storage/get?key=original/uuid/file.xlsx"
}
```

### POST /api/storage/store-json/
JSON body
```json
{
  "storage_type": "processed",
  "key_prefix": "<processing_id>",
  "data": {"any": "json"},
  "metadata": {"optional": true}
}
```

Response 201
```json
{
  "reference": {"key": "processed/uuid/<processing_id>/data.json", "storage_type": "processed", "content_type": "application/json", "size_bytes": 123, "created_at": "...", "metadata": {}},
  "download_url": "/api/storage/get?key=processed/uuid/<processing_id>/data.json"
}
```

### GET /api/storage/get?key=...
Downloads raw bytes for a stored object (local mode). In `s3` mode, use the `download_url` provided in responses.

### GET /api/storage/get-json?key=...
Fetch JSON and return inline.

### DELETE /api/storage/delete?key=...
Delete stored object by key.

### GET /api/storage/list?prefix=...
List references under a prefix.

## Integration in upload_and_convert

If `USE_STORAGE_SERVICE=true`, the following references will be stored and returned:
- `original_file` (StorageType.ORIGINAL_FILE)
- `processed_json` (StorageType.PROCESSED_JSON)
- `table_data` (StorageType.TABLE_DATA)

Example response fragment:
```json
{
  "storage": {
    "processing_id": "...",
    "original_file": {"key": "original/..."},
    "processed_json": {"key": "processed/..."},
    "table_data": {"key": "table_data/..."},
    "download_urls": {
      "original_file": "/api/storage/get?key=original/...",
      "processed_json": "/api/storage/get?key=processed/...",
      "table_data": "/api/storage/get?key=table_data/..."
    }
  }
}
```

## Curl Examples

- Store file:
```bash
curl -F "file=@tests/test_excel/Nickson_Lender_Financial_Model.xlsx" \
     -F "storage_type=original" \
     -F 'metadata={"processing_id":"123"}' \
     http://localhost:8000/api/storage/store-file/
```

- Store JSON:
```bash
curl -X POST http://localhost:8000/api/storage/store-json/ \
  -H 'Content-Type: application/json' \
  -d '{"storage_type":"processed","key_prefix":"123","data":{"ok":true}}'
```

- Get bytes:
```bash
curl -L 'http://localhost:8000/api/storage/get?key=processed/.../data.json'
```

- Delete:
```bash
curl -X DELETE 'http://localhost:8000/api/storage/delete?key=processed/.../data.json'
```


