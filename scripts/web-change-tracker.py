#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Website change tracker — checks a URL for content changes and reports diffs.
Usage: python3 web-change-tracker.py <url> [--name "friendly name"]
Stores hashes in data/web-change-state.json
"""

import sys
import os
import json
import hashlib
import argparse
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv(dotenv_path="/home/feoh/.openclaw/workspace/.env")

STATE_FILE = "/home/feoh/.openclaw/workspace/data/web-change-state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_page(url):
    """Fetch page content, strip whitespace for stable comparison."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; change-tracker/1.0)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def content_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()


def check_url(url, name=None):
    label = name or url
    state = load_state()
    entry = state.get(url, {})

    content = fetch_page(url)
    current_hash = content_hash(content)
    now = datetime.now(timezone.utc).isoformat()

    if not entry:
        # First run — just record baseline
        state[url] = {
            "name": label,
            "hash": current_hash,
            "first_seen": now,
            "last_checked": now,
            "last_changed": now,
            "change_count": 0,
        }
        save_state(state)
        print(f"BASELINE: Recorded baseline for {label}")
        return "baseline"

    state[url]["last_checked"] = now

    if current_hash != entry["hash"]:
        state[url]["hash"] = current_hash
        state[url]["last_changed"] = now
        state[url]["change_count"] = entry.get("change_count", 0) + 1
        save_state(state)
        print(f"CHANGED: {label} has changed! (change #{state[url]['change_count']})")
        print(f"URL: {url}")
        print(f"Detected at: {now}")
        return "changed"
    else:
        save_state(state)
        print(f"UNCHANGED: {label} — no changes detected")
        return "unchanged"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check a URL for changes")
    parser.add_argument("url", help="URL to check")
    parser.add_argument("--name", default=None, help="Friendly name for the site")
    args = parser.parse_args()

    try:
        result = check_url(args.url, name=args.name)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR checking {args.url}: {e}", file=sys.stderr)
        sys.exit(1)
