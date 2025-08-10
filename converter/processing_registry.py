from __future__ import annotations

import threading
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class ProcessingRegistry:
    """Thread-safe in-memory registry for processing records.

    Intended as a temporary solution; replace with Redis/DB for production.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Any]] = {}

    def register(self, processing_id: str, payload: Dict[str, Any]) -> None:
        with self._lock:
            record = dict(payload)
            record.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            record.setdefault("status", "completed")  # current flows are synchronous
            self._store[processing_id] = record

    def get(self, processing_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(processing_id)

    def delete(self, processing_id: str) -> bool:
        with self._lock:
            return self._store.pop(processing_id, None) is not None


processing_registry = ProcessingRegistry()


