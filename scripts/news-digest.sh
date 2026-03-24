#!/bin/bash
# Daily news digest fetcher
# Sources: BBC, AP, Reuters, Al Jazeera, and various outlets

OUTPUT_FILE="/home/feoh/.openclaw/workspace/data/news-digest-$(date +%Y-%m-%d).txt"

# Quick headlines fetch via BBC
curl -s "https://feeds.bbci.co.uk/news/world/rss.xml" | \
  python3 -c "
import sys, xml.etree.ElementTree as ET
tree = ET.parse(sys.stdin)
root = tree.getroot()
items = root.findall('.//item')
for i, item in enumerate(items[:15]):
    title = item.find('title').text
    link = item.find('link').text
    print(f'{i+1}. {title}')
    print(f'   {link}')
" > "$OUTPUT_FILE"

echo "Fetched: $(date)" >> "$OUTPUT_FILE"
cat "$OUTPUT_FILE"