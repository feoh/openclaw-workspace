#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain — Search memory objects
Usage: python3 openbrain-search.py "query" [--lane private] [--type note] [--limit 10]
"""

import psycopg
import os
import argparse
from dotenv import load_dotenv
load_dotenv()


def search_memory(query, lane=None, obj_type=None, domain_tag=None, limit=10, include_body=False):
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    # Build query with optional filters
    sql = """
        SELECT id, title, summary, lane, obj_type, domain_tags, provenance, confidence, 
               created_at, freshness_ts, curated
    """
    if include_body:
        sql += ", body"
    
    sql += """
        FROM memory_objects
        WHERE (
            title ILIKE %s 
            OR summary ILIKE %s 
            OR body ILIKE %s
        )
    """
    params = [f'%{query}%', f'%{query}%', f'%{query}%']
    
    if lane:
        sql += " AND lane = %s"
        params.append(lane)
    
    if obj_type:
        sql += " AND obj_type = %s"
        params.append(obj_type)
    
    if domain_tag:
        sql += " AND %s = ANY(domain_tags)"
        params.append(domain_tag)
    
    sql += " ORDER BY freshness_ts DESC LIMIT %s"
    params.append(limit)
    
    result = conn.execute(sql, params)
    rows = result.fetchall()
    
    return rows


def format_results(rows, include_body=False):
    if not rows:
        return "No results found."
    
    lines = []
    for row in rows:
        id_, title, summary, lane, obj_type, tags, provenance, confidence, created, freshness, curated = row[:11]
        lines.append(f"**{id_}.** {title}")
        lines.append(f"   Lane: {lane} | Type: {obj_type} | Confidence: {confidence}%")
        if tags:
            lines.append(f"   Tags: {', '.join(tags)}")
        if summary:
            lines.append(f"   {summary}")
        if include_body and len(row) > 11 and row[11]:
            lines.append(f"   {row[11][:200]}...")
        lines.append(f"   Created: {created.date()} | Freshness: {freshness.date()}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Search memory objects')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--lane', choices=['private', 'controlled', 'public'])
    parser.add_argument('--type', dest='obj_type', help='Object type filter')
    parser.add_argument('--tag', dest='domain_tag', help='Domain tag filter')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--body', action='store_true', help='Include body text')
    
    args = parser.parse_args()
    
    rows = search_memory(
        args.query,
        lane=args.lane,
        obj_type=args.obj_type,
        domain_tag=args.domain_tag,
        limit=args.limit,
        include_body=args.body
    )
    
    print(format_results(rows, include_body=args.body))
