#!/usr/bin/env python3
"""Fail-closed static guard for canonical Clay <-> Python reference contract drift.

The canonical Clay source uses a DB-resident profile, a mandatory Cognitive Fabric
admission stage, and a generic `inference_generate` boundary. The Python reference
runtime/tests may lag, but that lag must be explicit and must never cause the canonical
Clay contract to be rolled backward.

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

    prompt_index = clay.find('phase("pipeline_build_prompt"')
    cognitive_index = clay.find('phase("pipeline_cognitive_fabric_admit"')
    inference_index = clay.find('effect("inference_generate"')

    clay_contract = {
        "run_args": run_args,
        "three_argument_runtime_boundary": run_args == ["entity_db", "source_db", "secret_file"],
        "db_resident_profile_effect": 'effect("pipeline_profile_read"' in clay,
        "cognitive_fabric_admission_effect": 'phase("pipeline_cognitive_fabric_admit"' in clay,
        "cognitive_fabric_before_inference": (
            prompt_index >= 0 and cognitive_index > prompt_index and inference_index > cognitive_index
        ),
        "generic_inference_effect": 'effect("inference_generate"' in clay,
        "inference_uses_admitted_profile": 'map_set(infer,"inference",admitted.inference)' in clay,
        "inference_uses_admitted_system": 'map_set(infer,"system",admitted.system)' in clay,
        "inference_uses_admitted_user": 'map_set(infer,"user",admitted.user)' in clay,
        "inference_binds_packet_digest": 'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)' in clay,
        "inference_binds_fabric_receipt_digest": 'map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)' in clay,
        "raw_profile_inference_bypass_absent": 'map_set(infer,"inference",profile.inference)' not in clay,
        "raw_prompt_system_bypass_absent": 'map_set(infer,"system",prompt.system)' not in clay,
        "raw_prompt_user_bypass_absent": 'map_set(infer,"user",prompt.user)' not in clay,
        "old_profile_load_absent": 'effect("profile_load"' not in clay,
        "old_provider_chat_absent": 'effect("provider_chat_json"' not in clay,
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
            clay_contract["cognitive_fabric_before_inference"],
            clay_contract["generic_inference_effect"],
            clay_contract["inference_uses_admitted_profile"],
            clay_contract["inference_uses_admitted_system"],
            clay_contract["inference_uses_admitted_user"],
            clay_contract["inference_binds_packet_digest"],
            clay_contract["inference_binds_fabric_receipt_digest"],
            clay_contract["raw_profile_inference_bypass_absent"],
            clay_contract["raw_prompt_system_bypass_absent"],
            clay_contract["raw_prompt_user_bypass_absent"],
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
        "schema": "clay-structured-contract-sync/v3",
        "canonical_clay": clay_contract,
        "python_reference_runtime": runtime_contract,
        "python_reference_tests": tests_contract,
        "canonical_current_contract_detected": canonical_current,
        "reference_converged": reference_converged,
        "policy": "Canonical Clay DB-resident profile -> Cognitive Fabric admission -> inference_generate semantics are forward authority; runtime support requires executable allowed-effect + dispatch + handler binding, never comments/docstrings/dead strings. Missing Cognitive Fabric runtime support stays an explicit fail-closed convergence gap.",
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and not args.allow_gap:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
