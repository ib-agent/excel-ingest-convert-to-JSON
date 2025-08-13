#!/usr/bin/env sh
set -e

# Wait for optional dependencies if needed (DB services, etc.) — not required for SQLite

echo "Starting FastAPI service..."

exec "$@"


