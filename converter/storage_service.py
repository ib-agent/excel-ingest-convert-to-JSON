from __future__ import annotations

import json
import os
import uuid
import mimetypes
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Django-free defaulting: prefer env var LOCAL_STORAGE_PATH; otherwise use ./media/storage

try:
    import boto3  # type: ignore
    from botocore.client import Config  # type: ignore
    BOTO3_AVAILABLE = True
except Exception:
    boto3 = None  # type: ignore[assignment]
    Config = None  # type: ignore[assignment]
    BOTO3_AVAILABLE = False


class StorageType(Enum):
    ORIGINAL_FILE = "original"
    PROCESSED_JSON = "processed"
    AI_ANALYSIS = "ai_analysis"
    TABLE_DATA = "table_data"
    COMPLEXITY_METADATA = "complexity"

    @staticmethod
    def from_string(value: str) -> "StorageType":
        normalized = (value or "").strip().lower()
        for st in StorageType:
            if st.value == normalized:
                return st
        raise ValueError(f"Invalid storage type: {value}")


@dataclass
class StorageReference:
    key: str
    storage_type: str
    content_type: str
    size_bytes: int
    created_at: str
    metadata: Dict[str, Any]


class StorageService(ABC):
    @abstractmethod
    def store_file(self, *, data: bytes, storage_type: StorageType, filename: str,
                   metadata: Optional[Dict[str, Any]] = None) -> StorageReference:
        raise NotImplementedError

    @abstractmethod
    def store_json(self, *, data: Dict[str, Any], storage_type: StorageType, key_prefix: str,
                   metadata: Optional[Dict[str, Any]] = None) -> StorageReference:
        raise NotImplementedError

    @abstractmethod
    def get_download_url(self, reference: StorageReference, expires_in: int = 3600) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_bytes(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def get_json(self, key: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_by_prefix(self, prefix: str) -> List[StorageReference]:
        raise NotImplementedError


class LocalStorageService(StorageService):
    """Filesystem-backed storage for local development."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.getenv("LOCAL_STORAGE_PATH")
        if base_dir is None:
            # default under local media directory
            base_dir = str(Path("media") / "storage")
        self.base_path = Path(base_dir).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _full_path_for_key(self, key: str) -> Path:
        path = self.base_path / key
        # Prevent path traversal
        resolved = path.resolve()
        if not str(resolved).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid key path")
        return resolved

    def _guess_content_type(self, filename: str) -> str:
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"

    def _build_reference(self, key: str, storage_type: StorageType, content_type: str,
                         size_bytes: int, metadata: Optional[Dict[str, Any]]) -> StorageReference:
        created_at = datetime.now(timezone.utc).isoformat()
        return StorageReference(
            key=key,
            storage_type=storage_type.value,
            content_type=content_type,
            size_bytes=size_bytes,
            created_at=created_at,
            metadata=metadata or {},
        )

    def store_file(self, *, data: bytes, storage_type: StorageType, filename: str,
                   metadata: Optional[Dict[str, Any]] = None) -> StorageReference:
        key = f"{storage_type.value}/{uuid.uuid4()}/{filename}"
        full_path = self._full_path_for_key(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        content_type = self._guess_content_type(filename)
        return self._build_reference(key, storage_type, content_type, len(data), metadata)

    def store_json(self, *, data: Dict[str, Any], storage_type: StorageType, key_prefix: str,
                   metadata: Optional[Dict[str, Any]] = None) -> StorageReference:
        filename = "data.json"
        key = f"{storage_type.value}/{uuid.uuid4()}/{key_prefix.rstrip('/')}/{filename}" if key_prefix else f"{storage_type.value}/{uuid.uuid4()}/{filename}"
        full_path = self._full_path_for_key(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(data, separators=(",", ":")).encode("utf-8")
        with open(full_path, "wb") as f:
            f.write(encoded)
        return self._build_reference(key, storage_type, "application/json", len(encoded), metadata)

    def get_download_url(self, reference: StorageReference, expires_in: int = 3600) -> str:
        # For local, expose an internal API route that serves the bytes
        return f"/api/storage/get?key={reference.key}"

    def get_bytes(self, key: str) -> bytes:
        full_path = self._full_path_for_key(key)
        with open(full_path, "rb") as f:
            return f.read()

    def get_json(self, key: str) -> Dict[str, Any]:
        raw = self.get_bytes(key)
        return json.loads(raw.decode("utf-8"))

    def delete(self, key: str) -> bool:
        full_path = self._full_path_for_key(key)
        if full_path.exists():
            full_path.unlink()
            # attempt to remove empty parent directories up to base_path
            parent = full_path.parent
            try:
                while parent != self.base_path and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
            except Exception:
                pass
            return True
        return False

    def list_by_prefix(self, prefix: str) -> List[StorageReference]:
        target_dir = self._full_path_for_key(prefix)
        if not target_dir.exists():
            return []
        references: List[StorageReference] = []
        base_resolved = self.base_path.resolve()
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                rel_key = str(file_path.resolve().relative_to(base_resolved))
                stats = file_path.stat()
                references.append(
                    StorageReference(
                        key=rel_key,
                        storage_type=rel_key.split("/", 1)[0] if "/" in rel_key else "unknown",
                        content_type=mimetypes.guess_type(file_path.name)[0] or "application/octet-stream",
                        size_bytes=stats.st_size,
                        created_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
                        metadata={},
                    )
                )
        return references


class S3StorageService(StorageService):
    """S3-backed storage for cloud deployment. Supports LocalStack via AWS_ENDPOINT_URL."""

    def __init__(self, bucket_name: str, region: Optional[str] = None, endpoint_url: Optional[str] = None) -> None:
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 is required for S3StorageService but is not installed.")

        region_name = region or os.getenv("AWS_REGION", "us-east-1")
        session_kwargs: Dict[str, Any] = {}
        client_kwargs: Dict[str, Any] = {"region_name": region_name}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
            client_kwargs["config"] = Config(s3={"addressing_style": "path"}) if Config else None

        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", **client_kwargs)  # type: ignore[call-arg]

        # Ensure bucket exists (idempotent for LocalStack; in AWS this should be provisioned via IaC)
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except Exception:
            try:
                self.s3.create_bucket(Bucket=self.bucket_name)
            except Exception:
                # Ignore if no permissions; assume bucket exists
                pass

    def _guess_content_type(self, filename: str) -> str:
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"

    def store_file(self, *, data: bytes, storage_type: StorageType, filename: str,
                   metadata: Optional[Dict[str, Any]] = None) -> StorageReference:
        key = f"{storage_type.value}/{uuid.uuid4()}/{filename}"
        content_type = self._guess_content_type(filename)
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata={k: str(v) for k, v in (metadata or {}).items()},
        )
        return StorageReference(
            key=key,
            storage_type=storage_type.value,
            content_type=content_type,
            size_bytes=len(data),
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

    def store_json(self, *, data: Dict[str, Any], storage_type: StorageType, key_prefix: str,
                   metadata: Optional[Dict[str, Any]] = None) -> StorageReference:
        body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        filename = "data.json"
        key = f"{storage_type.value}/{uuid.uuid4()}/{key_prefix.rstrip('/')}/{filename}" if key_prefix else f"{storage_type.value}/{uuid.uuid4()}/{filename}"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body,
            ContentType="application/json",
            Metadata={k: str(v) for k, v in (metadata or {}).items()},
        )
        return StorageReference(
            key=key,
            storage_type=storage_type.value,
            content_type="application/json",
            size_bytes=len(body),
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

    def get_download_url(self, reference: StorageReference, expires_in: int = 3600) -> str:
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": reference.key},
            ExpiresIn=expires_in,
        )

    def get_bytes(self, key: str) -> bytes:
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
        return obj["Body"].read()

    def get_json(self, key: str) -> Dict[str, Any]:
        return json.loads(self.get_bytes(key).decode("utf-8"))

    def delete(self, key: str) -> bool:
        self.s3.delete_object(Bucket=self.bucket_name, Key=key)
        return True

    def list_by_prefix(self, prefix: str) -> List[StorageReference]:
        results: List[StorageReference] = []
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for item in page.get("Contents", []) or []:
                key = item["Key"]
                results.append(
                    StorageReference(
                        key=key,
                        storage_type=key.split("/", 1)[0] if "/" in key else "unknown",
                        content_type=mimetypes.guess_type(key)[0] or "application/octet-stream",
                        size_bytes=int(item.get("Size", 0)),
                        created_at=datetime.now(timezone.utc).isoformat(),
                        metadata={},
                    )
                )
        return results


def get_storage_service() -> StorageService:
    """Factory that returns the configured storage service.

    Configuration via environment variables:
    - STORAGE_BACKEND: 'local' (default) or 's3'
    - LOCAL_STORAGE_PATH: filesystem base path for local storage
    - S3_BUCKET_NAME: required when STORAGE_BACKEND='s3'
    - AWS_REGION: region name (default 'us-east-1')
    - AWS_ENDPOINT_URL: optional, for LocalStack/testing
    """
    backend = os.getenv("STORAGE_BACKEND", "local").strip().lower()
    if backend == "local":
        return LocalStorageService(base_dir=os.getenv("LOCAL_STORAGE_PATH"))
    if backend == "s3":
        bucket = os.getenv("S3_BUCKET_NAME")
        if not bucket:
            raise RuntimeError("S3_BUCKET_NAME must be set when STORAGE_BACKEND=s3")
        region = os.getenv("AWS_REGION", "us-east-1")
        endpoint = os.getenv("AWS_ENDPOINT_URL")
        return S3StorageService(bucket_name=bucket, region=region, endpoint_url=endpoint)
    raise RuntimeError(f"Unsupported STORAGE_BACKEND: {backend}")


