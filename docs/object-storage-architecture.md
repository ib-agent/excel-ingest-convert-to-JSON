## Object Storage Abstraction

This document defines the unified storage abstraction used by the system to persist original uploads, processed results, and metadata, while hiding the underlying storage backend (local filesystem or AWS S3).

### Goals

- Provide a consistent, key-first API for storing and retrieving content
- Support both local filesystem and AWS S3 via environment configuration
- Allow directory-like operations (create subdirectories, list files, list subdirectories, delete prefixes)
- Preserve backward compatibility with existing `StorageService` usage and endpoints
- Make processors always persist artifacts to storage, regardless of response format

### Configuration

- `STORAGE_BACKEND`: `local` (default) or `s3`
- `LOCAL_STORAGE_PATH`: base directory for local storage (default: `media/storage`)
- `S3_BUCKET_NAME`: bucket name when using `s3` (required for `s3`)
- `AWS_REGION`: S3 region (default: `us-east-1`)
- `AWS_ENDPOINT_URL`: optional S3-compatible endpoint (e.g., LocalStack)
- `STORAGE_ROOT_PREFIX`: optional root prefix for all keys (e.g., `app/`)
- `STORAGE_PRESIGN_TTL_SECONDS`: default URL TTL in seconds (default: `3600`)

Legacy toggle (backwards compatibility only):
- `USE_STORAGE_SERVICE`: when `true`, processors include storage references in responses; when `false`, processors still save to storage but return inline data and/or cache references.

### Concepts

- Key: a UTF-8 path-like identifier, e.g., `runs/{processing_id}/results/full.json`
- Prefix: a key prefix treated as a logical directory, e.g., `runs/{processing_id}/`
- Reference: a metadata record describing a stored object

### Python Interface

The upgraded interface augments `converter/storage_service.py` with key-first operations that work across backends.

Core operations:

```python
class StorageService(ABC):
    # Store bytes or JSON at an explicit key
    def put_bytes(self, key: str, data: bytes, content_type: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> StorageReference: ...
    def put_json(self, key: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> StorageReference: ...

    # Read, existence, deletion
    def get_bytes(self, key: str) -> bytes: ...
    def get_json(self, key: str) -> Dict[str, Any]: ...
    def exists(self, key: str) -> bool: ...
    def delete(self, key: str) -> bool: ...
    def delete_prefix(self, prefix: str) -> int: ...

    # Listing and directory-like operations
    def ensure_dir(self, prefix: str) -> None: ...
    def list(self, prefix: str, recursive: bool = True) -> List[StorageReference]: ...
    def list_dirs(self, prefix: str) -> List[str]: ...

    # URLs and utilities
    def get_url(self, key: str, expires_in: int = 3600) -> str: ...
    def get_download_url(self, reference: StorageReference, expires_in: int = 3600) -> str: ...  # backward-compatible
    def copy(self, src_key: str, dst_key: str) -> None: ...
    def move(self, src_key: str, dst_key: str) -> None: ...
```

Backward-compatible convenience methods remain available:

```python
def store_file(self, *, data: bytes, storage_type: StorageType, filename: str, metadata: Optional[Dict[str, Any]] = None) -> StorageReference
def store_json(self, *, data: Dict[str, Any], storage_type: StorageType, key_prefix: str, metadata: Optional[Dict[str, Any]] = None) -> StorageReference
```

These generate conventional keys under the hood and delegate to `put_bytes`/`put_json`.

### Key Conventions

To keep storage generic and not tied to specific documents, keys use a consistent run-oriented layout:

- `runs/{processing_id}/original/{filename}`
- `runs/{processing_id}/results/full.json`
- `runs/{processing_id}/results/tables.json`
- `runs/{processing_id}/meta/complexity.json`

This structure is a recommendation; the interface accepts any valid key. No document-specific logic is embedded.

### Backend Behavior

- Local filesystem
  - Keys map under `LOCAL_STORAGE_PATH`
  - `ensure_dir(prefix)` creates directories
  - `list_dirs(prefix)` enumerates immediate subdirectories
  - `get_url(key)` returns `/api/storage/get?key=...`

- AWS S3
  - Keys map to `Bucket` objects
  - `ensure_dir(prefix)` is a no-op or writes zero-byte marker objects
  - `list_dirs(prefix)` uses `Delimiter='/'` and `CommonPrefixes`
  - `get_url(key)` returns presigned URLs

### Processor Integration

Excel and PDF processors always persist artifacts to storage. Response bodies remain backward-compatible:

- When `USE_STORAGE_SERVICE=true`, responses include `storage` with keys and download URLs
- When `USE_STORAGE_SERVICE=false`, processors still write to storage but return inline/cached data for compatibility

### Examples

```python
storage = get_storage_service()
processing_id = str(uuid.uuid4())
base = f"runs/{processing_id}/"

storage.ensure_dir(base)
storage.put_bytes(f"{base}original/{filename}", file_bytes, content_type="application/pdf", metadata={"processing_id": processing_id})

full_ref = storage.put_json(f"{base}results/full.json", result)
tables_ref = storage.put_json(f"{base}results/tables.json", tables)

urls = {
  "original": storage.get_url(f"{base}original/{filename}"),
  "full": storage.get_url(full_ref.key),
  "tables": storage.get_url(tables_ref.key),
}
```

### Migration Notes

- Existing endpoints and callers using `store_file`/`store_json` continue to work
- New code should prefer `put_bytes`/`put_json` with explicit keys
- Tests can continue using local backend for determinism by setting `STORAGE_BACKEND=local` and `LOCAL_STORAGE_PATH` to a temp directory


