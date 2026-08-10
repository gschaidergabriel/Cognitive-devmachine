#!/usr/bin/env python3
"""WP04 stateful-call contract validator.

A callable may have a stable explicit parameter/return signature while still depending on
semantic receiver state. This layer requires that state dependency to be explicit, typed and
epoch-addressable before a runtime binding can ever admit execution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as base_typed
import claycode_wp04_explicit_contract_anchor_v1 as v1

DOMAIN = b"ClayCodeStatefulCallContract/v2\x00"
SCHEMA = "ClayCodeStatefulCallContract/v2-research"
ALLOWED_ACCESS = {"STATELESS", "READ_RECEIVER_STATE", "MUTATE_RECEIVER_STATE"}


class StatefulContractError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(DOMAIN + stable_json(value)).hexdigest()


def state_metadata(path: Path, grammar_path: Path) -> dict[tuple[str, int], dict[str, str]]:
    grammar = grammar_path.read_text(encoding="utf-8")
    artifact = front.compile_frontend(path.read_text(encoding="utf-8"), grammar, strict=True)
    fields = {
        "call_receiver_state_type": "receiver_state_type",
        "call_state_access": "state_access",
        "call_state_epoch_field": "state_epoch_field",
    }
    rows: dict[tuple[str, int], dict[str, str]] = {}
    for node in base_typed.walk(artifact["canonical_ast"]):
        if base_typed.kind(node) != "rule_decl":
            continue
        vals = base_typed.token_values(node)
        for rule_name, field in fields.items():
            parsed = v1._parse_contract_rule(vals, rule_name)
            if parsed is None:
                continue
            key, value = parsed
            row = rows.setdefault(key, {})
            if field in row and row[field] != value:
                raise StatefulContractError(f"conflicting {field} for {key}")
            row[field] = value
    return rows


def _record_map(ir: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r["name"]: r for r in ir.get("structural_records", []) if isinstance(r, dict) and isinstance(r.get("name"), str)}


def _field_type(record: dict[str, Any], field_name: str) -> str | None:
    for field in record.get("fields", []):
        if field.get("name") != field_name:
            continue
        expr = field.get("type_expr") or {}
        if expr.get("kind") != "nominal" or expr.get("optional"):
            return None
        return expr.get("name")
    return None


def build_stateful_report(
    graph: dict[str, Any],
    ir: dict[str, Any],
    call_meta: dict[tuple[str, int], dict[str, str]],
    state_meta: dict[tuple[str, int], dict[str, str]],
    *,
    candidate_source_ref: str,
    required_stateful_targets: set[tuple[str, int]],
) -> dict[str, Any]:
    try:
        base = v1.build_anchor_report(graph, ir, call_meta, candidate_source_ref=candidate_source_ref)
    except v1.ExplicitContractError as exc:
        raise StatefulContractError(str(exc)) from exc

    contracts = {(x["target"], int(x["arity"])): x for x in base["contracts"]}
    records = _record_map(ir)
    stateful = []
    for key in sorted(required_stateful_targets):
        if key not in contracts:
            raise StatefulContractError(f"required stateful target lacks exact explicit contract: {key}")
        meta = state_meta.get(key)
        if not meta:
            raise StatefulContractError(f"state-dependent callable hides receiver state: {key}")
        missing = {"receiver_state_type", "state_access", "state_epoch_field"} - set(meta)
        if missing:
            raise StatefulContractError(f"incomplete receiver-state contract for {key}: {sorted(missing)}")
        if meta["state_access"] not in ALLOWED_ACCESS or meta["state_access"] == "STATELESS":
            raise StatefulContractError(f"state-dependent callable cannot be STATELESS: {key}")
        state_type = meta["receiver_state_type"]
        if state_type not in records:
            raise StatefulContractError(f"receiver state type is not a declared structural record for {key}: {state_type}")
        epoch_field = meta["state_epoch_field"]
        if _field_type(records[state_type], epoch_field) != "Epoch":
            raise StatefulContractError(f"receiver state epoch field must be required Epoch for {key}: {state_type}.{epoch_field}")
        row = {
            "target": key[0],
            "arity": key[1],
            "receiver_state_type": state_type,
            "state_access": meta["state_access"],
            "state_epoch_field": epoch_field,
            "stale_epoch_execution": "FORBIDDEN",
            "runtime_binding": "NONE",
            "execution_admitted": False,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        }
        row["state_contract_semantic_hash"] = sha256(row)
        stateful.append(row)

    core = {
        "schema": SCHEMA,
        "candidate_source_ref": candidate_source_ref,
        "base_anchor_report_sha256": base["anchor_report_sha256"],
        "stateful_contracts": stateful,
        "invariants": {
            "hidden_semantic_receiver_state": "FORBIDDEN",
            "state_dependent_callable_without_receiver_contract": "FORBIDDEN",
            "receiver_state_without_required_epoch": "FORBIDDEN",
            "stale_epoch_execution": "FORBIDDEN",
            "state_contract_is_runtime_binding": "FORBIDDEN",
            "state_contract_mints_execution_authority": "FORBIDDEN",
            "state_contract_mints_truth_authority": "FORBIDDEN",
        },
    }
    report_hash = sha256(core)
    return {
        **core,
        "stateful_report_sha256": report_hash,
        "summary": {
            "explicit_exact_contracts": base["summary"]["explicit_exact_contracts"],
            "stateful_contracts": len(stateful),
            "receiver_state_records_verified": len(stateful),
            "epoch_fields_verified": len(stateful),
            "execution_admitted_calls": 0,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
        "promotion": "NONE",
        "wp03_status": "OPEN",
        "wp04_status": "OPEN",
    }
