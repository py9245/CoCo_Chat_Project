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

exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
