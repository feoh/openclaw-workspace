# Todoist Integration Notes

## Status

Todoist integration is installed and active on this machine via the OpenClaw Todoist plugin.

## What Was Used

- Plugin package: `openclaw-todoist-plugin`
- Plugin ID: `todoist`
- Required CLI: `@doist/todoist-cli`
- Command: `td`

## Important Config Notes

This OpenClaw build does **not** support a top-level `integrations.todoist` config block.
That older-looking config path was rejected by the installed schema.

The working configuration path is:

- `plugins.entries.todoist.config.apiToken`

## Host-Local Setup

These changes are machine-local and are **not committed to git**:

- `~/.openclaw/openclaw.json`
- `~/.openclaw/extensions/todoist/`
- `~/.config/todoist-cli/config.json`
- global npm installation of `@doist/todoist-cli`

The important split-brain detail is:

- OpenClaw plugin token lives in `~/.openclaw/openclaw.json`
- `td` CLI auth may also need its own cached credentials in `~/.config/todoist-cli/config.json`

If `td` loses auth but the plugin token still exists, recover with:

```bash
/home/feoh/.openclaw/workspace/scripts/fix-todoist-auth.sh
```

See also:

- `/home/feoh/.openclaw/workspace/docs/todoist-recovery.md`

## Node Migration Note

After switching from Volta-managed Node to Homebrew Node, OpenClaw required config cleanup for legacy schema drift:

- Discord channel config: `allow` → `enabled`
- removed obsolete `tools.web.search` config block

Once those were corrected, the gateway validated and the Todoist plugin loaded successfully.

## Security Note

The Todoist API token is a secret and must never be committed to the workspace repo.
