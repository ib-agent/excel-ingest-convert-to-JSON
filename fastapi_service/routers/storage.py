import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Response
from fastapi.responses import JSONResponse
import mimetypes
from converter.storage_service import (
    StorageType,
    get_storage_service,
)

router = APIRouter()


@router.post("/store-file/")
async def storage_store_file(file: UploadFile = File(...), storage_type: str = Query(...), metadata: Optional[str] = None):
    if not file:
        raise HTTPException(400, "No file provided")
    try:
        st = StorageType.from_string(storage_type)
    except Exception as e:
        raise HTTPException(400, str(e))

    meta: Dict[str, Any] = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except Exception:
            raise HTTPException(400, "metadata must be valid JSON")

    storage = get_storage_service()
    data = await file.read()
    ref = storage.store_file(data=data, storage_type=st, filename=file.filename, metadata=meta)
    url = storage.get_download_url(ref)
    return JSONResponse({"reference": ref.__dict__, "download_url": url}, status_code=201)


@router.post("/store-json/")
async def storage_store_json(payload: Dict[str, Any]):
    storage_type_str = payload.get("storage_type")
    if not storage_type_str:
        raise HTTPException(400, "storage_type is required")
    try:
        st = StorageType.from_string(storage_type_str)
    except Exception as e:
        raise HTTPException(400, str(e))

    data = payload.get("data")
    if data is None:
        raise HTTPException(400, "data is required")
    key_prefix = payload.get("key_prefix", "")
    metadata = payload.get("metadata", {})

    storage = get_storage_service()
    ref = storage.store_json(data=data, storage_type=st, key_prefix=key_prefix, metadata=metadata)
    url = storage.get_download_url(ref)
    return JSONResponse({"reference": ref.__dict__, "download_url": url}, status_code=201)


@router.get("/get")
def storage_get(key: str = Query(...)):
    storage = get_storage_service()
    try:
        data = storage.get_bytes(key)
    except Exception as e:
        raise HTTPException(404, str(e))
    guessed, _ = mimetypes.guess_type(key)
    return Response(content=data, media_type=guessed or "application/octet-stream")


@router.get("/get-json/")
def storage_get_json(key: str = Query(...)):
    storage = get_storage_service()
    try:
        obj = storage.get_json(key)
    except Exception as e:
        raise HTTPException(404, str(e))
    return {"key": key, "data": obj}


@router.delete("/delete/")
def storage_delete(key: str = Query(...)):
    storage = get_storage_service()
    ok = storage.delete(key)
    return {"deleted": ok, "key": key}


@router.get("/list/")
def storage_list(prefix: str = Query("")):
    storage = get_storage_service()
    refs = storage.list_by_prefix(prefix)
    return {"items": [r.__dict__ for r in refs]}


