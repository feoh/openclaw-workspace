# OpenClaw Workspace Backups

## Purpose

Weekly backup of critical OpenClaw state files to the NAS path:

- `/nas/container_configs/openclaw`

Backups are versioned by UTC timestamp and rotated automatically so only the **3 most recent** copies are kept.

## What Gets Backed Up

The backup script copies these files/directories from the workspace when present:

- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `IDENTITY.md`
- `TOOLS.md`
- `MEMORY.md`
- `HEARTBEAT.md`
- `.env`
- `.openclaw/workspace-state.json`
- `data/open_brain_health.json`
- `.ssh/id_ed25519`
- `.ssh/id_ed25519.pub`
- `memory/`

It also writes a `MANIFEST.txt` file into each backup directory.

## Script

Backup script location:

- `/home/feoh/.openclaw/workspace/scripts/backup-critical-state.sh`

Manual run:

```bash
/home/feoh/.openclaw/workspace/scripts/backup-critical-state.sh
```

## Schedule

Installed user cron entry:

```cron
17 3 * * 1 /home/feoh/.openclaw/workspace/scripts/backup-critical-state.sh >> /home/feoh/.openclaw/workspace/data/backup-critical-state.log 2>&1
```

Meaning:

- **Every Monday at 03:17 UTC**

## Retention

Backups are stored like:

- `/nas/container_configs/openclaw/critical-state-YYYYMMDDTHHMMSSZ`

After each run, the script keeps the **newest 3** backup directories and removes older ones.

## Logs

Cron output is appended to:

- `/home/feoh/.openclaw/workspace/data/backup-critical-state.log`

## Restore Notes

There is currently **no dedicated restore script**.

To restore manually:

1. Pick the desired backup directory under `/nas/container_configs/openclaw/`
2. Copy files back into `/home/feoh/.openclaw/workspace/`
3. Be careful with `.env` because it may contain secrets
4. Be careful not to overwrite newer memory files accidentally

Example manual inspection:

```bash
ls -1dt /nas/container_configs/openclaw/critical-state-*
```

## Security Note

The backup includes `.env` and the workspace SSH keypair when present. That means secrets and private keys may be copied into the NAS backup set. This is intentional for disaster recovery, but access to `/nas/container_configs/openclaw` should be treated as highly sensitive.
