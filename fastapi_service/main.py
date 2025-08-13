from fastapi import FastAPI
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from fastapi_service.routers import ui, excel, pdf, storage, status, results


def _load_dotenv_if_present(path: str = ".env") -> None:
    try:
        p = Path(path)
        if not p.exists():
            return
        with p.open("r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Do not override already-set env vars
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Fail silently; env can still be provided by the shell
        pass


_load_dotenv_if_present()


app = FastAPI(title="Excel/PDF Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ui.router)
# UI data endpoints
from fastapi_service.routers import ui_data  # type: ignore
app.include_router(ui_data.router, prefix="/api/ui")
app.include_router(excel.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")
app.include_router(storage.router, prefix="/api/storage")
app.include_router(status.router, prefix="/api")
app.include_router(results.router, prefix="/api")


# Configure default local storage directory for UI demo if not provided
if os.getenv("STORAGE_BACKEND", "local").lower() == "local":
    default_ui_storage = "/Users/jeffwinner/Projects/DocumentProcessingStorage"
    if not os.getenv("LOCAL_STORAGE_PATH"):
        os.environ["LOCAL_STORAGE_PATH"] = default_ui_storage
    try:
        Path(os.environ["LOCAL_STORAGE_PATH"]).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


