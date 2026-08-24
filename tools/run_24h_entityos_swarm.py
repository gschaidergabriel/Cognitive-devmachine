#!/usr/bin/env python3
"""EntityOS/HCU driver for the adaptive go swarm.

Provider credentials and provider network I/O are reachable only after a typed
EntityOS/HCU provider-admission decision with cost_class=FREE. Environment
attestation flags alone never admit a provider.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

import free_provider_admission_v1 as admission
import run_free_go_swarm as base

ROOT = Path(__file__).resolve().parents[1]
base.OWNER_DIRECTIVE_PATH = ROOT / "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md"
base.DEFAULT_ROLES = [
    ("ARCHITECT", "Advance EntityOS/HCU architecture with one high-information, measurable delta and a strongest counterarchitecture."),
    ("FALSIFIER", "Attack the strongest EntityOS/HCU assumption and design the cheapest executable falsifier."),
    ("CLAYCODE_FORGE", "Produce a minimal ClayCode-native implementation, invariants, tests and migration path for the active frontier."),
    ("HCU_CAUSAL", "Advance the causal chain from typed entry through verified loader/model execution to inference/J-Space/training evidence without overclaiming authority."),
    ("COGNITION", "Design aggressive synthetic cognition interventions, deception/pressure/ablation experiments and matched controls inside the authorized sandbox."),
    ("MEMORY_JSPACE", "Stress memory/J-Space provenance, replay, online learning, model switching, ablation and recovery semantics."),
    ("RUNTIME", "Find compiler/VM/runtime/loader bottlenecks and propose measurable EntityOS/HCU-native improvements."),
    ("EXTERNAL_HARVEST", "Identify exact GitHub/arXiv/upstream candidates to clone, reproduce and dissect; isolate the causal principle worth adapting."),
    ("EXPERIMENT_DESIGN", "Design A/B tests, ablations, negative controls, resource measurements, stopping rules and regression gates."),
    ("SECURITY", "Adversarially inspect truth/effect/capability boundaries and concrete negative tests. Model output never self-grants effects."),
    ("REVIEWER", "Find stale evidence, source-only overclaims, hidden coupling, duplicated semantics and unmeasured assumptions."),
    ("SYNTHESIZER", "Fuse nonredundant findings into one next executable EntityOS/HCU step while preserving disagreement and provenance."),
]

CATALOGS = {
    "groq": "https://api.groq.com/openai/v1/models",
    "mistral": "https://api.mistral.ai/v1/models",
    "nvidia": "https://integrate.api.nvidia.com/v1/models",
}
EXCLUDE = (
    "embedding", "embed-", "rerank", "whisper", "speech", "audio", "tts",
    "guard", "safety", "moderation", "classifier", "reward", "diffusion",
)
UNKNOWN_HIGH_VALUE = (
    "mistral-large", "mistral-medium", "mistral-small", "magistral", "codestral",
    "devstral", "nemotron", "deepseek", "reasoning", "instruct", "coder",
)

BOUNDARY_AUDIT = {"secret_lookup_count": 0, "network_attempt_count": 0}
_ORIGINAL_COLLECT_KEYS = base.collect_keys
_ORIGINAL_REQUEST_CHAT = base.request_chat


def reset_boundary_audit() -> None:
    BOUNDARY_AUDIT["secret_lookup_count"] = 0
    BOUNDARY_AUDIT["network_attempt_count"] = 0


def typed_provider_decision(provider: str) -> dict:
    return admission.provider_decision(provider)


def admitted_collect_keys(spec) -> list[str]:
    """Read provider key variables only after explicit typed FREE admission."""
    decision = typed_provider_decision(spec.name)
    if not decision["admitted"]:
        return []
    BOUNDARY_AUDIT["secret_lookup_count"] += 1
    return _ORIGINAL_COLLECT_KEYS(spec)


base.collect_keys = admitted_collect_keys


def sync_attestation_from_typed_admission() -> list[str]:
    """Derive legacy boolean compatibility flags from typed admission, never vice versa."""
    admitted = admission.free_providers()
    if admitted:
        os.environ["CLAY_FREE_ONLY_ATTESTED"] = "1"
    else:
        os.environ.pop("CLAY_FREE_ONLY_ATTESTED", None)
    for spec in base.PROVIDERS:
        if spec.name in admitted:
            os.environ[spec.attestation_env] = "1"
        else:
            os.environ.pop(spec.attestation_env, None)
    return admitted


def provider_bounded_request_chat(spec, key, model, prompt, max_tokens, timeout):
    decision = typed_provider_decision(spec.name)
    if not decision["admitted"]:
        raise RuntimeError(f"PROVIDER_ADMISSION_REVOKED_BEFORE_NETWORK:{spec.name}:{decision['reason']}")
    if spec.name == "groq":
        max_tokens = min(int(max_tokens), int(os.getenv("CLAY_GROQ_MAX_TOKENS", "1000")))
    elif spec.name == "mistral":
        max_tokens = min(int(max_tokens), int(os.getenv("CLAY_MISTRAL_MAX_TOKENS", "1600")))
    elif spec.name == "nvidia":
        max_tokens = min(int(max_tokens), int(os.getenv("CLAY_NVIDIA_MAX_TOKENS", "1800")))
    BOUNDARY_AUDIT["network_attempt_count"] += 1
    return _ORIGINAL_REQUEST_CHAT(spec, key, model, prompt, max_tokens, timeout)


base.request_chat = provider_bounded_request_chat


def fetch_catalog(url: str, key: str, timeout: float) -> list[dict]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return []
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    return [x if isinstance(x, dict) else {"id": str(x)} for x in rows]


def explicit_billions(model_id: str) -> float | None:
    vals: list[float] = []
    for raw in re.findall(r"(?i)(\d+(?:\.\d+)?)\s*b(?:\b|[-_])", model_id):
        try:
            vals.append(float(raw))
        except ValueError:
            pass
    return max(vals) if vals else None


def choose_models(provider: str, rows: list[dict]) -> list[str]:
    ranked: list[tuple[float, str]] = []
    for card in rows:
        model_id = str(card.get("id") or card.get("model") or "").strip()
        low = model_id.lower()
        if not model_id or any(x in low for x in EXCLUDE):
            continue
        capabilities = card.get("capabilities")
        if isinstance(capabilities, dict) and capabilities.get("completion_chat") is False:
            continue
        b = explicit_billions(model_id)
        if b is not None and b < 12.0:
            continue
        if b is None and not any(x in low for x in UNKNOWN_HIGH_VALUE):
            continue
        score = b or 0.0
        if any(x in low for x in ("ultra", "large", "reasoning", "deepseek", "120b", "405b", "550b")):
            score += 120.0
        if any(x in low for x in ("nemotron", "magistral", "devstral", "codestral", "coder", "instruct")):
            score += 60.0
        if model_id == "nvidia/llama-3.3-nemotron-super-49b-v1":
            score += 500.0
        ranked.append((score, model_id))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return base.unique([mid for _, mid in ranked])


def discover_and_export(timeout: float) -> dict[str, dict]:
    """Catalog discovery is impossible until typed FREE admission has passed."""
    report: dict[str, dict] = {}
    for spec in base.PROVIDERS:
        decision = typed_provider_decision(spec.name)
        if not decision["admitted"]:
            report[spec.name] = {
                "source": "typed_admission_blocked",
                "cost_class": decision["cost_class"],
                "reason": decision["reason"],
                "keys": "NOT_READ",
                "models": [],
                "secret_lookup_count": 0,
                "network_attempt_count": 0,
            }
            continue
        keys = base.collect_keys(spec)
        override = base.split_values(os.getenv(spec.models_env))
        if override:
            report[spec.name] = {
                "source": "environment_override",
                "cost_class": "FREE",
                "keys": len(keys),
                "models": override,
            }
            continue
        if not keys:
            report[spec.name] = {
                "source": "no_keys",
                "cost_class": "FREE",
                "keys": 0,
                "models": [],
            }
            continue
        BOUNDARY_AUDIT["network_attempt_count"] += 1
        rows = fetch_catalog(CATALOGS[spec.name], keys[0], timeout)
        selected = choose_models(spec.name, rows)
        if selected:
            os.environ[spec.models_env] = ",".join(selected)
            report[spec.name] = {
                "source": "live_catalog",
                "cost_class": "FREE",
                "keys": len(keys),
                "catalog": len(rows),
                "models": selected,
            }
        else:
            report[spec.name] = {
                "source": "controller_fallback",
                "cost_class": "FREE",
                "keys": len(keys),
                "catalog": len(rows),
                "models": list(spec.default_models),
            }
    return report


async def main(args: argparse.Namespace) -> int:
    reset_boundary_audit()
    admitted = sync_attestation_from_typed_admission()
    report = discover_and_export(args.timeout)
    print(json.dumps({
        "schema": "CLAY_ENTITYOS_SWARM_DISCOVERY/v3",
        "typed_free_providers": admitted,
        "boundary_audit": dict(BOUNDARY_AUDIT),
        "providers": report,
    }, ensure_ascii=False), flush=True)
    if args.inventory_only:
        return 0
    out = args.output_dir or f"/artifacts/clay-entityos-swarm/{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    base_args = argparse.Namespace(
        hours=args.hours,
        max_tokens=args.max_tokens,
        context_chars=args.context_chars,
        timeout=args.timeout,
        drain_seconds=args.drain_seconds,
        output_dir=out,
    )
    return await base.run(base_args)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the adaptive EntityOS/HCU research swarm for 24h")
    p.add_argument("--hours", type=float, default=24.0)
    p.add_argument("--max-tokens", type=int, default=1800)
    p.add_argument("--context-chars", type=int, default=22000)
    p.add_argument("--timeout", type=float, default=180.0)
    p.add_argument("--drain-seconds", type=float, default=240.0)
    p.add_argument("--output-dir", default="")
    p.add_argument("--inventory-only", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(parse_args())))
