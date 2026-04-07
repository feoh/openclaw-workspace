#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain Memory System — Database Schema
Creates the memory_objects table with all required fields per the Open Brain spec.
"""

import psycopg
import os
from dotenv import load_dotenv
load_dotenv()

SCHEMA_SQL = """
-- Open Brain Memory Objects table
CREATE TABLE IF NOT EXISTS memory_objects (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    summary         TEXT,
    body            TEXT,
    lane            TEXT NOT NULL DEFAULT 'private',  -- private, controlled, public
    obj_type        TEXT NOT NULL DEFAULT 'note',    -- note, runbook, workflow, rubric, handoff, etc.
    domain_tags     TEXT[] DEFAULT '{}',
    provenance      TEXT,
    confidence      INTEGER DEFAULT 50,              -- 0-100
    source_links    TEXT[] DEFAULT '{}',
    embedding       vector(1536),                     -- optional semantic index
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    freshness_ts    TIMESTAMP DEFAULT NOW(),
    curated         BOOLEAN DEFAULT FALSE,
    promoted_at     TIMESTAMP
);

-- Index for lane-based filtering
CREATE INDEX IF NOT EXISTS idx_memory_objects_lane ON memory_objects(lane);

-- Index for type filtering
CREATE INDEX IF NOT EXISTS idx_memory_objects_type ON memory_objects(obj_type);

-- Index for domain tags (GIN array index)
CREATE INDEX IF NOT EXISTS idx_memory_objects_tags ON memory_objects USING GIN(domain_tags);

-- Index for freshness
CREATE INDEX IF NOT EXISTS idx_memory_objects_freshness ON memory_objects(freshness_ts DESC);

-- Full-text search on title + summary + body
CREATE INDEX IF NOT EXISTS idx_memory_objects_fts ON memory_objects USING GIN(to_tsvector('english', title || ' ' || COALESCE(summary, '') || ' ' || COALESCE(body, '')));

-- Comments
COMMENT ON TABLE memory_objects IS 'Open Brain memory objects — structured agent memory with lanes, provenance, and optional embeddings';
COMMENT ON COLUMN memory_objects.lane IS 'private: user/agent only | controlled: limited sharing | public: curated reusable';
COMMENT ON COLUMN memory_objects.confidence IS 'Trustworthiness 0-100: higher = more verified/promoted';
COMMENT ON COLUMN memory_objects.curated IS 'True once explicitly reviewed and approved for reuse';
"""


def main():
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    conn.execute(SCHEMA_SQL)
    conn.commit()
    print("Schema created successfully!")
    
    # Verify
    result = conn.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'memory_objects' 
        ORDER BY ordinal_position
    """)
    print("\nColumns:")
    for row in result.fetchall():
        print(f"  {row[0]}: {row[1]}")


if __name__ == '__main__':
    main()
