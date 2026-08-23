#!/usr/bin/env python3
"""Fail-closed static guard for canonical Clay <-> Python reference contract drift.

The canonical Clay source owns the forward contract: DB-resident profile, one bounded
MiniUnifiedDB turn-selector input, one explicit pre-inference Cognitive Fabric admission,
generic inference, deterministic gate/CAS commit, and one post-turn UCF runtime-receipt
finalization. The Python reference runtime/tests may lag, but that lag must stay explicit
and must never roll the canonical Clay contract back.

Effect-surface admission is syntax-bound: comments, docstrings, dead string literals, or
unwired handler names do not count as runtime support. Runtime convergence additionally
requires a bounded downstream identity floor: inference must actually consume the admitted
InferencePacket + pre-inference admission identities, and finalization must consume the
same admitted/candidate/gate/commit terminal ancestry and expose a distinct final UCF digest.
This is source/mechanism evidence only, never runtime proof.
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
INFERENCE_REQUIRED_KEYS = {
    "inference_packet_digest",
    "cognitive_fabric_admission_receipt_digest",
}
FINALIZER_REQUIRED_INPUT_KEYS = {"admitted", "generated", "gated", "committed"}
FINALIZER_REQUIRED_OUTPUT_KEYS = {"ucf_runtime_receipt_digest"}
FINALIZER_FORBIDDEN_SELF_CALLS = {"_db", "_pipeline_commit", "_inference_generate", "effect"}


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


def _self_calls(method: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(method):
        if isinstance(node, ast.Call):
            name = _attribute_name(node.func)
            if name:
                out.add(name)
    return out


def _reachable_method_nodes(methods: dict[str, ast.AST], start: str) -> dict[str, ast.AST]:
    """Follow executable self.method(...) calls so helper decomposition still counts."""
    reachable: dict[str, ast.AST] = {}
    pending = [start]
    while pending:
        name = pending.pop()
        if name in reachable or name not in methods:
            continue
        method = methods[name]
        reachable[name] = method
        pending.extend(sorted(_self_calls(method) & set(methods)))
    return reachable


def _accessed_mapping_keys(nodes: list[ast.AST]) -> set[str]:
    """Collect literal mapping keys that executable code reads via [] or .get(...)."""
    out: set[str] = set()
    for root in nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Subscript):
                value = node.slice
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    out.add(value.value)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "get" and node.args:
                    first = node.args[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        out.add(first.value)
    return out


def _dict_literal_keys(nodes: list[ast.AST]) -> set[str]:
    out: set[str] = set()
    for root in nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        out.add(key.value)
    return out


def downstream_identity_contract(methods: dict[str, ast.AST]) -> dict[str, Any]:
    """Bounded source floor for preserving UCF ancestry after pre-inference admission.

    This intentionally does not prove semantic correctness. It prevents a future runtime
    from receiving convergence credit when handler names are wired but inference drops the
    admitted packet/receipt identities, or finalization ignores terminal ancestry / mints a
    final digest without structurally consuming the same turn outcome.
    """
    inference = _reachable_method_nodes(methods, "_inference_generate")
    finalizer = _reachable_method_nodes(methods, "_pipeline_cognitive_fabric_finalize")
    inference_nodes = list(inference.values())
    finalizer_nodes = list(finalizer.values())

    inference_reads = _accessed_mapping_keys(inference_nodes)
    finalizer_reads = _accessed_mapping_keys(finalizer_nodes)
    finalizer_outputs = _dict_literal_keys(finalizer_nodes)
    finalizer_self_calls = (
        set().union(*(_self_calls(node) for node in finalizer_nodes)) if finalizer_nodes else set()
    )
    forbidden = sorted(finalizer_self_calls & FINALIZER_FORBIDDEN_SELF_CALLS)

    inference_identity_bound = INFERENCE_REQUIRED_KEYS.issubset(inference_reads)
    finalizer_terminal_ancestry_bound = FINALIZER_REQUIRED_INPUT_KEYS.issubset(finalizer_reads)
    finalizer_exposes_distinct_digest = FINALIZER_REQUIRED_OUTPUT_KEYS.issubset(finalizer_outputs)
    semantic_floor = all(
        [
            inference_identity_bound,
            finalizer_terminal_ancestry_bound,
            finalizer_exposes_distinct_digest,
            not forbidden,
        ]
    )
    return {
        "inference_reachable_methods": sorted(inference),
        "inference_accessed_keys": sorted(INFERENCE_REQUIRED_KEYS & inference_reads),
        "inference_identity_bound": inference_identity_bound,
        "finalizer_reachable_methods": sorted(finalizer),
        "finalizer_accessed_inputs": sorted(FINALIZER_REQUIRED_INPUT_KEYS & finalizer_reads),
        "finalizer_output_keys": sorted(FINALIZER_REQUIRED_OUTPUT_KEYS & finalizer_outputs),
        "finalizer_terminal_ancestry_bound": finalizer_terminal_ancestry_bound,
        "finalizer_exposes_distinct_digest": finalizer_exposes_distinct_digest,
        "finalizer_forbidden_self_calls": forbidden,
        "semantic_floor": semantic_floor,
    }


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
            "downstream_identity": downstream_identity_contract({}),
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
            "downstream_identity": downstream_identity_contract({}),
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
    downstream = downstream_identity_contract(methods)
    legacy_absent = not ((allowed | set(dispatch)) & LEGACY_EFFECTS)
    converged = all(bindings.values()) and downstream["semantic_floor"] and legacy_absent
    return {
        "syntax_ok": True,
        "class_found": True,
        "allowed_effects": sorted(allowed),
        "dispatch": dict(sorted(dispatch.items())),
        "handlers": sorted(handlers),
        "required_effect_bindings": bindings,
        "downstream_identity": downstream,
        "legacy_effects_absent": legacy_absent,
        "converged": converged,
    }


def _literal_pipeline_calls(clay: str) -> list[str]:
    executable = re.sub(r"//[^\n]*", "", clay)
    matches = re.finditer(r"\b(?:phase|effect)\(\s*\"([^\"]+)\"", executable)
    return [match.group(1) for match in matches]


def clay_contract(clay: str) -> dict[str, Any]:
    signature = re.search(r"fn\s+run\((.*?)\)\s*->\s*Map", clay, re.S)
    run_args: list[str] = []
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

    return {
        "run_args": run_args,
        "cognition_invocation_runtime_boundary": run_args
        == ["entity_db", "source_db", "secret_file", "cognition_invocation"],
        "cognition_invocation_passed_only_to_admission": (
            'map_set(cognition_data,"invocation",cognition_invocation)' in clay
            and 'map_set(infer,"invocation",cognition_invocation)' not in clay
            and 'map_set(gate_data,"invocation",cognition_invocation)' not in clay
            and 'map_set(commit_data,"invocation",cognition_invocation)' not in clay
            and 'map_set(finalize_data,"invocation",cognition_invocation)' not in clay
        ),
        "caller_cognition_authority_absent": (
            'map_set(cognition_data,"zero_identity_digest",' not in clay
            and 'map_set(cognition_data,"grf_digest",' not in clay
            and 'map_set(cognition_data,"workspace_digest",' not in clay
            and 'map_set(cognition_data,"local_model_digest",' not in clay
            and 'map_set(cognition_data,"jspace_mode",' not in clay
        ),
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

    canonical = clay_contract(clay)
    runtime_contract = runtime_effect_contract(runtime)
    tests_contract = {
        "still_mentions_external_profile_path": "str(profile_path)" in tests,
        "still_constructs_profile_json_file": "write_profile(" in tests,
    }

    canonical_current = all(
        [
            canonical["cognition_invocation_runtime_boundary"],
            canonical["cognition_invocation_passed_only_to_admission"],
            canonical["caller_cognition_authority_absent"],
            canonical["db_resident_profile_effect"],
            canonical["cognitive_fabric_admission_effect"],
            canonical["cognitive_fabric_finalization_effect"],
            canonical["cognitive_fabric_temporal_order"],
            canonical["generic_inference_effect"],
            canonical["inference_consumes_admitted_engine"],
            canonical["inference_consumes_admitted_context"],
            canonical["inference_binds_pre_admission_only"],
            canonical["gate_commit_bind_same_admission"],
            canonical["finalizer_binds_terminal_turn"],
            canonical["raw_profile_prompt_inference_bypass_absent"],
            canonical["old_profile_load_absent"],
            canonical["old_provider_chat_absent"],
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
        "schema": "clay-structured-contract-sync/v5",
        "canonical_clay": canonical,
        "python_reference_runtime": runtime_contract,
        "python_reference_tests": tests_contract,
        "canonical_current_contract_detected": canonical_current,
        "reference_converged": reference_converged,
        "policy": "Canonical Clay authority is bounded MINI_COGNITIVE_INVOCATION/v1 selector -> DB-resident profile/state -> pre-inference Cognitive Fabric admission resolving only already-bound MiniUnifiedDB material -> exact admission identity consumed by inference -> deterministic gate/MiniUnifiedDB CAS commit -> post-turn UCF runtime-receipt finalization over the same terminal ancestry; runtime support requires executable effect binding plus the bounded downstream identity floor, never names/comments/dead strings alone.",
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and not args.allow_gap:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
