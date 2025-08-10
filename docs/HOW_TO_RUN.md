## How to run this project

This guide shows two ways to run the app:

- Docker (recommended for consistency)
- Local Python virtual environment (developer mode)

The app exposes web pages and REST endpoints for Excel and PDF processing.

---

## Prerequisites

- Docker and Docker Compose
- Or: Python 3.11 and a virtual environment tool (for local dev)

---

## Option A: Run with Docker

1) Create environment file

```bash
cd /Users/jeffwinner/excel-ingest-convert-to-JSON
cp env.example .env
```

You can keep the defaults for local dev. Useful vars in `.env`:

- `DJANGO_DEBUG=true|false`
- `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0`
- `CORS_ALLOW_ALL_ORIGINS=true|false`
- `USE_STORAGE_SERVICE=true|false`
- `CMD` (switch between dev server and Gunicorn)

2) Build and start

```bash
docker compose build
docker compose up
```

3) Open the app

- UI pages:
  - `http://localhost:8000/` (landing)
  - `http://localhost:8000/excel/`
  - `http://localhost:8000/pdf/`
- Health:
  - `GET http://localhost:8000/api/health/`

4) Call the APIs (examples)

- Excel upload (compact format by default in code):

```bash
curl -F "file=@tests/test_excel/Test_SpreadSheet_100_numbers.xlsx" \
  http://localhost:8000/api/upload/
```

- PDF upload (table removal path is default in code; compact response with `format=compact`):

```bash
curl -F "file=@tests/test_pdfs/Test_PDF_Table_9_numbers.pdf" \
  "http://localhost:8000/api/pdf/upload/?format=compact"
```

5) Persistent data

- Docker volumes keep uploads and collected static assets:
  - `media` mounted at `/app/media`
  - `staticfiles` mounted at `/app/staticfiles`

6) Production-like server (optional)

Switch to Gunicorn by editing `.env`:

```env
DJANGO_DEBUG=false
CMD=gunicorn excel_converter.wsgi:application --bind 0.0.0.0:8000 --workers=${WEB_CONCURRENCY:-2} --timeout=120
```

Then restart:

```bash
docker compose up --build
```

---

## Option B: Run locally (virtualenv)

1) Create and activate venv

```bash
cd /Users/jeffwinner/excel-ingest-convert-to-JSON
python3.11 -m venv venv
source venv/bin/activate
```

2) Install dependencies

```bash
pip install --upgrade pip
pip install -r docs/requirements.txt -r pdf_requirements.txt
```

3) Migrate and collect static (first run)

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

4) Run the server

```bash
python manage.py runserver 0.0.0.0:8000
```

Open `http://localhost:8000/`.

---

## Key endpoints

- Health: `GET /api/health/`

- Excel:
  - `POST /api/upload/` — upload `.xlsx` and get JSON + compact table-oriented data
  - `POST /api/excel/analyze-complexity/`
  - `POST /api/excel/comparison-analysis/`

- PDF:
  - `POST /api/pdf/upload/` — default: table removal approach; add `?format=compact` for compact response
  - `POST /api/pdf/table-removal/` — dedicated table removal endpoint
  - `POST /api/pdf/ai-failover/` — AI failover routing pipeline
  - `GET /api/pdf/status/`

- Storage (optional microservice-like endpoints):
  - `POST /api/storage/store-file/`
  - `POST /api/storage/store-json/`
  - `GET /api/storage/get/`
  - `GET /api/storage/get-json/`
  - `DELETE /api/storage/delete/`
  - `GET /api/storage/list/`

---

## Environment and settings

The app reads these env vars (with sensible dev defaults):

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOW_ALL_ORIGINS`
- `USE_STORAGE_SERVICE`

Static files are collected to `staticfiles/`. Uploaded files are stored under `media/`.


