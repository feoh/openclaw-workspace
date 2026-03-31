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
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCES = {
    "fox_news":    {"name": "Fox News",        "feed": "https://feeds.foxnews.com/foxnews/latest",                                  "leaning": "conservative"},
    "breitbart":   {"name": "Breitbart",        "feed": "https://feeds.feedburner.com/breitbart",                                    "leaning": "conservative"},
    "cnn":         {"name": "CNN",              "feed": "http://rss.cnn.com/rss/edition.rss",                                        "leaning": "liberal"},
    "msnbc":       {"name": "MSNBC",            "feed": "https://www.msnbc.com/rss/latest",                                          "leaning": "liberal"},
    "reuters":     {"name": "Reuters",          "feed": "https://feeds.reuters.com/reuters/topNews",                                 "leaning": "center"},
    "ap_news":     {"name": "AP News",          "feed": "https://apnews.com/rss",                                                    "leaning": "center"},
    "bbc_world":   {"name": "BBC World",        "feed": "https://feeds.bbci.co.uk/news/world/rss.xml",                              "leaning": "center"},
    "npr":         {"name": "NPR",              "feed": "https://feeds.npr.org/1001/rss.xml",                                        "leaning": "center"},
    "wa_post":     {"name": "Washington Post",  "feed": "https://feeds.washingtonpost.com/rss/national",                            "leaning": "center"},
    "ny_times":    {"name": "New York Times",   "feed": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",                "leaning": "center"},
}

FACT_CHECK_FEEDS = [
    ("PolitiFact", "https://www.politifact.com/feed/"),
    ("Snopes",     "https://snopes.com/feed/"),
]

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


def fetch_single(source_id, config):
    try:
        feed = feedparser.parse(config["feed"], agent="NewsDigest/1.0")
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
        return results
    except Exception as e:
        print(f"Error fetching {config['name']}: {e}", file=sys.stderr)
        return []


def fetch_fact_checks():
    checks = []
    for source_name, url in FACT_CHECK_FEEDS:
        try:
            feed = feedparser.parse(url, agent="NewsDigest/1.0")
            for entry in feed.entries[:20]:
                title = clean_title(getattr(entry, 'title', ''))
                link = getattr(entry, 'link', '') or ''
                ruling = extract_ruling(title, source_name)
                checks.append({"title": title, "url": link, "source": source_name, "ruling": ruling})
        except Exception as e:
            print(f"Error fetching {source_name}: {e}", file=sys.stderr)
    return checks


def extract_ruling(title, source):
    t = title.lower()
    if source == "PolitiFact":
        for label, icon in [("pants on fire","🔥"),("mostly false","❌"),("false","❌"),
                             ("half true","🤔"),("mostly true","⚠️"),("true","✅")]:
            if label in t:
                return icon
    elif source == "Snopes":
        if "false" in t: return "❌"
        if "misleading" in t: return "🤔"
        if "true" in t and "false" not in t: return "✅"
        if "unproven" in t or "unverified" in t: return "🔍"
    return "🔍"


def match_fact_check(keywords, fact_checks):
    best, best_score = None, 0
    for fc in fact_checks:
        overlap = len(keywords & fc_keywords(fc))
        if overlap > best_score and overlap >= 3:
            best_score = overlap
            best = fc
    return best


def fc_keywords(fc):
    return title_keywords(fc["title"])


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


def format_digest(clusters, fact_checks, limit=5):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"**📰 Evening News Digest — {today}**",
        "_Top stories across the political spectrum_\n",
        "**Coverage:** 🟪 both sides · 🟥 conservative · 🟦 liberal · ⚖️ center",
        "**Fact-check:** ✅ true · ⚠️ mostly true · 🤔 half true · ❌ false · 🔍 unverified\n",
    ]

    # Sort clusters by total source count (most coverage = most important)
    sorted_clusters = sorted(clusters, key=lambda c: len(c["headlines"]), reverse=True)

    for i, cluster in enumerate(sorted_clusters[:limit], 1):
        indicator = coverage_indicator(cluster)
        h = best_headline(cluster)

        # Fact check
        fc = match_fact_check(cluster["keywords"], fact_checks)
        fc_icon = fc["ruling"] if fc else "🔍"

        # Source list (deduplicated)
        sources = list(dict.fromkeys(x["source"] for x in cluster["headlines"]))
        source_str = ", ".join(sources[:5])
        count = len(cluster["headlines"])

        lines.append(f"{indicator}{fc_icon} **{i}.** [{h['title']}]({h['url']})")
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

    print("Fetching fact checks...", file=sys.stderr, flush=True)
    fact_checks = fetch_fact_checks()

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
        output = format_digest(clusters, fact_checks, limit=args.limit)
        if errors:
            output += "\n\n⚠️ **Digest warnings:**\n" + "\n".join(f"- {e}" for e in errors)
        if failed_sources:
            output += f"\n- Failed to fetch: {', '.join(failed_sources)}"
        print(output)
