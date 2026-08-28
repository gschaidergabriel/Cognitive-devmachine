#!/usr/bin/env python3
"""Repair historical Forge source-support counting without creating a new authority.

The historical backfill deduplicates detailed candidate_sources with INSERT OR IGNORE,
but the predecessor increments candidates.source_count *before* that admission.  A
transport/cursor replay of the same causal source therefore inflates apparent support.

This patch is function-scoped and exact-content bound, so it composes with the separate
GO878 cumulative-line checkpoint and historical-batch causal-binding repairs.  It makes
source_count count distinct source_event_id observations, while retaining detailed
chunk/extractor links in candidate_sources.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_REL = "tools/free_swarm_historical_backfill.py"
TEST_REL = "tests/test_free_swarm_historical_backfill.py"
EXPECTED_FUNCTION_SHA256 = "dfee73d91afea5aed1258d24483686f54013c561e10384dc3d0e456854ec153f"


def function_slice(text: str) -> tuple[int, int, str]:
    start_marker = "def _insert_candidate("
    end_marker = "\n\ndef _batch_binding("
    start = text.find(start_marker)
    end = text.find(end_marker, start + 1)
    if start < 0:
        raise SystemExit("SOURCE_COUNT_INSERT_FUNCTION_MISSING")
    if end < 0:
        # Pre-batch-binding predecessor uses _record_batch_progress as the next function.
        end_marker = "\n\ndef _record_batch_progress("
        end = text.find(end_marker, start + 1)
    if end < 0:
        raise SystemExit("SOURCE_COUNT_INSERT_FUNCTION_END_MISSING")
    return start, end, text[start:end]


REPLACEMENT = '''def _insert_candidate(con: sqlite3.Connection, *, obj: dict[str, Any], row: dict[str, Any], source_event_id: str, chunk_id: str, extraction_mode: str) -> tuple[bool, str]:
    valid, reasons = validate_delta(obj)
    if not valid:
        return False, "SCHEMA_INVALID:" + ",".join(reasons[:8])
    raw = canonical(obj)
    repo_head = str(row.get("repo_head_at_prompt") or "").strip().lower()
    if not COMMIT_RE.fullmatch(repo_head):
        repo_head = ""
    cid = concept_identity(obj, repo_head)
    vid = variant_identity(obj, repo_head)
    existing = con.execute(
        "SELECT candidate_hash FROM candidates WHERE variant_id=? ORDER BY evaluated_at IS NULL,ingested_at LIMIT 1",
        (vid,),
    ).fetchone()
    stamp = now()
    worker_sha = str(row.get("text_sha256") or sha_text(str(row.get("text") or "")))
    score = actionability_score(str(row.get("text") or ""), str(row.get("role") or ""))
    if existing:
        candidate_hash = str(existing[0])
        added = False
    else:
        candidate_hash = vid
        ready = bool(obj.get("ready_for_forge"))
        state = "NEW" if ready else "NEEDS_IMPLEMENTATION"
        con.execute(
            "INSERT INTO candidates(candidate_hash,delta_id,provider,model,role,worker_sha,repo_head,proposal_json,ready,state,ingested_at,concept_id,variant_id,source_count,first_seen_at,last_seen_at,extraction_mode,priority) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (candidate_hash, str(obj.get("delta_id") or candidate_hash[:16]), str(row.get("provider") or ""), str(row.get("model") or ""), str(row.get("role") or ""), worker_sha, repo_head, raw, int(ready), state, stamp, cid, vid, 1, stamp, stamp, extraction_mode, score),
        )
        added = True

    # Detailed provenance may contain multiple chunk/extractor links for one
    # causal worker output.  source_count is deliberately narrower: one unit per
    # distinct source_event_id, never one unit per replay or extraction link.
    had_source_event = bool(con.execute(
        "SELECT 1 FROM candidate_sources WHERE candidate_hash=? AND source_event_id=? LIMIT 1",
        (candidate_hash, source_event_id),
    ).fetchone())
    con.execute(
        "INSERT OR IGNORE INTO candidate_sources(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode,seen_at) VALUES(?,?,?,?,?,?)",
        (candidate_hash, source_event_id, chunk_id or "", worker_sha, extraction_mode, stamp),
    )
    if existing:
        if had_source_event:
            con.execute(
                "UPDATE candidates SET priority=MAX(COALESCE(priority,0),?) WHERE candidate_hash=?",
                (score, candidate_hash),
            )
        else:
            con.execute(
                "UPDATE candidates SET source_count=COALESCE(source_count,1)+1,last_seen_at=?,priority=MAX(COALESCE(priority,0),?) WHERE candidate_hash=?",
                (stamp, score, candidate_hash),
            )
    return added, candidate_hash'''


REGRESSIONS = r'''


def test_replaying_same_source_event_does_not_inflate_source_count(tmp_path: Path) -> None:
    con = _con()
    run = tmp_path / "same-source-replay"
    run.mkdir(parents=True)
    proposal = _proposal("stable-source", ready=False)
    worker = _worker("ARCHITECTURE_DELTA_JSON=" + json.dumps(proposal), serial=1)
    path = run / "workers.jsonl"
    path.write_text(json.dumps(worker) + "\n", encoding="utf-8")

    bf.ingest_artifact_history(con, tmp_path)
    before = con.execute("SELECT candidate_hash,source_count FROM candidates").fetchone()
    assert int(before["source_count"]) == 1

    # Replay the exact same append-only row from byte zero.  Detailed provenance
    # admission is idempotent, and the aggregate support count must be too.
    con.execute("DELETE FROM backfill_files WHERE source_path=?", (str(path),))
    con.commit()
    bf.ingest_artifact_history(con, tmp_path)
    after = con.execute("SELECT candidate_hash,source_count FROM candidates").fetchone()
    assert after["candidate_hash"] == before["candidate_hash"]
    assert int(after["source_count"]) == 1
    assert int(con.execute(
        "SELECT COUNT(DISTINCT source_event_id) FROM candidate_sources WHERE candidate_hash=?",
        (after["candidate_hash"],),
    ).fetchone()[0]) == 1


def test_distinct_source_events_increment_source_count_exactly_once(tmp_path: Path) -> None:
    con = _con()
    run = tmp_path / "distinct-source-events"
    run.mkdir(parents=True)
    a = _proposal("same-variant-a", ready=False)
    b = _proposal("same-variant-b", ready=False)
    rows = [
        _worker("ARCHITECTURE_DELTA_JSON=" + json.dumps(a), serial=1),
        _worker("ARCHITECTURE_DELTA_JSON=" + json.dumps(b), serial=2),
    ]
    (run / "workers.jsonl").write_text(
        "\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8"
    )
    bf.ingest_artifact_history(con, tmp_path)
    candidate = con.execute("SELECT candidate_hash,source_count FROM candidates").fetchone()
    assert int(candidate["source_count"]) == 2
    assert int(con.execute(
        "SELECT COUNT(DISTINCT source_event_id) FROM candidate_sources WHERE candidate_hash=?",
        (candidate["candidate_hash"],),
    ).fetchone()[0]) == 2
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    source = repo / SOURCE_REL
    tests = repo / TEST_REL
    source_text = source.read_text(encoding="utf-8")
    test_text = tests.read_text(encoding="utf-8")

    if "had_source_event = bool(con.execute(" in source_text:
        print("GO878_SOURCE_COUNT_ALREADY_FIXED")
        return 0

    start, end, old_function = function_slice(source_text)
    observed = hashlib.sha256(old_function.encode("utf-8")).hexdigest()
    if observed != EXPECTED_FUNCTION_SHA256:
        raise SystemExit(
            f"SOURCE_COUNT_FUNCTION_MOVED_FAIL_CLOSED:expected={EXPECTED_FUNCTION_SHA256}:observed={observed}"
        )
    source.write_text(source_text[:start] + REPLACEMENT + source_text[end:], encoding="utf-8")

    sentinel = "test_replaying_same_source_event_does_not_inflate_source_count"
    if sentinel not in test_text:
        tests.write_text(test_text.rstrip() + REGRESSIONS + "\n", encoding="utf-8")
    print("GO878_SOURCE_COUNT_PATCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
