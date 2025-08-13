"""
Lightweight module for shared in-memory state used by FastAPI routers.

This replaces the prior Django model import and keeps only what the
routers expect: a module-level cache for processed data results.
"""

from typing import Any, Dict

# Shared in-memory cache for processed file data (small, ephemeral)
processed_data_cache: Dict[str, Any] = {}
