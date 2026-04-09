#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/home/feoh/.openclaw/workspace"
STATE_FILE="$WORKSPACE/data/goodreads-last-seen.txt"
FEED_URL="https://www.goodreads.com/user/updates_rss/799620"
mkdir -p "$WORKSPACE/data"

trap 'status=$?; echo "GOODREADS_MONITOR_FAILED (exit $status)" >&2' ERR

python3 <<'PY'
import os
import urllib.request
import xml.etree.ElementTree as ET

feed_url = "https://www.goodreads.com/user/updates_rss/799620"
state_file = "/home/feoh/.openclaw/workspace/data/goodreads-last-seen.txt"

req = urllib.request.Request(feed_url, headers={"User-Agent": "OpenClaw-Goodreads-Monitor/1.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    xml = r.read()
root = ET.fromstring(xml)
items = root.findall('.//item')
if not items:
    raise RuntimeError('Goodreads feed returned no items')

first = items[0]
guid = (first.findtext('guid') or '').strip()
if not guid:
    raise RuntimeError('Goodreads feed first item missing guid')

last = None
if os.path.exists(state_file):
    with open(state_file) as f:
        last = f.read().strip() or None

if not last:
    with open(state_file, 'w') as f:
        f.write(guid)
    raise SystemExit(0)

if guid == last:
    raise SystemExit(0)

new_items = []
for item in items:
    g = (item.findtext('guid') or '').strip()
    if not g or g == last:
        break
    new_items.append({
        'guid': g,
        'title': (item.findtext('title') or '').strip(),
        'link': (item.findtext('link') or '').strip(),
    })

with open(state_file, 'w') as f:
    f.write(guid)

print(f'NEW_ACTIVITY {len(new_items)}')
for item in reversed(new_items):
    print(f"📚 {item['title']}")
    if item['link']:
        print(item['link'])
PY
