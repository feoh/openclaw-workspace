#!/bin/bash
# Pixelfed ferret checker - searches for ferret posts on Pixelfed via web search
# Runs weekly, reports new findings to Discord

SEARCH_URL="https://duckduckgo.com/html/?q=site%3Apixelfed.social+ferret&t=h&ia=web"
DATA_FILE="/home/feoh/.openclaw/workspace/data/pixelfed-ferrets-previous.txt"
TIMESTAMP=$(date -u +"%Y-%m-%d")

# Fetch search results
RESULT=$(curl -s --max-time 15 "$SEARCH_URL" 2>/dev/null)

if [ -z "$RESULT" ]; then
    echo "SEARCH_FAILED"
    exit 1
fi

# Extract pixelfed post URLs from results
echo "$RESULT" | grep -oP 'https://pixelfed\.social/p/[^"&]+' | sort -u > /tmp/current-ferret-posts.txt

if [ ! -f "$DATA_FILE" ]; then
    # First run - save current list and report
    cp /tmp/current-ferret-posts.txt "$DATA_FILE"
    echo "FIRST_RUN"
    exit 0
fi

# Compare with previous
diff "$DATA_FILE" /tmp/current-ferret-posts.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "NO_NEW_POSTS"
else
    # New posts found
    echo "NEW_POSTS_FOUND"
    diff "$DATA_FILE" /tmp/current-ferret-posts.txt | grep '^>' | sed 's/^> //'
    cp /tmp/current-ferret-posts.txt "$DATA_FILE"
fi