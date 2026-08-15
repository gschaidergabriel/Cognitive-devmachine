from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import sys
from tempfile import TemporaryDirectory

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from ucm2 import UCM2  # noqa: E402
from ucm2_lineage_anchor import ANCHOR_FILENAME, AnchoredUCM2  # noqa: E402


def expect_runtime_error(fn, expected: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert str(exc) == expected, (str(exc), expected)
    else:
        raise AssertionError(f"expected {expected}")


def rehash_from(stream: list[dict], index: int) -> None:
    prev_hash = stream[index - 1]["event_hash"] if index else ""
    for event in stream[index:]:
        event["prev_hash"] = prev_hash
        event["event_hash"] = UCM2._compute_event_hash(
            int(event["epoch"]),
            event["event_type"],
            event["object_id"],
            event["payload"],
            event["prev_hash"],
            event["created_at"],
        )
        prev_hash = event["event_hash"]


def backup_database(machine: AnchoredUCM2, target: Path) -> None:
    destination = sqlite3.connect(target)
    try:
        machine.machine.db.backup(destination)
    finally:
        destination.close()


def install_database_snapshot(root: Path, snapshot: Path) -> None:
    state = root / "state"
    for suffix in ("-wal", "-shm"):
        side = state / f"UCM2.sqlite{suffix}"
        if side.exists():
            side.unlink()
    shutil.copy2(snapshot, state / "UCM2.sqlite")


def main() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Branch 1: admitted current stream survives a normal restart.
        current_root = tmp / "current"
        current = AnchoredUCM2(current_root)
        current.upsert("world.main", "world_model", {"repo": "main-A"})
        current.upsert("state.focus", "state", {"focus": "UCM2"})
        admitted_epoch = current.epoch()
        admitted_head = current.verify_event_stream()
        anchor = json.loads(current.anchor_path.read_text(encoding="utf-8"))
        assert int(anchor["epoch"]) == admitted_epoch == 2
        assert anchor["terminal_event_hash"] == admitted_head
        assert stat.S_IMODE(current.anchor_path.stat().st_mode) == 0o600
        current.close()

        restarted = AnchoredUCM2(current_root)
        assert restarted.epoch() == admitted_epoch
        assert restarted.verify_event_stream() == admitted_head
        restarted.close()

        # BOUNDED UNUSUAL EXPERIMENT — WHOLE_DB_TIME_TRAVEL.
        # Keep the sidecar witness at a newer admitted generation but replace
        # only SQLite with a consistent older online-backup snapshot.  This is
        # intentionally a whole valid DB rewind, not an in-place corrupt page.
        rollback_root = tmp / "rollback"
        rollback = AnchoredUCM2(rollback_root)
        rollback.upsert("world.main", "world_model", {"repo": "epoch-1"})
        rollback.upsert("wiki.one", "wiki", {"text": "epoch-2"})
        stale_snapshot = tmp / "stale-epoch-2.sqlite"
        backup_database(rollback, stale_snapshot)
        rollback.upsert("state.three", "state", {"n": 3})
        rollback.upsert("state.four", "state", {"n": 4})
        assert rollback.epoch() == 4
        rollback.close()
        install_database_snapshot(rollback_root, stale_snapshot)
        expect_runtime_error(
            lambda: AnchoredUCM2(rollback_root), "LINEAGE_ROLLBACK_DETECTED"
        )

        # Branch 2: a coherent same-epoch sibling chain is internally valid but
        # is rejected because the surviving witness admitted a different head.
        sibling_root = tmp / "sibling-source"
        sibling_source = AnchoredUCM2(sibling_root)
        sibling_source.upsert("world.main", "world_model", {"repo": "canonical-main"})
        sibling_source.upsert("state.focus", "state", {"focus": "canonical"})
        canonical_stream = sibling_source.event_stream()
        canonical_head = sibling_source.verify_event_stream()
        sibling_source.close()

        sibling_stream = deepcopy(canonical_stream)
        sibling_index = 1
        sibling_stream[sibling_index]["payload"]["payload"]["repo"] = "coherent-sibling-main"
        rehash_from(sibling_stream, sibling_index)
        sibling_plain_root = tmp / "sibling-plain"
        sibling_plain = UCM2(sibling_plain_root)
        sibling_head = sibling_plain.verify_event_stream(sibling_stream)
        assert sibling_head != canonical_head
        sibling_plain.restore_from_event_stream(sibling_stream)
        sibling_plain.close()

        install_database_snapshot(
            sibling_root, sibling_plain_root / "state" / "UCM2.sqlite"
        )
        expect_runtime_error(
            lambda: AnchoredUCM2(sibling_root), "LINEAGE_HEAD_MISMATCH"
        )

        # Branch 3: removing the witness from a non-zero machine fails closed.
        missing_root = tmp / "missing"
        missing = AnchoredUCM2(missing_root)
        missing.upsert("state.one", "state", {"n": 1})
        missing.close()
        (missing_root / "state" / ANCHOR_FILENAME).unlink()
        expect_runtime_error(
            lambda: AnchoredUCM2(missing_root), "LINEAGE_ANCHOR_MISSING_NONZERO"
        )

        # Crash-window control: DB-ahead-of-anchor is not silently promoted.
        ahead_root = tmp / "ahead"
        ahead = AnchoredUCM2(ahead_root)
        ahead.upsert("state.one", "state", {"n": 1})
        ahead.close()
        plain = UCM2(ahead_root)
        plain.upsert("state.two", "state", {"n": 2})
        plain.close()
        expect_runtime_error(lambda: AnchoredUCM2(ahead_root), "LINEAGE_ANCHOR_STALE")

    print("UCM2_LINEAGE_ANCHOR_PASS")
    print("UCM2_WHOLE_DB_TIME_TRAVEL_REJECTED")
    print("UCM2_COHERENT_SIBLING_REJECTED")
    print("UCM2_MISSING_OR_STALE_ANCHOR_FAIL_CLOSED")


if __name__ == "__main__":
    main()
