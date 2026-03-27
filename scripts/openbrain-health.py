#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain — Health Snapshot Writer
Writes a JSON status file summarizing Open Brain health.
Run periodically via cron.
"""

import psycopg
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import ollama
load_dotenv()

HEALTH_FILE = "/home/feoh/.openclaw/workspace/data/open_brain_health.json"


def check_db_reachable():
    try:
        conn = psycopg.connect(
            host='localhost', port=5432, dbname='openclaw',
            user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', ''),
            connect_timeout=5
        )
        conn.execute("SELECT 1")
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def check_mcp_probe():
    """Check if Ollama is responsive."""
    try:
        models = ollama.list()
        return True, None
    except Exception as e:
        return False, str(e)


def check_vector_column():
    """Check if memory_objects table has embeddings."""
    try:
        conn = psycopg.connect(
            host='localhost', port=5432, dbname='openclaw',
            user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', ''),
            connect_timeout=5
        )
        result = conn.execute("SELECT COUNT(*) FROM memory_objects WHERE embedding IS NOT NULL")
        count = result.fetchone()[0]
        conn.close()
        return count > 0, count
    except Exception as e:
        return False, 0


def check_curation_fresh():
    """Check if curation has run recently."""
    try:
        conn = psycopg.connect(
            host='localhost', port=5432, dbname='openclaw',
            user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', ''),
            connect_timeout=5
        )
        result = conn.execute("SELECT MAX(updated_at) FROM memory_objects")
        last_update = result.fetchone()[0]
        conn.close()
        return last_update
    except:
        return None


def get_status(db_ok, mcp_ok, vector_populated):
    if not db_ok:
        return "critical", ["database unreachable"]
    if not mcp_ok:
        return "warn", ["MCP/Ollama probe failed"]
    if not vector_populated:
        return "warn", ["vector column unpopulated"]
    return "ok", []


def write_health_snapshot():
    # Run checks
    db_ok, db_err = check_db_reachable()
    mcp_ok, mcp_err = check_mcp_probe()
    vector_populated, embed_count = check_vector_column()
    last_curation = check_curation_fresh()
    
    status, reasons = get_status(db_ok, mcp_ok, vector_populated)
    
    snapshot = {
        "status": status,
        "reasons": reasons,
        "mcp_probe_ok": mcp_ok,
        "db_reachable": db_ok,
        "db_error": db_err if not db_ok else None,
        "mcp_error": mcp_err if not mcp_ok else None,
        "curation_fresh": last_curation.isoformat() if last_curation else None,
        "vector_column_populated": vector_populated,
        "embedding_count": embed_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fingerprint": f"{status}-{datetime.now(timezone.utc).date().isoformat()}"
    }
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(HEALTH_FILE), exist_ok=True)
    
    with open(HEALTH_FILE, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    return snapshot


if __name__ == '__main__':
    snapshot = write_health_snapshot()
    print(f"Health snapshot written: {snapshot['status'].upper()}")
    print(f"  DB reachable: {snapshot['db_reachable']}")
    print(f"  MCP probe OK: {snapshot['mcp_probe_ok']}")
    print(f"  Embeddings: {snapshot['embedding_count']}")
    print(f"  File: {HEALTH_FILE}")
