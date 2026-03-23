#!/bin/bash
# Track saved articles from Linkding for preference learning
# Run periodically to sync saved articles tagged 'toread'

WORKSPACE="/home/feoh/.openclaw/workspace"
TRACKING_FILE="$WORKSPACE/linkding-saved.json"
LINKDING_URL="https://linkding.reedfish-regulus.ts.net/api/bookmarks"
API_KEY="e8598748d64f35bd1de2ecd8dd0559a01bd9de93"

cd "$WORKSPACE" || exit 1

python3 << 'PYTHON_SCRIPT'
import json
import subprocess
import sys
import os
from datetime import datetime, timezone

WORKSPACE = "/home/feoh/.openclaw/workspace"
TRACKING_FILE = f"{WORKSPACE}/linkding-saved.json"
LINKDING_URL = "https://linkding.reedfish-regulus.ts.net/api/bookmarks"
API_KEY = "e8598748d64f35bd1de2ecd8dd0559a01bd9de93"

# Load existing tracking data
try:
    with open(TRACKING_FILE) as f:
        data = json.load(f)
except:
    data = {"articles": [], "seen_ids": set()}

seen_ids = set(data.get("seen_ids", []))
articles = data.get("articles", [])

# Fetch bookmarks from Linkding tagged 'toread' (paginated with offset)
offset = 0
limit = 100
new_count = 0

while True:
    url = f"{LINKDING_URL}/?offset={offset}&limit={limit}&tag=toread"
    result = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: Token {API_KEY}", url],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode != 0:
        print(f"Failed to fetch Linkding: {result.stderr}")
        break
    
    try:
        response = json.loads(result.stdout)
    except:
        print(f"Failed to parse Linkding response at offset {offset}")
        break
    
    results = response.get("results", [])
    if not results:
        break
    
    for bookmark in results:
        bookmark_id = bookmark.get("id")
        if bookmark_id and bookmark_id not in seen_ids:
            seen_ids.add(bookmark_id)
            
            # Extract tags
            tags = bookmark.get("tag_names", [])
            
            article = {
                "id": bookmark_id,
                "url": bookmark.get("url", ""),
                "title": bookmark.get("title", ""),
                "description": bookmark.get("description", ""),
                "tags": tags,
                "website_name": bookmark.get("website_title", ""),
                "saved_at": bookmark.get("date_added", ""),
            }
            articles.append(article)
            new_count += 1
    
    # Check if there are more pages
    if not response.get("next"):
        break
    
    offset += limit
    if offset > 5000:  # Safety limit
        break

# Save updated data (keep last 500)
data["articles"] = articles[-500:]
data["seen_ids"] = list(seen_ids)[-500:]

with open(TRACKING_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Synced {new_count} new 'toread' articles. Total tracked: {len(articles)}")

PYTHON_SCRIPT
