#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_base_typed_ir as typed
import claycode_wp03_typed_ir_v2_state_identity as v2

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
MVC = ROOT / "research_entity/claycode/base/fixtures/WP03_MVC_TYPED_STATE_V1.clay"
ABA = ROOT / "research_entity/claycode/base/fixtures/WP03_ABA_VERSIONED_STATE_V1.clay"


def expect_error(fn, marker: str | None = None, exc_type=v2.TypedIRV2Error) -> str:
    try:
        fn()
    except exc_type as exc:
        text = str(exc)
        if marker is not None:
            assert marker in text, (marker, text)
        return text
    raise AssertionError(f"expected {exc_type.__name__}")


def compile_text(source: str) -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="clay-wp03-v2-") as td:
        path = Path(td) / "fixture.clay"
        path.write_text(source, encoding="utf-8")
        doc = typed.front.compile_frontend(source, grammar, strict=True)
        return v2.build_typed_ir_v2([typed.SourceUnit(path, doc)])


def role_map(ir: dict) -> dict[str, str]:
    return {row["name"]: row["role"] for row in ir["type_roles"]}


def record_map(ir: dict) -> dict[str, dict]:
    return {row["name"]: row for row in ir["structural_records"]}


def test_real_corpus() -> dict:
    ir = v2.compile_sources([G9, DIALECT, MVC, ABA], GRAMMAR)
    sums = {x["name"]: x for x in ir["declarations"] if x.get("kind") == "sum_type"}
    expected_sums = {
        "EvidenceTier": ["GOLD", "SILVER", "BRONZE"],
        "FamiliarityResult": ["KNOWN_HIGH_CONFIDENCE", "KNOWN_NEEDS_CONFIRMATION", "AMBIGUOUS", "UNKNOWN", "CONFLICT"],
        "LearnerStage": ["CURRENT", "CANDIDATE", "LAST_KNOWN_GOOD", "REJECTED", "ROLLED_BACK"],
        "AtomicIdentityMode": ["VALUE_ONLY", "VERSION_BOUND"],
        "CasStrength": ["STRONG", "WEAK"],
        "AtomicOrdering": ["RELAXED", "ACQUIRE", "RELEASE", "ACQ_REL", "SEQ_CST"],
    }
    assert {k: v["variants"] for k, v in sums.items() if k in expected_sums} == expected_sums
    assert all(sums[name]["authority"] == "NONE" for name in expected_sums)

    roles = role_map(ir)
    expected_roles = {
        "Set": "COLLECTION_SET_UNORDERED",
        "Ordered": "COLLECTION_ORDERED",
        "List": "COLLECTION_LIST",
        "Map": "COLLECTION_MAP",
        "Result": "RESULT_DISCRIMINATED",
        "Option": "OPTIONAL_DISCRIMINATED",
        "Epoch": "VERSION_IDENTITY_COMPONENT",
        "Version": "VERSION_IDENTITY_COMPONENT",
        "ResourceRef": "RESOURCE_IDENTITY_COMPONENT",
        "CapabilityRef": "CAPABILITY_DESCRIPTOR_NON_BEARER",
    }
    for name, role in expected_roles.items():
        assert roles.get(name) == role, (name, roles.get(name), role)

    records = record_map(ir)
    for name in [
        "VisualTrainingExample", "VisualClassifierVersion", "VisualFamiliarityResult",
        "LearnerBudgetState", "VisualLearnerState", "GenericCoreState", "VersionedExpected",
        "AtomicCell", "CompareExchangeIntent", "CompareExchangeOutcome",
    ]:
        assert name in records, name
        for field in records[name]["fields"]:
            names = v2.type_names(field["type_expr"])
            assert "Any" not in names and "OpaqueParam" not in names, (name, field)

    return ir


def test_collection_and_result_identity(ir: dict) -> None:
    base = {
        "evidence": ["e2", "e1", "e1"],
        "ordered": ["a", "b"],
        "history": ["h1", "h2"],
        "by_ref": {"r2": 2, "r1": 1},
        "maybe_ref": "m1",
        "operation": {"ok": "done"},
    }
    reordered_set_map = {**base, "evidence": ["e1", "e2"], "by_ref": {"r1": 1, "r2": 2}}
    a = v2.typed_state_identity(ir, "GenericCoreState", base)
    b = v2.typed_state_identity(ir, "GenericCoreState", reordered_set_map)
    assert a["state_identity_sha256"] == b["state_identity_sha256"], (a, b)

    ordered_changed = copy.deepcopy(base)
    ordered_changed["ordered"] = ["b", "a"]
    c = v2.typed_state_identity(ir, "GenericCoreState", ordered_changed)
    assert c["state_identity_sha256"] != a["state_identity_sha256"]

    err = copy.deepcopy(base)
    err["operation"] = {"err": "done"}
    d = v2.typed_state_identity(ir, "GenericCoreState", err)
    assert d["state_identity_sha256"] != a["state_identity_sha256"]
    expect_error(lambda: v2.typed_state_identity(ir, "GenericCoreState", {**base, "operation": {"ok": "x", "err": "y"}}), "exactly one of ok/err")


def test_aba_version_and_resource_identity(ir: dict) -> None:
    state_a = {
        "cell_id": "resource:cell-1", "value": 7, "version": 10,
        "identity_mode": "VERSION_BOUND", "capability": "capability:descriptor-only",
    }
    state_a2 = {**state_a, "version": 12}
    state_other_resource = {**state_a, "cell_id": "resource:cell-2"}
    a = v2.typed_state_identity(ir, "AtomicCell", state_a)
    b = v2.typed_state_identity(ir, "AtomicCell", state_a2)
    c = v2.typed_state_identity(ir, "AtomicCell", state_other_resource)
    assert a["state_identity_sha256"] != b["state_identity_sha256"]
    assert a["state_identity_sha256"] != c["state_identity_sha256"]
    assert {x["field"] for x in a["identity_sensitive_fields"]} >= {"cell_id", "version"}
    assert a["capability_descriptor_fields"] == ["capability"]
    assert a["effect_authority"] == "NONE"
    assert a["execution_trace_in_identity"] is False
    assert state_a["value"] == state_a2["value"] == 7


def test_mvc_version_identity(ir: dict) -> None:
    current = {
        "version": "mvc-7", "feature_backbone_version": "clip-3", "stage": "CURRENT",
        "prototype_state_ref": "proto:7", "readout_state_ref": None, "calibration_ref": "cal:7",
        "training_examples": ["ex:2", "ex:1"], "evaluation_receipts": ["receipt:b", "receipt:a"],
        "parent_version": "mvc-6", "semantic_hash": "hash:same-visible-model",
    }
    next_version = {**current, "version": "mvc-8", "training_examples": ["ex:1", "ex:2"]}
    a = v2.typed_state_identity(ir, "VisualClassifierVersion", current)
    b = v2.typed_state_identity(ir, "VisualClassifierVersion", next_version)
    assert a["state_identity_sha256"] != b["state_identity_sha256"]
    assert {x["field"] for x in a["identity_sensitive_fields"]} >= {"version", "feature_backbone_version", "parent_version"}
    assert a["effect_authority"] == b["effect_authority"] == "NONE"


def test_negative_type_corpus() -> None:
    duplicate_variant = """module test.duplicate\nversion \"1\"\ntype E = A|A\nrecord R { value:E }\n"""
    expect_error(lambda: compile_text(duplicate_variant), "duplicate closed-sum variant")

    source_a = """module test.eq\nversion \"1\"\ntype E=A|B\nrecord R {\n  value:E\n  epoch:Epoch\n}\n"""
    source_b = """// layout/provenance-only difference\nmodule test.eq\n\nversion \"1\"\ntype E = A | B\nrecord R {\n  value:E\n  epoch:Epoch\n}\n"""
    ia = compile_text(source_a)
    ib = compile_text(source_b)
    assert ia["typed_ir_sha256"] == ib["typed_ir_sha256"]

    class_expr = """module test.classopaque\nversion \"1\"\nclass C = something\nrecord R { x:Int }\n"""
    ic = compile_text(class_expr)
    assert any(row.get("kind") == "class_decl" for row in ic["opaque_unlowered_semantics"])
    assert not any(d.get("name") == "C" and d.get("kind") == "sum_type" for d in ic["declarations"])


def test_sum_value_rejection(ir: dict) -> None:
    expect_error(lambda: v2.typed_state_identity(ir, "EvidenceTier", "PLATINUM"), "invalid EvidenceTier variant")


def main() -> int:
    ir = test_real_corpus()
    test_collection_and_result_identity(ir)
    test_aba_version_and_resource_identity(ir)
    test_mvc_version_identity(ir)
    test_negative_type_corpus()
    test_sum_value_rejection(ir)
    sums = [d for d in ir["declarations"] if d.get("kind") == "sum_type"]
    report = {
        "status": "PASS",
        "scope": "WP03_STRUCTURAL_TYPES_STATE_IDENTITY_REAL_MVC_ABA_CORPUS",
        "typed_ir_v2_sha256": ir["typed_ir_sha256"],
        "program_semantic_id": ir["program_semantic_id"],
        "closed_sum_types": len(sums),
        "target_sum_types": sorted(d["name"] for d in sums if d["name"] in {"EvidenceTier", "FamiliarityResult", "LearnerStage", "AtomicIdentityMode", "CasStrength", "AtomicOrdering"}),
        "mvc_records": 6,
        "aba_records": 4,
        "collection_result_option_roles": "PASS",
        "set_order_independence": "PASS",
        "ordered_order_sensitivity": "PASS",
        "result_discriminator": "PASS",
        "aba_visible_value_same_epoch_changed_identity": "PASS",
        "resource_identity_discrimination": "PASS",
        "mvc_version_identity_discrimination": "PASS",
        "capability_descriptor_authority": "NONE",
        "execution_trace_in_state_identity": False,
        "duplicate_sum_variant": "REJECTED",
        "invalid_sum_value": "REJECTED",
        "layout_provenance_equivalence": "PASS",
        "arbitrary_class_expression": "DEFERRED_OPAQUE_FAIL_CLOSED",
        "untyped_escape_hatch": "ABSENT_IN_TARGET_FIXTURES",
        "promotion": "NONE",
        "wp03_status": "OPEN",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
