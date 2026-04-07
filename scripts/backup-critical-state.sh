#!/usr/bin/env bash
set -euo pipefail

SRC="/home/feoh/.openclaw/workspace"
DEST_ROOT="/nas/container_configs/openclaw"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST_DIR="$DEST_ROOT/critical-state-$STAMP"
KEEP=3

mkdir -p "$DEST_DIR"

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

# Daily memory log directory
if [ -d "$SRC/memory" ]; then
  cp -a "$SRC/memory" "$DEST_DIR/memory"
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
- memory/ directory (if present)
MANIFEST

# Retention: keep newest N backup directories only
cd "$DEST_ROOT"
ls -1dt critical-state-* 2>/dev/null | awk 'NR>'"$KEEP"'' | while read -r old; do
  rm -rf -- "$old"
done

echo "Backup complete: $DEST_DIR"
