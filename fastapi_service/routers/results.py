import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from converter.processing_registry import processing_registry
from converter.storage_service import get_storage_service
from converter import models as django_like_models


router = APIRouter()


def _get_record(processing_id: str) -> Dict[str, Any]:
    record = processing_registry.get(processing_id)
    if record is None:
        raise HTTPException(status_code=404, detail="processing_id not found")
    return record


def _get_json_from_storage(key: str) -> Dict[str, Any]:
    storage = get_storage_service()
    try:
        return storage.get_json(key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"stored object not found: {str(e)}")


@router.get("/results/{processing_id}/full")
def get_full_result(processing_id: str):
    record = _get_record(processing_id)
    storage_info: Optional[Dict[str, Any]] = record.get("storage")

    # Prefer storage if available
    if storage_info and storage_info.get("processed_json"):
        key = storage_info["processed_json"].get("key")
        if key:
            obj = _get_json_from_storage(key)
            return JSONResponse({"processing_id": processing_id, "data": obj})

    # Fallback to cache if present
    file_id = record.get("file_id")
    cache = getattr(django_like_models, "processed_data_cache", {})
    if file_id and file_id in cache:
        cached = cache[file_id]
        return JSONResponse({
            "processing_id": processing_id,
            "data": cached.get("full_data"),
            "filename": cached.get("filename"),
            "format": cached.get("format", "verbose"),
        })

    raise HTTPException(status_code=404, detail="full result not available")


@router.get("/results/{processing_id}/table")
def get_table_result(processing_id: str):
    record = _get_record(processing_id)
    storage_info: Optional[Dict[str, Any]] = record.get("storage")

    # Prefer storage if available
    if storage_info:
        table_ref = storage_info.get("table_data")
        if table_ref and table_ref.get("key"):
            obj = _get_json_from_storage(table_ref["key"])
            return JSONResponse({"processing_id": processing_id, "table_data": obj})
        # Fallback for PDF storage which only stores processed_json
        processed_ref = storage_info.get("processed_json")
        if processed_ref and processed_ref.get("key"):
            obj = _get_json_from_storage(processed_ref["key"])
            return JSONResponse({"processing_id": processing_id, "table_data": obj})

    # Fallback to cache
    file_id = record.get("file_id")
    cache = getattr(django_like_models, "processed_data_cache", {})
    if file_id and file_id in cache:
        cached = cache[file_id]
        if "table_data" in cached:
            return JSONResponse({
                "processing_id": processing_id,
                "table_data": cached.get("table_data"),
                "filename": cached.get("filename"),
                "format": cached.get("format", "verbose"),
            })

    raise HTTPException(status_code=404, detail="table result not available")


@router.get("/results/{processing_id}/meta")
def get_meta_result(processing_id: str):
    record = _get_record(processing_id)

    # Prefer summary if present (Excel large file flow populates this now)
    if "summary" in record:
        return JSONResponse({"processing_id": processing_id, "summary": record["summary"]})

    # Try complexity metadata in storage
    storage_info: Optional[Dict[str, Any]] = record.get("storage")
    if storage_info and storage_info.get("complexity_results"):
        key = storage_info["complexity_results"].get("key")
        if key:
            obj = _get_json_from_storage(key)
            return JSONResponse({"processing_id": processing_id, "meta": obj})

    # Nothing else available
    raise HTTPException(status_code=404, detail="metadata not available")


