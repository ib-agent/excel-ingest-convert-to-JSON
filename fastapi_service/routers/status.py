from fastapi import APIRouter
from fastapi.responses import JSONResponse
from converter.processing_registry import processing_registry

router = APIRouter()


@router.get("/health/")
def health_check():
    return {"status": "healthy", "service": "Excel to JSON Converter", "version": "1.0.0"}


@router.get("/status/{processing_id}/")
def get_status(processing_id: str):
    rec = processing_registry.get(processing_id)
    if rec is None:
        return JSONResponse({"processing_id": processing_id, "status": "not_found"}, status_code=404)
    return JSONResponse({"processing_id": processing_id, **rec}, status_code=200)


