#!/bin/bash
# Weekly memory maintenance script
# Reviews daily memory files and updates MEMORY.md

MEMORY_DIR="/home/feoh/.openclaw/workspace/memory"
MEMORY_FILE="/home/feoh/.openclaw/workspace/MEMORY.md"
TODAY=$(date +%Y-%m-%d)

echo "Memory maintenance run: $TODAY"
echo "Daily files:"
ls -la "$MEMORY_DIR/"
echo "Done."