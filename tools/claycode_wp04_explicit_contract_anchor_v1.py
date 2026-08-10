#!/usr/bin/env python3
"""WP04 explicit-callable contract anchoring without execution admission.

This layer consumes an explicitly authored ClayCode interface plus explicit call metadata.
It does not infer concrete types from call sites. Exact interface signatures are matched to
exact target+arity obligations, then used only to anchor symbolic type-equality components.
Runtime binding and execution remain separate and fail closed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as base_typed

DOMAIN = b"ClayCodeExplicitCallContractAnchor/v1\x00"
CONTRACT_DOMAIN = b"ClayCodeExplicitCallContract/v1\x00"
SCHEMA = "ClayCodeExplicitCallContractAnchor/v1-research"
FORBIDDEN_ESCAPE_TYPES = {"Any", "Unknown", "Dynamic"}
ALLOWED_EFFECT_CLASSES = {"PURE", "READ_STATE", "DERIVED_STATE", "RESEARCH_ONLY", "EXTERNAL_EFFECT"}


class ExplicitContractError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + stable_json(value)).hexdigest()


def exact_signature_map(ir: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    """Return only exact TypedIR function/interface identities with explicit param/return types."""
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for decl in ir.get("declarations", []):
        if not isinstance(decl, dict):
            continue
        if decl.get("kind") == "function" and isinstance(decl.get("name"), str):
            params = decl.get("params", [])
            key = (decl["name"], len(params))
            row = {"target": key[0], "arity": key[1], "params": params, "returns": decl.get("returns")}
            if key in out:
                raise ExplicitContractError(f"duplicate exact callable identity: {key}")
            out[key] = row
        elif decl.get("kind") == "interface" and isinstance(decl.get("name"), str):
            iface = decl["name"]
            for method in decl.get("methods", []):
                if not isinstance(method, dict) or not isinstance(method.get("name"), str):
                    continue
                params = method.get("params", [])
                key = (f"{iface}.{method['name']}", len(params))
                row = {"target": key[0], "arity": key[1], "params": params, "returns": method.get("returns")}
                if key in out:
                    raise ExplicitContractError(f"duplicate exact callable identity: {key}")
                out[key] = row
    return out


def _parse_contract_rule(vals: list[str], rule_name: str) -> tuple[tuple[str, int], str] | None:
    """Parse only exact `rule name(target,arity)=value` canonical-token shapes."""
    if rule_name not in vals:
        return None
    try:
        i = vals.index(rule_name)
        lp = vals.index("(", i + 1)
        comma = vals.index(",", lp + 1)
        rp = vals.index(")", comma + 1)
        eq = vals.index("=", rp + 1)
    except ValueError as exc:
        raise ExplicitContractError(f"malformed {rule_name} rule tokens: {vals!r}") from exc
    target = "".join(vals[lp + 1 : comma])
    arity_text = "".join(vals[comma + 1 : rp])
    value = "".join(vals[eq + 1 :])
    if not target or not arity_text.isdigit() or not value:
        raise ExplicitContractError(f"invalid {rule_name} payload: {vals!r}")
    return (target, int(arity_text)), value


def explicit_call_metadata(path: Path, grammar_path: Path) -> dict[tuple[str, int], dict[str, str]]:
    """Read effect/authority/execution metadata from canonical ClayCode rules, not comments."""
    grammar = grammar_path.read_text(encoding="utf-8")
    artifact = front.compile_frontend(path.read_text(encoding="utf-8"), grammar, strict=True)
    rows: dict[tuple[str, int], dict[str, str]] = {}
    fields = {
        "call_effect": "effect_class",
        "call_binding_authority": "binding_authority",
        "call_execution_admitted": "execution_admitted",
        "call_truth_authority": "truth_authority",
    }
    for node in base_typed.walk(artifact["canonical_ast"]):
        if base_typed.kind(node) != "rule_decl":
            continue
        vals = base_typed.token_values(node)
        for rule_name, field in fields.items():
            parsed = _parse_contract_rule(vals, rule_name)
            if parsed is None:
                continue
            key, value = parsed
            row = rows.setdefault(key, {})
            if field in row and row[field] != value:
                raise ExplicitContractError(f"conflicting {field} metadata for {key}")
            row[field] = value
    for key, row in rows.items():
        missing = set(fields.values()) - set(row)
        if missing:
            raise ExplicitContractError(f"incomplete explicit call metadata for {key}: {sorted(missing)}")
        if row["effect_class"] not in ALLOWED_EFFECT_CLASSES:
            raise ExplicitContractError(f"unsupported effect class for {key}: {row['effect_class']}")
        if row["execution_admitted"] not in {"true", "false"}:
            raise ExplicitContractError(f"execution flag must be boolean for {key}")
    return rows


def _type_is_forbidden(type_name: str | None) -> bool:
    if not isinstance(type_name, str) or not type_name:
        return True
    parts = []
    cur = ""
    for ch in type_name:
        if ch.isalnum() or ch in "_.":
            cur += ch
        else:
            if cur:
                parts.append(cur)
                cur = ""
    if cur:
        parts.append(cur)
    return any(part in FORBIDDEN_ESCAPE_TYPES for part in parts)


def build_anchor_report(
    graph: dict[str, Any],
    ir: dict[str, Any],
    metadata: dict[tuple[str, int], dict[str, str]],
    *,
    candidate_source_ref: str,
) -> dict[str, Any]:
    signatures = exact_signature_map(ir)
    obligations = {
        (row["identity"]["target"], int(row["identity"]["arity"])): row
        for row in graph.get("obligations", [])
    }
    contracts = []
    anchor_types: dict[str, str] = {}

    for key in sorted(set(signatures) & set(metadata) & set(obligations)):
        obligation = obligations[key]
        if obligation.get("resolution_state") != "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING":
            raise ExplicitContractError(f"explicit contract did not resolve exact declaration identity for {key}")
        sig = signatures[key]
        meta = metadata[key]
        params = sig.get("params", [])
        if len(params) != key[1]:
            raise ExplicitContractError(f"arity/signature mismatch for {key}")
        if any(_type_is_forbidden(p.get("type")) for p in params):
            raise ExplicitContractError(f"missing/forbidden concrete parameter type for {key}")
        if _type_is_forbidden(sig.get("returns")):
            raise ExplicitContractError(f"missing/forbidden concrete return type for {key}")
        if meta["execution_admitted"] != "false":
            raise ExplicitContractError(f"candidate contract attempts execution admission for {key}")
        if meta["binding_authority"] != "NONE":
            raise ExplicitContractError(f"candidate contract attempts binding authority for {key}")
        if meta["truth_authority"] != "NONE":
            raise ExplicitContractError(f"candidate contract attempts truth authority for {key}")
        if meta["effect_class"] == "EXTERNAL_EFFECT":
            raise ExplicitContractError(f"ordinary explicit-contract anchor cannot admit EXTERNAL_EFFECT {key}")

        core = {
            "target": key[0],
            "arity": key[1],
            "params": [{"name": p.get("name", ""), "type": p["type"]} for p in params],
            "returns": sig["returns"],
            "effect_class": meta["effect_class"],
            "binding_authority": meta["binding_authority"],
            "execution_admitted": False,
            "truth_authority": meta["truth_authority"],
            "candidate_source_ref": candidate_source_ref,
        }
        contract_hash = sha256(CONTRACT_DOMAIN, core)
        contracts.append({**core, "contract_semantic_hash": contract_hash})
        for i, param in enumerate(params):
            anchor_types[f"param:{key[0]}/{key[1]}#{i}"] = param["type"]
        anchor_types[f"ret:{key[0]}/{key[1]}"] = sig["returns"]

    if not contracts:
        raise ExplicitContractError("no exact explicitly-authored contract matched a measured obligation")

    anchored_components = []
    conflicts = []
    for index, component in enumerate(graph.get("type_equality_components", [])):
        labels = sorted({anchor_types[node] for node in component if node in anchor_types})
        if not labels:
            continue
        row = {"component_index": index, "concrete_types": labels, "members": component}
        anchored_components.append(row)
        if len(labels) > 1:
            conflicts.append(row)
    if conflicts:
        raise ExplicitContractError(f"explicit contract creates concrete type conflict(s): {conflicts!r}")

    core = {
        "schema": SCHEMA,
        "source_constraint_graph_sha256": graph.get("constraint_graph_sha256"),
        "source_typed_ir_sha256": ir.get("typed_ir_sha256"),
        "candidate_source_ref": candidate_source_ref,
        "contracts": contracts,
        "concrete_anchor_nodes": dict(sorted(anchor_types.items())),
        "anchored_components": anchored_components,
        "invariants": {
            "signature_from_callsite_inference": "FORBIDDEN",
            "fuzzy_or_suffix_resolution": "FORBIDDEN",
            "any_unknown_dynamic_escape": "FORBIDDEN",
            "contract_is_runtime_binding": "FORBIDDEN",
            "contract_mints_execution_authority": "FORBIDDEN",
            "contract_mints_truth_authority": "FORBIDDEN",
            "external_effect_through_ordinary_anchor": "FORBIDDEN",
        },
    }
    report_hash = sha256(DOMAIN, core)
    total_components = len(graph.get("type_equality_components", []))
    return {
        **core,
        "anchor_report_sha256": report_hash,
        "summary": {
            "explicit_exact_contracts": len(contracts),
            "concrete_anchor_nodes": len(anchor_types),
            "anchored_components": len(anchored_components),
            "unanchored_components": total_components - len(anchored_components),
            "conflicting_components": 0,
            "execution_admitted_calls": 0,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
        "promotion": "NONE",
        "wp03_status": "OPEN",
        "wp04_status": "OPEN",
    }
