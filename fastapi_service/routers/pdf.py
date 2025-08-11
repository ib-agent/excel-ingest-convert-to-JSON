import os
import json
import uuid
import tempfile
from typing import Any, Dict, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
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
async def upload_and_process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    async_mode: bool = Form(False),
    callback_url: Optional[str] = Form(None),
    pubsub_provider: Optional[str] = Form(None),
    pubsub_topic: Optional[str] = Form(None),
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        if async_mode and background_tasks is not None:
            with open(full_path, 'rb') as f:
                file_bytes = f.read()

            processing_id = str(uuid.uuid4())
            try:
                processing_registry.register(processing_id, {
                    'filename': file.filename,
                    'type': 'pdf',
                    'status': 'processing',
                    'mode': 'table_removal',
                })
            except Exception:
                pass

            def _bg_task():
                from fastapi_service.notification_sender import send_notifications
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as t2:
                    t2.write(file_bytes)
                    path2 = t2.name
                try:
                    processor_local = PDFTableRemovalProcessor()
                    result_local = processor_local.process(path2)

                    use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
                    storage_local: StorageService | None = get_storage_service() if use_storage_service else None
                    response_storage_local = None
                    file_id_local = None
                    download_urls_local = None

                    if storage_local is not None:
                        try:
                            original_ref = storage_local.store_file(
                                data=file_bytes,
                                storage_type=StorageType.ORIGINAL_FILE,
                                filename=file.filename,
                                metadata={'processing_id': processing_id, 'type': 'pdf'}
                            )
                            result_ref = storage_local.store_json(
                                data=result_local,
                                storage_type=StorageType.PROCESSED_JSON,
                                key_prefix=f"{processing_id}"
                            )
                            response_storage_local = {
                                'processing_id': processing_id,
                                'original_file': original_ref.__dict__,
                                'processed_json': result_ref.__dict__,
                                'download_urls': {
                                    'original_file': storage_local.get_download_url(original_ref),
                                    'processed_json': storage_local.get_download_url(result_ref),
                                }
                            }
                        except Exception:
                            response_storage_local = None
                    else:
                        try:
                            from converter import models as django_like_models
                            file_id_local = str(uuid.uuid4())
                            django_like_models.processed_data_cache[file_id_local] = {
                                'full_data': result_local,
                                'table_data': result_local,
                                'filename': file.filename,
                                'format': 'verbose',
                            }
                            download_urls_local = {
                                'full_data': f'/api/download/?type=full&file_id={file_id_local}',
                                'table_data': f'/api/download/?type=table&file_id={file_id_local}',
                            }
                        except Exception:
                            file_id_local = None
                            download_urls_local = None

                    processing_registry.register(processing_id, {
                        'filename': file.filename,
                        'type': 'pdf',
                        'storage': response_storage_local,
                        'format': 'verbose',
                        'mode': 'table_removal',
                        **({ 'file_id': file_id_local, 'download_urls': download_urls_local } if file_id_local else {}),
                        'status': 'completed',
                    })
                finally:
                    try:
                        os.remove(path2)
                    except Exception:
                        pass
                final_rec = processing_registry.get(processing_id) or {'processing_id': processing_id, 'type': 'pdf', 'status': 'completed'}
                final_rec['processing_id'] = processing_id
                send_notifications(record=final_rec, callback_url=callback_url, pubsub_provider=pubsub_provider, pubsub_topic=pubsub_topic)

            background_tasks.add_task(_bg_task)
            return JSONResponse({
                'accepted': True,
                'processing_id': processing_id,
                'status_endpoint': f'/api/status/{processing_id}/',
                'results_endpoints': {
                    'full': f'/api/results/{processing_id}/full',
                    'table': f'/api/results/{processing_id}/table',
                }
            }, status_code=202)

        processor = PDFTableRemovalProcessor()
        result = processor.process(full_path)

        use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
        storage: StorageService | None = get_storage_service() if use_storage_service else None
        processing_id = str(uuid.uuid4())
        response_storage = None
        file_id = None
        download_urls = None
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
        else:
            # Cache result for retrieval via new results endpoints
            try:
                file_id = str(uuid.uuid4())
                # Reuse the excel cache structure for consistency
                from converter import models as django_like_models
                django_like_models.processed_data_cache[file_id] = {
                    'full_data': result,
                    'table_data': result,  # PDF result has a single structure; map to both keys for consumers
                    'filename': file.filename,
                    'format': 'verbose',
                }
                download_urls = {
                    'full_data': f'/api/download/?type=full&file_id={file_id}',
                    'table_data': f'/api/download/?type=table&file_id={file_id}',
                }
            except Exception:
                file_id = None
                download_urls = None

        if (response_storage is not None) or file_id is not None:
            try:
                processing_registry.register(processing_id, {
                    'filename': file.filename,
                    'type': 'pdf',
                    'storage': response_storage,
                    'format': 'verbose',
                    'mode': 'table_removal',
                    **({ 'file_id': file_id, 'download_urls': download_urls } if file_id else {}),
                })
            except Exception:
                pass

        return JSONResponse({
            'success': True,
            'format': 'verbose',
            'processing_mode': 'table_removal',
            'result': result,
            'filename': file.filename,
            'storage': response_storage,
            'processing_id': processing_id,
        })
    finally:
        try:
            os.remove(full_path)
        except Exception:
            pass


@router.post("/pdf/table-removal/")
async def upload_and_process_pdf_table_removal(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    async_mode: bool = Form(False),
    callback_url: Optional[str] = Form(None),
    pubsub_provider: Optional[str] = Form(None),
    pubsub_topic: Optional[str] = Form(None),
):
    # Fast path: if async requested, delegate to main handler
    if async_mode:
        return await upload_and_process_pdf(
            background_tasks=background_tasks,
            file=file,
            async_mode=async_mode,
            callback_url=callback_url,
            pubsub_provider=pubsub_provider,
            pubsub_topic=pubsub_topic,
        )

    # Sync processing for table removal (used by web UI)
    if not file or not getattr(file, 'filename', '').lower().endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        processor = PDFTableRemovalProcessor()
        result = processor.process(full_path)

        use_storage_service = os.getenv('USE_STORAGE_SERVICE', 'false').lower() == 'true'
        storage: StorageService | None = get_storage_service() if use_storage_service else None
        processing_id = str(uuid.uuid4())
        response_storage = None
        file_id = None
        download_urls = None
        if storage is not None:
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
        else:
            try:
                from converter import models as django_like_models
                file_id = str(uuid.uuid4())
                django_like_models.processed_data_cache[file_id] = {
                    'full_data': result,
                    'table_data': result,
                    'filename': file.filename,
                    'format': 'verbose',
                }
                download_urls = {
                    'full_data': f'/api/download/?type=full&file_id={file_id}',
                    'table_data': f'/api/download/?type=table&file_id={file_id}',
                }
            except Exception:
                file_id = None
                download_urls = None

        try:
            processing_registry.register(processing_id, {
                'filename': file.filename,
                'type': 'pdf',
                'storage': response_storage,
                'format': 'verbose',
                'mode': 'table_removal',
                **({ 'file_id': file_id, 'download_urls': download_urls } if file_id else {}),
                'status': 'completed',
            })
        except Exception:
            pass

        return JSONResponse({
            'success': True,
            'format': 'verbose',
            'processing_mode': 'table_removal',
            'result': result,
            'filename': file.filename,
            'storage': response_storage,
            'processing_id': processing_id,
        })
    finally:
        try:
            os.remove(full_path)
        except Exception:
            pass


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


