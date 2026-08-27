#!/usr/bin/env python3
"""Adaptive 6000-logical-worker Free Swarm fabric for EntityOS/HCU.

Version 2 uses one global work-stealing scheduler. Logical workers are queued
research organs, not pinned provider coroutines: whichever admitted FREE provider
has measured capacity takes the next shard. This prevents a Groq cooldown from
stranding work while NVIDIA/OpenRouter/Mistral capacity is idle.

Actual HTTP concurrency is still bounded by provider AIMD, the shared quota gate,
available credentials, runtime resources and provider truth (429/402/etc.).
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import sqlite3
import time
from typing import Any

import run_24h_entityos_swarm as opt
import run_free_go_swarm as base
from free_provider_admission import (
    ProviderAdmissionError,
    load_provider_admission,
    provider_is_admitted_free,
)
from free_swarm_quota import snapshot as quota_snapshot

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_SWARM_ARTIFACT_ROOT", "/artifacts/clay-entityos-swarm"))
DISTILLERY_DB = Path(os.getenv(
    "CLAY_RESEARCH_DISTILLERY_DB",
    str(ARTIFACT_ROOT / "distillery/distillery.sqlite3"),
))

# OpenRouter is deliberately restricted to its zero-price router. Provider
# admission remains mandatory and no paid fallback is present.
if not any(spec.name == "openrouter" for spec in base.PROVIDERS):
    base.PROVIDERS = base.PROVIDERS + (
        base.ProviderSpec(
            name="openrouter",
            endpoint="https://openrouter.ai/api/v1/chat/completions",
            key_envs=("OPENROUTER_API_KEY",),
            keys_list_env="OPENROUTER_API_KEYS",
            models_env="OPENROUTER_SWARM_MODELS",
            default_models=("openrouter/free",),
            attestation_env="CLAY_OPENROUTER_FREE_ATTESTED",
            default_max_concurrency=8,
        ),
    )
os.environ.setdefault("OPENROUTER_SWARM_MODELS", "openrouter/free")

DEFAULT_PROVIDER_CEILINGS = {
    "groq": 128,
    "mistral": 128,
    "nvidia": 256,
    "openrouter": 16,
}

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


def _open_questions(limit: int = 512) -> list[str]:
    if not DISTILLERY_DB.exists():
        return []
    try:
        con = sqlite3.connect(DISTILLERY_DB, timeout=2)
        rows = con.execute(
            "SELECT question FROM questions WHERE status IN ('OPEN','CYCLIC','RESEARCHING') "
            "ORDER BY priority DESC, attempts ASC, COALESCE(last_touched,'') ASC LIMIT ?",
            (limit,),
        ).fetchall()
        con.close()
        return [str(r[0]) for r in rows if r and r[0]]
    except Exception:
        return []


def sharded_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    text = _PREV_PROMPT(protocol, role, task, state_context, serial)
    qs = _open_questions()
    pool = qs or FALLBACK_SHARDS
    focus = pool[(serial - 1) % len(pool)]
    variant = 1 + ((serial - 1) // max(1, len(pool)))
    return text + f"""

6000-WORKER FABRIC SHARD
logical_call_serial={serial}
focus={focus}
mechanism_variant={variant}
- Treat this focus as your primary shard.
- If it has prior attempts, choose a causally different mechanism, counterexample or ablation.
- Produce at most ONE primary executable delta; spend remaining space on its falsifier/counterevidence.
- A duplicate architecture essay is a failed worker result even if eloquent.
- The scheduler may move this shard between FREE providers; provider identity is not part of the hypothesis.
"""


base.worker_prompt = sharded_prompt


class FastProviderRuntime(base.ProviderRuntime):
    """Faster AIMD ramp for empirically healthy free lanes.

    429 still halves target concurrency. A healthy lane grows ~33% after a small
    success window instead of +1 after 2*target successes, removing an artificial
    local ramp bottleneck.
    """

    async def on_success(self) -> None:
        async with self._condition:
            self.successes += 1
            self.success_streak += 1
            self.rate_backoff = max(1.0, self.rate_backoff * 0.75)
            threshold = max(4, self.target_concurrency // 2)
            if self.success_streak >= threshold and self.target_concurrency < self.max_concurrency:
                step = max(1, self.target_concurrency // 3)
                self.target_concurrency = min(self.max_concurrency, self.target_concurrency + step)
                self.success_streak = 0
            self._condition.notify_all()


def _set_high_ceiling_env() -> None:
    for provider, cap in DEFAULT_PROVIDER_CEILINGS.items():
        os.environ.setdefault(f"CLAY_{provider.upper()}_MAX_CONCURRENCY", str(cap))


def _initial_target(runtime: FastProviderRuntime, shared: dict[str, Any]) -> int:
    row = ((shared.get("providers") or {}).get(runtime.spec.name) or {})
    ok = int(row.get("total_success") or 0)
    r429 = int(row.get("total_429") or 0)
    attempts = max(1, ok + r429 + int(row.get("total_errors") or 0))
    rate_ratio = r429 / attempts
    keys = max(1, len(runtime.keys))

    explicit = os.getenv(f"CLAY_{runtime.spec.name.upper()}_INITIAL_CONCURRENCY")
    if explicit:
        try:
            return max(1, min(runtime.max_concurrency, int(explicit)))
        except ValueError:
            pass

    if runtime.spec.name == "nvidia":
        # Historical lane has shown substantial success with no provider 429s;
        # probe above the old 12-slot local gate, then AIMD corrects if reality changed.
        target = 24 if ok >= 20 and r429 == 0 else max(6, keys * 4)
    elif runtime.spec.name == "groq":
        target = 2 if rate_ratio >= 0.10 else max(3, keys * 3)
    elif runtime.spec.name == "openrouter":
        target = 3 if rate_ratio >= 0.05 else max(3, keys * 3)
    elif runtime.spec.name == "mistral":
        target = max(4, keys * 3)
    else:
        target = max(2, keys * 2)
    return max(1, min(runtime.max_concurrency, target))


class WorkStealingBroker:
    def __init__(self, runtimes: list[FastProviderRuntime]) -> None:
        self.runtimes = runtimes
        self.assignments: collections.Counter[str] = collections.Counter()
        self.roles: collections.Counter[str] = collections.Counter()
        self.models: collections.Counter[str] = collections.Counter()
        self.completed = 0

    @staticmethod
    def _score(rt: FastProviderRuntime) -> tuple[float, float, float]:
        headroom = max(0, rt.target_concurrency - rt.active)
        reliability = (rt.successes + 2.0) / (rt.requests + 4.0)
        # Fill every healthy provider; larger unused headroom wins first.
        return float(headroom), reliability, random.random()

    async def reserve_any(self) -> tuple[FastProviderRuntime, str, str] | None:
        now = time.monotonic()
        ranked = []
        for rt in self.runtimes:
            if rt.cooldown_until > now:
                continue
            if rt.active >= rt.target_concurrency:
                continue
            if not rt.enabled_keys() or not rt.enabled_models():
                continue
            ranked.append(rt)
        ranked.sort(key=self._score, reverse=True)

        for rt in ranked:
            async with rt._condition:
                now = time.monotonic()
                if rt.cooldown_until > now or rt.active >= rt.target_concurrency:
                    continue
                pair = rt.next_key_model()
                if pair is None:
                    continue
                rt.active += 1
                key, model = pair
                self.assignments[rt.spec.name] += 1
                self.models[f"{rt.spec.name}:{model}"] += 1
                return rt, key, model
        return None


async def execute_call(
    logical_slot: int,
    runtime: FastProviderRuntime,
    key: str,
    model: str,
    protocol: str,
    sink: base.JsonlSink,
    args: argparse.Namespace,
    serial_counter: list[int],
    broker: WorkStealingBroker,
    stop_event: asyncio.Event,
    queue: asyncio.Queue[int],
) -> None:
    serial_counter[0] += 1
    serial = serial_counter[0]
    role, task = base.DEFAULT_ROLES[(serial - 1) % len(base.DEFAULT_ROLES)]
    broker.roles[role] += 1
    prompt = base.worker_prompt(protocol, role, task, base.build_state_context(args.context_chars), serial)
    started = time.time()
    runtime.requests += 1
    common = {
        "schema": "CLAY_FREE_GO_SWARM_WORKER/v2",
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": runtime.spec.name,
        "model": model,
        "key_fp": base.key_fingerprint(key),
        "role": role,
        "worker_serial": serial,
        "logical_worker_slot": logical_slot,
        "scheduler": "GLOBAL_WORK_STEALING_V2",
        "repo_head_at_prompt": base.git_text("rev-parse", "HEAD"),
    }
    try:
        try:
            status, headers, payload = await asyncio.to_thread(
                base.request_chat,
                runtime.spec,
                key,
                model,
                prompt,
                args.max_tokens,
                args.timeout,
            )
        except Exception as exc:
            await runtime.on_transient_error()
            common.update({
                "http_status": "NETWORK_EXCEPTION",
                "error": f"{exc.__class__.__name__}:{str(exc)[:300]}",
                "elapsed_s": round(time.time() - started, 3),
            })
            await sink.append(common)
            return

        common.update({
            "http_status": status,
            "elapsed_s": round(time.time() - started, 3),
            "usage": base.usage_from(payload),
            "rate": {
                k: v for k, v in headers.items()
                if k.startswith("x-ratelimit-") or k == "retry-after"
            },
        })

        if 200 <= status < 300:
            text = base.extract_text(payload)
            common["text"] = text
            common["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            common["conformance"] = {
                "protocol_injected": prompt.startswith(base.PROTOCOL_BEGIN),
                "german_summary_marker": "DEUTSCHE_ZUSAMMENFASSUNG" in text,
                "architecture_delta_marker": "ARCHITECTURE_DELTA_JSON=" in text,
                "research_questions_marker": "OPEN_RESEARCH_QUESTIONS_JSON=" in text,
            }
            await sink.append(common)
            await runtime.on_success()
            broker.completed += 1
            return
        if status == 402:
            common["classification"] = "PAYMENT_REQUIRED_HARD_STOP_KEY"
            common["error_body"] = payload
            await sink.append(common)
            await runtime.disable_key(key)
            return
        if status in (401, 403):
            common["classification"] = "AUTH_OR_ENTITLEMENT_BLOCKED_KEY"
            common["error_body"] = payload
            await sink.append(common)
            await runtime.disable_key(key)
            return
        if status == 404:
            common["classification"] = "MODEL_OR_ENDPOINT_UNAVAILABLE"
            common["error_body"] = payload
            await sink.append(common)
            await runtime.disable_model(model)
            return
        if status == 429:
            retry_after = base.parse_retry_after(
                headers,
                min(900.0, runtime.rate_backoff),
            )
            common["classification"] = "RATE_LIMIT_PROVIDER_COOLDOWN"
            common["retry_after_s"] = retry_after
            common["error_body"] = payload
            await sink.append(common)
            await runtime.on_429(retry_after)
            return
        if 500 <= status < 600:
            common["classification"] = "PROVIDER_TRANSIENT_ERROR"
            common["error_body"] = payload
            await sink.append(common)
            await runtime.on_transient_error()
            return

        common["classification"] = "NONRETRYABLE_REQUEST_ERROR"
        common["error_body"] = payload
        runtime.errors += 1
        await sink.append(common)
    finally:
        await runtime.release()
        if not stop_event.is_set():
            await queue.put(logical_slot)


async def dispatch_loop(
    runtimes: list[FastProviderRuntime],
    broker: WorkStealingBroker,
    protocol: str,
    sink: base.JsonlSink,
    deadline: float,
    args: argparse.Namespace,
    serial_counter: list[int],
    stop_event: asyncio.Event,
    queue: asyncio.Queue[int],
    inflight: set[asyncio.Task],
) -> None:
    while not stop_event.is_set() and time.monotonic() < deadline:
        dispatched = 0
        while not queue.empty() and not stop_event.is_set():
            reservation = await broker.reserve_any()
            if reservation is None:
                break
            try:
                logical_slot = queue.get_nowait()
            except asyncio.QueueEmpty:
                rt, _, _ = reservation
                await rt.release()
                break
            rt, key, model = reservation
            task = asyncio.create_task(
                execute_call(
                    logical_slot, rt, key, model, protocol, sink, args,
                    serial_counter, broker, stop_event, queue,
                )
            )
            inflight.add(task)
            task.add_done_callback(inflight.discard)
            dispatched += 1
        if dispatched == 0:
            # Centralized wait: 6000 logical workers do not spin/poll individually.
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.10)
            except asyncio.TimeoutError:
                pass
        else:
            await asyncio.sleep(0)


async def fabric_status_loop(
    runtimes: list[FastProviderRuntime],
    sink: base.JsonlSink,
    deadline: float,
    stop_event: asyncio.Event,
    logical_workers: int,
    queue: asyncio.Queue[int],
    inflight: set[asyncio.Task],
    broker: WorkStealingBroker,
) -> None:
    while not stop_event.is_set() and time.monotonic() < deadline:
        active_calls = sum(rt.active for rt in runtimes)
        target_calls = sum(rt.target_concurrency for rt in runtimes)
        waiting = queue.qsize()
        await sink.status({
            "schema": "CLAY_6000_FREE_SWARM_STATUS/v2",
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "remaining_seconds": max(0, int(deadline - time.monotonic())),
            "logical_workers_configured": logical_workers,
            "logical_workers_waiting": waiting,
            "logical_workers_inflight": max(0, logical_workers - waiting),
            "actual_model_calls_inflight": active_calls,
            "actual_call_tasks_alive": len(inflight),
            "adaptive_provider_target_inflight": target_calls,
            "provider_hard_ceiling_sum": sum(rt.max_concurrency for rt in runtimes),
            "target_utilization": active_calls / target_calls if target_calls else 0.0,
            "work_stealing": True,
            "provider_assignments": dict(broker.assignments),
            "role_assignments": dict(broker.roles),
            "successful_calls": broker.completed,
            "providers": {rt.spec.name: rt.snapshot() for rt in runtimes},
            "shared_quota": quota_snapshot(),
            "meaning": (
                "6000=logical research organs in one global queue; actual HTTP inference "
                "concurrency is work-stolen across every healthy admitted FREE provider"
            ),
        })
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass


async def run(args: argparse.Namespace) -> int:
    _set_high_ceiling_env()
    discovery = opt.discover_and_export(args.timeout)
    print(json.dumps({
        "schema": "CLAY_6000_SWARM_DISCOVERY/v2",
        "logical_workers": args.logical_workers,
        "scheduler": "GLOBAL_WORK_STEALING_V2",
        "providers": discovery,
    }, ensure_ascii=False), flush=True)

    try:
        admission = load_provider_admission()
    except ProviderAdmissionError as exc:
        print(f"typed provider admission invalid: {exc}", flush=True)
        return 5
    if not base.truthy(os.getenv("CLAY_FREE_ONLY_ATTESTED")):
        print("CLAY_FREE_ONLY_ATTESTED compatibility assertion missing", flush=True)
        return 3

    protocol = base.load_protocol()
    run_id = dt.datetime.now(dt.timezone.utc).strftime("fabric6000-v2-%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir) if args.output_dir else ARTIFACT_ROOT / f"active-{run_id}"
    sink = base.JsonlSink(output_dir)
    shared = quota_snapshot()
    runtimes: list[FastProviderRuntime] = []

    for spec in base.PROVIDERS:
        if not provider_is_admitted_free(spec.name, admission):
            continue
        if not base.truthy(os.getenv(spec.attestation_env)):
            continue
        keys = base.collect_keys(spec, admission)
        if not keys:
            continue
        models = base.split_values(os.getenv(spec.models_env)) or list(spec.default_models)
        cap = int(os.getenv(
            f"CLAY_{spec.name.upper()}_MAX_CONCURRENCY",
            str(DEFAULT_PROVIDER_CEILINGS.get(spec.name, spec.default_max_concurrency)),
        ))
        rt = FastProviderRuntime(spec, keys, base.unique(models), cap)
        rt.target_concurrency = _initial_target(rt, shared)
        runtimes.append(rt)

    if not runtimes:
        print("no admitted provider runtime with credential", flush=True)
        return 4

    duration_s = max(1.0, args.hours * 3600.0)
    deadline = time.monotonic() + duration_s
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "CLAY_6000_FREE_SWARM_RUN/v2",
        "run_id": run_id,
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "duration_hours": args.hours,
        "logical_workers": args.logical_workers,
        "scheduler": "GLOBAL_WORK_STEALING_V2",
        "free_only": True,
        "provider_admission_epoch": admission.get("authority_epoch"),
        "repo_head": base.git_text("rev-parse", "HEAD"),
        "protocol_sha256": hashlib.sha256(protocol.encode()).hexdigest(),
        "providers": {
            rt.spec.name: {
                "key_fingerprints": [base.key_fingerprint(k) for k in rt.keys],
                "models": rt.models,
                "initial_target": rt.target_concurrency,
                "hard_ceiling": rt.max_concurrency,
            }
            for rt in runtimes
        },
        "invariants": [
            "6000_LOGICAL_NOT_6000_HTTP",
            "GLOBAL_WORK_STEALING",
            "FAST_AIMD",
            "SHARED_QUOTA_GATE",
            "402_HARD_STOP",
            "429_PROVIDER_COOLDOWN",
            "NO_PAID_FALLBACK",
            "OPENROUTER_FREE_ROUTER_ONLY",
            "MACHINE_READABLE_DELTAS",
            "SHARDED_OPEN_QUESTIONS",
        ],
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    queue: asyncio.Queue[int] = asyncio.Queue(maxsize=max(1, args.logical_workers * 2))
    for slot in range(args.logical_workers):
        queue.put_nowait(slot)

    serial_counter = [0]
    broker = WorkStealingBroker(runtimes)
    inflight: set[asyncio.Task] = set()

    dispatcher = asyncio.create_task(
        dispatch_loop(
            runtimes, broker, protocol, sink, deadline, args, serial_counter,
            stop_event, queue, inflight,
        )
    )
    status_task = asyncio.create_task(
        fabric_status_loop(
            runtimes, sink, deadline, stop_event, args.logical_workers,
            queue, inflight, broker,
        )
    )
    sleep_task = asyncio.create_task(asyncio.sleep(duration_s))
    stop_task = asyncio.create_task(stop_event.wait())
    _, pending = await asyncio.wait(
        {sleep_task, stop_task},
        return_when=asyncio.FIRST_COMPLETED,
    )
    stop_event.set()
    for task in pending:
        task.cancel()

    await asyncio.gather(dispatcher, status_task, return_exceptions=True)
    if inflight:
        try:
            await asyncio.wait_for(
                asyncio.gather(*list(inflight), return_exceptions=True),
                timeout=args.drain_seconds,
            )
        except asyncio.TimeoutError:
            for task in list(inflight):
                task.cancel()
            await asyncio.gather(*list(inflight), return_exceptions=True)

    final = {
        "schema": "CLAY_6000_FREE_SWARM_FINAL/v2",
        "run_id": run_id,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "logical_workers_configured": args.logical_workers,
        "worker_calls_started": serial_counter[0],
        "successful_calls": broker.completed,
        "work_stealing": True,
        "provider_assignments": dict(broker.assignments),
        "role_assignments": dict(broker.roles),
        "providers": {rt.spec.name: rt.snapshot() for rt in runtimes},
        "shared_quota": quota_snapshot(),
    }
    await sink.status(final)
    (output_dir / "final.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(final, ensure_ascii=False), flush=True)
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run 6000 logical EntityOS/HCU Free-Swarm organs with global work stealing"
    )
    p.add_argument("--logical-workers", type=int, default=6000)
    p.add_argument("--hours", type=float, default=24.0)
    p.add_argument("--max-tokens", type=int, default=1600)
    p.add_argument("--context-chars", type=int, default=15000)
    p.add_argument("--timeout", type=float, default=180.0)
    p.add_argument("--drain-seconds", type=float, default=300.0)
    p.add_argument("--output-dir", default="")
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
