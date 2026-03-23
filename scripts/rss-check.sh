#!/bin/bash
# RSS Checker - Run via cron twice daily
# Saves new articles to Linkding with "toread" tag

WORKSPACE="/home/feoh/.openclaw/workspace"
FEEDS_FILE="$WORKSPACE/rss-feeds.json"
LINKDING_URL="https://linkding.reedfish-regulus.ts.net/api/bookmarks"
API_KEY="e8598748d64f35bd1de2ecd8dd0559a01bd9de93"
TAG="toread"

cd "$WORKSPACE" || exit 1

# Read feeds from JSON (using python for JSON parsing since it's more reliable)
python3 << 'PYTHON_SCRIPT'
import json
import subprocess
import sys
from datetime import datetime, timezone

WORKSPACE = "/home/feoh/.openclaw/workspace"
FEEDS_FILE = f"{WORKSPACE}/rss-feeds.json"
STATE_FILE = f"{WORKSPACE}/rss-state.json"
LINKDING_URL = "https://linkding.reedfish-regulus.ts.net/bookmarks"
API_KEY = "e8598748d64f35bd1de2ecd8dd0559a01bd9de93"
TAG = "toread"

with open(FEEDS_FILE) as f:
    data = json.load(f)

feeds = data["feeds"]

try:
    with open(STATE_FILE) as f:
        state = json.load(f)
except:
    state = {"last_seen": {}}

new_articles = []

for feed in feeds:
    title = feed["title"]
    url = feed["url"]
    
    try:
        # Fetch the feed
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", url],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            print(f"Failed to fetch {title}: {result.stderr}")
            continue
        
        import xml.etree.ElementTree as ET
        content = result.stdout
        
        # Try to parse as XML
        try:
            root = ET.fromstring(content)
        except:
            # Try to handle namespace issues
            root = ET.fromstring(content)
        
        # Determine feed type and extract entries
        entries = []
        
        # Atom format
        if root.tag.endswith("}feed") or "atom" in content.lower():
            for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                e_url = entry.find("{http://www.w3.org/2005/Atom}id")
                e_title = entry.find("{http://www.w3.org/2005/Atom}title")
                e_url = entry.find("{http://www.w3.org/2005/Atom}link")
                if e_url is not None and e_url.get("href"):
                    entry_id = e_url.get("href")
                    entry_title = e_title.text if e_title is not None else "No title"
                    entries.append({"id": entry_id, "title": entry_title, "url": entry_id})
        
        # RSS format
        if not entries:
            for item in root.findall(".//item"):
                e_id = item.find("guid")
                e_title = item.find("title")
                e_link = item.find("link")
                entry_id = e_id.text if e_id is not None else (e_link.text if e_link is not None else None)
                entry_title = e_title.text if e_title is not None else "No title"
                if entry_id:
                    entries.append({"id": entry_id, "title": entry_title, "url": entry_id})
        
        # Also try enclosure/link as fallback
        if not entries:
            for item in root.findall(".//entry"):
                e_id = item.find("id")
                e_title = item.find("title")
                e_link = item.find("link[@rel='alternate']")
                if e_link is None:
                    e_link = item.find("link")
                entry_id = e_id.text if e_id is not None else None
                entry_url = e_link.get("href") if e_link is not None else entry_id
                entry_title = e_title.text if e_title is not None else "No title"
                if entry_id or entry_url:
                    entries.append({"id": entry_id or entry_url, "title": entry_title, "url": entry_url or entry_id})
        
        # Check for new entries
        last_seen = state["last_seen"].get(url, "")
        new_entries = []
        
        for entry in entries:
            entry_id = entry["id"]
            if entry_id != last_seen and entry_id:
                new_entries.append(entry)
        
        if new_entries:
            # Update last seen to the most recent
            if entries:
                state["last_seen"][url] = entries[0]["id"]
            
            for entry in new_entries:
                new_articles.append({
                    "feed": title,
                    "title": entry["title"],
                    "url": entry["url"]
                })
            print(f"{title}: {len(new_entries)} new article(s)")
            
    except Exception as e:
        print(f"Error processing {title}: {e}")
        import traceback
        traceback.print_exc()

# Save state
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)

# Save new articles to a file for review
if new_articles:
    with open(f"{WORKSPACE}/rss-new-articles.json", "w") as f:
        json.dump(new_articles, f, indent=2)
    print(f"\n{len(new_articles)} new article(s) saved to rss-new-articles.json")
else:
    print("\nNo new articles found.")
    # Remove old file if it exists
    import os
    try:
        os.remove(f"{WORKSPACE}/rss-new-articles.json")
    except:
        pass

PYTHON_SCRIPT

echo "---"
echo "RSS check completed at $(date)"
