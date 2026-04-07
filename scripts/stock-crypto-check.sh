#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="/home/feoh/.openclaw/workspace/data"
OUT_FILE="$OUT_DIR/stock-crypto-$(date -u +%F).txt"
mkdir -p "$OUT_DIR"

python3 <<'PY' > "$OUT_FILE"
import json, urllib.request
from datetime import datetime, timezone

UA = 'Mozilla/5.0 (X11; Linux x86_64) OpenClaw-StockCheck/1.0'

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8', 'ignore'))

lines = []
now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
lines.append(f"Morning stock + crypto check — {now}")
lines.append("")

# AMZN via Stooq CSV (no API key)
try:
    req = urllib.request.Request('https://stooq.com/q/l/?s=amzn.us&i=d', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        text = r.read().decode('utf-8', 'ignore').strip()
    parts = text.split(',')
    if len(parts) >= 8:
        symbol, date_s, time_s, open_, high, low, close, volume = parts[:8]
        lines.append(f"AMZN: open {open_} high {high} low {low} close {close} volume {volume}")
    else:
        lines.append(f"AMZN: quote unavailable ({text[:120]})")
except Exception as e:
    lines.append(f"AMZN: fetch failed ({e})")

# BTC/ETH via CoinGecko simple price
try:
    data = fetch_json('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true')
    btc = data.get('bitcoin', {})
    eth = data.get('ethereum', {})
    lines.append(f"BTC: ${btc.get('usd','?')} ({btc.get('usd_24h_change','?'):.2f}% 24h)" if isinstance(btc.get('usd_24h_change'), (int,float)) else f"BTC: ${btc.get('usd','?')}")
    lines.append(f"ETH: ${eth.get('usd','?')} ({eth.get('usd_24h_change','?'):.2f}% 24h)" if isinstance(eth.get('usd_24h_change'), (int,float)) else f"ETH: ${eth.get('usd','?')}")
except Exception as e:
    lines.append(f"Crypto: fetch failed ({e})")

print('\n'.join(lines))
PY

cat "$OUT_FILE"
