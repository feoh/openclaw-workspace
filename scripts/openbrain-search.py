#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain — Search memory objects (keyword + vector similarity)
Usage: python3 openbrain-search.py "query" [--lane private] [--type note] [--limit 10] [--semantic]
"""

import psycopg
import os
import argparse
from dotenv import load_dotenv
import ollama
load_dotenv()


def search_memory_keyword(query, lane=None, obj_type=None, domain_tag=None, limit=10, include_body=False):
    """Traditional keyword/ILKE search."""
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    sql = "SELECT id, title, summary, lane, obj_type, domain_tags, provenance, confidence, created_at, freshness_ts, curated"
    if include_body:
        sql += ", body"
    sql += " FROM memory_objects WHERE (title ILIKE %s OR summary ILIKE %s OR body ILIKE %s)"
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
    return result.fetchall()


def search_memory_semantic(query, lane=None, obj_type=None, domain_tag=None, limit=10, include_body=False):
    """Vector similarity search using Ollama embeddings."""
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    # Generate embedding for query
    try:
        response = ollama.embeddings(model='nomic-embed-text', prompt=query)
        query_embedding = response['embedding']
    except Exception as e:
        print(f"Warning: embedding generation failed: {e}", file=sys.stderr)
        return []
    
    # Build SQL with vector similarity
    sql = """
        SELECT id, title, summary, lane, obj_type, domain_tags, provenance, confidence, 
               created_at, freshness_ts, curated,
               1 - (embedding <=> %s::vector) AS similarity
    """
    if include_body:
        sql += ", body"
    sql += " FROM memory_objects WHERE embedding IS NOT NULL"
    params = [query_embedding]
    
    if lane:
        sql += " AND lane = %s"
        params.append(lane)
    if obj_type:
        sql += " AND obj_type = %s"
        params.append(obj_type)
    if domain_tag:
        sql += " AND %s = ANY(domain_tags)"
        params.append(domain_tag)
    
    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.append(query_embedding)
    params.append(limit)
    
    result = conn.execute(sql, params)
    return result.fetchall()


def format_results(rows, include_body=False, show_similarity=False):
    if not rows:
        return "No results found."
    
    lines = []
    for row in rows:
        base_cols = 11
        similarity = row[11] if show_similarity and len(row) > 11 else None
        id_, title, summary, lane, obj_type, tags, provenance, confidence, created, freshness, curated = row[:11]
        
        sim_str = f" | Similarity: {similarity:.2%}" if similarity is not None else ""
        lines.append(f"**{id_}.** {title}")
        lines.append(f"   Lane: {lane} | Type: {obj_type} | Confidence: {confidence}%{sim_str}")
        if tags:
            lines.append(f"   Tags: {', '.join(tags)}")
        if summary:
            lines.append(f"   {summary}")
        if include_body and len(row) > base_cols and row[base_cols]:
            lines.append(f"   {row[base_cols][:200]}...")
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
    parser.add_argument('--semantic', action='store_true', help='Use vector similarity search')
    
    args = parser.parse_args()
    
    if args.semantic:
        rows = search_memory_semantic(
            args.query,
            lane=args.lane,
            obj_type=args.obj_type,
            domain_tag=args.domain_tag,
            limit=args.limit,
            include_body=args.body
        )
        output = format_results(rows, include_body=args.body, show_similarity=True)
    else:
        rows = search_memory_keyword(
            args.query,
            lane=args.lane,
            obj_type=args.obj_type,
            domain_tag=args.domain_tag,
            limit=args.limit,
            include_body=args.body
        )
        output = format_results(rows, include_body=args.body)
    
    print(output)
