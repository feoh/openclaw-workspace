# OpenClaw Server Migration Checklist

This guide captures the exact technical steps to move Simplificus/OpenClaw to a different server, with an emphasis on preserving functionality while creating a safer and more isolated environment.

## Recommended migration approach

You are migrating four main things:

1. OpenClaw config and local state
2. Workspace repo
3. Secrets and credentials
4. Scheduled jobs and service runtime

---

## Phase 1: Prepare the new server

On the new server:

1. Install the same major prerequisites:
   - Node
   - OpenClaw
   - git
   - Python and `uv` if workspace scripts depend on them
   - any local dependencies your scripts expect

2. Create the target user account you want OpenClaw to run under.
   - Prefer a dedicated non-root user.

3. Clone the workspace repo.
   - Use the same path if possible, or be prepared to update hardcoded paths.

Example:

```bash
git clone git@github.com:feoh/openclaw-workspace.git /home/feoh/.openclaw/workspace
```

4. Install Python dependencies for workspace scripts:

```bash
cd /home/feoh/.openclaw/workspace
uv venv
uv pip install -r requirements.txt
```

If there is no `requirements.txt`, install the exact packages currently used in the old workspace.

---

## Phase 2: Copy the critical local state

From the current server, preserve these first.

### Must copy

- `~/.openclaw/openclaw.json`
- `~/.openclaw/workspace/.env` if used
- `~/.config/todoist-cli/config.json`
- workspace SSH keypair if the repo push key is local:
  - `/home/feoh/.openclaw/workspace/.ssh/id_ed25519`
  - `/home/feoh/.openclaw/workspace/.ssh/id_ed25519.pub`

### Probably copy

- `~/.openclaw/cron/`
- local cache/state files used by scripts:
  - `data/rss-last-digest.json`
  - `data/rss-shown-urls.json`
  - `data/goodreads-last-seen.txt`
  - backup metadata/state if relevant

### If using database-backed memory

Also migrate:

- PostgreSQL database
- `pgvector` extension
- any Ollama model/runtime dependencies if still used

---

## Phase 3: Sanitize server-specific config

Before starting OpenClaw on the new machine, review:

### In `~/.openclaw/openclaw.json`

Check for anything tied to the old host:

- bind addresses
- gateway port and bind mode
- file paths
- plugin paths
- device pairing or public URLs
- any hostname/IP-specific values

Especially watch for:

- `gateway.bind`
- `gateway.remote.url`
- anything under `plugins.entries.*`
- Discord/Todoist or other plugin config paths

If the new box is more isolated, this is where you would tighten:

- bind only to loopback or tailnet
- disable anything public you do not need
- reduce exposed surfaces

---

## Phase 4: Migrate cron jobs carefully

You have two ways to handle cron migration.

### Safer method, recommended

Recreate the jobs from known-good config rather than copying scheduler internals blindly.

Why:

- avoids carrying stale runtime/session metadata
- cleaner if hostnames or paths changed

### Faster method

Copy the cron state:

- `~/.openclaw/cron/`

But if you do that, inspect job payloads afterward for:

- old absolute paths
- old session keys
- delivery targets you no longer want

Given the current setup, the best compromise is:

- copy cron state initially
- then inspect with `openclaw cron list`

---

## Phase 5: Start and verify

On the new server:

1. Check config:

```bash
openclaw status
```

2. Start gateway/service:

```bash
openclaw gateway status
openclaw gateway start
```

If using the systemd user service, verify that too.

3. Confirm runtime health:

```bash
openclaw status --deep
openclaw update status
```

4. Verify scheduled jobs:

```bash
openclaw cron list
```

5. Test critical paths one by one:

- Discord connectivity
- RSS digest
- news digest
- Goodreads monitor
- Todoist reminder
- backup job
- Git push from workspace

---

## Phase 6: Test before cutover

Before retiring the old server:

1. Run one manual RSS/news test.
2. Confirm Discord delivery works.
3. Confirm backups still point where expected.
4. Confirm secrets are valid.
5. Confirm the repo can push.
6. Confirm database-backed features if applicable.

Only then disable the old server.

---

## What to back up first no matter what

Minimum "do not lose anything important" bundle:

```text
~/.openclaw/openclaw.json
~/.openclaw/cron/
~/.config/todoist-cli/config.json
/home/feoh/.openclaw/workspace/
```

And if Open Brain/Postgres is in use:

```text
PostgreSQL dump of database openclaw
```

---

## Safer isolation recommendations

If the goal is a safer environment, specifically do this on the new server:

1. dedicated non-root user
2. minimal inbound exposure
3. tailnet/VPN-only access if possible
4. disk encryption if practical
5. regular backups
6. tighter firewall defaults
7. keep OpenClaw and OS updates current
8. separate this host from the general-purpose box

---

## Biggest migration gotchas

Most likely trouble spots:

- absolute paths in cron payloads
- missing `.env`
- missing Todoist config
- missing workspace SSH key
- database not migrated
- gateway bind/public URL still pointing at old host
- copied cron jobs referencing old assumptions

---

## Recommended order of operations

1. Provision new server.
2. Clone workspace.
3. Copy config, secrets, and state.
4. Restore database if needed.
5. Start OpenClaw.
6. Verify Discord, cron, and scripts.
7. Only then cut over.
