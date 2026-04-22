"""Configuración compartida — paths, constantes, símbolos."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "supervised" / "model"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Símbolo y timeframes activos
SYMBOL = "BTCUSDT"
PRIMARY_TF = "15m"

# Binance klines API (sin key, datos públicos)
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"

# Model artifacts
MODEL_PATH = MODEL_DIR / "xgb_setup_score.pkl"
FEATURES_PATH = MODEL_DIR / "feature_names.json"
METRICS_PATH = MODEL_DIR / "metrics.json"
