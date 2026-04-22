"""Feature engineering para el modelo supervisado.

Features (todos replicables en tiempo real desde TradingView):
  - rsi_14              : RSI(14)
  - bb_pos              : posición dentro de BB(20,2), -1 (lower) a +1 (upper)
  - donchian_dist_low   : distancia % al Donchian Low(15)
  - donchian_dist_high  : distancia % al Donchian High(15)
  - vol_z_20            : z-score del volumen vs media 20 velas
  - atr_pct             : ATR(14) como % del precio
  - close_to_open_pct   : (close-open)/open de la vela actual
  - body_vs_range       : cuerpo/(high-low), indica fuerza de vela
  - hour_of_day_mx      : hora MX (0-23) — captura sesiones
  - day_of_week         : 0-6
  - momentum_3          : close - close hace 3 velas, normalizado
  - momentum_12         : close - close hace 12 velas, normalizado

Target:
  - tp_first_long   : 1 si TP(2.5×SL arriba) se alcanza antes que SL(1.5×ATR abajo) en próximas N velas
  - tp_first_short  : equivalente para short
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder's smoothing (EMA con alpha=1/length)
    avg_gain = gain.ewm(alpha=1/length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/length, adjust=False).mean()


def _bollinger(series: pd.Series, length: int = 20, k: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ma = series.rolling(length).mean()
    sd = series.rolling(length).std(ddof=0)
    upper = ma + k * sd
    lower = ma - k * sd
    return lower, ma, upper


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Toma un df OHLCV (de data_loader) y retorna df con features añadidas."""
    out = df.copy()

    # RSI
    out["rsi_14"] = _rsi(out["close"], 14)

    # Bollinger Bands (20,2) → posición normalizada
    lower, middle, upper = _bollinger(out["close"], 20, 2.0)
    band_width = (upper - lower).replace(0, np.nan)
    out["bb_pos"] = 2 * (out["close"] - middle) / band_width  # [-1, +1] en los bordes

    # Donchian 15
    don_high = out["high"].rolling(15).max()
    don_low = out["low"].rolling(15).min()
    out["donchian_dist_low"] = (out["close"] - don_low) / out["close"]
    out["donchian_dist_high"] = (don_high - out["close"]) / out["close"]

    # Volumen z-score vs 20 velas
    vol_ma = out["volume"].rolling(20).mean()
    vol_sd = out["volume"].rolling(20).std(ddof=0).replace(0, np.nan)
    out["vol_z_20"] = (out["volume"] - vol_ma) / vol_sd

    # ATR %
    out["atr_pct"] = _atr(out, 14) / out["close"]

    # Vela actual
    body = out["close"] - out["open"]
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    out["close_to_open_pct"] = body / out["open"]
    out["body_vs_range"] = body.abs() / rng

    # Hora/día (zona horaria MX — UTC-6)
    mx_time = out["open_time"].dt.tz_convert("America/Mexico_City")
    out["hour_of_day_mx"] = mx_time.dt.hour
    out["day_of_week"] = mx_time.dt.dayofweek

    # Momentum normalizado por ATR
    atr_abs = _atr(out, 14)
    out["momentum_3"] = (out["close"] - out["close"].shift(3)) / atr_abs
    out["momentum_12"] = (out["close"] - out["close"].shift(12)) / atr_abs

    return out


def build_targets(
    df: pd.DataFrame,
    lookahead_bars: int = 16,
    sl_atr_mult: float = 1.5,
    tp_sl_ratio: float = 2.5,
) -> pd.DataFrame:
    """Marca target TP-first (1) vs SL-first (0) en próximas `lookahead_bars` velas.

    LONG:
      - SL = close - sl_atr_mult * ATR
      - TP = close + tp_sl_ratio * (close - SL) = close + sl_atr_mult * ATR * tp_sl_ratio
      - tp_first_long = 1 si TP se toca ANTES que SL en la ventana

    SHORT: simétrico.

    Barra actual NO está en la ventana (lookahead empieza en t+1).
    Si ninguno toca dentro de la ventana → 0 (tratado como no-TP, conservador).
    """
    out = df.copy()
    atr_abs = _atr(out, 14)

    # Precios SL/TP por fila
    sl_offset = sl_atr_mult * atr_abs
    tp_offset = sl_atr_mult * atr_abs * tp_sl_ratio

    sl_long = out["close"] - sl_offset
    tp_long = out["close"] + tp_offset
    sl_short = out["close"] + sl_offset
    tp_short = out["close"] - tp_offset

    # Arrays para lookup
    highs = out["high"].values
    lows = out["low"].values
    n = len(out)

    tp_first_long = np.zeros(n, dtype=np.int8)
    tp_first_short = np.zeros(n, dtype=np.int8)

    sl_l = sl_long.values
    tp_l = tp_long.values
    sl_s = sl_short.values
    tp_s = tp_short.values

    for i in range(n - lookahead_bars):
        # Ventana: velas [i+1, i+lookahead_bars]
        win_h = highs[i+1:i+1+lookahead_bars]
        win_l = lows[i+1:i+1+lookahead_bars]

        # LONG
        tp_hit_idx_l = np.argmax(win_h >= tp_l[i]) if np.any(win_h >= tp_l[i]) else -1
        sl_hit_idx_l = np.argmax(win_l <= sl_l[i]) if np.any(win_l <= sl_l[i]) else -1
        if tp_hit_idx_l != -1 and (sl_hit_idx_l == -1 or tp_hit_idx_l < sl_hit_idx_l):
            tp_first_long[i] = 1

        # SHORT
        tp_hit_idx_s = np.argmax(win_l <= tp_s[i]) if np.any(win_l <= tp_s[i]) else -1
        sl_hit_idx_s = np.argmax(win_h >= sl_s[i]) if np.any(win_h >= sl_s[i]) else -1
        if tp_hit_idx_s != -1 and (sl_hit_idx_s == -1 or tp_hit_idx_s < sl_hit_idx_s):
            tp_first_short[i] = 1

    out["tp_first_long"] = tp_first_long
    out["tp_first_short"] = tp_first_short
    return out


FEATURE_COLS = [
    "rsi_14", "bb_pos",
    "donchian_dist_low", "donchian_dist_high",
    "vol_z_20", "atr_pct",
    "close_to_open_pct", "body_vs_range",
    "hour_of_day_mx", "day_of_week",
    "momentum_3", "momentum_12",
]


if __name__ == "__main__":
    # Smoke test
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
    from supervised.data_loader import cached_history

    df = cached_history(days=30, verbose=False)
    feats = compute_features(df)
    tgt = build_targets(feats)
    print(f"Features shape: {feats.shape}")
    print(f"Targets positive rate (long):  {tgt['tp_first_long'].mean():.3f}")
    print(f"Targets positive rate (short): {tgt['tp_first_short'].mean():.3f}")
    print(tgt[FEATURE_COLS + ["tp_first_long", "tp_first_short"]].tail(5))
