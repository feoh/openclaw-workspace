#!/bin/bash
# Track saved articles from Linkding for preference learning
# - Sync bookmarks tagged 'toread'
# - Build lightweight recommendation signals
# - Write a periodic summary into Open Brain when new items appear

set -euo pipefail

WORKSPACE="/home/feoh/.openclaw/workspace"
TRACKING_FILE="$WORKSPACE/linkding-saved.json"
SIGNALS_FILE="$WORKSPACE/data/linkding-recommendation-signals.json"
LINKDING_URL="https://linkding.reedfish-regulus.ts.net/api/bookmarks/"
OPENBRAIN_WRITE="$WORKSPACE/scripts/openbrain-write.py"

cd "$WORKSPACE" || exit 1
mkdir -p "$WORKSPACE/data"

# Load .env if present
if [[ -f "$WORKSPACE/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$WORKSPACE/.env"
  set +a
fi

API_KEY="${LINKDING_API_KEY:-}"

if [[ -z "$API_KEY" ]]; then
  echo "Error: LINKDING_API_KEY not set"
  exit 1
fi

python3 << 'PYTHON_SCRIPT'
import json
import subprocess
import os
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

WORKSPACE = "/home/feoh/.openclaw/workspace"
TRACKING_FILE = f"{WORKSPACE}/linkding-saved.json"
SIGNALS_FILE = f"{WORKSPACE}/data/linkding-recommendation-signals.json"
LINKDING_URL = "https://linkding.reedfish-regulus.ts.net/api/bookmarks/"
API_KEY = os.environ.get("LINKDING_API_KEY", "")
OPENBRAIN_WRITE = f"{WORKSPACE}/scripts/openbrain-write.py"
VENV_PYTHON = f"{WORKSPACE}/.venv/bin/python"

# Load existing tracking data
try:
    with open(TRACKING_FILE) as f:
        data = json.load(f)
except Exception:
    data = {"articles": [], "seen_ids": []}

seen_ids = set(data.get("seen_ids", []))
articles = data.get("articles", [])
new_articles = []

# Fetch bookmarks from Linkding tagged 'toread' (paginated with offset)
offset = 0
limit = 100
new_count = 0

while True:
    url = f"{LINKDING_URL}?offset={offset}&limit={limit}&tag=toread"
    result = subprocess.run(
        ["curl", "-s", "-H", f"Authorization: Token {API_KEY}", url],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        print(f"Failed to fetch Linkding: {result.stderr}")
        break

    try:
        response = json.loads(result.stdout)
    except Exception:
        print(f"Failed to parse Linkding response at offset {offset}")
        break

    results = response.get("results", [])
    if not results:
        break

    for bookmark in results:
        bookmark_id = bookmark.get("id")
        if bookmark_id and bookmark_id not in seen_ids:
            seen_ids.add(bookmark_id)
            article = {
                "id": bookmark_id,
                "url": bookmark.get("url", ""),
                "title": bookmark.get("title", ""),
                "description": bookmark.get("description", ""),
                "tags": bookmark.get("tag_names", []),
                "website_name": bookmark.get("website_title", ""),
                "saved_at": bookmark.get("date_added", ""),
            }
            articles.append(article)
            new_articles.append(article)
            new_count += 1

    if not response.get("next"):
        break

    offset += limit
    if offset > 5000:
        break

# Keep last 500 tracked records / IDs
articles = articles[-500:]
seen_ids_list = list(seen_ids)[-500:]
data["articles"] = articles
data["seen_ids"] = seen_ids_list

with open(TRACKING_FILE, "w") as f:
    json.dump(data, f, indent=2)

def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

recent = articles[-200:]
domain_counts = Counter(domain_of(a.get("url", "")) for a in recent if a.get("url"))
tag_counts = Counter(tag for a in recent for tag in a.get("tags", []))
website_counts = Counter((a.get("website_name") or domain_of(a.get("url", ""))) for a in recent)

signals = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "tracked_count": len(articles),
    "new_count": new_count,
    "top_domains": [{"name": k, "count": v} for k, v in domain_counts.most_common(15) if k],
    "top_tags": [{"name": k, "count": v} for k, v in tag_counts.most_common(20) if k],
    "top_sites": [{"name": k, "count": v} for k, v in website_counts.most_common(15) if k],
    "recent_new": [
        {
            "id": a.get("id"),
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "tags": a.get("tags", []),
            "saved_at": a.get("saved_at", ""),
        }
        for a in new_articles[-25:]
    ],
}

with open(SIGNALS_FILE, "w") as f:
    json.dump(signals, f, indent=2)

# If there are new articles, write a compact semantic summary into Open Brain.
if new_articles:
    top_domains_str = ", ".join(f"{d['name']} ({d['count']})" for d in signals["top_domains"][:5]) or "none"
    top_tags_str = ", ".join(f"{t['name']} ({t['count']})" for t in signals["top_tags"][:8]) or "none"

    sample_lines = []
    for a in new_articles[-10:]:
        title = a.get("title") or a.get("url") or "Untitled"
        tags = ", ".join(a.get("tags", [])) or "no tags"
        sample_lines.append(f"- {title} [{tags}] {a.get('url','')}")

    title = f"Linkding toread sync — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    summary = (
        f"Synced {new_count} new Linkding 'toread' bookmarks. "
        f"Current top domains: {top_domains_str}. Top tags: {top_tags_str}."
    )
    body = (
        "This memory object captures newly saved Linkding bookmarks tagged 'toread' "
        "plus recommendation signals derived from the recent tracked set.\n\n"
        f"Tracked total: {len(articles)}\n"
        f"New this run: {new_count}\n"
        f"Top domains: {top_domains_str}\n"
        f"Top tags: {top_tags_str}\n\n"
        "Recent examples from this run:\n" + "\n".join(sample_lines)
    )

    try:
        result = subprocess.run(
            [
                VENV_PYTHON, OPENBRAIN_WRITE, title,
                "--summary", summary,
                "--body", body,
                "--tags", "linkding,recommendations,preferences,toread,openbrain",
                "--provenance", "track-linkding.sh",
            ],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"Open Brain write failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"Open Brain write failed: {e}")

print(f"Synced {new_count} new 'toread' articles. Total tracked: {len(articles)}")
print(f"Wrote recommendation signals to {SIGNALS_FILE}")

PYTHON_SCRIPT
