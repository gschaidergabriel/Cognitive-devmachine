#!/usr/bin/env python3
"""Route-bound, catalog-safe 6000-worker Free Swarm with typed delta ingress.

The cache/productivity accelerator is installed before importing the v2 fabric so
its ProviderRuntime/prompt changes are inherited instead of becoming dead code.
The successor-current FREE_ONLY fences remain stronger than throughput: provider
catalog discovery is network-free before route binding; every concrete inference
route revalidates current credential+route economic provenance immediately before
network I/O and emits FREE_LANE_EXECUTION_RECEIPT/v1.

Successful model text remains noncanonical. Explicit architecture-delta/question
markers are deterministically parsed at sink ingress and materialized as bounded
candidate evidence; malformed/model-asserted readiness cannot mint canonical truth.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Any

# Import order is execution-relevant. run_6000_free_swarm captures both
# base.ProviderRuntime and base.worker_prompt while importing; install first.
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
from free_swarm_delta_ingress import parse_questions, parse_worker_delta  # noqa: E402

_ORIGINAL_REQUEST = fabric.base.request_chat
_ORIGINAL_NEXT_PAIR = fabric.FastProviderRuntime.next_key_model
_ORIGINAL_SINK_APPEND = fabric.base.JsonlSink.append
_RECEIPT_LOCK = threading.Lock()
_EVIDENCE_CACHE: dict[tuple[str, str, str, str], dict[str, Any]] = {}
_SOURCE = {
    "commit": fabric.base.git_text("rev-parse", "HEAD"),
    "tree": fabric.base.git_text("rev-parse", "HEAD^{tree}"),
}


def route_safe_discover_and_export(timeout: float) -> dict[str, dict]:
    """Resolve candidate models without provider catalog network I/O.

    Provider admission does not prove zero-cost semantics for an arbitrary
    authenticated catalog request. Explicit local model overrides or static
    defaults are therefore used here; final credential+route admission remains
    the responsibility of ``current_lane_binding``.
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

        # Credential material still comes only through the admission-aware loader.
        # No provider request is made by this discovery function.
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


async def ingress_aware_sink_append(self: fabric.base.JsonlSink, item: dict[str, Any]) -> None:
    """Attach deterministic candidate admission without promoting model text."""
    row = dict(item)
    text = row.get("text")
    status = row.get("http_status")
    candidate = None
    questions: list[str] = []

    if isinstance(text, str) and isinstance(status, int) and 200 <= status < 300:
        ingress = parse_worker_delta(text)
        questions = parse_questions(text)
        row["delta_ingress"] = {
            "schema": ingress["schema"],
            "status": ingress["status"],
            "valid": ingress["valid"],
            "ready_for_forge": ingress["ready_for_forge"],
            "reasons": ingress["reasons"],
            "proposal_sha256": ingress.get("proposal_sha256"),
            "question_count": len(questions),
        }
        if ingress.get("valid"):
            candidate = {
                "schema": "CLAY_ARCHITECTURE_DELTA_CANDIDATE/v1",
                "ts": row.get("ts"),
                "provider": row.get("provider"),
                "model": row.get("model"),
                "role": row.get("role"),
                "worker_serial": row.get("worker_serial"),
                "logical_worker_slot": row.get("logical_worker_slot"),
                "repo_head_at_prompt": row.get("repo_head_at_prompt"),
                "worker_text_sha256": row.get("text_sha256"),
                "proposal_sha256": ingress.get("proposal_sha256"),
                "ready_for_forge": ingress.get("ready_for_forge"),
                "proposal": ingress.get("proposal"),
            }

    # Preserve the historical raw worker ledger first. Candidate streams are
    # secondary append-only projections bound back by worker/proposal hashes.
    await _ORIGINAL_SINK_APPEND(self, row)

    if candidate is not None:
        async with self._lock:
            path = self.output_dir / "architecture_deltas.jsonl"
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")) + "\n")
                fh.flush()

    if questions:
        qrow = {
            "schema": "CLAY_OPEN_RESEARCH_QUESTIONS/v1",
            "ts": row.get("ts"),
            "worker_serial": row.get("worker_serial"),
            "worker_text_sha256": row.get("text_sha256"),
            "questions": questions,
        }
        async with self._lock:
            path = self.output_dir / "open_research_questions.jsonl"
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(qrow, ensure_ascii=False, separators=(",", ":")) + "\n")
                fh.flush()


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


# Preserve #1489's no-catalog-network pre-route boundary, then install the other
# execution hooks. None of these grants canonical/state/effect authority.
fabric.opt.discover_and_export = route_safe_discover_and_export
fabric.FastProviderRuntime.next_key_model = gated_next_key_model
fabric.base.request_chat = gated_request_chat
fabric.base.JsonlSink.append = ingress_aware_sink_append

run = fabric.run
parse_args = fabric.parse_args

if __name__ == "__main__":
    import asyncio
    raise SystemExit(asyncio.run(run(parse_args())))
