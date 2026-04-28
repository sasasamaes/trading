#!/usr/bin/env python3
"""
EMA-based trailing stop helper (modo de salida #4 según el PDF).

Filosofía:
  - SL inicial fijo (1.5×ATR retail / 0.4% FTMO / ATR×1.2 fotmarkets)
  - TP1 cierra parcial → SL a BE
  - TP2 cierra parcial → opcional
  - El runner (TP3 / 20-30%) NO usa target fijo, en su lugar trail con EMA(20)
  - Si precio TOCA la EMA(20) → exit el runner

Uso:
  python3 .claude/scripts/trailing_stop.py --file /tmp/bars.json \\
      --side long --entry 96000 --current 97500 [--ema 20] [--threshold 0.001]

Input bars: JSON list, keys h/l/c (también acepta {bars:[...]}).
Output: JSON con ema_value, trail_level, distance_pct, action (HOLD|EXIT_TRAIL|INVALID).
"""
from __future__ import annotations
import argparse
import json
import sys


def ema(values: list[float], length: int) -> list[float]:
    """Estándar EMA (no-Wilder)."""
    if len(values) < length:
        return []
    k = 2 / (length + 1)
    seed = sum(values[:length]) / length
    out = [seed]
    for v in values[length:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


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


def evaluate(
    bars: list[dict],
    side: str,
    entry: float,
    current: float,
    ema_length: int = 20,
    touch_threshold: float = 0.001,
) -> dict:
    """
    Returns dict with:
      ema_value      → último EMA(ema_length)
      trail_level    → mismo valor (el trail ES la EMA)
      distance_pct   → distancia % entre current y EMA
      ema_slope      → up/down/flat (last 3 EMA values)
      action         → HOLD | EXIT_TRAIL | INVALID
      reason         → texto explicando la action
    """
    side = side.lower()
    if side not in ("long", "short"):
        return {"error": f"side debe ser long|short, got {side}"}
    if len(bars) < ema_length + 5:
        return {"error": f"need >= {ema_length+5} bars for EMA({ema_length}), got {len(bars)}"}

    closes = [float(b.get("c") or b.get("close")) for b in bars]
    ema_series = ema(closes, ema_length)
    if not ema_series:
        return {"error": "EMA computation failed"}

    e = ema_series[-1]
    if len(ema_series) >= 3:
        slope_diff = ema_series[-1] - ema_series[-3]
        slope = "up" if slope_diff > 0 else ("down" if slope_diff < 0 else "flat")
    else:
        slope = "flat"

    distance_pct = (current - e) / e * 100

    # LONG: el trail está DEBAJO del precio. Salir si current <= EMA (toca o cruza)
    # SHORT: el trail está ARRIBA del precio. Salir si current >= EMA
    if side == "long":
        # Validar que el trail tiene sentido: EMA debajo del entry para LONG en profit
        in_profit = current > entry
        touched = current <= e * (1 + touch_threshold)
        if not in_profit:
            action, reason = "INVALID", "No usar trailing antes de TP1 (precio bajo entry)"
        elif touched:
            action, reason = "EXIT_TRAIL", f"Precio {current:.4f} tocó EMA{ema_length} {e:.4f}"
        elif slope == "down":
            action, reason = "HOLD_WARN", f"EMA{ema_length} bajando — trail acercándose"
        else:
            action, reason = "HOLD", f"Precio {distance_pct:.2f}% arriba de EMA{ema_length}"
    else:  # short
        in_profit = current < entry
        touched = current >= e * (1 - touch_threshold)
        if not in_profit:
            action, reason = "INVALID", "No usar trailing antes de TP1 (precio sobre entry)"
        elif touched:
            action, reason = "EXIT_TRAIL", f"Precio {current:.4f} tocó EMA{ema_length} {e:.4f}"
        elif slope == "up":
            action, reason = "HOLD_WARN", f"EMA{ema_length} subiendo — trail acercándose"
        else:
            action, reason = "HOLD", f"Precio {abs(distance_pct):.2f}% debajo de EMA{ema_length}"

    return {
        "side": side,
        "entry": entry,
        "current": current,
        "ema_length": ema_length,
        "ema_value": round(e, 4),
        "trail_level": round(e, 4),
        "distance_pct": round(distance_pct, 4),
        "ema_slope": slope,
        "action": action,
        "reason": reason,
        "in_profit_pct": round((current - entry) / entry * 100 * (1 if side == "long" else -1), 4),
        "bars_used": len(bars),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None, help="JSON file with bars (default: stdin)")
    ap.add_argument("--side", required=True, choices=["long", "short"])
    ap.add_argument("--entry", type=float, required=True, help="Entry price")
    ap.add_argument("--current", type=float, required=True, help="Current price")
    ap.add_argument("--ema", type=int, default=20, help="EMA length (default 20)")
    ap.add_argument("--threshold", type=float, default=0.001,
                    help="Touch threshold (0.001 = 0.1%%) for EXIT_TRAIL trigger")
    ap.add_argument("--quick", action="store_true", help="One-line shell output")
    args = ap.parse_args()

    try:
        bars = load_bars(args.file)
    except Exception as e:
        print(f"ERROR loading bars: {e}", file=sys.stderr)
        return 2

    res = evaluate(
        bars, args.side, args.entry, args.current,
        ema_length=args.ema, touch_threshold=args.threshold,
    )
    if "error" in res:
        print(f"ERROR: {res['error']}", file=sys.stderr)
        return 3

    if args.quick:
        print(
            f"TRAIL={res['trail_level']} EMA{res['ema_length']}={res['ema_value']} "
            f"DIST={res['distance_pct']}% SLOPE={res['ema_slope']} ACTION={res['action']}"
        )
    else:
        print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
