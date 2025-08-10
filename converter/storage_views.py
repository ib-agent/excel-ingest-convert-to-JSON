from __future__ import annotations

import base64
import json
from typing import Any, Dict

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.http import urlsafe_base64_decode

from .storage_service import (
    StorageType,
    StorageReference,
    get_storage_service,
)


def _bad_request(message: str) -> HttpResponseBadRequest:
    return HttpResponseBadRequest(json.dumps({"error": message}), content_type="application/json")


@csrf_exempt
@require_http_methods(["POST"])
def storage_store_file(request):
    """Store a binary file and return a reference. Mimics a microservice endpoint.

    Form fields:
      - file: uploaded binary file (required)
      - storage_type: one of StorageType values (required)
      - metadata: optional JSON string of metadata
    """
    try:
        if "file" not in request.FILES:
            return _bad_request("No file provided")
        storage_type_str = request.POST.get("storage_type")
        if not storage_type_str:
            return _bad_request("storage_type is required")
        try:
            storage_type = StorageType.from_string(storage_type_str)
        except Exception as e:
            return _bad_request(str(e))

        metadata_raw = request.POST.get("metadata")
        metadata: Dict[str, Any] = {}
        if metadata_raw:
            try:
                metadata = json.loads(metadata_raw)
            except Exception:
                return _bad_request("metadata must be valid JSON")

        uploaded = request.FILES["file"]
        storage = get_storage_service()
        reference = storage.store_file(
            data=uploaded.read(),
            storage_type=storage_type,
            filename=uploaded.name,
            metadata=metadata,
        )
        download_url = storage.get_download_url(reference)
        payload = {"reference": reference.__dict__, "download_url": download_url}
        return JsonResponse(payload, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def storage_store_json(request):
    """Store JSON and return a reference. Mimics a microservice endpoint.

    JSON body fields:
      - storage_type: one of StorageType values (required)
      - key_prefix: optional string
      - data: object to store (required)
      - metadata: optional object
    """
    try:
        try:
            body = json.loads(request.body.decode("utf-8"))
        except Exception:
            return _bad_request("Body must be valid JSON")

        storage_type_str = body.get("storage_type")
        if not storage_type_str:
            return _bad_request("storage_type is required")
        try:
            storage_type = StorageType.from_string(storage_type_str)
        except Exception as e:
            return _bad_request(str(e))

        data = body.get("data")
        if data is None:
            return _bad_request("data is required")
        key_prefix = body.get("key_prefix", "")
        metadata = body.get("metadata", {})

        storage = get_storage_service()
        reference = storage.store_json(
            data=data,
            storage_type=storage_type,
            key_prefix=key_prefix,
            metadata=metadata,
        )
        download_url = storage.get_download_url(reference)
        payload = {"reference": reference.__dict__, "download_url": download_url}
        return JsonResponse(payload, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def storage_get(request):
    """Download stored content by key. For local storage, serves bytes.

    Query params:
      - key: required storage key
    """
    key = request.GET.get("key")
    if not key:
        return _bad_request("key is required")
    try:
        storage = get_storage_service()
        data = storage.get_bytes(key)
        # naive content type inference by extension
        from mimetypes import guess_type

        content_type = guess_type(key)[0] or "application/octet-stream"
        resp = HttpResponse(data, content_type=content_type)
        resp["Content-Disposition"] = f"attachment; filename={key.split('/')[-1]}"
        return resp
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=404)


@require_http_methods(["GET"])
def storage_get_json(request):
    """Fetch stored JSON by key and return inline JSON."""
    key = request.GET.get("key")
    if not key:
        return _bad_request("key is required")
    try:
        storage = get_storage_service()
        obj = storage.get_json(key)
        return JsonResponse({"key": key, "data": obj}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=404)


@csrf_exempt
@require_http_methods(["DELETE"])
def storage_delete(request):
    """Delete an object by key."""
    key = request.GET.get("key")
    if not key:
        return _bad_request("key is required")
    try:
        storage = get_storage_service()
        ok = storage.delete(key)
        return JsonResponse({"deleted": ok, "key": key}, status=200 if ok else 404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def storage_list(request):
    """List objects under a prefix."""
    prefix = request.GET.get("prefix", "")
    try:
        storage = get_storage_service()
        refs = storage.list_by_prefix(prefix)
        return JsonResponse({"items": [r.__dict__ for r in refs]}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


