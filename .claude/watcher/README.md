# Watcher System

Auto-generated runtime state for the pending-orders watcher.

## Files

- `status.json` — last tick metadata (updated every run)
- `dashboard.md` — human-readable state of all pending orders (rewritten each tick)
- `whitelist_matrix.yaml` — cross-profile compatibility rules (hand-edited)
- `launchd/com.wallytrader.watcher.plist` — macOS launch agent template

## Install (one-time)

```bash
cp .claude/watcher/launchd/com.wallytrader.watcher.plist \
   ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.wallytrader.watcher.plist
launchctl list | grep wallytrader
```

See spec: `docs/superpowers/specs/2026-04-24-watcher-pending-orders-design.md`
