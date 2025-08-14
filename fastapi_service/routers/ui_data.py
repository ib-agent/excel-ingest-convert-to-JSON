from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from converter.storage_service import get_storage_service
from converter.metadata_analyzer import MetadataAnalyzer


router = APIRouter()


def _list_run_dirs() -> List[str]:
    storage = get_storage_service()
    # list immediate subdirectories - now runs are at root level
    try:
        return sorted(storage.list_dirs(""), reverse=True)
    except Exception:
        return []


@router.get("/runs")
def list_runs():
    storage = get_storage_service()
    run_dirs = _list_run_dirs()
    items: List[Dict[str, Any]] = []
    for rd in run_dirs:
        # each rd ends with trailing slash in local; normalize key
        key = f"{rd}meta.json" if rd.endswith("/") else f"{rd}/meta.json"
        try:
            meta = storage.get_json(key)
            items.append(meta)
        except Exception:
            continue
    # sort by created_at desc if present
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"runs": items}

@router.get("/runs/enhanced")
def list_runs_enhanced():
    """Get enhanced run list with detailed metadata and statistics."""
    storage = get_storage_service()
    
    # Determine storage path for metadata analyzer
    # For local storage, we can use the configured path
    if hasattr(storage, 'base_path'):
        storage_path = storage.base_path
    else:
        # Fallback to environment variable or default
        storage_path = os.environ.get('LOCAL_STORAGE_PATH', './storage')
    
    analyzer = MetadataAnalyzer(storage_path)
    run_dirs = _list_run_dirs()
    enhanced_items: List[Dict[str, Any]] = []
    
    for rd in run_dirs:
        try:
            # Clean run directory name
            clean_rd = rd.rstrip('/')
            
            # Get enhanced metadata
            enhanced_meta = analyzer.analyze_run(clean_rd)
            if enhanced_meta:
                # Get display summary
                display_summary = analyzer.get_display_summary(enhanced_meta)
                enhanced_items.append({
                    'run_dir': clean_rd,
                    'enhanced_metadata': enhanced_meta,
                    'display_summary': display_summary
                })
        except Exception as e:
            # If enhancement fails, fall back to basic metadata
            try:
                key = f"{rd}meta.json" if rd.endswith("/") else f"{rd}/meta.json"
                meta = storage.get_json(key)
                enhanced_items.append({
                    'run_dir': rd.rstrip('/'),
                    'enhanced_metadata': meta,
                    'display_summary': {
                        'filename': meta.get('filename', 'Unknown'),
                        'file_type': meta.get('file_type', 'unknown').upper(),
                        'created_at': meta.get('created_at', ''),
                        'error': f'Analysis failed: {str(e)}'
                    }
                })
            except Exception:
                continue
    
    # Sort by created_at desc
    enhanced_items.sort(
        key=lambda x: x.get('enhanced_metadata', {}).get('created_at', ''), 
        reverse=True
    )
    
    return {"runs": enhanced_items}


@router.get("/run/{run_dir}")
def get_run(run_dir: str):
    storage = get_storage_service()
    key = f"{run_dir}/meta.json"
    try:
        meta = storage.get_json(key)
    except Exception as e:
        raise HTTPException(404, f"run not found: {str(e)}")
    return {"run": meta}


@router.get("/run/{run_dir}/data")
def get_run_data(run_dir: str):
    storage = get_storage_service()
    meta_key = f"{run_dir}/meta.json"
    try:
        meta = storage.get_json(meta_key)
    except Exception as e:
        raise HTTPException(404, f"run not found: {str(e)}")
    
    data: Dict[str, Any] = {"meta": meta}
    
    # Load artifacts from the new unified structure
    artifacts = meta.get("artifacts", {})
    
    # Load processed JSON
    if artifacts.get("processed_json"):
        try:
            data["full"] = storage.get_json(artifacts["processed_json"])
        except Exception:
            pass
    
    # Load table data
    if artifacts.get("table_data"):
        try:
            data["tables"] = storage.get_json(artifacts["table_data"])
        except Exception:
            pass
    
    return data


@router.get("/run/{run_dir}/html", response_class=HTMLResponse)
def get_run_html(run_dir: str):
    """Serve pre-generated HTML for a run"""
    storage = get_storage_service()
    
    # First check if pre-generated HTML exists in new structure
    html_key = f"{run_dir}/display.html"
    try:
        html_bytes = storage.get_bytes(html_key)
        html_content = html_bytes.decode('utf-8')
        return HTMLResponse(content=html_content)
    except Exception:
        # If no pre-generated HTML, fall back to generating it on-demand
        try:
            # Get the run data to generate HTML
            meta_key = f"{run_dir}/meta.json"
            meta = storage.get_json(meta_key)
            artifacts = meta.get("artifacts", {})
            
            data = {"meta": meta}
            if artifacts.get("processed_json"):
                try:
                    data["full"] = storage.get_json(artifacts["processed_json"])
                except Exception:
                    pass
            if artifacts.get("table_data"):
                try:
                    data["tables"] = storage.get_json(artifacts["table_data"])
                except Exception:
                    pass
            
            # Generate HTML on-demand as fallback
            from converter.html_generator import HTMLGenerator
            html_generator = HTMLGenerator()
            html_content = html_generator.generate_complete_html(data, meta)
            
            # Optionally cache the generated HTML
            try:
                storage.put_bytes(html_key, html_content.encode('utf-8'), content_type='text/html')
            except Exception:
                pass  # Ignore caching errors
            
            return HTMLResponse(content=html_content)
            
        except Exception as e:
            raise HTTPException(404, f"run not found or HTML generation failed: {str(e)}")


@router.delete("/run/{run_dir}")
def delete_run(run_dir: str):
    storage = get_storage_service()
    # With the new unified structure, run directories are at root level
    prefix = f"{run_dir}/"
    try:
        deleted = storage.delete_prefix(prefix)
        # Best-effort: also try deleting the directory itself in case backends treat dirs differently
        storage.delete(run_dir.rstrip("/"))  # ignore result
    except Exception as e:
        raise HTTPException(500, f"failed to delete run: {str(e)}")
    return {"deleted": int(deleted) if isinstance(deleted, int) else (1 if deleted else 0), "run_dir": run_dir}


@router.delete("/cleanup-all")
def cleanup_all_runs():
    """Delete all runs and start fresh"""
    storage = get_storage_service()
    
    try:
        # Get all run directories
        run_dirs = _list_run_dirs()  # Remove storage parameter
        deleted_count = 0
        
        for run_dir in run_dirs:
            try:
                prefix = f"{run_dir}/"
                deleted = storage.delete_prefix(prefix)
                storage.delete(run_dir.rstrip("/"))  # ignore result
                deleted_count += 1
            except Exception as e:
                # Continue with other deletions even if one fails
                print(f"Failed to delete {run_dir}: {e}")
                
        return {
            "message": "All runs deleted successfully", 
            "deleted_count": deleted_count,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(500, f"Failed to cleanup all runs: {str(e)}")


