## API Usage Guide

This guide summarizes available endpoints for uploading and retrieving JSON created by Excel extraction and PDF table detection. It reflects the new results endpoints and consistent status records.

### Base
- FastAPI service title: "Excel/PDF Processor"
- Static files: `/static`

### Health and Status
- GET `/api/health/` → service health
- GET `/api/status/{processing_id}/` → processing record
  - Always contains:
    - `filename`, `type` (`excel`|`pdf`|...), `large_file` flag
    - `storage` object when storage is enabled, including `download_urls`
    - If storage is disabled and results were cached: `file_id` and `download_urls`
    - For large Excel: `summary` (sheet summaries, numeric cells)

### Excel
- POST `/api/upload/` (multipart/form-data)
  - Form fields: `file` (Excel), `enable_comparison` (bool), `enable_ai_analysis` (bool)
  - Small files: returns inline `data` (workbook JSON) and `table_data` (table-oriented JSON)
  - Large files: returns `summary` and download URLs
  - Response includes `processing_id` and, when applicable, `storage` with `download_urls`
  - When storage is disabled, results are also cached and exposed via `download_urls` and `file_id` for later retrieval
  - Async processing: add `async_mode=true`. Optional `callback_url` (HTTP POST webhook), `pubsub_provider` (e.g., `kafka`), and `pubsub_topic`. Returns 202 with `processing_id`, and the service will send a notification when complete.
  - Content-Type: `multipart/form-data`
  - Success responses:
    - 200 OK (sync): `{ success, format, filename, large_file, data?, table_data?, summary?, storage?, processing_id, ... }`
    - 202 Accepted (async): `{ accepted, processing_id, status_endpoint, results_endpoints }`
  - Error responses: 400 (validation), 500 (processing failure)

- POST `/api/transform-tables/` (JSON)
  - Body: `{ json_data, options }` → returns `table_data`

- POST `/api/resolve-headers/` (JSON)
  - Body: `{ table_data }` → returns same data (headers pre-resolved in labels)

- POST `/api/excel/analyze-complexity/` (multipart)
  - Returns per-sheet complexity and overall recommendation
  - When storage is enabled, complexity results are stored and exposed via `storage.download_urls`

- POST `/api/excel/comparison-analysis/` (multipart)
  - Returns traditional vs AI comparison results per sheet
  - When storage is enabled, stored and exposed via `storage.download_urls`

### PDF
- POST `/api/pdf/upload/` (multipart/form-data)
  - Returns extracted content (table removal pipeline)
  - Includes `processing_id`
  - When storage is disabled, results are cached to support later retrieval via results endpoints
  - Async processing: add `async_mode=true` and optional notification params like Excel.
  - Content-Type: `multipart/form-data`

- POST `/api/pdf/table-removal/` (multipart)
  - Alias of `/api/pdf/upload/`

- POST `/api/pdf/ai-failover/` (multipart)
  - Returns failover pipeline results; `processing_id` and storage info as configured

- POST `/api/pdf/process/` (JSON)
  - Body: `{ file_path, extract_tables, extract_text, extract_numbers }`
  - Returns inline results

- GET `/api/pdf/status/` → capability info

### Storage
- POST `/api/storage/store-file/` (multipart)
  - Query `storage_type` required; optional `metadata` (JSON string)
  - Returns `reference` and `download_url`

- POST `/api/storage/store-json/` (JSON)
  - Body: `{ storage_type, data, key_prefix?, metadata? }`
  - Returns `reference` and `download_url`

- GET `/api/storage/get?key=...` → raw bytes
- GET `/api/storage/get-json/?key=...` → JSON object
- GET `/api/storage/list/?prefix=...` → references under a path
- DELETE `/api/storage/delete/?key=...`

### New Result Retrieval Endpoints
- GET `/api/results/{processing_id}/full`
  - Returns full workbook JSON (Excel) or processed JSON
  - Resolves from storage if available; otherwise from cache using `file_id`

- GET `/api/results/{processing_id}/table`
  - Returns table-oriented JSON (Excel) if available
  - Resolves from storage or cache

- GET `/api/results/{processing_id}/meta`
  - Returns Excel large-file `summary` from status when present, or stored complexity results if available

### Async Notifications
- Notification payload fields (via webhook and Kafka message):
  - `type`, `filename`, `processing_id`, `status`
  - `results_endpoints`: `{ full, table, meta, status }`
  - `download_urls` (when available)
  - `storage_keys` (when available): S3 or local keys for `processed_json`, `table_data`, etc.
  - `cache_handle` (when available): `{ file_id }`
- Kafka publishing is best-effort. Provide brokers via `KAFKA_BROKERS` or `KAFKA_BOOTSTRAP_SERVERS` env vars.
 - Webhook retries are not currently implemented; failures are swallowed. Configure `WEBHOOK_TIMEOUT_SECONDS` (default 5) for HTTP notify.
 - Notification URLs are relative in `results_endpoints`; prefix with your service base URL in clients.

### Notes
- Env vars:
  - `USE_STORAGE_SERVICE` (`true`|`false`)
  - `STORAGE_BACKEND` (`local`|`s3`)
  - For `local`: `LOCAL_STORAGE_PATH`
  - For `s3`: `S3_BUCKET_NAME`, `AWS_REGION`, `AWS_ENDPOINT_URL` (optional)
- When storage is disabled, responses include `file_id` and cache `download_urls`, and results endpoints will still work.
 - Status values: `processing`, `completed`. Current flows process synchronously unless `async_mode=true` is used.
 - Large-file detection (Excel): estimated by cells; large files return summaries and download links rather than inline data.

### Example JSON locations and test outputs

- Example and expected JSON fixtures are under `tests/fixtures/json/`.
- Tests write any generated outputs to a temporary directory via pytest's `tmp_path` fixture, so no artifacts are left in the repository root.


