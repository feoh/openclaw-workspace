#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain — Write a memory object to the database
Usage: python3 openbrain-write.py "title" "summary" "body" [--lane private] [--type note] [--tags tag1,tag2]
"""

import psycopg
import os
import sys
import argparse
from dotenv import load_dotenv
load_dotenv()


def write_memory(title, summary, body, lane='private', obj_type='note', domain_tags=None, provenance=None, source_links=None):
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    tags = domain_tags or []
    links = source_links or []
    
    result = conn.execute("""
        INSERT INTO memory_objects (title, summary, body, lane, obj_type, domain_tags, provenance, source_links)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, (title, summary, body, lane, obj_type, tags, provenance, links))
    
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
    
    args = parser.parse_args()
    
    tags = [t.strip() for t in args.tags.split(',') if t.strip()]
    links = [l.strip() for l in args.links.split(',') if l.strip()]
    
    obj_id, created = write_memory(
        args.title, args.summary, args.body,
        lane=args.lane, obj_type=args.obj_type,
        domain_tags=tags, provenance=args.provenance or None,
        source_links=links
    )
    
    print(f"Created memory object #{obj_id} at {created}")
