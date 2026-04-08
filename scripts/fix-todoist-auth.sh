#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_CONFIG="${HOME}/.openclaw/openclaw.json"
TODOIST_CONFIG_DIR="${HOME}/.config/todoist-cli"
TODOIST_CONFIG="${TODOIST_CONFIG_DIR}/config.json"

if ! command -v td >/dev/null 2>&1; then
  echo "Error: td CLI is not installed." >&2
  echo "Install it with: npm install -g @doist/todoist-cli" >&2
  exit 1
fi

if [ ! -f "$OPENCLAW_CONFIG" ]; then
  echo "Error: OpenClaw config not found at $OPENCLAW_CONFIG" >&2
  exit 1
fi

TOKEN="$(python3 - <<'PY'
import json
import os

path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(path) as f:
    data = json.load(f)

token = (data.get('plugins', {}).get('entries', {}).get('todoist', {}).get('config', {}) or {}).get('apiToken')
if token:
    print(token)
PY
)"

if [ -z "$TOKEN" ]; then
  echo "Error: Todoist token not found in plugins.entries.todoist.config.apiToken" >&2
  exit 1
fi

mkdir -p "$TODOIST_CONFIG_DIR"
td auth token "$TOKEN" >/dev/null

echo "Todoist CLI auth refreshed from OpenClaw config."
td auth status

if [ -f "$TODOIST_CONFIG" ]; then
  echo
  echo "Note: td stores its token in $TODOIST_CONFIG if no system credential manager is available."
fi
