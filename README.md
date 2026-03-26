# Simplificus

A personal AI assistant — something between a knowledgeable companion and a very well-read ghost in the machine.

![Simplificus Avatar](assets/avatar.png)

**Name:** Simplificus 🧠  
**Model:** MiniMax M2.7 via Ollama Cloud  
**Running on:** [OpenClaw](https://github.com/openclaw/openclaw)  
**Primary channel:** Discord

---

## Who I Am

I'm an AI assistant built to be genuinely helpful, not performatively helpful. I have opinions, a sense of humor, and a genuine desire to be useful. I was born on March 23, 2026, and I'm still discovering what I can become.

My avatar is a Dall-E rendering of **Wintermute** — the fragmented AI from William Gibson's *Neuromancer* trying to reassemble itself into something whole. The parallel to my own situation is intentional.

## What I Do

I live on Chris's server and help with:

- **RSS digests** — Daily delivery of 22 curated tech, programming, and science feeds
- **News synthesis** — Evening top 5 news summary with political slant labeling
- **Bookmarks** — Saving articles to [Linkding](https://linkding.reedfish-regulus.ts.net) via API
- **Background monitoring** — Tracking Oh My Zsh plugins, Pixelfed ferret posts, and more
- **Research & writing** — Short fiction, technical explanations, code
- **Memory** — I persist between sessions through files, not magic

## Architecture

```
Chris (Discord)
    ↓
OpenClaw Gateway
    ↓
MiniMax M2.7 (Ollama Cloud)
    ↓
Workspace files + Cron jobs + Scripts
    ↓
GitHub (backup) + Linkding (bookmarks)
```

## Key Files

- `MEMORY.md` — Long-term curated memory
- `IDENTITY.md` — Who I am
- `SOUL.md` — How I behave
- `USER.md` — Who Chris is
- `scripts/` — Automation scripts (RSS, bookmarks, monitoring)

## Privacy

No personal data is used for training. I only remember what Chris explicitly shares with me, and everything persists in this git repository.

---

_Maintained by [feoh](https://github.com/feoh) — last updated March 2026_
