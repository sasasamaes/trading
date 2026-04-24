"""Integration-ish tests for watcher_tick — price feed + notify mocked."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from pending_lib import PROFILES, append_pending
from watcher_tick import run_tick, TickResult


def _iso_now_plus(hours):
    dt = datetime.now(timezone.utc) + timedelta(hours=hours)
    return dt.astimezone().isoformat(timespec="seconds")


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    for profile in PROFILES:
        memdir = tmp_path / ".claude" / "profiles" / profile / "memory"
        memdir.mkdir(parents=True, exist_ok=True)
        (memdir / "pending_orders.json").write_text(
            json.dumps({"pending": [], "meta": {}})
        )
    # whitelist matrix (copy from repo)
    # Fix: Path(__file__).parent.parent.parent.parent gives us repo root
    # (.claude/scripts/tests → .claude/scripts → .claude → wally-trader)
    watcher_dir = tmp_path / ".claude" / "watcher"
    watcher_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    repo_root = Path(__file__).parent.parent.parent.parent
    src_matrix = repo_root / ".claude" / "watcher" / "whitelist_matrix.yaml"
    shutil.copy(src_matrix, watcher_dir / "whitelist_matrix.yaml")
    # trading_log stubs (empty)
    for profile in PROFILES:
        log = tmp_path / ".claude" / "profiles" / profile / "memory" / "trading_log.md"
        log.write_text("# empty log\n")
    monkeypatch.setenv("WALLY_REPO_ROOT", str(tmp_path))
    return tmp_path


def test_tick_no_pendings_is_ok(tmp_repo):
    with patch("watcher_tick.price_for") as mock_price, \
         patch("watcher_tick.notify") as mock_notify:
        result = run_tick()
    assert result.ok
    assert result.pendings_checked == 0


def test_tick_invalidates_expired_ttl(tmp_repo):
    order = {
        "id": "ord_e",
        "profile": "retail",
        "asset": "BTCUSDT.P",
        "side": "LONG",
        "status": "pending",
        "entry": 77521,
        "expires_at": _iso_now_plus(-1),
        "force_exit_mx": _iso_now_plus(5),
        "invalidation_price": 0,
        "invalidation_side": "below",
        "created_at": _iso_now_plus(-6),
    }
    append_pending("retail", order)
    with patch("watcher_tick.price_for", return_value=77500.0), \
         patch("watcher_tick.notify") as mock_notify:
        result = run_tick()
    assert result.ok
    from pending_lib import load_pendings
    pendings = load_pendings("retail")
    assert pendings[0]["status"] == "expired_ttl"
    mock_notify.assert_called()


def test_tick_escalates_near_entry(tmp_repo):
    order = {
        "id": "ord_near",
        "profile": "retail",
        "asset": "BTCUSDT.P",
        "side": "LONG",
        "status": "pending",
        "entry": 77521,
        "expires_at": _iso_now_plus(5),
        "force_exit_mx": _iso_now_plus(5),
        "invalidation_price": 76000,
        "invalidation_side": "below",
        "created_at": _iso_now_plus(-1),
    }
    append_pending("retail", order)
    with patch("watcher_tick.price_for", return_value=77540.0), \
         patch("watcher_tick.notify") as mock_notify, \
         patch("watcher_tick.spawn_escalate") as mock_escalate:
        result = run_tick()
    assert result.ok
    mock_escalate.assert_called_once_with("ord_near")
    from pending_lib import load_pendings
    assert load_pendings("retail")[0]["status"] == "triggered_validating"


def test_tick_heartbeat_when_far(tmp_repo):
    order = {
        "id": "ord_far",
        "profile": "retail",
        "asset": "BTCUSDT.P",
        "side": "LONG",
        "status": "pending",
        "entry": 77521,
        "expires_at": _iso_now_plus(5),
        "force_exit_mx": _iso_now_plus(5),
        "invalidation_price": 70000,
        "invalidation_side": "below",
        "created_at": _iso_now_plus(-1),
    }
    append_pending("retail", order)
    with patch("watcher_tick.price_for", return_value=80000.0), \
         patch("watcher_tick.notify") as mock_notify, \
         patch("watcher_tick.spawn_escalate") as mock_escalate:
        result = run_tick()
    assert result.ok
    mock_escalate.assert_not_called()
    from pending_lib import load_pendings
    # status unchanged
    assert load_pendings("retail")[0]["status"] == "pending"


def test_tick_writes_status_and_dashboard(tmp_repo):
    with patch("watcher_tick.price_for"), patch("watcher_tick.notify"):
        run_tick()
    status = tmp_repo / ".claude" / "watcher" / "status.json"
    dashboard = tmp_repo / ".claude" / "watcher" / "dashboard.md"
    assert status.exists()
    assert dashboard.exists()
    data = json.loads(status.read_text())
    assert "last_tick_utc" in data
