#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (this script is under scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[run_tests] Project root: $PROJECT_ROOT"

# Ensure venv exists
if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
  echo "[run_tests] Creating virtual environment..."
  python3 -m venv venv
fi

echo "[run_tests] Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

echo "[run_tests] Installing requirements..."
pip install -q -r docs/requirements.txt

# Configure environment for tests
export DJANGO_SETTINGS_MODULE=excel_converter.settings
export STORAGE_BACKEND="${STORAGE_BACKEND:-local}"
export USE_STORAGE_SERVICE="${USE_STORAGE_SERVICE:-true}"

# Create a temporary local storage path if using local backend
TEMP_STORAGE_CREATED=false
if [[ "$STORAGE_BACKEND" == "local" ]]; then
  if [[ -z "${LOCAL_STORAGE_PATH:-}" ]]; then
    export LOCAL_STORAGE_PATH="$(mktemp -d)"
    TEMP_STORAGE_CREATED=true
  fi
  echo "[run_tests] Using LOCAL_STORAGE_PATH=$LOCAL_STORAGE_PATH"
fi

cleanup() {
  if [[ "$TEMP_STORAGE_CREATED" == "true" && -n "${LOCAL_STORAGE_PATH:-}" && -d "$LOCAL_STORAGE_PATH" ]]; then
    echo "[run_tests] Cleaning up temporary LOCAL_STORAGE_PATH=$LOCAL_STORAGE_PATH"
    rm -rf "$LOCAL_STORAGE_PATH" || true
  fi
}
trap cleanup EXIT

echo "[run_tests] Running pytest..."
pytest -q tests
echo "[run_tests] Tests completed successfully."


