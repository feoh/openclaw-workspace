# Todoist Recovery and Persistence

## Why this exists

Todoist auth currently has two layers on this machine:

1. OpenClaw plugin config
   - `~/.openclaw/openclaw.json`
   - token path: `plugins.entries.todoist.config.apiToken`
2. Todoist CLI auth cache
   - `~/.config/todoist-cli/config.json`

If the second layer disappears, Todoist operations through `td` fail even if the plugin token still exists.

## Known-good config path

Use this OpenClaw config path:

- `plugins.entries.todoist.config.apiToken`

Do **not** use:

- `integrations.todoist`

That path is not supported by the installed OpenClaw build.

## Fast recovery

Run:

```bash
/home/feoh/.openclaw/workspace/scripts/fix-todoist-auth.sh
```

What it does:

- reads the Todoist API token from `~/.openclaw/openclaw.json`
- re-seeds `td` auth with `td auth token <token>`
- prints `td auth status`

## Manual recovery

If needed, the manual flow is:

```bash
td auth token "<todoist-api-token>"
td auth status
```

Or reapply from OpenClaw config with Python:

```bash
python3 - <<'PY'
import json, os
path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(path) as f:
    data = json.load(f)
print((data.get('plugins', {}).get('entries', {}).get('todoist', {}).get('config', {}) or {}).get('apiToken', ''))
PY
```

## Backup coverage

The weekly backup now includes both host-level recovery files:

- `~/.openclaw/openclaw.json`
- `~/.config/todoist-cli/config.json`

These are stored in backup snapshots under:

- `host-home/.openclaw/openclaw.json`
- `host-home/.config/todoist-cli/config.json`

## Security note

These files contain secrets. They must never be committed to git.
They are intentionally included in the NAS backup for disaster recovery, so NAS access should be treated as highly sensitive.
