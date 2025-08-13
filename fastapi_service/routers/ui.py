from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
def main_landing():
    return FileResponse("converter/templates/converter/main_landing.html")


@router.get("/excel/", include_in_schema=False)
def excel_page():
    return FileResponse("converter/templates/converter/excel_processor.html")


@router.get("/pdf/", include_in_schema=False)
def pdf_page():
    return FileResponse("converter/templates/converter/pdf_processor.html")


@router.get("/run/{run_dir}", include_in_schema=False)
def run_page(run_dir: str):
    # The page will fetch data via /api/ui/run/{run_dir}
    return FileResponse("converter/templates/converter/run_results.html")


