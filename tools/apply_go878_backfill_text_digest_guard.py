#!/usr/bin/env python3
"""Fail-closed donor patch for historical worker text-digest identity.

Historical ``workers.jsonl`` rows are untrusted evidence input. The current backfill
accepts ``row.text_sha256`` as the hash used by ``source_event_identity`` and by the
candidate provenance path without recomputing the digest from ``row.text``. A stale,
corrupt, or forged claim can therefore split one physical text observation into a
second apparent causal/provenance identity.

This patcher is deliberately successor-dynamic: parallel GO878 work is already
modifying the same backfill file, so it binds to one exact unsafe semantic anchor
instead of a whole-file blob. It refuses to guess if that anchor moved or if an
equivalent guard is already present. Digest mismatches are preserved as bounded
append-only negative evidence before the row is rejected. It adds no provider/model/
network execution and mints no runtime, HCU, J-Space, training, or whole-product credit.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SOURCE_REL = "tools/free_swarm_historical_backfill.py"
TEST_REL = "tests/test_free_swarm_historical_backfill.py"

UNSAFE = '''    text_sha = str(row.get("text_sha256") or sha_text(text))\n    event_id = source_event_identity(row, source_path, line_no, text_sha)\n    proposals, batches = explicit_deltas(text)\n'''

SAFE = '''    computed_text_sha = sha_text(text)\n    claimed_text_sha = str(row.get("text_sha256") or "").strip().lower()\n    if claimed_text_sha and claimed_text_sha != computed_text_sha:\n        # Receipt-provided hashes are evidence claims, never identity authority.\n        # Preserve the exact negative observation, then reject before any event,\n        # chunk, candidate, candidate-source, or batch-progress mutation.\n        con.execute(\n            "CREATE TABLE IF NOT EXISTS backfill_integrity_rejections("\n            "rejection_id TEXT PRIMARY KEY,source_path TEXT NOT NULL,line_no INTEGER NOT NULL,"\n            "reason TEXT NOT NULL,claimed_text_sha256 TEXT NOT NULL,computed_text_sha256 TEXT NOT NULL,"\n            "worker_id TEXT,worker_serial TEXT,observed_at TEXT NOT NULL)"\n        )\n        rejection_id = sha_text(canonical({\n            "source_path": source_path,\n            "line_no": line_no,\n            "reason": "TEXT_SHA256_MISMATCH",\n            "claimed_text_sha256": claimed_text_sha,\n            "computed_text_sha256": computed_text_sha,\n            "worker_id": row.get("worker_id"),\n            "worker_serial": row.get("worker_serial"),\n        }))\n        con.execute(\n            "INSERT OR IGNORE INTO backfill_integrity_rejections("\n            "rejection_id,source_path,line_no,reason,claimed_text_sha256,computed_text_sha256,"\n            "worker_id,worker_serial,observed_at) VALUES(?,?,?,?,?,?,?,?,?)",\n            (rejection_id, source_path, line_no, "TEXT_SHA256_MISMATCH", claimed_text_sha,\n             computed_text_sha, str(row.get("worker_id") or ""),\n             str(row.get("worker_serial") or ""), now()),\n        )\n        return {"successful": 0, "candidates_added": 0, "chunks_added": 0, "batches": 0}\n    # Canonicalize the verified/missing claim so every downstream provenance use\n    # receives the digest of the bytes we actually parsed, not caller spelling.\n    row = dict(row)\n    row["text_sha256"] = computed_text_sha\n    text_sha = computed_text_sha\n    event_id = source_event_identity(row, source_path, line_no, text_sha)\n    proposals, batches = explicit_deltas(text)\n'''

REGRESSION = r'''


def test_worker_text_digest_claim_cannot_mint_false_historical_identity() -> None:
    con = _con()
    text = "ARCHITECTURE_DELTA_JSON=" + json.dumps(_proposal("digest-forged", ready=False))
    row = _worker(text, serial=71)
    row["text_sha256"] = "0" * 64

    result = bf._ingest_worker_row(con, row, "/artifact/run/workers.jsonl", 1)

    assert result["successful"] == 0
    assert con.execute("SELECT COUNT(*) FROM historical_outputs").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM historical_chunks").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM candidate_sources").fetchone()[0] == 0
    rejected = con.execute(\n        "SELECT reason,claimed_text_sha256,computed_text_sha256 FROM backfill_integrity_rejections"\n    ).fetchone()
    assert rejected["reason"] == "TEXT_SHA256_MISMATCH"
    assert rejected["claimed_text_sha256"] == "0" * 64
    assert rejected["computed_text_sha256"] == bf.sha_text(text)


def test_worker_text_digest_missing_claim_uses_observed_text_digest() -> None:
    con = _con()
    text = "ARCHITECTURE_DELTA_JSON=" + json.dumps(_proposal("digest-missing", ready=False))
    row = _worker(text, serial=72)
    del row["text_sha256"]

    result = bf._ingest_worker_row(con, row, "/artifact/run/workers.jsonl", 1)

    assert result["successful"] == 1
    observed = con.execute(
        "SELECT worker_sha,text_sha256 FROM historical_outputs LIMIT 1"
    ).fetchone()
    assert observed["worker_sha"] == bf.sha_text(text)
    assert observed["text_sha256"] == bf.sha_text(text)


def test_worker_text_digest_verified_claim_is_canonicalized_downstream() -> None:
    con = _con()
    text = "ARCHITECTURE_DELTA_JSON=" + json.dumps(_proposal("digest-case", ready=False))
    row = _worker(text, serial=73)
    row["text_sha256"] = row["text_sha256"].upper()

    result = bf._ingest_worker_row(con, row, "/artifact/run/workers.jsonl", 1)

    assert result["successful"] == 1
    expected = bf.sha_text(text)
    source = con.execute(
        "SELECT extractor_worker_sha FROM candidate_sources LIMIT 1"
    ).fetchone()
    assert source["extractor_worker_sha"] == expected
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}_ANCHOR_COUNT_{count}_FAIL_CLOSED")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    source_path = repo / SOURCE_REL
    test_path = repo / TEST_REL

    source = source_path.read_text(encoding="utf-8")
    if "computed_text_sha = sha_text(text)" in source:
        raise SystemExit("BACKFILL_TEXT_DIGEST_GUARD_ALREADY_PRESENT")
    source = replace_once(source, UNSAFE, SAFE, "BACKFILL_TEXT_DIGEST")

    tests = test_path.read_text(encoding="utf-8")
    sentinel = "test_worker_text_digest_claim_cannot_mint_false_historical_identity"
    if sentinel in tests:
        raise SystemExit("BACKFILL_TEXT_DIGEST_REGRESSION_ALREADY_PRESENT")

    source_path.write_text(source, encoding="utf-8")
    test_path.write_text(tests.rstrip() + REGRESSION + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
