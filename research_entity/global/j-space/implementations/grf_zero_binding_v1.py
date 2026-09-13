#!/usr/bin/env python3
"""Fail-closed binding between one GRF Brain trace and canonical ZERO prepare material.

The canonical MiniUnifiedDB ``grf_digest`` identifies the versioned GRF framework object.
A per-turn R0..R6 trace is a separate candidate/control artifact identified by
``trace_digest`` and carrying ``framework_digest``. This adapter proves that the trace
uses exactly the framework already bound into the active prepare, plus the same entity
generation and causal turn. It owns no truth/state/effect/runtime authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

import grf_brain_v1 as grf

SCHEMA = "OMEGA_GRF_ZERO_BINDING/v1"
COMPILER_VERSION = "omega-grf-zero-binding/1.1"
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
    """Bind a SEALED per-turn trace to the canonical GRF framework in one prepare."""
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
    prepare_framework_digest = _digest(prepare.get("grf_digest"), "prepare.grf_digest")
    turn_binding_digest = _digest(prepare.get("turn_binding_digest"), "prepare.turn_binding_digest")
    boot_binding_digest = _digest(prepare.get("boot_binding_digest"), "prepare.boot_binding_digest")
    trace_digest = _digest(trace.get("trace_digest"), "trace.trace_digest")
    framework_digest = _digest(trace.get("framework_digest"), "trace.framework_digest")

    _need(trace.get("entity_generation") == generation, "GRF_GENERATION_MISMATCH")
    _need(trace.get("causal_turn_id") == causal_turn_id, "GRF_CAUSAL_TURN_MISMATCH")
    _need(framework_digest == prepare_framework_digest, "GRF_FRAMEWORK_NOT_PREPARE_BOUND")

    receipt = {
        "schema": SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "entity_generation": generation,
        "causal_turn_id": causal_turn_id,
        "framework_digest": framework_digest,
        "trace_digest": trace_digest,
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
    validate_binding(receipt)
    return receipt


def validate_binding(receipt: Mapping[str, Any]) -> dict[str, Any]:
    _need(isinstance(receipt, Mapping), "BINDING_RECEIPT_OBJECT_REQUIRED")
    doc = dict(receipt)
    expected = {
        "schema",
        "compiler_version",
        "entity_generation",
        "causal_turn_id",
        "framework_digest",
        "trace_digest",
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
    _digest(doc.get("framework_digest"), "binding.framework_digest")
    _digest(doc.get("trace_digest"), "binding.trace_digest")
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
        "framework_digest": doc["framework_digest"],
        "trace_digest": doc["trace_digest"],
        "runtime_credit": "ZERO",
        "truth_credit": "ZERO",
        "effect_credit": "ZERO",
    }
