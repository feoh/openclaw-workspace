#!/usr/bin/env python3
import json
import subprocess
import sys

LINKDING_URL = "https://linkding.reedfish-regulus.ts.net/api/bookmarks/"
API_KEY = "<LINKDING_API_KEY>"
INPUT_FILE = "/home/feoh/.openclaw/workspace/rss-new-articles.json"

# Load articles
with open(INPUT_FILE, 'r') as f:
    articles = json.load(f)

print(f"Processing {len(articles)} articles...")

saved = []
failed = []

for article in articles:
    title = article.get('title', '')
    url = article.get('url', '')
    feed = article.get('feed', '')
    
    # Build curl command
    cmd = [
        'curl', '-s', '-w', '\\n%{http_code}',
        '-X', 'POST',
        LINKDING_URL,
        '-H', f'Authorization: Token {API_KEY}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps({
            'url': url,
            'title': title,
            'tag_names': ['toread']
        })
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    lines = output.split('\n')
    http_code = lines[-1] if lines else ''
    
    if http_code in ('200', '201'):
        saved.append((title, url))
        print(f"SAVED: {title[:60]}...")
    else:
        failed.append((title, url, http_code, output))
        print(f"FAILED ({http_code}): {title[:60]}...")

# Delete the file after processing
import os
os.remove(INPUT_FILE)
print(f"\nDeleted {INPUT_FILE}")

print(f"\nSummary: {len(saved)} saved, {len(failed)} failed")

if failed:
    print("\nFailed articles:")
    for title, url, code, _ in failed:
        print(f"  [{code}] {title} - {url}")
