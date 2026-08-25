#!/usr/bin/env python3
"""Execute and validate the pure ClayCode authority kernel for the current cognitive protocol.

This validator uses the repository's existing ClayCode BASE compiler/interpreter. Passing
proves only executable pure decision semantics at the declared source identity. It does not
prove model runtime, DB runtime, Claude Code runtime, EffectGate execution, J-Space causality,
full HCU, whole EntityOS, or training acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import claycode_base_compiler as base

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KERNEL = ROOT / "research_entity/global/CLAYCODE_COGNITIVE_AUTHORITY_KERNEL_v1.clay"
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
DEFAULT_CENSUS = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
DEFAULT_BOUNDARY = ROOT / "research_entity/global/DB_VS_SIMULATION_BOUNDARY_v1.json"

EXPECTED_FUNCTIONS = {
    "valid_process_id": (["Int"], "Bool"),
    "valid_grid_n": (["Int"], "Bool"),
    "generation_matches": (["Int", "Int"], "Bool"),
    "semantic_process_identity": (["Int", "Int"], "Int"),
    "state_class_valid": (["Int"], "Bool"),
    "state_class_is_canonical": (["Int"], "Bool"),
    "workspace_state_can_mint_truth": (["Int"], "Bool"),
    "local_cognition_can_mint_truth": (["Int"], "Bool"),
    "direct_cognitive_db_commit_allowed": (["Int"], "Bool"),
    "db_write_proposal_process": (["Int"], "Bool"),
    "effect_proposal_process": (["Int"], "Bool"),
    "real_effect_authority_process": (["Int"], "Bool"),
    "direct_cognitive_effect_allowed": (["Int"], "Bool"),
    "unknown_effect_blind_replay_allowed": (["Int"], "Bool"),
    "workspace_process": (["Int"], "Bool"),
    "claude_bridge_process": (["Int"], "Bool"),
    "claude_direct_canonical_write_allowed": (["Int"], "Bool"),
    "jspace_direct_truth_allowed": (["Int"], "Bool"),
}

ROLE_BINDINGS = {
    "ZECP10": "GLOBAL_WORKSPACE_COMPETITION_BROADCAST_REENTRY",
    "ZECP13": "CLAUDE_CODE_HANDOFF",
    "ZECP14": "CLAUDE_CODE_RESULT_RECONCILIATION",
    "ZECP15": "MEMORY_UPDATE_PROPOSAL",
    "ZECP16": "TOOL_EFFECT_PROPOSAL",
    "ZECP17": "EFFECTGATE_JOURNAL_COMMIT",
}


class KernelValidationError(ValueError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise KernelValidationError(code)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _signature_map(ir: dict[str, Any]) -> dict[str, tuple[list[str], str]]:
    return {
        fn["name"]: ([p["type"] for p in fn["params"]], fn["return"])
        for fn in ir["functions"]
    }


def _eval(ir: dict[str, Any], name: str, args: list[Any]) -> Any:
    return base.eval_function(ir, name, args)


def validate(
    source: str,
    grammar: str,
    census: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, Any]:
    _require(census.get("schema") == "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1", "CENSUS_SCHEMA_DRIFT")
    _require(boundary.get("schema") == "DB_VS_SIMULATION_BOUNDARY/v1", "DB_BOUNDARY_SCHEMA_DRIFT")
    _require(boundary.get("authority", {}).get("grid_law") == "VARIABLE_N_RUNTIME_PARAMETER", "VARIABLE_N_BOUNDARY_REQUIRED")
    _require(set(boundary.get("state_classes", {})) == {"S0", "S1", "S2"}, "S0_S1_S2_BOUNDARY_REQUIRED")

    census_roles = {
        item.get("id"): item.get("name")
        for item in census.get("processes", [])
        if isinstance(item, dict)
    }
    for process_id, expected_name in ROLE_BINDINGS.items():
        _require(census_roles.get(process_id) == expected_name, f"CENSUS_ROLE_DRIFT:{process_id}")

    built = base.build(source, grammar)
    ir = built["ir"]
    _require(_signature_map(ir) == EXPECTED_FUNCTIONS, "KERNEL_FUNCTION_SIGNATURE_DRIFT")

    for process in range(1, 21):
        _require(_eval(ir, "valid_process_id", [process]) is True, f"VALID_PROCESS_REJECTED:{process}")
    for process in (0, -1, 21, 999):
        _require(_eval(ir, "valid_process_id", [process]) is False, f"INVALID_PROCESS_ACCEPTED:{process}")

    for n in (1, 2, 10, 20, 64, 600):
        _require(_eval(ir, "valid_grid_n", [n]) is True, f"VALID_GRID_N_REJECTED:{n}")
    for n in (0, -1, -20):
        _require(_eval(ir, "valid_grid_n", [n]) is False, f"INVALID_GRID_N_ACCEPTED:{n}")

    # Process semantics are independent of runtime grid size N.
    for process in range(1, 21):
        observed = {
            _eval(ir, "semantic_process_identity", [process, n])
            for n in (1, 2, 10, 20, 64, 600)
        }
        _require(observed == {process}, f"N_CHANGED_PROCESS_SEMANTICS:{process}:{sorted(observed)}")

    _require(_eval(ir, "generation_matches", [7, 7]) is True, "MATCHING_GENERATION_REJECTED")
    _require(_eval(ir, "generation_matches", [7, 6]) is False, "STALE_GENERATION_ACCEPTED")

    for state_class in (0, 1, 2):
        _require(_eval(ir, "state_class_valid", [state_class]) is True, f"STATE_CLASS_REJECTED:{state_class}")
    for state_class in (-1, 3, 99):
        _require(_eval(ir, "state_class_valid", [state_class]) is False, f"UNKNOWN_STATE_CLASS_ACCEPTED:{state_class}")
    _require(_eval(ir, "state_class_is_canonical", [0]) is True, "S0_NOT_CANONICAL")
    _require(_eval(ir, "state_class_is_canonical", [1]) is False, "S1_PROMOTED_TO_CANONICAL")
    _require(_eval(ir, "state_class_is_canonical", [2]) is False, "S2_PROMOTED_TO_CANONICAL")

    for state_class in (0, 1, 2):
        _require(_eval(ir, "workspace_state_can_mint_truth", [state_class]) is False, "WORKSPACE_MINTED_TRUTH")
        _require(_eval(ir, "local_cognition_can_mint_truth", [state_class]) is False, "LOCAL_COGNITION_MINTED_TRUTH")

    for process in range(1, 21):
        _require(_eval(ir, "direct_cognitive_db_commit_allowed", [process]) is False, f"DIRECT_DB_COMMIT_ALLOWED:{process}")
        _require(_eval(ir, "direct_cognitive_effect_allowed", [process]) is False, f"DIRECT_COGNITIVE_EFFECT_ALLOWED:{process}")
        _require(_eval(ir, "claude_direct_canonical_write_allowed", [process]) is False, f"CLAUDE_DIRECT_CANONICAL_WRITE_ALLOWED:{process}")
        _require(_eval(ir, "jspace_direct_truth_allowed", [process]) is False, f"JSPACE_DIRECT_TRUTH_ALLOWED:{process}")

    for outcome_class in (-1, 0, 1, 2, 3):
        _require(_eval(ir, "unknown_effect_blind_replay_allowed", [outcome_class]) is False, "UNKNOWN_EFFECT_BLIND_REPLAY_ALLOWED")

    for fn_name, allowed in (
        ("workspace_process", {10}),
        ("claude_bridge_process", {13, 14}),
        ("db_write_proposal_process", {15}),
        ("effect_proposal_process", {16}),
        ("real_effect_authority_process", {17}),
    ):
        observed = {p for p in range(1, 21) if _eval(ir, fn_name, [p]) is True}
        _require(observed == allowed, f"PROCESS_ROLE_BINDING_DRIFT:{fn_name}:{sorted(observed)}")

    c11 = base.lower_c(ir, "semantic_process_identity")
    _require("ccf_semantic_process_identity" in c11, "C11_LOWERING_MISSING_ENTRY")
    _require("int main(" in c11, "C11_LOWERING_MISSING_MAIN")

    return {
        "ok": True,
        "schema": "CLAYCODE_COGNITIVE_AUTHORITY_KERNEL/v1",
        "compiler_ir_schema": ir.get("schema"),
        "function_count": len(ir["functions"]),
        "source_sha256": _sha256(source),
        "grammar_sha256": _sha256(grammar),
        "semantic_hash": built["semantic_hash"],
        "n_discriminator_values": [1, 2, 10, 20, 64, 600],
        "process_count": 20,
        "c11_lowering": "PASS",
        "credit_scope": "EXECUTABLE_PURE_CLAYCODE_AUTHORITY_KERNEL_COMPONENT_ONLY",
        "model_runtime_credit": 0,
        "db_runtime_credit": 0,
        "claude_runtime_credit": 0,
        "jspace_causal_credit": 0,
        "full_hcu_credit": 0,
        "whole_entityos_credit": 0,
        "training_credit": 0,
        "next_gate": "GLOBAL_WORKSPACE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel", type=Path, default=DEFAULT_KERNEL)
    parser.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    parser.add_argument("--census", type=Path, default=DEFAULT_CENSUS)
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    args = parser.parse_args()
    try:
        result = validate(
            args.kernel.read_text(encoding="utf-8"),
            args.grammar.read_text(encoding="utf-8"),
            _load_json(args.census),
            _load_json(args.boundary),
        )
    except (KernelValidationError, base.CompileError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
