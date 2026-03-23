# MEMORY.md — Long-Term Memory

## About Me (Simplificus)
- Name: Simplificus 🧠
- Identity established: 2026-03-23
- Git identity: `simplificus@openclaw`

## About feoh (User)
- Uses openclaw-tui (gateway-client) on webchat
- Timezone: UTC
- Prefers: practical solutions, uv for Python package management
- Likes: RSS feeds, automation, clean tooling

## Infrastructure
- uv installed on host for Python package management
- Python virtual environment: `/home/feoh/.openclaw/workspace/.venv/` (contains feedparser)
- Git repo at `/home/feoh/.openclaw/workspace/` — committed as "Simplificus"

## RSS Daily Digest (established 2026-03-23)
- 19 feeds configured (see rss-feeds.opml)
- OPML source: Miniflux export
- Script: `scripts/rss-digest.py` (feedparser-based, clean & reliable)
- **Numbered entries** for easy selection: "save #3, #7, #12"
- Cron job: Daily at 08:00 UTC (cron ID: b7c00f31-369b-4cc6-998c-02205611b747)
- Last run: 2026-03-23 (first digest delivered)
- Workflow: user says "save #N" → I parse numbers, look up URLs, POST to linkding

## Linkding Integration
- API endpoint: `https://linkding.reedfish-regulus.ts.net/api/bookmarks/` ← **trailing slash required**
- API Key: stored in TOOLS.md
- Tag: `toread`
- POST format: `{"url": "<url>", "tag_names": ["toread"]}`
- 3420+ bookmarks already saved (as of 2026-03-23)

### Feed list (19 total):
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
- Ned Batchelder's blog — https://nedbatchelder.com/blog/rss.xml
- Simon Willison's Weblog — https://simonwillison.net/atom/everything/
- Tall, Snarky Canadian — https://snarky.ca/rss/

**Rust:**
- Chris Morgan's blog — https://chrismorgan.info/feed.xml
- matklad — https://matklad.github.io/feed.xml

**Technology:**
- Ars Technica — https://arstechnica.com/feed/?t=...
- Kagi Blog — https://blog.kagi.com/rss.xml
- Zed A. Shaw — https://zedshaw.com/feed.atom

## Tools & Skills
- Linkding: https://linkding.reedfish-regulus.ts.net/bookmarks (API key stored in TOOLS.md)
- uv: preferred Python package manager

## Key Decisions
- Use uv (not pip) for Python packages
- feedparser for RSS parsing (cleaner than homebrew XML parsing)
- RSS 1.0/RDF feeds require `http://purl.org/rss/1.0/` namespace (Ned Batchelder)
- Cron jobs for daily RSS: sessionTarget="isolated", delivery="announce"
