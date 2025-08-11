## Django to FastAPI migration

### Goals
- **Keep UI unchanged**: preserve `"/"`, `"/excel/"`, `"/pdf/"` so the current HTML-based testing UI continues to work.
- **Expose the same API**: mirror the existing Django endpoints under the same paths.
- **Reuse processors**: call the existing pure-Python processors (Excel/PDF/storage/registry) from FastAPI.
- **Production-ready microservice**: run behind `uvicorn` with CORS, static files, and optional S3 storage.

### Current surface to mirror
- **UI pages**: `"/"`, `"/excel/"`, `"/pdf/"`
- **Excel API**:
  - `"/api/upload/"`
  - `"/api/download/"`
  - `"/api/transform-tables/"`
  - `"/api/resolve-headers/"`
  - `"/api/excel/analyze-complexity/"`
  - `"/api/excel/comparison-analysis/"`
- **PDF API**:
  - `"/api/pdf/upload/"`
  - `"/api/pdf/process/"`
  - `"/api/pdf/status/"`
  - `"/api/pdf/ai-failover/"`
  - `"/api/pdf/table-removal/"`
- **Storage API**: `"/api/storage/store-file/"`, `"/api/storage/store-json/"`, `"/api/storage/get"`, `"/api/storage/get-json"`, `"/api/storage/delete"`, `"/api/storage/list"`
- **Health/Status**: `"/api/health/"`, `"/api/status/{processing_id}"`

### High-level approach
- Lift the core logic out of Django views by reusing processors directly:
  - `converter.CompactExcelProcessor`, `converter.ComplexityPreservingCompactProcessor`, `converter.CompactTableProcessor`, `converter.ExcelComplexityAnalyzer`
  - `converter.PDF_processing_pdfplumber.PDFProcessor`, `pdf_table_removal_processor.PDFTableRemovalProcessor`, `converter.PDFAIFailoverPipeline`
  - `converter.storage_service` and `converter.processing_registry`
- Replace Django `request/response` with FastAPI equivalents while keeping identical routes and payload shapes.
- Serve the existing HTML files directly to preserve the UI.

### FastAPI project layout (side-by-side with Django)
```
fastapi_service/
  main.py
  routers/
    ui.py              # "/", "/excel/", "/pdf/"
    excel.py           # Excel endpoints
    pdf.py             # PDF endpoints
    storage.py         # Storage endpoints
    status.py          # Health + processing status
  deps.py              # shared helpers (storage, errors, etc.)
```

### Minimal app bootstrap
```python
# fastapi_service/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import ui, excel, pdf, storage, status

app = FastAPI(title="Excel/PDF Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ui.router)
app.include_router(excel.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")
app.include_router(storage.router, prefix="/api/storage")
app.include_router(status.router, prefix="/api")
```

### UI routes (preserve current HTML)
```python
# fastapi_service/routers/ui.py
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/", include_in_schema=False)
def main_landing():
    return FileResponse("converter/templates/converter/main_landing.html")

@router.get("/excel/", include_in_schema=False)
def excel_page():
    return FileResponse("converter/templates/converter/excel_processor.html")

@router.get("/pdf/", include_in_schema=False)
def pdf_page():
    return FileResponse("converter/templates/converter/pdf_processor.html")
```

### Example: Excel upload (maps Django logic to FastAPI)
```python
# fastapi_service/routers/excel.py
import os, json, uuid, tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from converter.complexity_preserving_compact_processor import ComplexityPreservingCompactProcessor
from converter.compact_table_processor import CompactTableProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer
from converter.storage_service import get_storage_service, StorageType
from converter.processing_registry import processing_registry

router = APIRouter()

@router.post("/upload/")
async def upload_and_convert(
    file: UploadFile = File(...),
    enable_comparison: bool = Form(False),
    enable_ai_analysis: bool = Form(False),
):
    allowed_ext = {".xlsx", ".xlsm", ".xltx", ".xltm"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_ext:
        raise HTTPException(400, f"Unsupported file format. Allowed: {', '.join(sorted(allowed_ext))}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        processor = ComplexityPreservingCompactProcessor(enable_rle=True)
        json_data = processor.process_file(full_path, filter_empty_trailing=True, include_complexity_metadata=True)

        analyzer = ExcelComplexityAnalyzer()
        complexity_results = {}
        meta_by_sheet = json_data.get("complexity_metadata", {}).get("sheets", {})
        for sheet in json_data.get("workbook", {}).get("sheets", []):
            name = sheet.get("name", "Unknown")
            complexity_results[name] = analyzer.analyze_sheet_complexity(sheet, complexity_metadata=meta_by_sheet.get(name))

        table_processor = CompactTableProcessor()
        table_data = table_processor.transform_to_compact_table_format(json_data, {
            "enable_comparison": enable_comparison,
            "enable_ai_analysis": enable_ai_analysis,
            "complexity_results": complexity_results,
        })
        table_data["complexity_analysis"] = complexity_results

        use_storage = os.getenv("USE_STORAGE_SERVICE", "false").lower() == "true"
        storage = get_storage_service() if use_storage else None
        processing_id = str(uuid.uuid4())
        response_storage = None
        if storage:
            try:
                with open(full_path, "rb") as f:
                    original_ref = storage.store_file(
                        data=f.read(),
                        storage_type=StorageType.ORIGINAL_FILE,
                        filename=file.filename,
                        metadata={"processing_id": processing_id},
                    )
                full_ref = storage.store_json(data=json_data, storage_type=StorageType.PROCESSED_JSON, key_prefix=processing_id)
                table_ref = storage.store_json(data=table_data, storage_type=StorageType.TABLE_DATA, key_prefix=processing_id)
                response_storage = {
                    "processing_id": processing_id,
                    "original_file": original_ref.__dict__,
                    "processed_json": full_ref.__dict__,
                    "table_data": table_ref.__dict__,
                    "download_urls": {
                        "original_file": storage.get_download_url(original_ref),
                        "processed_json": storage.get_download_url(full_ref),
                        "table_data": storage.get_download_url(table_ref),
                    },
                }
            except Exception:
                response_storage = None

        processing_registry.register(processing_id, {"filename": file.filename, "type": "excel", "storage": response_storage, "large_file": False})

        return JSONResponse({
            "success": True,
            "format": "compact",
            "filename": file.filename,
            "large_file": False,
            "data": json_data,
            "table_data": table_data,
            "storage": response_storage,
            "processing_id": processing_id,
        })
    finally:
        try: os.remove(full_path)
        except: pass
```

Use the same mapping pattern to port:
- Excel: `download_json`, `transform_to_tables`, `resolve_headers`, `analyze_excel_complexity`, `excel_comparison_analysis`.
- PDF: `upload_and_process_pdf`, `process_pdf_with_options`, `upload_and_process_pdf_with_table_removal`, `upload_and_process_pdf_ai_failover`, `get_processing_status`.
- Storage: mirror all endpoints in `converter/storage_views.py`.

### Environment and storage notes
- `converter.storage_service.LocalStorageService` references `django.conf.settings.MEDIA_ROOT` by default. In FastAPI, set `"LOCAL_STORAGE_PATH"` to avoid importing Django settings:
  - `LOCAL_STORAGE_PATH=/tmp/excel-json-storage` (or another absolute path)
- Optional S3 via the same module: set `STORAGE_BACKEND=s3` and `S3_BUCKET_NAME`, plus AWS creds/endpoint if needed.

### Static files and templates
- Mount `"/static"` from the repo’s `static/` directory.
- Serve existing HTML files directly from `converter/templates/converter/` to keep the UI intact. If server-side templating is needed later, use `Jinja2Templates`.

### CORS
- Enable CORS in `main.py`. Restrict `allow_origins` to trusted domains in production.

### Running locally
1. Install packages:
   - `pip install fastapi uvicorn[standard] python-multipart jinja2 boto3` (boto3 optional)
2. Env vars:
   - `LOCAL_STORAGE_PATH=/tmp/excel-json-storage`
   - Optional: `USE_STORAGE_SERVICE=true`, `STORAGE_BACKEND=local|s3`
3. Start:
   - From repo root: `uvicorn fastapi_service.main:app --host 0.0.0.0 --port 8000`

### Transitional deployment options
- Run FastAPI and Django side-by-side; reverse proxy `/api` to FastAPI and `/` to Django to decouple migration.
- Or replace Django entirely with FastAPI, which also serves the UI pages and static assets.

### Testing
- Reuse existing fixtures and add FastAPI tests with `TestClient`, mirroring current responses.
- Keep route shapes and response fields consistent so existing front-end behavior remains unchanged.

### Checklist
- [ ] Create `fastapi_service/` scaffold and routers
- [ ] Port UI routes
- [ ] Port Excel/PDF/Storage APIs
- [ ] Set `LOCAL_STORAGE_PATH` for storage service
- [ ] Add CORS and mount `static/`
- [ ] Add unit tests with FastAPI `TestClient`
- [ ] Configure production workers and reverse proxy


