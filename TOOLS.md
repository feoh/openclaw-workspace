# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

## Discord Bot
- Token stored in `.env` (DISCORD_BOT_TOKEN) — never commit this
- Configured for Simplificus assistant on Chris's private server

## Linkding API
- URL: https://linkding.reedfish-regulus.ts.net/api/bookmarks/ ← **trailing slash required** (POST returns 301 otherwise)
- API Key: `<LINKDING_API_KEY>` — stored locally, never commit this
- Tag for "toread": `toread`
- Known working POST format: `{"url": "<url>", "tag_names": ["toread"]}`
- Linkding already has 3420+ bookmarks saved (as of 2026-03-23)

### RSS Feeds

- OPML: `/home/feoh/.openclaw/workspace/rss-feeds.opml`
- Cache: `/home/feoh/.openclaw/workspace/rss-cache/`
- Latest parsed: `/home/feoh/.openclaw/workspace/rss-latest.json`
- 19 feeds configured (see OPML or memory/2026-03-23.md)

## Python Tools
- **uv** — preferred package manager (NOT pip). Use `uv pip install` or `uv add` in the workspace venv
- Virtual environment: `/home/feoh/.openclaw/workspace/.venv/`
- **Always use the Python inside the workspace virtualenv**: `/home/feoh/.openclaw/workspace/.venv/bin/python`
- **Do not use system Python for workspace tasks**. Leave system Python untouched.
- Manage workspace Python dependencies with `uv` only.

## PostgreSQL + pgvector
- Host: localhost, Port: 5432
- Database: `openclaw`
- User: `simplificus`
- Password: stored in `.env` (never commit this)
- pgvector version: 0.6.0
- Connection: `POSTGRES_*` vars in `.env`

## Open Brain Memory System
- Schema + tools in `scripts/openbrain-*.py`
- Write: `python3 scripts/openbrain-write.py "title" --summary "..." --body "..." --tags "tag1,tag2"`
- Search: `python3 scripts/openbrain-search.py "query" [--semantic] [--lane private] [--tag python]`
- Promote: `python3 scripts/openbrain-promote.py <id> [--lane controlled] [--confidence 80]`
- Health: `python3 scripts/openbrain-health.py`
- **MCP Server**: `python3 scripts/openbrain-mcp.py` (stdio-based, for MCP clients)
- Embedding model: `nomic-embed-text` via Ollama (768-dim vectors)
- Tables: `memory_objects` (private/controlled/public lanes, provenance, confidence)
