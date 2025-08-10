#!/usr/bin/env sh
set -e

# Wait for optional dependencies if needed (DB services, etc.) — not required for SQLite

echo "Applying database migrations (if any)..."
python manage.py migrate --noinput || true

if [ "${DJANGO_COLLECTSTATIC:-true}" = "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput || true
fi

exec "$@"


