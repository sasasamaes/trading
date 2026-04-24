#!/bin/bash
# watcher_escalate.sh — spawned by watcher_tick when price near entry.
# Runs claude -p "/watch-deep <id>" in background, deduped per order_id.
#
# Usage: watcher_escalate.sh <order_id>

set -eu

ORDER_ID="${1:-}"
if [ -z "$ORDER_ID" ]; then
    echo "Usage: $0 <order_id>" >&2
    exit 1
fi

LOG="/tmp/wally_escalate_${ORDER_ID}.log"
PIDFILE="/tmp/wally_escalate_${ORDER_ID}.pid"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Dedupe: if a previous escalate is still running, skip
if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[$TIMESTAMP] Escalate already running (pid $OLD_PID) for $ORDER_ID, skipping" >> "$LOG"
        exit 0
    fi
fi

REPO_ROOT="$HOME/Documents/wally-trader"
cd "$REPO_ROOT"

# Spawn Claude headless with 120s hard timeout
echo "[$TIMESTAMP] Spawning claude -p /watch-deep $ORDER_ID" >> "$LOG"

# Detached background with nohup to survive parent exit
# Portable timeout: use background sleep killer (macOS/Linux compatible)
nohup bash -c "(sleep 120; kill -9 \$\$ 2>/dev/null) & claude -p '/watch-deep ${ORDER_ID}' --permission-mode acceptEdits >> '${LOG}' 2>&1" &
echo $! > "$PIDFILE"

exit 0
