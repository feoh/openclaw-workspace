#!/usr/bin/env bash
set -euo pipefail

SRC="/home/feoh/.openclaw/workspace"
DEST_ROOT="/nas/container_configs/openclaw"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST_DIR="$DEST_ROOT/critical-state-$STAMP"
DB_DUMP="$DEST_ROOT/postgres-openclaw-$STAMP.sql.gz"
KEEP=3

mkdir -p "$DEST_DIR"

# Load env for database backup if present
if [ -f "$SRC/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$SRC/.env"
  set +a
fi

copy_if_exists() {
  local path="$1"
  if [ -e "$SRC/$path" ]; then
    mkdir -p "$DEST_DIR/$(dirname "$path")"
    cp -a "$SRC/$path" "$DEST_DIR/$path"
  fi
}

# Core identity / memory / config
copy_if_exists AGENTS.md
copy_if_exists SOUL.md
copy_if_exists USER.md
copy_if_exists IDENTITY.md
copy_if_exists TOOLS.md
copy_if_exists MEMORY.md
copy_if_exists HEARTBEAT.md
copy_if_exists .env
copy_if_exists .openclaw/workspace-state.json
copy_if_exists data/open_brain_health.json

# SSH material for GitHub access
copy_if_exists .ssh/id_ed25519
copy_if_exists .ssh/id_ed25519.pub

# Daily memory log directory
if [ -d "$SRC/memory" ]; then
  cp -a "$SRC/memory" "$DEST_DIR/memory"
fi

# PostgreSQL Open Brain dump (best effort)
if command -v pg_dump >/dev/null 2>&1 && [ -n "${POSTGRES_PASSWORD:-}" ]; then
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-simplificus}" \
    -d "${POSTGRES_DB:-openclaw}" \
    --no-owner --no-privileges | gzip -c > "$DB_DUMP"
  DB_STATUS="created: $(basename "$DB_DUMP")"
else
  DB_STATUS="skipped (pg_dump missing or POSTGRES_PASSWORD unavailable)"
fi

# Manifest for quick inspection
cat > "$DEST_DIR/MANIFEST.txt" <<MANIFEST
OpenClaw critical state backup
Created (UTC): $STAMP
Source: $SRC
Files included:
- AGENTS.md
- SOUL.md
- USER.md
- IDENTITY.md
- TOOLS.md
- MEMORY.md
- HEARTBEAT.md
- .env (if present)
- .openclaw/workspace-state.json (if present)
- data/open_brain_health.json (if present)
- .ssh/id_ed25519 and .ssh/id_ed25519.pub (if present)
- memory/ directory (if present)
Database dump:
- $DB_STATUS
MANIFEST

# Retention: keep newest N backup directories only
cd "$DEST_ROOT"
ls -1dt critical-state-* 2>/dev/null | awk 'NR>'"$KEEP"'' | while read -r old; do
  rm -rf -- "$old"
done

# Retention: keep newest N database dumps only
ls -1dt postgres-openclaw-*.sql.gz 2>/dev/null | awk 'NR>'"$KEEP"'' | while read -r old; do
  rm -f -- "$old"
done

echo "Backup complete: $DEST_DIR"
echo "Database dump: $DB_STATUS"
