#!/home/feoh/.openclaw/workspace/.venv/bin/python
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

API_URL = "https://linkding.reedfish-regulus.ts.net/api/bookmarks/"
DEFAULT_TAGS = ["toread"]
WORKSPACE = Path("/home/feoh/.openclaw/workspace")


def load_api_key() -> str:
    env_path = WORKSPACE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("LINKDING_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    tools_md = WORKSPACE / "TOOLS.md"
    if tools_md.exists():
        m = re.search(r"<LINKDING_API_KEY>", tools_md.read_text())
        if m:
            raise SystemExit("LINKDING_API_KEY placeholder found in TOOLS.md; real key must come from .env")

    raise SystemExit("LINKDING_API_KEY not found in workspace .env")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: linkding-add-url.py <url> [title]", file=sys.stderr)
        return 2

    url = sys.argv[1].strip()
    title = sys.argv[2].strip() if len(sys.argv) > 2 else None

    payload = {"url": url, "tag_names": DEFAULT_TAGS}
    if title:
        payload["title"] = title

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Token {load_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            print(body)
            return 0
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(detail, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
