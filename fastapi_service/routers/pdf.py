import os
import json
import uuid
import tempfile
from typing import Any, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from converter.storage_service import get_storage_service, StorageService, StorageType
from converter.processing_registry import processing_registry

# Import processors
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PDF_processing_pdfplumber import PDFProcessor  # type: ignore
from pdf_table_removal_processor import PDFTableRemovalProcessor  # type: ignore
from converter.pdf_ai_failover_pipeline import PDFAIFailoverPipeline

router = APIRouter()


@router.post("/pdf/upload/")
async def upload_and_process_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        processor = PDFTableRemovalProcessor()
        result = processor.process(full_path)

        use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
        storage: StorageService | None = get_storage_service() if use_storage_service else None
        processing_id = str(uuid.uuid4()) if use_storage_service else None
        response_storage = None
        if storage is not None and processing_id is not None:
            try:
                with open(full_path, 'rb') as f:
                    original_bytes = f.read()
                original_ref = storage.store_file(
                    data=original_bytes,
                    storage_type=StorageType.ORIGINAL_FILE,
                    filename=file.filename,
                    metadata={'processing_id': processing_id, 'type': 'pdf'}
                )
                result_ref = storage.store_json(
                    data=result,
                    storage_type=StorageType.PROCESSED_JSON,
                    key_prefix=f"{processing_id}"
                )
                response_storage = {
                    'processing_id': processing_id,
                    'original_file': original_ref.__dict__,
                    'processed_json': result_ref.__dict__,
                    'download_urls': {
                        'original_file': storage.get_download_url(original_ref),
                        'processed_json': storage.get_download_url(result_ref),
                    }
                }
            except Exception:
                response_storage = None

        if response_storage is not None and processing_id is not None:
            try:
                processing_registry.register(processing_id, {
                    'filename': file.filename,
                    'type': 'pdf',
                    'storage': response_storage,
                    'format': 'verbose',
                    'mode': 'table_removal',
                })
            except Exception:
                pass

        return JSONResponse({
            'success': True,
            'format': 'verbose',
            'processing_mode': 'table_removal',
            'result': result,
            'filename': file.filename,
            'storage': response_storage
        })
    finally:
        try:
            os.remove(full_path)
        except Exception:
            pass


@router.post("/pdf/table-removal/")
async def upload_and_process_pdf_table_removal(file: UploadFile = File(...)):
    return await upload_and_process_pdf(file)


@router.post("/pdf/ai-failover/")
async def upload_and_process_pdf_ai_failover(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        pipeline = PDFAIFailoverPipeline()
        result = pipeline.process(full_path)

        use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
        storage: StorageService | None = get_storage_service() if use_storage_service else None
        processing_id = str(uuid.uuid4()) if use_storage_service else None
        response_storage = None
        if storage is not None and processing_id is not None:
            try:
                with open(full_path, 'rb') as f:
                    original_bytes = f.read()
                original_ref = storage.store_file(
                    data=original_bytes,
                    storage_type=StorageType.ORIGINAL_FILE,
                    filename=file.filename,
                    metadata={'processing_id': processing_id, 'type': 'pdf'}
                )
                result_ref = storage.store_json(
                    data=result,
                    storage_type=StorageType.PROCESSED_JSON,
                    key_prefix=f"{processing_id}"
                )
                response_storage = {
                    'processing_id': processing_id,
                    'original_file': original_ref.__dict__,
                    'processed_json': result_ref.__dict__,
                    'download_urls': {
                        'original_file': storage.get_download_url(original_ref),
                        'processed_json': storage.get_download_url(result_ref),
                    }
                }
            except Exception:
                response_storage = None

        if response_storage is not None and processing_id is not None:
            try:
                processing_registry.register(processing_id, {
                    'filename': file.filename,
                    'type': 'pdf',
                    'storage': response_storage,
                    'mode': 'ai_failover_routing',
                })
            except Exception:
                pass

        return JSONResponse({
            'success': True,
            'processing_mode': 'ai_failover_routing',
            'result': result,
            'filename': file.filename,
            'storage': response_storage
        })
    finally:
        try:
            os.remove(full_path)
        except Exception:
            pass


@router.get("/pdf/status/")
def get_processing_status():
    try:
        _ = PDFProcessor()
        return {
            'success': True,
            'status': 'available',
            'supported_formats': ['pdf'],
            'supported_output_formats': ['verbose', 'compact'],
            'capabilities': {
                'table_extraction': True,
                'text_extraction': True,
                'number_extraction': True,
                'multi_page_support': True,
                'quality_scoring': True
            }
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/pdf/process/")
def process_pdf_with_options(payload: Dict[str, Any]):
    data = payload
    format_type = data.get('format', 'verbose').lower()
    use_compact = format_type == 'compact'

    if 'file_path' not in data:
        raise HTTPException(400, 'File path is required')
    file_path = data['file_path']
    config = data.get('config', {})
    extract_tables = data.get('extract_tables', True)
    extract_text = data.get('extract_text', True)
    extract_numbers = data.get('extract_numbers', True)

    try:
        processor = PDFProcessor(config)
        result = processor.process_file(
            file_path,
            extract_tables=extract_tables,
            extract_text=extract_text,
            extract_numbers=extract_numbers
        )
        # No extra compression implemented here; parity with Django is optional
        result_size = len(json.dumps(result))
        response_data = {
            'success': True,
            'format': format_type,
            'result': result,
            'file_info': { 'result_size_mb': result_size / 1024 / 1024 }
        }
        return JSONResponse(response_data)
    except Exception as e:
        raise HTTPException(500, f'Processing failed: {str(e)}')


