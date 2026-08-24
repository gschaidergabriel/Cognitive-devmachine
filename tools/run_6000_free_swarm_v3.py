#!/usr/bin/env python3
"""Epoch-8.71 economic gate + typed delta ingress for the global work-stealing Free Swarm.

Imports the v2 scheduler, prevents reservation/network I/O for concrete credential+route
pairs lacking current provider-side zero-cost/free-entitlement evidence, emits exact FREE
lane receipts, and deterministically materializes worker architecture-delta candidates for
Evidence Forge. Model output remains noncanonical.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Any

import run_6000_free_swarm as fabric
from free_lane_provenance import (
    binding_still_current,
    current_lane_binding,
    emit_execution_receipt,
    lane_evidence,
)
from free_swarm_delta_ingress import (
    CANDIDATE_SCHEMA,
    parse_questions,
    parse_worker_delta,
)

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
    """Resolve candidate models without provider network I/O."""
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


def _append_sidecar(path, record: dict[str, Any]) -> None:
    sink = fabric.base.JsonlSink(path)
    _ORIGINAL_SINK_APPEND(sink, record)


def ingress_aware_sink_append(self: fabric.base.JsonlSink, row: dict[str, Any]) -> None:
    """Classify worker output once and materialize the typed Forge handoff."""
    if self.path.name != "workers.jsonl" or not isinstance(row, dict):
        _ORIGINAL_SINK_APPEND(self, row)
        return

    enriched = dict(row)
    status = enriched.get("http_status")
    text = str(enriched.get("text") or "")
    ingress = None
    questions: list[str] = []
    if isinstance(status, int) and 200 <= status < 300:
        ingress = parse_worker_delta(text)
        questions = parse_questions(text)
        enriched["delta_ingress"] = {
            "schema": ingress["schema"],
            "status": ingress["status"],
            "valid": ingress["valid"],
            "ready_for_forge": ingress["ready_for_forge"],
            "reasons": ingress["reasons"],
            "proposal_sha256": ingress["proposal_sha256"],
        }

    _ORIGINAL_SINK_APPEND(self, enriched)

    if ingress and ingress["valid"]:
        worker_sha = str(
            enriched.get("text_sha256")
            or hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        )
        record = {
            "schema": CANDIDATE_SCHEMA,
            "ingress_schema": ingress["schema"],
            "provider": str(enriched.get("provider") or ""),
            "model": str(enriched.get("model") or ""),
            "role": str(enriched.get("role") or ""),
            "worker_serial": enriched.get("worker_serial"),
            "logical_worker_slot": enriched.get("logical_worker_slot"),
            "repo_head_at_prompt": (
                enriched.get("repo_head_at_prompt")
                or enriched.get("repo_head")
                or _SOURCE["commit"]
            ),
            "worker_text_sha256": worker_sha,
            "proposal_sha256": ingress["proposal_sha256"],
            "ready_for_forge": ingress["ready_for_forge"],
            "proposal": ingress["proposal"],
        }
        _append_sidecar(self.path.parent / "architecture_deltas.jsonl", record)

    for question in questions:
        qsha = hashlib.sha256(question.encode("utf-8")).hexdigest()
        _append_sidecar(
            self.path.parent / "open_research_questions.jsonl",
            {
                "schema": "CLAY_OPEN_RESEARCH_QUESTION/v1",
                "question_sha256": qsha,
                "question": question,
                "provider": str(enriched.get("provider") or ""),
                "model": str(enriched.get("model") or ""),
                "role": str(enriched.get("role") or ""),
            },
        )


# The high-I/O launcher installs accelerator behavior before importing this module.
# Preserve that order; this module only adds economic gates and typed candidate ingress.
fabric.opt.discover_and_export = route_safe_discover_and_export
fabric.FastProviderRuntime.next_key_model = gated_next_key_model
fabric.base.request_chat = gated_request_chat
fabric.base.JsonlSink.append = ingress_aware_sink_append

run = fabric.run
parse_args = fabric.parse_args

if __name__ == "__main__":
    import asyncio
    raise SystemExit(asyncio.run(run(parse_args())))
