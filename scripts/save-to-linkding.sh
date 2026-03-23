#!/bin/bash
# Saves new RSS articles to Linkding
# Requires LINKDING_API_KEY env var

TAG="toread"
INPUT_FILE="/home/feoh/.openclaw/workspace/rss-new-articles.json"

# Load .env if present
if [[ -f "$(dirname "$0")/../.env" ]]; then
  source "$(dirname "$0")/../.env"
fi

API_KEY="${LINKDING_API_KEY}"
API_URL="https://linkding.reedfish-regulus.ts.net/api/bookmarks/"

if [[ -z "$API_KEY" ]]; then
  echo "Error: LINKDING_API_KEY not set"
  exit 1
fi

# Read articles from JSON and save each to Linkding
jq -c '.[]' "$INPUT_FILE" | while IFS= read -r article; do
  title=$(echo "$article" | jq -r '.title')
  url=$(echo "$article" | jq -r '.url')
  feed=$(echo "$article" | jq -r '.feed')
  
  response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
    -H "Authorization: Token $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$url\", \"title\": \"$title\", \"tag_names\": [\"$TAG\"]}")
  
  http_code=$(echo "$response" | tail -1)
  if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
    echo "SAVED: $title"
  else
    echo "FAILED ($http_code): $title - $url"
  fi
done

# Delete the file after processing
rm -f "$INPUT_FILE"
echo "Deleted $INPUT_FILE"
