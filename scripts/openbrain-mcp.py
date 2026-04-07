#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Open Brain MCP Server
Exposes Open Brain memory tools via the Model Context Protocol.

Run with: python3 openbrain-mcp.py
Then connect via OpenClaw MCP client config.
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl
import psycopg
import ollama

# Open Brain MCP Server instance
server = Server("openbrain")

# Database connection helper
def get_db():
    return psycopg.connect(
        host='localhost', port=5432, dbname='openclaw',
        user='simplificus', password=os.environ.get('POSTGRES_PASSWORD', '')
    )


# Tool: search_memory
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="openbrain_search",
            description="Search Open Brain memory objects. Use semantic=True for AI-powered similarity search, or False for keyword matching.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "semantic": {"type": "boolean", "description": "Use vector similarity search (default: true)"},
                    "lane": {"type": "string", "enum": ["private", "controlled", "public"], "description": "Filter by lane"},
                    "obj_type": {"type": "string", "description": "Filter by object type"},
                    "domain_tag": {"type": "string", "description": "Filter by domain tag"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="openbrain_write",
            description="Write a new memory object to Open Brain. Returns the new object ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title"},
                    "summary": {"type": "string", "description": "Short summary"},
                    "body": {"type": "string", "description": "Full body text"},
                    "lane": {"type": "string", "enum": ["private", "controlled", "public"], "description": "Privacy lane (default: private)"},
                    "obj_type": {"type": "string", "description": "Object type (default: note)"},
                    "domain_tags": {"type": "string", "description": "Comma-separated tags"},
                    "provenance": {"type": "string", "description": "Source/provenance note"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="openbrain_get",
            description="Get a specific memory object by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Object ID"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="openbrain_promote",
            description="Promote a memory object to a higher lane (controlled or public).",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Object ID"},
                    "target_lane": {"type": "string", "enum": ["controlled", "public"], "description": "Target lane"},
                    "confidence": {"type": "integer", "description": "Set confidence (0-100)"}
                },
                "required": ["id", "target_lane"]
            }
        ),
        Tool(
            name="openbrain_health",
            description="Get Open Brain health status and statistics.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "openbrain_search":
        return await tool_search(arguments)
    elif name == "openbrain_write":
        return await tool_write(arguments)
    elif name == "openbrain_get":
        return await tool_get(arguments)
    elif name == "openbrain_promote":
        return await tool_promote(arguments)
    elif name == "openbrain_health":
        return await tool_health(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def tool_search(args):
    query = args.get("query", "")
    semantic = args.get("semantic", True)
    lane = args.get("lane")
    obj_type = args.get("obj_type")
    domain_tag = args.get("domain_tag")
    limit = args.get("limit", 10)
    
    conn = get_db()
    
    try:
        if semantic:
            # Vector similarity search
            try:
                response = ollama.embeddings(model='nomic-embed-text', prompt=query)
                query_embedding = response['embedding']
            except Exception as e:
                return [TextContent(type="text", text=f"Embedding generation failed: {e}")]
            
            sql = """
                SELECT id, title, summary, lane, obj_type, domain_tags, confidence, 
                       1 - (embedding <=> %s::vector) AS similarity
                FROM memory_objects WHERE embedding IS NOT NULL
            """
            params = [query_embedding]
        else:
            # Keyword search
            sql = """
                SELECT id, title, summary, lane, obj_type, domain_tags, confidence, 1.0 AS similarity
                FROM memory_objects
                WHERE title ILIKE %s OR summary ILIKE %s OR body ILIKE %s
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
        
        sql += f" ORDER BY similarity DESC LIMIT {limit}"
        
        if semantic:
            params.append(query_embedding)
        
        result = conn.execute(sql, params)
        rows = result.fetchall()
        
        if not rows:
            return [TextContent(type="text", text="No results found.")]
        
        lines = []
        for row in rows:
            sim = f"{row[7]:.1%}" if row[7] else "N/A"
            tags = ', '.join(row[5]) if row[5] else ''
            lines.append(f"**{row[0]}.** {row[1]}")
            lines.append(f"   {row[3]} | {row[4]} | conf: {row[6]}% | sim: {sim}")
            if row[2]:
                lines.append(f"   {row[2]}")
            if tags:
                lines.append(f"   [{tags}]")
            lines.append("")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    finally:
        conn.close()


async def tool_write(args):
    title = args["title"]
    summary = args.get("summary", "")
    body = args.get("body", "")
    lane = args.get("lane", "private")
    obj_type = args.get("obj_type", "note")
    tags = [t.strip() for t in args.get("domain_tags", "").split(",") if t.strip()]
    provenance = args.get("provenance")
    
    conn = get_db()
    
    try:
        # Generate embedding
        embed_text = f"{title} {summary} {body}"
        try:
            response = ollama.embeddings(model='nomic-embed-text', prompt=embed_text)
            embedding = response['embedding']
        except:
            embedding = None
        
        result = conn.execute("""
            INSERT INTO memory_objects (title, summary, body, lane, obj_type, domain_tags, provenance, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (title, summary, body, lane, obj_type, tags, provenance, embedding))
        
        row = result.fetchone()
        conn.commit()
        
        return [TextContent(type="text", text=f"Created memory object #{row[0]} at {row[1]}")]
    
    finally:
        conn.close()


async def tool_get(args):
    obj_id = args["id"]
    conn = get_db()
    
    try:
        result = conn.execute("""
            SELECT id, title, summary, body, lane, obj_type, domain_tags, provenance,
                   confidence, created_at, freshness_ts, curated, promoted_at
            FROM memory_objects WHERE id = %s
        """, (obj_id,))
        row = result.fetchone()
        
        if not row:
            return [TextContent(type="text", text=f"Object #{obj_id} not found")]
        
        tags = ', '.join(row[6]) if row[6] else ''
        lines = [
            f"**#{row[0]}:** {row[1]}",
            f"Lane: {row[4]} | Type: {row[5]} | Confidence: {row[8]}%",
            f"Tags: [{tags}]",
            f"Created: {row[9]} | Updated: {row[10]}",
            f"Curated: {row[11]} | Promoted: {row[12]}",
            "",
            f"Summary: {row[2]}",
        ]
        if row[3]:
            lines.append(f"\nBody:\n{row[3][:500]}")
        if row[7]:
            lines.append(f"\nProvenance: {row[7]}")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    finally:
        conn.close()


async def tool_promote(args):
    obj_id = args["id"]
    target_lane = args["target_lane"]
    confidence = args.get("confidence")
    
    conn = get_db()
    
    try:
        from datetime import datetime, timezone
        updates = ["lane = %s", "curated = TRUE", "promoted_at = NOW()"]
        params = [target_lane]
        
        if confidence is not None:
            updates.append("confidence = %s")
            params.append(confidence)
        
        params.append(obj_id)
        
        conn.execute(f"UPDATE memory_objects SET {', '.join(updates)} WHERE id = %s", params)
        conn.commit()
        
        return [TextContent(type="text", text=f"✓ Promoted #{obj_id} to {target_lane}")]
    
    finally:
        conn.close()


async def tool_health(args):
    conn = get_db()
    
    try:
        # DB check
        conn.execute("SELECT 1")
        db_ok = True
        
        # Stats
        total = conn.execute("SELECT COUNT(*) FROM memory_objects").fetchone()[0]
        with_embed = conn.execute("SELECT COUNT(*) FROM memory_objects WHERE embedding IS NOT NULL").fetchone()[0]
        by_lane = conn.execute("SELECT lane, COUNT(*) FROM memory_objects GROUP BY lane").fetchall()
        
        conn.close()
        
        lines = [
            "**Open Brain Health: OK**",
            f"Total objects: {total}",
            f"With embeddings: {with_embed}",
            "By lane:"
        ]
        for lane, count in by_lane:
            lines.append(f"  - {lane}: {count}")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Health check failed: {e}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
