#!/usr/bin/env python3
"""Fail-closed binding between a sealed GRF Brain trace and ZERO prepare material.

This adapter does not allocate turns, write durable state, execute a model, select
GWT winners, or grant truth/effect/runtime credit. It only proves that the GRF
trace presented to the cognitive fabric is sealed, digest-identical, and bound
to the same entity generation + causal turn as the canonical prepare object.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

import grf_brain_v1 as grf

SCHEMA = "OMEGA_GRF_ZERO_BINDING/v1"
COMPILER_VERSION = "omega-grf-zero-binding/1.0"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class GRFZeroBindingError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise GRFZeroBindingError(message)


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GRFZeroBindingError("NONCANONICAL_JSON") from exc


def _sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def bind_trace_to_prepare(trace: Mapping[str, Any], prepare: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and bind one SEALED GRF trace to one canonical prepare mapping."""
    _need(isinstance(trace, Mapping), "GRF_TRACE_OBJECT_REQUIRED")
    _need(isinstance(prepare, Mapping), "PREPARE_OBJECT_REQUIRED")

    try:
        result = grf.validate(trace, allow_open=False)
    except grf.GRFError as exc:
        raise GRFZeroBindingError(f"GRF_TRACE_INVALID:{exc}") from exc
    _need(result.get("state") == "SEALED", "SEALED_GRF_TRACE_REQUIRED")

    generation = prepare.get("entity_generation")
    _need(type(generation) is int and generation >= 0, "PREPARE_GENERATION_INVALID")
    causal_turn_id = _text(prepare.get("causal_turn_id"), "prepare.causal_turn_id")
    prepare_grf_digest = _digest(prepare.get("grf_digest"), "prepare.grf_digest")
    turn_binding_digest = _digest(prepare.get("turn_binding_digest"), "prepare.turn_binding_digest")
    boot_binding_digest = _digest(prepare.get("boot_binding_digest"), "prepare.boot_binding_digest")

    _need(trace.get("entity_generation") == generation, "GRF_GENERATION_MISMATCH")
    _need(trace.get("causal_turn_id") == causal_turn_id, "GRF_CAUSAL_TURN_MISMATCH")
    _need(trace.get("grf_digest") == prepare_grf_digest, "GRF_DIGEST_NOT_PREPARE_BOUND")

    receipt = {
        "schema": SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "entity_generation": generation,
        "causal_turn_id": causal_turn_id,
        "grf_digest": prepare_grf_digest,
        "turn_binding_digest": turn_binding_digest,
        "boot_binding_digest": boot_binding_digest,
        "grf_trace_schema": trace.get("schema"),
        "grf_trace_nodes": len(trace.get("nodes", [])),
        "authority": "BINDING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY",
        "runtime_credit": "ZERO",
        "truth_credit": "ZERO",
        "effect_credit": "ZERO",
    }
    receipt["binding_digest"] = _sha256_obj(receipt)
    return receipt


def cognition_store_registration(trace: Mapping[str, Any], provenance_refs: list[str]) -> dict[str, Any]:
    """Compile exact kwargs for MiniUnifiedDB ``register_object`` as native GRF object.

    The store's CANONICAL_JSON digest is computed over the unsigned trace payload
    (the trace without its self-identifying ``grf_digest`` field). This is exactly
    the material that ``seal_trace`` hashes, avoiding a circular self-hash while
    preserving native MiniUnifiedDB object identity.
    """
    _need(isinstance(trace, Mapping), "GRF_TRACE_OBJECT_REQUIRED")
    try:
        result = grf.validate(trace, allow_open=False)
    except grf.GRFError as exc:
        raise GRFZeroBindingError(f"GRF_TRACE_INVALID:{exc}") from exc
    _need(result.get("state") == "SEALED", "SEALED_GRF_TRACE_REQUIRED")
    _need(type(provenance_refs) is list, "PROVENANCE_REFS_LIST_REQUIRED")
    refs = [_text(ref, "provenance_ref") for ref in provenance_refs]
    _need(bool(refs), "PROVENANCE_REQUIRED")
    _need(len(refs) == len(set(refs)), "PROVENANCE_DUPLICATE")

    payload = dict(trace)
    object_digest = _digest(payload.pop("grf_digest"), "trace.grf_digest")
    _need(grf.sha256_obj(payload) == object_digest, "GRF_STORE_PAYLOAD_DIGEST_MISMATCH")
    return {
        "object_kind": "GRF",
        "object_version": grf.COMPILER_VERSION,
        "object_digest": object_digest,
        "digest_basis": "CANONICAL_JSON",
        "payload": payload,
        "provenance_refs": refs,
    }


def validate_binding(receipt: Mapping[str, Any]) -> dict[str, Any]:
    _need(isinstance(receipt, Mapping), "BINDING_RECEIPT_OBJECT_REQUIRED")
    doc = dict(receipt)
    expected = {
        "schema",
        "compiler_version",
        "entity_generation",
        "causal_turn_id",
        "grf_digest",
        "turn_binding_digest",
        "boot_binding_digest",
        "grf_trace_schema",
        "grf_trace_nodes",
        "authority",
        "runtime_credit",
        "truth_credit",
        "effect_credit",
        "binding_digest",
    }
    _need(set(doc) == expected, "BINDING_FIELD_SET_MISMATCH")
    _need(doc.get("schema") == SCHEMA, "BINDING_SCHEMA_MISMATCH")
    _need(doc.get("compiler_version") == COMPILER_VERSION, "BINDING_COMPILER_MISMATCH")
    _need(type(doc.get("entity_generation")) is int and doc["entity_generation"] >= 0, "BINDING_GENERATION_INVALID")
    _text(doc.get("causal_turn_id"), "binding.causal_turn_id")
    _digest(doc.get("grf_digest"), "binding.grf_digest")
    _digest(doc.get("turn_binding_digest"), "binding.turn_binding_digest")
    _digest(doc.get("boot_binding_digest"), "binding.boot_binding_digest")
    _need(doc.get("grf_trace_schema") == grf.SCHEMA, "BINDING_GRF_SCHEMA_MISMATCH")
    _need(type(doc.get("grf_trace_nodes")) is int and doc["grf_trace_nodes"] > 0, "BINDING_NODE_COUNT_INVALID")
    _need(doc.get("authority") == "BINDING_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY", "BINDING_AUTHORITY_ESCALATION")
    _need(doc.get("runtime_credit") == "ZERO", "BINDING_RUNTIME_CREDIT_FORBIDDEN")
    _need(doc.get("truth_credit") == "ZERO", "BINDING_TRUTH_CREDIT_FORBIDDEN")
    _need(doc.get("effect_credit") == "ZERO", "BINDING_EFFECT_CREDIT_FORBIDDEN")
    digest = _digest(doc.get("binding_digest"), "binding.binding_digest")
    unsigned = dict(doc)
    unsigned.pop("binding_digest")
    _need(digest == _sha256_obj(unsigned), "BINDING_DIGEST_MISMATCH")
    return {
        "ok": True,
        "schema": SCHEMA,
        "binding_digest": digest,
        "runtime_credit": "ZERO",
        "truth_credit": "ZERO",
        "effect_credit": "ZERO",
    }
