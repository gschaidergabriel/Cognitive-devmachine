#!/usr/bin/env python3
"""Fail-closed static guard for canonical Clay <-> Python reference contract drift.

Canonical temporal law:
  FETCH -> pre-inference Cognitive Fabric admission -> inference_generate
        -> post-inference UCF runtime-cycle validation -> gate -> commit.

The pre-inference envelope binds ZERO_WORKSPACE_CAPSULE/v1 + ZERO_INFERENCE_PACKET/v1.
UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1 is post-inference evidence and MUST NOT be
pretended to exist before inference executes.

Effect-surface admission is syntax-bound: comments/docstrings/dead strings do not count.
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
    "pipeline_cognitive_fabric_validate": "_pipeline_cognitive_fabric_validate",
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
    return {
        item.value
        for item in node.elts
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    }


def _attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return node.attr
    return None


def runtime_effect_contract(runtime: str) -> dict[str, Any]:
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
            value = None
            targets: list[ast.AST] = []
            if isinstance(node, ast.Assign):
                value = node.value
                targets = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                value = node.value
                targets = [node.target]
            if value is not None and any(
                isinstance(target, ast.Attribute) and _attribute_name(target) == "allowed_effects"
                for target in targets
            ):
                allowed |= _literal_string_set(value)
    dispatch: dict[str, str] = {}
    effect = methods.get("effect")
    if effect is not None:
        for node in ast.walk(effect):
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Dict):
                for key, val in zip(node.value.keys, node.value.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        handler = _attribute_name(val)
                        if handler:
                            dispatch[key.value] = handler
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
                    called: set[str] = set()
                    for child in node.body:
                        for call in ast.walk(child):
                            if isinstance(call, ast.Call):
                                name = _attribute_name(call.func)
                                if name:
                                    called.add(name)
                    if len(called) == 1:
                        dispatch[test.comparators[0].value] = next(iter(called))
    bindings = {
        effect_name: effect_name in allowed and dispatch.get(effect_name) == handler and handler in handlers
        for effect_name, handler in REQUIRED_EFFECTS.items()
    }
    legacy_absent = not ((allowed | set(dispatch)) & LEGACY_EFFECTS)
    return {
        "syntax_ok": True,
        "class_found": True,
        "allowed_effects": sorted(allowed),
        "dispatch": dict(sorted(dispatch.items())),
        "handlers": sorted(handlers),
        "required_effect_bindings": bindings,
        "legacy_effects_absent": legacy_absent,
        "converged": all(bindings.values()) and legacy_absent,
    }


def _literal_calls(clay: str) -> list[str]:
    executable = re.sub(r"//[^\n]*", "", clay)
    return [m.group(1) for m in re.finditer(r"\b(?:phase|effect)\(\s*\"([^\"]+)\"", executable)]


def canonical_contract(clay: str) -> dict[str, Any]:
    signature = re.search(r"fn\s+run\((.*?)\)\s*->\s*Map", clay, re.S)
    run_args = [] if signature is None else [
        item.strip().split(":", 1)[0].strip()
        for item in signature.group(1).split(",") if item.strip()
    ]
    calls = _literal_calls(clay)
    temporal = [
        "pipeline_build_prompt",
        "pipeline_cognitive_fabric_admit",
        "inference_generate",
        "pipeline_cognitive_fabric_validate",
        "pipeline_gate",
        "pipeline_commit",
    ]
    temporal_ok = all(name in calls for name in temporal)
    if temporal_ok:
        positions = [calls.index(name) for name in temporal]
        temporal_ok = positions == sorted(positions)
    return {
        "run_args": run_args,
        "three_argument_runtime_boundary": run_args == ["entity_db", "source_db", "secret_file"],
        "db_resident_profile_effect": 'effect("pipeline_profile_read"' in clay,
        "pre_inference_admission": 'phase("pipeline_cognitive_fabric_admit"' in clay,
        "generic_inference_effect": 'effect("inference_generate"' in clay,
        "post_inference_validation": 'phase("pipeline_cognitive_fabric_validate"' in clay,
        "temporal_order_ok": temporal_ok,
        "admitted_inference_inputs": all(token in clay for token in [
            'map_set(infer,"inference",admitted.inference)',
            'map_set(infer,"system",admitted.system)',
            'map_set(infer,"user",admitted.user)',
            'map_set(infer,"zero_workspace_capsule_digest",admitted.zero_workspace_capsule_digest)',
            'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)',
        ]),
        "post_receipt_only_after_inference": (
            'map_set(result,"cognitive_fabric_receipt_digest",cognitive_cycle.cognitive_fabric_receipt_digest)' in clay
            and 'map_set(infer,"cognitive_fabric_receipt_digest"' not in clay
            and 'admitted.cognitive_fabric_receipt_digest' not in clay
        ),
        "raw_profile_prompt_bypass_absent": all(token not in clay for token in [
            'map_set(infer,"inference",profile.inference)',
            'map_set(infer,"system",prompt.system)',
            'map_set(infer,"user",prompt.user)',
        ]),
        "legacy_effects_absent": 'effect("profile_load"' not in clay and 'effect("provider_chat_json"' not in clay,
        "literal_call_sequence": calls,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-gap", action="store_true")
    args = parser.parse_args()
    here = Path(__file__).resolve()
    root = here.parents[2]
    clay = here.with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")
    runtime = (root / "tools" / "clay_profile_pipeline_runtime.py").read_text(encoding="utf-8")
    tests = here.with_name("test_blogpost_entity.py").read_text(encoding="utf-8")
    clay_contract = canonical_contract(clay)
    runtime_contract = runtime_effect_contract(runtime)
    tests_contract = {
        "still_mentions_external_profile_path": "str(profile_path)" in tests,
        "still_constructs_profile_json_file": "write_profile(" in tests,
    }
    canonical_current = all(value for key, value in clay_contract.items() if key not in {"run_args", "literal_call_sequence"})
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
        "policy": "Pre-inference Capsule+InferencePacket admission and post-inference UCF runtime receipt validation are distinct causal phases; runtime support requires executable bindings for both.",
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if (not errors or args.allow_gap) else 2


if __name__ == "__main__":
    raise SystemExit(main())
