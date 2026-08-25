from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import free_swarm_historical_backfill_receipt as receipt


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute(
        "CREATE TABLE backfill_files("
        "source_path TEXT PRIMARY KEY,inode INTEGER,byte_offset INTEGER NOT NULL DEFAULT 0,"
        "file_size INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL)"
    )
    return con


def _track(con: sqlite3.Connection, path: Path, offset: int | None = None) -> None:
    st = path.stat()
    con.execute(
        "INSERT OR REPLACE INTO backfill_files(source_path,inode,byte_offset,file_size,updated_at) "
        "VALUES(?,?,?,?,?)",
        (str(path), int(st.st_ino), int(st.st_size if offset is None else offset), int(st.st_size), "test"),
    )
    con.commit()


def _clean_db_after() -> dict[str, object]:
    return {
        "schema_ready": True,
        "historical_outputs": 1,
        "remaining_pending_extraction": 0,
        "max_passes_reached": 0,
        "non_saturated_chunks": 0,
    }


def _classify(
    cutoff: dict[str, object],
    progress: dict[str, object],
    *,
    external_db_changed: bool = False,
) -> tuple[str, list[str]]:
    return receipt.classify(
        source={"dirty": False},
        cutoff=cutoff,
        progress=progress,
        db_after=_clean_db_after(),
        rounds=[{"lines_seen": 0}],
        external_db_changed=external_db_changed,
    )


def test_unchanged_cutoff_file_can_be_caught_up(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    run = root / "run"
    run.mkdir(parents=True)
    worker = run / "workers.jsonl"
    worker.write_bytes(b'{"row":1}\n')

    cutoff = receipt.artifact_cutoff(root)
    con = _con()
    _track(con, worker)
    progress = receipt.cutoff_progress(con, root, cutoff)

    assert progress["caught_up_files"] == 1
    assert progress["uncaught_up_files"] == 0
    assert progress["appended_after_cutoff_files"] == 0
    assert progress["content_changed_at_cutoff_files"] == 0
    assert progress["post_cutoff_new_file_count"] == 0


def test_append_after_cutoff_fails_closed_instead_of_contaminating_receipt(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    run = root / "run"
    run.mkdir(parents=True)
    worker = run / "workers.jsonl"
    worker.write_bytes(b'{"row":1}\n')
    cutoff = receipt.artifact_cutoff(root)

    worker.write_bytes(worker.read_bytes() + b'{"row":2}\n')
    con = _con()
    _track(con, worker)
    progress = receipt.cutoff_progress(con, root, cutoff)
    status, blockers = _classify(cutoff, progress)

    assert progress["appended_after_cutoff_files"] == 1
    assert progress["caught_up_files"] == 0
    assert status == "BLOCKED"
    assert "CUTOFF_FILE_APPENDED_AFTER_CUTOFF" in blockers


def test_same_size_in_place_mutation_fails_closed_by_cutoff_hash(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    run = root / "run"
    run.mkdir(parents=True)
    worker = run / "workers.jsonl"
    worker.write_bytes(b'{"row":1}\n')
    cutoff = receipt.artifact_cutoff(root)

    worker.write_bytes(b'{"row":2}\n')
    con = _con()
    _track(con, worker)
    progress = receipt.cutoff_progress(con, root, cutoff)
    status, blockers = _classify(cutoff, progress)

    assert progress["content_changed_at_cutoff_files"] == 1
    assert progress["caught_up_files"] == 0
    assert status == "BLOCKED"
    assert "CUTOFF_FILE_CONTENT_CHANGED" in blockers


def test_new_workers_file_after_cutoff_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    first = root / "first"
    first.mkdir(parents=True)
    original = first / "workers.jsonl"
    original.write_bytes(b'{"row":1}\n')
    cutoff = receipt.artifact_cutoff(root)

    second = root / "second"
    second.mkdir(parents=True)
    (second / "workers.jsonl").write_bytes(b'{"row":2}\n')

    con = _con()
    _track(con, original)
    progress = receipt.cutoff_progress(con, root, cutoff)
    status, blockers = _classify(cutoff, progress)

    assert progress["post_cutoff_new_file_count"] == 1
    assert progress["post_cutoff_new_files"] == ["second/workers.jsonl"]
    assert status == "BLOCKED"
    assert "POST_CUTOFF_NEW_WORKERS_FILES_OBSERVED" in blockers


def test_external_db_change_is_a_fail_closed_receipt_blocker(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    run = root / "run"
    run.mkdir(parents=True)
    worker = run / "workers.jsonl"
    worker.write_bytes(b'{"row":1}\n')
    cutoff = receipt.artifact_cutoff(root)

    con = _con()
    _track(con, worker)
    progress = receipt.cutoff_progress(con, root, cutoff)
    status, blockers = _classify(cutoff, progress, external_db_changed=True)

    assert status == "BLOCKED"
    assert "FORGE_DB_CHANGED_BY_OTHER_CONNECTION_DURING_RECEIPT" in blockers


def test_sqlite_data_version_changes_only_for_other_connection_commit(tmp_path: Path) -> None:
    db = tmp_path / "forge.sqlite3"
    observer = sqlite3.connect(db)
    observer.execute("CREATE TABLE probe(v INTEGER)")
    observer.commit()
    before = receipt.db_data_version(observer)

    other = sqlite3.connect(db)
    other.execute("INSERT INTO probe(v) VALUES(1)")
    other.commit()
    other.close()
    after_other = receipt.db_data_version(observer)
    assert after_other != before

    observer.execute("INSERT INTO probe(v) VALUES(2)")
    observer.commit()
    after_self = receipt.db_data_version(observer)
    assert after_self == after_other
    observer.close()
