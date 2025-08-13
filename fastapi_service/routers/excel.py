import os
import json
import uuid
import tempfile
from typing import Any, Dict, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from converter.complexity_preserving_compact_processor import ComplexityPreservingCompactProcessor
from converter.compact_table_processor import CompactTableProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer
from converter.storage_service import get_storage_service, StorageType
from converter.processing_registry import processing_registry
from converter import models as django_like_models

router = APIRouter()


def _is_rle_cell(cell: list) -> bool:
    return isinstance(cell, list) and len(cell) >= 5 and isinstance(cell[-1], int) and cell[-1] > 1


def _is_numeric(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


def _estimate_total_cells_from_workbook(workbook: dict) -> int:
    total_cells = 0
    try:
        sheets = (workbook or {}).get('sheets', [])
        for sheet in sheets:
            if isinstance(sheet.get('cells'), dict):
                total_cells += len(sheet.get('cells', {}))
                continue
            rows = sheet.get('rows') or []
            for row in rows:
                total_cells += len(row.get('cells') or [])
    except Exception:
        total_cells = 0
    return total_cells


def _estimate_total_numeric_cells_from_workbook(workbook: dict) -> int:
    total_numeric = 0
    try:
        sheets = (workbook or {}).get('sheets', [])
        for sheet in sheets:
            if isinstance(sheet.get('cells'), dict):
                for cell in sheet['cells'].values():
                    value = cell.get('value') if isinstance(cell, dict) else None
                    if _is_numeric(value):
                        total_numeric += 1
                continue
            rows = sheet.get('rows') or []
            for row in rows:
                for cell in row.get('cells', []):
                    if not isinstance(cell, list) or len(cell) < 2:
                        continue
                    value = cell[1]
                    if _is_numeric(value):
                        if _is_rle_cell(cell):
                            total_numeric += max(int(cell[-1]), 0)
                        else:
                            total_numeric += 1
    except Exception:
        total_numeric = 0
    return total_numeric


def _estimate_numeric_cells_for_sheet(sheet: dict) -> int:
    numeric = 0
    try:
        if isinstance(sheet.get('cells'), dict):
            for cell in sheet['cells'].values():
                value = cell.get('value') if isinstance(cell, dict) else None
                if _is_numeric(value):
                    numeric += 1
            return numeric
        for row in sheet.get('rows', []) or []:
            for cell in row.get('cells', []) or []:
                if not isinstance(cell, list) or len(cell) < 2:
                    continue
                value = cell[1]
                if _is_numeric(value):
                    if _is_rle_cell(cell):
                        numeric += max(int(cell[-1]), 0)
                    else:
                        numeric += 1
    except Exception:
        return numeric
    return numeric


@router.post("/upload/")
async def upload_and_convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enable_comparison: bool = Form(False),
    enable_ai_analysis: bool = Form(False),
    async_mode: bool = Form(False),
    callback_url: Optional[str] = Form(None),
    pubsub_provider: Optional[str] = Form(None),
    pubsub_topic: Optional[str] = Form(None),
):
    allowed_ext = {".xlsx", ".xlsm", ".xltx", ".xltm"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_ext:
        raise HTTPException(400, f"Unsupported file format. Allowed: {', '.join(sorted(allowed_ext))}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        # Support async processing: capture bytes and schedule background task
        if async_mode and background_tasks is not None:
            with open(full_path, "rb") as f:
                file_bytes = f.read()

            use_storage = os.getenv("USE_STORAGE_SERVICE", "false").lower() == "true"
            storage = get_storage_service() if use_storage else None
            processing_id = str(uuid.uuid4())

            # Optionally store original file reference
            response_storage = None
            if storage:
                try:
                    original_ref = storage.store_file(
                        data=file_bytes,
                        storage_type=StorageType.ORIGINAL_FILE,
                        filename=file.filename,
                        metadata={"processing_id": processing_id},
                    )
                    response_storage = {"processing_id": processing_id, "original_file": original_ref.__dict__}
                except Exception:
                    response_storage = None

            try:
                processing_registry.register(processing_id, {
                    'filename': file.filename,
                    'type': 'excel',
                    'status': 'processing',
                    **({'storage': response_storage} if response_storage else {}),
                })
            except Exception:
                pass

            def _bg_task():
                from fastapi_service.notification_sender import send_notifications
                # Write bytes to a temp file for processor
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as t2:
                    t2.write(file_bytes)
                    path2 = t2.name
                # Reuse existing sync logic by invoking processor inline
                try:
                    processor = ComplexityPreservingCompactProcessor(enable_rle=True)
                    json_data_local = processor.process_file(path2, filter_empty_trailing=True, include_complexity_metadata=True)

                    analyzer = ExcelComplexityAnalyzer()
                    complexity_results_local: Dict[str, Any] = {}
                    meta_by_sheet = json_data_local.get("complexity_metadata", {}).get("sheets", {})
                    for sheet in json_data_local.get("workbook", {}).get("sheets", []):
                        name = sheet.get("name", "Unknown")
                        complexity_results_local[name] = analyzer.analyze_sheet_complexity(sheet, complexity_metadata=meta_by_sheet.get(name))

                    table_processor = CompactTableProcessor()
                    table_data_local = table_processor.transform_to_compact_table_format(json_data_local, {
                        "enable_comparison": enable_comparison,
                        "enable_ai_analysis": enable_ai_analysis,
                        "complexity_results": complexity_results_local,
                    })
                    table_data_local["complexity_analysis"] = complexity_results_local

                    total_cells = _estimate_total_cells_from_workbook(json_data_local.get('workbook', {}))
                    total_numeric_cells = _estimate_total_numeric_cells_from_workbook(json_data_local.get('workbook', {}))
                    estimated_size = total_cells * 200

                    use_storage_local = os.getenv("USE_STORAGE_SERVICE", "false").lower() == "true"
                    storage_local = get_storage_service() if use_storage_local else None
                    response_storage_local = None
                    file_id_local = None
                    download_urls_local = None

                    if estimated_size > 5 * 1024 * 1024:
                        summary_data = {'workbook': {'meta': json_data_local.get('workbook', {}).get('meta', {}), 'sheets': []}}
                        for sheet in json_data_local.get('workbook', {}).get('sheets', []):
                            tables = sheet.get('tables', [])
                            sheet_summary = {
                                'name': sheet.get('name', 'Unknown'),
                                'table_count': len(tables),
                                'total_rows': sum(len(t.get('labels', {}).get('rows', [])) for t in tables),
                                'total_columns': sum(len(t.get('labels', {}).get('cols', [])) for t in tables),
                                'numeric_cells': _estimate_numeric_cells_for_sheet(sheet),
                            }
                            summary_data['workbook']['sheets'].append(sheet_summary)

                        if storage_local:
                            try:
                                full_ref = storage_local.store_json(data=json_data_local, storage_type=StorageType.PROCESSED_JSON, key_prefix=f"{processing_id}")
                                table_ref = storage_local.store_json(data=table_data_local, storage_type=StorageType.TABLE_DATA, key_prefix=f"{processing_id}")
                                response_storage_local = {
                                    'processing_id': processing_id,
                                    'processed_json': full_ref.__dict__,
                                    'table_data': table_ref.__dict__,
                                    'download_urls': {
                                        'processed_json': storage_local.get_download_url(full_ref),
                                        'table_data': storage_local.get_download_url(table_ref),
                                    }
                                }
                            except Exception:
                                response_storage_local = None
                            download_urls_local = { 'full_data': None, 'table_data': None }
                        else:
                            file_id_local = str(uuid.uuid4())
                            django_like_models.processed_data_cache[file_id_local] = {
                                'full_data': json_data_local,
                                'table_data': table_data_local,
                                'filename': file.filename,
                                'format': 'compact',
                            }
                            download_urls_local = {
                                'full_data': f'/api/download/?type=full&file_id={file_id_local}',
                                'table_data': f'/api/download/?type=table&file_id={file_id_local}',
                            }

                        processing_registry.register(processing_id, {
                            'filename': file.filename,
                            'type': 'excel',
                            'storage': response_storage_local,
                            'size_estimated_bytes': estimated_size,
                            'large_file': True,
                            'summary': {
                                **summary_data,
                                'workbook': { **summary_data['workbook'], 'total_numeric_cells': total_numeric_cells }
                            },
                            **({ 'file_id': file_id_local, 'download_urls': download_urls_local } if not storage_local else {}),
                            'status': 'completed',
                        })
                    else:
                        if not storage_local:
                            try:
                                file_id_local = str(uuid.uuid4())
                                django_like_models.processed_data_cache[file_id_local] = {
                                    'full_data': json_data_local,
                                    'table_data': table_data_local,
                                    'filename': file.filename,
                                    'format': 'compact',
                                }
                                download_urls_local = {
                                    'full_data': f'/api/download/?type=full&file_id={file_id_local}',
                                    'table_data': f'/api/download/?type=table&file_id={file_id_local}',
                                }
                            except Exception:
                                file_id_local = None
                                download_urls_local = None

                        if storage_local:
                            try:
                                full_ref = storage_local.store_json(data=json_data_local, storage_type=StorageType.PROCESSED_JSON, key_prefix=f"{processing_id}")
                                table_ref = storage_local.store_json(data=table_data_local, storage_type=StorageType.TABLE_DATA, key_prefix=f"{processing_id}")
                                response_storage_local = {
                                    'processing_id': processing_id,
                                    'processed_json': full_ref.__dict__,
                                    'table_data': table_ref.__dict__,
                                    'download_urls': {
                                        'processed_json': storage_local.get_download_url(full_ref),
                                        'table_data': storage_local.get_download_url(table_ref),
                                    }
                                }
                            except Exception:
                                response_storage_local = None

                        processing_registry.register(processing_id, {
                            'filename': file.filename,
                            'type': 'excel',
                            'storage': response_storage_local,
                            'size_actual_bytes': len(json.dumps(json_data_local, default=str)) + len(json.dumps(table_data_local, default=str)),
                            'large_file': False,
                            **({ 'file_id': file_id_local, 'download_urls': download_urls_local } if not storage_local and file_id_local else {}),
                            'status': 'completed',
                        })
                finally:
                    try:
                        os.remove(path2)
                    except Exception:
                        pass

                # Send notifications with the final record
                final_rec = processing_registry.get(processing_id) or {'processing_id': processing_id, 'type': 'excel', 'status': 'completed'}
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
                    'meta': f'/api/results/{processing_id}/meta',
                }
            }, status_code=202)
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

        # Large-file parity behavior
        total_cells = _estimate_total_cells_from_workbook(json_data.get('workbook', {}))
        total_numeric_cells = _estimate_total_numeric_cells_from_workbook(json_data.get('workbook', {}))
        estimated_size = total_cells * 200  # rough bytes per cell
        LARGE_FILE_THRESHOLD = 5 * 1024 * 1024

        use_storage = os.getenv("USE_STORAGE_SERVICE", "false").lower() == "true"
        storage = get_storage_service() if use_storage else None
        processing_id = str(uuid.uuid4())
        response_storage = None
        original_ref = None
        if storage:
            try:
                with open(full_path, "rb") as f:
                    original_ref = storage.store_file(
                        data=f.read(),
                        storage_type=StorageType.ORIGINAL_FILE,
                        filename=file.filename,
                        metadata={"processing_id": processing_id},
                    )
            except Exception:
                original_ref = None

        if estimated_size > LARGE_FILE_THRESHOLD:
            # Build summary only
            summary_data = {'workbook': {'meta': json_data.get('workbook', {}).get('meta', {}), 'sheets': []}}
            sheets = json_data.get('workbook', {}).get('sheets', [])
            for sheet in sheets:
                tables = sheet.get('tables', [])
                sheet_summary = {
                    'name': sheet.get('name', 'Unknown'),
                    'table_count': len(tables),
                    'total_rows': sum(len(t.get('labels', {}).get('rows', [])) for t in tables),
                    'total_columns': sum(len(t.get('labels', {}).get('cols', [])) for t in tables),
                    'numeric_cells': _estimate_numeric_cells_for_sheet(sheet),
                }
                summary_data['workbook']['sheets'].append(sheet_summary)

            # Store full results if storage is configured
            if storage:
                try:
                    full_ref = storage.store_json(data=json_data, storage_type=StorageType.PROCESSED_JSON, key_prefix=f"{processing_id}")
                    table_ref = storage.store_json(data=table_data, storage_type=StorageType.TABLE_DATA, key_prefix=f"{processing_id}")
                    response_storage = {
                        'processing_id': processing_id,
                        'original_file': original_ref.__dict__ if original_ref else None,
                        'processed_json': full_ref.__dict__,
                        'table_data': table_ref.__dict__,
                        'download_urls': {
                            'original_file': storage.get_download_url(original_ref) if original_ref else None,
                            'processed_json': storage.get_download_url(full_ref),
                            'table_data': storage.get_download_url(table_ref),
                        }
                    }
                except Exception:
                    response_storage = None
                download_urls = { 'full_data': None, 'table_data': None }
            else:
                # Legacy in-memory cache
                file_id = str(uuid.uuid4())
                django_like_models.processed_data_cache[file_id] = {
                    'full_data': json_data,
                    'table_data': table_data,
                    'filename': file.filename,
                    'format': 'compact',
                }
                download_urls = {
                    'full_data': f'/api/download/?type=full&file_id={file_id}',
                    'table_data': f'/api/download/?type=table&file_id={file_id}',
                }

            processing_registry.register(processing_id, {
                'filename': file.filename,
                'type': 'excel',
                'storage': response_storage,
                'size_estimated_bytes': estimated_size,
                'large_file': True,
                'summary': {
                    **summary_data,
                    'workbook': { **summary_data['workbook'], 'total_numeric_cells': total_numeric_cells }
                },
                **({ 'file_id': file_id, 'download_urls': download_urls } if not storage else {}),
            })

            estimated_size_mb = estimated_size / 1024 / 1024
            json_data_size_mb = estimated_size_mb
            table_data_size_mb = max(estimated_size_mb * 0.6, 0.0)
            return JSONResponse({
                'success': True,
                'format': 'compact',
                'filename': file.filename,
                'large_file': True,
                'warning': f'File is very large (estimated {estimated_size_mb:.1f} MB). Use download links below.',
                'summary': {
                    **summary_data,
                    'workbook': { **summary_data['workbook'], 'total_numeric_cells': total_numeric_cells }
                },
                'download_urls': download_urls,
                'storage': response_storage,
                'processing_id': processing_id,
                'file_info': {
                    'estimated_size_mb': estimated_size_mb,
                    'json_data_size_mb': json_data_size_mb,
                    'table_data_size_mb': table_data_size_mb,
                    'total_cells': total_cells,
                    'total_numeric_cells': total_numeric_cells,
                    'sheet_count': len(json_data.get('workbook', {}).get('sheets', [])),
                    'total_tables': sum(len(s.get('tables', [])) for s in json_data.get('workbook', {}).get('sheets', []))
                },
                'compression_stats': {
                    'format_used': 'compact',
                    'estimated_verbose_size_mb': estimated_size_mb * 3.5,
                    'estimated_reduction_percent': 70,
                    'rle_enabled': True
                }
            })
        else:
            # Small file: return inline
            try:
                if 'workbook' in json_data:
                    json_data['workbook']['numeric_cell_count'] = _estimate_total_numeric_cells_from_workbook(json_data['workbook'])
                if 'workbook' in table_data:
                    table_data['workbook']['numeric_cell_count'] = json_data['workbook'].get('numeric_cell_count', 0)
            except Exception:
                pass

            # For consistent retrieval later, also cache when storage is not configured
            download_urls = None
            file_id = None
            if not storage:
                try:
                    file_id = str(uuid.uuid4())
                    django_like_models.processed_data_cache[file_id] = {
                        'full_data': json_data,
                        'table_data': table_data,
                        'filename': file.filename,
                        'format': 'compact',
                    }
                    download_urls = {
                        'full_data': f'/api/download/?type=full&file_id={file_id}',
                        'table_data': f'/api/download/?type=table&file_id={file_id}',
                    }
                except Exception:
                    file_id = None
                    download_urls = None

            if storage:
                try:
                    full_ref = storage.store_json(data=json_data, storage_type=StorageType.PROCESSED_JSON, key_prefix=f"{processing_id}")
                    table_ref = storage.store_json(data=table_data, storage_type=StorageType.TABLE_DATA, key_prefix=f"{processing_id}")
                    response_storage = {
                        'processing_id': processing_id,
                        'original_file': original_ref.__dict__ if original_ref else None,
                        'processed_json': full_ref.__dict__,
                        'table_data': table_ref.__dict__,
                        'download_urls': {
                            'original_file': storage.get_download_url(original_ref) if original_ref else None,
                            'processed_json': storage.get_download_url(full_ref),
                            'table_data': storage.get_download_url(table_ref),
                        }
                    }
                except Exception:
                    response_storage = None

            processing_registry.register(processing_id, {
                'filename': file.filename,
                'type': 'excel',
                'storage': response_storage,
                'size_actual_bytes': len(json.dumps(json_data, default=str)) + len(json.dumps(table_data, default=str)),
                'large_file': False,
                **({ 'file_id': file_id, 'download_urls': download_urls } if not storage and file_id else {}),
            })

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
        try:
            os.remove(full_path)
        except Exception:
            pass


@router.post("/transform-tables/")
def transform_to_tables(payload: Dict[str, Any]):
    json_data = payload.get("json_data")
    if not json_data:
        raise HTTPException(400, "No JSON data provided")
    options = payload.get("options", {})

    # Detect input schema and delegate appropriately
    # - If compact-style (rows list), use CompactTableProcessor
    # - If table-oriented (cells dict), use TableProcessor
    from converter.table_processor import TableProcessor
    is_compact_input = False
    try:
        sheets = json_data.get("workbook", {}).get("sheets", [])
        if sheets:
            first_sheet = sheets[0]
            # Compact has 'rows' (list of row objects), table-oriented has 'cells' (dict)
            is_compact_input = isinstance(first_sheet.get("rows"), list) and not isinstance(first_sheet.get("cells"), dict)
    except Exception:
        is_compact_input = False

    if is_compact_input:
        table_processor = CompactTableProcessor()
        table_data = table_processor.transform_to_compact_table_format(json_data, options)
    else:
        # Fallback to table-oriented transformation
        tp = TableProcessor()
        table_data = tp.transform_to_table_format(json_data, options)

    original_size = len(json.dumps(json_data))
    compressed_size = len(json.dumps(table_data))
    return {
        "success": True,
        "format": "compact",
        "table_data": table_data,
        "compression_stats": {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "reduction_percent": int((1 - compressed_size / original_size) * 100) if original_size > 0 else 0,
            "rle_enabled": True,
        },
    }


@router.post("/resolve-headers/")
def resolve_headers(payload: Dict[str, Any]):
    table_data = payload.get("table_data")
    if not table_data:
        raise HTTPException(400, "No table data provided")
    # Perform header resolution using TableProcessor's HeaderResolver
    from converter.header_resolver import HeaderResolver
    try:
        resolver = HeaderResolver()
        resolved = resolver.resolve_headers(table_data)
    except Exception:
        # If resolution fails, return original
        resolved = table_data
    return {
        "success": True,
        "format": "compact",
        "resolved_data": resolved,
    }


@router.post("/excel/analyze-complexity/")
async def analyze_excel_complexity(file: UploadFile = File(...)):
    allowed_ext = {".xlsx", ".xlsm", ".xltx", ".xltm"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_ext:
        raise HTTPException(400, f"Unsupported file format. Allowed: {', '.join(sorted(allowed_ext))}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        from converter.compact_excel_processor import CompactExcelProcessor

        processor = CompactExcelProcessor()
        json_data = processor.process_file(full_path)

        analyzer = ExcelComplexityAnalyzer()
        complexity_results: Dict[str, Any] = {}
        recommendations = []
        for sheet in json_data.get("workbook", {}).get("sheets", []):
            name = sheet.get("name", "Unknown")
            analysis = analyzer.analyze_sheet_complexity(sheet)
            complexity_results[name] = analysis
            recommendations.append(analysis.get("recommendation"))

        if "ai_first" in recommendations:
            overall_recommendation = "ai_first"
        elif "dual" in recommendations:
            overall_recommendation = "dual"
        else:
            overall_recommendation = "traditional"

        use_storage = os.getenv("USE_STORAGE_SERVICE", "false").lower() == "true"
        storage = get_storage_service() if use_storage else None
        processing_id = str(uuid.uuid4()) if use_storage else None
        response_storage = None
        if storage is not None and processing_id is not None:
            try:
                with open(full_path, "rb") as f:
                    original_bytes = f.read()
                original_ref = storage.store_file(
                    data=original_bytes,
                    storage_type=StorageType.ORIGINAL_FILE,
                    filename=file.filename,
                    metadata={"processing_id": processing_id, "type": "excel_complexity"},
                )
                payload = {
                    "success": True,
                    "filename": file.filename,
                    "overall_recommendation": overall_recommendation,
                    "sheet_analysis": complexity_results,
                }
                results_ref = storage.store_json(data=payload, storage_type=StorageType.COMPLEXITY_METADATA, key_prefix=f"{processing_id}")
                response_storage = {
                    "processing_id": processing_id,
                    "original_file": original_ref.__dict__,
                    "complexity_results": results_ref.__dict__,
                    "download_urls": {
                        "original_file": storage.get_download_url(original_ref),
                        "complexity_results": storage.get_download_url(results_ref),
                    },
                }
                try:
                    processing_registry.register(processing_id, {
                        "filename": file.filename,
                        "type": "excel_complexity",
                        "storage": response_storage,
                    })
                except Exception:
                    pass
            except Exception:
                response_storage = None

        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "overall_recommendation": overall_recommendation,
            "sheet_analysis": complexity_results,
            **({"storage": response_storage, "processing_id": processing_id} if response_storage else {}),
        })
    finally:
        try:
            os.remove(full_path)
        except Exception:
            pass


@router.post("/excel/comparison-analysis/")
async def excel_comparison_analysis(file: UploadFile = File(...)):
    allowed_ext = {".xlsx", ".xlsm", ".xltx", ".xltm"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_ext:
        raise HTTPException(400, f"Unsupported file format. Allowed: {', '.join(sorted(allowed_ext))}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        full_path = tmp.name

    try:
        from converter.compact_excel_processor import CompactExcelProcessor
        from converter.ai_result_parser import AIResultParser
        from converter.anthropic_excel_client import AnthropicExcelClient
        from converter.comparison_engine import ComparisonEngine

        processor = CompactExcelProcessor()
        json_data = processor.process_file(full_path)

        analyzer = ExcelComplexityAnalyzer()
        table_processor = CompactTableProcessor()
        comparison_results: Dict[str, Any] = {}

        for sheet in json_data.get("workbook", {}).get("sheets", []):
            sheet_name = sheet.get("name", "Unknown")
            complexity_analysis = analyzer.analyze_sheet_complexity(sheet)
            traditional_result = table_processor.transform_to_compact_table_format({"workbook": {"sheets": [sheet]}}, {"enable_comparison": False, "enable_ai_analysis": False})

            ai_client = AnthropicExcelClient()
            ai_parser = AIResultParser()
            if ai_client.is_available():
                ai_raw_response = ai_client.analyze_excel_sheet(sheet, complexity_metadata=complexity_analysis, analysis_focus="comprehensive")
                ai_result = ai_parser.parse_excel_analysis(ai_raw_response)
            else:
                ai_result = {
                    'status': 'unavailable',
                    'ai_analysis': {'tables': [], 'sheet_summary': {'total_tables': 0}, 'confidence': 0.0},
                    'table_count': 0,
                }

            comp = ComparisonEngine().compare_analysis_results(traditional_result=traditional_result, ai_result=ai_result, complexity_metadata=complexity_analysis, sheet_name=sheet_name)
            comparison_results[sheet_name] = comp

        use_storage = os.getenv("USE_STORAGE_SERVICE", "false").lower() == "true"
        storage = get_storage_service() if use_storage else None
        processing_id = str(uuid.uuid4()) if use_storage else None
        response_storage = None
        if storage is not None and processing_id is not None:
            try:
                with open(full_path, "rb") as f:
                    original_bytes = f.read()
                original_ref = storage.store_file(data=original_bytes, storage_type=StorageType.ORIGINAL_FILE, filename=file.filename, metadata={"processing_id": processing_id, "type": "excel_comparison"})
                results_ref = storage.store_json(data={"success": True, "filename": file.filename, "comparison_results": comparison_results}, storage_type=StorageType.PROCESSED_JSON, key_prefix=f"{processing_id}")
                response_storage = {
                    "processing_id": processing_id,
                    "original_file": original_ref.__dict__,
                    "comparison_results": results_ref.__dict__,
                    "download_urls": {
                        "original_file": storage.get_download_url(original_ref),
                        "comparison_results": storage.get_download_url(results_ref),
                    },
                }
                try:
                    processing_registry.register(processing_id, {"filename": file.filename, "type": "excel_comparison", "storage": response_storage})
                except Exception:
                    pass
            except Exception:
                response_storage = None

        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "comparison_results": comparison_results,
            **({"storage": response_storage, "processing_id": processing_id} if response_storage else {}),
        })
    finally:
        try:
            os.remove(full_path)
        except Exception:
            pass


@router.get("/download/")
def download_json(type: str = "full", file_id: str = ""):
    cache = getattr(django_like_models, "processed_data_cache", {})
    if not file_id or file_id not in cache:
        return JSONResponse({"error": "File not found or expired"}, status_code=404)
    cached = cache[file_id]
    filename = cached.get("filename", "data.xlsx")
    fmt = cached.get("format", "verbose")
    if type == "full":
        content = json.dumps(cached.get("full_data", {}), indent=2)
        download_filename = f"{os.path.splitext(filename)[0]}_full_data_{fmt}.json"
    else:
        content = json.dumps(cached.get("table_data", {}), indent=2)
        download_filename = f"{os.path.splitext(filename)[0]}_table_data_{fmt}.json"
    headers = {"Content-Disposition": f"attachment; filename=\"{download_filename}\""}
    return Response(content=content, media_type="application/json", headers=headers)


