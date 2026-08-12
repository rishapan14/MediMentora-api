#!/bin/sh
set -eu

# Bind the HTTP server immediately so Railway liveness never reports a platform
# 502 while MySQL is starting. The Flask worker initializes the schema in a
# background thread and gates DB-backed routes with a controlled 503 until ready.
if [ "${RUN_SCHEMA_BOOTSTRAP:-true}" = "true" ]; then
  export RUN_SCHEMA_BOOTSTRAP_BACKGROUND=true
  export SCHEMA_READY_FILE=/tmp/medimentora-schema-ready
  rm -f /tmp/medimentora-schema-ready
else
  export RUN_SCHEMA_BOOTSTRAP_BACKGROUND=false
  unset SCHEMA_READY_FILE
fi

# Run document processing in a separate Railway worker service in production.
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
  --capture-output \
  --log-level info \
  run:app