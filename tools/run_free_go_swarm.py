#!/usr/bin/env python3
"""EntityOS/HCU FREE_ONLY adaptive research-swarm controller.

Security boundary: typed provider admission is resolved before any provider-key
environment lookup or network operation. Environment attestation flags are not
authority. Only cost_class=FREE may enter the credential/network region.
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

from free_swarm_provider_admission import AdmissionDocument, AdmissionError, admitted_free_providers, load_admission

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_8_63.md"
BOOTSTRAP_PATH = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE_PATH = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
OWNER_DIRECTIVE_PATH = ROOT / "governance/CLAY_24H_EXTERNAL_WORKER_SWARM_POLICY.md"

DEFAULT_ROLES = [
    ("ARCHITECT", "Advance EntityOS/HCU architecture with one measurable delta and strongest counterarchitecture."),
    ("FALSIFIER", "Attack the strongest EntityOS/HCU assumption and design the cheapest executable falsifier."),
    ("CLAYCODE_FORGE", "Produce a minimal ClayCode-native implementation, invariants, tests and migration path."),
    ("HCU_CAUSAL", "Advance typed entry through verified loader/model execution to inference/J-Space/training evidence without overclaiming."),
    ("MEMORY_JSPACE", "Stress memory/J-Space provenance, replay, vector control, ablation and recovery semantics."),
    ("SECURITY", "Adversarially inspect truth/effect/capability boundaries and concrete negative tests."),
    ("SYNTHESIZER", "Fuse nonredundant findings while preserving disagreement and provenance."),
]


@dataclasses.dataclass(frozen=True)
class ProviderSpec:
    name: str
    endpoint: str
    key_envs: tuple[str, ...]
    keys_list_env: str
    models_env: str
    default_models: tuple[str, ...]
    default_max_concurrency: int


PROVIDERS = (
    ProviderSpec("groq", "https://api.groq.com/openai/v1/chat/completions", ("GROQ_API_KEY",), "GROQ_API_KEYS", "GROQ_SWARM_MODELS", ("openai/gpt-oss-120b", "qwen/qwen3.6-27b", "openai/gpt-oss-20b"), 12),
    ProviderSpec("mistral", "https://api.mistral.ai/v1/chat/completions", ("MISTRAL_API_KEY",), "MISTRAL_API_KEYS", "MISTRAL_SWARM_MODELS", ("mistral-small-latest",), 6),
    ProviderSpec("nvidia", "https://integrate.api.nvidia.com/v1/chat/completions", ("NVIDIA_API_KEY", "NGC_API_KEY", "NVIDIA_NIM_API_KEY"), "NVIDIA_API_KEYS", "NVIDIA_SWARM_MODELS", ("nvidia/nemotron-3-super-120b-a12b", "nvidia/nemotron-3-ultra-550b-a55b"), 12),
)


def split_values(value: str | None) -> list[str]:
    return [x.strip() for x in re.split(r"[,\n;]+", value or "") if x.strip()]


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def collect_keys(spec: ProviderSpec) -> list[str]:
    """Credential region. Call only after typed FREE admission for spec.name."""
    keys = split_values(os.getenv(spec.keys_list_env))
    for name in spec.key_envs:
        value = os.getenv(name)
        if value:
            keys.append(value.strip())
    prefixes = tuple(name + "_" for name in spec.key_envs)
    for env_name, value in os.environ.items():
        if any(env_name.startswith(prefix) for prefix in prefixes) and value.strip():
            keys.append(value.strip())
    return unique(keys)


def key_fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:10]


def git_text(*args: str) -> str:
    try:
        p = subprocess.run(["git", "-C", str(ROOT), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False)
        return p.stdout.strip()
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
    return read_bounded(PROTOCOL_PATH, 12000)


def build_state_context(max_chars: int) -> str:
    each = max(1000, max_chars // 4)
    payload = {
        "repo_head": git_text("rev-parse", "HEAD"),
        "bootstrap": read_bounded(BOOTSTRAP_PATH, each),
        "program_state": read_bounded(PROGRAM_STATE_PATH, each),
        "supervisor_inbox": read_bounded(SUPERVISOR_PATH, each),
        "owner_directive": read_bounded(OWNER_DIRECTIVE_PATH, each),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:max_chars]


def request_chat(spec: ProviderSpec, key: str, model: str, prompt: str, max_tokens: int, timeout: float):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0.7, "stream": False}
    req = urllib.request.Request(spec.endpoint, data=json.dumps(body).encode(), method="POST", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "clay-entityos-hcu-free-swarm/2"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            headers = {k.lower(): v for k, v in resp.headers.items()}
            try: payload = json.loads(raw)
            except json.JSONDecodeError: payload = raw
            return int(resp.status), headers, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        try: payload = json.loads(raw)
        except json.JSONDecodeError: payload = raw
        return int(exc.code), headers, payload


def _extract_text(payload: Any) -> str:
    try: value = payload["choices"][0]["message"]["content"]
    except (TypeError, KeyError, IndexError): return ""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _usage(payload: Any) -> dict[str, Any]:
    return payload.get("usage", {}) if isinstance(payload, dict) and isinstance(payload.get("usage"), dict) else {}


class ProviderRuntime:
    def __init__(self, spec: ProviderSpec, keys: list[str], models: list[str], max_concurrency: int):
        self.spec, self.keys, self.models = spec, keys, models
        self.max_concurrency = max(1, max_concurrency)
        self.target_concurrency = min(max(1, len(keys)), self.max_concurrency)
        self.active = self.requests = self.successes = self.rate_limits = self.errors = 0
        self.cooldown_until = 0.0
        self.rate_backoff = 2.0
        self.disabled_keys: set[str] = set()
        self.disabled_models: set[str] = set()
        self._condition = asyncio.Condition()
        self._cursor = 0

    def pair(self):
        keys = [k for k in self.keys if key_fingerprint(k) not in self.disabled_keys]
        models = [m for m in self.models if m not in self.disabled_models]
        if not keys or not models: return None
        idx = self._cursor % (len(keys) * len(models)); self._cursor += 1
        return keys[(idx // len(models)) % len(keys)], models[idx % len(models)]

    async def acquire(self, deadline: float) -> bool:
        while time.monotonic() < deadline:
            async with self._condition:
                wait = self.cooldown_until - time.monotonic()
                if wait <= 0 and self.active < self.target_concurrency:
                    self.active += 1; return True
                try: await asyncio.wait_for(self._condition.wait(), timeout=min(5.0, max(.2, wait)) if wait > 0 else .5)
                except asyncio.TimeoutError: pass
        return False

    async def release(self):
        async with self._condition:
            self.active = max(0, self.active - 1); self._condition.notify_all()

    def snapshot(self):
        return {"keys_total": len(self.keys), "models": [m for m in self.models if m not in self.disabled_models], "target_concurrency": self.target_concurrency, "active": self.active, "requests": self.requests, "successes": self.successes, "rate_limits": self.rate_limits, "errors": self.errors}


class JsonlSink:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir; output_dir.mkdir(parents=True, exist_ok=True)
        self.path = output_dir / "workers.jsonl"; self.status_path = output_dir / "status.json"; self._lock = asyncio.Lock()
    async def append(self, item):
        async with self._lock:
            with self.path.open("a", encoding="utf-8") as fh: fh.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    async def status(self, item):
        async with self._lock:
            tmp = self.status_path.with_suffix(".tmp"); tmp.write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n"); tmp.replace(self.status_path)


def worker_prompt(protocol: str, role: str, task: str, state: str, serial: int) -> str:
    return f"""[CLAY :: ENTITYOS/HCU WORKER]
Persistent entity: Clay. You are a temporary organ. Product: EntityOS. Architecture: HCU. FREE_ONLY.
{protocol}
role={role} serial={serial}\nTASK={task}\nSTATE={state}\nReturn evidence-bounded results, strongest counterhypothesis, discriminator, and DEUTSCHE_ZUSAMMENFASSUNG.
[/CLAY :: ENTITYOS/HCU WORKER]"""


async def worker_loop(rt: ProviderRuntime, protocol: str, sink: JsonlSink, deadline: float, args, serial: list[int], stop: asyncio.Event):
    while not stop.is_set() and time.monotonic() < deadline:
        pair = rt.pair()
        if pair is None or not await rt.acquire(deadline): return
        key, model = pair
        try:
            serial[0] += 1; idx = serial[0]; role, task = DEFAULT_ROLES[(idx - 1) % len(DEFAULT_ROLES)]
            prompt = worker_prompt(protocol, role, task, build_state_context(args.context_chars), idx)
            rt.requests += 1
            try: status, headers, payload = await asyncio.to_thread(request_chat, rt.spec, key, model, prompt, args.max_tokens, args.timeout)
            except Exception as exc:
                rt.errors += 1; await sink.append({"schema":"CLAY_FREE_GO_SWARM_WORKER/v2","provider":rt.spec.name,"model":model,"worker_serial":idx,"http_status":"NETWORK_EXCEPTION","error":exc.__class__.__name__}); continue
            row = {"schema":"CLAY_FREE_GO_SWARM_WORKER/v2","ts":dt.datetime.now(dt.timezone.utc).isoformat(),"provider":rt.spec.name,"model":model,"key_fp":key_fingerprint(key),"role":role,"worker_serial":idx,"http_status":status,"usage":_usage(payload)}
            if 200 <= status < 300:
                text = _extract_text(payload); row["text"] = text; row["text_sha256"] = hashlib.sha256(text.encode()).hexdigest(); rt.successes += 1
            elif status == 402:
                row["classification"] = "PAYMENT_REQUIRED_HARD_STOP_KEY"; rt.disabled_keys.add(key_fingerprint(key))
            elif status in (401,403):
                row["classification"] = "AUTH_OR_ENTITLEMENT_BLOCKED_KEY"; rt.disabled_keys.add(key_fingerprint(key))
            elif status == 404:
                row["classification"] = "MODEL_OR_ENDPOINT_UNAVAILABLE"; rt.disabled_models.add(model)
            elif status == 429:
                row["classification"] = "RATE_LIMIT_PROVIDER_COOLDOWN"; rt.rate_limits += 1; rt.target_concurrency = max(1, rt.target_concurrency // 2); rt.cooldown_until = time.monotonic() + min(900.0, rt.rate_backoff * 2 + random.random()); rt.rate_backoff = min(900.0, rt.rate_backoff * 2)
            else:
                row["classification"] = "REQUEST_ERROR"; rt.errors += 1
            await sink.append(row)
        finally:
            await rt.release()


def resolve_admission(path: str | None) -> tuple[AdmissionDocument, set[str]]:
    doc = load_admission(path)
    return doc, set(admitted_free_providers(doc))


async def run(args: argparse.Namespace) -> int:
    admission_path = getattr(args, "provider_admission_file", "") or os.getenv("CLAY_PROVIDER_ADMISSION_FILE", "")
    try:
        admission, free = resolve_admission(admission_path)
    except AdmissionError as exc:
        print(f"ADMISSION_BLOCKED before credential/network region: {exc}", file=sys.stderr); return 3
    if not free:
        print("ADMISSION_BLOCKED: no provider has effective cost_class=FREE", file=sys.stderr); return 3

    # Credential region begins only here, after typed admission.
    runtimes: list[ProviderRuntime] = []
    for spec in PROVIDERS:
        if spec.name not in free: continue
        keys = collect_keys(spec)
        if not keys: continue
        models = split_values(os.getenv(spec.models_env)) or list(spec.default_models)
        try: cap = int(os.getenv(f"CLAY_{spec.name.upper()}_MAX_CONCURRENCY", spec.default_max_concurrency))
        except ValueError: cap = spec.default_max_concurrency
        runtimes.append(ProviderRuntime(spec, keys, unique(models), cap))
    if not runtimes:
        print("No credentials for typed-FREE admitted providers. Nothing to run.", file=sys.stderr); return 4

    protocol = load_protocol()
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else Path.home()/".local/state/clay-free-go-swarm"/run_id
    sink = JsonlSink(output_dir)
    manifest = {"schema":"CLAY_FREE_GO_SWARM_RUN/v2","run_id":run_id,"free_only":True,"repo_head":git_text("rev-parse","HEAD"),"provider_admission":{"admission_id":admission.admission_id,"generation":admission.generation,"source_ref":admission.source_ref,"sha256":admission.sha256,"free_providers":sorted(free)},"invariants":["TYPED_FREE_ADMISSION_BEFORE_CREDENTIAL_LOOKUP","TYPED_FREE_ADMISSION_BEFORE_NETWORK","HTTP_402_HARD_STOP","NO_PAID_FALLBACK"]}
    output_dir.mkdir(parents=True, exist_ok=True); (output_dir/"run_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    duration = max(1.0, args.hours * 3600); deadline = time.monotonic() + duration; stop = asyncio.Event(); serial=[0]
    loop=asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try: loop.add_signal_handler(sig, stop.set)
        except NotImplementedError: pass
    tasks=[asyncio.create_task(worker_loop(rt, protocol, sink, deadline, args, serial, stop)) for rt in runtimes for _ in range(rt.max_concurrency)]
    sleeper=asyncio.create_task(asyncio.sleep(duration)); stopper=asyncio.create_task(stop.wait()); await asyncio.wait({sleeper,stopper}, return_when=asyncio.FIRST_COMPLETED); stop.set()
    for t in tasks: t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    final={"schema":"CLAY_FREE_GO_SWARM_FINAL/v2","run_id":run_id,"workers_started":serial[0],"providers":{rt.spec.name:rt.snapshot() for rt in runtimes}}; await sink.status(final); return 0


def parse_args(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--hours",type=float,default=24); p.add_argument("--max-tokens",type=int,default=1800); p.add_argument("--context-chars",type=int,default=22000); p.add_argument("--timeout",type=float,default=180); p.add_argument("--drain-seconds",type=float,default=240); p.add_argument("--output-dir",default=""); p.add_argument("--provider-admission-file",default=os.getenv("CLAY_PROVIDER_ADMISSION_FILE","")); return p.parse_args(argv)


if __name__ == "__main__":
    try: raise SystemExit(asyncio.run(run(parse_args())))
    except KeyboardInterrupt: raise SystemExit(130)
