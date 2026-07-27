#!/usr/bin/env bash
set -euo pipefail

backup_directory="${MEMGUARD_BACKUP_DIR:-./backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="${backup_directory}/memguard-${timestamp}.dump"

mkdir -p "$backup_directory"
docker compose exec -T postgres pg_dump \
  -U memguard \
  -d memguard \
  --format=custom \
  --file=- > "$backup_file"

echo "MemGuard backup created: $backup_file"
