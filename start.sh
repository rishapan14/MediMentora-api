#!/bin/sh
set -eu

# Railway must be able to reach /health even while MySQL is starting or schema
# patches are still running. Keep bootstrap off the critical path of the web
# listener; API requests remain protected by the application's schema guard.
if [ "${RUN_SCHEMA_BOOTSTRAP:-true}" = "true" ]; then
  python -m app.schema_bootstrap &
fi

# Run document processing in a separate Railway worker service in production.
# Enabling it in the web container is supported for larger single-service plans,
# but is deliberately off by default to prevent memory pressure from killing the
# public API process.
if [ "${RUN_LEARNING_WORKER:-false}" = "true" ]; then
  python -m app.learning_worker &
fi

exec gunicorn \
  --bind "0.0.0.0:${PORT:-5000}" \
  --workers "${MEDIMENTORA_WEB_WORKERS:-1}" \
  --worker-class gthread \
  --threads "${MEDIMENTORA_WEB_THREADS:-2}" \
  --timeout 180 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --max-requests 500 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile - \
  --log-level warning \
  run:app
