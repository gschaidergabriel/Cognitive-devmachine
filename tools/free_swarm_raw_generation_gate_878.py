#!/usr/bin/env python3
"""Fail-closed raw-generation gate for Supervisor 8.78.

This is a deterministic control-plane helper only. It never reads provider credentials,
never calls a provider/model/network surface, and never mints canonical truth or runtime
credit.

Raw Free-Swarm generation is allowed only when the currently visible historical corpus is
caught up in the canonical Forge backfill database, every historical chunk is saturated,
and the remaining ready/implementation conversion backlog is below the configured threshold.
A pre/post workers.jsonl snapshot closes the obvious file-append/replacement TOCTOU window.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable

SCHEMA = "CLAY_SWARM_RAW_GENERATION_BACKPRESSURE/v2"
DEFAULT_ARTIFACT_ROOT = Path("/artifacts/clay-entityos-swarm")
DEFAULT_THRESHOLD = 64


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def worker_snapshot(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(p for p in root.rglob("workers.jsonl") if p.is_file()):
        try:
            st = path.stat()
        except OSError:
            continue
        rows.append(
            {
                "path": str(path),
                "inode": int(st.st_ino),
                "size": int(st.st_size),
                "mtime_ns": int(st.st_mtime_ns),
            }
        )
    return rows


def _table_names(con: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def _scalar(con: sqlite3.Connection, sql: str) -> int:
    row = con.execute(sql).fetchone()
    return int(row[0] or 0) if row else 0


def _db_measurement(db: Path, workers: list[dict[str, Any]], threshold: int) -> dict[str, Any]:
    if not db.exists():
        return {
            "state": "UNKNOWN_FORGE_DB",
            "allow_raw_generation": False,
            "action": "PAUSE_RAW_GENERATION_FAIL_CLOSED",
            "blockers": ["FORGE_DB_MISSING"],
        }

    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2.0)
    except sqlite3.Error as exc:
        return {
            "state": "FORGE_DB_OPEN_FAILED",
            "allow_raw_generation": False,
            "action": "PAUSE_RAW_GENERATION_FAIL_CLOSED",
            "blockers": ["FORGE_DB_OPEN_FAILED"],
            "error_class": type(exc).__name__,
        }

    try:
        tables = _table_names(con)
        required = {"candidates", "historical_chunks", "backfill_files"}
        missing = sorted(required - tables)
        if missing:
            return {
                "state": "FORGE_SCHEMA_INCOMPLETE",
                "allow_raw_generation": False,
                "action": "PAUSE_RAW_GENERATION_FAIL_CLOSED",
                "blockers": ["FORGE_SCHEMA_INCOMPLETE"],
                "missing_tables": missing,
            }

        tracked: dict[str, tuple[int | None, int, int]] = {}
        for row in con.execute(
            "SELECT source_path,inode,byte_offset,file_size FROM backfill_files ORDER BY source_path"
        ):
            tracked[str(row[0])] = (
                int(row[1]) if row[1] is not None else None,
                int(row[2] or 0),
                int(row[3] or 0),
            )

        uncaught: list[dict[str, Any]] = []
        for item in workers:
            path = str(item["path"])
            current_inode = int(item["inode"])
            current_size = int(item["size"])
            prior = tracked.get(path)
            if prior is None:
                uncaught.append({"path": path, "reason": "UNTRACKED_FILE"})
                continue
            tracked_inode, byte_offset, recorded_file_size = prior
            if tracked_inode != current_inode:
                uncaught.append(
                    {
                        "path": path,
                        "reason": "INODE_MISMATCH",
                        "tracked_inode": tracked_inode,
                        "current_inode": current_inode,
                    }
                )
                continue
            # Exact equality is deliberate. offset < size means unscanned bytes or an
            # incomplete trailing JSONL line; offset > size means truncation/reset has
            # not yet been reconciled by the backfill scanner.
            if byte_offset != current_size:
                uncaught.append(
                    {
                        "path": path,
                        "reason": "BYTE_OFFSET_NOT_CAUGHT_UP",
                        "tracked_byte_offset": byte_offset,
                        "current_size": current_size,
                        "recorded_file_size": recorded_file_size,
                    }
                )

        chunk_states = {
            str(row[0]): int(row[1])
            for row in con.execute(
                "SELECT state,COUNT(*) FROM historical_chunks GROUP BY state ORDER BY state"
            )
        }
        total_chunks = sum(chunk_states.values())
        saturated_chunks = int(chunk_states.get("SATURATED", 0))
        non_saturated_chunks = max(0, total_chunks - saturated_chunks)
        pending_extraction = int(chunk_states.get("PENDING_EXTRACTION", 0))
        max_passes_reached = int(chunk_states.get("MAX_PASSES_REACHED", 0))

        ready_backlog = _scalar(
            con, "SELECT COUNT(*) FROM candidates WHERE ready=1 AND state='NEW'"
        )
        implementation_backlog = _scalar(
            con, "SELECT COUNT(*) FROM candidates WHERE state='NEEDS_IMPLEMENTATION'"
        )
        conversion_pressure = ready_backlog + implementation_backlog + pending_extraction

        blockers: list[str] = []
        if not workers:
            blockers.append("NO_VISIBLE_WORKERS_JSONL")
        if uncaught:
            blockers.append("HISTORICAL_SCAN_NOT_CAUGHT_UP")
        if non_saturated_chunks:
            blockers.append("HISTORICAL_CHUNKS_NOT_SATURATED")
        if max_passes_reached:
            blockers.append("MAX_PASSES_REACHED_UNRESOLVED")
        if conversion_pressure >= threshold:
            blockers.append("CONVERSION_PRESSURE_AT_OR_ABOVE_THRESHOLD")

        allowed = not blockers
        return {
            "state": "OBSERVED",
            "allow_raw_generation": allowed,
            "action": "ALLOW_RAW_GENERATION" if allowed else "PAUSE_RAW_GENERATION_BACKPRESSURE",
            "blockers": blockers,
            "worker_files_visible": len(workers),
            "tracked_backfill_files": len(tracked),
            "uncaught_scan_files": uncaught[:32],
            "uncaught_scan_file_count": len(uncaught),
            "chunk_states": chunk_states,
            "historical_chunks": total_chunks,
            "saturated_chunks": saturated_chunks,
            "non_saturated_chunks": non_saturated_chunks,
            "pending_extraction": pending_extraction,
            "max_passes_reached": max_passes_reached,
            "ready_backlog": ready_backlog,
            "implementation_backlog": implementation_backlog,
            "conversion_pressure": conversion_pressure,
            "threshold": threshold,
        }
    except sqlite3.Error as exc:
        return {
            "state": "FORGE_DB_READ_FAILED",
            "allow_raw_generation": False,
            "action": "PAUSE_RAW_GENERATION_FAIL_CLOSED",
            "blockers": ["FORGE_DB_READ_FAILED"],
            "error_class": type(exc).__name__,
        }
    finally:
        con.close()


def evaluate(
    artifact_root: Path,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    snapshot_fn: Callable[[Path], list[dict[str, Any]]] = worker_snapshot,
) -> dict[str, Any]:
    threshold = max(1, int(threshold))
    pre = snapshot_fn(artifact_root)
    result = _db_measurement(artifact_root / "forge" / "forge.sqlite3", pre, threshold)
    post = snapshot_fn(artifact_root)
    stable = pre == post

    blockers = list(result.get("blockers") or [])
    if not stable and "WORKERS_JSONL_CHANGED_DURING_GATE" not in blockers:
        blockers.append("WORKERS_JSONL_CHANGED_DURING_GATE")
    allowed = bool(result.get("allow_raw_generation")) and stable and not blockers

    return {
        "schema": SCHEMA,
        "observed_at": utc_now(),
        "source": "FORGE_SQLITE_PLUS_WORKERS_JSONL_LOCAL_STATE",
        "external_provider_calls": 0,
        "credentials_read": False,
        "canonical_truth_minted": False,
        "runtime_credit_minted": False,
        **result,
        "workers_snapshot_stable": stable,
        "blockers": blockers,
        "allow_raw_generation": allowed,
        "action": "ALLOW_RAW_GENERATION" if allowed else "PAUSE_RAW_GENERATION_BACKPRESSURE",
    }


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    args = ap.parse_args()
    result = evaluate(args.artifact_root, threshold=args.threshold)
    atomic_json(args.artifact_root / "RAW_GENERATION_BACKPRESSURE.json", result)
    return 0 if result["allow_raw_generation"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
