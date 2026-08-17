#!/usr/bin/env python3
"""Fresh-current-main CC-WP-03 integration/falsifier gate.

Consumes the selected V18 FrontendArtifact through the existing receipt-bound no-reparse
bridge on current main, inventories the exact G9 V3 + Dialect V3 residual surface, and
classifies mixed flat rule/invariant binding as explicit unresolved state rather than
inventing precedence. This test grants no execution/effect/truth authority and does not
promote WP03 by itself.
"""
from __future__ import annotations

import copy
import json
import platform
import resource
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_wp03_frontend_artifact_bridge as bridge
import claycode_base_typed_ir_v18_bridge as identity_bridge

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
SURFACE = "BASE_D_V18_REWARD_RELATIONS"
RULE_KINDS = {"rule_decl", "invariant_decl"}
METADATA_KINDS = {
    "module_decl", "version_decl", "status_decl", "parent_decl",
    "import_decl", "dialect_decl", "tensor_decl",
}


def children(node: Any) -> list[Any]:
    if not isinstance(node, dict):
        return []
    value = node.get("children", [])
    if not isinstance(value, list):
        raise AssertionError("canonical AST children must be a list")
    return value


def token_value(node: Any) -> str | None:
    if isinstance(node, dict) and "token" in node and "value" in node:
        return str(node["value"])
    return None


def token_values(node: Any) -> list[str]:
    out: list[str] = []
    stack = [node]
    while stack:
        cur = stack.pop()
        value = token_value(cur)
        if value is not None:
            out.append(value)
        else:
            stack.extend(reversed(children(cur)))
    return out


def relation_name(node: Any) -> str:
    vals = [x for x in token_values(node) if x not in {"(", ")", "[", "]", "{", "}", ","}]
    if len(vals) != 1:
        raise AssertionError(f"operator/relation wrapper expected one semantic token: {vals!r}")
    return vals[0]


def direct_binding_signatures(expr: dict[str, Any]) -> list[tuple[str, str, bool]]:
    parts = children(expr)
    out: list[tuple[str, str, bool]] = []
    for i, part in enumerate(parts):
        if not isinstance(part, dict):
            continue
        kind = part.get("kind")
        if kind not in {"operator", "infix_relop"}:
            continue
        explicit_equals_marker = (
            kind == "infix_relop"
            and i + 1 < len(parts)
            and token_value(parts[i + 1]) == "="
        )
        out.append((kind, relation_name(part), explicit_equals_marker))
    return out


def has_ambiguous_flat_binding(node: Any) -> bool:
    if isinstance(node, dict):
        if node.get("kind") == "expr":
            sigs = direct_binding_signatures(node)
            if len(sigs) >= 2 and any(sig != sigs[0] for sig in sigs[1:]):
                return True
        return any(has_ambiguous_flat_binding(child) for child in children(node))
    if isinstance(node, list):
        return any(has_ambiguous_flat_binding(child) for child in node)
    return False


def materialize_bridge() -> tuple[dict[str, Any], int, list[dict[str, Any]]]:
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="clay-wp03-current-main-") as td:
        temp = Path(td)
        grammar_copy = temp / "V18.lark"
        grammar_copy.write_text(grammar_text, encoding="utf-8")
        units: list[dict[str, str]] = []
        docs: list[dict[str, Any]] = []
        for i, source in enumerate(SOURCES):
            source_copy = temp / f"source-{i}.clay"
            source_copy.write_bytes(source.read_bytes())
            doc = front.compile_frontend(source_copy.read_text(encoding="utf-8"), grammar_text, strict=True)
            docs.append(doc)
            artifact = temp / f"artifact-{i}.json"
            artifact.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            units.append({
                "artifact": str(artifact),
                "source": str(source_copy),
                "grammar": str(grammar_copy),
                "expected_surface": SURFACE,
            })

        parser_calls = 0
        original_build_parser = front.build_parser

        def forbidden_reparse(*args, **kwargs):
            nonlocal parser_calls
            parser_calls += 1
            raise AssertionError("silent downstream source reparse attempted")

        front.build_parser = forbidden_reparse
        try:
            compiled = bridge.compile_manifest({"units": units})
        finally:
            front.build_parser = original_build_parser
        return compiled, parser_calls, docs


def main() -> int:
    started = time.perf_counter()
    compiled, parser_calls, docs = materialize_bridge()
    ir = compiled["typed_ir"]
    residuals = ir.get("opaque_unlowered_semantics")
    assert isinstance(residuals, list)

    kind_counts = Counter(row.get("kind") for row in residuals if isinstance(row, dict))
    rule_rows = [row for row in residuals if isinstance(row, dict) and row.get("kind") in RULE_KINDS]
    metadata_rows = [row for row in residuals if isinstance(row, dict) and row.get("kind") in METADATA_KINDS]
    cycle_rows = [row for row in residuals if isinstance(row, dict) and row.get("kind") == "cycle_decl"]
    unknown_rows = [
        row for row in residuals
        if isinstance(row, dict)
        and row.get("kind") not in RULE_KINDS | METADATA_KINDS | {"cycle_decl"}
    ]

    ambiguous = [row for row in rule_rows if has_ambiguous_flat_binding(row["canonical_ast"])]
    explicit_or_single = [row for row in rule_rows if not has_ambiguous_flat_binding(row["canonical_ast"])]

    assert len(residuals) == 100, len(residuals)
    assert len(rule_rows) == 81, len(rule_rows)
    assert Counter(row["kind"] for row in rule_rows) == {"rule_decl": 67, "invariant_decl": 14}
    assert len(metadata_rows) == 18, len(metadata_rows)
    assert len(cycle_rows) == 1, len(cycle_rows)
    assert not unknown_rows, [row.get("kind") for row in unknown_rows]
    assert len(explicit_or_single) == 64, len(explicit_or_single)
    assert len(ambiguous) == 17, len(ambiguous)
    assert parser_calls == 0, parser_calls
    assert ir["invariants"]["opaque_semantics_mint_effect_authority"] == "FORBIDDEN"
    assert compiled["invariants"]["silent_reparse"] == "FORBIDDEN"
    assert compiled["invariants"]["opaque_semantics_execution_authority"] == "FORBIDDEN"

    # The single GO out-of-box discriminator: semantic program identity is stable across
    # runtime epochs, while epoch/version-bound state instance identity is not.
    semantic_id = ir["program_semantic_id"]
    state7 = identity_bridge.state_instance_identity(semantic_id, epoch=7, version=3)
    state8 = identity_bridge.state_instance_identity(semantic_id, epoch=8, version=3)
    assert state7 != state8

    # Cross-control: mutate admitted semantics at the source/frontend boundary and prove its
    # semantic identity changes while runtime epoch is held fixed. No downstream reparse.
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    original_text = SOURCES[0].read_text(encoding="utf-8")
    mutated_text = original_text.replace("logical_time:Epoch", "logical_time:Version", 1)
    assert mutated_text != original_text
    mutated = front.compile_frontend(mutated_text, grammar_text, strict=True)
    assert mutated["semantic_hash"] != docs[0]["semantic_hash"]
    semantic_mutation_state = identity_bridge.state_instance_identity(
        "frontend:" + mutated["semantic_hash"], epoch=7, version=3
    )
    original_frontend_state = identity_bridge.state_instance_identity(
        "frontend:" + docs[0]["semantic_hash"], epoch=7, version=3
    )
    assert semantic_mutation_state != original_frontend_state

    # Fail-closed tamper control on the already-admitted artifact contract.
    tampered = copy.deepcopy(docs[0])
    tampered["semantic_hash"] = "0" * 64
    try:
        identity_bridge.validate_frontend_artifact(tampered)
    except identity_bridge.V18BridgeError:
        tamper_rejected = True
    else:
        tamper_rejected = False
    assert tamper_rejected

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    report = {
        "status": "PASS",
        "scope": "CC_WP03_CURRENT_MAIN_V18_RECEIPT_BOUND_UNRESOLVED_BINDING_GATE",
        "surface": SURFACE,
        "grammar_sha256": docs[0]["grammar_sha256"],
        "typed_ir_sha256": ir["typed_ir_sha256"],
        "typed_ir_artifact_sha256": compiled["typed_ir_artifact_sha256"],
        "residual_count": len(residuals),
        "residual_kind_counts": dict(sorted((str(k), v) for k, v in kind_counts.items())),
        "rule_invariant": len(rule_rows),
        "explicit_or_single_binding": len(explicit_or_single),
        "ambiguous_binding_unresolved": len(ambiguous),
        "metadata": len(metadata_rows),
        "cycle": len(cycle_rows),
        "gaps": len(unknown_rows),
        "parser_calls_after_frontend_artifact_creation": parser_calls,
        "implicit_execution_count": 0,
        "ambiguous_binding_execution": "FORBIDDEN",
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "identity_cross_control": {
            "same_semantics_different_epoch_state_identity": "DISTINCT_PASS",
            "same_epoch_semantic_mutation_identity": "DISTINCT_PASS",
        },
        "frontend_semantic_hash_tamper": "REJECTED",
        "elapsed_ms": elapsed_ms,
        "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "architecture_delta": "NO_V18_SEMANTIC_CHANGE; PRESERVE_AMBIGUOUS_BINDING_AS_NON_EXECUTABLE_UNRESOLVED_STATE",
        "promotion": "NONE",
        "wp03_status": "OPEN_PENDING_STRUCTURAL_TYPE_INTEGRATION_AND_EXACT_TARGET_VPS_PACKAGE_ADJUDICATION",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
