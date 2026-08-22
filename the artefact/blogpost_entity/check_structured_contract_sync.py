#!/usr/bin/env python3
"""Fail-closed static guard for canonical Clay <-> Python reference contract drift.

The canonical Clay source has already moved to a DB-resident profile plus generic
`inference_generate` boundary. The Python reference runtime/tests may lag, but that lag
must be explicit and must never cause the canonical Clay contract to be rolled backward.

Effect parity is derived from executable structure, not substring presence. Literal names
in comments, docstrings, dead strings or unused dictionaries cannot satisfy the gate.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


def _literal_string_set(node: ast.AST) -> set[str] | None:
    if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return None
    values: set[str] = set()
    for item in node.elts:
        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
            return None
        values.add(item.value)
    return values


def _called_dispatch_names(effect_fn: ast.AST) -> set[str]:
    """Return local mapping variables actually called as mapping[kind](...)."""
    names: set[str] = set()
    for node in ast.walk(effect_fn):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Subscript):
            continue
        sub = node.func
        if not isinstance(sub.value, ast.Name):
            continue
        slice_node = sub.slice
        if isinstance(slice_node, ast.Name) and slice_node.id == "kind":
            names.add(sub.value.id)
    return names


def extract_runtime_effect_contract(runtime: str) -> tuple[set[str], set[str]]:
    """Return literal allowed effects and effect names actually dispatched by effect()."""
    tree = ast.parse(runtime)
    allowed: set[str] = set()
    dispatched: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and target.attr == "allowed_effects"
            ):
                values = _literal_string_set(node.value)
                if values is not None:
                    allowed = values

    effect_fn = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "effect"
        ),
        None,
    )
    if effect_fn is None:
        return allowed, dispatched

    # Direct branch dispatch: if kind == "pipeline_init": ...
    for node in ast.walk(effect_fn):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
            continue
        if not isinstance(node.ops[0], ast.Eq):
            continue
        if not isinstance(node.left, ast.Name) or node.left.id != "kind":
            continue
        other = node.comparators[0]
        if isinstance(other, ast.Constant) and isinstance(other.value, str):
            dispatched.add(other.value)

    # Literal dispatch map: dispatch = {"pipeline_init": self._pipeline_init, ...};
    # dispatch[kind](payload). Only mappings actually called by `kind` count.
    called_maps = _called_dispatch_names(effect_fn)
    for node in ast.walk(effect_fn):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if not any(name in called_maps for name in targets):
            continue
        entries: set[str] = set()
        valid = True
        for key, value in zip(node.value.keys, node.value.values):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                valid = False
                break
            if not (
                isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name)
                and value.value.id == "self"
            ):
                valid = False
                break
            entries.add(key.value)
        if valid:
            dispatched.update(entries)

    return allowed, dispatched


def extract_clay_effect_surface(clay: str) -> set[str]:
    """Extract literal phase/effect responsibility names used by canonical Clay."""
    return set(re.findall(r'\b(?:effect|phase)\(\s*"([^"]+)"', clay))


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
    parity_path = here / "native" / "NATIVE_PROFILE_V2_PARITY_CONTRACT.json"

    clay = clay_path.read_text(encoding="utf-8")
    runtime = runtime_path.read_text(encoding="utf-8")
    tests = tests_path.read_text(encoding="utf-8")
    parity = json.loads(parity_path.read_text(encoding="utf-8"))

    required_effects = set(parity["required_reference_effect_surface"])
    legacy_effects = set(parity["legacy_reference_effects_to_deauthorize"])
    clay_effects = extract_clay_effect_surface(clay)
    runtime_allowed, runtime_dispatched = extract_runtime_effect_contract(runtime)

    signature = re.search(r"fn\s+run\((.*?)\)\s*->\s*Map", clay, re.S)
    run_args = []
    if signature:
        run_args = [
            item.strip().split(":", 1)[0].strip()
            for item in signature.group(1).split(",")
            if item.strip()
        ]

    clay_contract = {
        "run_args": run_args,
        "three_argument_runtime_boundary": run_args == ["entity_db", "source_db", "secret_file"],
        "effect_surface": sorted(clay_effects),
        "effect_surface_matches_parity_contract": clay_effects == required_effects,
        "legacy_effects_absent": not bool(clay_effects & legacy_effects),
    }

    runtime_contract = {
        "allowed_effects": sorted(runtime_allowed),
        "dispatched_effects": sorted(runtime_dispatched),
        "required_effects": sorted(required_effects),
        "legacy_effects": sorted(legacy_effects),
        "allowed_surface_exact": runtime_allowed == required_effects,
        "dispatch_surface_exact": runtime_dispatched == required_effects,
        "legacy_allowed_absent": not bool(runtime_allowed & legacy_effects),
        "legacy_dispatch_absent": not bool(runtime_dispatched & legacy_effects),
    }

    tests_contract = {
        "still_mentions_external_profile_path": "str(profile_path)" in tests,
        "still_constructs_profile_json_file": "write_profile(" in tests,
    }

    canonical_current = all(
        [
            clay_contract["three_argument_runtime_boundary"],
            clay_contract["effect_surface_matches_parity_contract"],
            clay_contract["legacy_effects_absent"],
        ]
    )
    reference_converged = (
        runtime_contract["allowed_surface_exact"]
        and runtime_contract["dispatch_surface_exact"]
        and runtime_contract["legacy_allowed_absent"]
        and runtime_contract["legacy_dispatch_absent"]
        and not tests_contract["still_mentions_external_profile_path"]
        and not tests_contract["still_constructs_profile_json_file"]
    )

    missing = sorted(required_effects - runtime_allowed)
    stale = sorted(legacy_effects & runtime_allowed)
    gap = parity["reference_runtime_effect_surface"]
    gap_consistent = (
        gap.get("status") == ("PARITY" if reference_converged else "FAIL_CLOSED_MISMATCH")
        and sorted(gap.get("missing_current_effects", [])) == missing
        and sorted(gap.get("stale_current_effects", [])) == stale
    )

    errors: list[str] = []
    if not canonical_current:
        errors.append("CANONICAL_CLAY_CONTRACT_UNEXPECTED")
    if not runtime_allowed:
        errors.append("REFERENCE_ALLOWED_EFFECTS_NOT_LITERAL_OR_MISSING")
    if not runtime_dispatched:
        errors.append("REFERENCE_EFFECT_DISPATCH_NOT_DETECTED")
    if not reference_converged:
        errors.append("REFERENCE_RUNTIME_NOT_CONVERGED")
    if not gap_consistent:
        errors.append("REFERENCE_PARITY_CONTRACT_STALE")

    report = {
        "schema": "clay-structured-contract-sync/v2",
        "parity_contract": str(parity_path.relative_to(root)),
        "canonical_clay": clay_contract,
        "python_reference_runtime": runtime_contract,
        "python_reference_tests": tests_contract,
        "canonical_current_contract_detected": canonical_current,
        "reference_converged": reference_converged,
        "reference_parity_contract_consistent": gap_consistent,
        "policy": "Canonical Clay DB-resident profile + inference_generate semantics are forward authority; runtime parity requires executable registry+dispatch equality, not textual name presence.",
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and not args.allow_gap:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
