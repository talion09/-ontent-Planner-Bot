#!/bin/bash
set -e

until PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d "postgres" -c '\q'; do
  echo >&2 "Postgres is unavailable - sleeping"
  sleep 1
done

echo >&2 "Postgres is up - continuing"

alembic -c api_service/migrations/alembic.ini revision --autogenerate -m "Initial migration"
alembic -c api_service/migrations/alembic.ini upgrade head
uvicorn api_service.main:app --port 8000 --host 0.0.0.0