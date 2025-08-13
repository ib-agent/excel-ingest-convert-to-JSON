from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException

from converter.storage_service import get_storage_service


router = APIRouter()


def _list_run_dirs() -> List[str]:
    storage = get_storage_service()
    # list immediate subdirectories under runs/
    try:
        return sorted(storage.list_dirs("runs/"), reverse=True)
    except Exception:
        return []


@router.get("/runs")
def list_runs():
    storage = get_storage_service()
    run_dirs = _list_run_dirs()
    items: List[Dict[str, Any]] = []
    for rd in run_dirs:
        # each rd ends with trailing slash in local; normalize key
        key = f"{rd}meta/index.json" if rd.endswith("/") else f"{rd}/meta/index.json"
        try:
            meta = storage.get_json(key)
            items.append(meta)
        except Exception:
            continue
    # sort by created_at desc if present
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"runs": items}


@router.get("/run/{run_dir}")
def get_run(run_dir: str):
    storage = get_storage_service()
    key = f"runs/{run_dir}/meta/index.json"
    try:
        meta = storage.get_json(key)
    except Exception as e:
        raise HTTPException(404, f"run not found: {str(e)}")
    return {"run": meta}


@router.get("/run/{run_dir}/data")
def get_run_data(run_dir: str):
    storage = get_storage_service()
    index_key = f"runs/{run_dir}/meta/index.json"
    try:
        meta = storage.get_json(index_key)
    except Exception as e:
        raise HTTPException(404, f"run not found: {str(e)}")
    data: Dict[str, Any] = {"meta": meta}
    keys: Dict[str, Optional[str]] = (meta or {}).get("keys", {})
    # Load available artifacts safely
    if keys.get("processed_json"):
        try:
            data["full"] = storage.get_json(keys["processed_json"])  # type: ignore[arg-type]
        except Exception:
            pass
    if keys.get("table_data"):
        try:
            data["tables"] = storage.get_json(keys["table_data"])  # type: ignore[arg-type]
        except Exception:
            pass
    if keys.get("complexity_results"):
        try:
            data["complexity"] = storage.get_json(keys["complexity_results"])  # type: ignore[arg-type]
        except Exception:
            pass
    return data


@router.delete("/run/{run_dir}")
def delete_run(run_dir: str):
    storage = get_storage_service()
    prefix = f"runs/{run_dir}/"
    try:
        deleted = storage.delete_prefix(prefix)
        # Best-effort: also try deleting the meta marker in case backends treat dirs differently
        storage.delete(prefix.rstrip("/"))  # ignore result
    except Exception as e:
        raise HTTPException(500, f"failed to delete run: {str(e)}")
    return {"deleted": int(deleted) if isinstance(deleted, int) else (1 if deleted else 0), "run_dir": run_dir}


