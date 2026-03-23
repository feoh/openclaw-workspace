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
    ("Zed A. Shaw", "https://zedshaw.com", "https://zedshaw.com/feed.atom"),
]

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


def fetch_feeds():
    """Fetch all feeds and return sorted entries."""
    entries = []
    for feed_title, blog_url, feed_url in FEEDS:
        try:
            f = feedparser.parse(feed_url, agent="RSS-Digest/1.0")
            for entry in f.entries[:5]:
                e = parse_entry(entry, feed_title, blog_url)
                if e['title']:
                    entries.append(e)
        except Exception as e:
            print(f"Error fetching {feed_title}: {e}", file=sys.stderr)
    
    entries.sort(key=lambda x: x["date"] or datetime.min, reverse=True)
    return entries


def format_digest(entries, limit=25):
    """Format entries as a text digest."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"RSS Daily Digest — {today} · {len(entries)} entries\n"]
    
    for e in entries[:limit]:
        date_str = e["date"].strftime("%Y-%m-%d") if e["date"] else "????-??-??"
        lines.append(f"[{date_str}] {e['feed']}")
        lines.append(f"  {e['title']}")
        lines.append(f"  {e['url']}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RSS Daily Digest")
    parser.add_argument("--limit", type=int, default=25, help="Max entries to show")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")
    parser.add_argument("--save", metavar="FILE", help="Save entries to JSON file")
    args = parser.parse_args()
    
    entries = fetch_feeds()
    
    if args.json:
        print(json.dumps(entries, default=str, indent=2))
    else:
        print(format_digest(entries, limit=args.limit))
    
    if args.save:
        with open(args.save, "w") as f:
            json.dump(entries, f, default=str, indent=2)
        print(f"\nSaved {len(entries)} entries to {args.save}", file=sys.stderr)
