#!/usr/bin/env bash
# adapters/opencode/install.sh
# First-time setup + install git pre-commit hook for auto-sync.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

# Verify Python 3 + pyyaml available
python3 -c "import yaml" 2>/dev/null || {
  echo "⚠️  PyYAML not installed. Installing..."
  pip3 install --user pyyaml
}

# First generation
echo "🔄 Generating .opencode/ from system/..."
python3 "$REPO/adapters/opencode/transform.py"

# Install pre-commit hook — use git rev-parse for compatibility with worktrees
HOOK_PATH="$(git rev-parse --git-path hooks/pre-commit)"
HOOK_DIR="$(dirname "$HOOK_PATH")"

# Handle case where HOOK_DIR doesn't exist (rare, e.g. linked worktree)
mkdir -p "$HOOK_DIR"

# Marker to detect if already installed
MARKER='# opencode-adapter-v2'
LEGACY_MARKER='# opencode-adapter-v1'

# Auto-upgrade v1 → v2 (replace legacy hook block in place)
if [ -f "$HOOK_PATH" ] && grep -q "$LEGACY_MARKER" "$HOOK_PATH" && ! grep -q "$MARKER" "$HOOK_PATH"; then
  echo "↻ Upgrading pre-commit hook v1 → v2..."
  # Strip the legacy block (from marker to next blank line / EOF)
  awk -v marker="$LEGACY_MARKER" '
    BEGIN {skip=0}
    $0 ~ marker {skip=1; next}
    skip && /^fi$/ {skip=0; next}
    !skip {print}
  ' "$HOOK_PATH" > "$HOOK_PATH.tmp" && mv "$HOOK_PATH.tmp" "$HOOK_PATH"
fi

if [ -f "$HOOK_PATH" ] && grep -q "$MARKER" "$HOOK_PATH"; then
  echo "✓ pre-commit hook already installed (v2)"
else
  if [ -f "$HOOK_PATH" ]; then
    # Backup existing hook and append our logic
    cp "$HOOK_PATH" "$HOOK_PATH.backup-$(date +%s)"
    echo "   Backed up existing pre-commit to $HOOK_PATH.backup-*"
  fi

  cat >> "$HOOK_PATH" <<'EOF'

# opencode-adapter-v2 — auto-regenerate .opencode/ + opencode.json on system/ changes
__REPO="$(git rev-parse --show-toplevel)"
__CHANGED=$(git diff --cached --name-only | grep -E '^system/(commands|agents|mcp)/' || true)
if [ -n "$__CHANGED" ]; then
  echo "[opencode-adapter] system/ changed → re-generando .opencode/ + opencode.json"
  python3 "$__REPO/adapters/opencode/transform.py" || exit 1
  git add "$__REPO/.opencode" "$__REPO/opencode.json"
fi
EOF
  chmod +x "$HOOK_PATH"
  echo "✓ pre-commit hook installed at $HOOK_PATH"
fi

echo ""
echo "✅ OpenCode adapter ready."
echo "   .opencode/ will auto-regenerate on git commit when system/ changes."
echo "   For real-time sync during active editing: bash adapters/opencode/watch.sh"
