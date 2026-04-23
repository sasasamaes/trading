"""
guardian.py — FTMO rules engine for Claude trading system.

Usage:
    python guardian.py --profile ftmo --action status
    python guardian.py --profile ftmo --action check-entry --asset BTCUSD \
                       --entry 77538 --sl 77238 --size 0.1
    python guardian.py --profile ftmo --action equity-update --value 10247
"""
import argparse
import csv
import json
import sys
from datetime import datetime, date
from pathlib import Path


def load_equity_curve(csv_path):
    """Load equity_curve.csv into list of dicts with parsed timestamps."""
    p = Path(csv_path)
    if not p.exists():
        return []
    rows = []
    with open(p, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "timestamp": datetime.fromisoformat(r["timestamp"]),
                "equity": float(r["equity"]),
                "source": r["source"],
                "note": r.get("note", ""),
            })
    rows.sort(key=lambda x: x["timestamp"])
    return rows


def peak_equity(curve):
    """Highest equity value in the curve. 0.0 if empty."""
    if not curve:
        return 0.0
    return max(r["equity"] for r in curve)


def daily_pnl(curve, target_date):
    """Equity delta for a specific calendar date.
    Returns 0.0 if no data or only one point on the date.
    """
    today_rows = [r for r in curve if r["timestamp"].date() == target_date]
    if len(today_rows) < 2:
        return 0.0
    # Sorted chronologically by load_equity_curve
    return today_rows[-1]["equity"] - today_rows[0]["equity"]


def trailing_dd(curve):
    """Drawdown from the peak equity. Positive value = in drawdown.
    0.0 if empty or at new peak.
    """
    if not curve:
        return 0.0
    peak = peak_equity(curve)
    last = curve[-1]["equity"]
    dd = peak - last
    return max(0.0, dd)


def main():
    # Stub — expanded in later tasks
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--action", required=True)
    args, _ = parser.parse_known_args()
    print(json.dumps({"profile": args.profile, "action": args.action, "stub": True}))


if __name__ == "__main__":
    main()
