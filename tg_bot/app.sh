#!/bin/bash
set -e

until PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d "postgres" -c '\q'; do
  echo >&2 "Postgres is unavailable - sleeping"
  sleep 1
done

echo >&2 "Postgres is up - continuing"
ls -a
python -m tg_bot.bot