#!/usr/bin/env python3
"""6000-logical-worker Free Swarm fabric for EntityOS/HCU.

This is deliberately a *logical* worker fabric: thousands of independently
scheduled research organs can stay runnable while actual provider calls remain
bounded by the shared quota gate + provider AIMD. This keeps every free lane
saturated without pretending that 6000 simultaneous HTTP model calls exist.

The fabric imports the optimized 24h swarm controller, so workers retain the
machine-readable ARCHITECTURE_DELTA_JSON / OPEN_RESEARCH_QUESTIONS_JSON contract,
live runtime context, empirical model routing, 402 hard stops and 429 cooldowns.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import time
from typing import Any

import run_24h_entityos_swarm as opt
import run_free_go_swarm as base
from free_provider_admission import load_provider_admission, provider_is_admitted_free, ProviderAdmissionError
from free_swarm_quota import snapshot as quota_snapshot

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
DISTILLERY_DB = Path(os.getenv("CLAY_RESEARCH_DISTILLERY_DB", str(ARTIFACT_ROOT / "distillery/distillery.sqlite3")))

# High ceilings are not immediate fan-out: ProviderRuntime starts near one lane per
# credential and AIMD raises/lower target concurrency from empirical success/429.
DEFAULT_PROVIDER_CEILINGS = {"groq": 128, "mistral": 128, "nvidia": 256}

FALLBACK_SHARDS = [
    "typed-entry causal identity", "loader consumed-byte proof", "model execution receipts",
    "GRID10/inference receipt closure", "J-Space causal provenance", "J-Space intervention controls",
    "online training trace causality", "memory replay and forgetting", "hot backend/model switching",
    "ClayCode compiler semantics", "Clay VM scheduling", "Clay runtime latency",
    "EffectGate UNKNOWN outcomes", "capability authority", "atomic lease semantics",
    "crash recovery and exactly-once", "negative-path mutation testing", "differential parity",
    "local inference performance", "SQLite concurrency", "state compression", "causal cache invalidation",
    "global-workspace routing", "attention/broadcast sparsity", "cognition ablations",
    "counterfactual state intervention", "self-model falsification", "recursive improvement controls",
    "architecture search", "benchmark design", "token-quality efficiency", "information-transfer latency",
    "provider/runtime isolation", "sandbox reproducibility", "repo mining", "arXiv mechanism transfer",
    "failure injection", "property-based tests", "deterministic replay", "provenance compaction",
    "model-family ensemble diversity", "Goodhart resistance", "Goodman ancestry collapse",
    "cross-worker disagreement preservation", "knowledge packet reinjection", "distillery yield",
    "forge candidate conversion", "patch synthesis", "benchmark non-regression", "test survival over GO cycles",
    "HCU scale limits", "HCU latency floor", "logical-cell scheduling", "resident-model multiplexing",
    "causal event/admission identity", "world-model non-authority", "synthetic cognition controls",
    "runtime observability", "effect journaling", "secret-free research lanes", "public-repo reproduction",
    "local 4B reviewer lane", "research queue closure", "open-question decomposition", "architecture delta ranking",
]

_PREV_PROMPT = base.worker_prompt


def _open_questions(limit: int = 256) -> list[str]:
    if not DISTILLERY_DB.exists():
        return []
    try:
        con = sqlite3.connect(DISTILLERY_DB, timeout=2)
        rows = con.execute(
            "SELECT question FROM questions WHERE status IN ('OPEN','CYCLIC','RESEARCHING') "
            "ORDER BY priority DESC, attempts ASC, COALESCE(last_touched,'') ASC LIMIT ?", (limit,)
        ).fetchall()
        con.close()
        return [str(r[0]) for r in rows if r and r[0]]
    except Exception:
        return []


def sharded_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    text = _PREV_PROMPT(protocol, role, task, state_context, serial)
    qs = _open_questions()
    focus = qs[(serial - 1) % len(qs)] if qs else FALLBACK_SHARDS[(serial - 1) % len(FALLBACK_SHARDS)]
    variant = 1 + ((serial - 1) // max(1, len(qs) or len(FALLBACK_SHARDS)))
    return text + f"""

6000-WORKER FABRIC SHARD
logical_worker_serial={serial}
focus={focus}
mechanism_variant={variant}
- Treat this focus as your primary shard, not as permission to repeat an old mechanism.
- If this question/focus has prior attempts, choose a causally different mechanism/ablation.
- Produce at most ONE primary executable delta; spend remaining space on its falsifier/counterevidence.
- A duplicate architecture essay is a failed worker result even if eloquent.
"""


base.worker_prompt = sharded_prompt


def _set_high_ceiling_env() -> None:
    for provider, cap in DEFAULT_PROVIDER_CEILINGS.items():
        os.environ.setdefault(f"CLAY_{provider.upper()}_MAX_CONCURRENCY", str(cap))


async def fabric_status_loop(runtimes: list[base.ProviderRuntime], sink: base.JsonlSink,
                             deadline: float, stop_event: asyncio.Event,
                             logical_workers: int, task_count: int) -> None:
    while not stop_event.is_set() and time.monotonic() < deadline:
        active_calls = sum(rt.active for rt in runtimes)
        target_calls = sum(rt.target_concurrency for rt in runtimes)
        await sink.status({
            "schema": "CLAY_6000_FREE_SWARM_STATUS/v1",
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "remaining_seconds": max(0, int(deadline - time.monotonic())),
            "logical_workers_configured": logical_workers,
            "logical_worker_tasks_alive": task_count,
            "actual_model_calls_inflight": active_calls,
            "adaptive_provider_target_inflight": target_calls,
            "provider_hard_ceiling_sum": sum(rt.max_concurrency for rt in runtimes),
            "providers": {rt.spec.name: rt.snapshot() for rt in runtimes},
            "shared_quota": quota_snapshot(),
            "meaning": "6000=logical research organs; actual HTTP inference concurrency is empirical/AIMD/rate-limit bounded",
        })
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass


async def run(args: argparse.Namespace) -> int:
    _set_high_ceiling_env()
    discovery = opt.discover_and_export(args.timeout)
    print(json.dumps({"schema":"CLAY_6000_SWARM_DISCOVERY/v1","logical_workers":args.logical_workers,"providers":discovery}, ensure_ascii=False), flush=True)

    try:
        admission = load_provider_admission()
    except ProviderAdmissionError as exc:
        print(f"typed provider admission invalid: {exc}", flush=True)
        return 5
    if not base.truthy(os.getenv("CLAY_FREE_ONLY_ATTESTED")):
        print("CLAY_FREE_ONLY_ATTESTED compatibility assertion missing", flush=True)
        return 3

    protocol = base.load_protocol()
    run_id = dt.datetime.now(dt.timezone.utc).strftime("fabric6000-%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir) if args.output_dir else ARTIFACT_ROOT / f"active-{run_id}"
    sink = base.JsonlSink(output_dir)
    runtimes: list[base.ProviderRuntime] = []
    for spec in base.PROVIDERS:
        if not provider_is_admitted_free(spec.name, admission):
            continue
        if not base.truthy(os.getenv(spec.attestation_env)):
            continue
        keys = base.collect_keys(spec, admission)
        if not keys:
            continue
        models = base.split_values(os.getenv(spec.models_env)) or list(spec.default_models)
        cap = int(os.getenv(f"CLAY_{spec.name.upper()}_MAX_CONCURRENCY", str(DEFAULT_PROVIDER_CEILINGS.get(spec.name, spec.default_max_concurrency))))
        runtimes.append(base.ProviderRuntime(spec, keys, base.unique(models), cap))
    if not runtimes:
        print("no admitted provider runtime with credential", flush=True)
        return 4

    duration_s = max(1.0, args.hours * 3600.0)
    deadline = time.monotonic() + duration_s
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try: loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError: pass

    manifest = {
        "schema":"CLAY_6000_FREE_SWARM_RUN/v1", "run_id":run_id,
        "started_at":dt.datetime.now(dt.timezone.utc).isoformat(), "duration_hours":args.hours,
        "logical_workers":args.logical_workers, "free_only":True,
        "provider_admission_epoch":admission.get("authority_epoch"),
        "repo_head":base.git_text("rev-parse","HEAD"),
        "protocol_sha256":hashlib.sha256(protocol.encode()).hexdigest(),
        "providers":{rt.spec.name:{"key_fingerprints":[base.key_fingerprint(k) for k in rt.keys],"models":rt.models,"hard_ceiling":rt.max_concurrency} for rt in runtimes},
        "invariants":["6000_LOGICAL_NOT_6000_HTTP", "AIMD", "SHARED_QUOTA_GATE", "402_HARD_STOP", "429_PROVIDER_COOLDOWN", "NO_PAID_FALLBACK", "MACHINE_READABLE_DELTAS", "SHARDED_OPEN_QUESTIONS"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/"run_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    serial_counter=[0]
    worker_tasks=[]
    # Distribute exactly N logical research organs across available provider runtimes.
    for slot in range(args.logical_workers):
        rt = runtimes[slot % len(runtimes)]
        worker_tasks.append(asyncio.create_task(base.worker_loop(rt, slot, protocol, sink, deadline, args, serial_counter, stop_event)))
    status_task=asyncio.create_task(fabric_status_loop(runtimes,sink,deadline,stop_event,args.logical_workers,len(worker_tasks)))
    sleep_task=asyncio.create_task(asyncio.sleep(duration_s)); stop_task=asyncio.create_task(stop_event.wait())
    _, pending = await asyncio.wait({sleep_task,stop_task}, return_when=asyncio.FIRST_COMPLETED)
    stop_event.set()
    for task in pending: task.cancel()
    try:
        await asyncio.wait_for(asyncio.gather(*worker_tasks,status_task,return_exceptions=True), timeout=args.drain_seconds)
    except asyncio.TimeoutError:
        for task in worker_tasks: task.cancel()
        status_task.cancel()
        await asyncio.gather(*worker_tasks,status_task,return_exceptions=True)
    final={
        "schema":"CLAY_6000_FREE_SWARM_FINAL/v1", "run_id":run_id,
        "finished_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "logical_workers_configured":args.logical_workers, "worker_calls_started":serial_counter[0],
        "providers":{rt.spec.name:rt.snapshot() for rt in runtimes}, "shared_quota":quota_snapshot(),
    }
    await sink.status(final)
    (output_dir/"final.json").write_text(json.dumps(final,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(final,ensure_ascii=False),flush=True)
    return 0


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(description="Run 6000 logical EntityOS/HCU Free-Swarm research organs")
    p.add_argument("--logical-workers",type=int,default=6000)
    p.add_argument("--hours",type=float,default=24.0)
    p.add_argument("--max-tokens",type=int,default=1600)
    p.add_argument("--context-chars",type=int,default=15000)
    p.add_argument("--timeout",type=float,default=180.0)
    p.add_argument("--drain-seconds",type=float,default=300.0)
    p.add_argument("--output-dir",default="")
    return p.parse_args()

if __name__=="__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
