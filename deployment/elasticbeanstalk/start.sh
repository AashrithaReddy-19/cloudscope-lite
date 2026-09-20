#!/bin/sh
set -eu

max_attempts="${DB_STARTUP_MAX_ATTEMPTS:-30}"
retry_seconds="${DB_STARTUP_RETRY_SECONDS:-10}"
attempt=1

while [ "$attempt" -le "$max_attempts" ]; do
  if alembic upgrade head; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
  fi

  if [ "$attempt" -eq "$max_attempts" ]; then
    echo "Database migration failed after ${max_attempts} attempts." >&2
    exit 1
  fi

  echo "Database is not ready; retrying migration in ${retry_seconds} seconds (${attempt}/${max_attempts})." >&2
  sleep "$retry_seconds"
  attempt=$((attempt + 1))
done
