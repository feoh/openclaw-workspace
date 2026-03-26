#!/bin/bash
# Batch save articles to Linkding - fixed JSON escaping

API_URL="https://linkding.reedfish-regulus.ts.net/api/bookmarks/"
API_KEY="e8598748d64f35bd1de2ecd8dd0559a01bd9de93"

INPUT_FILE="/home/feoh/.openclaw/workspace/rss-new-articles.json"
OUTPUT_FILE="/home/feoh/.openclaw/workspace/rss-saved-articles.json"

# Check if file exists and has content
if [ ! -s "$INPUT_FILE" ]; then
    echo "No new articles to save"
    exit 0
fi

TOTAL=$(jq length "$INPUT_FILE")
echo "Processing $TOTAL articles..."

SUCCESS=0
FAIL=0
SAVED_URLS=()

# Read each article line by line
while IFS= read -r article; do
    URL=$(echo "$article" | jq -r '.url')
    TITLE=$(echo "$article" | jq -r '.title')
    FEED=$(echo "$article" | jq -r '.feed')
    
    # Validate URL - must be a proper http/https URL
    if [[ ! "$URL" =~ ^https?:// ]]; then
        FAIL=$((FAIL + 1))
        continue
    fi
    
    # Build JSON body properly using jq -n
    BODY=$(jq -n \
        --arg url "$URL" \
        --arg title "$TITLE" \
        '{url: $url, tag_names: ["toread"], title: $title}')
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
        -H "Authorization: Token $API_KEY" \
        -H "Content-Type: application/json" \
        -d "$BODY")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "201" ]; then
        SAVED_URLS+=("[$FEED] $TITLE")
        SUCCESS=$((SUCCESS + 1))
    else
        FAIL=$((FAIL + 1))
    fi
    
    # Small delay every 100 requests to be nice to the server
    TOTAL_DONE=$((SUCCESS + FAIL))
    if [ $((TOTAL_DONE % 100)) -eq 0 ] && [ $TOTAL_DONE -lt $TOTAL ]; then
        echo "  ... $TOTAL_DONE processed, continuing..."
        sleep 0.5
    fi
    
done < <(jq -c '.[]' "$INPUT_FILE")

echo ""
echo "=== Summary ==="
echo "Total in file: $TOTAL"
echo "Successful: $SUCCESS"
echo "Failed (invalid URLs): $FAIL"

# Save success list
if [ ${#SAVED_URLS[@]} -gt 0 ]; then
    printf '%s\n' "${SAVED_URLS[@]}" > "$OUTPUT_FILE"
    echo "Saved success list to $OUTPUT_FILE"
fi

# Delete the input file
rm -f "$INPUT_FILE"
echo "Deleted $INPUT_FILE"
