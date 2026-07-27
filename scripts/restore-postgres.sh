#!/usr/bin/env bash
set -euo pipefail

backup_file="${1:?Usage: ./scripts/restore-postgres.sh <backup-file.dump>}"

if [[ ! -f "$backup_file" ]]; then
  echo "Backup file not found: $backup_file" >&2
  exit 1
fi

docker compose exec -T postgres pg_restore \
  -U memguard \
  -d memguard \
  --clean \
  --if-exists \
  --no-owner < "$backup_file"

echo "MemGuard database restored from: $backup_file"
