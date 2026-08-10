#!/usr/bin/env python3
"""Inventory the exact mixed-flat binding frontier without choosing precedence.

Input is the already preserved residual TypedIR and the explicit-binding bundle. For every
REJECTED_AMBIGUOUS_BINDING clause this tool emits canonical tokens and every ambiguous flat-chain
operator signature. It never proposes an ordering, rewrites source, executes calls, or mints
truth/effect/execution authority.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

import claycode_wp03_rule_invariant_binding_gate_v1 as binding

SCHEMA = "ClayCodeAmbiguousBindingInventory/v1"
DOMAIN = b"ClayCodeAmbiguousBindingInventory/v1\x00"


def stable_json(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _collect_ambiguous(plan: Any, path: str = "$") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(plan, dict):
        if plan.get("binding_status") == "AMBIGUOUS_BINDING":
            ops = plan.get("operators") or []
            out.append({
                "path": path,
                "operators": [
                    {
                        "class": op.get("class"),
                        "name": op.get("name"),
                        "explicit_equals_marker": bool(op.get("explicit_equals_marker")),
                    }
                    for op in ops
                    if isinstance(op, dict)
                ],
                "operator_signature": [
                    f"{op.get('class')}:{op.get('name')}:{1 if op.get('explicit_equals_marker') else 0}"
                    for op in ops
                    if isinstance(op, dict)
                ],
                "operand_count": len(plan.get("operands") or []),
            })
        for key, value in plan.items():
            out.extend(_collect_ambiguous(value, f"{path}.{key}"))
    elif isinstance(plan, list):
        for i, value in enumerate(plan):
            out.extend(_collect_ambiguous(value, f"{path}[{i}]"))
    return out


def build_inventory(typed_ir: dict[str, Any]) -> dict[str, Any]:
    bundle = binding.lower_bundle(typed_ir)
    clauses = {int(c["index"]): c for c in bundle.get("clauses", [])}
    residuals = typed_ir.get("opaque_unlowered_semantics") or []
    rows: list[dict[str, Any]] = []
    for rejected in bundle.get("rejected", []):
        index = int(rejected["index"])
        clause = clauses[index]
        residual = residuals[index]
        ast = residual.get("canonical_ast") if isinstance(residual, dict) else None
        ambiguous = _collect_ambiguous(clause.get("plan"))
        if not ambiguous:
            raise ValueError(f"rejected binding {index} has no ambiguous plan node")
        token_values = binding.token_values(ast)
        row_core = {
            "residual_index": index,
            "clause_kind": residual.get("kind"),
            "binding_id": clause.get("binding_id"),
            "source_residual_sha256": clause.get("source_residual_sha256"),
            "canonical_tokens": token_values,
            "canonical_compact": " ".join(token_values),
            "ambiguous_flat_chains": ambiguous,
            "required_resolution": "EXPLICIT_GROUPING_OR_SEPARATELY_FROZEN_PRECEDENCE",
            "automatic_precedence_choice": "FORBIDDEN",
            "semantic_consumer": "DENY",
            "execution_authority": "NONE",
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        }
        row_hash = hashlib.sha256(b"ClayCodeAmbiguousBindingRow/v1\x00" + stable_json(row_core)).hexdigest()
        rows.append({**row_core, "row_sha256": row_hash})

    signature_counts = Counter()
    for row in rows:
        for chain in row["ambiguous_flat_chains"]:
            signature_counts[" -> ".join(chain["operator_signature"])] += 1
    core = {
        "schema": SCHEMA,
        "source_typed_ir_sha256": typed_ir.get("typed_ir_sha256"),
        "source_binding_bundle_sha256": bundle.get("bundle_sha256"),
        "rows": rows,
        "summary": {
            "ambiguous_clause_count": len(rows),
            "ambiguous_chain_count": sum(len(r["ambiguous_flat_chains"]) for r in rows),
            "operator_signature_counts": dict(sorted(signature_counts.items())),
            "automatic_precedence_choice": "FORBIDDEN",
            "semantic_consumer_admitted": 0,
            "execution_admitted": 0,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
        "promotion": "NONE",
    }
    return {**core, "inventory_sha256": hashlib.sha256(DOMAIN + stable_json(core)).hexdigest()}
