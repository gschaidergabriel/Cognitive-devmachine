#!/usr/bin/env python3
"""CC-WP-03 candidate: preserve unlowered top-level semantics in TypedIR identity.

This is intentionally a narrow adapter around the existing builder. Structured declarations
continue to use the existing typed lowering. Top-level statements not yet semantically lowered
remain as canonical frontend AST in `opaque_unlowered_semantics` instead of disappearing.

The representation is conservative: it may distinguish source-order variants until a later
verified lowering proves an equivalence, but it must not silently equate distinct admitted
rule/law/invariant semantics. This is a candidate, not WP03 promotion.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import claycode_base_typed_ir as typed

DOMAIN = b"ClayCodeBaseTypedIR/v1.2-residual-semantics-candidate\x00"
LOWERED_TOP_LEVEL = {"record_decl", "interface_decl", "fn_decl"}


def _canon_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _opaque_top_level(unit: typed.SourceUnit) -> list[dict[str, Any]]:
    ast = unit.frontend["canonical_ast"]
    out: list[dict[str, Any]] = []
    for node in typed.children(ast):
        k = typed.kind(node)
        if k is None or k in LOWERED_TOP_LEVEL:
            continue
        out.append({"kind": k, "canonical_ast": node})
    return out


def build_typed_ir(units: list[typed.SourceUnit]) -> dict[str, Any]:
    base = typed.build_typed_ir(units)
    opaque: list[dict[str, Any]] = []
    for unit in units:
        opaque.extend(_opaque_top_level(unit))

    semantic_core = {
        "schema_version": "1.2-candidate",
        "ir_schema": "ClayCodeBaseTypedIR/v1",
        "types": base["types"],
        "declarations": base["declarations"],
        "opaque_unlowered_semantics": opaque,
        "invariants": {
            **base["invariants"],
            "unlowered_semantics_may_be_dropped": "FORBIDDEN",
            "opaque_semantics_mint_effect_authority": "FORBIDDEN",
        },
    }
    ir_hash = hashlib.sha256(DOMAIN + _canon_bytes(semantic_core)).hexdigest()
    return {
        **semantic_core,
        "sources": base["sources"],
        "typed_ir_sha256": ir_hash,
        "program_semantic_id": f"clayir-candidate:{ir_hash}",
        "lowering_status": "PARTIAL_CONSERVATIVE_PRESERVATION",
        "promotion": "NONE",
    }
