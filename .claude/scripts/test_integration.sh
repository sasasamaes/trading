#!/usr/bin/env bash
# End-to-end integration test for dual-profile system.
# Run from repo root: bash .claude/scripts/test_integration.sh

set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== TEST 1: profile.sh show/get/set ==="
bash .claude/scripts/profile.sh set retail
test "$(bash .claude/scripts/profile.sh get)" = "retail" && echo "  ✓ retail set"

bash .claude/scripts/profile.sh set ftmo
test "$(bash .claude/scripts/profile.sh get)" = "ftmo" && echo "  ✓ ftmo set"

echo ""
echo "=== TEST 2: statusline under retail ==="
bash .claude/scripts/profile.sh set retail
OUT=$(bash .claude/scripts/statusline.sh)
echo "  output: $OUT"
echo "$OUT" | grep -q "RETAIL" && echo "  ✓ retail statusline" || { echo "  ✗ retail missing"; exit 1; }

echo ""
echo "=== TEST 3: statusline under ftmo ==="
bash .claude/scripts/profile.sh set ftmo
OUT=$(bash .claude/scripts/statusline.sh)
echo "  output: $OUT"
echo "$OUT" | grep -q "FTMO" && echo "  ✓ ftmo statusline" || { echo "  ✗ ftmo missing"; exit 1; }

echo ""
echo "=== TEST 4: guardian status ==="
python3 .claude/scripts/guardian.py --profile ftmo --action status > /tmp/guardian_status.json
python3 -c "import json; d=json.load(open('/tmp/guardian_status.json')); assert d['profile']=='ftmo'; assert d['equity_current']==10000; print('  ✓ guardian status OK')"

echo ""
echo "=== TEST 5: guardian equity-update + re-read ==="
python3 .claude/scripts/guardian.py --profile ftmo --action equity-update --value 10150 --note "integration test"
python3 .claude/scripts/guardian.py --profile ftmo --action status > /tmp/guardian_after.json
AFTER=$(python3 -c "import json; d=json.load(open('/tmp/guardian_after.json')); print(d['equity_current'])")
test "$AFTER" = "10150.0" && echo "  ✓ equity updated to $AFTER" || { echo "  ✗ expected 10150.0, got $AFTER"; exit 1; }

# Cleanup test curve row
python3 -c "
import csv
from pathlib import Path
p = Path('.claude/profiles/ftmo/memory/equity_curve.csv')
rows = list(csv.reader(open(p)))
# Keep header + drop test row (last)
filtered = [rows[0]] + [r for r in rows[1:] if 'integration test' not in ' '.join(r)]
with open(p, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerows(filtered)
"

echo ""
echo "=== TEST 6: guardian check-entry OK on fresh profile ==="
RESULT=$(python3 .claude/scripts/guardian.py --profile ftmo --action check-entry \
  --asset BTCUSD --entry 77538 --sl 77238 --loss-if-sl 50)
echo "$RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); assert d['verdict']=='OK'; print('  ✓ OK verdict')"

echo ""
echo "=== TEST 7: memory structure integrity ==="
test -d .claude/profiles/retail/memory && echo "  ✓ retail memory dir"
test -d .claude/profiles/ftmo/memory && echo "  ✓ ftmo memory dir"
test -f .claude/profiles/retail/memory/trading_log.md && echo "  ✓ retail trading_log migrated"
test -f .claude/memory/user_profile.md && echo "  ✓ global user_profile kept"
test ! -f .claude/memory/trading_log.md && echo "  ✓ retail log NOT in global" || { echo "  ✗ trading_log still in global"; exit 1; }

echo ""
echo "=== TEST 8: reset to retail ==="
bash .claude/scripts/profile.sh set retail
test "$(bash .claude/scripts/profile.sh get)" = "retail" && echo "  ✓ back to retail"

echo ""
echo "╔═══════════════════════════════════╗"
echo "║  ALL INTEGRATION TESTS PASSED  ✓  ║"
echo "╚═══════════════════════════════════╝"
