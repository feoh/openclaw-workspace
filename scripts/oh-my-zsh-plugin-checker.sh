#!/bin/bash
# Check Oh My Zsh plugins repo for new plugins
# Stores last known plugin list in ~/.openclaw/workspace/data/oh-my-zsh-plugins.json

DATA_DIR="/home/feoh/.openclaw/workspace/data"
PREV_FILE="$DATA_DIR/oh-my-zsh-plugins.json"
CURR_FILE="$DATA_DIR/oh-my-zsh-plugins-current.json"

mkdir -p "$DATA_DIR"

# Fetch current plugin list from GitHub API
curl -s "https://api.github.com/repos/ohmyzsh/ohmyzsh/contents/plugins" | \
  python3 -c "
import sys, json
try:
    items = json.load(sys.stdin)
    plugins = sorted([f['name'] for f in items if f['type'] == 'dir'])
    print(json.dumps({'plugins': plugins, 'count': len(plugins)}))
except Exception as e:
    print(json.dumps({'error': str(e)}))
    sys.exit(1)
" > "$CURR_FILE"

if [ ! -f "$PREV_FILE" ]; then
    echo "First run - saving plugin list"
    cp "$CURR_FILE" "$PREV_FILE"
    echo "NO_NEW_PLUGINS"
    exit 0
fi

# Compare
python3 -c "
import json

with open('$PREV_FILE') as f:
    prev = json.load(f)
with open('$CURR_FILE') as f:
    curr = json.load(f)

prev_plugins = set(prev.get('plugins', []))
curr_plugins = set(curr.get('plugins', []))
new_plugins = curr_plugins - prev_plugins

if new_plugins:
    print(f'NEW_PLUGINS: {len(new_plugins)}')
    for p in sorted(new_plugins):
        print(f'  - {p}')
else:
    print('NO_NEW_PLUGINS')
"

# Update stored list
mv "$CURR_FILE" "$PREV_FILE"