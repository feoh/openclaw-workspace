#!/home/feoh/.openclaw/workspace/.venv/bin/python3
"""
Save articles from the last RSS digest to Linkding by number.
Usage: python3 rss-save.py 1 3 7   or   python3 rss-save.py all
"""
import json
import os
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv(dotenv_path="/home/feoh/.openclaw/workspace/.env")

LAST_DIGEST_FILE = "/home/feoh/.openclaw/workspace/data/rss-last-digest.json"
LINKDING_URL = "https://linkding.reedfish-regulus.ts.net/api/bookmarks/"


def save_to_linkding(url, title):
    api_key = os.getenv("LINKDING_API_KEY")
    if not api_key:
        print("ERROR: LINKDING_API_KEY not set", file=sys.stderr)
        return None

    data = json.dumps({
        "url": url,
        "title": title,
        "tag_names": ["toread"],
    }).encode()
    req = urllib.request.Request(
        LINKDING_URL,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Token {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("id")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "unique" in body.lower() or e.code == 400:
            return "already_saved"
        print(f"HTTP {e.code} saving {url}: {body[:100]}", file=sys.stderr)
        return None


def main():
    if not os.path.exists(LAST_DIGEST_FILE):
        print("No digest found. Run rss-digest.py first.")
        sys.exit(1)

    with open(LAST_DIGEST_FILE) as f:
        articles = json.load(f)

    if len(sys.argv) < 2:
        print("Usage: rss-save.py <numbers...>  or  rss-save.py all")
        sys.exit(1)

    if sys.argv[1] == "all":
        targets = articles
    else:
        nums = []
        for arg in sys.argv[1:]:
            try:
                nums.append(int(arg))
            except ValueError:
                print(f"Skipping invalid number: {arg}")
        targets = [a for a in articles if a["num"] in nums]

        found_nums = {a["num"] for a in targets}
        for n in nums:
            if n not in found_nums:
                print(f"⚠️  #{n} not found in last digest")

    print(f"Saving {len(targets)} articles to Linkding...\n")
    for a in targets:
        result = save_to_linkding(a["url"], a["title"])
        if result == "already_saved":
            print(f"⏭️  #{a['num']} already saved — {a['title'][:55]}")
        elif result:
            print(f"✅ #{a['num']} ID:{result} — {a['title'][:55]}")
        else:
            print(f"❌ #{a['num']} FAILED — {a['title'][:55]}")


if __name__ == "__main__":
    main()
