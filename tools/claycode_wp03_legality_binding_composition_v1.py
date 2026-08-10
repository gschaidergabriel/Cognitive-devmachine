#!/usr/bin/env python3
"""Compose ClayCode rule/invariant structural legality with binding authority.

The structural legality gate and the explicit-binding gate answer different questions:
1. Is this preserved V18 AST inside a finite admitted rule/invariant syntax envelope?
2. Is its semantic binding explicit enough to admit a WP05 symbolic semantic plan?

A structurally legal row with unresolved flat binding remains data-preserved but is DENIED
semantic-consumer admission. This module never executes calls and mints no effect/truth authority.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import claycode_wp04_rule_invariant_legality_v1 as legality

SCHEMA = "ClayCodeLegalityBindingComposition/v1"
DOMAIN = b"ClayCodeLegalityBindingComposition/v1\x00"
SEMANTICALLY_BOUND = "STRUCTURALLY_LEGAL_SEMANTICALLY_BOUND"
BINDING_UNRESOLVED = "STRUCTURALLY_LEGAL_BINDING_UNRESOLVED"
STRUCTURAL_REJECT = "STRUCTURAL_LEGALITY_REJECTED"
DEFERRED = "NON_TARGET_CLASS_DEFERRED"


class CompositionError(ValueError):
    pass


def stable_json(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(v: Any) -> str:
    return hashlib.sha256(DOMAIN + stable_json(v)).hexdigest()


def compose(*, residuals: list[dict[str, Any]], structural_receipt: dict[str, Any], binding_bundle: dict[str, Any]) -> dict[str, Any]:
    legality.validate_receipt(structural_receipt)
    structural_rows = structural_receipt.get("rows")
    binding_rows = binding_bundle.get("clauses")
    if not isinstance(structural_rows, list) or len(structural_rows) != len(residuals):
        raise CompositionError("structural receipt must cover the exact residual inventory")
    if not isinstance(binding_rows, list):
        raise CompositionError("binding bundle clauses missing")
    binding_by_index = {int(r["index"]): r for r in binding_rows}
    if len(binding_by_index) != len(binding_rows):
        raise CompositionError("duplicate binding index")

    rows: list[dict[str, Any]] = []
    for index, residual in enumerate(residuals):
        if structural_rows[index].get("index") != index:
            raise CompositionError("structural row index drift")
        sr = structural_rows[index]
        kind = residual.get("kind") if isinstance(residual, dict) else None
        if kind not in {"rule_decl", "invariant_decl"}:
            if sr.get("status") != legality.DEFERRED:
                raise CompositionError(f"non-target residual {index} was not deferred")
            rows.append({
                "index": index,
                "kind": kind,
                "status": DEFERRED,
                "semantic_consumer": "DENY",
                "effect_authority": "NONE",
                "truth_authority": "NONE",
            })
            continue

        if sr.get("status") != legality.LOWERED:
            rows.append({
                "index": index,
                "kind": kind,
                "status": STRUCTURAL_REJECT,
                "semantic_consumer": "DENY",
                "structural_reason": sr.get("reason"),
                "effect_authority": "NONE",
                "truth_authority": "NONE",
            })
            continue

        br = binding_by_index.get(index)
        if br is None:
            raise CompositionError(f"structurally legal target row {index} has no binding adjudication")
        if br.get("effect_authority") != "NONE" or br.get("truth_authority") != "NONE":
            raise CompositionError("binding adjudication minted authority")
        binding_status = br.get("binding_status")
        if binding_status == "LOWERED_AND_VALIDATED_EXPLICIT_BINDING":
            status = SEMANTICALLY_BOUND
            consumer = "ALLOW_DATA_ONLY_SYMBOLIC_SEMANTICS"
        elif binding_status == "REJECTED_AMBIGUOUS_BINDING":
            status = BINDING_UNRESOLVED
            consumer = "DENY"
        else:
            raise CompositionError(f"unknown binding status: {binding_status!r}")
        rows.append({
            "index": index,
            "kind": kind,
            "status": status,
            "semantic_consumer": consumer,
            "structural_constraint_sha256": sr.get("constraint_sha256"),
            "binding_id": br.get("binding_id"),
            "binding_semantic_sha256": br.get("binding_semantic_sha256"),
            "effect_authority": "NONE",
            "truth_authority": "NONE",
            "execution_authority": "NONE",
        })

    counts = {
        SEMANTICALLY_BOUND: sum(r["status"] == SEMANTICALLY_BOUND for r in rows),
        BINDING_UNRESOLVED: sum(r["status"] == BINDING_UNRESOLVED for r in rows),
        STRUCTURAL_REJECT: sum(r["status"] == STRUCTURAL_REJECT for r in rows),
        DEFERRED: sum(r["status"] == DEFERRED for r in rows),
    }
    core = {
        "schema": SCHEMA,
        "source_structural_receipt_sha256": structural_receipt.get("receipt_sha256"),
        "source_binding_bundle_sha256": binding_bundle.get("bundle_sha256"),
        "rows": rows,
        "summary": {
            **counts,
            "total": len(rows),
            "semantic_consumer_admitted": counts[SEMANTICALLY_BOUND],
            "execution_admitted": 0,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
        "invariants": {
            "structural_legality_implies_binding": "FORBIDDEN",
            "ambiguous_binding_semantic_consumption": "FORBIDDEN",
            "raw_ast_preservation_mints_truth": "FORBIDDEN",
            "call_descriptor_execution": "FORBIDDEN",
        },
        "promotion": "NONE",
    }
    return {**core, "composition_sha256": digest(core)}


def semantic_consume(composed_row: dict[str, Any]) -> dict[str, Any]:
    if composed_row.get("status") != SEMANTICALLY_BOUND:
        raise CompositionError("semantic consumer requires structurally legal + explicitly bound row")
    if composed_row.get("semantic_consumer") != "ALLOW_DATA_ONLY_SYMBOLIC_SEMANTICS":
        raise CompositionError("semantic consumer gate mismatch")
    if any(composed_row.get(k) != "NONE" for k in ("effect_authority", "truth_authority", "execution_authority")):
        raise CompositionError("authority violation")
    core = {
        "schema": "ClayCodeBoundSymbolicPlan/v1",
        "binding_semantic_sha256": composed_row.get("binding_semantic_sha256"),
        "structural_constraint_sha256": composed_row.get("structural_constraint_sha256"),
        "mode": "DATA_ONLY_BOUND_SYMBOLIC_SEMANTICS",
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "execution_authority": "NONE",
    }
    return {**core, "plan_sha256": hashlib.sha256(b"ClayCodeBoundSymbolicPlan/v1\x00" + stable_json(core)).hexdigest()}
