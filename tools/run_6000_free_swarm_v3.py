#!/usr/bin/env python3
"""Epoch-8.71 economic gate for the global work-stealing Free Swarm.

The cache/productivity accelerator is installed before the v2 scheduler fabric is
imported so its worker prompt and ProviderRuntime are actually captured by the
6000-worker layer. Concrete provider requests still require provider-side
zero-cost/free-entitlement evidence and emit FREE_LANE_EXECUTION_RECEIPT/v1.

The v2 scheduler historically performed authenticated provider model-catalog
network discovery before the per-lane gate ran. Current FREE_ONLY authority does
not establish catalog-endpoint zero-cost provenance, so this wrapper also replaces
that pre-route discovery with a network-free environment/static-default resolver.

Forge-ready workers additionally receive one small exact-source capsule selected
from their shard. The capsule binds the current file digest and a bounded excerpt;
model output remains noncanonical and MUST stay design-only when the supplied
source is insufficient to construct an applicable patch.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import threading
from typing import Any

# Import order is a causal invariant. run_6000_free_swarm captures the base
# ProviderRuntime and worker_prompt at import time; installing afterward leaves
# the accelerator dead while appearing configured.
import run_free_go_swarm as _base
import run_24h_entityos_swarm as _opt
from free_swarm_accelerator_v2 import install as _install_accelerator

_install_accelerator(_base, _opt)
ACCELERATOR_BINDING = "FREE_SWARM_ACCELERATOR_V2_PRE_FABRIC"

import run_6000_free_swarm as fabric  # noqa: E402
from free_lane_provenance import (  # noqa: E402
    binding_still_current,
    current_lane_binding,
    emit_execution_receipt,
    lane_evidence,
)

_ORIGINAL_REQUEST = fabric.base.request_chat
_ORIGINAL_NEXT_PAIR = fabric.FastProviderRuntime.next_key_model
_ORIGINAL_WORKER_PROMPT = fabric.base.worker_prompt
_RECEIPT_LOCK = threading.Lock()
_EVIDENCE_CACHE: dict[tuple[str, str, str, str], dict[str, Any]] = {}
_ROOT = Path(__file__).resolve().parents[1]
_SOURCE = {
    "commit": fabric.base.git_text("rev-parse", "HEAD"),
    "tree": fabric.base.git_text("rev-parse", "HEAD^{tree}"),
}

# One source capsule per worker keeps context bounded while turning the most
# conversion-critical shards from blind patch synthesis into exact-byte work.
# Selection is deterministic and does not grant any authority to the source map.
_SOURCE_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("forge candidate conversion", "patch synthesis", "benchmark non-regression", "test survival over go cycles"),
     "tools/run_free_evidence_forge.py", "def validate_candidate"),
    (("distillery yield", "knowledge packet reinjection", "research queue closure", "open-question decomposition"),
     "tools/run_research_distillery.py", "panel_ok="),
    (("j-space causal provenance", "j-space intervention controls", "global-workspace routing", "attention/broadcast sparsity", "cognition ablations", "counterfactual state intervention"),
     "tools/hcu_jspace_local_activation_probe.py", "def validate_atomic_claim"),
)


def _source_capsule_for_prompt(prompt: str, limit: int = 9000) -> str:
    low = prompt.lower()
    selected: tuple[str, str] | None = None
    for needles, rel, anchor in _SOURCE_RULES:
        if any(needle in low for needle in needles):
            selected = (rel, anchor)
            break
    if selected is None:
        return (
            "\n\nEXACT_SOURCE_CAPSULE\n"
            "status=NOT_SELECTED_FOR_THIS_SHARD\n"
            "For code changes, ready_for_forge MUST remain false unless exact target bytes are otherwise present in the supplied context.\n"
        )

    rel, anchor = selected
    path = (_ROOT / rel).resolve()
    try:
        path.relative_to(_ROOT)
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
    except (OSError, ValueError):
        return (
            "\n\nEXACT_SOURCE_CAPSULE\n"
            f"status=UNAVAILABLE path={rel}\n"
            "ready_for_forge MUST remain false for this source target.\n"
        )

    digest = hashlib.sha256(raw).hexdigest()
    idx = text.find(anchor)
    if idx >= 0:
        start = max(0, idx - limit // 3)
        end = min(len(text), start + limit)
        excerpt = text[start:end]
        excerpt_start = start
        excerpt_end = end
    elif len(text) <= limit:
        excerpt = text
        excerpt_start = 0
        excerpt_end = len(text)
    else:
        half = max(1, (limit - len("\n...[EXCERPT_GAP]...\n")) // 2)
        excerpt = text[:half] + "\n...[EXCERPT_GAP]...\n" + text[-half:]
        excerpt_start = 0
        excerpt_end = len(text)

    return (
        "\n\nEXACT_SOURCE_CAPSULE\n"
        "status=BOUND_EXCERPT_ONLY\n"
        f"repo_head={_SOURCE['commit']}\n"
        f"repo_tree={_SOURCE['tree']}\n"
        f"path={rel}\n"
        f"full_file_sha256={digest}\n"
        f"excerpt_char_range={excerpt_start}:{excerpt_end}\n"
        "Rules:\n"
        "- This is source evidence, not canonical truth authority.\n"
        "- ready_for_forge=true only if every modified hunk is grounded in visible exact source context and target_files names only supplied exact-source paths.\n"
        "- If the needed function/lines are outside this excerpt, emit a design-only candidate with ready_for_forge=false instead of guessing.\n"
        "- Preserve current FREE_ONLY/effect/state authority; never weaken a fail-closed gate merely to make a test pass.\n"
        "--- BEGIN EXACT SOURCE EXCERPT ---\n"
        f"{excerpt}\n"
        "--- END EXACT SOURCE EXCERPT ---\n"
    )


def source_grounded_worker_prompt(
    protocol: str, role: str, task: str, state_context: str, serial: int
) -> str:
    prompt = _ORIGINAL_WORKER_PROMPT(protocol, role, task, state_context, serial)
    return prompt + _source_capsule_for_prompt(prompt)


def route_safe_discover_and_export(timeout: float) -> dict[str, dict]:
    """Resolve candidate models without provider network I/O.

    Provider-level admission authorizes only the owner's free contingent; it is
    not economic proof for an arbitrary authenticated catalog request. Current
    FREE_ONLY economic provenance binds concrete inference routes, not catalog
    endpoints. Therefore the active 6000-worker path may use an explicit local
    model override or the controller's static defaults, while final credential +
    route admission remains the responsibility of ``current_lane_binding``.

    ``timeout`` is retained for API compatibility with the v2 scheduler.
    """
    del timeout
    report: dict[str, dict] = {}
    try:
        admission = fabric.load_provider_admission()
    except fabric.ProviderAdmissionError as exc:
        return {
            spec.name: {
                "source": "typed_admission_invalid",
                "keys": 0,
                "models": [],
                "catalog_network_attempted": False,
                "status": str(exc),
            }
            for spec in fabric.base.PROVIDERS
        }

    if not fabric.base.truthy(os.getenv("CLAY_FREE_ONLY_ATTESTED")):
        return {
            spec.name: {
                "source": "global_compat_attestation_missing",
                "keys": 0,
                "models": [],
                "catalog_network_attempted": False,
            }
            for spec in fabric.base.PROVIDERS
        }

    for spec in fabric.base.PROVIDERS:
        if not fabric.provider_is_admitted_free(spec.name, admission):
            report[spec.name] = {
                "source": "typed_admission_blocked",
                "keys": 0,
                "models": [],
                "catalog_network_attempted": False,
            }
            continue
        if not fabric.base.truthy(os.getenv(spec.attestation_env)):
            report[spec.name] = {
                "source": "provider_compat_attestation_missing",
                "keys": 0,
                "models": [],
                "catalog_network_attempted": False,
            }
            continue

        # Credential material is still collected only through the canonical
        # provider-admission-aware loader. No provider request is made here.
        keys = fabric.base.collect_keys(spec, admission)
        override = fabric.base.split_values(os.getenv(spec.models_env))
        models = fabric.base.unique(override or list(spec.default_models))
        if models:
            os.environ[spec.models_env] = ",".join(models)
        report[spec.name] = {
            "source": (
                "environment_override"
                if override
                else "static_defaults_no_catalog_economic_provenance"
            ),
            "keys": len(keys),
            "models": models,
            "catalog_network_attempted": False,
            "route_binding_deferred_to_current_lane_binding": True,
        }
    return report


def _evidence(spec: fabric.base.ProviderSpec, key: str, model: str) -> dict[str, Any]:
    """Cheap reservation filter only; network authorization is always re-read fresh."""
    fp = fabric.base.key_fingerprint(key)
    ck = (spec.name, fp, model, spec.endpoint)
    if ck not in _EVIDENCE_CACHE:
        _EVIDENCE_CACHE[ck] = lane_evidence(
            spec.name,
            fp,
            model,
            spec.endpoint,
            artifacts=fabric.ARTIFACT_ROOT,
        )
    return _EVIDENCE_CACHE[ck]


def gated_next_key_model(self: fabric.FastProviderRuntime):
    attempts = max(1, len(self.keys) * len(self.models))
    for _ in range(attempts):
        pair = _ORIGINAL_NEXT_PAIR(self)
        if pair is None:
            return None
        key, model = pair
        if _evidence(self.spec, key, model).get("ok"):
            return key, model
    return None


def _request_id(headers: dict[str, str], payload: Any) -> str | None:
    for key in ("x-request-id", "request-id", "x-groq-request-id", "cf-ray"):
        if headers.get(key):
            return str(headers[key])
    if isinstance(payload, dict):
        for key in ("id", "request_id"):
            if payload.get(key):
                return str(payload[key])
    return None


def gated_request_chat(
    spec: fabric.base.ProviderSpec,
    key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
):
    fp = fabric.base.key_fingerprint(key)
    binding = current_lane_binding(
        spec.name,
        fp,
        model,
        spec.endpoint,
        artifacts=fabric.ARTIFACT_ROOT,
    )
    if not binding.get("ok"):
        return 460, {}, {
            "error": "FREE_LANE_CURRENT_BINDING_REQUIRED",
            "provider": spec.name,
            "model": model,
            "reason": binding.get("reason"),
        }

    # Final fail-closed digest check immediately before the provider call. This
    # prevents a cached reservation decision from surviving a current authority
    # or economic-provenance update.
    if not binding_still_current(binding):
        return 460, {}, {
            "error": "FREE_LANE_BINDING_CHANGED_BEFORE_NETWORK",
            "provider": spec.name,
            "model": model,
        }

    status, headers, payload = _ORIGINAL_REQUEST(
        spec, key, model, prompt, max_tokens, timeout
    )
    stable_after_call = binding_still_current(binding)
    usage = fabric.base.usage_from(payload)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()
    with _RECEIPT_LOCK:
        emit_execution_receipt(
            provider=spec.name,
            credential_fingerprint=fp,
            model_or_route=model,
            endpoint=spec.endpoint,
            binding=binding,
            request_id=_request_id(headers, payload),
            usage=usage,
            http_status=status,
            result_digest=digest,
            source_commit_and_tree=_SOURCE,
            binding_stable_after_call=stable_after_call,
            artifacts=fabric.ARTIFACT_ROOT,
        )
    return status, headers, payload


# The v2 fabric invokes opt.discover_and_export() at the start of run(). Replace
# it before exporting run so the active v3 launcher cannot perform authenticated
# catalog I/O outside the route/credential economic boundary.
fabric.opt.discover_and_export = route_safe_discover_and_export
fabric.FastProviderRuntime.next_key_model = gated_next_key_model
fabric.base.request_chat = gated_request_chat
fabric.base.worker_prompt = source_grounded_worker_prompt

run = fabric.run
parse_args = fabric.parse_args

if __name__ == "__main__":
    import asyncio
    raise SystemExit(asyncio.run(run(parse_args())))
