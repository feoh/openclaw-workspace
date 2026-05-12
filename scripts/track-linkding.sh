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
VENV_PYTHON="$WORKSPACE/.venv/bin/python"

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

"$VENV_PYTHON" << 'PYTHON_SCRIPT'
import json
import subprocess
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse
import re
import math

WORKSPACE = "/home/feoh/.openclaw/workspace"
TRACKING_FILE = f"{WORKSPACE}/linkding-saved.json"
SIGNALS_FILE = f"{WORKSPACE}/data/linkding-recommendation-signals.json"
LINKDING_URL = "https://linkding.reedfish-regulus.ts.net/api/bookmarks/"
API_KEY = os.environ.get("LINKDING_API_KEY", "")
OPENBRAIN_WRITE = f"{WORKSPACE}/scripts/openbrain-write.py"
VENV_PYTHON = f"{WORKSPACE}/.venv/bin/python"
HISTORY_LIMIT = 5000
RECENT_WINDOW = 400
HALF_LIFE_DAYS = 180

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

STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'how',
    'in', 'into', 'is', 'it', 'its', 'of', 'on', 'or', 'that', 'the', 'this',
    'to', 'what', 'when', 'with', 'your', 'can', 'could', 'have', 'has', 'had',
    'all', 'than', 'then', 'they', 'their', 'there', 'them', 'more', 'most',
    'after', 'before', 'over', 'under', 'onto', 'about', 'because', 'through',
    'while', 'where', 'who', 'whose', 'which', 'will', 'would', 'should',
    'just', 'now', 'out', 'new'
}
NOISY_TERMS = {
    'you', 'why', 'just', 'not', 'earned', 'badge', 'chris', 'untappd'
}
NOISY_DOMAINS = {
    't.co', 'x.com', 'twitter.com', 'www.twitter.com', 'untappd.com',
    'foursquare.com', 'bit.ly', 'feedproxy.google.com'
}


def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def parse_saved_at(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def tokenize(text: str):
    return [
        token for token in re.findall(r"[a-z0-9][a-z0-9+.-]{2,}", (text or '').lower())
        if token not in STOPWORDS and token not in NOISY_TERMS and not token.isdigit()
    ]


def normalize_label(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def decay_weight(saved_at: str, now_dt: datetime) -> float:
    parsed = parse_saved_at(saved_at)
    if not parsed:
        return 0.15
    age_days = max((now_dt - parsed).total_seconds() / 86400.0, 0.0)
    return max(0.05, math.pow(0.5, age_days / HALF_LIFE_DAYS))


def weighted_rows(counter, count_counter=None, limit=25, min_weight=0.0, min_count=1):
    rows = []
    for name, weight in counter.items():
        count = int(count_counter.get(name, 0)) if count_counter else 0
        if weight < min_weight or count < min_count or not name:
            continue
        rows.append({"name": name, "weight": round(weight, 4), "count": count})
    rows.sort(key=lambda row: (row["weight"], row["count"], row["name"]), reverse=True)
    return rows[:limit]


articles.sort(key=lambda a: (parse_saved_at(a.get("saved_at", "")) or datetime.min.replace(tzinfo=timezone.utc), a.get("id", 0)))
articles = articles[-HISTORY_LIMIT:]
new_articles.sort(key=lambda a: (parse_saved_at(a.get("saved_at", "")) or datetime.min.replace(tzinfo=timezone.utc), a.get("id", 0)))
seen_ids_list = [a.get("id") for a in articles if a.get("id")][-HISTORY_LIMIT:]
data["articles"] = articles
data["seen_ids"] = seen_ids_list

with open(TRACKING_FILE, "w") as f:
    json.dump(data, f, indent=2)

recent = articles[-RECENT_WINDOW:]
now_dt = datetime.now(timezone.utc)
domain_counts = Counter()
domain_weights = defaultdict(float)
tag_counts = Counter()
tag_weights = defaultdict(float)
website_counts = Counter()
website_weights = defaultdict(float)
title_term_counts = Counter()
title_term_weights = defaultdict(float)
title_bigram_counts = Counter()
title_bigram_weights = defaultdict(float)
feed_term_counts = Counter()
feed_term_weights = defaultdict(float)
recent_cutoff = None
if recent:
    recent_cutoff = parse_saved_at(recent[0].get("saved_at", ""))

for article in recent:
    article_domain = domain_of(article.get("url", ""))
    if article_domain in NOISY_DOMAINS:
        continue
    weight = decay_weight(article.get("saved_at", ""), now_dt)

    if article_domain:
        domain_counts[article_domain] += 1
        domain_weights[article_domain] += weight

    website_name = normalize_label(article.get("website_name") or article_domain)
    if website_name and website_name not in NOISY_DOMAINS:
        website_counts[website_name] += 1
        website_weights[website_name] += weight

    for tag in article.get("tags", []):
        norm_tag = normalize_label(tag)
        if norm_tag and norm_tag != "toread":
            tag_counts[norm_tag] += 1
            tag_weights[norm_tag] += weight

    title_tokens = tokenize(article.get("title", ""))
    desc_tokens = tokenize(article.get("description", ""))
    for token in title_tokens:
        title_term_counts[token] += 1
        title_term_weights[token] += weight * 1.0
    for token in desc_tokens[:12]:
        title_term_counts[token] += 1
        title_term_weights[token] += weight * 0.35
    for bigram in (f"{a} {b}" for a, b in zip(title_tokens, title_tokens[1:])):
        title_bigram_counts[bigram] += 1
        title_bigram_weights[bigram] += weight
    for token in tokenize(article.get("website_name", "")):
        feed_term_counts[token] += 1
        feed_term_weights[token] += weight

signals = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "tracked_count": len(articles),
    "new_count": new_count,
    "model_version": 2,
    "training": {
        "history_limit": HISTORY_LIMIT,
        "recent_window": len(recent),
        "half_life_days": HALF_LIFE_DAYS,
        "recent_oldest_saved_at": recent_cutoff.isoformat() if recent_cutoff else None,
    },
    "top_domains": weighted_rows(domain_weights, domain_counts, limit=20, min_weight=0.35, min_count=2),
    "top_tags": weighted_rows(tag_weights, tag_counts, limit=25, min_weight=0.25, min_count=2),
    "top_sites": weighted_rows(website_weights, website_counts, limit=20, min_weight=0.35, min_count=2),
    "top_title_terms": weighted_rows(title_term_weights, title_term_counts, limit=35, min_weight=0.35, min_count=2),
    "top_title_bigrams": weighted_rows(title_bigram_weights, title_bigram_counts, limit=25, min_weight=0.25, min_count=2),
    "top_feed_terms": weighted_rows(feed_term_weights, feed_term_counts, limit=20, min_weight=0.25, min_count=2),
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
    top_terms_str = ", ".join(f"{t['name']} ({t['count']})" for t in signals["top_title_terms"][:10]) or "none"

    sample_lines = []
    for a in new_articles[-10:]:
        title = a.get("title") or a.get("url") or "Untitled"
        tags = ", ".join(a.get("tags", [])) or "no tags"
        sample_lines.append(f"- {title} [{tags}] {a.get('url','')}")

    title = f"Linkding toread sync — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    summary = (
        f"Synced {new_count} new Linkding 'toread' bookmarks. "
        f"Current top domains: {top_domains_str}. Top tags: {top_tags_str}. Top title terms: {top_terms_str}."
    )
    body = (
        "This memory object captures newly saved Linkding bookmarks tagged 'toread' "
        "plus recommendation signals derived from the recent tracked set.\n\n"
        f"Tracked total: {len(articles)}\n"
        f"New this run: {new_count}\n"
        f"Top domains: {top_domains_str}\n"
        f"Top tags: {top_tags_str}\n"
        f"Top title terms: {top_terms_str}\n\n"
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
