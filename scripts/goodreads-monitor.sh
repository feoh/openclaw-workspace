#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/home/feoh/.openclaw/workspace"
STATE_FILE="$WORKSPACE/data/goodreads-last-seen.txt"
FEED_URL="https://www.goodreads.com/user/updates_rss/799620"
mkdir -p "$WORKSPACE/data"

python3 <<'PY'
import os, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

feed_url = "https://www.goodreads.com/user/updates_rss/799620"
state_file = "/home/feoh/.openclaw/workspace/data/goodreads-last-seen.txt"

req = urllib.request.Request(feed_url, headers={"User-Agent": "OpenClaw-Goodreads-Monitor/1.0"})
with urllib.request.urlopen(req, timeout=20) as r:
    xml = r.read()
root = ET.fromstring(xml)
items = root.findall('.//item')
if not items:
    print('NO_ITEMS')
    raise SystemExit(0)

first = items[0]
guid = (first.findtext('guid') or '').strip()
title = (first.findtext('title') or '').strip()
link = (first.findtext('link') or '').strip()
pub = (first.findtext('pubDate') or '').strip()

last = None
if os.path.exists(state_file):
    with open(state_file) as f:
        last = f.read().strip() or None

if not last:
    with open(state_file, 'w') as f:
        f.write(guid)
    print(f'BASELINE_SET {guid}')
    raise SystemExit(0)

if guid == last:
    print('NO_CHANGE')
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
        'pubDate': (item.findtext('pubDate') or '').strip(),
    })

with open(state_file, 'w') as f:
    f.write(guid)

print(f'NEW_ACTIVITY {len(new_items)}')
for item in reversed(new_items):
    print(f"📚 {item['title']}")
    if item['link']:
        print(item['link'])
PY
