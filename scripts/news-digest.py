#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Daily News Digest — Multi-source with political leaning and fact-check status
Sources categorized by leaning: 🟥 conservative, 🟦 liberal, ⚖️ balanced/center
Fact-check icons: ✅ true, ⚠️ mostly true, 🤔 half true, ❌ false, 🔍 unverified
"""

import feedparser
import html
import re
import json
import sys
from datetime import datetime
from collections import defaultdict

# Source configuration: (name, url, rss_feed, leaning)
# leaning: 1 = conservative, 2 = liberal, 3 = balanced/center
SOURCES = {
    # Conservative sources
    "fox_news": {
        "name": "Fox News",
        "feed": "https://feeds.foxnews.com/foxnews/latest",
        "leaning": 1,
        "category": "conservative"
    },
    "breitbart": {
        "name": "Breitbart",
        "feed": "https://feeds.feedburner.com/breitbart",
        "leaning": 1,
        "category": "conservative"
    },
    # Liberal sources
    "cnn": {
        "name": "CNN",
        "feed": "http://rss.cnn.com/rss/edition.rss",
        "leaning": 2,
        "category": "liberal"
    },
    "msnbc": {
        "name": "MSNBC",
        "feed": "https://www.msnbc.com/rss/latest",
        "leaning": 2,
        "category": "liberal"
    },
    # Balanced/Center sources
    "reuters": {
        "name": "Reuters",
        "feed": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "leaning": 3,
        "category": "balanced"
    },
    "ap_news": {
        "name": "AP News",
        "feed": "https://apnews.com/rss",
        "leaning": 3,
        "category": "balanced"
    },
    "bbc_world": {
        "name": "BBC World",
        "feed": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "leaning": 3,
        "category": "balanced"
    },
    "npr": {
        "name": "NPR",
        "feed": "https://feeds.npr.org/1001/rss.xml",
        "leaning": 3,
        "category": "balanced"
    },
    "wa_post": {
        "name": "Washington Post",
        "feed": "https://feeds.washingtonpost.com/rss/national",
        "leaning": 3,
        "category": "balanced"
    },
    "ny_times": {
        "name": "New York Times",
        "feed": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "leaning": 3,
        "category": "balanced"
    },
}

# Fact check feeds
FACT_CHECK_SOURCES = {
    "politifact": {
        "name": "PolitiFact",
        "feed": "https://www.politifact.com/feed/",
    },
    "snopes": {
        "name": "Snopes",
        "feed": "https://snopes.com/feed/",
    },
    "reuters_fact": {
        "name": "Reuters Fact Check",
        "feed": "https://feeds.reuters.com/reuters/MostRead/?format=xml",
        # Note: Reuters fact-check section has different feeds
    },
    "ap_factcheck": {
        "name": "AP Fact Check",
        "feed": "https://apnews.com/rss/factcheck",
    },
}

LEANING_EMOJI = {
    1: "🟥",  # conservative
    2: "🟦",  # liberal
    3: "⚖️"   # balanced
}

def clean_title(raw_title):
    """Clean HTML entities and extra whitespace from title."""
    title = html.unescape(raw_title or "")
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def fetch_headlines():
    """Fetch headlines from all sources."""
    headlines = []
    seen_urls = set()
    
    for source_id, config in SOURCES.items():
        try:
            feed = feedparser.parse(config["feed"], agent="NewsDigest/1.0")
            for entry in feed.entries[:5]:
                title = clean_title(getattr(entry, 'title', ''))
                link = getattr(entry, 'link', '') or ''
                
                if not title or not link or link in seen_urls:
                    continue
                
                seen_urls.add(link)
                
                # Extract date
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
                
                headlines.append({
                    "title": title,
                    "url": link,
                    "source": config["name"],
                    "source_id": source_id,
                    "leaning": config["leaning"],
                    "leaning_emoji": LEANING_EMOJI[config["leaning"]],
                    "date": date,
                    "fact_check": None,  # Will be filled by fact-check lookup
                })
        except Exception as e:
            print(f"Error fetching {config['name']}: {e}", file=sys.stderr)
    
    # Sort by date, newest first
    headlines.sort(key=lambda x: x["date"] or datetime.min, reverse=True)
    return headlines

def fetch_fact_checks():
    """Fetch recent fact checks from known sources."""
    fact_checks = []
    
    # Try PolitiFact first - they have good RSS
    try:
        feed = feedparser.parse(FACT_CHECK_SOURCES["politifact"]["feed"], agent="NewsDigest/1.0")
        for entry in feed.entries[:20]:
            title = clean_title(getattr(entry, 'title', ''))
            link = getattr(entry, 'link', '') or ''
            
            # Extract ruling from title (PolitiFact format: "Statement: Ruling")
            ruling = extract_ruling(title)
            
            fact_checks.append({
                "title": title,
                "url": link,
                "source": "PolitiFact",
                "ruling": ruling,
            })
    except Exception as e:
        print(f"Error fetching PolitiFact: {e}", file=sys.stderr)
    
    # Try Snopes
    try:
        feed = feedparser.parse(FACT_CHECK_SOURCES["snopes"]["feed"], agent="NewsDigest/1.0")
        for entry in feed.entries[:15]:
            title = clean_title(getattr(entry, 'title', ''))
            link = getattr(entry, 'link', '') or ''
            
            ruling = extract_snopes_ruling(title)
            
            fact_checks.append({
                "title": title,
                "url": link,
                "source": "Snopes",
                "ruling": ruling,
            })
    except Exception as e:
        print(f"Error fetching Snopes: {e}", file=sys.stderr)
    
    return fact_checks

def extract_ruling(title):
    """Extract ruling from PolitiFact-style title."""
    title_lower = title.lower()
    
    # PolitiFact rulings
    rulings = {
        "true": "✅",
        "mostly true": "⚠️",
        "half true": "🤔",
        "mostly false": "❌",
        "false": "❌",
        "pants on fire": "🔥",
    }
    
    for ruling, emoji in rulings.items():
        if ruling in title_lower:
            return emoji
    
    return "🔍"  # unverified

def extract_snopes_ruling(title):
    """Extract ruling from Snopes-style title."""
    title_lower = title.lower()
    
    if "true" in title_lower and "false" not in title_lower:
        return "✅"
    elif "false" in title_lower:
        return "❌"
    elif "misleading" in title_lower:
        return "🤔"
    elif "unproven" in title_lower or "unverified" in title_lower:
        return "🔍"
    
    return "🔍"

def match_fact_check(headline, fact_checks):
    """Try to match a headline with a fact check article."""
    headline_words = set(headline["title"].lower().split())
    
    best_match = None
    best_score = 0
    
    for fc in fact_checks:
        fc_words = set(fc["title"].lower().split())
        
        # Calculate word overlap
        overlap = len(headline_words & fc_words)
        if overlap > best_score and overlap >= 3:
            best_score = overlap
            best_match = fc
    
    return best_match

def format_digest(headlines, fact_checks, limit=15):
    """Format the digest for Discord output."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    lines = [
        f"**📰 Daily News Digest — {today}**",
        f"__{len(headlines)} headlines from {len(SOURCES)} sources__\n",
        "**Political leaning:** 🟥 conservative · 🟦 liberal · ⚖️ balanced/center",
        "**Fact-check status:** ✅ true · ⚠️ mostly true · 🤔 half true · ❌ false · 🔍 unverified\n",
    ]
    
    # Group by leaning for diversity display
    by_leaning = defaultdict(list)
    for h in headlines:
        by_leaning[h["leaning"]].append(h)
    
    count = 0
    for h in headlines:
        if count >= limit:
            break
        
        # Try to match a fact check
        fc = match_fact_check(h, fact_checks)
        fact_icon = fc["ruling"] if fc else "🔍"
        fact_source = f" ({fc['source']})" if fc and fc.get("source") else ""
        
        date_str = h["date"].strftime("%m-%d") if h["date"] else "??"
        
        lines.append(
            f"{h['leaning_emoji']}{fact_icon} **{count + 1}.** [{h['title']}]({h['url']})"
        )
        lines.append(f"   {date_str} · {h['source']}{fact_source}\n")
        
        count += 1
    
    return "\n".join(lines)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Daily News Digest")
    parser.add_argument("--limit", type=int, default=15, help="Max headlines")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    print("Fetching headlines...", file=sys.stderr)
    headlines = fetch_headlines()
    
    print("Fetching fact checks...", file=sys.stderr)
    fact_checks = fetch_fact_checks()
    
    # Match fact checks to headlines
    for h in headlines:
        fc = match_fact_check(h, fact_checks)
        if fc:
            h["fact_check"] = fc["ruling"]
            h["fact_check_source"] = fc["source"]
    
    if args.json:
        print(json.dumps({
            "headlines": headlines,
            "fact_checks": fact_checks,
        }, default=str, indent=2))
    else:
        print(format_digest(headlines, fact_checks, limit=args.limit))
