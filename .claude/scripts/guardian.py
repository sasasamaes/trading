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


def main():
    # Stub — expanded in later tasks
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--action", required=True)
    args, _ = parser.parse_known_args()
    print(json.dumps({"profile": args.profile, "action": args.action, "stub": True}))


if __name__ == "__main__":
    main()
