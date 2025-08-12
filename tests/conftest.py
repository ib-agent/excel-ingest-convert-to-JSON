import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from fastapi_service.main import app
import os


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def fixtures_dir(project_root: Path) -> Path:
    return project_root / 'tests' / 'fixtures'


@pytest.fixture(scope="session")
def excel_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / 'excel'


@pytest.fixture(scope="session")
def pdfs_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / 'pdfs'


@pytest.fixture()
def storage_env(monkeypatch):
    monkeypatch.setenv('STORAGE_BACKEND', 'local')
    tmp = tempfile.TemporaryDirectory()
    monkeypatch.setenv('LOCAL_STORAGE_PATH', tmp.name)
    monkeypatch.setenv('USE_STORAGE_SERVICE', 'true')
    yield
    try:
        tmp.cleanup()
    except Exception:
        pass


@pytest.fixture()
def fastapi_client(storage_env):
    # Ensure Anthropic is available for AI-dependent tests when key is provided
    if 'ANTHROPIC_API_KEY' not in os.environ:
        key = os.getenv('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        if key:
            os.environ['ANTHROPIC_API_KEY'] = key
    return TestClient(app)


@pytest.fixture()
def excel_path(excel_dir: Path):
    def _get(name: str) -> str:
        p = excel_dir / name
        assert p.exists(), f"Excel fixture not found: {p}"
        return str(p)
    return _get


@pytest.fixture()
def pdf_path(pdfs_dir: Path):
    def _get(name: str) -> str:
        p = pdfs_dir / name
        assert p.exists(), f"PDF fixture not found: {p}"
        return str(p)
    return _get


