#!/usr/bin/env python3
"""Fail-closed static guard for canonical Clay <-> Python reference contract drift.

The canonical Clay source has already moved to a DB-resident profile plus generic
`inference_generate` boundary. The Python reference runtime/tests may lag, but that lag
must be explicit and must never cause the canonical Clay contract to be rolled backward.

Effect-surface admission is syntax-bound: comments, docstrings, dead string literals, or
unwired handler names do not count as runtime support. Canonical Clay call-order admission
likewise scans executable `phase("...")` / `effect("...")` calls rather than raw text.
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


def clay_literal_effect_order(source: str) -> list[str]:
    """Return executable literal first-argument calls to phase/effect, ignoring comments/strings."""
    out: list[str] = []
    i = 0
    n = len(source)
    while i < n:
        if source.startswith("//", i):
            end = source.find("\n", i + 2)
            i = n if end < 0 else end + 1
            continue
        ch = source[i]
        if ch == '"':
            i += 1
            while i < n:
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if ch.isalpha() or ch == "_":
            start = i
            i += 1
            while i < n and (source[i].isalnum() or source[i] == "_"):
                i += 1
            ident = source[start:i]
            if ident not in {"phase", "effect"}:
                continue
            j = i
            while j < n and source[j].isspace():
                j += 1
            if j >= n or source[j] != "(":
                continue
            j += 1
            while j < n and source[j].isspace():
                j += 1
            if j >= n or source[j] != '"':
                continue
            k = j + 1
            escaped = False
            while k < n:
                if escaped:
                    escaped = False
                elif source[k] == "\\":
                    escaped = True
                elif source[k] == '"':
                    break
                k += 1
            if k >= n:
                continue
            try:
                value = json.loads(source[j : k + 1])
            except json.JSONDecodeError:
                continue
            if isinstance(value, str):
                out.append(value)
            i = k + 1
            continue
        i += 1
    return out


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

    effect_order = clay_literal_effect_order(clay)
    try:
        prompt_idx = effect_order.index("pipeline_build_prompt")
        fabric_idx = effect_order.index("pipeline_cognitive_fabric_admit")
        inference_idx = effect_order.index("inference_generate")
    except ValueError:
        prompt_idx = fabric_idx = inference_idx = -1

    clay_contract = {
        "run_args": run_args,
        "three_argument_runtime_boundary": run_args == ["entity_db", "source_db", "secret_file"],
        "effect_order": effect_order,
        "db_resident_profile_effect": "pipeline_profile_read" in effect_order,
        "cognitive_fabric_admit_effect": effect_order.count("pipeline_cognitive_fabric_admit") == 1,
        "cognitive_fabric_between_prompt_and_inference": (
            prompt_idx >= 0 and fabric_idx > prompt_idx and inference_idx > fabric_idx
        ),
        "generic_inference_effect": "inference_generate" in effect_order,
        "old_profile_load_absent": "profile_load" not in effect_order,
        "old_provider_chat_absent": "provider_chat_json" not in effect_order,
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
            clay_contract["cognitive_fabric_admit_effect"],
            clay_contract["cognitive_fabric_between_prompt_and_inference"],
            clay_contract["generic_inference_effect"],
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
        "policy": "Canonical Clay DB-resident profile -> single Cognitive Fabric admission -> inference_generate semantics are forward authority; runtime support requires executable allowed-effect + dispatch + handler binding, never comments/docstrings/dead strings.",
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and not args.allow_gap:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())