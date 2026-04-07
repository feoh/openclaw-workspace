#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain — Write a memory object to the database with automatic embedding generation
Usage: python3 openbrain-write.py "title" "summary" "body" [--lane private] [--type note] [--tags tag1,tag2]
"""

import psycopg
import os
import sys
import argparse
from dotenv import load_dotenv
import ollama
load_dotenv()


def generate_embedding(text):
    """Generate embedding using nomic-embed-text via Ollama."""
    if not text:
        return None
    try:
        response = ollama.embeddings(model='nomic-embed-text', prompt=text[:10000])
        return response['embedding']
    except Exception as e:
        print(f"Warning: embedding generation failed: {e}", file=sys.stderr)
        return None


def write_memory(title, summary, body, lane='private', obj_type='note', 
                 domain_tags=None, provenance=None, source_links=None,
                 generate_embed=True):
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    tags = domain_tags or []
    links = source_links or []
    
    # Combine text for embedding
    embed_text = f"{title} {summary} {body}" if body else f"{title} {summary}"
    embedding = generate_embedding(embed_text) if generate_embed else None
    
    result = conn.execute("""
        INSERT INTO memory_objects (title, summary, body, lane, obj_type, domain_tags, provenance, source_links, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, (title, summary, body, lane, obj_type, tags, provenance, links, embedding))
    
    row = result.fetchone()
    conn.commit()
    return row[0], row[1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Write a memory object')
    parser.add_argument('title', help='Title')
    parser.add_argument('--summary', default='', help='Summary')
    parser.add_argument('--body', default='', help='Body text')
    parser.add_argument('--lane', default='private', choices=['private', 'controlled', 'public'])
    parser.add_argument('--type', dest='obj_type', default='note', help='Object type')
    parser.add_argument('--tags', default='', help='Comma-separated tags')
    parser.add_argument('--provenance', default='', help='Provenance note')
    parser.add_argument('--links', default='', help='Comma-separated source links')
    parser.add_argument('--no-embed', dest='no_embed', action='store_true', help='Skip embedding generation')
    
    args = parser.parse_args()
    
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    links = [l.strip() for l in args.links.split(',') if l.strip()]
    
    obj_id, created = write_memory(
        args.title, args.summary, args.body,
        lane=args.lane, obj_type=args.obj_type,
        domain_tags=tags, provenance=args.provenance or None,
        source_links=links,
        generate_embed=not args.no_embed
    )
    
    embed_note = " with embedding" if not args.no_embed else "without embedding"
    print(f"Created memory object #{obj_id} at {created}{embed_note}")
