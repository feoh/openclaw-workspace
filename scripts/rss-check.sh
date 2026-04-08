#!/bin/bash
# RSS Checker - Run via cron twice daily
# Identifies new articles and saves list for review

WORKSPACE="/home/feoh/.openclaw/workspace"
STATE_FILE="$WORKSPACE/rss-state.json"
FEEDS_FILE="$WORKSPACE/rss-feeds.opml"
OUTPUT_FILE="$WORKSPACE/rss-new-articles.json"

cd "$WORKSPACE" || exit 1

# Use python to do the heavy lifting
python3 << 'PYTHON_SCRIPT'
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import feedparser
import re
from datetime import datetime, timezone

WORKSPACE = "/home/feoh/.openclaw/workspace"
STATE_FILE = f"{WORKSPACE}/rss-state.json"
OUTPUT_FILE = f"{WORKSPACE}/rss-new-articles.json"

# Load feeds from OPML
import xml.etree.ElementTree as ET
try:
    tree = ET.parse(f"{WORKSPACE}/rss-feeds.opml")
    root = tree.getroot()
    feeds = []
    for outline in root.findall(".//{http://backend.userland.com/OPML}outline") + root.findall(".//outline"):
        xml_url = outline.get("xmlUrl")
        title = outline.get("text") or outline.get("title") or xml_url
        html_url = outline.get("htmlUrl", "")
        if xml_url:
            feeds.append({"title": title, "url": html_url, "xmlUrl": xml_url})
except Exception as e:
    print(f"Error parsing OPML: {e}")
    sys.exit(1)

try:
    with open(STATE_FILE) as f:
        state = json.load(f)
except:
    state = {"last_seen": {}}

new_articles = []

for feed in feeds:
    title = feed["title"]
    xml_url = feed["xmlUrl"]
    
    try:
        f = feedparser.parse(xml_url, agent="RSS-Digest/1.0")
        if not f.entries:
            continue
        
        last_seen = state["last_seen"].get(xml_url, "")
        found_new = False
        
        for entry in f.entries[:10]:
            entry_id = getattr(entry, 'id', None) or getattr(entry, 'link', None)
            if not entry_id:
                continue
            
            if entry_id == last_seen:
                break  # we've reached already-seen articles
            
            entry_title = getattr(entry, 'title', 'No title') or 'No title'
            entry_url = getattr(entry, 'link', '') or ''
            
            # Skip malformed entries
            if not entry_url or len(entry_url) < 10:
                continue
            
            new_articles.append({
                "feed": title,
                "title": entry_title,
                "url": entry_url
            })
            found_new = True
        
        if found_new and f.entries:
            state["last_seen"][xml_url] = f.entries[0].id or f.entries[0].link or ""
            
    except Exception as e:
        print(f"Error processing {title}: {e}")

    # Save state after each feed (don't lose progress on error)
    with open(STATE_FILE, "w") as sf:
        json.dump(state, sf, indent=2)

# Save new articles
if new_articles:
    with open(OUTPUT_FILE, "w") as f:
        json.dump(new_articles, f, indent=2, default=str)
    print(f"{len(new_articles)} new article(s) found — saved to rss-new-articles.json")
else:
    import os
    try:
        os.remove(OUTPUT_FILE)
    except:
        pass
    print("No new articles found.")

PYTHON_SCRIPT

echo "RSS check completed at $(date)"
