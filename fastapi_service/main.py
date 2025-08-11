from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from fastapi_service.routers import ui, excel, pdf, storage, status


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
app.include_router(excel.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")
app.include_router(storage.router, prefix="/api/storage")
app.include_router(status.router, prefix="/api")


