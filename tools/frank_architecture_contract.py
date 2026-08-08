#!/usr/bin/env python3
"""Validate that a FRANK research run expresses its architecture in ClayCode semantic IR.

FRANK is derived from Clay, authored in ClayCode, and must incorporate current
ClayGraph associative-memory plus UnifiedDB persistence/query/transaction research.
The deterministic host authority remains outside model self-authorization.
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
ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity" / "global" / "RESEARCH_TRIGGER_REGISTRY.json"


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


def _registered_scientific_branches() -> list[str]:
    data = _load(REGISTRY)
    return [
        name for name, spec in (data.get("triggers") or {}).items()
        if (spec or {}).get("kind") in {"domain_research", "integrated_research_foundry"}
    ]


def template(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.2",
        "language": "ClayCode",
        "representation": "canonical_semantic_ir_json_projection",
        "ir_version": "OPEN",
        "architecture_id": f"frank-{run_id}",
        "run_id": run_id,
        "status": "OPEN_ARCHITECTURE_CANDIDATE",
        "source_research": {
            "clay": [],
            "claycode": [],
            "claygraph": [],
            "unifieddb": [],
            "gwt": [],
            "hyperposition": [],
            "emergenz": [],
            "frank_runtime": []
        },
        "semantic_contract": {
            "canonical_truth_is_not_activation": True,
            "model_output_is_proposal_not_authority": True,
            "semantic_identity_independent_of_wire_projection": True,
            "unknown_conflict_revoked_are_explicit": True,
            "claygraph_activation_is_derived_not_canonical_truth": True
        },
        "modules": [{
            "module_id": "REPLACE_ME",
            "kind": "organ_or_runtime_boundary",
            "state_contract_refs": [],
            "dependencies": [],
            "invariants": [],
            "claygraph_refs": []
        }],
        "transitions": [{
            "op_id": "REPLACE_ME",
            "proposal_class": "PURE_TRANSFORM",
            "reads": [],
            "writes": [],
            "invariant_scope": [],
            "effects": [],
            "capability_refs": [],
            "causal_links": [],
            "gwt_links": [],
            "claygraph_links": []
        }],
        "persistence_replay": {
            "event_identity": "REPLACE_ME",
            "replay_semantics": "REPLACE_ME",
            "recovery_boundary": "REPLACE_ME",
            "graph_projection_rebuildable": True
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

    registry_branches = _registered_scientific_branches()
    registered = list(inter.get("registry_scientific_branches") or [])
    if set(registered) != set(registry_branches) or len(registered) != len(registry_branches):
        violations.append(
            f"INTERCONNECT_MANIFEST scientific branches must exactly match current registry: "
            f"manifest={registered!r} registry={registry_branches!r}"
        )

    priority = inter.get("branch_priority") or []
    expected_prefix = ["clay", "claycode", "claygraph", "unifieddb"]
    if priority[:4] != expected_prefix:
        violations.append(
            "INTERCONNECT_MANIFEST must prioritize clay, claycode, claygraph, then unifieddb for FRANK"
        )
    if set(priority) != set(registry_branches) or len(priority) != len(registry_branches):
        violations.append("FRANK branch_priority must contain every current registered scientific branch exactly once")

    special = inter.get("special_rules") or {}
    if special.get("frank_requires_latest_clay_architecture_as_primary_foundation") is not True:
        violations.append("FRANK interconnect must require latest Clay architecture foundation")
    if special.get("frank_requires_deep_claycode_architecture_input") is not True:
        violations.append("FRANK interconnect must require deep ClayCode architecture input")
    if special.get("frank_requires_deep_claygraph_substrate_input") is not True:
        violations.append("FRANK interconnect must require deep ClayGraph substrate input")
    if special.get("frank_requires_deep_unifieddb_persistence_input") is not True:
        violations.append("FRANK interconnect must require deep UnifiedDB persistence/query input")
    if special.get("frank_architecture_source_language") != "ClayCode semantic IR":
        violations.append("FRANK architecture source language must be ClayCode semantic IR")

    if arch.get("language") != "ClayCode":
        violations.append("architecture language must be ClayCode")
    if "semantic_ir" not in str(arch.get("representation", "")):
        violations.append("architecture representation must be a ClayCode semantic IR projection")
    if not arch.get("architecture_id"):
        violations.append("architecture_id is required")

    source = arch.get("source_research") or {}
    for required in ("clay", "claycode", "claygraph", "unifieddb"):
        if not isinstance(source.get(required), list) or not source.get(required):
            violations.append(f"source_research.{required} must cite at least one {required} input")

    semantic = arch.get("semantic_contract") or {}
    if semantic.get("model_output_is_proposal_not_authority") is not True:
        violations.append("semantic contract must preserve proposal != authority")
    if semantic.get("semantic_identity_independent_of_wire_projection") is not True:
        violations.append("semantic identity must be independent of reader/wire projection")
    if semantic.get("canonical_truth_is_not_activation") is not True:
        violations.append("canonical truth must remain distinct from activation")
    if semantic.get("claygraph_activation_is_derived_not_canonical_truth") is not True:
        violations.append("ClayGraph activation must be explicitly derived, not canonical truth")

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

    replay = arch.get("persistence_replay") or {}
    if replay.get("graph_projection_rebuildable") is not True:
        violations.append("ClayGraph projection must be explicitly rebuildable from authoritative state until separately promoted")

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
        "registry_scientific_branches": registry_branches,
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
        text = json.dumps(template(args.run_id), ensure_ascii=False, indent=2) + "\n"
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
