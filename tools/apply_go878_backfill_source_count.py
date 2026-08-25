#!/usr/bin/env python3
"""Repair historical Forge source support while preserving extractor lineage.

Two independent replay hazards are covered:
1. candidate source_count must not increment when an already-admitted provenance link replays;
2. for HISTORICAL_BATCH, evidence support belongs to the canonical *original* historical
   source_event_id resolved by _batch_binding(), not to each extractor worker event.

Detailed chunk/extractor lineage remains append-only in candidate_sources through
extractor_worker_sha. This patcher is fail-closed and creates no second Forge/truth/effect
authority. It is safe as a successor to the already-fused source-link idempotence repair.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_REL = "tools/free_swarm_historical_backfill.py"
TEST_REL = "tests/test_free_swarm_historical_backfill.py"
EXPECTED_PRE_IDEMPOTENCE_FUNCTION_SHA256 = "dfee73d91afea5aed1258d24483686f54013c561e10384dc3d0e456854ec153f"


def function_slice(text: str) -> tuple[int, int, str]:
    start_marker = "def _insert_candidate("
    end_marker = "\n\ndef _batch_binding("
    start = text.find(start_marker)
    end = text.find(end_marker, start + 1)
    if start < 0 or end < 0:
        raise SystemExit("SOURCE_COUNT_INSERT_FUNCTION_ANCHOR_MISSING")
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

    had_source_event = bool(con.execute(
        "SELECT 1 FROM candidate_sources WHERE candidate_hash=? AND source_event_id=? LIMIT 1",
        (candidate_hash, source_event_id),
    ).fetchone())
    con.execute(
        "INSERT OR IGNORE INTO candidate_sources(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode,seen_at) VALUES(?,?,?,?,?,?)",
        (candidate_hash, source_event_id, chunk_id or "", worker_sha, extraction_mode, stamp),
    )
    if existing:
        con.execute(
            "UPDATE candidates SET source_count=COALESCE(source_count,1)+?,last_seen_at=?,priority=MAX(COALESCE(priority,0),?) WHERE candidate_hash=?",
            (0 if had_source_event else 1, stamp, score, candidate_hash),
        )
    return added, candidate_hash'''


INGEST_OLD = '''    for obj in proposals:
        chunk_id = str(obj.get("historical_chunk_id") or "")
        if chunk_id and _batch_binding(con, obj) is None:
            # Model-generated causal references are input, never authority. A
            # foreign/stale/future pass cannot attach provenance or mint a candidate.
            continue
        mode = "HISTORICAL_BATCH" if chunk_id else "EXPLICIT_WORKER_DELTA"
        was_added, _ = _insert_candidate(con, obj=obj, row=row, source_event_id=event_id, chunk_id=chunk_id, extraction_mode=mode)
        added += int(was_added)
        if chunk_id:
            batch_novel[chunk_id] = batch_novel.get(chunk_id, 0) + int(was_added)
'''

INGEST_NEW = '''    for obj in proposals:
        chunk_id = str(obj.get("historical_chunk_id") or "")
        binding = _batch_binding(con, obj) if chunk_id else None
        if chunk_id and binding is None:
            # Model-generated causal references are input, never authority. A
            # foreign/stale/future pass cannot attach provenance or mint a candidate.
            continue
        mode = "HISTORICAL_BATCH" if chunk_id else "EXPLICIT_WORKER_DELTA"
        # Historical support belongs to the canonical original source resolved by
        # _batch_binding(). The extractor worker remains independently preserved
        # through extractor_worker_sha inside candidate_sources.
        candidate_source_event_id = str(binding[1]) if binding is not None else event_id
        was_added, _ = _insert_candidate(
            con,
            obj=obj,
            row=row,
            source_event_id=candidate_source_event_id,
            chunk_id=chunk_id,
            extraction_mode=mode,
        )
        added += int(was_added)
        if chunk_id:
            batch_novel[chunk_id] = batch_novel.get(chunk_id, 0) + int(was_added)
'''


REGRESSIONS = r'''


def test_historical_batch_extractor_replay_counts_original_source_once(tmp_path: Path) -> None:
    con = _con()
    run = tmp_path / "origin-vs-extractor"
    run.mkdir(parents=True)
    path = run / "workers.jsonl"

    original = _worker(
        "old source with hypothesis, test, benchmark and falsifier but no modern marker",
        serial=1,
    )
    path.write_text(json.dumps(original) + "\n", encoding="utf-8")
    bf.ingest_artifact_history(con, tmp_path)
    chunk = con.execute("SELECT chunk_id,source_event_id FROM historical_chunks LIMIT 1").fetchone()
    assert chunk is not None

    p1 = _proposal("historical-origin-pass-1", ready=False)
    p1.update({
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
    })
    batch1 = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 1,
        "exhaustive": False,
        "deltas": [p1],
    }
    extractor1 = _worker("ARCHITECTURE_DELTA_BATCH_JSON=" + json.dumps(batch1), serial=2)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(extractor1) + "\n")
    bf.ingest_artifact_history(con, tmp_path)

    p2 = dict(p1)
    p2["delta_id"] = "historical-origin-pass-2"
    p2["extraction_pass"] = 2
    batch2 = {
        "historical_source_event_id": chunk["source_event_id"],
        "historical_chunk_id": chunk["chunk_id"],
        "extraction_pass": 2,
        "exhaustive": True,
        "deltas": [p2],
    }
    extractor2 = _worker("ARCHITECTURE_DELTA_BATCH_JSON=" + json.dumps(batch2), serial=3)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(extractor2) + "\n")
    bf.ingest_artifact_history(con, tmp_path)

    candidate = con.execute("SELECT candidate_hash,source_count FROM candidates").fetchone()
    assert candidate is not None
    assert int(candidate["source_count"]) == 1
    links = con.execute(
        "SELECT source_event_id,extractor_worker_sha FROM candidate_sources WHERE candidate_hash=?",
        (candidate["candidate_hash"],),
    ).fetchall()
    assert len(links) == 2
    assert {row["source_event_id"] for row in links} == {chunk["source_event_id"]}
    assert len({row["extractor_worker_sha"] for row in links}) == 2
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
    changed = False

    # Source-count replay idempotence may already be fused on newer main. Only
    # replace the predecessor function when its exact hash matches.
    _, _, current_function = function_slice(source_text)
    if not (
        "source_link_added = con.total_changes > before_source_link" in current_function
        or "had_source_event = bool(con.execute(" in current_function
    ):
        observed = hashlib.sha256(current_function.encode("utf-8")).hexdigest()
        if observed != EXPECTED_PRE_IDEMPOTENCE_FUNCTION_SHA256:
            raise SystemExit(
                f"SOURCE_COUNT_FUNCTION_MOVED_FAIL_CLOSED:expected={EXPECTED_PRE_IDEMPOTENCE_FUNCTION_SHA256}:observed={observed}"
            )
        start, end, _ = function_slice(source_text)
        source_text = source_text[:start] + REPLACEMENT + source_text[end:]
        changed = True

    origin_sentinel = "candidate_source_event_id = str(binding[1]) if binding is not None else event_id"
    if origin_sentinel not in source_text:
        count = source_text.count(INGEST_OLD)
        if count != 1:
            raise SystemExit(f"HISTORICAL_ORIGIN_INGEST_ANCHOR_COUNT:{count}")
        source_text = source_text.replace(INGEST_OLD, INGEST_NEW, 1)
        changed = True

    if changed:
        source.write_text(source_text, encoding="utf-8")

    sentinel = "test_historical_batch_extractor_replay_counts_original_source_once"
    if sentinel not in test_text:
        tests.write_text(test_text.rstrip() + REGRESSIONS + "\n", encoding="utf-8")

    print("GO878_ORIGIN_SOURCE_SUPPORT_PATCHED" if changed else "GO878_ORIGIN_SOURCE_SUPPORT_ALREADY_FIXED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
