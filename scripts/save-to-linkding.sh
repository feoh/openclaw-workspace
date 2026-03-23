#!/bin/bash
# Saves new RSS articles to Linkding

LINKDING_URL="https://linkding.reedfish-regulus.ts.net/bookmarks"
API_KEY="e8598748d64f35bd1de2ecd8dd0559a01bd9de93"
TAG="toread"
INPUT_FILE="/home/feoh/.openclaw/workspace/rss-new-articles.json"

# Read articles from JSON and save each to Linkding
jq -c '.[]' "$INPUT_FILE" | while IFS= read -r article; do
  title=$(echo "$article" | jq -r '.title')
  url=$(echo "$article" | jq -r '.url')
  feed=$(echo "$article" | jq -r '.feed')
  
  # Create bookmark with toread tag
  response=$(curl -s -w "\n%{http_code}" -X POST "$LINKDING_URL" \
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
