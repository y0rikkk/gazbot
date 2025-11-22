#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
# Ждем, пока PostgreSQL будет готов принимать подключения
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "gazbot" -d "gazbot_db" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing migrations"

# Применяем миграции Alembic
alembic upgrade head

echo "Migrations completed successfully"

# Запускаем приложение
exec "$@"
