#!/bin/sh
set -eu

echo "⏳ Waiting for Postgres..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "✅ Postgres is up"

echo "⏳ Waiting for Redis..."
until nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  sleep 1
done
echo "✅ Redis is up"

echo "🚀 Starting app..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000

