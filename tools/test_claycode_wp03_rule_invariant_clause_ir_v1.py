#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_residual_semantics_candidate as residual
import claycode_wp03_rule_invariant_clause_ir_v1 as clause

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
SUPERVISOR = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_STATE.json"
FRONTEND = ROOT / "tools/claycode_base_frontend.py"
TYPED_IR = ROOT / "tools/claycode_base_typed_ir.py"
RESIDUAL = ROOT / "tools/claycode_wp03_residual_semantics_candidate.py"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def blob(path: Path) -> str:
    return git("hash-object", str(path.relative_to(ROOT)))


def current_work_revision() -> dict[str, str]:
    supervisor = json.loads(SUPERVISOR.read_text(encoding="utf-8"))
    steering_ref = supervisor.get("steering_ref")
    assert isinstance(steering_ref, str) and steering_ref
    steering = ROOT / steering_ref
    assert steering.is_file(), steering
    return {
        "repo_head": git("rev-parse", "HEAD"),
        "supervisor_blob_sha": blob(SUPERVISOR),
        "steering_ref": steering_ref,
        "steering_blob_sha": blob(steering),
        "frontend_blob_sha": blob(FRONTEND),
        "grammar_blob_sha": blob(GRAMMAR),
        "typed_ir_blob_sha": blob(TYPED_IR),
        "residual_builder_blob_sha": blob(RESIDUAL),
    }


def real_typed_ir() -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    units = []
    for path in SOURCES:
        source = path.read_text(encoding="utf-8")
        compiled = front.compile_frontend(source, grammar, strict=True)
        units.append(typed.SourceUnit(path, compiled))
    a = residual.build_typed_ir(units)
    b = residual.build_typed_ir(units)
    assert a["typed_ir_sha256"] == b["typed_ir_sha256"]
    assert a == b
    return a


def expect_error(fn, marker: str | None = None) -> str:
    try:
        fn()
    except clause.ClauseIRError as exc:
        text = str(exc)
        if marker is not None:
            assert marker in text, (marker, text)
        return text
    raise AssertionError("expected ClauseIRError")


def first_kind(ir: dict, kind: str) -> dict:
    return next(row for row in ir["opaque_unlowered_semantics"] if row.get("kind") == kind)


def mutate_first_relation(row: dict) -> dict:
    out = copy.deepcopy(row)
    stack = [out["canonical_ast"]]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        if node.get("token") in clause.RELATION_TOKEN_TYPES:
            node["value"] = "FORGED_RELATION"
            return out
        stack.extend(reversed(node.get("children", [])))
    raise AssertionError("fixture did not contain relation token")


def mutate_first_symbol(row: dict) -> dict:
    out = copy.deepcopy(row)
    stack = [out["canonical_ast"]]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        if node.get("token") == "NAME" and isinstance(node.get("value"), str):
            node["value"] = node["value"] + "_MUT"
            return out
        stack.extend(reversed(node.get("children", [])))
    raise AssertionError("fixture did not contain NAME token")


def test_real_inventory_and_consumer() -> dict:
    ir = real_typed_ir()
    work = current_work_revision()
    receipt = clause.lower_bundle(ir, work_revision=work)
    clause.validate_bundle(receipt, expected_work_revision=work)

    assert receipt["source_typed_ir_sha256"] == ir["typed_ir_sha256"]
    assert receipt["summary"]["clause_count"] == 81, receipt["summary"]
    assert receipt["summary"]["clause_kind_counts"] == {"INVARIANT": 14, "RULE": 67}
    assert receipt["summary"]["deferred_count"] == 19
    assert receipt["summary"]["effect_authority"] == "NONE"
    assert receipt["summary"]["runtime_execution_authority"] == "NONE"
    assert all(c["effect_authority"] == "NONE" for c in receipt["clauses"])
    assert all(c["truth_authority"] == "NONE" for c in receipt["clauses"])

    consumed = clause.consume_declarative_clauses(receipt, expected_work_revision=work)
    assert consumed["status"] == "PASS_CONSUMPTION_BOUNDARY_ONLY"
    assert consumed["implicit_execution_count"] == 0
    assert consumed["effect_authority"] == "NONE"
    assert len(consumed["registry"]) == 81
    return {
        "typed_ir_sha256": ir["typed_ir_sha256"],
        "clause_receipt_sha256": receipt["clause_receipt_sha256"],
        "consumer_receipt_sha256": consumed["consumer_receipt_sha256"],
        "work_revision": work,
        "counts": receipt["summary"],
    }


def test_semantic_mutation_changes_identity() -> None:
    ir = real_typed_ir()
    work = current_work_revision()
    original = first_kind(ir, "rule_decl")
    changed = mutate_first_symbol(original)
    a = clause.lower_clause(original, index=0, work_revision=work)
    b = clause.lower_clause(changed, index=0, work_revision=work)
    assert a["clause_semantic_sha256"] != b["clause_semantic_sha256"]
    assert a["source_residual_sha256"] != b["source_residual_sha256"]


def test_relation_tamper_fails_closed() -> None:
    ir = real_typed_ir()
    work = current_work_revision()
    target = None
    for kind in ("rule_decl", "invariant_decl"):
        for row in ir["opaque_unlowered_semantics"]:
            if row.get("kind") != kind:
                continue
            try:
                target = mutate_first_relation(row)
                break
            except AssertionError:
                pass
        if target is not None:
            break
    assert target is not None
    expect_error(lambda: clause.lower_clause(target, index=0, work_revision=work), "unknown")


def test_stale_work_revision_fails_closed() -> None:
    ir = real_typed_ir()
    work = current_work_revision()
    receipt = clause.lower_bundle(ir, work_revision=work)
    for field in ("repo_head", "supervisor_blob_sha", "grammar_blob_sha", "residual_builder_blob_sha"):
        stale = dict(work)
        stale[field] = "0" * 40
        expect_error(lambda stale=stale: clause.validate_bundle(receipt, expected_work_revision=stale), "STALE_EXECUTION_RECEIPT")
        expect_error(lambda stale=stale: clause.consume_declarative_clauses(receipt, expected_work_revision=stale), "STALE_EXECUTION_RECEIPT")


def test_missing_component_binding_fails_closed() -> None:
    ir = real_typed_ir()
    work = current_work_revision()
    bad = dict(work)
    bad.pop("typed_ir_blob_sha")
    expect_error(lambda: clause.lower_bundle(ir, work_revision=bad), "missing exact bindings")


def test_authority_tamper_fails_closed() -> None:
    ir = real_typed_ir()
    work = current_work_revision()
    receipt = clause.lower_bundle(ir, work_revision=work)
    bad = copy.deepcopy(receipt)
    bad["clauses"][0]["effect_authority"] = "FORGED"
    expect_error(lambda: clause.validate_bundle(bad, expected_work_revision=work), "authority")


def test_unsupported_class_remains_outside_clause_lowerer() -> None:
    ir = real_typed_ir()
    work = current_work_revision()
    dialect = first_kind(ir, "dialect_decl")
    expect_error(lambda: clause.lower_clause(dialect, index=0, work_revision=work), "unsupported residual class")
    receipt = clause.lower_bundle(ir, work_revision=work)
    assert any(row["kind"] == "dialect_decl" for row in receipt["deferred"])
    assert all(row["status"] == "EXPLICITLY_DEFERRED_FAIL_CLOSED" for row in receipt["deferred"])


def main() -> int:
    summary = test_real_inventory_and_consumer()
    test_semantic_mutation_changes_identity()
    test_relation_tamper_fails_closed()
    test_stale_work_revision_fails_closed()
    test_missing_component_binding_fails_closed()
    test_authority_tamper_fails_closed()
    test_unsupported_class_remains_outside_clause_lowerer()
    print(json.dumps({
        "status": "PASS",
        "scope": "REAL_G9_V18_RULE_INVARIANT_CLAUSE_IR_PLUS_FAIL_CLOSED_CONSUMER",
        "summary": summary,
        "semantic_mutation_identity": "PASS",
        "relation_tamper": "REJECTED",
        "stale_work_or_component_revision": "REJECTED",
        "missing_component_binding": "REJECTED",
        "authority_tamper": "REJECTED",
        "unsupported_class": "DEFERRED_FAIL_CLOSED",
        "wp03_promotion": "NONE",
        "effect_authority": "NONE",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
