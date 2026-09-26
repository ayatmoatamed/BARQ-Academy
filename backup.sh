#!/usr/bin/env bash
set -euo pipefail

mkdir -p backups

BACKUP_FILE="backups/barq_tasks_$(date +%Y%m%d_%H%M%S).sql"

echo "Creating PostgreSQL backup..."
docker exec postgres pg_dump \
  -U barq_app \
  -d barq_tasks \
  > "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"
