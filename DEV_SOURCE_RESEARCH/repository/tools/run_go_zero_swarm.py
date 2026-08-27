#!/usr/bin/env python3
"""Coordinated FREE_ONLY Mini Entity worker swarm for user triggers `go` and `zero`.

This is a trigger-scoped orchestration layer over tools/run_free_go_swarm.py.
It keeps one parent macrocycle id per invocation, injects the mandatory GRF/ClayCode
protocol into every child `go`, coordinates active leases/targets across processes,
tracks recent token usage, and refuses paid/unknown execution just like the base
FREE_ONLY controller.

Secrets are never persisted. The shared state stores key fingerprints only.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import signal
import sys
import time
from typing import Any
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "tools/run_free_go_swarm.py"
DEFAULT_STATE_DIR = Path.home() / ".local/state/clay-trigger-swarm"

LANES: tuple[tuple[str, str], ...] = (
    ("ARCH::PRODUCT_BOUNDARY", "Re-evaluate the current Mini Entity/EntityOS product boundary and find one highest-information convergence delta."),
    ("ARCH::COGNITIVE_FABRIC", "Stress the Unified J-Space/GWT/GRF/Hyperposition/ClayCode cognitive-fabric contract for hidden coupling or missing invariants."),
    ("TRUTH::EPISTEMIC", "Attack UNKNOWN/ZERO/ERROR/MEASURED and REPORTED/MEASURED separation with concrete counterexamples."),
    ("TRUTH::AUTHORITY", "Attack model-output versus canonical truth/effect authority boundaries and propose deterministic falsifiers."),
    ("DB::ATOMICITY", "Stress MiniUnifiedDB atomicity, CAS, generations and crash ambiguity with one concrete failure schedule."),
    ("DB::EXACTLY_ONCE", "Stress exactly-once/effect receipts/replay ambiguity and find a duplicate-effect counterexample if one exists."),
    ("DB::RECOVERY", "Analyze restart/recovery/provenance continuity and preserve UNKNOWN where receipts are missing."),
    ("PARITY::REFERENCE_NATIVE", "Find the smallest unproved divergence between reference and native Mini Entity behavior."),
    ("PARITY::PROFILE_V2", "Find profile-v2/configuration parity gaps and produce a minimal differential test."),
    ("PARITY::EFFECT_SURFACE", "Compare effect-surface semantics including inference_generate/profile read/write and stale-generation handling."),
    ("INFER::LOCAL_EXEC", "Stress generic local_exec integration, timeout/error classification and state preservation across backend swaps."),
    ("INFER::REMOTE_API", "Stress adaptive remote API profiles, fail-closed capability negotiation, rate-limit/cost policy and provenance."),
    ("INFER::CLAUDE_ADAPTER", "Review the first-class Claude Code adapter boundary without granting identity/truth/effect authority."),
    ("INFER::SCHEDULER", "Challenge inference-scheduler routing, capability profiles and deterministic reason receipts."),
    ("COG08::GRF", "Advance/falsify explicit GRF R0..R6 semantics for the bundled ~0.8B cognition path."),
    ("COG08::HYPERPOSITION", "Find premature-collapse failure modes in Hyperposition and propose discriminators/receipts."),
    ("COG08::OMEGA", "Stress typed omega grammar/type/schema/authority/generation validation and rejection paths."),
    ("COG08::OOD", "Design or critique OOD/compositional generalization tests for generic ClayCode cognition."),
    ("COG08::QUANT_RSS", "Advance exact quantization/runtime/RSS measurement planning without claiming unmeasured RAM."),
    ("JSPACE::IDENTITY", "Stress exact checkpoint/tokenizer/runtime/lens identity and stale-profile rejection."),
    ("JSPACE::CALIBRATION", "Challenge all unmeasured layer/band/threshold/slot assumptions and define cheapest calibration tests."),
    ("GWT::WORKSPACE", "Stress GWT competition/broadcast/occupancy semantics without equating workspace stability with truth."),
    ("GWT::THALAMUS", "Stress Thalamus admission/routing semantics and failure isolation."),
    ("EPQ::TELEMETRY", "Audit EPQ/trajectory telemetry semantics, provenance and non-authority boundaries."),
    ("CLAY::COMPILER", "Find one compiler/parser/type-system defect that directly blocks current Mini Entity semantics."),
    ("CLAY::RUNTIME", "Find one runtime/VM semantic gap that directly blocks the current product and define an executable test."),
    ("CLAY::INTEROP", "Review host-language adapters/build glue and ensure Mini Entity semantics remain represented in ClayCode."),
    ("SEC::SECRETS", "Attack secret_ref/token isolation, logs, prompts, exports and telemetry for leak paths."),
    ("SEC::STALE_GENERATION", "Attack stale-generation rejection and concurrent commit/effect races."),
    ("SEC::PROMPT_BOUNDARY", "Attack runtime-editable prompt/personality/application versus immutable architecture/truth gates."),
    ("TEST::MUTATION", "Generate one high-information mutation/property test for the current frontier."),
    ("TEST::DIFFERENTIAL", "Generate one high-information differential test across independent implementations/backends."),
    ("TEST::FAILURE_PATH", "Generate one concrete failure-path schedule that could falsify a current green claim."),
    ("REVIEW::OVERCLAIM", "Search current evidence for source-only, stale-head, fixture-only or zero-step overclaims."),
    ("REVIEW::ANCESTRY", "Check whether supposedly independent evidence shares implementation/model/test ancestry."),
    ("FUSION::CONFLICTS", "Fuse recent results while preserving unresolved contradictions instead of averaging them away."),
    ("FUSION::NEXT_GATE", "Select the next cheapest executable product-level discriminator from current evidence."),
)


def load_base():
    spec = importlib.util.spec_from_file_location("clay_free_go_swarm", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base controller {BASE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


BASE = load_base()


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def mono() -> float:
    return time.monotonic()


def epoch() -> float:
    return time.time()


def make_macrocycle_id(trigger: str) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{trigger}-{stamp}-{uuid.uuid4().hex[:12]}"


@dataclasses.dataclass
class Lease:
    lease_id: str
    macrocycle_id: str
    parent_trigger: str
    child_trigger: str
    pid: int
    provider: str
    model: str
    key_fp: str
    lane: str
    task: str
    worker_serial: int
    started_at: float
    expires_at: float
    reserved_output_tokens: int

    def public(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class SharedCoordinator:
    """Cross-process file-locked coordination state with no API secrets."""

    def __init__(self, state_dir: Path, lease_ttl: float, history_limit: int = 160) -> None:
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / "coordination.json"
        self.lock_path = self.state_dir / "coordination.lock"
        self.lease_ttl = max(30.0, lease_ttl)
        self.history_limit = max(20, history_limit)

    @contextlib.contextmanager
    def locked_state(self):
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+") as lock_fh:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
            try:
                state = self._read_unlocked()
                self._prune_unlocked(state)
                yield state
                self._write_unlocked(state)
            finally:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)

    def _read_unlocked(self) -> dict[str, Any]:
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
        return {"schema": "CLAY_TRIGGER_SWARM_COORDINATION/v1", "active": {}, "recent": [], "token_events": []}

    def _write_unlocked(self, state: dict[str, Any]) -> None:
        state["updated_at"] = now_utc()
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    def _prune_unlocked(self, state: dict[str, Any]) -> None:
        t = epoch()
        active = state.setdefault("active", {})
        for lid in [lid for lid, x in active.items() if float(x.get("expires_at", 0)) <= t]:
            active.pop(lid, None)
        recent = state.setdefault("recent", [])
        if len(recent) > self.history_limit:
            state["recent"] = recent[-self.history_limit:]
        cutoff = t - 86400.0
        token_events = state.setdefault("token_events", [])
        state["token_events"] = [x for x in token_events if float(x.get("ts_epoch", 0)) >= cutoff][-4000:]

    def claim(self, *, macrocycle_id: str, parent_trigger: str, provider: str, model: str,
              key_fp: str, worker_serial: int, max_tokens: int, avoid_lanes: set[str]) -> Lease | None:
        with self.locked_state() as state:
            active = state["active"]
            occupied = {str(x.get("lane")) for x in active.values()}
            recent_lane_order = [str(x.get("lane")) for x in state.get("recent", [])[-len(LANES):]]
            candidates = [x for x in LANES if x[0] not in occupied and x[0] not in avoid_lanes]
            if not candidates:
                return None
            def score(item: tuple[str, str]) -> tuple[int, float]:
                lane = item[0]
                try:
                    recency = recent_lane_order[::-1].index(lane)
                except ValueError:
                    recency = 10000
                return (recency, random.random())
            lane, task = max(candidates, key=score)
            lease_id = uuid.uuid4().hex
            started = epoch()
            lease = Lease(
                lease_id=lease_id,
                macrocycle_id=macrocycle_id,
                parent_trigger=parent_trigger,
                child_trigger="go",
                pid=os.getpid(),
                provider=provider,
                model=model,
                key_fp=key_fp,
                lane=lane,
                task=task,
                worker_serial=worker_serial,
                started_at=started,
                expires_at=started + self.lease_ttl,
                reserved_output_tokens=max_tokens,
            )
            active[lease_id] = lease.public()
            return lease

    def heartbeat(self, lease_id: str) -> None:
        with self.locked_state() as state:
            item = state["active"].get(lease_id)
            if item:
                item["expires_at"] = epoch() + self.lease_ttl
                item["heartbeat_at"] = epoch()

    def finish(self, lease: Lease, *, status: Any, usage: dict[str, Any], text: str,
               classification: str, elapsed_s: float) -> None:
        with self.locked_state() as state:
            state["active"].pop(lease.lease_id, None)
            state.setdefault("recent", []).append({
                "finished_at": epoch(),
                "macrocycle_id": lease.macrocycle_id,
                "parent_trigger": lease.parent_trigger,
                "child_trigger": "go",
                "provider": lease.provider,
                "model": lease.model,
                "lane": lease.lane,
                "worker_serial": lease.worker_serial,
                "http_status": status,
                "classification": classification,
                "usage": usage,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None,
                "result_excerpt": text[-800:] if text else "",
                "elapsed_s": elapsed_s,
            })
            total = usage.get("total_tokens") if isinstance(usage, dict) else None
            prompt = usage.get("prompt_tokens") if isinstance(usage, dict) else None
            completion_tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
            if any(isinstance(v, (int, float)) for v in (total, prompt, completion_tokens)):
                state.setdefault("token_events", []).append({
                    "ts_epoch": epoch(), "provider": lease.provider, "model": lease.model,
                    "total_tokens": total, "prompt_tokens": prompt,
                    "completion_tokens": completion_tokens,
                    "macrocycle_id": lease.macrocycle_id,
                })

    def snapshot(self, provider: str | None = None) -> dict[str, Any]:
        with self.locked_state() as state:
            active = list(state.get("active", {}).values())
            recent = list(state.get("recent", []))[-40:]
            events = list(state.get("token_events", []))
            if provider:
                active = [x for x in active if x.get("provider") == provider]
                recent = [x for x in recent if x.get("provider") == provider]
                events = [x for x in events if x.get("provider") == provider]
            t = epoch()
            minute = [x for x in events if float(x.get("ts_epoch", 0)) >= t - 60]
            day = [x for x in events if float(x.get("ts_epoch", 0)) >= t - 86400]
            def tsum(xs: list[dict[str, Any]]) -> int:
                return int(sum(int(x.get("total_tokens") or 0) for x in xs))
            return {
                "active": active,
                "recent": recent,
                "token_observation": {
                    "last_60s_total_tokens": tsum(minute),
                    "last_24h_total_tokens": tsum(day),
                    "last_60s_requests": len(minute),
                    "last_24h_requests": len(day),
                },
            }


def parse_optional_int(name: str) -> int | None:
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        val = int(raw)
    except ValueError:
        return None
    return val if val > 0 else None


def provider_budget_ok(coord: SharedCoordinator, provider: str, reserve_tokens: int) -> tuple[bool, dict[str, Any]]:
    snap = coord.snapshot(provider)
    obs = snap["token_observation"]
    prefix = provider.upper()
    tpm = parse_optional_int(f"CLAY_{prefix}_TPM_BUDGET")
    tpd = parse_optional_int(f"CLAY_{prefix}_TPD_BUDGET")
    rpm = parse_optional_int(f"CLAY_{prefix}_RPM_BUDGET")
    rpd = parse_optional_int(f"CLAY_{prefix}_RPD_BUDGET")
    checks = {
        "configured_tpm": tpm, "configured_tpd": tpd,
        "configured_rpm": rpm, "configured_rpd": rpd, **obs,
    }
    if tpm is not None and obs["last_60s_total_tokens"] + reserve_tokens > tpm:
        return False, checks
    if tpd is not None and obs["last_24h_total_tokens"] + reserve_tokens > tpd:
        return False, checks
    if rpm is not None and obs["last_60s_requests"] + 1 > rpm:
        return False, checks
    if rpd is not None and obs["last_24h_requests"] + 1 > rpd:
        return False, checks
    return True, checks


def worker_prompt(protocol: str, lease: Lease, state_context: str,
                  peer_snapshot: dict[str, Any], token_obs: dict[str, Any]) -> str:
    peers = json.dumps(peer_snapshot, ensure_ascii=False, separators=(",", ":"))
    tokens = json.dumps(token_obs, ensure_ascii=False, separators=(",", ":"))
    return f"""{protocol}

module clay.swarm.trigger.child_go
let parent_trigger = \"{lease.parent_trigger}\"
let child_trigger = \"go\"
let macrocycle_id = \"{lease.macrocycle_id}\"
let lease_id = \"{lease.lease_id}\"
let lane = \"{lease.lane}\"
let worker_serial = {lease.worker_serial}

COORDINATION LAW
- This is a CHILD `go` inside the existing parent macrocycle, not a new user macrocycle.
- Do NOT mint another macrocycle_id.
- Do NOT initiate a bounded unusual experiment; unusual-experiment count for this worker is 0 unless a separate upstream atomic lease explicitly assigns it.
- Your lane is atomically leased. Stay inside it; do not duplicate another active worker's lane.
- Observe ACTIVE_PEERS_AND_RECENT_WORK before forming the next hypothesis. If another worker already covers an idea, attack it, discriminate it, replicate independently, or choose a non-overlapping subproblem inside your leased lane.
- TOKEN_OBSERVATION is coordination telemetry, not provider entitlement. Never infer more quota than measured/configured. 429/402/authority failures remain authoritative.

TASK
{lease.task}

ACTIVE_PEERS_AND_RECENT_WORK
{peers}

TOKEN_OBSERVATION
{tokens}

REPOSITORY_STATE_SNAPSHOT
{state_context}

OUTPUT CONTRACT
1. Substantive result first in ClayCode/GRF form using R0..R6, Hyperposition and omega where applicable.
2. Explicitly identify which peer work you observed and how you avoided duplicate work.
3. Never invent execution, measurements, repository writes, token availability, provider capability or PASS.
4. Preserve strongest counterhypothesis and cheapest next discriminator.
5. End with `DEUTSCHE_ZUSAMMENFASSUNG`: Ergebnis; Messstatus/Evidenzklasse; stärkster Gegenpunkt; nächster ausführbarer Schritt.
"""


async def heartbeat_loop(coord: SharedCoordinator, lease_id: str, stop: asyncio.Event, interval: float) -> None:
    while not stop.is_set():
        coord.heartbeat(lease_id)
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


async def coordinated_worker_loop(runtime: Any, protocol: str, sink: Any, coord: SharedCoordinator,
                                  deadline: float, args: argparse.Namespace, serial_counter: list[int],
                                  stop_event: asyncio.Event, macrocycle_id: str) -> None:
    avoided: set[str] = set()
    while not stop_event.is_set() and mono() < deadline:
        pair = runtime.next_key_model()
        if pair is None:
            return
        key, model = pair
        budget_ok, budget_snapshot = provider_budget_ok(coord, runtime.spec.name, args.max_tokens)
        if not budget_ok:
            await asyncio.sleep(min(30.0, 1.0 + random.random() * 3.0))
            continue
        if not await runtime.acquire(deadline):
            return
        lease: Lease | None = None
        try:
            serial_counter[0] += 1
            serial = serial_counter[0]
            lease = coord.claim(
                macrocycle_id=macrocycle_id,
                parent_trigger=args.trigger,
                provider=runtime.spec.name,
                model=model,
                key_fp=BASE.key_fingerprint(key),
                worker_serial=serial,
                max_tokens=args.max_tokens,
                avoid_lanes=avoided,
            )
            if lease is None:
                avoided.clear()
                await asyncio.sleep(0.2 + random.random() * 0.8)
                continue
            avoided.add(lease.lane)
            peer_snapshot = coord.snapshot()
            prompt = worker_prompt(
                protocol,
                lease,
                BASE.build_state_context(args.context_chars),
                {"active": peer_snapshot["active"], "recent": peer_snapshot["recent"][-20:]},
                budget_snapshot,
            )
            started = epoch()
            runtime.requests += 1
            hb_stop = asyncio.Event()
            hb_task = asyncio.create_task(heartbeat_loop(coord, lease.lease_id, hb_stop, args.heartbeat_seconds))
            try:
                try:
                    status, headers, payload = await asyncio.to_thread(
                        BASE.request_chat, runtime.spec, key, model, prompt, args.max_tokens, args.timeout
                    )
                except Exception as exc:
                    elapsed = epoch() - started
                    await runtime.on_transient_error()
                    await sink.append({
                        "schema": "CLAY_TRIGGER_SWARM_WORKER/v1", "ts": now_utc(),
                        "macrocycle_id": macrocycle_id, "parent_trigger": args.trigger, "child_trigger": "go",
                        "lease_id": lease.lease_id, "lane": lease.lane,
                        "provider": runtime.spec.name, "model": model,
                        "key_fp": BASE.key_fingerprint(key), "worker_serial": serial,
                        "http_status": "NETWORK_EXCEPTION", "classification": "NETWORK_EXCEPTION",
                        "error": f"{exc.__class__.__name__}:{str(exc)[:300]}",
                        "elapsed_s": round(elapsed, 3), "token_observation": budget_snapshot,
                    })
                    coord.finish(lease, status="NETWORK_EXCEPTION", usage={}, text="",
                                 classification="NETWORK_EXCEPTION", elapsed_s=elapsed)
                    continue

                usage = BASE.usage_from(payload)
                text = BASE.extract_text(payload) if 200 <= status < 300 else ""
                rate = {k: v for k, v in headers.items()
                        if k.startswith("x-ratelimit-") or k == "retry-after"}
                classification = "SUCCESS" if 200 <= status < 300 else "HTTP_ERROR"
                common = {
                    "schema": "CLAY_TRIGGER_SWARM_WORKER/v1", "ts": now_utc(),
                    "macrocycle_id": macrocycle_id, "parent_trigger": args.trigger, "child_trigger": "go",
                    "unusual_experiment": {"count_for_this_macrocycle": 0, "id": None},
                    "lease_id": lease.lease_id, "lane": lease.lane,
                    "provider": runtime.spec.name, "model": model,
                    "key_fp": BASE.key_fingerprint(key), "worker_serial": serial,
                    "http_status": status, "usage": usage, "rate": rate,
                    "elapsed_s": round(epoch() - started, 3),
                    "repo_head_at_prompt": BASE.git_text("rev-parse", "HEAD"),
                    "token_observation_before_call": budget_snapshot,
                }
                if 200 <= status < 300:
                    common["classification"] = "SUCCESS"
                    common["text"] = text
                    common["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    common["conformance"] = {
                        "protocol_injected": prompt.startswith(BASE.PROTOCOL_BEGIN),
                        "german_summary_marker": "DEUTSCHE_ZUSAMMENFASSUNG" in text,
                        "macrocycle_propagated": macrocycle_id in prompt,
                        "lane_lease_propagated": lease.lease_id in prompt,
                    }
                    await sink.append(common)
                    await runtime.on_success()
                    classification = "SUCCESS"
                elif status == 402:
                    classification = "PAYMENT_REQUIRED_HARD_STOP_KEY"
                    common["classification"] = classification
                    common["error_body"] = payload
                    await sink.append(common)
                    await runtime.disable_key(key)
                elif status in (401, 403):
                    classification = "AUTH_OR_ENTITLEMENT_BLOCKED_KEY"
                    common["classification"] = classification
                    common["error_body"] = payload
                    await sink.append(common)
                    await runtime.disable_key(key)
                elif status == 404:
                    classification = "MODEL_OR_ENDPOINT_UNAVAILABLE"
                    common["classification"] = classification
                    common["error_body"] = payload
                    await sink.append(common)
                    await runtime.disable_model(model)
                elif status == 429:
                    retry_after = BASE.parse_retry_after(headers, min(900.0, runtime.rate_backoff))
                    classification = "RATE_LIMIT_PROVIDER_COOLDOWN"
                    common["classification"] = classification
                    common["retry_after_s"] = retry_after
                    common["error_body"] = payload
                    await sink.append(common)
                    await runtime.on_429(retry_after)
                elif 500 <= status < 600:
                    classification = "PROVIDER_TRANSIENT_ERROR"
                    common["classification"] = classification
                    common["error_body"] = payload
                    await sink.append(common)
                    await runtime.on_transient_error()
                else:
                    classification = "NONRETRYABLE_REQUEST_ERROR"
                    common["classification"] = classification
                    common["error_body"] = payload
                    await sink.append(common)
                    runtime.errors += 1
                    await asyncio.sleep(min(30.0, 1.0 + random.random() * 4.0))
                coord.finish(
                    lease, status=status, usage=usage, text=text,
                    classification=classification, elapsed_s=epoch() - started,
                )
            finally:
                hb_stop.set()
                with contextlib.suppress(Exception):
                    await hb_task
        finally:
            if lease is not None:
                with coord.locked_state() as state:
                    state.get("active", {}).pop(lease.lease_id, None)
            await runtime.release()


async def status_loop(runtimes: list[Any], coord: SharedCoordinator, sink: Any,
                      deadline: float, stop_event: asyncio.Event,
                      macrocycle_id: str, trigger: str) -> None:
    while not stop_event.is_set() and mono() < deadline:
        await sink.status({
            "schema": "CLAY_TRIGGER_SWARM_STATUS/v1", "updated_at": now_utc(),
            "macrocycle_id": macrocycle_id, "parent_trigger": trigger, "child_trigger": "go",
            "remaining_seconds": max(0, int(deadline - mono())),
            "providers": {rt.spec.name: rt.snapshot() for rt in runtimes},
            "coordination": coord.snapshot(),
        })
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            pass


async def run(args: argparse.Namespace) -> int:
    if args.trigger not in {"go", "zero"}:
        print("trigger must be go or zero", file=sys.stderr)
        return 2
    if not BASE.truthy(os.getenv("CLAY_FREE_ONLY_ATTESTED")):
        print("Refusing: CLAY_FREE_ONLY_ATTESTED=1 is required for FREE_ONLY provider execution.", file=sys.stderr)
        return 3

    protocol = BASE.load_protocol()
    macrocycle_id = args.macrocycle_id or make_macrocycle_id(args.trigger)
    coord = SharedCoordinator(Path(args.coordination_dir).expanduser(), args.lease_ttl, args.history_limit)
    run_id = f"{args.trigger}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else coord.state_dir / "runs" / run_id
    sink = BASE.JsonlSink(output_dir)

    runtimes: list[Any] = []
    for spec in BASE.PROVIDERS:
        keys = BASE.collect_keys(spec)
        if not keys or not BASE.truthy(os.getenv(spec.attestation_env)):
            continue
        models = BASE.split_values(os.getenv(spec.models_env)) or list(spec.default_models)
        cap_env = f"CLAY_{spec.name.upper()}_MAX_CONCURRENCY"
        try:
            cap = int(os.getenv(cap_env, str(spec.default_max_concurrency)))
        except ValueError:
            cap = spec.default_max_concurrency
        rt = BASE.ProviderRuntime(spec, keys, BASE.unique(models), max(1, cap))
        if args.full_burst:
            rt.target_concurrency = rt.max_concurrency
        runtimes.append(rt)
    if not runtimes:
        print("No FREE_ONLY-attested provider keys available in this runtime.", file=sys.stderr)
        return 4

    duration_s = max(1.0, args.hours * 3600.0)
    deadline = mono() + duration_s
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    manifest = {
        "schema": "CLAY_TRIGGER_SWARM_RUN/v1", "run_id": run_id,
        "macrocycle_id": macrocycle_id, "parent_trigger": args.trigger,
        "child_trigger": "go", "started_at": now_utc(),
        "duration_hours": args.hours, "free_only": True,
        "repo_head": BASE.git_text("rev-parse", "HEAD"),
        "protocol_sha256": hashlib.sha256(protocol.encode("utf-8")).hexdigest(),
        "coordination_dir": str(coord.state_dir), "lanes": len(LANES),
        "providers": {rt.spec.name: {
            "key_fingerprints": [BASE.key_fingerprint(k) for k in rt.keys],
            "models": rt.models, "max_concurrency": rt.max_concurrency,
        } for rt in runtimes},
        "invariants": [
            "GO_AND_ZERO_PARENT_TRIGGERS", "EVERY_CHILD_IS_GO",
            "ONE_PARENT_MACROCYCLE_ID_PROPAGATED", "ATOMIC_CROSS_PROCESS_LANE_LEASES",
            "ACTIVE_PEER_OBSERVATION_BEFORE_EACH_CALL", "ROLLING_TOKEN_OBSERVATION_BEFORE_EACH_CALL",
            "OPTIONAL_EXPLICIT_TPM_TPD_RPM_RPD_BUDGETS", "NO_RATE_LIMIT_KEY_ROTATION_BYPASS",
            "HTTP_429_PROVIDER_WIDE_COOLDOWN", "HTTP_402_HARD_STOP",
            "GRF_CLAYCODE_PROTOCOL_AT_TOP", "NO_SECRETS_IN_COORDINATION_OR_RECEIPTS",
            "CHILD_WORKERS_DO_NOT_CONSUME_UNUSUAL_EXPERIMENT_SLOT",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "run_id": run_id, "macrocycle_id": macrocycle_id,
        "providers": list(manifest["providers"]),
    }, ensure_ascii=False))

    serial_counter = [0]
    tasks: list[asyncio.Task[Any]] = []
    for rt in runtimes:
        for _ in range(rt.max_concurrency):
            tasks.append(asyncio.create_task(coordinated_worker_loop(
                rt, protocol, sink, coord, deadline, args,
                serial_counter, stop_event, macrocycle_id
            )))
    tasks.append(asyncio.create_task(status_loop(
        runtimes, coord, sink, deadline, stop_event, macrocycle_id, args.trigger
    )))

    sleep_task = asyncio.create_task(asyncio.sleep(duration_s))
    stop_task = asyncio.create_task(stop_event.wait())
    _, pending = await asyncio.wait({sleep_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
    stop_event.set()
    for task in pending:
        task.cancel()
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=args.drain_seconds)
    except asyncio.TimeoutError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    final = {
        "schema": "CLAY_TRIGGER_SWARM_FINAL/v1", "run_id": run_id,
        "macrocycle_id": macrocycle_id, "parent_trigger": args.trigger,
        "finished_at": now_utc(), "workers_started": serial_counter[0],
        "providers": {rt.spec.name: rt.snapshot() for rt in runtimes},
        "coordination": coord.snapshot(),
    }
    (output_dir / "final.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    await sink.status(final)
    print(json.dumps(final, ensure_ascii=False))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Coordinated FREE_ONLY go/zero Mini Entity swarm")
    p.add_argument("trigger", choices=("go", "zero"),
                   help="parent user trigger; spawned workers always receive child go")
    p.add_argument("--hours", type=float, default=24.0)
    p.add_argument("--max-tokens", type=int, default=1800)
    p.add_argument("--context-chars", type=int, default=18000)
    p.add_argument("--timeout", type=float, default=180.0)
    p.add_argument("--drain-seconds", type=float, default=240.0)
    p.add_argument("--lease-ttl", type=float, default=360.0)
    p.add_argument("--heartbeat-seconds", type=float, default=30.0)
    p.add_argument("--history-limit", type=int, default=160)
    p.add_argument("--coordination-dir", default=str(DEFAULT_STATE_DIR))
    p.add_argument("--output-dir", default="")
    p.add_argument("--macrocycle-id", default="",
                   help="only pass an orchestrator-issued id; otherwise this parent invocation mints one")
    p.add_argument("--full-burst", action=argparse.BooleanOptionalAction, default=True,
                   help="start each provider at configured concurrency cap; 429 still halves/cools provider-wide")
    return p.parse_args(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run(parse_args())))
    except KeyboardInterrupt:
        raise SystemExit(130)
