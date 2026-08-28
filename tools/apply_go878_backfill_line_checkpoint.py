#!/usr/bin/env python3
"""Repair replay-stable historical source-event identity across incremental resumes.

Supervisor 8.78 requires historical replay to preserve execution identity. The current
backfill persists byte offsets but resets its per-call line counter, so a physical JSONL
row can receive a different source_event_id depending on max_new_lines chunking.

This exact-blob patcher adds a cumulative line checkpoint, deterministic migration of
legacy offset-only checkpoints, and a one-shot-vs-resumed identity regression. It does
not run providers/models or grant runtime/model/training credit.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

SOURCE_REL = "tools/free_swarm_historical_backfill.py"
TEST_REL = "tests/test_free_swarm_historical_backfill.py"
EXPECTED_SOURCE_BLOB = "5cb0045f5c355170372efd4f08c033b33c91fbed"
EXPECTED_TEST_BLOB = "702c2e42fe6e4881ef7a08b67f6b8b0b567ac8b4"


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "hash-object", rel], text=True).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_MARKER_{label}_COUNT_{count}")
    return text.replace(old, new, 1)


def patch_source(text: str) -> str:
    text = replace_once(
        text,
        '''        CREATE TABLE IF NOT EXISTS backfill_files(\n          source_path TEXT PRIMARY KEY, inode INTEGER, byte_offset INTEGER NOT NULL DEFAULT 0,\n          file_size INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL\n        );''',
        '''        CREATE TABLE IF NOT EXISTS backfill_files(\n          source_path TEXT PRIMARY KEY, inode INTEGER, byte_offset INTEGER NOT NULL DEFAULT 0,\n          file_size INTEGER NOT NULL DEFAULT 0, line_no INTEGER NOT NULL DEFAULT 0,\n          updated_at TEXT NOT NULL\n        );''',
        "BACKFILL_SCHEMA",
    )
    text = replace_once(
        text,
        '''    con.execute("CREATE INDEX IF NOT EXISTS idx_historical_chunks_queue ON historical_chunks(state,actionability DESC,extraction_passes,chunk_index)")''',
        '''    # Additive successor-dynamic migration for databases created before the\n    # replay-stable cumulative line checkpoint existed.\n    backfill_cols = {str(row[1]) for row in con.execute("PRAGMA table_info(backfill_files)")}\n    if "line_no" not in backfill_cols:\n        con.execute("ALTER TABLE backfill_files ADD COLUMN line_no INTEGER NOT NULL DEFAULT 0")\n    con.execute("CREATE INDEX IF NOT EXISTS idx_historical_chunks_queue ON historical_chunks(state,actionability DESC,extraction_passes,chunk_index)")''',
        "BACKFILL_SCHEMA_MIGRATION",
    )
    text = replace_once(
        text,
        '''        saved = con.execute("SELECT inode,byte_offset,file_size FROM backfill_files WHERE source_path=?", (key,)).fetchone()\n        offset = int(saved[1] or 0) if saved else 0\n        saved_inode = int(saved[0]) if saved and saved[0] is not None else None\n        if saved and (saved_inode != int(st.st_ino) or int(st.st_size) < offset):\n            offset = 0\n        try:\n            with path.open("rb") as fh:\n                fh.seek(offset)\n                local_line = 0''',
        '''        saved = con.execute("SELECT inode,byte_offset,file_size,line_no FROM backfill_files WHERE source_path=?", (key,)).fetchone()\n        offset = int(saved[1] or 0) if saved else 0\n        saved_inode = int(saved[0]) if saved and saved[0] is not None else None\n        absolute_line = int(saved[3] or 0) if saved else 0\n        if saved and (saved_inode != int(st.st_ino) or int(st.st_size) < offset):\n            offset = 0\n            absolute_line = 0\n        elif saved and offset > 0 and absolute_line == 0:\n            # Legacy checkpoints persisted only byte_offset. Recover the absolute\n            # completed-line count from the exact byte prefix instead of inventing\n            # a post-hoc identity. If the checkpoint is not a complete-line boundary,\n            # fail safely by replaying from byte zero.\n            try:\n                with path.open("rb") as checkpoint_fh:\n                    prefix = checkpoint_fh.read(offset)\n                if len(prefix) != offset or not prefix.endswith(b"\\n"):\n                    offset = 0\n                    absolute_line = 0\n                else:\n                    absolute_line = prefix.count(b"\\n")\n            except OSError:\n                offset = 0\n                absolute_line = 0\n        try:\n            with path.open("rb") as fh:\n                fh.seek(offset)''',
        "LOAD_CHECKPOINT",
    )
    text = replace_once(text, "                    local_line += 1", "                    absolute_line += 1", "LINE_INCREMENT")
    text = replace_once(
        text,
        '''                    stats = _ingest_worker_row(con, row, key, local_line)''',
        '''                    stats = _ingest_worker_row(con, row, key, absolute_line)''',
        "ABSOLUTE_LINE_IDENTITY",
    )
    text = replace_once(
        text,
        '''            "INSERT INTO backfill_files(source_path,inode,byte_offset,file_size,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(source_path) DO UPDATE SET inode=excluded.inode,byte_offset=excluded.byte_offset,file_size=excluded.file_size,updated_at=excluded.updated_at",\n            (key, int(st.st_ino), offset, int(st.st_size), now()),''',
        '''            "INSERT INTO backfill_files(source_path,inode,byte_offset,file_size,line_no,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(source_path) DO UPDATE SET inode=excluded.inode,byte_offset=excluded.byte_offset,file_size=excluded.file_size,line_no=excluded.line_no,updated_at=excluded.updated_at",\n            (key, int(st.st_ino), offset, int(st.st_size), absolute_line, now()),''',
        "SAVE_CHECKPOINT",
    )
    if "local_line" in text:
        raise SystemExit("LOCAL_LINE_REMAINS_FAIL_CLOSED")
    return text


REGRESSION = r'''


def test_incremental_resume_preserves_absolute_line_source_event_identity(tmp_path: Path) -> None:
    """Physical JSONL identity must not depend on max_new_lines chunking."""
    run = tmp_path / "stable-source"
    run.mkdir(parents=True)
    rows = [
        _worker("first historical output with test benchmark falsifier", serial=1),
        _worker("second historical output with test benchmark falsifier", serial=2),
        _worker("third historical output with test benchmark falsifier", serial=3),
    ]
    worker_file = run / "workers.jsonl"
    worker_file.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")

    one_shot = _con()
    stats = bf.ingest_artifact_history(one_shot, tmp_path, max_new_lines=10)
    assert stats["lines_seen"] == 3
    expected = [
        (int(r["line_no"]), str(r["source_event_id"]), str(r["text_sha256"]))
        for r in one_shot.execute(
            "SELECT line_no,source_event_id,text_sha256 FROM historical_outputs ORDER BY line_no"
        ).fetchall()
    ]
    assert [x[0] for x in expected] == [1, 2, 3]

    resumed = _con()
    assert bf.ingest_artifact_history(resumed, tmp_path, max_new_lines=1)["lines_seen"] == 1
    assert bf.ingest_artifact_history(resumed, tmp_path, max_new_lines=1)["lines_seen"] == 1
    assert bf.ingest_artifact_history(resumed, tmp_path, max_new_lines=1)["lines_seen"] == 1
    observed = [
        (int(r["line_no"]), str(r["source_event_id"]), str(r["text_sha256"]))
        for r in resumed.execute(
            "SELECT line_no,source_event_id,text_sha256 FROM historical_outputs ORDER BY line_no"
        ).fetchall()
    ]
    assert observed == expected


def test_legacy_offset_only_checkpoint_recovers_absolute_line(tmp_path: Path) -> None:
    """Old DB checkpoints migrate from byte offset without assigning row 2 line 1."""
    run = tmp_path / "legacy-source"
    run.mkdir(parents=True)
    rows = [
        _worker("legacy first historical output with test benchmark falsifier", serial=1),
        _worker("legacy second historical output with test benchmark falsifier", serial=2),
    ]
    encoded = [(json.dumps(x) + "\n").encode("utf-8") for x in rows]
    worker_file = run / "workers.jsonl"
    worker_file.write_bytes(b"".join(encoded))

    con = _con()
    st = worker_file.stat()
    first_size = len(encoded[0])
    # Model a pre-fix checkpoint: offset is valid but the newly added line_no column
    # has its migration default zero.
    con.execute(
        "INSERT INTO backfill_files(source_path,inode,byte_offset,file_size,line_no,updated_at) VALUES(?,?,?,?,0,?)",
        (str(worker_file), int(st.st_ino), first_size, int(st.st_size), bf.now()),
    )
    con.commit()
    stats = bf.ingest_artifact_history(con, tmp_path, max_new_lines=1)
    assert stats["lines_seen"] == 1
    row = con.execute("SELECT line_no FROM historical_outputs").fetchone()
    assert row is not None
    assert int(row["line_no"]) == 2
    checkpoint = con.execute(
        "SELECT byte_offset,line_no FROM backfill_files WHERE source_path=?", (str(worker_file),)
    ).fetchone()
    assert int(checkpoint["byte_offset"]) == int(st.st_size)
    assert int(checkpoint["line_no"]) == 2
'''


def patch_test(text: str) -> str:
    if "test_incremental_resume_preserves_absolute_line_source_event_identity" in text:
        raise SystemExit("REGRESSION_ALREADY_PRESENT")
    return text.rstrip() + REGRESSION + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    source = repo / SOURCE_REL
    test = repo / TEST_REL

    observed_source = git_blob(repo, SOURCE_REL)
    observed_test = git_blob(repo, TEST_REL)
    if observed_source != EXPECTED_SOURCE_BLOB:
        raise SystemExit(f"BACKFILL_SOURCE_MOVED_FAIL_CLOSED:expected={EXPECTED_SOURCE_BLOB}:observed={observed_source}")
    if observed_test != EXPECTED_TEST_BLOB:
        raise SystemExit(f"BACKFILL_TEST_MOVED_FAIL_CLOSED:expected={EXPECTED_TEST_BLOB}:observed={observed_test}")

    source.write_text(patch_source(source.read_text(encoding="utf-8")), encoding="utf-8")
    test.write_text(patch_test(test.read_text(encoding="utf-8")), encoding="utf-8")
    subprocess.run(["python3", "-m", "py_compile", str(source)], check=True)
    print("GO878_BACKFILL_LINE_CHECKPOINT_PATCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
