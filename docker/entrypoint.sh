#!/bin/bash
# Single-image start script: prepare the app, then run Gunicorn + nginx together.
set -e

# 1. Point the frontend at the API. Same-origin relative paths by default so the
#    image works on any host; override API_BASE_URL / STATIC_BASE_URL if needed.
CONFIG="/usr/share/nginx/html/shared/scripts/config.js"
API_BASE_URL="${API_BASE_URL:-/api/}"
STATIC_BASE_URL="${STATIC_BASE_URL:-/}"
if [ -f "$CONFIG" ]; then
    sed -i "s#^const API_BASE_URL = .*#const API_BASE_URL = '${API_BASE_URL}';#" "$CONFIG"
    sed -i "s#^const STATIC_BASE_URL = .*#const STATIC_BASE_URL = '${STATIC_BASE_URL}';#" "$CONFIG"
fi

cd /app

# 2. Database and static files.
echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Optionally seed demo content on an empty database (SEED_DEMO_DATA=1).
if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    echo "Seeding demo data..."
    python manage.py seed_demo_data
fi

# 3. Run both processes. Gunicorn in the background, nginx in the foreground.
#    If Gunicorn exits, stop the container so the orchestrator can restart it.
echo "Starting Gunicorn..."
gunicorn core.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers "${GUNICORN_WORKERS:-3}" &
GUNICORN_PID=$!

trap 'kill -TERM "$GUNICORN_PID" 2>/dev/null' TERM INT

echo "Starting nginx..."
nginx -g 'daemon off;' &
NGINX_PID=$!

# Exit as soon as either process stops.
wait -n "$GUNICORN_PID" "$NGINX_PID"
EXIT_CODE=$?
kill -TERM "$GUNICORN_PID" "$NGINX_PID" 2>/dev/null || true
exit "$EXIT_CODE"
