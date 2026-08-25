#!/usr/bin/env python3
"""Fail-closed exact-source receipt for the FREE Swarm historical Forge backfill.

The historical replay implementation remains ``free_swarm_historical_backfill.py``.
This tool creates no second Forge authority.  It runs that existing incremental
scanner to a bounded quiescent point and then measures whether every workers.jsonl
visible at the beginning of the run has been scanned through its exact byte cutoff
and whether the shared Forge DB has no unresolved historical extraction chunks.

The receipt is deliberately scoped.  A PASS proves only historical backfill
scan/extraction saturation for the bound source/authority/artifact-cutoff/Forge-DB
state.  It grants zero whole-EntityOS, HCU, J-Space model, provider or training
credit.  Appends/new files after the cutoff are reported but do not rewrite the
identity of the bounded historical set.
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
CUTOFF_SCHEMA = "FREE_SWARM_HISTORICAL_SCAN_CUTOFF/v1"
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


def read_json_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return value, raw


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


def authority_identity(repo: Path) -> dict[str, Any]:
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox, inbox_raw = read_json_bytes(inbox_path)
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_rel = inbox.get("steering")
    if not epoch or not isinstance(steering_rel, str) or not steering_rel.strip():
        raise RuntimeError("SUPERVISOR_INBOX_AUTHORITY_REQUIRED")
    steering_path = repo / steering_rel
    steering, steering_raw = read_json_bytes(steering_path)
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise RuntimeError("SUPERVISOR_EPOCH_MISMATCH")
    if steering.get("program") != "ENTITYOS_HCU":
        raise RuntimeError("SUPERVISOR_PROGRAM_MISMATCH")
    if steering.get("product") != "EntityOS":
        raise RuntimeError("SUPERVISOR_PRODUCT_MISMATCH")
    if steering.get("integrated_cognition_compute_architecture") != "HCU":
        raise RuntimeError("SUPERVISOR_ARCHITECTURE_MISMATCH")
    mode = str(steering.get("mode") or "")
    if mode and mode != "FREE_ONLY":
        raise RuntimeError(f"SUPERVISOR_MODE_NOT_FREE_ONLY:{mode}")
    return {
        "epoch": epoch,
        "inbox_path": inbox_path.relative_to(repo).as_posix(),
        "inbox_sha256": sha256_bytes(inbox_raw),
        "steering_path": steering_rel,
        "steering_sha256": sha256_bytes(steering_raw),
        "mode": mode or "FREE_ONLY",
    }


def source_identity(repo: Path) -> dict[str, Any]:
    head = git_text(repo, "rev-parse", "HEAD")
    tree = git_text(repo, "rev-parse", "HEAD^{tree}")
    status = git_text(repo, "status", "--porcelain", "--untracked-files=no")
    files = [
        repo / "tools/free_swarm_historical_backfill.py",
        Path(__file__).resolve(),
        repo / "tools/run_free_evidence_forge_backfill.py",
        repo / "tools/run_free_evidence_forge_safe.py",
    ]
    hashes: dict[str, str | None] = {}
    for path in files:
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
        "authority": authority_identity(repo),
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
    chunks = scalar(con, "SELECT COUNT(*) FROM historical_chunks")
    saturated = int(chunk_states.get("SATURATED", 0))
    return {
        "schema_ready": True,
        "historical_outputs": scalar(con, "SELECT COUNT(*) FROM historical_outputs"),
        "historical_chunks": chunks,
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
        "saturated_chunks": saturated,
        "non_saturated_chunks": max(0, chunks - saturated),
        "explicit_deltas_recovered": int(extraction_modes.get("EXPLICIT_WORKER_DELTA", 0)),
        "batch_deltas_recovered": int(extraction_modes.get("HISTORICAL_BATCH", 0)),
        "extraction_mode_unique_variants": extraction_modes,
        "extraction_mode_observations": extraction_observations,
    }


def artifact_cutoff(artifact_root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    paths = sorted(p for p in artifact_root.rglob("workers.jsonl") if p.is_file()) if artifact_root.exists() else []
    for path in paths:
        st = path.stat()
        try:
            rel = path.relative_to(artifact_root).as_posix()
        except ValueError:
            rel = str(path)
        rows.append(
            {
                "path": rel,
                "size_cutoff": int(st.st_size),
                "mtime_ns_at_cutoff": int(st.st_mtime_ns),
                "inode_at_cutoff": int(st.st_ino),
            }
        )
    identity = {
        "schema": CUTOFF_SCHEMA,
        "files": rows,
    }
    return {
        **identity,
        "file_count": len(rows),
        "cutoff_identity_sha256": sha256_bytes(canonical_json(identity)),
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


def cutoff_progress(
    con: sqlite3.Connection,
    artifact_root: Path,
    cutoff: dict[str, Any],
) -> dict[str, Any]:
    tracked = _tracked_offsets(con)
    rows: list[dict[str, Any]] = []
    cutoff_paths = {str(row["path"]) for row in cutoff.get("files", [])}
    current_paths = {
        p.relative_to(artifact_root).as_posix(): p
        for p in artifact_root.rglob("workers.jsonl")
        if p.is_file()
    } if artifact_root.exists() else {}

    for row in cutoff.get("files", []):
        rel = str(row["path"])
        path = artifact_root / rel
        key = str(path)
        prior = tracked.get(key) or {}
        offset = int(prior.get("byte_offset") or 0)
        tracked_inode = prior.get("inode")
        exists = path.exists() and path.is_file()
        current_size = None
        current_inode = None
        replaced_or_truncated = True
        if exists:
            st = path.stat()
            current_size = int(st.st_size)
            current_inode = int(st.st_ino)
            replaced_or_truncated = (
                current_inode != int(row["inode_at_cutoff"])
                or current_size < int(row["size_cutoff"])
            )
        tracked_matches_cutoff_inode = (
            tracked_inode is not None and int(tracked_inode) == int(row["inode_at_cutoff"])
        )
        caught_up = bool(
            exists
            and not replaced_or_truncated
            and tracked_matches_cutoff_inode
            and offset >= int(row["size_cutoff"])
        )
        rows.append(
            {
                **row,
                "exists_after": exists,
                "current_size": current_size,
                "current_inode": current_inode,
                "tracked_inode": int(tracked_inode) if tracked_inode is not None else None,
                "tracked_byte_offset": offset,
                "replaced_or_truncated": replaced_or_truncated,
                "caught_up_to_cutoff": caught_up,
            }
        )

    post_cutoff = sorted(path for path in current_paths if path not in cutoff_paths)
    return {
        "cutoff_identity_sha256": cutoff.get("cutoff_identity_sha256"),
        "cutoff_file_count": len(rows),
        "caught_up_files": sum(int(bool(row["caught_up_to_cutoff"])) for row in rows),
        "uncaught_up_files": sum(int(not bool(row["caught_up_to_cutoff"])) for row in rows),
        "replaced_or_truncated_files": sum(int(bool(row["replaced_or_truncated"])) for row in rows),
        "files": rows,
        "post_cutoff_new_files": post_cutoff,
        "post_cutoff_new_file_count": len(post_cutoff),
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
    cutoff: dict[str, Any],
    progress: dict[str, Any],
    db_after: dict[str, Any],
    rounds: list[dict[str, int]],
) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if source.get("dirty"):
        blockers.append("DIRTY_SOURCE")
    if not db_after.get("schema_ready"):
        blockers.append("FORGE_BACKFILL_SCHEMA_NOT_READY")
    if int(cutoff.get("file_count", 0) or 0) <= 0:
        blockers.append("NO_VISIBLE_WORKERS_JSONL_AT_CUTOFF")
    if int(progress.get("replaced_or_truncated_files", 0) or 0) > 0:
        blockers.append("CUTOFF_FILE_REPLACED_OR_TRUNCATED")
    if int(progress.get("uncaught_up_files", 0) or 0) > 0:
        blockers.append("HISTORICAL_SCAN_NOT_CAUGHT_UP_TO_CUTOFF")
    if rounds and int(rounds[-1].get("lines_seen", 0)) != 0:
        blockers.append("NO_QUIESCENT_SCAN_ROUND_OBSERVED")
    if int(db_after.get("historical_outputs", 0) or 0) <= 0:
        blockers.append("NO_SUCCESSFUL_HISTORICAL_OUTPUTS")
    if int(db_after.get("remaining_pending_extraction", 0) or 0) > 0:
        blockers.append("PENDING_EXTRACTION_REMAINS")
    if int(db_after.get("max_passes_reached", 0) or 0) > 0:
        blockers.append("MAX_PASSES_REACHED_UNRESOLVED")
    if int(db_after.get("non_saturated_chunks", 0) or 0) > 0:
        blockers.append("NON_SATURATED_CHUNKS_REMAIN")
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


def blocked_receipt(
    *,
    repo: Path,
    artifact_root: Path,
    forge_db: Path,
    blocker: str,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "status": "BLOCKED",
        "blockers": [blocker],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "source": source,
        "repo": str(repo),
        "artifact_root": str(artifact_root),
        "forge_db": str(forge_db),
        "scope": SCOPE,
        "runtime_credit_added": 0,
        "model_credit_added": 0,
        "training_credit_added": 0,
    }


def build_receipt(
    repo: Path,
    artifact_root: Path,
    forge_db: Path,
    *,
    max_rounds: int,
    max_new_lines_per_round: int,
) -> dict[str, Any]:
    source_before = source_identity(repo)
    if not forge_db.exists():
        return blocked_receipt(
            repo=repo,
            artifact_root=artifact_root,
            forge_db=forge_db,
            blocker="FORGE_DB_MISSING",
            source=source_before,
        )

    cutoff = artifact_cutoff(artifact_root)
    con = sqlite3.connect(str(forge_db), timeout=30)
    con.row_factory = sqlite3.Row
    try:
        if not table_exists(con, "candidates"):
            return blocked_receipt(
                repo=repo,
                artifact_root=artifact_root,
                forge_db=forge_db,
                blocker="FORGE_CANDIDATES_TABLE_MISSING",
                source=source_before,
            )
        backfill.ensure_schema(con)
        before = db_snapshot(con)
        rounds = run_incremental_scan(
            con,
            artifact_root,
            max_rounds=max_rounds,
            max_new_lines_per_round=max_new_lines_per_round,
        )
        after = db_snapshot(con)
        progress = cutoff_progress(con, artifact_root, cutoff)
    finally:
        con.close()

    source_after = source_identity(repo)
    source_stable = source_before == source_after
    if not source_stable:
        source_after = dict(source_after)
        source_after["changed_during_receipt"] = True

    status, blockers = classify(
        source=source_after,
        cutoff=cutoff,
        progress=progress,
        db_after=after,
        rounds=rounds,
    )
    if not source_stable:
        status = "BLOCKED"
        blockers = [*blockers, "SOURCE_OR_AUTHORITY_CHANGED_DURING_RECEIPT"]

    lines_scanned = sum(int(row.get("lines_seen", 0)) for row in rounds)
    successful_outputs_observed = sum(int(row.get("successful_outputs", 0)) for row in rounds)
    receipt = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "status": status,
        "blockers": blockers,
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "source": source_after,
        "artifact_root": str(artifact_root),
        "forge_db": str(forge_db),
        "artifact_root_scan_set": cutoff,
        "artifact_root_scan_progress": progress,
        "post_cutoff_history_excluded_from_cutoff_identity": True,
        "incremental_scan_rounds": rounds,
        "lines_scanned": lines_scanned,
        "successful_outputs": successful_outputs_observed,
        "successful_outputs_total": after.get("historical_outputs"),
        "explicit_deltas_recovered": delta(after, before, "explicit_deltas_recovered"),
        "explicit_deltas_recovered_total": after.get("explicit_deltas_recovered"),
        "batch_deltas_recovered": delta(after, before, "batch_deltas_recovered"),
        "batch_deltas_recovered_total": after.get("batch_deltas_recovered"),
        "new_concepts": delta(after, before, "distinct_concepts"),
        "distinct_concepts_total": after.get("distinct_concepts"),
        "new_execution_variants": delta(after, before, "distinct_execution_variants"),
        "distinct_execution_variants_total": after.get("distinct_execution_variants"),
        "duplicates_superseded": delta(after, before, "duplicates_superseded"),
        "duplicates_superseded_total": after.get("duplicates_superseded"),
        "ready_backlog": after.get("ready_backlog"),
        "implementation_backlog": after.get("implementation_backlog"),
        "remaining_pending_extraction": after.get("remaining_pending_extraction"),
        "max_passes_reached_unresolved": after.get("max_passes_reached"),
        "saturated_chunks": after.get("saturated_chunks"),
        "non_saturated_chunks": after.get("non_saturated_chunks"),
        "before": before,
        "after": after,
        "scope": SCOPE,
        "runtime_credit_added": 0,
        "model_credit_added": 0,
        "training_credit_added": 0,
        "evidence_note": (
            "PASS establishes only exact-source historical backfill scan/extraction saturation at the bound cutoff and Forge DB. "
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
    try:
        receipt = build_receipt(
            repo,
            artifact_root,
            forge_db,
            max_rounds=max(1, args.max_rounds),
            max_new_lines_per_round=max(1, args.max_new_lines_per_round),
        )
    except Exception as exc:
        receipt = blocked_receipt(
            repo=repo,
            artifact_root=artifact_root,
            forge_db=forge_db,
            blocker=f"RECEIPT_EXCEPTION:{type(exc).__name__}:{str(exc)[:500]}",
        )
    atomic_json(output, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
