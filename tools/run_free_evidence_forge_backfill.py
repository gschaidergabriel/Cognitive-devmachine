#!/usr/bin/env python3
"""Backlog-first safe Evidence Forge entrypoint.

Layers historical replay/extraction and backlog-aware scheduling on top of the
current bubblewrap-gated Forge authority without creating a second evaluator.
Every status write carries an exact runtime identity envelope so a fresh LIVE file
cannot be mistaken for evidence from a stale or alternate Forge writer.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time

import run_free_evidence_forge_safe_871 as safe
from free_swarm_backfill_provenance import reconcile_candidate_source_counts
import free_swarm_historical_backfill as historical_backfill_core
from free_swarm_backfill_exhaustiveness_878 import install as install_exhaustiveness

# The active Forge consumer must share the producer's conservative completion
# semantics. A chunk is never SATURATED from an implicit/one-off zero-novel pass.
install_exhaustiveness(historical_backfill_core)
backfill_metrics = historical_backfill_core.backfill_metrics
ensure_schema = historical_backfill_core.ensure_schema
ingest_artifact_history = historical_backfill_core.ingest_artifact_history

base = safe.base
_ORIGINAL_CONNECT = base.connect
_ORIGINAL_METRICS = base.metrics
_ENTRYPOINT = Path(__file__).resolve()
_PROCESS_GENERATION_ID = f"pid:{os.getpid()}:start_ns:{time.time_ns()}"


def _entrypoint_sha256() -> str:
    try:
        return hashlib.sha256(_ENTRYPOINT.read_bytes()).hexdigest()
    except OSError:
        return "UNREADABLE"


def _source_identity() -> dict[str, str | None]:
    try:
        root = Path(__file__).resolve().parents[1]
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).strip()
        tree = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD^{tree}"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).strip()
        return {"head": head, "tree": tree}
    except Exception:
        return {"head": None, "tree": None}


_RUNTIME_SOURCE_IDENTITY = _source_identity()
_RUNTIME_ENTRYPOINT_SHA256 = _entrypoint_sha256()


def runtime_identity() -> dict[str, object]:
    return {
        "schema": "CLAY_FORGE_RUNTIME_IDENTITY/v1",
        "runtime_entrypoint_path": str(_ENTRYPOINT),
        "runtime_entrypoint_sha256": _RUNTIME_ENTRYPOINT_SHA256,
        "source_commit": _RUNTIME_SOURCE_IDENTITY.get("head"),
        "source_tree": _RUNTIME_SOURCE_IDENTITY.get("tree"),
        "process_generation_identity": _PROCESS_GENERATION_ID,
        "supervisor_generation_or_start_nonce": os.getenv("CLAY_SUPERVISOR_GENERATION_NONCE"),
        "status_writer_schema_version": "BACKLOG_FIRST_FORGE_STATUS/v2",
    }


def connect():
    con = _ORIGINAL_CONNECT()
    ensure_schema(con)
    return con


def ingest_worker_candidates(con, max_lines_per_file: int = 0) -> int:
    del max_lines_per_file
    stats = ingest_artifact_history(
        con,
        base.ARTIFACT_ROOT,
        max_new_lines=int(os.getenv("CLAY_FORGE_BACKFILL_MAX_NEW_LINES", "50000")),
    )
    reconciled = reconcile_candidate_source_counts(con)
    base.bump(con, "historical_backfill_lines", stats["lines_seen"])
    base.bump(con, "historical_backfill_successful_outputs", stats["successful_outputs"])
    base.bump(con, "historical_backfill_candidate_variants_added", stats["candidate_variants_added"])
    base.bump(con, "historical_backfill_source_counts_reconciled", reconciled)
    con.commit()
    return int(stats["candidate_variants_added"])


def metrics(con, peak_parallel: int = 0):
    out = _ORIGINAL_METRICS(con, peak_parallel)
    out["runtime_identity"] = runtime_identity()
    out["historical_backfill"] = backfill_metrics(con)
    out["ready_backlog"] = int(con.execute("SELECT COUNT(*) FROM candidates WHERE ready=1 AND state='NEW'").fetchone()[0])
    out["implementation_backlog"] = int(con.execute("SELECT COUNT(*) FROM candidates WHERE state='NEEDS_IMPLEMENTATION'").fetchone()[0])
    out["deduplicated_backlog"] = int(con.execute("SELECT COUNT(*) FROM candidates WHERE state='DUPLICATE_SUPERSEDED'").fetchone()[0])
    return out


async def cycle(con, args: argparse.Namespace) -> int:
    ingest_worker_candidates(con)
    backfill = backfill_metrics(con)
    ready_backlog = int(con.execute("SELECT COUNT(*) FROM candidates WHERE ready=1 AND state='NEW'").fetchone()[0])
    impl_backlog = int(con.execute("SELECT COUNT(*) FROM candidates WHERE state='NEEDS_IMPLEMENTATION'").fetchone()[0])
    conversion_pressure = ready_backlog + impl_backlog + int(backfill.get("pending_extraction", 0))

    question_budget = args.questions_per_cycle
    if conversion_pressure >= args.backpressure_threshold:
        question_budget = min(question_budget, args.backpressure_questions_per_cycle)

    questions = base.open_questions(question_budget)
    todo = [q for q in questions if not con.execute("SELECT 1 FROM processed_questions WHERE question_hash=?", (base.sha(q),)).fetchone()]
    discoveries = []
    sem = asyncio.Semaphore(args.discovery_parallel)
    active = 0
    peak = 0
    lock = asyncio.Lock()

    async def wrapped(q):
        nonlocal active, peak
        async with sem:
            async with lock:
                active += 1
                peak = max(peak, active)
            try:
                return await base.discovery_for_question(con, q)
            finally:
                async with lock:
                    active -= 1

    if todo:
        groups = await asyncio.gather(*(wrapped(q) for q in todo[: args.discovery_parallel * 2]), return_exceptions=True)
        for group in groups:
            if isinstance(group, list):
                discoveries.extend(group)

    rows = con.execute(
        "SELECT * FROM candidates WHERE ready=1 AND state='NEW' "
        "ORDER BY COALESCE(priority,0) DESC,COALESCE(source_count,1) DESC,ingested_at LIMIT ?",
        (args.candidates_per_cycle,),
    ).fetchall()
    local_sem = asyncio.Semaphore(args.local_parallel)

    async def val(row):
        async with local_sem:
            return await asyncio.to_thread(base.validate_candidate, con, row)

    vals = await asyncio.gather(*(val(row) for row in rows), return_exceptions=True) if rows else []
    for row, result in zip(rows, vals):
        if isinstance(result, dict):
            base.append_jsonl(base.EVAL_PATH, result)
            con.execute(
                "UPDATE candidates SET state=?,evaluated_at=?,last_reason=? WHERE candidate_hash=?",
                (str(result.get("status") or "EVALUATED").upper(), base.now(), str(result.get("reason") or "")[:1000], row["candidate_hash"]),
            )
            base.bump(con, "evaluations", 1)
            base.bump(con, "accepted_deltas", int(result.get("status") == "accepted"))
        else:
            con.execute(
                "UPDATE candidates SET state='FORGE_ERROR',evaluated_at=?,last_reason=? WHERE candidate_hash=?",
                (base.now(), type(result).__name__, row["candidate_hash"]),
            )
    con.commit()

    github = [d for d in discoveries if d.get("provider") == "github"][: args.e2b_jobs_per_cycle]
    e2b_sem = asyncio.Semaphore(args.e2b_parallel)

    async def er(discovery):
        async with e2b_sem:
            return await base.e2b_reproduce(con, discovery, args.e2b_sandbox_seconds_budget)

    if github:
        await asyncio.gather(*(er(d) for d in github), return_exceptions=True)

    base.atomic_json(base.STATUS_PATH, metrics(con, max(peak, args.local_parallel if rows else 0)))
    return len(rows) + len(discoveries)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backlog-first FREE Evidence Forge")
    p.add_argument("--hours", type=float, default=24.0)
    p.add_argument("--max-cycles", type=int, default=0)
    p.add_argument("--sleep-seconds", type=float, default=5.0)
    p.add_argument("--questions-per-cycle", type=int, default=12)
    p.add_argument("--backpressure-questions-per-cycle", type=int, default=2)
    p.add_argument("--backpressure-threshold", type=int, default=64)
    p.add_argument("--discovery-parallel", type=int, default=4)
    p.add_argument("--candidates-per-cycle", type=int, default=int(os.getenv("CLAY_FORGE_CANDIDATES_PER_CYCLE", "24")))
    p.add_argument("--local-parallel", type=int, default=int(os.getenv("CLAY_FORGE_LOCAL_PARALLEL", "4")))
    p.add_argument("--e2b-parallel", type=int, default=int(os.getenv("CLAY_E2B_MAX_CONCURRENCY", "20")))
    p.add_argument("--e2b-jobs-per-cycle", type=int, default=2)
    p.add_argument("--e2b-sandbox-seconds-budget", type=float, default=float(os.getenv("CLAY_E2B_MAX_SANDBOX_SECONDS", "36000")))
    return p.parse_args()


async def main_async(args: argparse.Namespace) -> int:
    con = connect()
    deadline = time.monotonic() + max(1, args.hours * 3600)
    cycles = 0
    try:
        while time.monotonic() < deadline and (args.max_cycles <= 0 or cycles < args.max_cycles):
            usage = shutil.disk_usage(base.ARTIFACT_ROOT)
            reserve = max(20 * 1024**3, int(usage.total * 0.12))
            if usage.free <= reserve:
                break
            try:
                await cycle(con, args)
            except Exception as exc:
                base.append_jsonl(base.FORGE_ROOT / "errors.jsonl", {"ts": base.now(), "error": type(exc).__name__ + ":" + str(exc)[:1000]})
            cycles += 1
            base.atomic_json(base.STATUS_PATH, metrics(con))
            await asyncio.sleep(max(1, args.sleep_seconds))
    finally:
        base.atomic_json(base.STATUS_PATH, metrics(con))
        con.close()
    return 0


def main() -> int:
    base.connect = connect
    base.ingest_worker_candidates = ingest_worker_candidates
    base.metrics = metrics
    base.cycle = cycle
    return asyncio.run(main_async(parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
