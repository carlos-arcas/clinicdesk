#!/usr/bin/env sh
set -eu

if [ -z "${APP_SECRET_KEY:-}" ]; then
  echo "[entrypoint] ERROR: APP_SECRET_KEY es obligatorio" >&2
  exit 1
fi

if [ -z "${APP_ALLOWED_HOSTS:-}" ]; then
  echo "[entrypoint] ERROR: APP_ALLOWED_HOSTS es obligatorio" >&2
  exit 1
fi

if [ -f "manage.py" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  exec python manage.py runserver 0.0.0.0:"${APP_PORT:-8000}"
fi

exec python -m clinicdesk.web.serve_health
