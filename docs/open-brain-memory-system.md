# Open Brain Memory System

This document describes the Open Brain memory system used in this workspace, in enough detail for another agent or operator to reimplement it from scratch.

## What it is

Open Brain is a lightweight structured memory layer for agents.

It combines:
- PostgreSQL for durable storage
- pgvector for semantic similarity search
- Ollama embeddings for local vector generation
- a small set of Python scripts for write, search, promotion, health checks, and MCP exposure

The design goal is simple:
- keep raw memory objects in a database
- support both keyword and semantic retrieval
- separate private vs shareable knowledge using lanes
- allow explicit curation and promotion over time
- fail open when embeddings are unavailable

## Core design principles

1. **Private first**
   - New memory objects default to the `private` lane.
   - Nothing becomes more widely reusable unless explicitly promoted.

2. **Explicit curation**
   - Promotion is a deliberate action.
   - `curated` and `promoted_at` track whether an object has been reviewed.

3. **Dual retrieval paths**
   - Keyword search is always available.
   - Semantic search is additive, not required for basic function.

4. **Graceful degradation**
   - If Ollama or embeddings fail, writes can still succeed.
   - The system should still function as a keyword memory store.

5. **Operational simplicity**
   - Everything is plain Python scripts.
   - No heavy orchestration layer is required.

## Stack

Current implementation:
- PostgreSQL 16+
- pgvector extension
- Ollama
- embedding model: `nomic-embed-text`
- Python with:
  - `psycopg`
  - `python-dotenv`
  - `ollama`
  - `mcp`
  - `pydantic`

## Environment and secrets

The current scripts load credentials from `.env`.

Expected variables:
- `POSTGRES_PASSWORD`
- optionally other `POSTGRES_*` variables for your own implementation

The current workspace implementation connects to:
- host: `localhost`
- port: `5432`
- database: `openclaw`
- user: `simplificus`

If you are reimplementing this elsewhere, make those values configurable instead of hardcoding them.

## Data model

All memory lives in one table: `memory_objects`.

### Schema

```sql
CREATE TABLE IF NOT EXISTS memory_objects (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    summary         TEXT,
    body            TEXT,
    lane            TEXT NOT NULL DEFAULT 'private',
    obj_type        TEXT NOT NULL DEFAULT 'note',
    domain_tags     TEXT[] DEFAULT '{}',
    provenance      TEXT,
    confidence      INTEGER DEFAULT 50,
    source_links    TEXT[] DEFAULT '{}',
    embedding       vector(1536),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    freshness_ts    TIMESTAMP DEFAULT NOW(),
    curated         BOOLEAN DEFAULT FALSE,
    promoted_at     TIMESTAMP
);
```

### Important note about embedding size

The current schema declares:
- `embedding vector(1536)`

But the documented operational model in this workspace is:
- `nomic-embed-text` via Ollama
- 768-dimensional embeddings

So if you are implementing this fresh, **verify your actual embedding dimension first** and make the pgvector column match it.

In other words:
- if your embedding model returns 768 dimensions, use `vector(768)`
- if it returns 1536, use `vector(1536)`

Do not blindly copy the column size without checking the live model output.

### Field meanings

- `id`: numeric primary key
- `title`: short durable label
- `summary`: compact human-readable gist
- `body`: full memory content
- `lane`: visibility / trust boundary
  - `private`
  - `controlled`
  - `public`
- `obj_type`: memory category such as:
  - `note`
  - `runbook`
  - `workflow`
  - `rubric`
  - `handoff`
- `domain_tags`: freeform tags for filtering and recall
- `provenance`: where the memory came from
- `confidence`: 0 to 100 trust score
- `source_links`: related URLs or references
- `embedding`: vector for semantic search
- `created_at`: first write time
- `updated_at`: last update time
- `freshness_ts`: recency signal used for sorting
- `curated`: whether it has been explicitly reviewed
- `promoted_at`: when it was promoted to a higher lane

## Indexes

Recommended indexes from the current implementation:

```sql
CREATE INDEX IF NOT EXISTS idx_memory_objects_lane
    ON memory_objects(lane);

CREATE INDEX IF NOT EXISTS idx_memory_objects_type
    ON memory_objects(obj_type);

CREATE INDEX IF NOT EXISTS idx_memory_objects_tags
    ON memory_objects USING GIN(domain_tags);

CREATE INDEX IF NOT EXISTS idx_memory_objects_freshness
    ON memory_objects(freshness_ts DESC);

CREATE INDEX IF NOT EXISTS idx_memory_objects_fts
    ON memory_objects USING GIN(
        to_tsvector('english', title || ' ' || COALESCE(summary, '') || ' ' || COALESCE(body, ''))
    );
```

If you want fast semantic search at scale, also add an ANN index appropriate to your pgvector version and workload.
The current implementation is small enough to work without one.

## Lanes and promotion model

The lane system is the heart of Open Brain.

### `private`
Default lane.

Use for:
- raw session takeaways
- user-specific context
- half-formed notes
- unreviewed observations

### `controlled`
Reviewed and shareable in limited contexts.

Use for:
- stable procedures
- handoff notes
- reusable but not fully public knowledge

### `public`
Highly reusable, curated knowledge.

Use for:
- polished workflows
- implementation guides
- reusable rubrics
- patterns safe to share broadly

### Promotion rules

The current implementation only allows upward movement:
- `private -> controlled`
- `controlled -> public`

No demotion path is implemented.

Promotion also:
- sets `curated = TRUE`
- sets `promoted_at`
- can raise `confidence`
- refreshes `freshness_ts`

This is intentionally conservative.

## Write path

Script:
- `scripts/openbrain-write.py`

Purpose:
- insert a memory object
- optionally generate an embedding first

### Current CLI

```bash
/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-write.py \
  "Title" \
  --summary "Short summary" \
  --body "Longer body text" \
  --lane private \
  --type note \
  --tags "tag1,tag2" \
  --provenance "where this came from"
```

### Write flow

1. Load env vars.
2. Connect to PostgreSQL.
3. Build embedding input from title + summary + body.
4. Ask Ollama for an embedding using `nomic-embed-text`.
5. Insert row into `memory_objects`.
6. Commit and return the new object ID.

### Failure handling

If embedding generation fails:
- emit a warning
- continue writing the object with `embedding = NULL`

That fail-open behavior is important. Memory capture should not depend on vector infrastructure always being healthy.

## Search path

Script:
- `scripts/openbrain-search.py`

Open Brain supports two retrieval modes.

### 1. Keyword search

Uses SQL `ILIKE` against:
- `title`
- `summary`
- `body`

Optional filters:
- `lane`
- `obj_type`
- `domain_tag`

Default ordering:
- `freshness_ts DESC`

### 2. Semantic search

Flow:
1. generate an embedding for the query
2. filter to rows where `embedding IS NOT NULL`
3. rank by pgvector distance
4. return similarity scores alongside metadata

The current SQL uses:
- `<=>` distance operator
- similarity displayed as `1 - distance`

### Current CLI examples

Keyword:

```bash
/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-search.py "rss bug"
```

Semantic:

```bash
/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-search.py "feed deduplication problem" --semantic
```

Filtered:

```bash
/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-search.py "postgres" --semantic --lane private --tag database --limit 5
```

## Promotion / curation path

Script:
- `scripts/openbrain-promote.py`

Purpose:
- inspect a memory object
- promote it to a higher lane
- optionally adjust confidence

### Current CLI

```bash
/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-promote.py 42 --lane controlled --confidence 80
```

### Behavior

- fetch current object state
- reject missing objects
- reject demotion or same-lane updates
- update lane, `curated`, `promoted_at`, and optionally `confidence`

This gives Open Brain a light editorial workflow rather than a flat dump of notes.

## Health monitoring

Script:
- `scripts/openbrain-health.py`

Purpose:
- produce a JSON health snapshot for automation and debugging

Output file:
- `data/open_brain_health.json`

### Checks performed

- database reachability
- Ollama responsiveness
- whether any rows have embeddings
- timestamp of the most recent memory update

### Status model

- `critical`: database unreachable
- `warn`: Ollama failed or vectors missing
- `ok`: all major subsystems healthy

### Why this matters

This lets other automation answer questions like:
- is memory working at all?
- are semantic features degraded?
- is the system capturing new knowledge?

## MCP server

Script:
- `scripts/openbrain-mcp.py`

Purpose:
- expose Open Brain as MCP tools over stdio

### Exposed tools

- `openbrain_search`
- `openbrain_write`
- `openbrain_get`
- `openbrain_promote`
- `openbrain_health`

### Run it

```bash
/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-mcp.py
```

Then attach it from an MCP client using stdio transport.

### Why MCP is useful

It lets other agents use the memory system as a tool instead of shelling out to ad hoc scripts.
That gives a cleaner contract and makes cross-agent reuse easier.

## Reference implementation layout

Current workspace files:

- `scripts/openbrain-schema.py`
- `scripts/openbrain-write.py`
- `scripts/openbrain-search.py`
- `scripts/openbrain-promote.py`
- `scripts/openbrain-health.py`
- `scripts/openbrain-mcp.py`

## Reimplementation recipe

If another agent wanted to rebuild this cleanly, I would recommend this order.

### Step 1: provision dependencies

- PostgreSQL
- pgvector extension
- Ollama
- embedding model available locally, for example:
  - `nomic-embed-text`

### Step 2: create the database objects

- create the database
- enable `pgvector`
- create `memory_objects`
- create the indexes

### Step 3: implement the write path

Start with:
- insert title / summary / body / lane / tags
- no embeddings yet if necessary

Then add:
- embedding generation
- optional source links and provenance

### Step 4: implement retrieval

Start with keyword search first.
That gives you a usable system immediately.

Then add semantic search with pgvector.

### Step 5: implement curation

Add promotion rules and confidence updates.
This is what turns a note store into a memory system.

### Step 6: implement health checks

At minimum, verify:
- DB reachable
- embedding provider reachable
- at least some vectors exist

### Step 7: expose via MCP or equivalent

If multiple agents need access, add a narrow tool surface rather than forcing everyone to manipulate SQL directly.

## Operational guidance

### What to store

Good memory objects include:
- decisions
- stable user preferences
- implementation notes
- repair procedures
- lessons from failures
- reusable checklists

### What not to store casually

Be careful with:
- secrets
- raw tokens
- personally sensitive content
- temporary noise with no future retrieval value

### Good object shape

A useful memory object usually has:
- a specific title
- a short summary
- a body with enough detail to act on later
- tags that reflect domain, not just keywords
- provenance explaining why it should be trusted

### Confidence guidance

Rough convention:
- `30-50`: weak or provisional
- `60-75`: decent working knowledge
- `80-90`: reviewed and trusted
- `95-100`: highly verified or canonical

## Known rough edges in the current implementation

This system works, but it is not pretending to be perfect.

### 1. Hardcoded DB connection values
Current scripts hardcode host, port, dbname, and username.
A cleaner implementation should use env vars or a config file.

### 2. Embedding dimension mismatch risk
As noted above, the schema and the documented embedding model need to be kept aligned.
Verify dimension first.

### 3. `updated_at` is not automatically maintained
The schema defines `updated_at`, but there is no trigger in the current implementation to refresh it on every update.
A stronger implementation should add one.

### 4. No ANN vector index yet
Fine for small datasets, but larger memory collections should add an HNSW or IVFFlat index.

### 5. Limited object lifecycle
There is no archiving, deduplication, merge workflow, or demotion path yet.
Those can be added later.

## Recommended improvements for a v2

If you are implementing your own version, I’d improve it like this:

1. make all DB settings configurable
2. verify embedding dimension automatically and fail early on mismatch
3. add an `updated_at` trigger
4. add ANN vector indexing
5. add hybrid ranking that blends text relevance, similarity, confidence, and freshness
6. add deduplication or near-duplicate detection
7. add explicit object versioning or supersession
8. add access-control rules if multiple users share the same memory store

## Minimal viable implementation checklist

If you want the smallest useful replica, build this:

- [ ] PostgreSQL + pgvector
- [ ] `memory_objects` table
- [ ] write script
- [ ] keyword search script
- [ ] semantic search script
- [ ] promotion script
- [ ] health snapshot script
- [ ] MCP wrapper or equivalent tool layer

That is enough to reproduce the current Open Brain architecture in practice.

## Related workspace notes

Implementation sources in this repo:
- `scripts/openbrain-schema.py`
- `scripts/openbrain-write.py`
- `scripts/openbrain-search.py`
- `scripts/openbrain-promote.py`
- `scripts/openbrain-health.py`
- `scripts/openbrain-mcp.py`

Historical notes:
- `memory/2026-03-27.md`
- `MEMORY.md`
