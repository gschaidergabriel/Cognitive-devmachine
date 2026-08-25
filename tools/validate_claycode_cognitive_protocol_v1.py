#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from lark import Token, Tree

from claycode_base_frontend import build_parser, compile_frontend

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "research_entity/global/CLAYCODE_COGNITIVE_PROTOCOL_v1.clay"
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"


class ProtocolValidationError(ValueError):
    pass


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise ProtocolValidationError(code)


def _tokens(node: Tree | Token) -> list[str]:
    if isinstance(node, Token):
        return [str(node)]
    out: list[str] = []
    for child in node.children:
        if isinstance(child, (Tree, Token)):
            out.extend(_tokens(child))
    return out


def _records(tree: Tree) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for node in tree.find_data("record_decl"):
        toks = _tokens(node)
        _require(len(toks) >= 3 and toks[0] == "record", "RECORD_SHAPE_INVALID")
        name = toks[1]
        fields: set[str] = set()
        for field in node.find_data("field"):
            ftoks = _tokens(field)
            _require(bool(ftoks), f"FIELD_SHAPE_INVALID_{name}")
            fields.add(ftoks[0])
        out[name] = fields
    return out


def _type_values(tree: Tree, name: str) -> set[str]:
    for node in tree.find_data("class_decl"):
        toks = _tokens(node)
        if len(toks) >= 4 and toks[0] == "type" and toks[1] == name:
            return {x for x in toks[3:] if x not in {"|", "="}}
    raise ProtocolValidationError(f"TYPE_MISSING_{name}")


def _rule_sequences(tree: Tree) -> set[tuple[str, ...]]:
    return {tuple(_tokens(node)[1:]) for node in tree.find_data("rule_decl")}


def validate(source: str, grammar: str) -> dict[str, Any]:
    parser = build_parser(grammar, strict=False)
    tree = parser.parse(source)
    frontend = compile_frontend(source, grammar, strict=False)

    parents = set()
    for node in tree.find_data("parent_decl"):
        parents.update(x for x in _tokens(node) if x.startswith("@"))
    required_parents = {
        "@research_entity/global/COGNITIVE_PROCESS_ABI_v1.json",
        "@research_entity/global/DB_VS_SIMULATION_BOUNDARY_v1.json",
        "@research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json",
    }
    _require(required_parents <= parents, "CURRENT_CONTRACT_PARENT_MISSING")

    records = _records(tree)
    required_fields = {
        "GridRuntime": {"requested_N", "observed_available_N", "grid_instance_id"},
        "DbStateRef": {"ref_id", "store", "snapshot_or_epoch", "object_key", "digest", "provenance", "mutability"},
        "CognitiveWorkPacket": {
            "schema", "causal_event_id", "admission_id", "generation", "work_id", "process_id",
            "parent_work_ids", "workspace_epoch", "state_snapshot_ref", "input_refs", "epistemic_inputs",
            "capability_scope_ref", "resource_budget", "grid_runtime", "route_policy_ref", "completion_contract",
        },
        "GridExecutorBinding": {
            "grid_instance_id", "requested_N", "available_N", "executor_id", "lease_id", "process_id",
            "runtime_identity", "started_at", "ended_at",
        },
        "DbWriteProposal": {
            "causal_event_id", "admission_id", "generation", "work_id", "source_result_id", "expected_state_ref",
            "object_key", "value_ref", "value_digest", "provenance_ref",
        },
        "EffectProposal": {
            "causal_event_id", "admission_id", "generation", "work_id", "source_result_id",
            "capability_scope_ref", "request_ref", "request_digest",
        },
        "WorkspaceReentry": {
            "source_result_id", "source_process_id", "causal_event_id", "from_workspace_epoch", "to_workspace_epoch",
            "reentry_payload_ref", "reentry_digest", "observed_downstream_change",
        },
        "ClaudeCodeBridgePacket": {
            "bridge_id", "direction", "causal_event_id", "work_id", "workspace_epoch", "interface_class",
            "payload_ref", "payload_digest", "state_refs", "tool_scope_ref", "request_or_result_identity",
        },
        "JSpaceMeasurement": {
            "measurement_id", "causal_event_id", "generation", "model_runtime_identity", "interface_identity",
            "intervention_identity", "pre_state_digest", "post_state_digest", "behavioral_result_ref", "credit_scope",
        },
        "CognitiveResultPacket": {
            "schema", "causal_event_id", "admission_id", "generation", "work_id", "process_id", "executor_binding",
            "result_id", "result_class", "result_payload_ref", "result_digest", "evidence_refs", "unknowns",
            "db_write_proposals", "effect_request_candidates", "workspace_reentry", "runtime_receipt",
        },
    }
    for name, fields in required_fields.items():
        _require(name in records, f"RECORD_MISSING_{name}")
        _require(fields <= records[name], f"REQUIRED_FIELD_MISSING_{name}")

    _require(_type_values(tree, "ResultClass") == {"CANDIDATE", "PROJECTION", "MEASUREMENT"}, "RESULT_CLASS_AUTHORITY_ESCALATION")
    _require(_type_values(tree, "EpistemicStatus") == {"OBSERVED", "INFERRED", "HYPOTHESIS", "UNKNOWN"}, "EPISTEMIC_STATUS_SET_MISMATCH")
    _require(_type_values(tree, "TriState") == {"TRUE", "FALSE", "UNKNOWN"}, "TRISTATE_SET_MISMATCH")

    rules = _rule_sequences(tree)
    mandatory_rules = {
        ("GridRuntime", ".", "requested_N", "never_implies", "CognitiveProcessIdentity"),
        ("GridRuntime", ".", "observed_available_N", "never_implies", "CognitiveProcessIdentity"),
        ("CognitiveResultPacket", "never_confers", "CanonicalFact"),
        ("DbWriteProposal", "never_confers", "CanonicalDBCommit"),
        ("EffectProposal", "cannot_authorize", "RealEffect"),
        ("RealEffect", "requires", "ZECP17"),
        ("ClaudeCodeBridgePacket", "never_confers", "CanonicalFact"),
        ("WorkspaceReentry", ".", "observed_downstream_change", "never_implies", "JSpaceCausalCredit"),
        ("JSpaceMeasurement", "never_confers", "CanonicalFact"),
        ("JSpaceMeasurement", "never_confers", "RealEffectAuthority"),
        ("UNKNOWN", "distinct_from", "false"),
        ("MethodPresent", "never_implies", "FactPresent"),
    }
    _require(mandatory_rules <= rules, "MANDATORY_AUTHORITY_RULE_MISSING")

    return {
        "ok": True,
        "schema": "CLAYCODE_COGNITIVE_PROTOCOL/v1",
        "frontend_schema": frontend["frontend_schema"],
        "surface": frontend["surface"],
        "semantic_hash": frontend["semantic_hash"],
        "record_count": len(records),
        "runtime_credit": 0,
        "jspace_credit": 0,
        "training_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    ap.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    args = ap.parse_args()
    result = validate(args.protocol.read_text(encoding="utf-8"), args.grammar.read_text(encoding="utf-8"))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
