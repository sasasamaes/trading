"""CRUD + invalidation + whitelist for pending orders JSON files.

File layout (per profile):
  .claude/profiles/<profile>/memory/pending_orders.json
  {
    "pending": [<order>, ...],
    "meta": {...}
  }
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

PROFILES = ("retail", "retail-bingx", "ftmo", "fotmarkets")


def _repo_root() -> Path:
    """Allow tests to override with WALLY_REPO_ROOT."""
    env = os.environ.get("WALLY_REPO_ROOT")
    if env:
        return Path(env)
    # Default: walk up from this file to find wally-trader root
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists() and (parent / ".claude").is_dir():
            return parent
    raise RuntimeError("Could not locate wally-trader repo root")


def _pending_path(profile: str) -> Path:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Valid: {PROFILES}")
    return _repo_root() / ".claude" / "profiles" / profile / "memory" / "pending_orders.json"


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_file(profile: str) -> dict:
    path = _pending_path(profile)
    if not path.exists():
        return {"pending": [], "meta": {}}
    with path.open() as f:
        return json.load(f)


def _save_file(profile: str, payload: dict) -> None:
    """Atomic write: temp file + os.replace."""
    path = _pending_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=path.parent,
        delete=False,
        prefix=".pending_",
        suffix=".tmp",
    ) as tf:
        json.dump(payload, tf, indent=2)
        tmp_name = tf.name
    os.replace(tmp_name, path)


def load_pendings(profile: str) -> list[dict]:
    """Return list of pending orders for a profile."""
    return _load_file(profile).get("pending", [])


def save_pendings(profile: str, pendings: list[dict], meta: Optional[dict] = None) -> None:
    """Overwrite the pending list for a profile. meta is merged with existing."""
    payload = _load_file(profile)
    payload["pending"] = pendings
    if meta:
        payload.setdefault("meta", {}).update(meta)
    _save_file(profile, payload)


def append_pending(profile: str, order: dict) -> dict:
    """Append a new order. Initializes status_history if missing."""
    order = dict(order)  # don't mutate caller
    if "status_history" not in order:
        order["status_history"] = [
            {
                "at": _now_iso(),
                "status": order.get("status", "pending"),
                "note": "created via append_pending",
            }
        ]
    pendings = load_pendings(profile)
    pendings.append(order)
    save_pendings(profile, pendings)
    return order


def update_status(profile: str, order_id: str, new_status: str, note: str = "") -> dict:
    """Mutate status + append to status_history. Raises KeyError if id not found."""
    pendings = load_pendings(profile)
    for order in pendings:
        if order["id"] == order_id:
            order["status"] = new_status
            history = order.setdefault("status_history", [])
            history.append({"at": _now_iso(), "status": new_status, "note": note})
            save_pendings(profile, pendings)
            return order
    raise KeyError(f"No pending order with id={order_id!r} in profile {profile!r}")


def find_by_id(order_id: str) -> Optional[tuple[str, dict]]:
    """Search all profiles for an order. Returns (profile, order) or None."""
    for profile in PROFILES:
        for order in load_pendings(profile):
            if order["id"] == order_id:
                return profile, order
    return None


def load_all_pendings() -> dict[str, list[dict]]:
    """Return {profile: [pendings, ...]} for all profiles."""
    return {profile: load_pendings(profile) for profile in PROFILES}
