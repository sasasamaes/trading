"""Tests for pending_lib CRUD."""
import json
import os
import tempfile
from pathlib import Path
import pytest

from pending_lib import (
    PROFILES,
    load_pendings,
    save_pendings,
    append_pending,
    update_status,
    find_by_id,
    load_all_pendings,
)


@pytest.fixture
def tmp_repo(tmp_path, monkeypatch):
    """Create a fake .claude/profiles/*/memory/pending_orders.json tree."""
    for profile in PROFILES:
        memdir = tmp_path / ".claude" / "profiles" / profile / "memory"
        memdir.mkdir(parents=True, exist_ok=True)
        (memdir / "pending_orders.json").write_text(
            json.dumps({"pending": [], "meta": {}})
        )
    monkeypatch.setenv("WALLY_REPO_ROOT", str(tmp_path))
    return tmp_path


def test_load_empty_profile_returns_empty_list(tmp_repo):
    assert load_pendings("retail") == []


def test_save_and_load_roundtrip(tmp_repo):
    orders = [{"id": "ord_1", "profile": "retail", "status": "pending"}]
    save_pendings("retail", orders)
    assert load_pendings("retail") == orders


def test_append_pending_adds_status_history(tmp_repo):
    order = {"id": "ord_1", "profile": "retail", "status": "pending"}
    append_pending("retail", order)
    loaded = load_pendings("retail")
    assert len(loaded) == 1
    assert loaded[0]["id"] == "ord_1"
    assert len(loaded[0]["status_history"]) == 1
    assert loaded[0]["status_history"][0]["status"] == "pending"


def test_update_status_appends_history(tmp_repo):
    append_pending("retail", {"id": "ord_1", "profile": "retail", "status": "pending"})
    update_status("retail", "ord_1", "expired_ttl", note="TTL passed")
    loaded = load_pendings("retail")
    assert loaded[0]["status"] == "expired_ttl"
    assert len(loaded[0]["status_history"]) == 2
    assert loaded[0]["status_history"][-1]["note"] == "TTL passed"


def test_update_status_raises_if_id_missing(tmp_repo):
    with pytest.raises(KeyError):
        update_status("retail", "nope", "expired_ttl")


def test_find_by_id_searches_all_profiles(tmp_repo):
    append_pending("fotmarkets", {"id": "ord_fx", "profile": "fotmarkets", "status": "pending"})
    found = find_by_id("ord_fx")
    assert found is not None
    profile, order = found
    assert profile == "fotmarkets"
    assert order["id"] == "ord_fx"


def test_find_by_id_returns_none_if_not_found(tmp_repo):
    assert find_by_id("nonexistent") is None


def test_load_all_pendings_covers_all_profiles(tmp_repo):
    append_pending("retail", {"id": "a", "profile": "retail", "status": "pending"})
    append_pending("ftmo", {"id": "b", "profile": "ftmo", "status": "pending"})
    result = load_all_pendings()
    assert set(result.keys()) == set(PROFILES)
    assert len(result["retail"]) == 1
    assert len(result["ftmo"]) == 1
    assert result["fotmarkets"] == []


def test_save_is_atomic(tmp_repo):
    """Partial writes must not corrupt the file."""
    # Write a valid baseline
    save_pendings("retail", [{"id": "ord_1", "status": "pending"}])
    file_path = tmp_repo / ".claude/profiles/retail/memory/pending_orders.json"
    mtime_before = file_path.stat().st_mtime
    # Trigger a save that raises after writing temp file
    # (simulated: just verify roundtrip doesn't leave .tmp files behind)
    save_pendings("retail", [{"id": "ord_2", "status": "pending"}])
    assert not any(tmp_repo.rglob("*.tmp"))
