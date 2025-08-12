## API Cookbook

Practical recipes for using the Excel/PDF Processor API.

### 1) Sync Excel upload (simple)

Request:

```bash
curl -s -X POST \
  -F "file=@/path/to/file.xlsx" \
  http://localhost:8000/api/upload/
```

Response (200): contains `data` and `table_data` inline for small files.

### 2) Large Excel upload with storage disabled

Env: ensure storage is disabled (default). Response includes `download_urls` and `processing_id`.

```bash
curl -s -X POST \
  -F "file=@/path/to/large.xlsx" \
  http://localhost:8000/api/upload/
```

Then download later via cache:

```bash
curl -OJ "http://localhost:8000/api/download/?type=full&file_id=<file_id>"
curl -OJ "http://localhost:8000/api/download/?type=table&file_id=<file_id>"
```

Or via results endpoints:

```bash
curl -s "http://localhost:8000/api/results/<processing_id>/full"
curl -s "http://localhost:8000/api/results/<processing_id>/table"
curl -s "http://localhost:8000/api/results/<processing_id>/meta"
```

### 3) Excel upload with async + webhook

Start a local webhook receiver (example using `nc`):

```bash
while true; do nc -l 9001; done
```

Upload:

```bash
curl -s -X POST \
  -F "file=@/path/to/file.xlsx" \
  -F "async_mode=true" \
  -F "callback_url=http://localhost:9001" \
  http://localhost:8000/api/upload/
```

Response (202): `{ accepted, processing_id, status_endpoint, results_endpoints }`

Later, fetch results:

```bash
curl -s "http://localhost:8000/api/results/<processing_id>/full"
```

### 4) Excel upload with Kafka notification

Set env in server process:

```bash
export KAFKA_BROKERS=localhost:9092
```

Upload:

```bash
curl -s -X POST \
  -F "file=@/path/to/file.xlsx" \
  -F "async_mode=true" \
  -F "pubsub_provider=kafka" \
  -F "pubsub_topic=excel-results" \
  http://localhost:8000/api/upload/
```

Consumers should read from `excel-results` topic; message contains `processing_id`, `results_endpoints`, optional `download_urls`, and storage keys when available.

### 5) PDF upload (sync)

```bash
curl -s -X POST \
  -F "file=@/path/to/file.pdf" \
  http://localhost:8000/api/pdf/upload/
```

Response (200): `{ success, result, filename, processing_id?, storage? }`

### 6) PDF upload (async) and retrieve results

```bash
curl -s -X POST \
  -F "file=@/path/to/file.pdf" \
  -F "async_mode=true" \
  http://localhost:8000/api/pdf/upload/
```

Poll and fetch:

```bash
curl -s "http://localhost:8000/api/status/<processing_id>/"
curl -s "http://localhost:8000/api/results/<processing_id>/table"
```

### 7) Transform pre-extracted Excel JSON to tables

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"json_data": {"workbook": {"sheets": []}}, "options": {}}' \
  http://localhost:8000/api/transform-tables/
```

### 8) Storage service: store and fetch JSON

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"storage_type": "processed", "data": {"x":1}}' \
  http://localhost:8000/api/storage/store-json/

curl -s "http://localhost:8000/api/storage/get-json/?key=<key>"
```

### 9) End-to-end: robust client flow (pseudo)

1. Upload with `async_mode=true`.
2. Poll `/api/status/{processing_id}/` until `status=completed` or await webhook/Kafka.
3. Fetch results via `/api/results/{processing_id}/full` and `/table`.
4. Optionally use `download_urls` for direct file download.

### Example JSON and fixtures

- Example JSON responses and expected data are under `tests/fixtures/json/`.
- Tests write generated JSON outputs to a temporary directory via pytest `tmp_path` to avoid leaving files in the repository.

