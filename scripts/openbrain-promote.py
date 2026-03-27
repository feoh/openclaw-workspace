#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain — Promote/Curate a memory object
Usage: python3 openbrain-promote.py <id> [--lane controlled] [--confidence 80]
"""

import psycopg
import os
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()


def promote_object(obj_id, target_lane='controlled', confidence=None):
    valid_lanes = ['private', 'controlled', 'public']
    if target_lane not in valid_lanes:
        raise ValueError(f"Invalid lane: {target_lane}. Must be one of {valid_lanes}")
    
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    # Get current state
    result = conn.execute("""
        SELECT id, title, lane, confidence, curated 
        FROM memory_objects WHERE id = %s
    """, (obj_id,))
    row = result.fetchone()
    
    if not row:
        conn.close()
        return None, "Object not found"
    
    current_id, title, current_lane, current_confidence, curated = row
    
    # Promotion rules
    lane_order = {'private': 0, 'controlled': 1, 'public': 2}
    
    if lane_order.get(target_lane, -1) <= lane_order.get(current_lane, -1):
        conn.close()
        return None, f"Cannot demote from {current_lane} to {target_lane}. Promotion only."
    
    # Build update
    updates = ["lane = %s", "curated = TRUE", "promoted_at = %s", "freshness_ts = %s"]
    params = [target_lane, datetime.now(timezone.utc), datetime.now(timezone.utc)]
    
    if confidence is not None:
        updates.append("confidence = %s")
        params.append(confidence)
    
    params.append(obj_id)
    
    conn.execute(f"UPDATE memory_objects SET {', '.join(updates)} WHERE id = %s", params)
    conn.commit()
    
    return {
        "id": obj_id,
        "title": title,
        "from_lane": current_lane,
        "to_lane": target_lane,
        "confidence": confidence or current_confidence,
        "curated": True
    }, "promoted"


def get_object(obj_id):
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )
    
    result = conn.execute("""
        SELECT id, title, summary, lane, obj_type, domain_tags, provenance, 
               confidence, created_at, freshness_ts, curated, promoted_at
        FROM memory_objects WHERE id = %s
    """, (obj_id,))
    row = result.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "id": row[0], "title": row[1], "summary": row[2], "lane": row[3],
        "obj_type": row[4], "domain_tags": row[5], "provenance": row[6],
        "confidence": row[7], "created_at": row[8], "freshness_ts": row[9],
        "curated": row[10], "promoted_at": row[11]
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Promote/curate a memory object')
    parser.add_argument('id', type=int, help='Object ID to promote')
    parser.add_argument('--lane', default='controlled', 
                       choices=['private', 'controlled', 'public'],
                       help='Target lane (default: controlled)')
    parser.add_argument('--confidence', type=int, help='Set confidence (0-100)')
    
    args = parser.parse_args()
    
    # First show current state
    obj = get_object(args.id)
    if not obj:
        print(f"Error: Object #{args.id} not found")
        exit(1)
    
    print(f"Current state of #{args.id}: {obj['title']}")
    print(f"  Lane: {obj['lane']} → {args.lane}")
    print(f"  Confidence: {obj['confidence']}%")
    print(f"  Curated: {obj['curated']}")
    
    if args.confidence:
        if args.confidence < 0 or args.confidence > 100:
            print("Error: Confidence must be 0-100")
            exit(1)
    
    result, msg = promote_object(args.id, target_lane=args.lane, confidence=args.confidence)
    
    if result:
        print(f"\n✓ {msg}: #{result['id']} '{result['title']}'")
        print(f"  Now in: {result['from_lane']} → {result['to_lane']}")
        print(f"  Confidence: {result['confidence']}%")
    else:
        print(f"\n✗ {msg}")
