#!/usr/bin/env python3
"""Entrena dos clasificadores XGBoost: uno para LONG, otro para SHORT.

Output: modelos calibrados guardados en `supervised/model/`.

Uso:
  python3 train.py                        # 365 días, TF 15m, default params
  python3 train.py --days 730             # 2 años
  python3 train.py --interval 1h          # otro TF
  python3 train.py --refresh              # ignora cache, redescarga data
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Path setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.config import MODEL_DIR, MODEL_PATH, FEATURES_PATH, METRICS_PATH, PRIMARY_TF, SYMBOL
from supervised.data_loader import cached_history
from supervised.features import compute_features, build_targets, FEATURE_COLS


def _split_time(df: pd.DataFrame, train_frac: float = 0.8):
    """Split temporal (NO aleatorio — evita leakage)."""
    n = len(df)
    cut = int(n * train_frac)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def _train_one(X_train, y_train, X_test, y_test, label: str):
    import xgboost as xgb
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import roc_auc_score, log_loss, classification_report, brier_score_loss

    print(f"\n── Training {label} ──────────────────────────")
    print(f"   train n={len(X_train)}, positives={int(y_train.sum())} ({y_train.mean():.2%})")
    print(f"   test  n={len(X_test)},  positives={int(y_test.sum())} ({y_test.mean():.2%})")

    base = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        tree_method="hist",
        eval_metric="logloss",
        n_jobs=-1,
        random_state=42,
    )
    base.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Calibración (importante para que el score ML sea interpretable como probabilidad)
    # Prefit para no re-entrenar sobre el mismo data
    calib = CalibratedClassifierCV(base, method="sigmoid", cv="prefit")
    calib.fit(X_test, y_test)  # calibra usando el test set, sacrificando un poco para confiabilidad

    # Métricas sobre test
    proba = base.predict_proba(X_test)[:, 1]
    proba_cal = calib.predict_proba(X_test)[:, 1]

    metrics = {
        "label": label,
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "positive_rate_train": float(y_train.mean()),
        "positive_rate_test": float(y_test.mean()),
        "auc": float(roc_auc_score(y_test, proba)),
        "logloss": float(log_loss(y_test, np.clip(proba, 1e-6, 1-1e-6))),
        "brier": float(brier_score_loss(y_test, proba_cal)),
        "brier_uncalibrated": float(brier_score_loss(y_test, proba)),
    }
    print(f"   AUC: {metrics['auc']:.3f}   LogLoss: {metrics['logloss']:.4f}   Brier(cal): {metrics['brier']:.4f}")

    # Feature importance
    fi_raw = base.feature_importances_
    fi_pairs = sorted(zip(FEATURE_COLS, fi_raw), key=lambda x: -x[1])[:8]
    print("   Top features:")
    for name, imp in fi_pairs:
        print(f"     {name:<20} {imp:.3f}")

    return calib, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default=SYMBOL)
    parser.add_argument("--interval", default=PRIMARY_TF)
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--lookahead", type=int, default=16, help="Barras hacia adelante para el target")
    args = parser.parse_args()

    print(f"=== XGBoost Training — {args.symbol} {args.interval} ({args.days}d) ===")

    # 1. Data
    df = cached_history(args.symbol, args.interval, days=args.days, refresh=args.refresh)
    if df.empty:
        print("ERROR: sin data")
        sys.exit(1)
    print(f"Data: {len(df)} velas desde {df['open_time'].min()} hasta {df['open_time'].max()}")

    # 2. Features + targets
    df = compute_features(df)
    df = build_targets(df, lookahead_bars=args.lookahead)
    df = df.dropna(subset=FEATURE_COLS).reset_index(drop=True)
    print(f"Después de dropna: {len(df)} filas utilizables")

    # 3. Train/test split temporal
    train_df, test_df = _split_time(df, 0.8)

    X_train = train_df[FEATURE_COLS].values
    X_test = test_df[FEATURE_COLS].values

    y_train_l = train_df["tp_first_long"].values
    y_test_l = test_df["tp_first_long"].values
    y_train_s = train_df["tp_first_short"].values
    y_test_s = test_df["tp_first_short"].values

    # 4. Entrenar los dos modelos
    model_long, metrics_long = _train_one(X_train, y_train_l, X_test, y_test_l, "LONG")
    model_short, metrics_short = _train_one(X_train, y_train_s, X_test, y_test_s, "SHORT")

    # 5. Persistir
    import joblib

    artifact = {
        "long": model_long,
        "short": model_short,
        "feature_cols": FEATURE_COLS,
        "params": vars(args),
    }
    joblib.dump(artifact, MODEL_PATH)
    with open(FEATURES_PATH, "w") as f:
        json.dump(FEATURE_COLS, f, indent=2)
    with open(METRICS_PATH, "w") as f:
        json.dump({"long": metrics_long, "short": metrics_short, "params": vars(args)}, f, indent=2)

    print(f"\n✓ Modelo guardado: {MODEL_PATH}")
    print(f"✓ Métricas:        {METRICS_PATH}")

    # Reality check
    print("\n── Reality check ──")
    for m in [metrics_long, metrics_short]:
        auc = m["auc"]
        if auc < 0.52:
            verdict = "⚠️  AUC <0.52 → modelo apenas mejor que azar, no confiar"
        elif auc < 0.58:
            verdict = "🟡 AUC modesto — usar como señal auxiliar, peso bajo"
        elif auc < 0.65:
            verdict = "🟢 AUC razonable — útil como 5° filtro"
        else:
            verdict = "⚠️  AUC >0.65 sospechoso de overfitting o leakage — validar walk-forward"
        print(f"   {m['label']:<6} AUC={auc:.3f}  → {verdict}")


if __name__ == "__main__":
    main()
