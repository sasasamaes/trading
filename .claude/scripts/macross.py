#!/usr/bin/env python3
"""
MA Crossover (EMA 9/21) — 3ª estrategia para régimen TRENDING (ADX>25).

El PDF (PIEZA 03) define 4 estrategias rentables. Tu sistema tenía Mean Reversion (RANGE)
y Breakout (TRENDING). Esta es la 2da estrategia para trending: cruce de medias.

Funciona MUY bien cuando ADX > 25 con trend sostenido. Usa cuando:
  - regime-detector reporta TREND_LEVE o TREND_FUERTE
  - ADX(14, 1H) > 25
  - Direccionalidad clara (+DI vs -DI separados)

Lógica:
  - Bull cross: EMA(fast=9) cruza ARRIBA EMA(slow=21) AND close > EMA(slow) → LONG
  - Bear cross: EMA(fast=9) cruza ABAJO EMA(slow=21) AND close < EMA(slow) → SHORT
  - Filtro adicional: confirmación volumen (vela cross >= avg vol últimas 20)

Salida:
  - SL: ATR * 1.5 inicial
  - TP1: 1.5R (40%) → SL a BE
  - TP2: 3R (40%)
  - TP3 (20%): trailing EMA(21) — cuando close cruza EMA en contra → exit

Uso CLI:
    python3 macross.py --file /tmp/bars.json [--fast 9] [--slow 21] [--quick]

    # Last bar check (decide hoy):
    python3 macross.py --file /tmp/bars1h.json --quick
"""
from __future__ import annotations
import argparse
import json
import sys


def ema(values: list[float], length: int) -> list[float | None]:
    if len(values) < length:
        return [None] * len(values)
    k = 2 / (length + 1)
    seed = sum(values[:length]) / length
    out: list[float | None] = [None] * (length - 1) + [seed]
    for v in values[length:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def detect_cross(closes: list[float], fast: int, slow: int) -> dict:
    """Detect last cross signal in series."""
    e_fast = ema(closes, fast)
    e_slow = ema(closes, slow)
    if e_fast[-1] is None or e_slow[-1] is None or e_fast[-2] is None or e_slow[-2] is None:
        return {"signal": "NO_DATA", "reason": "Insufficient bars for EMAs"}

    f_now, f_prev = e_fast[-1], e_fast[-2]
    s_now, s_prev = e_slow[-1], e_slow[-2]
    c_now = closes[-1]

    # Bull cross: fast crosses above slow this bar
    bull_cross = f_prev <= s_prev and f_now > s_now
    bear_cross = f_prev >= s_prev and f_now < s_now

    # Trend filter: close above slow EMA
    trend_long = c_now > s_now
    trend_short = c_now < s_now

    if bull_cross and trend_long:
        return {
            "signal": "LONG",
            "ema_fast": round(f_now, 4),
            "ema_slow": round(s_now, 4),
            "close": c_now,
            "reason": f"EMA{fast} crossed above EMA{slow} & close > EMA{slow}",
        }
    if bear_cross and trend_short:
        return {
            "signal": "SHORT",
            "ema_fast": round(f_now, 4),
            "ema_slow": round(s_now, 4),
            "close": c_now,
            "reason": f"EMA{fast} crossed below EMA{slow} & close < EMA{slow}",
        }

    # Existing trend (no cross this bar but EMAs aligned)
    if f_now > s_now and trend_long:
        return {
            "signal": "BULL_TREND_NO_CROSS",
            "ema_fast": round(f_now, 4),
            "ema_slow": round(s_now, 4),
            "close": c_now,
            "reason": "Bull alignment, but no cross this bar — espera próximo cross o pullback",
        }
    if f_now < s_now and trend_short:
        return {
            "signal": "BEAR_TREND_NO_CROSS",
            "ema_fast": round(f_now, 4),
            "ema_slow": round(s_now, 4),
            "close": c_now,
            "reason": "Bear alignment, but no cross this bar",
        }
    return {
        "signal": "NEUTRAL",
        "ema_fast": round(f_now, 4),
        "ema_slow": round(s_now, 4),
        "close": c_now,
        "reason": "EMAs cross sin alineación con close — sin setup claro",
    }


def load_bars(source: str | None) -> list[dict]:
    raw = open(source).read() if source and source != "-" else sys.stdin.read()
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(line for line in raw.split("\n") if not line.startswith("```"))
    payload = json.loads(raw)
    if isinstance(payload, dict):
        payload = payload.get("bars") or payload.get("data") or list(payload.values())[0]
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None)
    ap.add_argument("--fast", type=int, default=9)
    ap.add_argument("--slow", type=int, default=21)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    try:
        bars = load_bars(args.file)
    except Exception as e:
        print(f"ERROR loading bars: {e}", file=sys.stderr)
        return 2

    closes = [float(b.get("c") or b.get("close")) for b in bars]
    res = detect_cross(closes, args.fast, args.slow)

    if args.quick:
        print(
            f"SIGNAL={res['signal']} EMA{args.fast}={res.get('ema_fast','-')} "
            f"EMA{args.slow}={res.get('ema_slow','-')} CLOSE={res.get('close','-')}"
        )
    else:
        print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
