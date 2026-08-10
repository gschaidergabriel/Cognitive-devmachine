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

import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_residual_semantics_candidate as residual
import claycode_wp03_rule_invariant_binding_gate_v1 as binding

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"


def compile_paths(paths: list[Path]) -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    units = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        doc = front.compile_frontend(source, grammar, strict=True)
        units.append(typed.SourceUnit(path, doc))
    return residual.build_typed_ir(units)


def compile_text(source: str) -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="clay-binding-") as td:
        path = Path(td) / "fixture.clay"
        path.write_text(source, encoding="utf-8")
        doc = front.compile_frontend(source, grammar, strict=True)
        return residual.build_typed_ir([typed.SourceUnit(path, doc)])


def clause_source(row: dict) -> str:
    return " ".join(binding.token_values(row["canonical_ast"]))


def find_clause(typed_ir: dict, needle: str) -> dict:
    for row in typed_ir["opaque_unlowered_semantics"]:
        if isinstance(row, dict) and row.get("kind") in binding.SUPPORTED and needle in clause_source(row):
            return row
    raise AssertionError(f"missing clause containing {needle!r}")


def test_real_corpus() -> tuple[dict, dict]:
    ir = compile_paths([G9, DIALECT])
    bundle = binding.lower_bundle(ir)
    summary = bundle["summary"]
    assert summary["total"] == 81, summary
    assert summary["kind_counts"] == {"INVARIANT": 14, "RULE": 67}, summary
    assert summary["accepted"] + summary["rejected_ambiguous"] == 81
    assert summary["rejected_ambiguous"] > 0, "flat V18 mixed binding must not silently disappear"
    assert summary["implicit_execution_count"] == 0
    assert summary["effect_authority"] == summary["truth_authority"] == "NONE"
    assert len(bundle["accepted_registry"]) == summary["accepted"]
    assert len(bundle["rejected"]) == summary["rejected_ambiguous"]

    lifecycle = binding.lower_clause(find_clause(ir, "external_effect lifecycle"), index=0)
    assert lifecycle["binding_status"] == "LOWERED_AND_VALIDATED_EXPLICIT_BINDING", lifecycle
    assert lifecycle["plan"]["operator"]["name"] == "lifecycle"
    assert lifecycle["plan"]["operator"]["explicit_equals_marker"] is True

    call_rule = binding.lower_clause(find_clause(ir, "materialize ( Query ) -> CognitiveView"), index=0)
    assert call_rule["binding_status"] == "LOWERED_AND_VALIDATED_EXPLICIT_BINDING"
    text = json.dumps(call_rule["plan"], sort_keys=True)
    assert '"execution": "FORBIDDEN"' in text

    return ir, bundle


def test_mixed_binding_rejected_and_grouping_resolves() -> None:
    flat = compile_text('module t\nversion "1"\nrule a requires b && c\n')
    grouped = compile_text('module t\nversion "1"\nrule a requires (b && c)\n')
    flat_bundle = binding.lower_bundle(flat)
    grouped_bundle = binding.lower_bundle(grouped)
    assert flat_bundle["summary"]["rejected_ambiguous"] == 1, flat_bundle
    assert grouped_bundle["summary"]["accepted"] == 1, grouped_bundle
    assert grouped_bundle["summary"]["rejected_ambiguous"] == 0, grouped_bundle
    assert flat_bundle["bundle_sha256"] != grouped_bundle["bundle_sha256"]


def test_same_operator_chain_is_ordered_nary() -> None:
    ir = compile_text('module t\nversion "1"\nrule a -> b -> c -> d\n')
    bundle = binding.lower_bundle(ir)
    assert bundle["summary"]["accepted"] == 1
    clause = bundle["clauses"][0]
    assert clause["plan"]["k"] == "nary_chain"
    assert clause["plan"]["operator"]["name"] == "->"
    assert [x["name"] for x in clause["plan"]["operands"]] == ["a", "b", "c", "d"]
    assert clause["plan"]["ordered"] is True


def test_relation_and_authority_tamper_fail_closed() -> None:
    ir = compile_text('module t\nversion "1"\nrule a never_implies b\n')
    row = next(x for x in ir["opaque_unlowered_semantics"] if x.get("kind") == "rule_decl")
    first = binding.lower_clause(row, index=0)
    mutant = copy.deepcopy(row)
    relation = next(
        n for n in binding.children(mutant["canonical_ast"]["children"][1])
        if binding.kind(n) == "infix_relop"
    )
    relation["children"][0]["value"] = "never_requires"
    second = binding.lower_clause(mutant, index=0)
    assert first["binding_semantic_sha256"] != second["binding_semantic_sha256"]
    assert first["effect_authority"] == second["effect_authority"] == "NONE"
    assert first["truth_authority"] == second["truth_authority"] == "NONE"

    malformed = copy.deepcopy(row)
    malformed["canonical_ast"]["children"].append({"kind": "cycle_block", "children": []})
    try:
        binding.lower_clause(malformed, index=0)
    except binding.BindingError:
        pass
    else:
        raise AssertionError("malformed clause/root envelope must fail closed")


def main() -> int:
    ir, bundle = test_real_corpus()
    test_mixed_binding_rejected_and_grouping_resolves()
    test_same_operator_chain_is_ordered_nary()
    test_relation_and_authority_tamper_fail_closed()

    rejected = []
    clause_by_index = {
        i: row for i, row in enumerate(ir["opaque_unlowered_semantics"])
        if isinstance(row, dict) and row.get("kind") in binding.SUPPORTED
    }
    for item in bundle["clauses"]:
        if item["binding_status"] != "LOWERED_AND_VALIDATED_EXPLICIT_BINDING":
            row = clause_by_index[item["index"]]
            rejected.append({
                "index": item["index"],
                "kind": item["clause_kind"],
                "source": clause_source(row),
                "binding_semantic_sha256": item["binding_semantic_sha256"],
            })

    report = {
        "status": "PASS_DIAGNOSTIC_EXACT_BINDING_FRONTIER",
        "scope": "WP03_RULE_INVARIANT_EXPLICIT_BINDING_GATE_V1",
        "source_typed_ir_sha256": bundle["source_typed_ir_sha256"],
        "bundle_sha256": bundle["bundle_sha256"],
        "total_clauses": bundle["summary"]["total"],
        "accepted_explicit_or_single_binding": bundle["summary"]["accepted"],
        "rejected_ambiguous_binding": bundle["summary"]["rejected_ambiguous"],
        "ambiguous_clauses": rejected,
        "same_operator_chain": "ORDERED_NARY_PASS",
        "mixed_flat_chain": "FAIL_CLOSED_PASS",
        "parenthesized_nested_binding": "PASS",
        "relation_mutation_identity": "PASS",
        "runtime_call_execution": "FORBIDDEN",
        "implicit_execution_count": 0,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "promotion": "NONE",
        "wp03_status": bundle["wp03_status"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
