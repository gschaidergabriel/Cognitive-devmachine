#!/usr/bin/env python3
"""Epoch-8.70 economic gate for the global work-stealing Free Swarm.

The cache/throughput accelerator is installed *before* importing the v2 fabric so
its ProviderRuntime base class and worker-prompt wrapper are inherited by the
6000-worker scheduler. The route-level economic gate then prevents reservation /
network I/O for any concrete credential+route lacking provider-side zero-cost or
free-entitlement evidence. Every executed provider request emits
FREE_LANE_EXECUTION_RECEIPT/v1.
"""
from __future__ import annotations

import hashlib
import json
import threading
from typing import Any

# Import order is execution-relevant. Installing after run_6000_free_swarm would
# leave its FastProviderRuntime subclass and _PREV_PROMPT bound to the old base.
import run_free_go_swarm as _base
import run_24h_entityos_swarm as _opt
from free_swarm_accelerator_v2 import install as _install_accelerator

_install_accelerator(_base, _opt)
ACCELERATOR_BINDING = "FREE_SWARM_ACCELERATOR_V2_PRE_FABRIC"

import run_6000_free_swarm as fabric  # noqa: E402
from free_lane_provenance import lane_evidence, emit_execution_receipt  # noqa: E402

_ORIGINAL_REQUEST = fabric.base.request_chat
_ORIGINAL_NEXT_PAIR = fabric.FastProviderRuntime.next_key_model
_RECEIPT_LOCK = threading.Lock()
_EVIDENCE_CACHE: dict[tuple[str, str, str, str], dict[str, Any]] = {}
_SOURCE = {
    "commit": fabric.base.git_text("rev-parse", "HEAD"),
    "tree": fabric.base.git_text("rev-parse", "HEAD^{tree}"),
}


def _evidence(spec: fabric.base.ProviderSpec, key: str, model: str) -> dict[str, Any]:
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
    # Explore at most the cartesian product once. Invalid pairs never reach the
    # provider boundary and therefore cannot consume paid/unknown capacity.
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
    evidence = _evidence(spec, key, model)
    if not evidence.get("ok"):
        # This path should normally be unreachable because reservation is gated.
        # It remains a second independent boundary immediately before network I/O.
        return 460, {}, {
            "error": "FREE_LANE_ECONOMIC_PROVENANCE_REQUIRED",
            "provider": spec.name,
            "model": model,
            "reason": evidence.get("reason"),
        }

    status, headers, payload = _ORIGINAL_REQUEST(
        spec, key, model, prompt, max_tokens, timeout
    )
    usage = fabric.base.usage_from(payload)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()
    with _RECEIPT_LOCK:
        emit_execution_receipt(
            provider=spec.name,
            credential_fingerprint=fabric.base.key_fingerprint(key),
            model_or_route=model,
            endpoint=spec.endpoint,
            evidence=evidence,
            request_id=_request_id(headers, payload),
            usage=usage,
            http_status=status,
            result_digest=digest,
            source_commit_and_tree=_SOURCE,
            artifacts=fabric.ARTIFACT_ROOT,
        )
    return status, headers, payload


fabric.FastProviderRuntime.next_key_model = gated_next_key_model
fabric.base.request_chat = gated_request_chat

# Re-export the public scheduler surface used by the fast launcher.
run = fabric.run
parse_args = fabric.parse_args

if __name__ == "__main__":
    import asyncio
    raise SystemExit(asyncio.run(run(parse_args())))
