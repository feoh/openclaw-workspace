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

It also copies these host-level recovery files when present:

- `~/.openclaw/openclaw.json`
- `~/.config/todoist-cli/config.json`

They are stored inside the backup under:

- `host-home/.openclaw/openclaw.json`
- `host-home/.config/todoist-cli/config.json`

It also writes a `MANIFEST.txt` file into each backup directory.

In addition, the script attempts a compressed PostgreSQL dump of the Open Brain database:

- `postgres-openclaw-YYYYMMDDTHHMMSSZ.sql.gz`

The database dump is written directly under:

- `/nas/container_configs/openclaw`

## Script

Backup script location:

- `/home/feoh/.openclaw/workspace/scripts/backup-critical-state.sh`

Manual run:

```bash
/home/feoh/.openclaw/workspace/scripts/backup-critical-state.sh
```

## Schedule

The backup cadence currently observed on this host is:

- `2026-05-11 03:17 UTC`
- `2026-05-18 03:17 UTC`
- `2026-05-25 03:17 UTC`

That is consistent with a weekly run at roughly:

- **Every Monday at 03:17 UTC**

Important:

- Older documentation claimed this was installed via a user crontab entry.
- On `2026-05-26`, that exact entry was **not** present in `crontab -l`.
- The backup artifacts themselves are real and recent, but the current scheduler source was not identified during that verification pass.
- Treat the weekly cadence as verified; treat the exact scheduler mechanism as still needing traceability cleanup.

## Retention

Backups are stored like:

- `/nas/container_configs/openclaw/critical-state-YYYYMMDDTHHMMSSZ`
- `/nas/container_configs/openclaw/postgres-openclaw-YYYYMMDDTHHMMSSZ.sql.gz`

After each run, the script keeps the **newest 3** backup directories and the **newest 3** database dumps, removing older ones.

## Logs

Older documentation claimed cron output was appended to:

- `/home/feoh/.openclaw/workspace/data/backup-critical-state.log`

On `2026-05-26`, that file was **not** present on the host.

So at the moment:

- backup artifacts on the NAS are the primary proof that runs succeeded
- the expected local backup log path should be treated as stale documentation until the live scheduler path is traced

## Verification Notes

Careful validation performed on `2026-05-26` showed:

- `/nas/container_configs` is mounted read-write over NFS
- the newest three backup directories and PostgreSQL dumps exist
- the newest backup is `critical-state-20260525T031717Z`
- the newest dump is `postgres-openclaw-20260525T031717Z.sql.gz`
- the newest dump passes `gzip -t`
- the newest backup directory contains expected files including `MANIFEST.txt`, `.env`, `MEMORY.md`, `memory/`, SSH keys, and host OpenClaw config
- a live create/write/delete test on `/nas/container_configs/openclaw` succeeded during validation

## Restore Notes

There is currently **no dedicated restore script**.

To restore manually:

1. Pick the desired backup directory under `/nas/container_configs/openclaw/`
2. Copy files back into `/home/feoh/.openclaw/workspace/`
3. Be careful with `.env` because it may contain secrets
4. Restore host-level config files back to their original locations if needed:
   - `host-home/.openclaw/openclaw.json` → `~/.openclaw/openclaw.json`
   - `host-home/.config/todoist-cli/config.json` → `~/.config/todoist-cli/config.json`
5. Be careful not to overwrite newer memory files accidentally

Example manual inspection:

```bash
ls -1dt /nas/container_configs/openclaw/critical-state-*
```

## Security Note

The backup includes `.env`, the workspace SSH keypair, host-level OpenClaw/Todoist auth files, and a PostgreSQL dump when available. That means secrets, private keys, API tokens, and database contents may be copied into the NAS backup set. This is intentional for disaster recovery, but access to `/nas/container_configs/openclaw` should be treated as highly sensitive.
