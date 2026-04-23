#!/usr/bin/env bash
# adapters/claude-code/install.sh
# Idempotent: creates symlinks from .claude/ to system/
# Safe to run multiple times.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

# Symlink commands/agents/skills if not already symlinked
for dir in commands agents skills; do
  src="system/$dir"
  dst=".claude/$dir"

  if [ ! -d "$src" ]; then
    echo "⚠️  $src does not exist — run migration first"
    continue
  fi

  if [ -L "$dst" ]; then
    # Already a symlink, verify target
    target=$(readlink "$dst")
    if [ "$target" = "../system/$dir" ]; then
      echo "✓ $dst already symlinked"
    else
      echo "⚠️  $dst points to $target, expected ../system/$dir — fixing"
      rm "$dst"
      ln -s "../system/$dir" "$dst"
    fi
  elif [ -d "$dst" ] && [ ! -L "$dst" ]; then
    echo "⚠️  $dst is a real dir (not symlink) — backup & symlink"
    mv "$dst" "${dst}.backup"
    ln -s "../system/$dir" "$dst"
    echo "   Backup in ${dst}.backup — delete manually if safe"
  else
    # Doesn't exist yet
    ln -s "../system/$dir" "$dst"
    echo "✓ created symlink $dst → ../system/$dir"
  fi
done

echo ""
echo "✅ Claude Code adapter synced."
echo "   MCP config stays in global ~/.claude (via 'claude mcp add' or plugins)."
echo "   To sync MCP from system/mcp/servers.json, manually re-add:"
echo "   claude mcp remove tradingview && claude mcp add-json tradingview \"\$(cat system/mcp/servers.json | jq '.servers.tradingview')\""
