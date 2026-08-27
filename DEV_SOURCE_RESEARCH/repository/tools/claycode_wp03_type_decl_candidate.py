#!/usr/bin/env python3
"""CC-WP-03 candidate: preserve V18 type/class declarations in typed semantic IR.

The current BASE V18 frontend admits `type`/`class` declarations, but the production
`claycode_base_typed_ir` slice only materializes record/interface/function declarations.
That makes changes confined to a type/class declaration invisible to the current typed
semantic identity and can misclassify a locally declared nominal as EXTERNAL_NOMINAL.

This module is deliberately a candidate wrapper, not a silent production promotion. It
reuses the current builder, adds only already-parsed V18 declaration semantics, recomputes
typed semantic identity, and preserves the authority law that declarations mint no runtime
capability/effect authority.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import claycode_base_typed_ir as base

VERSION = "claycode-wp03-type-decl-candidate/0.1"
IR_SCHEMA = "ClayCodeBaseTypedIR/v1.1-candidate-type-class-declarations"
DOMAIN = b"ClayCodeBaseTypedIRTypeDeclCandidate/v1\x00"
TYPE_KINDS = {"record", "interface", "type", "class"}


class TypeDeclCandidateError(ValueError):
    pass


def _stable(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_type_or_class(node: Any) -> dict[str, Any]:
    vals = base.token_values(node)
    if not vals:
        raise TypeDeclCandidateError("empty class_decl")
    decl_kind = vals[0]
    if decl_kind not in {"type", "class"}:
        raise TypeDeclCandidateError(f"class_decl missing type/class keyword: {vals!r}")
    name = base.direct_identifier(node)
    if not name:
        raise TypeDeclCandidateError(f"{decl_kind} declaration without name: {vals!r}")
    try:
        eq = vals.index("=")
    except ValueError as exc:
        raise TypeDeclCandidateError(f"{decl_kind} declaration without '=': {vals!r}") from exc
    rhs = vals[eq + 1 :]
    if not rhs:
        raise TypeDeclCandidateError(f"{decl_kind} declaration without RHS: {vals!r}")
    return {
        "kind": decl_kind,
        "name": name,
        "rhs_tokens": rhs,
        "authority": "NONE",
    }


def _candidate_declarations(units: list[base.SourceUnit]) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    for unit in units:
        ast = unit.frontend["canonical_ast"]
        for node in base.walk(ast):
            if base.kind(node) == "class_decl":
                extra.append(parse_type_or_class(node))
    return extra


def build_typed_ir_candidate(units: list[base.SourceUnit]) -> dict[str, Any]:
    current = base.build_typed_ir(units)
    declarations = list(current["declarations"]) + _candidate_declarations(units)

    # Type-space declaration names must be unique regardless of syntactic declaration kind.
    # This is fail-closed in the candidate because one nominal cannot safely denote two
    # independent semantic definitions at the same program identity.
    type_names = [d["name"] for d in declarations if d.get("kind") in TYPE_KINDS]
    duplicates = sorted({name for name in type_names if type_names.count(name) > 1})
    if duplicates:
        raise TypeDeclCandidateError(f"duplicate type-space declaration(s): {duplicates}")
    declared_types = set(type_names)

    rows = {row["name"]: dict(row) for row in current["types"]}
    for name in declared_types:
        row = rows.get(name)
        if row is None:
            rows[name] = {"name": name, "class": "DECLARED_NOMINAL"}
        elif row.get("class") not in {"PRIMITIVE", "TYPE_CONSTRUCTOR"}:
            row["class"] = "DECLARED_NOMINAL"

    semantic_core = {
        "schema_version": "1.2-candidate",
        "ir_schema": IR_SCHEMA,
        "types": [rows[name] for name in sorted(rows)],
        "declarations": sorted(declarations, key=lambda d: (d["kind"], d["name"])),
        "invariants": dict(current["invariants"]),
    }
    semantic_core["invariants"]["v18_type_class_declaration_semantics_preserved"] = "REQUIRED"
    ir_hash = _sha256(DOMAIN + _stable(semantic_core))

    return {
        **semantic_core,
        "sources": list(current["sources"]),
        "typed_ir_sha256": ir_hash,
        "program_semantic_id": f"clayir-candidate:{ir_hash}",
        "candidate": {
            "version": VERSION,
            "baseline_ir_schema": current["ir_schema"],
            "semantic_change": "NONE_SURFACE; IMPLEMENT_ALREADY_PARSED_TYPE_CLASS_DECLARATIONS",
            "promotion": "NONE",
        },
    }


__all__ = [
    "VERSION",
    "IR_SCHEMA",
    "TypeDeclCandidateError",
    "parse_type_or_class",
    "build_typed_ir_candidate",
]
