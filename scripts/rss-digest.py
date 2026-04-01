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
from datetime import datetime
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

FEEDS = [
    ("Terence Eden's Blog", "https://shkspr.mobi/blog", "https://shkspr.mobi/blog/feed/"),
    ("Unfinished Bitness", "https://unfinishedbitness.info", "https://unfinishedbitness.info/feed/"),
    ("Blind Not Dumb", "https://www.feoh.org", "https://www.feoh.org/feed.atom"),
    ("John P. Murphy", "https://johnpmurphy.net", "https://johnpmurphy.net/feed/"),
    ("Zarf Updates", "https://blog.zarfhome.com", "https://blog.zarfhome.com/feeds/posts/default"),
    ("Aeracode", "https://www.aeracode.org", "https://aeracode.org/feed/atom/"),
    ("Anthony Shaw's blog", "https://tonybaloney.github.io", "https://tonybaloney.github.io/rss.xml"),
    ("Deciphering Glyph", "https://blog.glyph.im", "https://blog.glyph.im/feeds/all.atom.xml"),
    ("Hynek Schlawack", "https://hynek.me", "https://hynek.me/index.xml"),
    ("Daniel Roy Greenfeld", "https://daniel.feldroy.com", "https://daniel.feldroy.com/feeds/atom.xml"),
    ("Michael Kennedy", "https://mkennedy.codes", "https://mkennedy.codes/index.xml"),
    ("Ned Batchelder's blog", "https://nedbatchelder.com/blog", "https://nedbatchelder.com/blog/rss.xml"),
    ("Simon Willison's Weblog", "https://simonwillison.net", "https://simonwillison.net/atom/everything/"),
    ("Tall, Snarky Canadian", "https://snarky.ca", "https://snarky.ca/rss/"),
    ("Chris Morgan's blog", "https://chrismorgan.info", "https://chrismorgan.info/feed.xml"),
    ("matklad", "https://matklad.github.io", "https://matklad.github.io/feed.xml"),
    ("Ars Technica", "https://arstechnica.com", "https://arstechnica.com/feed/?t=d46dc635cfe2031785f81a4b0c4f7f73da4f3bbf"),
    ("Kagi Blog", "https://blog.kagi.com", "https://blog.kagi.com/rss.xml"),
    ("Fujinet News", "https://fujinet.online", "https://fujinet.online/feed/"),
    ("Zed A. Shaw", "https://zedshaw.com", "https://zedshaw.com/feed.atom"),
    ("Nushell Blog", "https://www.nushell.sh", "https://www.nushell.sh/atom.xml"),
    ("Lobsters", "https://lobste.rs", "https://lobste.rs/top.rss"),
]

FEED_CATEGORIES = {
    "All": ["Terence Eden's Blog", "Unfinished Bitness", "Fujinet News"],
    "Fun": ["Blind Not Dumb", "John P. Murphy", "Zarf Updates"],
    "Python": ["Aeracode", "Anthony Shaw's blog", "Deciphering Glyph", "Hynek Schlawack", "Daniel Roy Greenfeld", "Michael Kennedy", "Ned Batchelder's blog", "Simon Willison's Weblog", "Tall, Snarky Canadian"],
    "Rust": ["Chris Morgan's blog", "matklad"],
    "Technology": ["Ars Technica", "Kagi Blog", "Zed A. Shaw", "Fujinet News", "Nushell Blog", "Lobsters"],
}

# Filter patterns — entries matching these (case-insensitive) are skipped
FILTER_PATTERNS = [
    r"\b(ev|electric vehicle|electric car|tesla|charging station|charging cable)\b",
]

def should_skip(entry, saved_urls):
    """Return True if entry should be filtered out."""
    # Skip if already saved to Linkding
    entry_url = entry["url"].rstrip("/")
    if entry_url in saved_urls:
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


def fetch_feeds(saved_urls=None):
    """Fetch all feeds and return sorted entries."""
    if saved_urls is None:
        saved_urls = set()
    
    entries = []
    for feed_title, blog_url, feed_url in FEEDS:
        try:
            f = feedparser.parse(feed_url, agent="RSS-Digest/1.0")
            for entry in f.entries[:5]:
                e = parse_entry(entry, feed_title, blog_url)
                if e['title'] and not should_skip(e, saved_urls):
                    entries.append(e)
        except Exception as e:
            print(f"Error fetching {feed_title}: {e}", file=sys.stderr)
    
    entries.sort(key=lambda x: x["date"] or datetime.min, reverse=True)
    return entries


def format_digest(entries, limit=25):
    """Format entries as Discord-ready Markdown."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"**📬 RSS Daily Digest — {today}**\n_{len(entries)} entries_\n"]
    
    for i, e in enumerate(entries[:limit], 1):
        date_str = e["date"].strftime("%Y-%m-%d") if e["date"] else "????-??-??"
        lines.append(f"**{i}.** [{e['title']}]({e['url']})")
        lines.append(f"_{date_str} · {e['feed']}_\n")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RSS Daily Digest")
    parser.add_argument("--limit", type=int, default=25, help="Max entries to show")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument("--save", metavar="FILE", help="Save entries to JSON file")
    parser.add_argument("--no-filter", action="store_true", help="Skip Linkding filter")
    args = parser.parse_args()
    
    # Fetch saved URLs from Linkding unless disabled
    saved_urls = set()
    if not args.no_filter:
        saved_urls = get_saved_urls()
        print(f"Filtered {len(saved_urls)} already-saved URLs", file=sys.stderr)
    
    entries = fetch_feeds(saved_urls=saved_urls)
    
    if args.json:
        print(json.dumps(entries, default=str, indent=2))
    else:
        print(format_digest(entries, limit=args.limit))
    
    if args.save:
        with open(args.save, "w") as f:
            json.dump(entries, f, default=str, indent=2)
        print(f"\nSaved {len(entries)} entries to {args.save}", file=sys.stderr)
