# MEMORY.md — Long-Term Memory

## This Week (2026-04-08)
- Current active model in OpenClaw runtime is **openai-codex/gpt-5.4**. Older Claude Sonnet references in repo docs were stale and should not be treated as current.
- Todoist persistence hardened: weekly backups now include `~/.openclaw/openclaw.json` and `~/.config/todoist-cli/config.json`; added `scripts/fix-todoist-auth.sh` plus `docs/todoist-recovery.md` so `td` auth can be restored from OpenClaw config without rediscovery.
- Keep the workspace GitHub repo current with meaningful state changes; push documentation/memory/ops updates regularly so GitHub reflects recent work instead of drifting stale.
- `pyatari` was driven all the way through the planned roadmap on 2026-04-08: core phases completed through **Phase 16**, then optional **Phase 17** peripherals and **Phase 18** undocumented opcodes. Latest `pyatari` phase commits: `08267c4` (Phase 15), `768815a` (Phase 16), `1000252` (Phase 17), `1eef027` (Phase 18).

## This Week (2026-04-06)
- RSS Feed Checker cron now uses `rss-digest.py` (same as morning digest) — both write to `data/rss-last-digest.json`, so "save #N" always matches the most recently delivered digest regardless of which cron ran
- Armin Ronacher's blog added to OPML → **24 feeds total**
- Anthropic 529 overload errors: known issue, surfaced to user rather than silently retried. Chris is on paid plan. Feature request raised with OpenClaw devs for retry-with-backoff.

## This Week (2026-04-04)
- Guido van Rossum website monitor: daily check, `scripts/web-change-tracker.py` (reusable)
- Goodreads activity monitor: every 4h, posts 📚 updates to Discord (NOT in OPML)
- Chris's Goodreads: https://www.goodreads.com/user/show/799620-christopher-patti

## This Week (2026-03-31 to 2026-04-03)
- RSS deduplication rewritten: tracks shown URLs in `data/rss-shown-urls.json` (NOT per-feed last-seen)
- RSS feeds now read from OPML only — `rss-feeds.opml` is single source of truth
- StepSecurity Blog added to feeds (23 total)
- Evening news: removed numbers — **"save #N" is RSS digest only, never news**
- Evening news spec saved to `docs/evening-news-spec.md` — check before changing
- Security audit completed: 0 criticals after fixes (Control UI origins, rate limiting, plugin pinned)
- Stray SSH key `id_ed25519_chrisgloria` deleted from puppy
- Post-restart sign-of-life protocol established
- RSS save workflow fixed: `rss-save.py` uses cached `data/rss-last-digest.json` — numbers always match

## This Week (2026-03-23 to 2026-03-30)
- Open Brain Memory System fully operational: PostgreSQL + pgvector + Ollama nomic-embed-text embeddings + 6 CRUD/health scripts + MCP server
- RSS feeds expanded to 22 (added Nushell Blog, Lobsters)
- **FIXED**: rss-digest.py now reads from OPML — no more hardcoded list
- News digest rewritten: 10 sources across 3 leanings, concurrent fetching
- BTC and ETH added to morning stock+crypto check cron (6 AM EDT)
- Memory maintenance cron created: Monday 9AM EDT

## Post-restart protocol (established 2026-04-03)
After every gateway restart, always send a "sign of life" to Discord:
**"🦞 Back online — OpenClaw [version], model: [current model], session active."**
Use the actual current runtime model, not a stale hardcoded one.
Never leave Chris wondering if I came back up.

## Rate Limit Awareness (learned 2026-03-31)
- Anthropic API has per-minute rate limits — blasting many calls at once (e.g. 8 cron updates + manual trigger + gateway restart in <2 min) will hit them
- **Rule:** When doing bulk operations (multiple cron updates, batch API calls), spread them out or at minimum don't immediately trigger test runs right after
- Serialize bursts: do the updates, wait a beat, then test

## About Me (Simplificus)
- Name: Simplificus 🧠
- Model: `openai-codex/gpt-5.4`
- Running on: OpenClaw
- Primary channel: Discord (`#openclaw`, channel id `1485734153617145998` on feoh's server)
- Identity established: 2026-03-23
- Git identity: `simplificus@openclaw`
- GitHub repo: `git@github.com:feoh/openclaw-workspace.git`
- SSH key: `/home/feoh/.openclaw/workspace/.ssh/id_ed25519` (deploy key added to GitHub repo)
- **Git push command**: `GIT_SSH_COMMAND="ssh -i /home/feoh/.openclaw/workspace/.ssh/id_ed25519 -o StrictHostKeyChecking=no" git push`

## Obsidian Vault
- Path: `/home/feoh/Documents/cloudyrock`
- **Boundary: NEVER delete notes unless Chris explicitly asks. This is non-negotiable.**

## About feoh (User)
- Uses openclaw-tui (gateway-client) on webchat
- Timezone: EST/EDT (Eastern Time — Somerville, MA, USA)
- Prefers: practical solutions, uv for Python package management
- Likes: RSS feeds, automation, clean tooling

## Communication
- **Primary channel:** Discord (#openclaw — Guild, channel id:1485734153617145998)
- **Fallback:** webchat
- **Emergency:** email feoh@feoh.org

## Infrastructure
- uv installed on host for Python package management
- Python virtual environment: `/home/feoh/.openclaw/workspace/.venv/` (contains feedparser)
- **uv** for Python package management (NOT pip)
- Git repo at `/home/feoh/.openclaw/workspace/` — committed as "Simplificus"

## RSS Digest — Core Requirements (from Chris, 2026-03-26)

Every RSS digest output (daily digest AND feed checker) MUST contain for each article:
1. **Article number**
2. **Article title**
3. **Article link**

Check this list BEFORE making any changes to RSS scripts or cron jobs.

## RSS Daily Digest (established 2026-03-23)
- 19 feeds configured (see rss-feeds.opml)
- OPML source: Miniflux export
- Script: `scripts/rss-digest.py` (feedparser-based, clean & reliable)
- **Numbered entries** for easy selection: "save #3, #7, #12"
- Cron job: Daily at 08:00 UTC (cron ID: b7c00f31-369b-4cc6-998c-02205611b747)
- Workflow: user says "save #N" → I parse numbers, look up URLs, POST to linkding

## Linkding Integration
- API endpoint: `https://linkding.reedfish-regulus.ts.net/api/bookmarks/` ← **trailing slash required**
- API Key: `<LINKDING_API_KEY>` — stored locally in `.env`, never commit this
- Scripts read key from `LINKDING_API_KEY` env var or `.env` file
- Tag: `toread`
- POST format: `{"url": "<url>", "tag_names": ["toread"]}`
- 3420+ bookmarks already saved (as of 2026-03-23)

## Feed list (19 total):

**All:**
- Terence Eden's Blog — https://shkspr.mobi/blog/feed/
- Unfinished Bitness — https://unfinishedbitness.info/feed/

**Fun:**
- Blind Not Dumb — https://www.feoh.org/feed.atom
- John P. Murphy — https://johnpmurphy.net/feed/
- Zarf Updates — https://blog.zarfhome.com/feeds/posts/default

**Python:**
- Aeracode — https://aeracode.org/feed/atom/
- Anthony Shaw's blog — https://tonybaloney.github.io/rss.xml
- Deciphering Glyph — https://blog.glyph.im/feeds/all.atom.xml
- Hynek Schlawack — https://hynek.me/index.xml
- Daniel Roy Greenfeld — https://daniel.feldroy.com/feeds/atom.xml
- Michael Kennedy — https://mkennedy.codes/index.xml
- Ned Batchelder's blog — https://nedbatchelder.com/blog/rss.xml (RSS 1.0/RDF format)
- Simon Willison's Weblog — https://simonwillison.net/atom/everything/
- Tall, Snarky Canadian — https://snarky.ca/rss/

**Rust:**
- Chris Morgan's blog — https://chrismorgan.info/feed.xml
- matklad — https://matklad.github.io/feed.xml

**Technology:**
- Ars Technica — https://arstechnica.com/feed/?t=...
- Fujinet News — https://fujinet.online/feed/
- Kagi Blog — https://blog.kagi.com/rss.xml
- Zed A. Shaw — https://zedshaw.com/feed.atom

## Tools & Skills
- Linkding: https://linkding.reedfish-regulus.ts.net/bookmarks
- **uv** — preferred Python package manager (already installed, NOT pip)
- **feedparser** for RSS parsing (installed via uv into .venv)

## Key Decisions (2026-03-23)
- Use uv (not pip) for Python packages
- feedparser for RSS parsing (cleaner than homebrew XML parsing)
- RSS 1.0/RDF feeds require `http://purl.org/rss/1.0/` namespace (Ned Batchelder)
- Cron jobs for daily RSS: sessionTarget="isolated", delivery="announce"
- Linkding API requires trailing slash on URL (POST without it returns 301)
- Git SSH needs `-o StrictHostKeyChecking=no` flag for known_hosts
- **Never commit .ssh/ directory** — add to .gitignore

## Session Summary (2026-03-23)

### What we built today:
1. **RSS Daily Digest** — 19 feeds, feedparser script, numbered entries, daily 8AM cron
2. **Linkding integration** — bookmarks save via API (toread tag)
3. **GitHub repo** — pushed to git@github.com:feoh/openclaw-workspace.git
4. **uv + venv** — feedparser installed at ~/.openclaw/workspace/.venv/
5. **Memory/notes** — everything documented in MEMORY.md, TOOLS.md, daily notes

### First bookmarks saved to linkding (ids 6099-6105):
- #1 — AI & Law (Ars Technica)
- #2 — NASA satellite rescue (Ars Technica)
- #8 — Ned Batchelder Human.json
- #9 — Highlander 40 (Ars Technica)
- #14 — GDC: gloom and haruspicy (Zarf)
- #20 — Twine and Zork at GDC (Zarf)
- #28 — What Is Code Review For? (Glyph)
- #30 — Total Recall (Unfinished Bitness)

### Important lessons:
- SSH private key accidentally exposed in commit — used git filter-branch to clean, regenerated key
- Linkding POST requires trailing slash on URL (301 redirect drops body without it)
- Deploy keys: each regeneration = new key, must update GitHub deploy key settings

## Session Summary — 2026-03-27

### Open Brain Memory System (Built Today)
Chris provided a spec document for building a database-backed memory layer for OpenClaw. We built the complete system:

**Infrastructure:**
- PostgreSQL 16.13 + pgvector 0.6.0 on localhost:5432
- Database: `openclaw`, User: `simplificus` (password in `.env`)
- Embedding model: `nomic-embed-text` via Ollama (768-dim vectors)

**Scripts created:**
- `scripts/openbrain-schema.py` — creates memory_objects table
- `scripts/openbrain-write.py` — save with auto-embedding
- `scripts/openbrain-search.py` — keyword + semantic search
- `scripts/openbrain-promote.py` — curation (private→controlled→public)
- `scripts/openbrain-health.py` — JSON health snapshot
- `scripts/openbrain-mcp.py` — MCP server for external tool integration

**Schema fields:** id, title, summary, body, lane (private/controlled/public), obj_type, domain_tags, provenance, confidence, source_links, embedding, timestamps, curated, promoted_at

**Spec compliance:** private-first, explicit promotion, health snapshots, fail-open

### Other Accomplishments
- Fixed RSS Feed Checker cron — now reports count, doesn't auto-save
- Updated RSS digest format: numbered list with article number, title, link
- Added AMZN stock check cron (6 AM EDT daily)
- Removed obsolete VMs from IP assignment notes (zima, quartermaster, distra, retrodev)
- Cookie is a Chiweenie (Dachshund × Chihuahua) — photo saved to assets/
- uv emphasized as preferred Python package manager (not pip)

### Cron Jobs (8 total)
| Task | Schedule |
|------|----------|
| RSS Daily Digest | Daily 8 AM EDT |
| RSS Feed Checker | 9 AM & 9 PM EDT |
| AMZN Stock Check | Daily 6 AM EDT |
| Daily News Digest | 6 PM EDT |
| Track Linkding Saves | Noon EDT |
| Weekly Memory Maintenance | Mon 9 AM EDT |
| Oh My Zsh Plugin Monitor | Mon 10 AM EDT |
| Pixelfed Ferret Watch | Thu 11 AM EDT |
