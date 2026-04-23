# Unit tests for guardian.py — run with: pytest .claude/scripts/test_guardian.py -v
import sys
import tempfile
import pathlib
from datetime import datetime, date

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import guardian


def _write_curve(rows):
    """Helper: write rows to a temp CSV, return path."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    tmp.write("timestamp,equity,source,note\n")
    for r in rows:
        tmp.write(",".join(str(x) for x in r) + "\n")
    tmp.close()
    return tmp.name


def test_load_empty_curve():
    path = _write_curve([])
    curve = guardian.load_equity_curve(path)
    assert curve == []


def test_load_single_row():
    path = _write_curve([
        ("2026-04-23T06:00:00", 10000.0, "manual", "initial"),
    ])
    curve = guardian.load_equity_curve(path)
    assert len(curve) == 1
    assert curve[0]["equity"] == 10000.0
    assert curve[0]["source"] == "manual"
    assert isinstance(curve[0]["timestamp"], datetime)


def test_peak_equity_empty():
    assert guardian.peak_equity([]) == 0.0


def test_peak_equity_single():
    curve = [{"timestamp": datetime(2026,4,23,6,0), "equity": 10000.0, "source": "m", "note": ""}]
    assert guardian.peak_equity(curve) == 10000.0


def test_peak_equity_multiple():
    curve = [
        {"timestamp": datetime(2026,4,23,6,0), "equity": 10000.0, "source": "m", "note": ""},
        {"timestamp": datetime(2026,4,23,9,0), "equity": 10200.0, "source": "m", "note": ""},
        {"timestamp": datetime(2026,4,23,12,0), "equity": 10150.0, "source": "m", "note": ""},
    ]
    assert guardian.peak_equity(curve) == 10200.0


def test_daily_pnl_no_data():
    assert guardian.daily_pnl([], date(2026,4,23)) == 0.0


def test_daily_pnl_single_point_no_baseline():
    curve = [{"timestamp": datetime(2026,4,23,9,0), "equity": 10180.0, "source": "m", "note": ""}]
    # Only one point today — can't compute intraday P&L
    assert guardian.daily_pnl(curve, date(2026,4,23)) == 0.0


def test_daily_pnl_positive():
    curve = [
        {"timestamp": datetime(2026,4,23,6,0), "equity": 10000.0, "source": "m", "note": ""},
        {"timestamp": datetime(2026,4,23,9,0), "equity": 10180.0, "source": "m", "note": ""},
    ]
    assert guardian.daily_pnl(curve, date(2026,4,23)) == 180.0


def test_daily_pnl_negative():
    curve = [
        {"timestamp": datetime(2026,4,23,6,0), "equity": 10000.0, "source": "m", "note": ""},
        {"timestamp": datetime(2026,4,23,14,0), "equity": 9780.0, "source": "m", "note": ""},
    ]
    assert guardian.daily_pnl(curve, date(2026,4,23)) == -220.0


def test_trailing_dd_no_peak():
    curve = [{"timestamp": datetime(2026,4,23,6,0), "equity": 10000.0, "source": "m", "note": ""}]
    assert guardian.trailing_dd(curve) == 0.0


def test_trailing_dd_in_drawdown():
    curve = [
        {"timestamp": datetime(2026,4,23,6,0), "equity": 10000.0, "source": "m", "note": ""},
        {"timestamp": datetime(2026,4,24,10,0), "equity": 10400.0, "source": "m", "note": ""},
        {"timestamp": datetime(2026,4,25,9,0), "equity": 10250.0, "source": "m", "note": ""},
    ]
    # Peak 10400, current 10250, dd = 150
    assert guardian.trailing_dd(curve) == 150.0


def test_trailing_dd_at_new_peak():
    curve = [
        {"timestamp": datetime(2026,4,23,6,0), "equity": 10000.0, "source": "m", "note": ""},
        {"timestamp": datetime(2026,4,24,10,0), "equity": 10400.0, "source": "m", "note": ""},
    ]
    assert guardian.trailing_dd(curve) == 0.0
