#!/usr/bin/env python3
"""Patch the exact Supervisor-8.78 historical-backfill batch identity gap.

The historical extraction batch is model output and therefore untrusted.  This patch
binds every batch proposal/progress update to the canonical (chunk_id, source_event_id,
next extraction_pass) tuple, refuses oversized envelopes, and forbids non-exhaustive
zero-novel passes from claiming SATURATED.

This helper is intentionally source-hash guarded.  It grants no runtime/product/model
credit by itself and must be executed with the focused regressions on exact current
source.
"""
from __future__ import annotations

from pathlib import Path
import subprocess

EXPECTED_SOURCE_BLOB = "6c441c92024df8b0ff14c4246478523ae3d54266"
EXPECTED_TEST_BLOB = "702c2e42fe6e4881ef7a08b67f6b8b0b567ac8b4"


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "hash-object", rel], text=True
    ).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_MARKER_{label}_COUNT_{count}")
    return text.replace(old, new, 1)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    source_rel = "tools/free_swarm_historical_backfill.py"
    test_rel = "tests/test_free_swarm_historical_backfill.py"
    source_path = repo / source_rel
    test_path = repo / test_rel

    if git_blob(repo, source_rel) != EXPECTED_SOURCE_BLOB:
        raise SystemExit("BACKFILL_SOURCE_BLOB_MOVED_FAIL_CLOSED")
    if git_blob(repo, test_rel) != EXPECTED_TEST_BLOB:
        raise SystemExit("BACKFILL_TEST_BLOB_MOVED_FAIL_CLOSED")

    source = source_path.read_text(encoding="utf-8")
    old_progress = '''def _record_batch_progress(con: sqlite3.Connection, envelope: dict[str, Any], novel_count: int) -> None:\n    chunk_id = str(envelope.get("historical_chunk_id") or "").strip()\n    if not chunk_id:\n        return\n    row = con.execute("SELECT extraction_passes,consecutive_zero_novel FROM historical_chunks WHERE chunk_id=?", (chunk_id,)).fetchone()\n    if not row:\n        return\n    passes = max(int(row[0] or 0) + 1, int(envelope.get("extraction_pass") or 0))\n    zero = int(row[1] or 0) + 1 if novel_count == 0 else 0\n    state = "PENDING_EXTRACTION"\n    if passes >= 2 and zero >= 1:\n        state = "SATURATED"\n    elif passes >= MAX_PASSES:\n        state = "MAX_PASSES_REACHED"\n    con.execute(\n        "UPDATE historical_chunks SET extraction_passes=?,consecutive_zero_novel=?,last_novel_count=?,last_extracted_at=?,state=? WHERE chunk_id=?",\n        (passes, zero, novel_count, now(), state, chunk_id),\n    )\n'''
    new_progress = '''def _batch_binding(con: sqlite3.Connection, value: dict[str, Any]) -> tuple[str, str, int] | None:\n    """Resolve only the exact canonical chunk/source/next-pass binding."""\n    chunk_id = str(value.get("historical_chunk_id") or "").strip()\n    source_event_id = str(value.get("historical_source_event_id") or "").strip()\n    try:\n        extraction_pass = int(value.get("extraction_pass"))\n    except (TypeError, ValueError):\n        return None\n    if not chunk_id or not source_event_id or extraction_pass <= 0:\n        return None\n    row = con.execute(\n        "SELECT source_event_id,extraction_passes FROM historical_chunks WHERE chunk_id=?",\n        (chunk_id,),\n    ).fetchone()\n    if not row or str(row[0]) != source_event_id:\n        return None\n    expected_pass = int(row[1] or 0) + 1\n    if extraction_pass != expected_pass:\n        return None\n    return chunk_id, source_event_id, expected_pass\n\n\ndef _record_batch_progress(con: sqlite3.Connection, envelope: dict[str, Any], novel_count: int) -> None:\n    binding = _batch_binding(con, envelope)\n    values = envelope.get("deltas")\n    if binding is None or not isinstance(values, list) or len(values) > MAX_BATCH_DELTAS:\n        return\n    chunk_id, _, passes = binding\n    row = con.execute(\n        "SELECT consecutive_zero_novel FROM historical_chunks WHERE chunk_id=?",\n        (chunk_id,),\n    ).fetchone()\n    if not row:\n        return\n    zero = int(row[0] or 0) + 1 if novel_count == 0 else 0\n    state = "PENDING_EXTRACTION"\n    if passes >= 2 and zero >= 1 and envelope.get("exhaustive") is True:\n        state = "SATURATED"\n    elif passes >= MAX_PASSES:\n        state = "MAX_PASSES_REACHED"\n    con.execute(\n        "UPDATE historical_chunks SET extraction_passes=?,consecutive_zero_novel=?,last_novel_count=?,last_extracted_at=?,state=? WHERE chunk_id=?",\n        (passes, zero, novel_count, now(), state, chunk_id),\n    )\n'''
    source = replace_once(source, old_progress, new_progress, "PROGRESS")

    old_loop = '''    for obj in proposals:\n        chunk_id = str(obj.get("historical_chunk_id") or "")\n        mode = "HISTORICAL_BATCH" if chunk_id else "EXPLICIT_WORKER_DELTA"\n        was_added, _ = _insert_candidate(con, obj=obj, row=row, source_event_id=event_id, chunk_id=chunk_id, extraction_mode=mode)\n        added += int(was_added)\n        if chunk_id:\n            batch_novel[chunk_id] = batch_novel.get(chunk_id, 0) + int(was_added)\n'''
    new_loop = '''    for obj in proposals:\n        chunk_id = str(obj.get("historical_chunk_id") or "")\n        if chunk_id and _batch_binding(con, obj) is None:\n            # Model-generated causal references are input, never authority.  A\n            # foreign/stale/future pass cannot attach provenance or mint a candidate.\n            continue\n        mode = "HISTORICAL_BATCH" if chunk_id else "EXPLICIT_WORKER_DELTA"\n        was_added, _ = _insert_candidate(con, obj=obj, row=row, source_event_id=event_id, chunk_id=chunk_id, extraction_mode=mode)\n        added += int(was_added)\n        if chunk_id:\n            batch_novel[chunk_id] = batch_novel.get(chunk_id, 0) + int(was_added)\n'''
    source = replace_once(source, old_loop, new_loop, "PROPOSAL_BINDING")
    source_path.write_text(source, encoding="utf-8")

    tests = test_path.read_text(encoding="utf-8")
    test_addition = r'''


def _one_pending_chunk(con: sqlite3.Connection, tmp_path: Path):
    run = tmp_path / "binding"
    run.mkdir(parents=True, exist_ok=True)
    original = _worker("historical source with test benchmark hypothesis and falsifier", serial=21)
    (run / "workers.jsonl").write_text(json.dumps(original) + "\n", encoding="utf-8")
    bf.ingest_artifact_history(con, tmp_path)
    return run, con.execute(
        "SELECT chunk_id,source_event_id,extraction_passes,state FROM historical_chunks LIMIT 1"
    ).fetchone()


def test_foreign_source_event_cannot_mutate_chunk_or_ingest_candidate(tmp_path: Path) -> None:
    con = _con()
    run, chunk = _one_pending_chunk(con, tmp_path)
    proposal = _proposal("foreign", ready=False)
    proposal.update({
        "historical_source_event_id": "foreign-event",
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
    })
    envelope = {
        "historical_source_event_id": "foreign-event",
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": True,
        "deltas": [proposal],
    }
    with (run / "workers.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_worker("ARCHITECTURE_DELTA_BATCH_JSON=" + json.dumps(envelope), serial=22)) + "\n")
    stats = bf.ingest_artifact_history(con, tmp_path)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?", (chunk["chunk_id"],)
    ).fetchone()
    assert stats["candidate_variants_added"] == 0
    assert current["extraction_passes"] == 0
    assert current["state"] == "PENDING_EXTRACTION"


def test_future_or_replayed_pass_cannot_advance_chunk(tmp_path: Path) -> None:
    con = _con()
    _, chunk = _one_pending_chunk(con, tmp_path)
    envelope = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 2,
        "exhaustive": True,
        "deltas": [],
    }
    bf._record_batch_progress(con, envelope, 0)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?", (chunk["chunk_id"],)
    ).fetchone()
    assert current["extraction_passes"] == 0
    assert current["state"] == "PENDING_EXTRACTION"


def test_non_exhaustive_zero_novel_pass_does_not_claim_saturation(tmp_path: Path) -> None:
    con = _con()
    _, chunk = _one_pending_chunk(con, tmp_path)
    first = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": False,
        "deltas": [],
    }
    bf._record_batch_progress(con, first, 0)
    second = dict(first, extraction_pass=2)
    bf._record_batch_progress(con, second, 0)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?", (chunk["chunk_id"],)
    ).fetchone()
    assert current["extraction_passes"] == 2
    assert current["state"] == "PENDING_EXTRACTION"


def test_oversized_batch_cannot_advance_progress(tmp_path: Path) -> None:
    con = _con()
    _, chunk = _one_pending_chunk(con, tmp_path)
    envelope = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": True,
        "deltas": [{} for _ in range(bf.MAX_BATCH_DELTAS + 1)],
    }
    bf._record_batch_progress(con, envelope, 0)
    current = con.execute(
        "SELECT extraction_passes,state FROM historical_chunks WHERE chunk_id=?", (chunk["chunk_id"],)
    ).fetchone()
    assert current["extraction_passes"] == 0
    assert current["state"] == "PENDING_EXTRACTION"
'''
    if "test_foreign_source_event_cannot_mutate_chunk_or_ingest_candidate" in tests:
        raise SystemExit("BACKFILL_IDENTITY_REGRESSIONS_ALREADY_PRESENT_FAIL_CLOSED")
    test_path.write_text(tests.rstrip() + test_addition + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
