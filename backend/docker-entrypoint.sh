#!/usr/bin/env bash
set -e

# Postgres 준비 대기
until nc -z db 5432; do
  echo "Waiting for Postgres on db:5432 ..."
  sleep 1
done

echo "Postgres is up"

python manage.py migrate --noinput || true
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
