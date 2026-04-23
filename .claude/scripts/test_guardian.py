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
