#!/usr/bin/env python3
"""Exact-source, provider-free historical Free-Swarm backfill runtime capsule.

This capsule is intentionally narrower than the long-lived Evidence Forge. It only
replays existing workers.jsonl history into the existing Forge SQLite authority via
free_swarm_historical_backfill, repeats incremental ingestion until the bounded scan
set is cursor-saturated, and emits a machine-readable receipt. It makes no provider,
model, web, paid, Together, canonical-effect, or training call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_free_evidence_forge as forge  # noqa: E402
import free_swarm_historical_backfill as historical_backfill_core  # noqa: E402
from free_swarm_backfill_exhaustiveness_878 import install as install_exhaustiveness  # noqa: E402

# The exact-source provider-free capsule mutates the same historical backfill state as
# the live Forge and scheduler. Install the shared completion policy before binding any
# mutation-capable helpers so one chunk cannot receive path-dependent saturation state.
install_exhaustiveness(historical_backfill_core)
backfill_metrics = historical_backfill_core.backfill_metrics
ensure_schema = historical_backfill_core.ensure_schema
ingest_artifact_history = historical_backfill_core.ingest_artifact_history

SCHEMA = "FREE_SWARM_HISTORICAL_BACKFILL_RECEIPT/v1"
PASS_STATUS = "PASS_FULL_HISTORICAL_SATURATION"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def candidate_state(con: sqlite3.Connection) -> dict[str, int]:
    rows = con.execute("SELECT state, COUNT(*) FROM candidates GROUP BY state").fetchall()
    out = {str(row[0]): int(row[1]) for row in rows}
    out["READY_BACKLOG"] = int(
        con.execute("SELECT COUNT(*) FROM candidates WHERE ready=1 AND state='NEW'").fetchone()[0]
    )
    out["IMPLEMENTATION_BACKLOG"] = int(
        con.execute("SELECT COUNT(*) FROM candidates WHERE state='NEEDS_IMPLEMENTATION'").fetchone()[0]
    )
    return out


def extraction_mode_counts(con: sqlite3.Connection) -> dict[str, int]:
    rows = con.execute(
        "SELECT COALESCE(extraction_mode,'UNCLASSIFIED'), COUNT(*) FROM candidates GROUP BY COALESCE(extraction_mode,'UNCLASSIFIED')"
    ).fetchall()
    return {str(row[0]): int(row[1]) for row in rows}


def bounded_scan_manifest(con: sqlite3.Connection, artifact_root: Path) -> tuple[list[dict[str, Any]], bool]:
    entries: list[dict[str, Any]] = []
    saturated = True
    for path in sorted(artifact_root.rglob("workers.jsonl")):
        try:
            before = path.stat()
            digest = sha256_file(path)
            after = path.stat()
        except OSError:
            saturated = False
            continue
        stable = (
            int(before.st_ino) == int(after.st_ino)
            and int(before.st_size) == int(after.st_size)
            and int(before.st_mtime_ns) == int(after.st_mtime_ns)
        )
        cursor = con.execute(
            "SELECT inode, byte_offset, file_size FROM backfill_files WHERE source_path=?",
            (str(path),),
        ).fetchone()
        cursor_inode = int(cursor[0]) if cursor and cursor[0] is not None else None
        cursor_offset = int(cursor[1]) if cursor else None
        cursor_file_size = int(cursor[2]) if cursor else None
        complete = bool(
            stable
            and cursor
            and cursor_inode == int(after.st_ino)
            and cursor_offset == int(after.st_size)
            and cursor_file_size == int(after.st_size)
        )
        saturated = saturated and complete
        entries.append({
            "path": path.relative_to(artifact_root).as_posix(),
            "inode": int(after.st_ino),
            "size": int(after.st_size),
            "mtime_ns": int(after.st_mtime_ns),
            "sha256": digest,
            "cursor_offset": cursor_offset,
            "cursor_file_size": cursor_file_size,
            "cursor_complete": complete,
        })
    if not entries:
        saturated = False
    return entries, saturated


def classify_full_saturation(
    metrics: dict[str, Any],
    consecutive_zero_scan_passes: int,
    manifest_saturated: bool,
) -> str:
    """Return a terminal fail-closed status for the historical-backfill receipt.

    Cursor saturation proves only that the bounded workers.jsonl scan stopped moving.
    It does not prove that semantic extraction completed. Runtime PASS additionally
    requires every admitted historical chunk to have reached the explicit SATURATED
    state under the shared two-confirmation policy, with no pending or max-pass stall.
    """
    if consecutive_zero_scan_passes < 2 or not manifest_saturated:
        return "FAIL_SCAN_SET_NOT_SATURATED"

    states_raw = metrics.get("chunk_states")
    states = states_raw if isinstance(states_raw, dict) else {}
    chunks = int(metrics.get("historical_chunks", 0) or 0)
    pending = int(metrics.get("pending_extraction", 0) or 0)
    max_passes_reached = int(states.get("MAX_PASSES_REACHED", 0) or 0)
    saturated = int(states.get("SATURATED", 0) or 0)

    if chunks <= 0:
        return "FAIL_NO_HISTORICAL_CHUNKS"
    if pending > 0:
        return "FAIL_PENDING_EXTRACTION"
    if max_passes_reached > 0:
        return "FAIL_MAX_PASSES_REACHED"
    if saturated != chunks:
        return "FAIL_CHUNK_STATE_NOT_SATURATED"
    return PASS_STATUS


def authority_snapshot() -> dict[str, Any]:
    inbox_path = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = json.loads(inbox_path.read_text(encoding="utf-8"))
    steering_rel = inbox.get("steering")
    if not isinstance(steering_rel, str) or not steering_rel:
        raise RuntimeError("SUPERVISOR_STEERING_REQUIRED")
    steering_path = ROOT / steering_rel
    steering = json.loads(steering_path.read_text(encoding="utf-8"))
    inbox_epoch = str(inbox.get("schema_version") or "")
    steering_epoch = str(steering.get("schema_version") or "")
    if inbox_epoch != steering_epoch:
        raise RuntimeError(f"SUPERVISOR_EPOCH_MISMATCH:{inbox_epoch}:{steering_epoch}")
    if steering.get("product") != "EntityOS":
        raise RuntimeError("ENTITYOS_AUTHORITY_REQUIRED")
    if steering.get("integrated_cognition_compute_architecture") != "HCU":
        raise RuntimeError("HCU_AUTHORITY_REQUIRED")
    mode = steering.get("mode")
    authority = steering.get("authority") if isinstance(steering.get("authority"), dict) else {}
    free_only = mode == "FREE_ONLY" or authority.get("free_only") is True
    if not free_only:
        raise RuntimeError("FREE_ONLY_REQUIRED")
    return {
        "authority_epoch": inbox_epoch,
        "inbox_path": inbox_path.relative_to(ROOT).as_posix(),
        "steering_path": steering_path.relative_to(ROOT).as_posix(),
        "inbox_sha256": sha256_file(inbox_path),
        "steering_sha256": sha256_file(steering_path),
        "free_only": True,
    }


def delta(after: dict[str, int], before: dict[str, int], key: str) -> int:
    return int(after.get(key, 0)) - int(before.get(key, 0))


def run(artifact_root: Path, max_lines: int, max_passes: int) -> dict[str, Any]:
    if not artifact_root.is_dir():
        raise RuntimeError(f"ARTIFACT_ROOT_REQUIRED:{artifact_root}")
    authority = authority_snapshot()
    con = forge.connect()
    ensure_schema(con)
    before_metrics = backfill_metrics(con)
    before_states = candidate_state(con)
    before_modes = extraction_mode_counts(con)

    totals = {
        "passes": 0,
        "lines_scanned": 0,
        "successful_outputs": 0,
        "candidate_variants_added": 0,
        "chunks_added": 0,
        "batches_seen": 0,
    }
    consecutive_zero = 0
    final_manifest: list[dict[str, Any]] = []
    manifest_saturated = False

    for _ in range(max(1, max_passes)):
        stats = ingest_artifact_history(con, artifact_root, max_new_lines=max_lines)
        totals["passes"] += 1
        totals["lines_scanned"] += int(stats.get("lines_seen", 0))
        totals["successful_outputs"] += int(stats.get("successful_outputs", 0))
        totals["candidate_variants_added"] += int(stats.get("candidate_variants_added", 0))
        totals["chunks_added"] += int(stats.get("chunks_added", 0))
        totals["batches_seen"] += int(stats.get("batches_seen", 0))
        final_manifest, manifest_saturated = bounded_scan_manifest(con, artifact_root)
        if int(stats.get("lines_seen", 0)) == 0 and manifest_saturated:
            consecutive_zero += 1
        else:
            consecutive_zero = 0
        if consecutive_zero >= 2:
            break

    after_metrics = backfill_metrics(con)
    after_states = candidate_state(con)
    after_modes = extraction_mode_counts(con)
    con.commit()
    con.close()

    source_sha = os.environ.get("CLAY_GO878_SOURCE_SHA", "")
    source_tree = os.environ.get("CLAY_GO878_SOURCE_TREE", "")
    dirty = os.environ.get("CLAY_GO878_DIRTY_STATE", "UNKNOWN")
    status = classify_full_saturation(after_metrics, consecutive_zero, manifest_saturated)
    chunk_states = after_metrics.get("chunk_states") if isinstance(after_metrics.get("chunk_states"), dict) else {}
    semantic_saturated = status == PASS_STATUS

    receipt = {
        "schema": SCHEMA,
        "status": status,
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "authority": authority,
        "source": {
            "commit": source_sha or None,
            "tree": source_tree or None,
            "dirty_state": dirty,
            "capsule_path": "tools/run_free_swarm_historical_backfill_capsule_878.py",
            "capsule_sha256": sha256_file(Path(__file__)),
        },
        "execution": {
            "transport": os.environ.get("CLAY_GO878_TRANSPORT", "UNKNOWN"),
            "sandbox": os.environ.get("CLAY_GO878_SANDBOX", "UNKNOWN"),
            "run_id": os.environ.get("CLAY_GO878_RUN_ID") or None,
            "artifact_root": str(artifact_root),
            "forge_db": str(forge.DB_PATH),
            "provider_model_network_io": False,
            "paid_provider_io": False,
            "together_io": False,
            "canonical_effects": False,
        },
        "scan": {
            **totals,
            "scan_set_files": len(final_manifest),
            "scan_set_manifest_sha256": sha256_json(final_manifest),
            "scan_set": final_manifest,
            "consecutive_zero_line_saturated_passes": consecutive_zero,
            "cursor_saturated_for_manifest": manifest_saturated,
            "semantic_chunk_saturation": semantic_saturated,
            "chunk_states": chunk_states,
        },
        "recovery": {
            "explicit_deltas_recovered": delta(after_modes, before_modes, "EXPLICIT_WORKER_DELTA"),
            "batch_deltas_recovered": delta(after_modes, before_modes, "HISTORICAL_BATCH"),
            "new_concepts": int(after_metrics.get("distinct_concepts", 0)) - int(before_metrics.get("distinct_concepts", 0)),
            "new_execution_variants": int(after_metrics.get("distinct_execution_variants", 0)) - int(before_metrics.get("distinct_execution_variants", 0)),
            "duplicates_superseded": int(after_states.get("DUPLICATE_SUPERSEDED", 0)),
            "ready_backlog": int(after_states.get("READY_BACKLOG", 0)),
            "implementation_backlog": int(after_states.get("IMPLEMENTATION_BACKLOG", 0)),
            "remaining_pending_extraction": int(after_metrics.get("pending_extraction", 0)),
            "max_passes_reached": int(chunk_states.get("MAX_PASSES_REACHED", 0) or 0),
            "saturated_chunks": int(chunk_states.get("SATURATED", 0) or 0),
            "historical_chunks": int(after_metrics.get("historical_chunks", 0) or 0),
        },
        "before": {
            "backfill": before_metrics,
            "candidate_states": before_states,
            "extraction_modes": before_modes,
        },
        "after": {
            "backfill": after_metrics,
            "candidate_states": after_states,
            "extraction_modes": after_modes,
        },
        "credit": {
            "scope": "HISTORICAL_BACKFILL_INGEST_COMPONENT_ONLY",
            "historical_backfill_runtime_credit": 1 if status == PASS_STATUS else 0,
            "whole_entityos_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
            "canonical_semantics_promotion": False,
        },
        "note": "Cursor saturation alone is not semantic extraction saturation. PASS requires every admitted historical chunk to be SATURATED under the shared explicit-exhaustiveness policy; pending/max-pass/other chunk states fail closed. Historical replay preserves execution provenance; deduplicated repackaging is not independent evidence.",
    }
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", type=Path, default=Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm")))
    ap.add_argument("--max-lines-per-pass", type=int, default=50000)
    ap.add_argument("--max-passes", type=int, default=64)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()
    receipt = run(args.artifact_root.resolve(), max(1, args.max_lines_per_pass), max(1, args.max_passes))
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "lines_scanned": receipt["scan"]["lines_scanned"],
        "successful_outputs": receipt["scan"]["successful_outputs"],
        "new_execution_variants": receipt["recovery"]["new_execution_variants"],
        "remaining_pending_extraction": receipt["recovery"]["remaining_pending_extraction"],
        "max_passes_reached": receipt["recovery"]["max_passes_reached"],
        "saturated_chunks": receipt["recovery"]["saturated_chunks"],
        "historical_chunks": receipt["recovery"]["historical_chunks"],
        "scan_set_manifest_sha256": receipt["scan"]["scan_set_manifest_sha256"],
    }, sort_keys=True))
    return 0 if receipt["status"] == PASS_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
