# Coderr — single image running the Django/Gunicorn API and the nginx-served
# frontend together. nginx (port 80) serves the static site and reverse-proxies
# /api/, /admin/, /static/ and /media/ to Gunicorn on 127.0.0.1:8000.
#
#   docker build -t coderr .
#   docker run -d -p 8080:80 -e DJANGO_SECRET_KEY=... -v coderr-data:/app/data coderr
#
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DB_PATH=/app/data/db.sqlite3 \
    DJANGO_MEDIA_ROOT=/app/data/media

# nginx serves the frontend and proxies the API; gosu drops Gunicorn to a
# non-root user; curl backs the container health check.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx gosu curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Unprivileged account that runs the Django/Gunicorn process.
RUN useradd --system --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Python deps first for layer caching.
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend code and static frontend.
COPY backend/ /app/
COPY frontend/ /usr/share/nginx/html/

# nginx server block and the start script (runs migrations, then both procs).
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /app/data/media /app/staticfiles \
    # Data and static dirs are written by the unprivileged Gunicorn process.
    && chown -R appuser:appuser /app/data /app/staticfiles

EXPOSE 80

# Hits the public endpoint through nginx -> Gunicorn, so it covers both procs.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1/api/base-info/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
