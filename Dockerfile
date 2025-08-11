# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# System deps for Pillow and common scientific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    # OpenCV runtime deps
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY docs/requirements.txt /app/docs/requirements.txt
COPY pdf_requirements.txt /app/pdf_requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install -r /app/docs/requirements.txt && \
    pip install -r /app/pdf_requirements.txt && \
    pip install gunicorn

# Copy application source
COPY . /app

# Default environment
ENV DJANGO_SETTINGS_MODULE=excel_converter.settings \
    DJANGO_DEBUG=true \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0 \
    CORS_ALLOW_ALL_ORIGINS=true

# Ensure runtime dirs exist
RUN mkdir -p /app/media /app/staticfiles

# Entrypoint handles migrations/collectstatic
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

# Default command can be overridden by docker-compose; set a safe default to uvicorn
ENV CMD="uvicorn fastapi_service.main:app --host 0.0.0.0 --port 8000"

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=10 \
  CMD curl -fsS http://localhost:8000/api/health/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-lc", "$CMD"]


