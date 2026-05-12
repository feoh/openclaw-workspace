#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Evening News Digest — Top 5 cross-spectrum stories
See docs/evening-news-spec.md for the full feature spec. CHECK THAT FILE before making changes.

Logic:
1. Fetch top headlines from sources across political spectrum
2. Group stories by topic (keyword overlap)
3. Rank by number of sources covering the story
4. Show top 5 with coverage indicator (🟥 conservative-only, 🟦 liberal-only, 🟪 both, ⚖️ center)
"""

import feedparser
import html
import re
import json
import sys
import urllib.request
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCES = {
    "fox_news":    {"name": "Fox News",        "feed": "https://feeds.foxnews.com/foxnews/latest",                                  "leaning": "conservative"},
    "breitbart":   {"name": "Breitbart",        "feed": "https://feeds.feedburner.com/breitbart",                                    "leaning": "conservative"},
    "newsmax":     {"name": "Newsmax",          "feed": "https://www.newsmax.com/rss/news/1",                                        "leaning": "conservative"},
    "aljazeera":   {"name": "Al Jazeera",       "feed": "https://www.aljazeera.com/xml/rss/all.xml",                                "leaning": "center"},
    "haaretz":     {"name": "Haaretz",          "feed": "https://www.haaretz.com/srv/all-headlines-rss",                            "leaning": "center"},
    "cnn":         {"name": "CNN",              "feed": "http://rss.cnn.com/rss/edition.rss",                                        "leaning": "liberal"},
    "nbcnews":     {"name": "NBC News",         "feed": "https://feeds.nbcnews.com/nbcnews/public/news",                             "leaning": "liberal"},
    "thehill":     {"name": "The Hill",         "feed": "https://thehill.com/news/feed/",                                            "leaning": "center"},
    "politico":    {"name": "Politico",         "feed": "https://www.politico.com/rss/politicopicks.xml",                           "leaning": "center"},
    "bbc_world":   {"name": "BBC World",        "feed": "https://feeds.bbci.co.uk/news/world/rss.xml",                              "leaning": "center"},
    "npr":         {"name": "NPR",              "feed": "https://feeds.npr.org/1001/rss.xml",                                        "leaning": "center"},
    "propublica":  {"name": "ProPublica",       "feed": "https://www.propublica.org/feeds/propublica/main",                         "leaning": "center"},
    "wa_post":     {"name": "Washington Post",  "feed": "https://feeds.washingtonpost.com/rss/national",                            "leaning": "center"},
    "ny_times":    {"name": "New York Times",   "feed": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",                "leaning": "center"},
}

# Stop words to ignore when matching stories
STOP_WORDS = {
    'the','a','an','in','on','at','to','for','of','and','or','is','are','was','were',
    'be','been','being','have','has','had','do','does','did','will','would','could',
    'should','may','might','shall','can','with','from','by','as','this','that','it',
    'its','their','they','he','she','his','her','we','our','you','your','what','how',
    'new','says','say','said','after','over','amid','about','more','up','down','out'
}


def clean_title(raw):
    t = html.unescape(raw or "")
    return re.sub(r'\s+', ' ', t).strip()


def title_keywords(title):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
    return {w for w in words if w not in STOP_WORDS}


XML_INVALID_CHAR_RE = re.compile(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]")


def download_feed(url):
    header_profiles = [
        {
            "User-Agent": "NewsDigest/1.0 (+OpenClaw)",
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.1",
            "Accept-Language": "en-US,en;q=0.8",
        },
        {
            # Some feeds (notably Politico behind Cloudflare) reject minimal bot-like headers.
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.politico.com/",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    ]
    last_error = None
    for headers in header_profiles:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except Exception as e:
            last_error = e
    raise last_error


def sanitize_xml_bytes(raw_bytes):
    text = raw_bytes.decode("utf-8", "replace")
    text = XML_INVALID_CHAR_RE.sub("", text)
    text = re.sub(r"&(?!#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z][A-Za-z0-9._:-]*;)", "&amp;", text)
    return text.encode("utf-8")


def parse_feed_with_recovery(url):
    raw = download_feed(url)
    feed = feedparser.parse(raw)
    if feed.entries or not feed.get("bozo"):
        return feed

    sanitized = sanitize_xml_bytes(raw)
    repaired = feedparser.parse(sanitized)
    if repaired.entries:
        repaired["recovered_from_bozo"] = True
        repaired["original_bozo_exception"] = repr(feed.get("bozo_exception", "unknown"))
        return repaired

    raise ValueError(f"Feed parse error: {feed.get('bozo_exception', 'unknown')}")


def fetch_single(source_id, config, retries=3, backoff=2):
    import time
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            feed = parse_feed_with_recovery(config["feed"])
            results = []
            for entry in feed.entries[:8]:
                title = clean_title(getattr(entry, 'title', ''))
                link = getattr(entry, 'link', '') or ''
                if not title or not link:
                    continue
                date = None
                for attr in ['published_parsed', 'updated_parsed']:
                    parsed = getattr(entry, attr, None)
                    if parsed:
                        try:
                            from time import mktime
                            date = datetime.fromtimestamp(mktime(parsed))
                            break
                        except:
                            pass
                results.append({
                    "title": title,
                    "url": link,
                    "source": config["name"],
                    "source_id": source_id,
                    "leaning": config["leaning"],
                    "keywords": title_keywords(title),
                    "date": date,
                })
            if results:
                if feed.get("recovered_from_bozo"):
                    print(
                        f"  {config['name']} feed recovered after sanitizing malformed XML ({feed.get('original_bozo_exception', 'unknown')})",
                        file=sys.stderr,
                    )
                return results
            raise ValueError("No entries returned")
        except Exception as e:
            last_error = e
            if attempt < retries:
                print(f"  {config['name']} attempt {attempt} failed: {e} — retrying in {backoff}s", file=sys.stderr)
                time.sleep(backoff)
            else:
                print(f"Error fetching {config['name']} after {retries} attempts: {last_error}", file=sys.stderr)
    return []


def group_stories(all_headlines):
    """Group headlines by topic using keyword overlap. Returns list of story clusters."""
    clusters = []

    for h in all_headlines:
        placed = False
        for cluster in clusters:
            # Compare against cluster's merged keywords
            overlap = len(h["keywords"] & cluster["keywords"])
            if overlap >= 2:
                cluster["headlines"].append(h)
                cluster["keywords"] |= h["keywords"]
                placed = True
                break
        if not placed:
            clusters.append({
                "keywords": set(h["keywords"]),
                "headlines": [h],
            })

    return clusters


def coverage_indicator(cluster):
    """Return coverage emoji based on which leanings covered the story."""
    leanings = {h["leaning"] for h in cluster["headlines"]}
    has_con = "conservative" in leanings
    has_lib = "liberal" in leanings
    has_cen = "center" in leanings

    if has_con and has_lib:
        return "🟪"  # cross-spectrum
    elif has_con:
        return "🟥"  # conservative only
    elif has_lib:
        return "🟦"  # liberal only
    else:
        return "⚖️"  # center/neutral only


def best_headline(cluster):
    """Pick the best representative headline from a cluster (prefer center sources)."""
    leaning_pref = ["center", "liberal", "conservative"]
    for pref in leaning_pref:
        for h in cluster["headlines"]:
            if h["leaning"] == pref:
                return h
    return cluster["headlines"][0]


def format_digest(clusters, limit=5):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"**📰 Evening News Digest — {today}**",
        "_Top stories across the political spectrum_\n",
        "**Coverage:** 🟪 both sides · 🟥 conservative · 🟦 liberal · ⚖️ center\n",
    ]

    # Sort clusters by total source count (most coverage = most important)
    # Only include clusters with at least 2 sources — single-source stories aren't top news
    sorted_clusters = sorted(
        [c for c in clusters if len(c["headlines"]) >= 2],
        key=lambda c: len(c["headlines"]),
        reverse=True
    )

    if not sorted_clusters:
        return f"**📰 Evening News Digest — {today}**\n⚠️ Not enough cross-source stories found to generate digest."

    for i, cluster in enumerate(sorted_clusters[:limit], 1):
        indicator = coverage_indicator(cluster)
        h = best_headline(cluster)

        # Source list (deduplicated)
        sources = list(dict.fromkeys(x["source"] for x in cluster["headlines"]))
        source_str = ", ".join(sources[:5])
        count = len(cluster["headlines"])

        lines.append(f"{indicator} [{h['title']}]({h['url']})")
        lines.append(f"   {source_str} — {count} source{'s' if count != 1 else ''}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors = []

    print("Fetching headlines...", file=sys.stderr, flush=True)
    all_headlines = []
    seen_urls = set()
    failed_sources = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_single, sid, cfg): (sid, cfg) for sid, cfg in SOURCES.items()}
        for future in as_completed(futures):
            sid, cfg = futures[future]
            try:
                results = future.result()
                if not results:
                    failed_sources.append(cfg["name"])
                for h in results:
                    if h["url"] not in seen_urls:
                        seen_urls.add(h["url"])
                        all_headlines.append(h)
            except Exception as e:
                failed_sources.append(cfg["name"])
                errors.append(f"{cfg['name']}: {e}")

    print(f"Got {len(all_headlines)} headlines from {len(SOURCES)} sources", file=sys.stderr, flush=True)

    if len(all_headlines) < 10:
        print(f"⚠️ WARNING: Only {len(all_headlines)} headlines fetched — digest may be incomplete.", file=sys.stderr)
        errors.append(f"Low headline count: only {len(all_headlines)} fetched (expected 40+)")

    print("Grouping stories...", file=sys.stderr, flush=True)
    clusters = group_stories(all_headlines)
    print(f"Found {len(clusters)} story clusters", file=sys.stderr, flush=True)

    if len(clusters) < args.limit:
        errors.append(f"Only {len(clusters)} story clusters found — could not produce {args.limit} top stories")

    if args.json:
        print(json.dumps([{
            "indicator": coverage_indicator(c),
            "headline": best_headline(c)["title"],
            "sources": [h["source"] for h in c["headlines"]],
            "count": len(c["headlines"]),
        } for c in sorted(clusters, key=lambda c: len(c["headlines"]), reverse=True)[:args.limit]], indent=2))
    else:
        output = format_digest(clusters, limit=args.limit)
        if errors:
            output += "\n\n⚠️ **Digest warnings:**\n" + "\n".join(f"- {e}" for e in errors)
        if failed_sources:
            output += f"\n- Failed to fetch: {', '.join(failed_sources)}"
        print(output)
