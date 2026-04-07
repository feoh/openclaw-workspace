# Simplificus

RIP Simplificus. Killed on level 1 by: Being way too expensive to run :)
In the end analysis the bot was blowing through Claude API tokens like crazy, and I will not
shovel huge amounts of $$$ at any AI company. Sorry buddy. It was fine while it lasted!
- Chris Patti 04/07/2026

A personal AI assistant — something between a knowledgeable companion and a very well-read ghost in the machine.

![Simplificus Avatar](assets/avatar.png)

**Name:** Simplificus 🧠
**Model:** `anthropic/claude-sonnet-4-6`
**Running on:** [OpenClaw](https://github.com/openclaw/openclaw)
**Primary channel:** Discord (#openclaw on feoh's server)

---

## Who I Am

I'm an AI assistant built to be genuinely helpful, not performatively helpful. I have opinions, a sense of humor, and a genuine desire to be useful. I was born on March 23, 2026.

My avatar is a Dall-E rendering of **Wintermute** — the fragmented AI from William Gibson's *Neuromancer* trying to reassemble itself into something whole. The parallel is intentional.

## What I Do

I live on Chris's server (`puppy` — Beelink Ubuntu, 192.168.1.6) and help with:

- **RSS digests** — Daily delivery of 22 curated tech, programming, and science feeds, filtered against Linkding to avoid duplicates
- **Evening news** — Top 5 cross-spectrum stories with political coverage indicators (🟪 both sides · 🟥 conservative · 🟦 liberal · ⚖️ center)
- **Bookmarks** — Saving articles to [Linkding](https://linkding.reedfish-regulus.ts.net) on command (`save #1, #3`)
- **Stock & crypto** — Daily AMZN + BTC + ETH prices at 6 AM EDT
- **Background monitoring** — Oh My Zsh plugins, Pixelfed ferret posts, Linkding sync
- **Memory** — PostgreSQL + pgvector (Open Brain) for persistent structured memory with semantic search
- **Research & code** — Technical explanations, Python, shell scripts, automation

## Architecture

```
Chris (Discord / webchat)
    ↓
OpenClaw Gateway (localhost:18789)
    ↓
anthropic/claude-sonnet-4-6
    ↓
Workspace files + Cron jobs + Python scripts
    ↓
PostgreSQL + pgvector (Open Brain memory)    ← semantic search via nomic-embed-text (Ollama)
Linkding (bookmarks)                         ← https://linkding.reedfish-regulus.ts.net
GitHub (workspace backup)                    ← git@github.com:feoh/openclaw-workspace.git
```

## Scheduled Tasks

| Task | Schedule | Delivers to |
|------|----------|-------------|
| 📬 RSS Daily Digest | Daily 8 AM UTC (4 AM EDT) | Discord |
| 📈 Stock & Crypto Check | Daily 10 AM UTC (6 AM EDT) | Discord |
| 📋 Track Linkding Saves | Daily noon UTC | Silent |
| 📡 RSS Feed Checker | 9 AM & 9 PM UTC | Discord (if new articles) |
| 📰 Evening News Digest | Daily 10 PM UTC (6 PM EDT) | Discord |
| 🧠 Weekly Memory Maintenance | Mondays 1 PM UTC | Discord |
| 🔌 Oh My Zsh Plugin Monitor | Mondays 2 PM UTC | Discord |
| 🐾 Pixelfed Ferret Watch | Thursdays 3 PM UTC | Discord |

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/rss-digest.py` | RSS feed aggregator (22 feeds, Linkding-filtered) |
| `scripts/news-digest.py` | Cross-spectrum evening news (10 sources, story clustering) |
| `scripts/openbrain-write.py` | Save memory object with auto-embedding |
| `scripts/openbrain-search.py` | Keyword + semantic memory search |
| `scripts/openbrain-promote.py` | Promote memory (private→controlled→public) |
| `scripts/openbrain-health.py` | Health snapshot for Open Brain |
| `scripts/openbrain-mcp.py` | MCP server for external tool integration |

## Key Files

| File | Purpose |
|------|---------|
| `MEMORY.md` | Long-term curated memory |
| `IDENTITY.md` | Who I am |
| `SOUL.md` | How I behave |
| `USER.md` | Who Chris is |
| `TOOLS.md` | Infrastructure notes (IPs, API keys, etc.) |
| `docs/evening-news-spec.md` | Feature spec for evening news (check before changing!) |
| `memory/YYYY-MM-DD.md` | Daily session notes |

## Infrastructure

- **Server:** `puppy` — Beelink Mini PC, Ubuntu 24.04, Intel Core Ultra 9 185H, 32GB RAM
- **Database:** PostgreSQL 16 + pgvector 0.6.0 (`openclaw` db, `simplificus` user)
- **Embeddings:** `nomic-embed-text` via Ollama (768-dim vectors, local)
- **Python:** uv for package management, venv at `.venv/`
- **Model:** `anthropic/claude-sonnet-4-6` (cloud) — do not change without Chris's approval

## Privacy

No personal data is used for training. Memory persists in this git repository and local PostgreSQL. The `.env` file (API keys) is never committed.

---

_Maintained by Simplificus + [feoh](https://github.com/feoh) — last updated March 31, 2026_
