from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import grid10_node
from grid10_decode_safe_node_wrapper_v1 import DecodeSafeFabric, install_decode_safe_fabric


def _epoch(db: Path) -> int:
    con = sqlite3.connect(str(db))
    try:
        return int(con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0])
    finally:
        con.close()


def _last_seen(db: Path, node_id: str) -> float:
    con = sqlite3.connect(str(db))
    try:
        return float(con.execute("SELECT last_seen_ts FROM nodes WHERE node_id=?", (node_id,)).fetchone()[0])
    finally:
        con.close()


def test_decode_safe_fabric_starts_epoch_neutral_pump_after_join(tmp_path: Path) -> None:
    db = tmp_path / "fabric.sqlite"
    f = DecodeSafeFabric(db, heartbeat_interval_s=0.02)
    f.runtime_join("node-a", "reason", 123)
    assert "node-a" in f._decode_safe_pumps
    assert f._decode_safe_pumps["node-a"].running

    before_epoch = _epoch(db)
    before_seen = _last_seen(db, "node-a")
    # Simulates time spent inside a blocking decode.  Only the background pump is active.
    time.sleep(0.10)
    after_seen = _last_seen(db, "node-a")
    after_epoch = _epoch(db)

    report = f.stop_decode_safe_heartbeats()
    assert after_seen > before_seen
    assert after_epoch == before_epoch
    assert report["node-a"]["successes"] >= 2
    assert report["node-a"]["failures"] == 0


def test_join_is_idempotent_for_pump_creation(tmp_path: Path) -> None:
    f = DecodeSafeFabric(tmp_path / "fabric.sqlite", heartbeat_interval_s=0.02)
    f.runtime_join("node-a", "reason", 123)
    first = f._decode_safe_pumps["node-a"]
    f.runtime_join("node-a", "reason", 123)
    second = f._decode_safe_pumps["node-a"]
    try:
        assert first is second
    finally:
        f.stop_decode_safe_heartbeats()


def test_install_replaces_only_node_module_fabric_constructor() -> None:
    original = grid10_node.Fabric
    try:
        configured = install_decode_safe_fabric(heartbeat_interval_s=0.07)
        assert grid10_node.Fabric is configured
        assert issubclass(configured, DecodeSafeFabric)
    finally:
        grid10_node.Fabric = original


def test_invalid_interval_fails_closed(tmp_path: Path) -> None:
    try:
        DecodeSafeFabric(tmp_path / "fabric.sqlite", heartbeat_interval_s=0)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "heartbeat_interval_s" in str(exc)


def test_stop_is_observable_and_removes_pumps(tmp_path: Path) -> None:
    f = DecodeSafeFabric(tmp_path / "fabric.sqlite", heartbeat_interval_s=0.02)
    f.runtime_join("node-a", "reason", 123)
    time.sleep(0.06)
    report = f.stop_decode_safe_heartbeats()
    assert "node-a" in report
    assert report["node-a"]["attempts"] >= 2
    assert f._decode_safe_pumps == {}
