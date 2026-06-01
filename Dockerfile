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

# nginx serves the frontend and proxies the API within the container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

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
    && mkdir -p /app/data/media /app/staticfiles

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
