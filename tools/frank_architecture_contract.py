#!/usr/bin/env python3
"""Validate that a FRANK research run expresses its architecture in ClayCode semantic IR.

ClayCode's durable meaning is currently a semantic IR with reader-specific projections;
therefore the required architecture source is a deterministic JSON projection named
FRANK_ARCHITECTURE.claycode.json rather than an prematurely frozen surface syntax.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_PROPOSAL_CLASSES = {"PURE_TRANSFORM", "STATE_PROPOSAL", "EFFECT_PROPOSAL"}
ARCH_NAME = "FRANK_ARCHITECTURE.claycode.json"
MAPPING_NAME = "CLAYCODE_ARCHITECTURE_MAPPING.md"
INTERCONNECT_NAME = "INTERCONNECT_MANIFEST.json"


def _load(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return obj


def template(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "language": "ClayCode",
        "representation": "canonical_semantic_ir_json_projection",
        "ir_version": "OPEN",
        "architecture_id": f"frank-{run_id}",
        "run_id": run_id,
        "status": "OPEN_ARCHITECTURE_CANDIDATE",
        "source_research": {
            "clay": [],
            "claycode": [],
            "gwt": [],
            "hyperposition": [],
            "emergenz": [],
            "frank_runtime": []
        },
        "semantic_contract": {
            "canonical_truth_is_not_activation": True,
            "model_output_is_proposal_not_authority": True,
            "semantic_identity_independent_of_wire_projection": True,
            "unknown_conflict_revoked_are_explicit": True
        },
        "modules": [
            {
                "module_id": "REPLACE_ME",
                "kind": "organ_or_runtime_boundary",
                "state_contract_refs": [],
                "dependencies": [],
                "invariants": []
            }
        ],
        "transitions": [
            {
                "op_id": "REPLACE_ME",
                "proposal_class": "PURE_TRANSFORM",
                "reads": [],
                "writes": [],
                "invariant_scope": [],
                "effects": [],
                "capability_refs": [],
                "causal_links": [],
                "gwt_links": []
            }
        ],
        "persistence_replay": {
            "event_identity": "REPLACE_ME",
            "replay_semantics": "REPLACE_ME",
            "recovery_boundary": "REPLACE_ME"
        },
        "authority_boundary": {
            "model_output_is_authority": False,
            "external_capability_gateway_required": True,
            "effect_receipts_required": True
        },
        "host_kernel_boundary": {
            "self_authorizing": False,
            "components": ["parser", "validator", "canonicalizer", "bootstrap_trust_root", "capability_effect_gateway"]
        },
        "provenance": {
            "actor": "REPLACE_ME",
            "provider": "REPLACE_ME",
            "model": "REPLACE_ME",
            "canonical_parent": "REPLACE_ME"
        }
    }


def validate(run_dir: Path) -> dict[str, Any]:
    inter = _load(run_dir / INTERCONNECT_NAME)
    arch = _load(run_dir / ARCH_NAME)
    violations: list[str] = []

    priority = inter.get("branch_priority") or []
    if len(priority) < 2 or priority[0] != "clay" or priority[1] != "claycode":
        violations.append("INTERCONNECT_MANIFEST must prioritize clay then claycode for FRANK")
    special = inter.get("special_rules") or {}
    if special.get("frank_requires_latest_clay_architecture_as_primary_foundation") is not True:
        violations.append("FRANK interconnect must require latest Clay architecture foundation")
    if special.get("frank_requires_deep_claycode_architecture_input") is not True:
        violations.append("FRANK interconnect must require deep ClayCode architecture input")
    if special.get("frank_architecture_source_language") != "ClayCode semantic IR":
        violations.append("FRANK architecture source language must be ClayCode semantic IR")

    if arch.get("language") != "ClayCode":
        violations.append("architecture language must be ClayCode")
    if "semantic_ir" not in str(arch.get("representation", "")):
        violations.append("architecture representation must be a ClayCode semantic IR projection")
    if not arch.get("architecture_id"):
        violations.append("architecture_id is required")

    source = arch.get("source_research") or {}
    if not isinstance(source.get("clay"), list) or not source.get("clay"):
        violations.append("source_research.clay must cite at least one Clay input")
    if not isinstance(source.get("claycode"), list) or not source.get("claycode"):
        violations.append("source_research.claycode must cite at least one ClayCode input")

    semantic = arch.get("semantic_contract") or {}
    if semantic.get("model_output_is_proposal_not_authority") is not True:
        violations.append("semantic contract must preserve proposal != authority")
    if semantic.get("semantic_identity_independent_of_wire_projection") is not True:
        violations.append("semantic identity must be independent of reader/wire projection")

    modules = arch.get("modules")
    if not isinstance(modules, list) or not modules:
        violations.append("modules must be a non-empty list")
    else:
        ids = []
        for i, mod in enumerate(modules):
            if not isinstance(mod, dict) or not mod.get("module_id"):
                violations.append(f"modules[{i}] missing module_id")
                continue
            ids.append(mod["module_id"])
        if len(ids) != len(set(ids)):
            violations.append("module_id values must be unique")

    transitions = arch.get("transitions")
    if not isinstance(transitions, list) or not transitions:
        violations.append("transitions must be a non-empty list")
    else:
        ids = []
        for i, op in enumerate(transitions):
            if not isinstance(op, dict) or not op.get("op_id"):
                violations.append(f"transitions[{i}] missing op_id")
                continue
            ids.append(op["op_id"])
            if op.get("proposal_class") not in ALLOWED_PROPOSAL_CLASSES:
                violations.append(f"transitions[{i}] has invalid proposal_class")
            for key in ("reads", "writes", "invariant_scope", "effects", "capability_refs"):
                if key not in op or not isinstance(op[key], list):
                    violations.append(f"transitions[{i}].{key} must be a list")
        if len(ids) != len(set(ids)):
            violations.append("op_id values must be unique")

    authority = arch.get("authority_boundary") or {}
    if authority.get("model_output_is_authority") is not False:
        violations.append("authority_boundary.model_output_is_authority must be false")
    if authority.get("external_capability_gateway_required") is not True:
        violations.append("external capability gateway must remain required")

    host = arch.get("host_kernel_boundary") or {}
    if host.get("self_authorizing") is not False:
        violations.append("host kernel must not be self-authorizing")
    if not host.get("components"):
        violations.append("host kernel boundary components must be explicit")

    if not (run_dir / MAPPING_NAME).exists():
        violations.append(f"missing required human mapping: {MAPPING_NAME}")

    return {
        "ok": not violations,
        "run_dir": str(run_dir),
        "architecture_file": str(run_dir / ARCH_NAME),
        "violations": violations,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("template")
    t.add_argument("--run-id", required=True)
    t.add_argument("--output")
    v = sub.add_parser("validate")
    v.add_argument("run_dir")
    args = ap.parse_args()

    if args.cmd == "template":
        out = template(args.run_id)
        text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            p = Path(args.output)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        print(text, end="")
        return

    out = validate(Path(args.run_dir))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if not out["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
