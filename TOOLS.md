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
- Virtual environment: `/home/feoh/.openclaw/workspace/.venv/` (contains feedparser)

---

Add whatever helps you do your job. This is your cheat sheet.
