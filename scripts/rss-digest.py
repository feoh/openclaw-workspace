#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
RSS Daily Digest Generator
Fetches all feeds from rss-feeds.opml and generates a formatted digest.
"""
import feedparser
import html
import re
import json
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv(dotenv_path="/home/feoh/.openclaw/workspace/.env")


def get_saved_urls():
    """Fetch all existing bookmark URLs from Linkding."""
    import psycopg
    import ollama
    api_key = os.environ.get("LINKDING_API_KEY")
    if not api_key:
        print("⚠️ WARNING: LINKDING_API_KEY not set — Linkding filter disabled, all articles will show", file=sys.stderr)
        return set()
    
    base_url = "https://linkding.reedfish-regulus.ts.net/api/bookmarks/"
    headers = {"Authorization": f"Token {api_key}"}
    saved = set()
    offset = 0
    limit = 100
    
    while True:
        import urllib.request
        url = f"{base_url}?limit={limit}&offset={offset}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                results = data.get("results", [])
                if not results:
                    break
                for item in results:
                    if item.get("url"):
                        saved.add(item["url"].rstrip("/"))
                if len(results) < limit:
                    break
                offset += limit
        except Exception as e:
            print(f"Warning: could not fetch saved URLs from Linkding: {e}", file=sys.stderr)
            break
    
    return saved

OPML_FILE = "/home/feoh/.openclaw/workspace/rss-feeds.opml"

def load_feeds_from_opml(opml_path=OPML_FILE):
    """
    Single source of truth: load feeds from rss-feeds.opml.
    Returns list of (title, html_url, xml_url) tuples.
    To add/remove feeds, edit rss-feeds.opml only.
    """
    import xml.etree.ElementTree as ET
    tree = ET.parse(opml_path)
    feeds = []
    for outline in tree.iter("outline"):
        xml_url = outline.get("xmlUrl")
        if not xml_url:
            continue
        title = outline.get("title") or outline.get("text") or xml_url
        html_url = outline.get("htmlUrl") or xml_url
        feeds.append((title, html_url, xml_url))
    return feeds

FEEDS = load_feeds_from_opml()

# Filter patterns — entries matching these (case-insensitive) are skipped
FILTER_PATTERNS = [
    r"\b(ev|electric vehicle|electric car|tesla|charging station|charging cable)\b",
]

DEFAULT_FEED_ENTRY_LIMIT = 10
FEED_BACKFILL_LIMITS = {
    # High-volume feeds, worth a deeper scan so older-but-still-recent items
    # don't silently fall out before we ever show them.
    "Ars Technica": 50,
    "Lobsters": 50,
}
FEED_BACKFILL_DAYS = {
    "Ars Technica": 60,
    "Lobsters": 60,
}

def should_skip(entry, saved_urls, shown_urls=None):
    """Return True if entry should be filtered out."""
    entry_url = entry["url"].rstrip("/")

    # Skip if already saved to Linkding
    if entry_url in saved_urls:
        return True

    # Skip if already shown in a previous digest
    if shown_urls and entry_url in shown_urls:
        return True

    # Filter Ars Technica EV articles
    if entry["feed"] == "Ars Technica":
        t = entry["title"].lower()
        for pat in FILTER_PATTERNS:
            if re.search(pat, t):
                return True
    return False

def parse_entry(entry, feed_title, blog_url):
    """Extract title, url, and date from a feedparser entry."""
    # Title
    title = getattr(entry, 'title', '') or ''
    title = re.sub(r'<[^>]+>', '', html.unescape(title)).strip()
    
    # URL: try link, then href, then guilink
    url = blog_url
    if hasattr(entry, 'link') and entry.link:
        url = entry.link.strip()
    elif hasattr(entry, 'href') and entry.href:
        url = entry.href.strip()
    
    # Date
    dt = None
    for attr in ['published_parsed', 'updated_parsed', 'created_parsed']:
        if hasattr(entry, attr):
            parsed = getattr(entry, attr)
            if parsed:
                try:
                    from time import mktime
                    dt = datetime.fromtimestamp(mktime(parsed))
                    break
                except:
                    pass
    
    return {"title": title, "url": url, "date": dt, "feed": feed_title}


SHOWN_FILE = "/home/feoh/.openclaw/workspace/data/rss-shown-urls.json"
LINKDING_TRACKING_FILE = "/home/feoh/.openclaw/workspace/linkding-saved.json"
LINKDING_SIGNALS_FILE = "/home/feoh/.openclaw/workspace/data/linkding-recommendation-signals.json"

PREFERENCE_STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'how',
    'in', 'into', 'is', 'it', 'its', 'of', 'on', 'or', 'that', 'the', 'this',
    'to', 'what', 'when', 'with', 'your'
}


def load_shown_urls():
    """Load URLs that have already been shown in a digest."""
    if os.path.exists(SHOWN_FILE):
        with open(SHOWN_FILE) as f:
            return set(json.load(f))
    return set()

def save_shown_urls(shown):
    """Save the set of URLs already shown."""
    os.makedirs(os.path.dirname(SHOWN_FILE), exist_ok=True)
    with open(SHOWN_FILE, "w") as f:
        json.dump(sorted(shown), f, indent=2)

def load_preference_model():
    """Load lightweight Linkding-derived preference signals for digest highlighting."""
    model = {
        'domains': set(),
        'sites': set(),
        'keywords': set(),
    }

    try:
        with open(LINKDING_SIGNALS_FILE) as f:
            signals = json.load(f)
        model['domains'] = {
            item['name'].lower() for item in signals.get('top_domains', [])[:10]
            if item.get('count', 0) >= 2 and item.get('name')
        }
        model['sites'] = {
            item['name'].lower() for item in signals.get('top_sites', [])[:10]
            if item.get('count', 0) >= 2 and item.get('name')
        }
    except Exception:
        pass

    try:
        with open(LINKDING_TRACKING_FILE) as f:
            tracking = json.load(f)
        articles = tracking.get('articles', [])[-200:]
        keyword_counts = {}
        for article in articles:
            text = f"{article.get('title', '')} {article.get('website_name', '')}".lower()
            for token in re.findall(r"[a-z0-9][a-z0-9+.-]{2,}", text):
                if token in PREFERENCE_STOPWORDS or token.isdigit():
                    continue
                keyword_counts[token] = keyword_counts.get(token, 0) + 1
        model['keywords'] = {
            token for token, count in keyword_counts.items()
            if count >= 3
        }
    except Exception:
        pass

    return model


def annotate_preferences(entries, preference_model):
    """Mark entries that look aligned with saved Linkding interests."""
    if not entries:
        return entries

    domains = preference_model.get('domains', set())
    sites = preference_model.get('sites', set())
    keywords = preference_model.get('keywords', set())

    for entry in entries:
        score = 0
        url = entry.get('url', '').lower()
        title = entry.get('title', '').lower()
        feed = entry.get('feed', '').lower()

        if any(domain and domain in url for domain in domains):
            score += 2
        if feed in sites:
            score += 2

        title_tokens = {
            token for token in re.findall(r"[a-z0-9][a-z0-9+.-]{2,}", title)
            if token not in PREFERENCE_STOPWORDS and not token.isdigit()
        }
        overlap = len(title_tokens & keywords)
        score += min(overlap, 3)

        entry['preferred'] = score >= 2
        entry['preference_score'] = score

    return entries


def fetch_feeds(saved_urls=None, shown_urls=None):
    """Fetch all feeds and return entries not yet shown to the user."""
    if saved_urls is None:
        saved_urls = set()
    if shown_urls is None:
        shown_urls = set()

    entries = []
    now = datetime.now()

    for feed_title, blog_url, feed_url in FEEDS:
        try:
            f = feedparser.parse(feed_url, agent="RSS-Digest/1.0")
            entry_limit = FEED_BACKFILL_LIMITS.get(feed_title, DEFAULT_FEED_ENTRY_LIMIT)
            backfill_days = FEED_BACKFILL_DAYS.get(feed_title)
            cutoff = None if backfill_days is None else now - timedelta(days=backfill_days)

            for entry in f.entries[:entry_limit]:
                e = parse_entry(entry, feed_title, blog_url)
                if not e['title']:
                    continue
                if cutoff and e['date'] and e['date'] < cutoff:
                    continue
                if not should_skip(e, saved_urls, shown_urls):
                    entries.append(e)
        except Exception as e:
            print(f"Error fetching {feed_title}: {e}", file=sys.stderr)

    entries.sort(key=lambda x: x["date"] or datetime.min, reverse=True)
    preference_model = load_preference_model()
    return annotate_preferences(entries, preference_model)


def format_digest(entries, limit=25):
    """Format entries as Discord-ready Markdown."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"**📬 RSS Daily Digest — {today}**\n_{len(entries)} entries_\n"]
    
    for i, e in enumerate(entries[:limit], 1):
        date_str = e["date"].strftime("%Y-%m-%d") if e["date"] else "????-??-??"
        marker = " ⭐" if e.get('preferred') else ""
        lines.append(f"**{i}.** [{e['title']}]({e['url']}){marker}")
        lines.append(f"_{date_str} · {e['feed']}_\n")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RSS Daily Digest")
    parser.add_argument("--limit", type=int, default=25, help="Max entries to show")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument("--save", metavar="FILE", help="Save entries to JSON file")
    parser.add_argument("--no-filter", action="store_true", help="Skip Linkding filter")
    parser.add_argument("--peek", action="store_true", help="Preview entries without recording them as shown or replacing rss-last-digest.json")
    args = parser.parse_args()
    
    # Fetch saved URLs from Linkding unless disabled
    saved_urls = set()
    if not args.no_filter:
        saved_urls = get_saved_urls()
        print(f"Filtered {len(saved_urls)} already-saved URLs", file=sys.stderr)

    # Load previously shown URLs
    shown_urls = load_shown_urls()
    print(f"Filtered {len(shown_urls)} already-shown URLs", file=sys.stderr)

    entries = fetch_feeds(saved_urls=saved_urls, shown_urls=shown_urls)

    # Save the numbered list to a fixed file so "save #N" commands work correctly.
    # Important: do NOT wipe the previous digest cache when there are no new entries,
    # or users lose the numbering from the last delivered digest.
    LAST_DIGEST_FILE = "/home/feoh/.openclaw/workspace/data/rss-last-digest.json"
    numbered = [{"num": i, "title": e["title"], "url": e["url"], "feed": e["feed"]}
                for i, e in enumerate(entries, 1)]
    if args.peek:
        print("Peek mode: preserving rss-last-digest.json numbering", file=sys.stderr)
    else:
        os.makedirs(os.path.dirname(LAST_DIGEST_FILE), exist_ok=True)
        if numbered:
            with open(LAST_DIGEST_FILE, "w") as f:
                json.dump(numbered, f, default=str, indent=2)
        else:
            print("No new entries, preserving previous rss-last-digest.json numbering", file=sys.stderr)

    if args.json:
        print(json.dumps(entries, default=str, indent=2))
    else:
        print(format_digest(entries, limit=args.limit))

    # Record shown URLs AFTER output — these won't appear in future digests
    if args.peek:
        print("Peek mode: not recording URLs as shown", file=sys.stderr)
    else:
        new_shown = shown_urls | {e["url"].rstrip("/") for e in entries}
        save_shown_urls(new_shown)
        print(f"Recorded {len(entries)} new URLs as shown ({len(new_shown)} total)", file=sys.stderr)

    if args.save:
        with open(args.save, "w") as f:
            json.dump(entries, f, default=str, indent=2)
        print(f"\nSaved {len(entries)} entries to {args.save}", file=sys.stderr)
