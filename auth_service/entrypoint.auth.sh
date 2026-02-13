#!/bin/sh
set -eu

wait_for() {
  name="$1"
  host="$2"
  port="$3"
  max_retries="${4:-60}"

  echo "Waiting for $name..."
  i=0
  until nc -z "$host" "$port"; do
    sleep 1
    i=$((i+1))
    if [ "$i" -ge "$max_retries" ]; then
      echo "$name is not available after ${max_retries}s. Exiting."
      exit 1
    fi
  done
  echo "$name is up"
}

wait_for "Postgres" "$DB_HOST" "$DB_PORT" 60
wait_for "Redis" "$REDIS_HOST" "$REDIS_PORT" 60

echo "Starting app..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000