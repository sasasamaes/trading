#!/bin/bash
# setup_venv.sh — Crea .claude/scripts/.venv con dependencias opcionales (yfinance, etc.)
# Uso: bash .claude/scripts/setup_venv.sh
#
# Las deps son OPCIONALES — los helpers funcionan sin ellas, pero per_asset_backtest.py
# necesita yfinance para forex/indices. Crypto sigue funcionando sin nada extra (urllib).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQ_FILE="$SCRIPT_DIR/requirements-helpers.txt"

# Find Python (prefer 3.11+)
PY_BIN=""
for cand in python3.13 python3.12 python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
        PY_BIN=$(command -v "$cand")
        break
    fi
done

if [[ -z "$PY_BIN" ]]; then
    echo "ERROR: no Python 3 found. Instala Python 3.11+ primero (brew install python@3.13)"
    exit 1
fi

echo "Usando $PY_BIN"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creando venv en $VENV_DIR..."
    "$PY_BIN" -m venv "$VENV_DIR"
fi

echo "Instalando deps de $REQ_FILE..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$REQ_FILE"

echo ""
echo "✅ Venv listo en $VENV_DIR"
"$VENV_DIR/bin/python" -c "import yfinance; print(f'  yfinance {yfinance.__version__}')"
echo ""
echo "Los helpers detectarán este venv automáticamente. No hace falta activar nada."
