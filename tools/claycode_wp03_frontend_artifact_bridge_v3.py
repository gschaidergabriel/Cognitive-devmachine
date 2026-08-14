#!/usr/bin/env python3
"""Receipt-bound frontend-artifact -> structural ClayCode TypedIR v2 bridge candidate.

This is the production-path successor candidate to the current WP03 bridge v2. It reuses the
already-admitted frontend artifact verification contract, then builds the structural
sum-type/state-identity TypedIR without reparsing source. The bridge itself grants no execution,
effect, bearer or truth authority and does not close WP03.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import claycode_wp03_frontend_artifact_bridge as bridge_v2
import claycode_wp03_typed_ir_v2_state_identity as typed_v2

BRIDGE_SCHEMA = "ClayCodeTypedIRFrontendBinding/v3-structural-state-identity"
ARTIFACT_DOMAIN = b"ClayCodeTypedIRFrontendBinding/v3-structural-state-identity\x00"


class FrontendBindingV3Error(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    specs = manifest.get("units")
    if not isinstance(specs, list) or not specs:
        raise FrontendBindingV3Error("manifest.units must be a non-empty list")

    units = []
    bindings: list[dict[str, Any]] = []
    by_source: dict[str, tuple[str, str, str]] = {}
    for raw in specs:
        if not isinstance(raw, dict):
            raise FrontendBindingV3Error("every manifest unit must be an object")
        try:
            unit, binding = bridge_v2.verify_frontend_unit(raw)
        except bridge_v2.FrontendBindingError as exc:
            raise FrontendBindingV3Error(str(exc)) from exc
        identity = (
            binding["surface"],
            binding["grammar_sha256"],
            binding["frontend_semantic_hash"],
        )
        previous = by_source.get(binding["source_sha256"])
        if previous is not None and previous != identity:
            raise FrontendBindingV3Error(
                "same source bytes arrived through multiple non-equivalent frontend identities"
            )
        if previous is not None:
            raise FrontendBindingV3Error("duplicate frontend artifact for identical source bytes")
        by_source[binding["source_sha256"]] = identity
        units.append(unit)
        bindings.append(binding)

    ir = typed_v2.build_typed_ir_v2(units)
    if ir.get("ir_schema") != typed_v2.IR_SCHEMA:
        raise FrontendBindingV3Error(f"unexpected structural TypedIR schema: {ir.get('ir_schema')!r}")
    invariants = ir.get("invariants") if isinstance(ir.get("invariants"), dict) else {}
    required = {
        "source_identity_equals_semantic_identity": "FORBIDDEN",
        "unknown_type_to_any": "FORBIDDEN",
        "epoch_version_resource_identity_may_be_dropped": "FORBIDDEN",
        "capability_descriptor_mints_bearer_authority": "FORBIDDEN",
        "execution_trace_in_state_identity": "FORBIDDEN",
    }
    for key, expected in required.items():
        if invariants.get(key) != expected:
            raise FrontendBindingV3Error(f"structural TypedIR invariant mismatch {key}: {invariants.get(key)!r}")

    core = {
        "bridge_schema": BRIDGE_SCHEMA,
        "typed_ir_sha256": ir["typed_ir_sha256"],
        "frontend_bindings": bindings,
    }
    artifact_hash = sha256(ARTIFACT_DOMAIN + stable_json(core))
    return {
        "schema_version": "3.0-candidate",
        "bridge_schema": BRIDGE_SCHEMA,
        "typed_ir": ir,
        "frontend_bindings": bindings,
        "typed_ir_artifact_sha256": artifact_hash,
        "identity_semantics": {
            "typed_ir_sha256": "semantic structural IR identity; excludes source/provenance",
            "typed_ir_artifact_sha256": "binds structural IR to exact frontend/source/grammar/surface contracts",
            "runtime_state_identity": "type semantic identity + canonical typed value; version/epoch/resource fields participate",
        },
        "invariants": {
            "silent_reparse": "FORBIDDEN",
            "implicit_frontend_dispatch": "FORBIDDEN",
            "unbound_surface_relabel": "FORBIDDEN",
            "same_source_cross_surface_ambiguity": "FAIL_CLOSED_WITHOUT_EQUIVALENCE_RECEIPT",
            "unknown_type_to_any": "FORBIDDEN",
            "model_output_execution_authority": "FORBIDDEN",
            "capability_descriptor_bearer_authority": "FORBIDDEN",
            "frontend_artifact_mints_authority": "FORBIDDEN",
        },
        "promotion_scope": "WP03_STRUCTURAL_TYPEDIR_PRODUCTION_PATH_CANDIDATE",
        "promotion": "NONE",
        "wp03_status": "OPEN_PENDING_EXACT_CURRENT_ADJUDICATION",
    }
