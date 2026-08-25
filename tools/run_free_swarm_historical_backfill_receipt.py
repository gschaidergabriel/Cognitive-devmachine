#!/usr/bin/env python3
"""Run the existing FREE-swarm historical backfill to a stable local saturation point.

This runner is deliberately offline: it performs no provider/model/network call. It reuses
`free_swarm_historical_backfill.ingest_artifact_history` and the existing Forge SQLite
authority, then emits a bounded `FREE_SWARM_HISTORICAL_BACKFILL_RECEIPT/v1`.

Saturation here means the append-only workers.jsonl corpus visible to this process has been
consumed through complete newline-terminated records and the recorded backfill offsets equal
the stable file sizes in two consecutive verification rounds. Pending semantic extraction is
reported separately and is never silently promoted to "done".
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_historical_backfill as bf  # noqa: E402
import run_free_evidence_forge as forge  # noqa: E402

SCHEMA = "FREE_SWARM_HISTORICAL_BACKFILL_RECEIPT/v1"


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def scan_workers(root: Path, *, with_sha: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted(root.rglob("workers.jsonl")):
        try:
            st = path.stat()
        except OSError:
            continue
        rel = str(path.relative_to(root))
        row: dict[str, Any] = {
            "path": rel,
            "size_bytes": int(st.st_size),
            "mtime_ns": int(st.st_mtime_ns),
            "inode": int(st.st_ino),
        }
        if with_sha:
            row["sha256"] = sha256_file(path)
        out.append(row)
    return out


def stable_scan(root: Path, attempts: int = 8, delay_s: float = 0.15) -> list[dict[str, Any]]:
    """Return a content-hashed scan set only when metadata is unchanged across hashing."""
    for _ in range(max(1, attempts)):
        before = scan_workers(root, with_sha=False)
        hashed = scan_workers(root, with_sha=True)
        after = scan_workers(root, with_sha=False)
        b = [(x["path"], x["size_bytes"], x["mtime_ns"], x["inode"]) for x in before]
        a = [(x["path"], x["size_bytes"], x["mtime_ns"], x["inode"]) for x in after]
        h = [(x["path"], x["size_bytes"], x["mtime_ns"], x["inode"]) for x in hashed]
        if b == a == h:
            return hashed
        time.sleep(delay_s)
    raise RuntimeError("ARTIFACT_SCAN_SET_NOT_STABLE")


def scalar(con: sqlite3.Connection, sql: str, args: tuple[Any, ...] = ()) -> int:
    row = con.execute(sql, args).fetchone()
    return int(row[0] or 0) if row else 0


def db_counts(con: sqlite3.Connection) -> dict[str, Any]:
    bf.ensure_schema(con)
    return {
        "historical_outputs": scalar(con, "SELECT COUNT(*) FROM historical_outputs"),
        "historical_chunks": scalar(con, "SELECT COUNT(*) FROM historical_chunks"),
        "explicit_candidate_source_links": scalar(con, "SELECT COUNT(*) FROM candidate_sources WHERE extraction_mode='EXPLICIT_WORKER_DELTA'"),
        "batch_candidate_source_links": scalar(con, "SELECT COUNT(*) FROM candidate_sources WHERE extraction_mode='HISTORICAL_BATCH'"),
        "distinct_concepts": scalar(con, "SELECT COUNT(DISTINCT concept_id) FROM candidates WHERE concept_id IS NOT NULL"),
        "distinct_execution_variants": scalar(con, "SELECT COUNT(DISTINCT variant_id) FROM candidates WHERE variant_id IS NOT NULL"),
        "duplicates_superseded": scalar(con, "SELECT COUNT(*) FROM candidates WHERE state='DUPLICATE_SUPERSEDED'"),
        "ready_backlog": scalar(con, "SELECT COUNT(*) FROM candidates WHERE ready=1 AND state='NEW'"),
        "implementation_backlog": scalar(con, "SELECT COUNT(*) FROM candidates WHERE state='NEEDS_IMPLEMENTATION'"),
        "remaining_pending_extraction": scalar(con, "SELECT COUNT(*) FROM historical_chunks WHERE state='PENDING_EXTRACTION'"),
        "saturated_chunks": scalar(con, "SELECT COUNT(*) FROM historical_chunks WHERE state='SATURATED'"),
    }


def offsets_match_scan(con: sqlite3.Connection, artifact_root: Path, scan: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    mismatches: list[dict[str, Any]] = []
    scan_paths = {str((artifact_root / row["path"]).resolve()): row for row in scan}
    for full_path, row in scan_paths.items():
        saved = con.execute(
            "SELECT inode,byte_offset,file_size FROM backfill_files WHERE source_path=?",
            (full_path,),
        ).fetchone()
        if not saved:
            mismatches.append({"path": row["path"], "reason": "NO_BACKFILL_OFFSET"})
            continue
        inode, offset, recorded_size = int(saved[0]), int(saved[1]), int(saved[2])
        expected_size = int(row["size_bytes"])
        if inode != int(row["inode"]) or offset != expected_size or recorded_size != expected_size:
            mismatches.append({
                "path": row["path"],
                "reason": "OFFSET_OR_INODE_MISMATCH",
                "expected_inode": int(row["inode"]),
                "observed_inode": inode,
                "expected_size": expected_size,
                "observed_offset": offset,
                "recorded_file_size": recorded_size,
            })
    db_paths = {str(r[0]) for r in con.execute("SELECT source_path FROM backfill_files")}
    extras = sorted(db_paths - set(scan_paths))
    # Historical removed/rotated paths remain provenance and are not a saturation failure.
    return not mismatches, [{"historical_db_only_path": x} for x in extras] + mismatches


def delta(after: dict[str, Any], before: dict[str, Any], key: str) -> int:
    return int(after.get(key, 0)) - int(before.get(key, 0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", type=Path, default=forge.ARTIFACT_ROOT)
    ap.add_argument("--db", type=Path, default=forge.DB_PATH)
    ap.add_argument("--max-lines-per-pass", type=int, default=50_000)
    ap.add_argument("--max-passes", type=int, default=64)
    ap.add_argument("--stable-zero-rounds", type=int, default=2)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()

    artifact_root = args.artifact_root.resolve()
    db_path = args.db.resolve()
    if not artifact_root.is_dir():
        raise SystemExit(f"ARTIFACT_ROOT_REQUIRED:{artifact_root}")
    initial_scan = stable_scan(artifact_root)
    if not initial_scan:
        raise SystemExit("WORKERS_JSONL_SCAN_SET_REQUIRED")
    if not db_path.exists():
        raise SystemExit(f"FORGE_DB_REQUIRED:{db_path}")

    started_at = utcnow()
    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    dirty = bool(git_text("status", "--porcelain"))
    source_files = {}
    for rel in (
        "tools/free_swarm_historical_backfill.py",
        "tools/run_free_evidence_forge_backfill.py",
        "tools/run_free_evidence_forge_safe.py",
        "tools/run_free_swarm_historical_backfill_receipt.py",
        "tests/test_free_swarm_historical_backfill.py",
    ):
        p = ROOT / rel
        if p.exists():
            source_files[rel] = sha256_file(p)

    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    bf.ensure_schema(con)
    before = db_counts(con)

    accumulated = {
        "passes": 0,
        "lines_scanned": 0,
        "successful_outputs_observed": 0,
        "candidate_variants_added": 0,
        "chunks_added": 0,
        "batch_envelopes_seen": 0,
    }
    zero_rounds = 0
    final_scan: list[dict[str, Any]] = []
    offset_evidence: list[dict[str, Any]] = []
    for _ in range(max(1, args.max_passes)):
        stats = bf.ingest_artifact_history(
            con,
            artifact_root,
            max_new_lines=max(1, args.max_lines_per_pass),
        )
        accumulated["passes"] += 1
        accumulated["lines_scanned"] += int(stats.get("lines_seen", 0))
        accumulated["successful_outputs_observed"] += int(stats.get("successful_outputs", 0))
        accumulated["candidate_variants_added"] += int(stats.get("candidate_variants_added", 0))
        accumulated["chunks_added"] += int(stats.get("chunks_added", 0))
        accumulated["batch_envelopes_seen"] += int(stats.get("batches_seen", 0))

        scan = stable_scan(artifact_root)
        offsets_ok, offset_evidence = offsets_match_scan(con, artifact_root, scan)
        if int(stats.get("lines_seen", 0)) == 0 and offsets_ok:
            zero_rounds += 1
        else:
            zero_rounds = 0
        final_scan = scan
        if zero_rounds >= max(1, args.stable_zero_rounds):
            break
    else:
        con.close()
        raise SystemExit("HISTORICAL_BACKFILL_DID_NOT_REACH_STABLE_EOF")

    after = db_counts(con)
    final_offsets_ok, offset_evidence = offsets_match_scan(con, artifact_root, final_scan)
    con.close()
    if not final_offsets_ok:
        raise SystemExit("FINAL_BACKFILL_OFFSETS_NOT_AT_STABLE_EOF")

    receipt = {
        "schema": SCHEMA,
        "created_at": utcnow(),
        "started_at": started_at,
        "status": "PASS_STABLE_EOF",
        "scope": "historical workers.jsonl ingestion/dedupe/backlog materialization only; pending semantic extraction remains explicit",
        "source_identity": {
            "commit": head,
            "tree": tree,
            "dirty": dirty,
            "source_file_sha256": source_files,
        },
        "artifact_root": str(artifact_root),
        "forge_db": str(db_path),
        "initial_artifact_root_scan_set": initial_scan,
        "final_artifact_root_scan_set": final_scan,
        "stable_zero_rounds": zero_rounds,
        "backfill_execution": accumulated,
        "before": before,
        "after": after,
        "recovered": {
            "historical_outputs": delta(after, before, "historical_outputs"),
            "explicit_delta_source_links": delta(after, before, "explicit_candidate_source_links"),
            "batch_delta_source_links": delta(after, before, "batch_candidate_source_links"),
            "new_concepts": delta(after, before, "distinct_concepts"),
            "new_execution_variants": delta(after, before, "distinct_execution_variants"),
            "new_duplicates_superseded": delta(after, before, "duplicates_superseded"),
        },
        "backlog": {
            "ready": after["ready_backlog"],
            "needs_implementation": after["implementation_backlog"],
            "remaining_pending_extraction": after["remaining_pending_extraction"],
            "saturated_chunks": after["saturated_chunks"],
        },
        "offset_verification": {
            "all_current_scan_files_at_stable_eof": True,
            "details": offset_evidence,
        },
        "goodman_evidence_family_preserved": True,
        "historical_replay_creates_new_independent_execution_credit": False,
        "external_provider_calls": 0,
        "external_model_calls": 0,
        "network_required": False,
        "runtime_credit_added": 0,
        "whole_entityos_hcu_credit_added": 0,
        "jspace_model_credit_added": 0,
        "training_credit_added": 0,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "lines_scanned": accumulated["lines_scanned"],
        "historical_outputs_recovered": receipt["recovered"]["historical_outputs"],
        "new_execution_variants": receipt["recovered"]["new_execution_variants"],
        "ready_backlog": receipt["backlog"]["ready"],
        "implementation_backlog": receipt["backlog"]["needs_implementation"],
        "remaining_pending_extraction": receipt["backlog"]["remaining_pending_extraction"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
