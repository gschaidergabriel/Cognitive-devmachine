#!/usr/bin/env python3
"""Supervisor-8.70 route-bound wrapper for the trigger-scoped GO/ZERO swarm.

The compatibility trigger controller in ``run_go_zero_swarm.py`` remains the
coordination implementation. This wrapper narrows every concrete provider/model
reservation to a route+credential lane with provider-side zero-cost evidence and
emits ``FREE_LANE_EXECUTION_RECEIPT/v1`` for every request that reaches the
provider boundary.

It deliberately does not create another provider authority. Provider-level typed
admission remains enforced by ``run_free_go_swarm.py``; this module adds the
narrower economic provenance required by supervisor 8.70 before network I/O and
selects the versioned 8.70 worker-injection profile for this trigger path.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any

import run_go_zero_swarm as fabric
from free_lane_provenance import emit_execution_receipt, lane_evidence

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.getenv("CLAY_FREE_SWARM_ARTIFACTS", "/artifacts/clay-entityos-swarm"))
PROTOCOL_870 = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_8_70.md"
_ORIGINAL_REQUEST = fabric.BASE.request_chat
_ORIGINAL_NEXT_PAIR = fabric.BASE.ProviderRuntime.next_key_model
_RECEIPT_LOCK = threading.Lock()
_EVIDENCE_CACHE: dict[tuple[str, str, str, str], dict[str, Any]] = {}
_SOURCE = {
    "commit": fabric.BASE.git_text("rev-parse", "HEAD"),
    "tree": fabric.BASE.git_text("rev-parse", "HEAD^{tree}"),
}

# The legacy base module defaults to the unversioned compatibility directive.
# Bind this trigger invocation to the current versioned runtime injection profile
# without rewriting historical directives or receipts.
fabric.BASE.PROTOCOL_PATH = PROTOCOL_870


def _evidence(spec: fabric.BASE.ProviderSpec, key: str, model: str) -> dict[str, Any]:
    fp = fabric.BASE.key_fingerprint(key)
    cache_key = (spec.name, fp, model, spec.endpoint)
    if cache_key not in _EVIDENCE_CACHE:
        _EVIDENCE_CACHE[cache_key] = lane_evidence(
            spec.name,
            fp,
            model,
            spec.endpoint,
            artifacts=ARTIFACT_ROOT,
        )
    return _EVIDENCE_CACHE[cache_key]


def gated_next_key_model(self: fabric.BASE.ProviderRuntime):
    """Return only a route whose concrete credential/model pair is zero-cost bound."""
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
    spec: fabric.BASE.ProviderSpec,
    key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
):
    evidence = _evidence(spec, key, model)
    if not evidence.get("ok"):
        # No socket call is performed on this branch.
        return 460, {}, {
            "error": "FREE_LANE_ECONOMIC_PROVENANCE_REQUIRED",
            "provider": spec.name,
            "model": model,
            "reason": evidence.get("reason"),
        }

    status, headers, payload = _ORIGINAL_REQUEST(
        spec, key, model, prompt, max_tokens, timeout
    )
    usage = fabric.BASE.usage_from(payload)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()
    with _RECEIPT_LOCK:
        emit_execution_receipt(
            provider=spec.name,
            credential_fingerprint=fabric.BASE.key_fingerprint(key),
            model_or_route=model,
            endpoint=spec.endpoint,
            evidence=evidence,
            request_id=_request_id(headers, payload),
            usage=usage,
            http_status=status,
            result_digest=digest,
            source_commit_and_tree=_SOURCE,
            artifacts=ARTIFACT_ROOT,
        )
    return status, headers, payload


fabric.BASE.ProviderRuntime.next_key_model = gated_next_key_model
fabric.BASE.request_chat = gated_request_chat

run = fabric.run
parse_args = fabric.parse_args


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
