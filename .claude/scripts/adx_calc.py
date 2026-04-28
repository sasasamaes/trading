#!/usr/bin/env python3
"""
ADX(14) + Directional Movement (+DI / -DI) calculator.

Usage:
    # Pipe OHLCV JSON via stdin:
    cat /tmp/bars.json | python3 .claude/scripts/adx_calc.py

    # Or pass file:
    python3 .claude/scripts/adx_calc.py --file /tmp/bars.json [--length 14]

    # Or quick mode for regime-detector (Bash-friendly):
    python3 .claude/scripts/adx_calc.py --file /tmp/bars.json --quick

Input JSON: list of bars with keys h/high, l/low, c/close (also accepts {bars:[...]} wrapper).

Output (--quick): single line `ADX=<v> +DI=<v> -DI=<v> REGIME=<X>`
Output default: JSON with adx, plus_di, minus_di, last_adx, regime_label, last_close.
"""
from __future__ import annotations
import argparse
import json
import sys
from typing import Iterable


def _wilder_smooth(values: list[float], length: int) -> list[float]:
    """Wilder's RMA smoothing (used in ADX)."""
    if len(values) < length:
        return []
    out = [sum(values[:length])]
    for v in values[length:]:
        out.append(out[-1] - (out[-1] / length) + v)
    return out


def adx(bars: list[dict], length: int = 14) -> dict:
    """
    Compute ADX, +DI, -DI series from OHLCV bars (Wilder method).
    Returns dict with arrays and last values.
    """
    n = len(bars)
    if n < length * 2 + 1:
        return {"error": f"need at least {length*2+1} bars, got {n}"}

    highs = [float(b.get("h") or b.get("high")) for b in bars]
    lows = [float(b.get("l") or b.get("low")) for b in bars]
    closes = [float(b.get("c") or b.get("close")) for b in bars]

    plus_dm: list[float] = []
    minus_dm: list[float] = []
    tr: list[float] = []
    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)
        tr_v = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        tr.append(tr_v)

    sm_tr = _wilder_smooth(tr, length)
    sm_plus = _wilder_smooth(plus_dm, length)
    sm_minus = _wilder_smooth(minus_dm, length)
    if not sm_tr or not sm_plus or not sm_minus:
        return {"error": "smoothing failed (insufficient data)"}

    plus_di = [100 * (p / t) if t > 0 else 0.0 for p, t in zip(sm_plus, sm_tr)]
    minus_di = [100 * (m / t) if t > 0 else 0.0 for m, t in zip(sm_minus, sm_tr)]
    dx = [
        100 * abs(p - m) / (p + m) if (p + m) > 0 else 0.0
        for p, m in zip(plus_di, minus_di)
    ]
    if len(dx) < length:
        return {"error": f"DX series too short ({len(dx)}<{length})"}

    adx_series: list[float] = [sum(dx[:length]) / length]
    for v in dx[length:]:
        adx_series.append((adx_series[-1] * (length - 1) + v) / length)

    return {
        "adx": adx_series,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "last_adx": round(adx_series[-1], 2),
        "last_plus_di": round(plus_di[-1], 2),
        "last_minus_di": round(minus_di[-1], 2),
        "last_close": closes[-1],
        "bars_used": n,
        "length": length,
    }


def label_regime(adx_val: float, plus_di: float, minus_di: float) -> tuple[str, str]:
    """Map ADX value + DI direction → (regime_label, strategy_recommendation)."""
    direction = "LONG_BIAS" if plus_di > minus_di else "SHORT_BIAS"
    diff = abs(plus_di - minus_di)
    if diff < 2:
        direction = "NEUTRAL"

    if adx_val < 20:
        return "RANGE_CHOP", "Mean Reversion (o NO OPERAR si <15)"
    if adx_val < 25:
        return "TRANSITION", "Cautela: rango terminando o trend incipiente"
    if adx_val < 30:
        return f"TREND_LEVE_{direction}", "Pullback trades en dirección del trend"
    if adx_val < 40:
        return f"TREND_FUERTE_{direction}", "Breakout/Momentum, evitar reversiones"
    return f"TREND_EXTREMO_{direction}", "NO scalping reversal — solo runners trend"


def load_bars(source: str | None) -> list[dict]:
    if source and source != "-":
        with open(source) as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(line for line in raw.split("\n") if not line.startswith("```"))
    payload = json.loads(raw)
    if isinstance(payload, dict):
        payload = payload.get("bars") or payload.get("data") or list(payload.values())[0]
    if not isinstance(payload, list):
        raise ValueError("Expected list of bar dicts")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None, help="JSON file with bars (default: stdin)")
    ap.add_argument("--length", type=int, default=14)
    ap.add_argument("--quick", action="store_true", help="Single-line output for shell")
    args = ap.parse_args()

    try:
        bars = load_bars(args.file)
    except Exception as e:
        print(f"ERROR loading bars: {e}", file=sys.stderr)
        return 2

    res = adx(bars, args.length)
    if "error" in res:
        print(f"ERROR: {res['error']}", file=sys.stderr)
        return 3

    regime, strat = label_regime(res["last_adx"], res["last_plus_di"], res["last_minus_di"])
    if args.quick:
        print(
            f"ADX={res['last_adx']} +DI={res['last_plus_di']} "
            f"-DI={res['last_minus_di']} REGIME={regime} BARS={res['bars_used']}"
        )
    else:
        print(json.dumps({
            "last_adx": res["last_adx"],
            "last_plus_di": res["last_plus_di"],
            "last_minus_di": res["last_minus_di"],
            "regime": regime,
            "strategy_hint": strat,
            "bars_used": res["bars_used"],
            "length": args.length,
        }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
