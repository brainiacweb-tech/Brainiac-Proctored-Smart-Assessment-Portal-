#!/usr/bin/env bash
set -euo pipefail

echo "==> Brainiac Portal starting"
echo "    PORT=${PORT:-unset}"
echo "    DATABASE_URL=${DATABASE_URL:+configured}"
echo "    DEBUG=${DEBUG:-unset}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "==> Launching Gunicorn on 0.0.0.0:${PORT:-8080}"

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8080}" \
  --workers 1 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
