#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"

if [[ -z "$BACKUP_FILE" || ! -f "$BACKUP_FILE" ]]; then
    echo "Usage: ./restore.sh <backup.sql>"
    exit 1
fi

TEST_DB="barq_restore_test"

echo "Creating clean restore database..."

docker exec postgres dropdb \
  -U barq_app \
  --if-exists "$TEST_DB"

docker exec postgres createdb \
  -U barq_app \
  "$TEST_DB"

echo "Restoring backup..."

docker exec -i postgres psql \
  -U barq_app \
  -d "$TEST_DB" \
  < "$BACKUP_FILE" \
  > /dev/null

echo "Verifying restored database..."

COUNT=$(docker exec postgres psql \
  -U barq_app \
  -d "$TEST_DB" \
  -tAc "SELECT COUNT(*) FROM records;")

echo "Restored records: $COUNT"

docker exec postgres dropdb \
  -U barq_app \
  "$TEST_DB"

echo "Restore verification successful."
