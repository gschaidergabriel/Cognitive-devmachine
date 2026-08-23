#!/usr/bin/env python3
"""Fail-closed static guard for canonical Clay <-> Python reference contract drift.

The canonical Clay source owns the forward contract: DB-resident profile, one explicit
pre-inference Cognitive Fabric admission, generic inference, deterministic gate/CAS commit,
and one post-turn UCF runtime-receipt finalization. The Python reference runtime/tests may
lag, but that lag must stay explicit and must never roll the canonical Clay contract back.

Effect-surface admission is syntax-bound: comments, docstrings, dead string literals, or
unwired handler names do not count as runtime support.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_EFFECTS = {
    "pipeline_profile_read": "_pipeline_profile_read",
    "pipeline_cognitive_fabric_admit": "_pipeline_cognitive_fabric_admit",
    "inference_generate": "_inference_generate",
    "pipeline_cognitive_fabric_finalize": "_pipeline_cognitive_fabric_finalize",
}
LEGACY_EFFECTS = {"profile_load", "provider_chat_json"}


def _class_node(tree: ast.AST, name: str) -> ast.ClassDef | None:
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _literal_string_set(node: ast.AST) -> set[str]:
    if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return set()
    out: set[str] = set()
    for item in node.elts:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            out.add(item.value)
    return out


def _attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return node.attr
    return None


def runtime_effect_contract(runtime: str) -> dict[str, Any]:
    """Extract effect admission from executable Python syntax, never raw substrings."""
    try:
        tree = ast.parse(runtime)
    except SyntaxError as exc:
        return {
            "syntax_ok": False,
            "syntax_error": str(exc),
            "allowed_effects": [],
            "dispatch": {},
            "handlers": [],
            "required_effect_bindings": {name: False for name in REQUIRED_EFFECTS},
            "legacy_effects_absent": False,
            "converged": False,
        }

    cls = _class_node(tree, "ProfilePipelineRuntime")
    if cls is None:
        return {
            "syntax_ok": True,
            "class_found": False,
            "allowed_effects": [],
            "dispatch": {},
            "handlers": [],
            "required_effect_bindings": {name: False for name in REQUIRED_EFFECTS},
            "legacy_effects_absent": False,
            "converged": False,
        }

    methods = {node.name: node for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    handlers = set(methods)
    allowed: set[str] = set()

    init = methods.get("__init__")
    if init is not None:
        for node in ast.walk(init):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and _attribute_name(target) == "allowed_effects":
                        allowed |= _literal_string_set(node.value)
            elif isinstance(node, ast.AnnAssign):
                target = node.target
                if isinstance(target, ast.Attribute) and _attribute_name(target) == "allowed_effects":
                    allowed |= _literal_string_set(node.value) if node.value is not None else set()

    dispatch: dict[str, str] = {}
    effect = methods.get("effect")
    if effect is not None:
        for node in ast.walk(effect):
            if isinstance(node, ast.If):
                test = node.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "kind"
                    and len(test.ops) == 1
                    and isinstance(test.ops[0], ast.Eq)
                    and len(test.comparators) == 1
                    and isinstance(test.comparators[0], ast.Constant)
                    and isinstance(test.comparators[0].value, str)
                ):
                    effect_name = test.comparators[0].value
                    called: set[str] = set()
                    for child in node.body:
                        for call in ast.walk(child):
                            if isinstance(call, ast.Call):
                                name = _attribute_name(call.func)
                                if name:
                                    called.add(name)
                    if len(called) == 1:
                        dispatch[effect_name] = next(iter(called))
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if isinstance(value, ast.Dict):
                    for key, val in zip(value.keys, value.values):
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            handler = _attribute_name(val)
                            if handler:
                                dispatch[key.value] = handler

    bindings = {
        effect_name: (
            effect_name in allowed
            and dispatch.get(effect_name) == handler_name
            and handler_name in handlers
        )
        for effect_name, handler_name in REQUIRED_EFFECTS.items()
    }
    legacy_absent = not ((allowed | set(dispatch)) & LEGACY_EFFECTS)
    converged = all(bindings.values()) and legacy_absent
    return {
        "syntax_ok": True,
        "class_found": True,
        "allowed_effects": sorted(allowed),
        "dispatch": dict(sorted(dispatch.items())),
        "handlers": sorted(handlers),
        "required_effect_bindings": bindings,
        "legacy_effects_absent": legacy_absent,
        "converged": converged,
    }


def _literal_pipeline_calls(clay: str) -> list[str]:
    executable = re.sub(r"//[^\n]*", "", clay)
    matches = re.finditer(r"\b(?:phase|effect)\(\s*\"([^\"]+)\"", executable)
    return [match.group(1) for match in matches]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-gap",
        action="store_true",
        help="Report the current convergence gap without returning failure",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve()
    root = here.parents[2]
    clay_path = here.with_name("BLOGPOST_ENTITY.clay")
    runtime_path = root / "tools" / "clay_profile_pipeline_runtime.py"
    tests_path = here.with_name("test_blogpost_entity.py")

    clay = clay_path.read_text(encoding="utf-8")
    runtime = runtime_path.read_text(encoding="utf-8")
    tests = tests_path.read_text(encoding="utf-8")

    signature = re.search(r"fn\s+run\((.*?)\)\s*->\s*Map", clay, re.S)
    run_args = []
    if signature:
        run_args = [item.strip().split(":", 1)[0].strip() for item in signature.group(1).split(",") if item.strip()]

    call_sequence = _literal_pipeline_calls(clay)
    required_order = [
        "pipeline_build_prompt",
        "pipeline_cognitive_fabric_admit",
        "inference_generate",
        "pipeline_gate",
        "pipeline_commit",
        "pipeline_cognitive_fabric_finalize",
    ]
    order_ok = all(name in call_sequence for name in required_order)
    if order_ok:
        positions = [call_sequence.index(name) for name in required_order]
        order_ok = positions == sorted(positions)

    clay_contract = {
        "run_args": run_args,
        "three_argument_runtime_boundary": run_args == ["entity_db", "source_db", "secret_file"],
        "db_resident_profile_effect": 'effect("pipeline_profile_read"' in clay,
        "cognitive_fabric_admission_effect": 'phase("pipeline_cognitive_fabric_admit"' in clay,
        "cognitive_fabric_finalization_effect": 'phase("pipeline_cognitive_fabric_finalize"' in clay,
        "cognitive_fabric_temporal_order": order_ok,
        "generic_inference_effect": 'effect("inference_generate"' in clay,
        "inference_consumes_admitted_engine": 'map_set(infer,"inference",admitted.inference)' in clay,
        "inference_consumes_admitted_context": (
            'map_set(infer,"system",admitted.system)' in clay
            and 'map_set(infer,"user",admitted.user)' in clay
        ),
        "inference_binds_pre_admission_only": (
            'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)' in clay
            and 'map_set(infer,"cognitive_fabric_admission_receipt_digest",admitted.cognitive_fabric_receipt_digest)' in clay
            and 'map_set(infer,"ucf_runtime_receipt_digest"' not in clay
            and 'map_set(infer,"cognitive_fabric_receipt_digest"' not in clay
        ),
        "gate_commit_bind_same_admission": (
            'map_set(gate_data,"cognitive_fabric_admission",admitted)' in clay
            and 'map_set(commit_data,"cognitive_fabric_admission",admitted)' in clay
        ),
        "finalizer_binds_terminal_turn": (
            'map_set(finalize_data,"admitted",admitted)' in clay
            and 'map_set(finalize_data,"generated",generated)' in clay
            and 'map_set(finalize_data,"gated",gated)' in clay
            and 'map_set(finalize_data,"committed",committed)' in clay
            and 'map_set(result,"ucf_runtime_receipt_digest",finalized.ucf_runtime_receipt_digest)' in clay
        ),
        "raw_profile_prompt_inference_bypass_absent": (
            'map_set(infer,"inference",profile.inference)' not in clay
            and 'map_set(infer,"system",prompt.system)' not in clay
            and 'map_set(infer,"user",prompt.user)' not in clay
        ),
        "old_profile_load_absent": 'effect("profile_load"' not in clay,
        "old_provider_chat_absent": 'effect("provider_chat_json"' not in clay,
        "literal_call_sequence": call_sequence,
    }

    runtime_contract = runtime_effect_contract(runtime)
    tests_contract = {
        "still_mentions_external_profile_path": "str(profile_path)" in tests,
        "still_constructs_profile_json_file": "write_profile(" in tests,
    }

    canonical_current = all(
        [
            clay_contract["three_argument_runtime_boundary"],
            clay_contract["db_resident_profile_effect"],
            clay_contract["cognitive_fabric_admission_effect"],
            clay_contract["cognitive_fabric_finalization_effect"],
            clay_contract["cognitive_fabric_temporal_order"],
            clay_contract["generic_inference_effect"],
            clay_contract["inference_consumes_admitted_engine"],
            clay_contract["inference_consumes_admitted_context"],
            clay_contract["inference_binds_pre_admission_only"],
            clay_contract["gate_commit_bind_same_admission"],
            clay_contract["finalizer_binds_terminal_turn"],
            clay_contract["raw_profile_prompt_inference_bypass_absent"],
            clay_contract["old_profile_load_absent"],
            clay_contract["old_provider_chat_absent"],
        ]
    )
    reference_converged = (
        runtime_contract["converged"]
        and not tests_contract["still_mentions_external_profile_path"]
        and not tests_contract["still_constructs_profile_json_file"]
    )

    errors: list[str] = []
    if not canonical_current:
        errors.append("CANONICAL_CLAY_CONTRACT_UNEXPECTED")
    if not reference_converged:
        errors.append("REFERENCE_RUNTIME_NOT_CONVERGED")

    report = {
        "schema": "clay-structured-contract-sync/v4",
        "canonical_clay": clay_contract,
        "python_reference_runtime": runtime_contract,
        "python_reference_tests": tests_contract,
        "canonical_current_contract_detected": canonical_current,
        "reference_converged": reference_converged,
        "policy": "Canonical Clay authority is DB-resident profile -> pre-inference Cognitive Fabric admission -> inference_generate -> deterministic gate/MiniUnifiedDB CAS commit -> post-turn UCF runtime-receipt finalization; runtime support requires executable allowed-effect + dispatch + handler binding, never comments/docstrings/dead strings.",
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and not args.allow_gap:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
