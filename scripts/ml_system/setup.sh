#!/bin/bash
# Setup ML System dependencies
# Requiere Python 3.9+ y pip

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== ML System setup ==="
echo "Python: $(python3 --version)"
echo

echo "Instalando dependencias (sin Deep Learning — scaffold only)..."
python3 -m pip install --user -r "$SCRIPT_DIR/requirements.txt"

echo
echo "=== Verificación ==="
python3 -c "
import sys
missing = []
for mod in ['requests', 'feedparser', 'vaderSentiment', 'pandas', 'numpy', 'xgboost', 'sklearn', 'joblib']:
    try:
        __import__(mod.replace('-', '_'))
        print(f'  [OK] {mod}')
    except ImportError:
        missing.append(mod)
        print(f'  [FAIL] {mod}')
if missing:
    print()
    print('Falta instalar:', missing)
    sys.exit(1)
"

echo
echo "Setup completo. Siguiente paso:"
echo "  python3 scripts/ml_system/sentiment/aggregator.py"
echo "  python3 scripts/ml_system/supervised/train.py    # entrena modelo (descarga data Binance)"
