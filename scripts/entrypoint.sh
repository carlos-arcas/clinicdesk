#!/usr/bin/env sh
set -eu

MODO_WEB="${CLINICDESK_WEB_MODE:-api}"
export APP_PORT="${CLINICDESK_WEB_PORT:-8000}"

if [ "$MODO_WEB" = "healthz" ]; then
  exec python -m clinicdesk.web.serve_health
fi

exec python -m clinicdesk.web.api.serve
