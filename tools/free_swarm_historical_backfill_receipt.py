#!/usr/bin/env python3
"""Exact-source receipt for the FREE Swarm historical Forge backfill.

The backfill itself lives in ``free_swarm_historical_backfill.py`` and remains the
single historical replay/admission implementation.  This tool does not create a
second Forge authority.  It runs that existing incremental scanner to a bounded
quiescent point, then records whether the *currently visible* historical artifact
set is fully scanned and whether every extracted chunk is SATURATED.

A PASS is deliberately strict.  Source must be clean, the artifact set must stay
stable while the receipt is measured, every visible workers.jsonl must be caught
up to its current byte size, at least one successful historical output must exist,
and no PENDING_EXTRACTION or MAX_PASSES_REACHED chunks may remain.  Anything else
is a bounded BLOCKED result, not runtime/model/training credit.
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
from typing import Any

import free_swarm_historical_backfill as backfill

SCHEMA = "FREE_SWARM_HISTORICAL_BACKFILL_RECEIPT/v1"
SCOPE = "FREE_SWARM_HISTORICAL_BACKFILL_SATURATION_ONLY"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_text(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
    )
    return proc.stdout.strip()


def source_identity(repo: Path) -> dict[str, Any]:
    head = git_text(repo, "rev-parse", "HEAD")
    tree = git_text(repo, "rev-parse", "HEAD^{tree}")
    status = git_text(repo, "status", "--porcelain", "--untracked-files=no")
    source_files = [
        repo / "tools/free_swarm_historical_backfill.py",
        Path(__file__).resolve(),
        repo / "tools/run_free_evidence_forge_backfill.py",
        repo / "tools/run_free_evidence_forge_safe.py",
    ]
    hashes: dict[str, str | None] = {}
    for path in source_files:
        try:
            rel = path.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError:
            rel = str(path.resolve())
        hashes[rel] = sha256_file(path) if path.exists() and path.is_file() else None
    return {
        "commit": head,
        "tree": tree,
        "dirty": bool(status),
        "tracked_status": status or None,
        "source_file_sha256": hashes,
    }


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def scalar(con: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    row = con.execute(sql, params).fetchone()
    return int(row[0] or 0) if row else 0


def db_snapshot(con: sqlite3.Connection) -> dict[str, Any]:
    required = {
        "candidates",
        "historical_outputs",
        "historical_chunks",
        "candidate_sources",
        "backfill_files",
    }
    missing = sorted(name for name in required if not table_exists(con, name))
    if missing:
        return {"schema_ready": False, "missing_tables": missing}

    chunk_states = {
        str(row[0]): int(row[1])
        for row in con.execute(
            "SELECT state,COUNT(*) FROM historical_chunks GROUP BY state ORDER BY state"
        )
    }
    extraction_modes = {
        str(row[0]): int(row[1])
        for row in con.execute(
            "SELECT extraction_mode,COUNT(DISTINCT candidate_hash) "
            "FROM candidate_sources GROUP BY extraction_mode ORDER BY extraction_mode"
        )
    }
    extraction_observations = {
        str(row[0]): int(row[1])
        for row in con.execute(
            "SELECT extraction_mode,COUNT(*) FROM candidate_sources "
            "GROUP BY extraction_mode ORDER BY extraction_mode"
        )
    }
    return {
        "schema_ready": True,
        "historical_outputs": scalar(con, "SELECT COUNT(*) FROM historical_outputs"),
        "historical_chunks": scalar(con, "SELECT COUNT(*) FROM historical_chunks"),
        "chunk_states": chunk_states,
        "candidate_source_links": scalar(con, "SELECT COUNT(*) FROM candidate_sources"),
        "distinct_concepts": scalar(
            con, "SELECT COUNT(DISTINCT concept_id) FROM candidates WHERE concept_id IS NOT NULL"
        ),
        "distinct_execution_variants": scalar(
            con, "SELECT COUNT(DISTINCT variant_id) FROM candidates WHERE variant_id IS NOT NULL"
        ),
        "duplicates_superseded": scalar(
            con, "SELECT COUNT(*) FROM candidates WHERE state='DUPLICATE_SUPERSEDED'"
        ),
        "ready_backlog": scalar(
            con, "SELECT COUNT(*) FROM candidates WHERE ready=1 AND state='NEW'"
        ),
        "implementation_backlog": scalar(
            con, "SELECT COUNT(*) FROM candidates WHERE state='NEEDS_IMPLEMENTATION'"
        ),
        "remaining_pending_extraction": int(chunk_states.get("PENDING_EXTRACTION", 0)),
        "max_passes_reached": int(chunk_states.get("MAX_PASSES_REACHED", 0)),
        "saturated_chunks": int(chunk_states.get("SATURATED", 0)),
        "explicit_deltas_recovered": int(extraction_modes.get("EXPLICIT_WORKER_DELTA", 0)),
        "batch_deltas_recovered": int(extraction_modes.get("HISTORICAL_BATCH", 0)),
        "extraction_mode_unique_variants": extraction_modes,
        "extraction_mode_observations": extraction_observations,
    }


def _tracked_offsets(con: sqlite3.Connection) -> dict[str, dict[str, int | None]]:
    if not table_exists(con, "backfill_files"):
        return {}
    out: dict[str, dict[str, int | None]] = {}
    for row in con.execute(
        "SELECT source_path,inode,byte_offset,file_size FROM backfill_files ORDER BY source_path"
    ):
        out[str(row[0])] = {
            "inode": int(row[1]) if row[1] is not None else None,
            "byte_offset": int(row[2] or 0),
            "recorded_file_size": int(row[3] or 0),
        }
    return out


def artifact_scan_state(con: sqlite3.Connection, artifact_root: Path) -> dict[str, Any]:
    tracked = _tracked_offsets(con)
    rows: list[dict[str, Any]] = []
    visible = sorted(p for p in artifact_root.rglob("workers.jsonl") if p.is_file()) if artifact_root.exists() else []
    for path in visible:
        st = path.stat()
        key = str(path)
        prior = tracked.get(key) or {}
        offset = int(prior.get("byte_offset") or 0)
        inode = prior.get("inode")
        inode_matches = inode is not None and int(inode) == int(st.st_ino)
        caught_up = bool(inode_matches and offset >= int(st.st_size))
        try:
            rel = path.relative_to(artifact_root).as_posix()
        except ValueError:
            rel = key
        rows.append(
            {
                "path": rel,
                "size": int(st.st_size),
                "mtime_ns": int(st.st_mtime_ns),
                "inode": int(st.st_ino),
                "tracked_inode": int(inode) if inode is not None else None,
                "tracked_byte_offset": offset,
                "caught_up": caught_up,
            }
        )
    identity_rows = [
        {
            "path": row["path"],
            "size": row["size"],
            "mtime_ns": row["mtime_ns"],
            "inode": row["inode"],
            "tracked_inode": row["tracked_inode"],
            "tracked_byte_offset": row["tracked_byte_offset"],
        }
        for row in rows
    ]
    return {
        "artifact_root": str(artifact_root),
        "visible_workers_jsonl": len(rows),
        "caught_up_files": sum(int(bool(row["caught_up"])) for row in rows),
        "uncaught_up_files": sum(int(not bool(row["caught_up"])) for row in rows),
        "scan_set": rows,
        "scan_set_identity_sha256": sha256_bytes(canonical_json(identity_rows)),
    }


def run_incremental_scan(
    con: sqlite3.Connection,
    artifact_root: Path,
    *,
    max_rounds: int,
    max_new_lines_per_round: int,
) -> list[dict[str, int]]:
    rounds: list[dict[str, int]] = []
    for _ in range(max(1, max_rounds)):
        stats = backfill.ingest_artifact_history(
            con,
            artifact_root,
            max_new_lines=max(1, max_new_lines_per_round),
        )
        rounds.append({str(k): int(v) for k, v in stats.items()})
        if int(stats.get("lines_seen", 0)) == 0:
            break
    return rounds


def delta(after: dict[str, Any], before: dict[str, Any], key: str) -> int | None:
    a = after.get(key)
    b = before.get(key)
    if isinstance(a, int) and isinstance(b, int):
        return a - b
    return None


def classify(
    *,
    source: dict[str, Any],
    scan_before: dict[str, Any],
    scan_after: dict[str, Any],
    db_after: dict[str, Any],
    rounds: list[dict[str, int]],
) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if source.get("dirty"):
        blockers.append("DIRTY_SOURCE")
    if not db_after.get("schema_ready"):
        blockers.append("FORGE_BACKFILL_SCHEMA_NOT_READY")
    if scan_after.get("visible_workers_jsonl", 0) <= 0:
        blockers.append("NO_VISIBLE_WORKERS_JSONL")
    if scan_before.get("scan_set_identity_sha256") != scan_after.get("scan_set_identity_sha256"):
        blockers.append("ARTIFACT_SET_CHANGED_DURING_RECEIPT")
    if int(scan_after.get("uncaught_up_files", 0) or 0) > 0:
        blockers.append("HISTORICAL_SCAN_NOT_CAUGHT_UP")
    if rounds and int(rounds[-1].get("lines_seen", 0)) != 0:
        blockers.append("NO_QUIESCENT_SCAN_ROUND_OBSERVED")
    if int(db_after.get("historical_outputs", 0) or 0) <= 0:
        blockers.append("NO_SUCCESSFUL_HISTORICAL_OUTPUTS")
    if int(db_after.get("remaining_pending_extraction", 0) or 0) > 0:
        blockers.append("PENDING_EXTRACTION_REMAINS")
    if int(db_after.get("max_passes_reached", 0) or 0) > 0:
        blockers.append("MAX_PASSES_REACHED_UNRESOLVED")
    return ("PASS", []) if not blockers else ("BLOCKED", blockers)


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def build_receipt(
    repo: Path,
    artifact_root: Path,
    forge_db: Path,
    *,
    max_rounds: int,
    max_new_lines_per_round: int,
) -> dict[str, Any]:
    if not forge_db.exists():
        return {
            "schema": SCHEMA,
            "generated_at": utc_now(),
            "status": "BLOCKED",
            "blockers": ["FORGE_DB_MISSING"],
            "repo": str(repo),
            "artifact_root": str(artifact_root),
            "forge_db": str(forge_db),
            "scope": SCOPE,
            "runtime_credit_added": 0,
            "model_credit_added": 0,
            "training_credit_added": 0,
        }

    source_before = source_identity(repo)
    con = sqlite3.connect(str(forge_db), timeout=30)
    con.row_factory = sqlite3.Row
    try:
        if not table_exists(con, "candidates"):
            return {
                "schema": SCHEMA,
                "generated_at": utc_now(),
                "status": "BLOCKED",
                "blockers": ["FORGE_CANDIDATES_TABLE_MISSING"],
                "source": source_before,
                "repo": str(repo),
                "artifact_root": str(artifact_root),
                "forge_db": str(forge_db),
                "scope": SCOPE,
                "runtime_credit_added": 0,
                "model_credit_added": 0,
                "training_credit_added": 0,
            }

        backfill.ensure_schema(con)
        before = db_snapshot(con)
        scan_before = artifact_scan_state(con, artifact_root)
        rounds = run_incremental_scan(
            con,
            artifact_root,
            max_rounds=max_rounds,
            max_new_lines_per_round=max_new_lines_per_round,
        )
        after = db_snapshot(con)
        scan_after = artifact_scan_state(con, artifact_root)
    finally:
        con.close()

    source_after = source_identity(repo)
    source_stable = source_before == source_after
    if not source_stable:
        source_after = dict(source_after)
        source_after["changed_during_receipt"] = True

    status, blockers = classify(
        source=source_after,
        scan_before=scan_before,
        scan_after=scan_after,
        db_after=after,
        rounds=rounds,
    )
    if not source_stable:
        status = "BLOCKED"
        blockers = [*blockers, "SOURCE_CHANGED_DURING_RECEIPT"]

    lines_scanned = sum(int(row.get("lines_seen", 0)) for row in rounds)
    successful_outputs_observed = sum(int(row.get("successful_outputs", 0)) for row in rounds)
    explicit_new = delta(after, before, "explicit_deltas_recovered")
    batch_new = delta(after, before, "batch_deltas_recovered")
    concepts_new = delta(after, before, "distinct_concepts")
    variants_new = delta(after, before, "distinct_execution_variants")
    duplicates_new = delta(after, before, "duplicates_superseded")

    receipt = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "status": status,
        "blockers": blockers,
        "authority_epoch_expected": "8.78",
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "source": source_after,
        "artifact_root": str(artifact_root),
        "forge_db": str(forge_db),
        "artifact_root_scan_set": scan_after,
        "scan_set_stable_during_receipt": (
            scan_before.get("scan_set_identity_sha256") == scan_after.get("scan_set_identity_sha256")
        ),
        "incremental_scan_rounds": rounds,
        "lines_scanned": lines_scanned,
        "successful_outputs": successful_outputs_observed,
        "successful_outputs_total": after.get("historical_outputs"),
        "explicit_deltas_recovered": explicit_new,
        "explicit_deltas_recovered_total": after.get("explicit_deltas_recovered"),
        "batch_deltas_recovered": batch_new,
        "batch_deltas_recovered_total": after.get("batch_deltas_recovered"),
        "new_concepts": concepts_new,
        "distinct_concepts_total": after.get("distinct_concepts"),
        "new_execution_variants": variants_new,
        "distinct_execution_variants_total": after.get("distinct_execution_variants"),
        "duplicates_superseded": duplicates_new,
        "duplicates_superseded_total": after.get("duplicates_superseded"),
        "ready_backlog": after.get("ready_backlog"),
        "implementation_backlog": after.get("implementation_backlog"),
        "remaining_pending_extraction": after.get("remaining_pending_extraction"),
        "max_passes_reached_unresolved": after.get("max_passes_reached"),
        "saturated_chunks": after.get("saturated_chunks"),
        "before": before,
        "after": after,
        "scope": SCOPE,
        "runtime_credit_added": 0,
        "model_credit_added": 0,
        "training_credit_added": 0,
        "evidence_note": (
            "PASS establishes only exact-source historical backfill scan/extraction saturation at this bounded artifact/DB identity. "
            "It does not establish whole EntityOS/HCU, J-Space model, provider, or training acceptance."
        ),
    }
    receipt["receipt_digest_sha256"] = sha256_bytes(canonical_json(receipt))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--artifact-root", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    parser.add_argument("--forge-db", type=Path, default=None)
    parser.add_argument("--max-rounds", type=int, default=64)
    parser.add_argument("--max-new-lines-per-round", type=int, default=50_000)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    repo = args.repo.resolve()
    artifact_root = args.artifact_root.resolve()
    forge_db = (args.forge_db or (artifact_root / "forge/forge.sqlite3")).resolve()
    output = args.output or (
        repo / "research_entity/continuity/receipts/FREE_SWARM_HISTORICAL_BACKFILL_RECEIPT_V1.json"
    )
    receipt = build_receipt(
        repo,
        artifact_root,
        forge_db,
        max_rounds=max(1, args.max_rounds),
        max_new_lines_per_round=max(1, args.max_new_lines_per_round),
    )
    atomic_json(output, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
