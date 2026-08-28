#!/usr/bin/env python3
"""24h FREE_ONLY EntityOS/HCU `go` swarm controller.

Pure stdlib, OpenAI-compatible HTTP endpoints. Provider credentials are read only
after canonical typed provider admission establishes cost_class=FREE. Environment
attestations remain secondary compatibility assertions and cannot self-admit a
provider. The controller never upgrades billing, never retries HTTP 402, and
treats HTTP 429 as a provider-wide cooldown rather than rotating keys to evade a
rate limit.
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import time
from typing import Any
import urllib.error
import urllib.request

from free_provider_admission import (
    ProviderAdmissionError,
    load_provider_admission,
    provider_is_admitted_free,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
BOOTSTRAP_PATH = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE_PATH = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
OWNER_DIRECTIVE_PATH = ROOT / "research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md"

PROTOCOL_BEGIN = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
PROTOCOL_END = "[/MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"

DEFAULT_ROLES = [
    ("ARCHITECT", "Find the highest-information architecture convergence step for the current Mini Entity product. Produce ClayCode-first GRF alternatives, strongest counterarchitecture, discriminator, and an implementable delta."),
    ("FALSIFIER", "Attack the strongest current Mini Entity assumption. Seek a concrete counterexample in truth authority, effect authority, atomicity, inference boundaries, or persistence. Prefer a cheap executable falsifier."),
    ("CLAYCODE_FORGE", "Advance ClayCode semantics/compiler/runtime only where it directly improves Mini Entity. Express proposed semantics, invariants, tests, and implementation in ClayCode-first form."),
    ("UNIFIEDDB", "Analyze MiniUnifiedDB canonical-state authority, CAS/exactly-once/atomic persistence, crash ambiguity, generations, and recovery. Produce one highest-value ClayCode-first test or repair."),
    ("PARITY", "Find reference/native/profile-v2 divergence or unproven parity. Generate a differential test matrix and the smallest product-converging repair."),
    ("LOCAL_INFERENCE", "Advance replaceable local inference without state reset. Stress local_exec boundaries, model/backend switching, receipts, timeout/error semantics, and fail-closed behavior."),
    ("COGNITION_1B", "Advance or falsify the approximately-1B ClayCode cognition lane: GRF/Hyperposition/omega, OOD/compositional generalization, benchmark design, quantization/RSS, and generic local integration. Do not claim unmeasured results."),
    ("SECURITY", "Adversarially inspect truth/secret/effect gates, stale-generation rejection, prompt/runtime configuration boundaries, and model-output authority. Produce concrete negative tests."),
    ("RECOVERY", "Inspect provenance, crash recovery, UNKNOWN preservation, duplicate-effect prevention, and receipt binding. Seek an ambiguity that current contracts mishandle."),
    ("TESTER", "Design the cheapest executable discriminators that separate the leading Mini Entity hypotheses. Include positive, negative, mutation/property, differential, and failure-path tests where useful."),
    ("REVIEWER", "Review the current Mini Entity frontier for source-only overclaims, stale evidence, hidden coupling, duplicated semantics, and missing exact-identity execution. Return ClayCode-first corrections."),
    ("SYNTHESIZER", "Fuse current Mini Entity constraints into one nonredundant next step. Preserve conflicting evidence and Hyperpositions; do not average away disagreement."),
]

@dataclasses.dataclass(frozen=True)
class ProviderSpec:
    name: str
    endpoint: str
    key_envs: tuple[str, ...]
    keys_list_env: str
    models_env: str
    default_models: tuple[str, ...]
    attestation_env: str
    default_max_concurrency: int

PROVIDERS = (
    ProviderSpec(
        name="groq",
        endpoint="https://api.groq.com/openai/v1/chat/completions",
        key_envs=("GROQ_API_KEY",),
        keys_list_env="GROQ_API_KEYS",
        models_env="GROQ_SWARM_MODELS",
        default_models=("openai/gpt-oss-120b", "qwen/qwen3.6-27b", "openai/gpt-oss-20b"),
        attestation_env="CLAY_GROQ_FREE_ATTESTED",
        default_max_concurrency=12,
    ),
    ProviderSpec(
        name="mistral",
        endpoint="https://api.mistral.ai/v1/chat/completions",
        key_envs=("MISTRAL_API_KEY",),
        keys_list_env="MISTRAL_API_KEYS",
        models_env="MISTRAL_SWARM_MODELS",
        default_models=("mistral-small-latest",),
        attestation_env="CLAY_MISTRAL_FREE_ATTESTED",
        default_max_concurrency=6,
    ),
    ProviderSpec(
        name="nvidia",
        endpoint="https://integrate.api.nvidia.com/v1/chat/completions",
        key_envs=("NVIDIA_API_KEY", "NGC_API_KEY"),
        keys_list_env="NVIDIA_API_KEYS",
        models_env="NVIDIA_SWARM_MODELS",
        default_models=(
            "nvidia/nemotron-3-super-120b-a12b",
            "nvidia/nemotron-3-ultra-550b-a55b",
            "nvidia/nemotron-mini-4b-instruct",
        ),
        attestation_env="CLAY_NVIDIA_FREE_ATTESTED",
        default_max_concurrency=12,
    ),
)


def truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on", "attested"}


def split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in re.split(r"[,\n;]+", value) if x.strip()]


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def provider_execution_admitted(spec: ProviderSpec) -> bool:
    """Resolve every direct base-controller execution gate without reading secrets."""
    return (
        truthy(os.getenv("CLAY_FREE_ONLY_ATTESTED"))
        and truthy(os.getenv(spec.attestation_env))
        and provider_is_admitted_free(spec.name)
    )


def collect_keys(spec: ProviderSpec, admission: dict[str, Any] | None = None) -> list[str]:
    """Read provider credentials only after canonical typed FREE admission.

    ``admission`` is retained for caller compatibility but is deliberately not an
    authority input: a caller-supplied dictionary must never self-grant access to
    credential values. Environment names are scanned without materializing all
    environment values, so admitting one provider cannot read another provider's
    blocked credential as a side effect.
    """
    del admission
    if not provider_execution_admitted(spec):
        return []
    keys = split_values(os.getenv(spec.keys_list_env))
    for name in spec.key_envs:
        value = os.getenv(name)
        if value:
            keys.append(value.strip())
    prefixes = tuple(name + "_" for name in spec.key_envs)
    for env_name in os.environ:
        if not any(env_name.startswith(prefix) for prefix in prefixes):
            continue
        value = os.environ[env_name]
        if value.strip():
            keys.append(value.strip())
    return unique(keys)


def key_fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]


def git_text(*args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), *args], text=True, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
        return proc.stdout.strip()
    except Exception:
        return "UNKNOWN"


def read_bounded(path: Path, limit: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"UNAVAILABLE:{path}:{exc.__class__.__name__}"
    if len(text) <= limit:
        return text
    half = max(1, limit // 2)
    return text[:half] + "\n...[TRUNCATED]...\n" + text[-half:]


def load_protocol() -> str:
    """Resolve the current machine-readable worker authority first.

    The unversioned all-workers file became a successor-dynamic pointer at 8.71,
    so requiring an old embedded MINI ENTITY marker there incorrectly killed the
    live 6000-worker fabric. Reuse the current-authority resolver shared with Xeno;
    retain marker extraction only as a historical compatibility fallback.
    """
    live_error: Exception | None = None
    try:
        from xeno_current_authority_protocol import build_protocol
        protocol = build_protocol(ROOT)
        if PROTOCOL_BEGIN in protocol and PROTOCOL_END in protocol:
            return protocol
        live_error = RuntimeError("current authority builder returned no protocol envelope")
    except Exception as exc:
        live_error = exc

    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    start = text.find(PROTOCOL_BEGIN)
    end = text.find(PROTOCOL_END, start)
    if start >= 0 and end >= 0:
        return text[start : end + len(PROTOCOL_END)]
    raise RuntimeError(
        "current worker authority resolution failed and historical protocol block is absent: "
        f"{type(live_error).__name__}:{live_error}"
    )


def build_state_context(max_chars: int) -> str:
    head = git_text("rev-parse", "HEAD")
    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    status = git_text("status", "--short") or "CLEAN"
    each = max(1500, max_chars // 4)
    payload = {
        "repo_head": head, "repo_branch": branch, "git_status": status[:3000],
        "bootstrap": read_bounded(BOOTSTRAP_PATH, each),
        "program_state": read_bounded(PROGRAM_STATE_PATH, each),
        "supervisor_inbox": read_bounded(SUPERVISOR_PATH, each),
        "owner_directive": read_bounded(OWNER_DIRECTIVE_PATH, each),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:max_chars]


def parse_retry_after(headers: dict[str, str], fallback: float) -> float:
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if raw:
        try:
            return max(0.5, float(raw))
        except ValueError:
            pass
    return fallback


def request_chat(spec: ProviderSpec, key: str, model: str, prompt: str,
                 max_tokens: int, timeout: float) -> tuple[int, dict[str, str], dict[str, Any] | str]:
    if not provider_execution_admitted(spec):
        raise ProviderAdmissionError(f"PROVIDER_NETWORK_REQUIRES_TYPED_FREE_ADMISSION:{spec.name}")
    body: dict[str, Any] = {
        "model": model, "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": 0.7, "stream": False,
    }
    req = urllib.request.Request(
        spec.endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent":"clay-entityos-swarm/3.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            headers = {k.lower(): v for k, v in resp.headers.items()}
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw
            return int(resp.status), headers, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        return int(exc.code), headers, parsed


def extract_text(payload: dict[str, Any] | str) -> str:
    if not isinstance(payload, dict):
        return str(payload)
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)


def usage_from(payload: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("usage"), dict):
        return payload["usage"]
    return {}


class JsonlSink:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.path = output_dir / "workers.jsonl"
        self.status_path = output_dir / "status.json"
        self._lock = asyncio.Lock()

    async def append(self, item: dict[str, Any]) -> None:
        async with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
                fh.flush()

    async def status(self, item: dict[str, Any]) -> None:
        async with self._lock:
            tmp = self.status_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            tmp.replace(self.status_path)


class ProviderRuntime:
    def __init__(self, spec: ProviderSpec, keys: list[str], models: list[str], max_concurrency: int) -> None:
        self.spec, self.keys, self.models = spec, keys, models
        self.max_concurrency = max(1, max_concurrency)
        self.target_concurrency = min(max(1, len(keys)), self.max_concurrency)
        self.active = 0
        self.cooldown_until = 0.0
        self.rate_backoff = 2.0
        self.success_streak = 0
        self.disabled_keys: set[str] = set()
        self.disabled_models: set[str] = set()
        self.requests = self.successes = self.rate_limits = self.errors = 0
        self._condition = asyncio.Condition()
        self._cursor = 0

    def enabled_keys(self) -> list[str]:
        return [k for k in self.keys if key_fingerprint(k) not in self.disabled_keys]

    def enabled_models(self) -> list[str]:
        return [m for m in self.models if m not in self.disabled_models]

    def next_key_model(self) -> tuple[str, str] | None:
        keys, models = self.enabled_keys(), self.enabled_models()
        if not keys or not models:
            return None
        n = len(keys) * len(models)
        idx = self._cursor % n
        self._cursor += 1
        return keys[(idx // len(models)) % len(keys)], models[idx % len(models)]

    async def acquire(self, deadline: float) -> bool:
        while time.monotonic() < deadline:
            async with self._condition:
                wait_cooldown = self.cooldown_until - time.monotonic()
                if wait_cooldown <= 0 and self.active < self.target_concurrency:
                    self.active += 1
                    return True
                timeout = min(5.0, max(0.2, wait_cooldown)) if wait_cooldown > 0 else 0.5
                try:
                    await asyncio.wait_for(self._condition.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    pass
        return False

    async def release(self) -> None:
        async with self._condition:
            self.active = max(0, self.active - 1)
            self._condition.notify_all()

    async def on_success(self) -> None:
        async with self._condition:
            self.successes += 1
            self.success_streak += 1
            self.rate_backoff = max(2.0, self.rate_backoff * 0.8)
            threshold = max(4, self.target_concurrency * 2)
            if self.success_streak >= threshold and self.target_concurrency < self.max_concurrency:
                self.target_concurrency += 1
                self.success_streak = 0
            self._condition.notify_all()

    async def on_429(self, retry_after: float) -> None:
        async with self._condition:
            self.rate_limits += 1
            self.success_streak = 0
            self.target_concurrency = max(1, self.target_concurrency // 2)
            delay = max(retry_after, self.rate_backoff) + random.uniform(0.25, 1.5)
            self.cooldown_until = max(self.cooldown_until, time.monotonic() + delay)
            self.rate_backoff = min(900.0, max(2.0, self.rate_backoff * 2.0))
            self._condition.notify_all()

    async def on_transient_error(self) -> None:
        async with self._condition:
            self.errors += 1
            delay = min(120.0, 2.0 + random.uniform(0.5, 3.0) + self.errors ** 0.5)
            self.cooldown_until = max(self.cooldown_until, time.monotonic() + delay)
            self._condition.notify_all()

    async def disable_key(self, key: str) -> None:
        async with self._condition:
            self.disabled_keys.add(key_fingerprint(key))
            self._condition.notify_all()

    async def disable_model(self, model: str) -> None:
        async with self._condition:
            self.disabled_models.add(model)
            self._condition.notify_all()

    def snapshot(self) -> dict[str, Any]:
        return {
            "keys_total": len(self.keys), "keys_enabled": len(self.enabled_keys()),
            "models_enabled": self.enabled_models(), "target_concurrency": self.target_concurrency,
            "max_concurrency": self.max_concurrency, "active": self.active,
            "cooldown_seconds": round(max(0.0, self.cooldown_until - time.monotonic()), 2),
            "requests": self.requests, "successes": self.successes,
            "rate_limits": self.rate_limits, "errors": self.errors,
        }


async def worker_loop(runtime: ProviderRuntime, worker_id: int, protocol: str, sink: JsonlSink,
                      deadline: float, args: argparse.Namespace, serial_counter: list[int], stop_event: asyncio.Event) -> None:
    while not stop_event.is_set() and time.monotonic() < deadline:
        if not await runtime.acquire(deadline):
            break
        pair = runtime.next_key_model()
        if pair is None:
            await runtime.release()
            break
        key, model = pair
        serial_counter[0] += 1
        serial = serial_counter[0]
        role, task = DEFAULT_ROLES[(serial - 1) % len(DEFAULT_ROLES)]
        prompt = worker_prompt(protocol, role, task, build_state_context(args.context_chars), serial)
        started = time.time()
        runtime.requests += 1
        common: dict[str, Any] = {
            "schema":"CLAY_FREE_GO_SWARM_WORKER/v1", "ts":dt.datetime.now(dt.timezone.utc).isoformat(),
            "provider":runtime.spec.name, "model":model, "key_fp":key_fingerprint(key), "role":role,
            "worker_id":worker_id, "worker_serial":serial, "repo_head_at_prompt":git_text("rev-parse","HEAD"),
        }
        try:
            try:
                status, headers, payload = await asyncio.to_thread(
                    request_chat, runtime.spec, key, model, prompt, args.max_tokens, args.timeout
                )
            except Exception as exc:
                await runtime.on_transient_error()
                common.update({"http_status":"NETWORK_EXCEPTION","error":f"{exc.__class__.__name__}:{str(exc)[:300]}","elapsed_s":round(time.time()-started,3)})
                await sink.append(common)
                continue
            common.update({"http_status":status,"elapsed_s":round(time.time()-started,3),"usage":usage_from(payload),
                           "rate":{k:v for k,v in headers.items() if k.startswith("x-ratelimit-") or k=="retry-after"}})
            if 200 <= status < 300:
                text = extract_text(payload); common["text"] = text
                common["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
                common["conformance"] = {
                    "protocol_injected": prompt.startswith(PROTOCOL_BEGIN),
                    "german_summary_marker":"DEUTSCHE_ZUSAMMENFASSUNG" in text,
                    "grf_marker":"GRF" in text,
                }
                await sink.append(common); await runtime.on_success(); continue
            if status == 402:
                common["classification"]="PAYMENT_REQUIRED_HARD_STOP_KEY"; common["error_body"]=payload
                await sink.append(common); await runtime.disable_key(key); continue
            if status in (401,403):
                common["classification"]="AUTH_OR_ENTITLEMENT_BLOCKED_KEY"; common["error_body"]=payload
                await sink.append(common); await runtime.disable_key(key); continue
            if status == 404:
                common["classification"]="MODEL_OR_ENDPOINT_UNAVAILABLE"; common["error_body"]=payload
                await sink.append(common); await runtime.disable_model(model); continue
            if status == 429:
                retry_after=parse_retry_after(headers,min(900.0,runtime.rate_backoff))
                common["classification"]="RATE_LIMIT_PROVIDER_COOLDOWN"; common["retry_after_s"]=retry_after; common["error_body"]=payload
                await sink.append(common); await runtime.on_429(retry_after); continue
            if 500 <= status < 600:
                common["classification"]="PROVIDER_TRANSIENT_ERROR"; common["error_body"]=payload
                await sink.append(common); await runtime.on_transient_error(); continue
            common["classification"]="NONRETRYABLE_REQUEST_ERROR"; common["error_body"]=payload
            runtime.errors += 1; await sink.append(common)
        finally:
            await runtime.release()


def worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    return f"""{protocol}

You are temporary Clay research organ #{serial}. You are not a new persistent entity.
Current product: EntityOS. Current integrated cognition/compute architecture: HCU.
Role: {role}
Role task: {task}

RULES FOR THIS RUN
- Work on EntityOS/HCU only. Xeno/XCU names may appear only as transitional aliases where exact history requires them.
- Use supplied repository/runtime facts as evidence, not permission to invent unobserved PASS states.
- Follow current FREE_ONLY authority exactly. Never suggest paid fallback or Together.
- No plaintext credentials, access tokens, private keys, refresh tokens, passwords, or session material in output.
- Model/J-Space/world-model output is candidate/projection evidence only, never canonical state/effect authority.
- Prefer one concrete architecture delta, falsifier, patch, benchmark, or experiment over broad advice.
- If external research would resolve the blocker, name exact sources/repos/papers/tools and the discriminating experiment.
- Preserve contradictions and strongest counterhypothesis; do not average them away.
- End with a concise section named DEUTSCHE_ZUSAMMENFASSUNG containing: Befund, Gegenhypothese, naechster Test, erwartetes messbares Delta.

CURRENT STATE CONTEXT
{state_context}
"""


async def status_loop(runtimes: list[ProviderRuntime], sink: JsonlSink, deadline: float,
                      stop_event: asyncio.Event, run_id: str) -> None:
    while not stop_event.is_set() and time.monotonic() < deadline:
        await sink.status({
            "schema":"CLAY_FREE_GO_SWARM_STATUS/v1", "run_id":run_id,
            "updated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
            "remaining_seconds":max(0,int(deadline-time.monotonic())),
            "providers":{rt.spec.name:rt.snapshot() for rt in runtimes},
        })
        try:
            await asyncio.wait_for(stop_event.wait(),timeout=5.0)
        except asyncio.TimeoutError:
            pass


async def run(args: argparse.Namespace) -> int:
    try:
        admission = load_provider_admission()
    except ProviderAdmissionError as exc:
        print(f"typed provider admission invalid: {exc}", file=sys.stderr)
        return 5
    if not truthy(os.getenv("CLAY_FREE_ONLY_ATTESTED")):
        print("CLAY_FREE_ONLY_ATTESTED compatibility assertion missing; refusing external provider calls",file=sys.stderr)
        return 3
    protocol = load_protocol()
    runtimes: list[ProviderRuntime] = []
    for spec in PROVIDERS:
        if not provider_is_admitted_free(spec.name, admission):
            continue
        if not truthy(os.getenv(spec.attestation_env)):
            continue
        keys=collect_keys(spec,admission)
        if not keys:
            continue
        models=split_values(os.getenv(spec.models_env)) or list(spec.default_models)
        cap=int(os.getenv(f"CLAY_{spec.name.upper()}_MAX_CONCURRENCY",str(spec.default_max_concurrency)))
        runtimes.append(ProviderRuntime(spec,keys,unique(models),cap))
    if not runtimes:
        print("no provider runtime available",file=sys.stderr); return 4
    run_id=dt.datetime.now(dt.timezone.utc).strftime("go-%Y%m%dT%H%M%SZ")
    out=Path(args.output_dir) if args.output_dir else Path("/artifacts/clay-entityos-swarm")/run_id
    sink=JsonlSink(out); duration_s=max(1.0,args.hours*3600.0); deadline=time.monotonic()+duration_s
    stop_event=asyncio.Event(); loop=asyncio.get_running_loop()
    for sig in (signal.SIGINT,signal.SIGTERM):
        try:loop.add_signal_handler(sig,stop_event.set)
        except NotImplementedError:pass
    manifest={
        "schema":"CLAY_FREE_GO_SWARM_RUN/v1","run_id":run_id,"started_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "duration_hours":args.hours,"free_only":True,"provider_admission_epoch":admission.get("authority_epoch"),
        "repo_head":git_text("rev-parse","HEAD"),"repo_status":git_text("status","--short"),
        "protocol_sha256":hashlib.sha256(protocol.encode()).hexdigest(),
        "providers":{rt.spec.name:{"key_fingerprints":[key_fingerprint(k) for k in rt.keys],"models":rt.models,"max_concurrency":rt.max_concurrency} for rt in runtimes},
        "invariants":["EntityOS only","HCU only","FREE_ONLY","typed provider admission","no paid fallback","429 provider-wide cooldown","402 hard stop key","candidate outputs noncanonical"]
    }
    out.mkdir(parents=True,exist_ok=True); (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    workers=[]
    for rt in runtimes:
        for i in range(rt.max_concurrency):workers.append(asyncio.create_task(worker_loop(rt,i,protocol,sink,deadline,args,[0],stop_event)))
    status_task=asyncio.create_task(status_loop(runtimes,sink,deadline,stop_event,run_id))
    sleep_task=asyncio.create_task(asyncio.sleep(duration_s)); stop_task=asyncio.create_task(stop_event.wait())
    _, pending=await asyncio.wait({sleep_task,stop_task},return_when=asyncio.FIRST_COMPLETED); stop_event.set()
    for task in pending:task.cancel()
    try:await asyncio.wait_for(asyncio.gather(*workers,status_task,return_exceptions=True),timeout=args.drain_seconds)
    except asyncio.TimeoutError:
        for task in workers:task.cancel()
        status_task.cancel(); await asyncio.gather(*workers,status_task,return_exceptions=True)
    final={"schema":"CLAY_FREE_GO_SWARM_FINAL/v1","run_id":run_id,"finished_at":dt.datetime.now(dt.timezone.utc).isoformat(),"providers":{rt.spec.name:rt.snapshot() for rt in runtimes}}
    await sink.status(final); (out/"final.json").write_text(json.dumps(final,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); print(json.dumps(final,ensure_ascii=False)); return 0


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(description="Run the FREE_ONLY EntityOS/HCU go swarm")
    p.add_argument("--hours",type=float,default=24.0); p.add_argument("--max-tokens",type=int,default=1800)
    p.add_argument("--context-chars",type=int,default=18000); p.add_argument("--timeout",type=float,default=180.0)
    p.add_argument("--drain-seconds",type=float,default=240.0); p.add_argument("--output-dir",default="")
    return p.parse_args()


if __name__ == "__main__": raise SystemExit(asyncio.run(run(parse_args())))
