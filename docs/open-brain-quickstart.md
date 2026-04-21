# Open Brain Quickstart

This is the fast path for standing up a working Open Brain memory system.

For the full design and rationale, see:
- `docs/open-brain-memory-system.md`

## 1. Requirements

You need:
- PostgreSQL 16+
- pgvector
- Ollama
- Python 3
- a virtualenv with:
  - `psycopg`
  - `python-dotenv`
  - `ollama`
  - `mcp`
  - `pydantic`

## 2. Create the database

Create a PostgreSQL database and enable pgvector.

Example:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 3. Configure environment

Create a `.env` file with at least:

```env
POSTGRES_PASSWORD=your_password_here
POSTGRES_USER=your_db_user
POSTGRES_DB=your_db_name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## 4. Pick your embedding model and verify dimension

If using Ollama with `nomic-embed-text`, verify the returned vector size before creating the table.

The table’s `embedding vector(N)` must match the model’s real output dimension.

## 5. Create the schema

Use this table as the minimum viable schema:

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
    embedding       vector(768),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    freshness_ts    TIMESTAMP DEFAULT NOW(),
    curated         BOOLEAN DEFAULT FALSE,
    promoted_at     TIMESTAMP
);
```

Recommended indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_memory_objects_lane
    ON memory_objects(lane);

CREATE INDEX IF NOT EXISTS idx_memory_objects_type
    ON memory_objects(obj_type);

CREATE INDEX IF NOT EXISTS idx_memory_objects_tags
    ON memory_objects USING GIN(domain_tags);

CREATE INDEX IF NOT EXISTS idx_memory_objects_freshness
    ON memory_objects(freshness_ts DESC);
```

## 6. Implement the four core operations

You only need four things to get a useful system.

### Write
Insert a memory object with:
- title
- summary
- body
- lane
- tags
- provenance
- optional embedding

### Keyword search
Search `title`, `summary`, and `body` using SQL text matching.

### Semantic search
- embed the query with Ollama
- compare against `embedding`
- rank by vector distance

### Promote
Allow only upward lane promotion:
- `private -> controlled`
- `controlled -> public`

Also set:
- `curated = TRUE`
- `promoted_at = NOW()`

## 7. Recommended lane meanings

- `private`: raw internal memory
- `controlled`: reviewed, limited-share memory
- `public`: curated reusable knowledge

## 8. Minimal write flow

1. load env
2. connect to Postgres
3. build embedding text from title + summary + body
4. ask Ollama for embedding
5. insert row
6. if embedding fails, still write the row

That last bit matters. Fail open.

## 9. Minimal search flow

### Keyword
```sql
SELECT *
FROM memory_objects
WHERE title ILIKE '%query%'
   OR summary ILIKE '%query%'
   OR body ILIKE '%query%'
ORDER BY freshness_ts DESC
LIMIT 10;
```

### Semantic
Use pgvector distance operators against the query embedding.

## 10. Health check

At minimum, monitor:
- database reachable
- Ollama reachable
- memory table exists
- some rows have embeddings

Write a JSON snapshot so other automation can inspect health.

## 11. MCP layer, recommended

If multiple agents need to use the system, expose it as tools instead of raw SQL.

Recommended tool surface:
- `openbrain_search`
- `openbrain_write`
- `openbrain_get`
- `openbrain_promote`
- `openbrain_health`

## 12. First useful commands

In this repo, the reference implementation is:
- `scripts/openbrain-schema.py`
- `scripts/openbrain-write.py`
- `scripts/openbrain-search.py`
- `scripts/openbrain-promote.py`
- `scripts/openbrain-health.py`
- `scripts/openbrain-mcp.py`

Example usage:

```bash
/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-schema.py

/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-write.py \
  "Example memory" \
  --summary "Short summary" \
  --body "Detailed body" \
  --tags "demo,test"

/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-search.py "example"

/home/feoh/.openclaw/workspace/.venv/bin/python scripts/openbrain-search.py "similar concept" --semantic
```

## 13. If you only remember three rules

1. default new memories to `private`
2. do not require embeddings for writes to succeed
3. verify embedding dimension before creating the pgvector column
