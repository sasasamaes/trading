#!/usr/bin/env bash
# Wally Trader — aliases for multi-terminal Claude sessions.
# Source from ~/.zshrc or ~/.bashrc:
#   source /Users/josecampos/Documents/wally-trader/.claude/scripts/wally_aliases.sh
#
# Each alias spawns a Claude session with a fixed profile via WALLY_PROFILE env var.
# Profiles do not cross-contaminate: each terminal tab has its own WALLY_PROFILE.
# The on-disk .claude/active_profile is ignored when env var is set.

alias claude-retail='WALLY_PROFILE=retail claude'
alias claude-ftmo='WALLY_PROFILE=ftmo claude'
alias claude-fot='WALLY_PROFILE=fotmarkets claude'
alias claude-fotmarkets='WALLY_PROFILE=fotmarkets claude'

# Quick profile check (no Claude needed):
alias wally-profile='bash /Users/josecampos/Documents/wally-trader/.claude/scripts/profile.sh show'
