#!/usr/bin/env python3
"""Predice probabilidades TP-first (long/short) sobre estado de mercado actual.

Dos modos:

1. **Explícito** (sin API): pasas los features por CLI:
   python3 predict.py --rsi 32 --bb-pos -0.9 --donchian-dist-low 0.0008 \\
                       --donchian-dist-high 0.011 --vol-z 1.2 --atr-pct 0.0048 \\
                       --close-to-open 0.0003 --body-vs-range 0.7 \\
                       --hour-mx 9 --day 1 --mom3 0.4 --mom12 1.1

2. **Auto** (pide data actual a Binance): calcula features del último estado y predice:
   python3 predict.py --auto
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared.config import MODEL_PATH, METRICS_PATH, PRIMARY_TF, SYMBOL
from supervised.features import compute_features, FEATURE_COLS


def _load():
    import joblib
    if not MODEL_PATH.exists():
        print(f"ERROR: modelo no encontrado en {MODEL_PATH}")
        print(f"Ejecuta primero: python3 scripts/ml_system/supervised/train.py")
        sys.exit(2)
    return joblib.load(MODEL_PATH)


def _score_to_bucket(p: float) -> str:
    """Convierte probabilidad a score interpretable 0-100 con bucket."""
    score = round(p * 100)
    if score < 35:
        label = "🔴 BAJO — setup poco favorable según histórico"
    elif score < 50:
        label = "🟠 MEDIO-BAJO — reducir size 50% o pasar"
    elif score < 60:
        label = "🟡 NEUTRAL — el modelo no tiene opinión fuerte"
    elif score < 70:
        label = "🟢 MEDIO-ALTO — favorable"
    else:
        label = "🟢 ALTO — setup con alta probabilidad según modelo"
    return f"{score}/100 ({label})"


def predict_from_features(feats: dict) -> dict:
    artifact = _load()
    model_long = artifact["long"]
    model_short = artifact["short"]

    x = np.array([[feats[c] for c in FEATURE_COLS]], dtype=float)
    p_long = float(model_long.predict_proba(x)[0, 1])
    p_short = float(model_short.predict_proba(x)[0, 1])

    result = {
        "features": feats,
        "probability_long_tp_first": p_long,
        "probability_short_tp_first": p_short,
        "long_score": _score_to_bucket(p_long),
        "short_score": _score_to_bucket(p_short),
        "recommendation": _recommend(p_long, p_short),
    }
    return result


def _recommend(p_long: float, p_short: float) -> str:
    if p_long > 0.60 and p_short < 0.40:
        return "BIAS LONG — si setup técnico 4/4 LONG aparece, tiene edge."
    if p_short > 0.60 and p_long < 0.40:
        return "BIAS SHORT — si setup técnico 4/4 SHORT aparece, tiene edge."
    if p_long < 0.40 and p_short < 0.40:
        return "EVITAR ambos lados — condiciones actuales poco favorables para mean reversion."
    if p_long > 0.50 and p_short > 0.50:
        return "VOLATIL — modelo predice que cualquier lado puede ganar; operar con size reducido."
    return "NEUTRAL — seguir técnico puro, el modelo no aporta edge adicional."


def auto_features() -> dict:
    """Descarga últimas ~30 velas 15m y calcula features del cierre más reciente."""
    from supervised.data_loader import fetch_klines

    df = fetch_klines(SYMBOL, PRIMARY_TF, limit=200)
    if df.empty:
        raise RuntimeError("No data de Binance")

    df = compute_features(df)
    df = df.dropna(subset=FEATURE_COLS)
    if df.empty:
        raise RuntimeError("Features insuficientes (no data para rolling windows)")

    last = df.iloc[-1]
    return {c: float(last[c]) for c in FEATURE_COLS}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Descarga data actual y calcula features")
    parser.add_argument("--json", action="store_true")

    # Features manuales
    parser.add_argument("--rsi", type=float)
    parser.add_argument("--bb-pos", type=float, dest="bb_pos")
    parser.add_argument("--donchian-dist-low", type=float, dest="donchian_dist_low")
    parser.add_argument("--donchian-dist-high", type=float, dest="donchian_dist_high")
    parser.add_argument("--vol-z", type=float, dest="vol_z_20")
    parser.add_argument("--atr-pct", type=float, dest="atr_pct")
    parser.add_argument("--close-to-open", type=float, dest="close_to_open_pct")
    parser.add_argument("--body-vs-range", type=float, dest="body_vs_range")
    parser.add_argument("--hour-mx", type=int, dest="hour_of_day_mx")
    parser.add_argument("--day", type=int, dest="day_of_week")
    parser.add_argument("--mom3", type=float, dest="momentum_3")
    parser.add_argument("--mom12", type=float, dest="momentum_12")

    args = parser.parse_args()

    if args.auto:
        feats = auto_features()
        print(f"[auto] Features del último cierre {SYMBOL} {PRIMARY_TF}:")
        for c in FEATURE_COLS:
            print(f"  {c:<22} {feats[c]:+.4f}")
        print()
    else:
        feats = {}
        for c in FEATURE_COLS:
            val = getattr(args, c.replace("-", "_"), None)
            if val is None:
                parser.error(f"falta --{c.replace('_', '-')} (o usa --auto)")
            feats[c] = float(val)

    result = predict_from_features(feats)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("════════════════════════════════════════════════════")
        print(" 🤖 ML SETUP SCORE")
        print("════════════════════════════════════════════════════")
        print(f" LONG  → {result['long_score']}")
        print(f" SHORT → {result['short_score']}")
        print()
        print(f" 📍 {result['recommendation']}")
        print("════════════════════════════════════════════════════")

        # Si existe métricas del training, mostrar AUC de referencia
        if METRICS_PATH.exists():
            with open(METRICS_PATH) as f:
                m = json.load(f)
            print(f" [Training AUC: long={m['long']['auc']:.2f}, short={m['short']['auc']:.2f}]")


if __name__ == "__main__":
    main()
