#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
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
V3_G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
V3_DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
V4_G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V4_EXPLICIT_BINDING.clay"
V4_DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V4_EXPLICIT_BINDING.clay"


def compile_paths(paths: list[Path]) -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    units = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        doc = front.compile_frontend(source, grammar, strict=True)
        units.append(typed.SourceUnit(path, doc))
    return residual.build_typed_ir(units)


def clause_rows(ir: dict) -> list[dict]:
    return [
        row for row in ir["opaque_unlowered_semantics"]
        if isinstance(row, dict) and row.get("kind") in binding.SUPPORTED
    ]


def flat_key(row: dict) -> tuple[str, tuple[str, ...]]:
    return row["kind"], tuple(binding.token_values(row["canonical_ast"]))


def ast_bytes(row: dict) -> bytes:
    return binding.stable_json(row["canonical_ast"])


def main() -> int:
    v3 = compile_paths([V3_G9, V3_DIALECT])
    v4 = compile_paths([V4_G9, V4_DIALECT])
    v3_rows = clause_rows(v3)
    v4_rows = clause_rows(v4)
    assert len(v3_rows) == len(v4_rows) == 81

    v3_keys = [flat_key(x) for x in v3_rows]
    v4_keys = [flat_key(x) for x in v4_rows]
    assert Counter(v3_keys) == Counter(v4_keys), "V4 changed clause token semantics rather than binding only"
    assert len(set(v3_keys)) == 81 and len(set(v4_keys)) == 81, "clause token keys must be unique in measured corpus"

    v3_map = {flat_key(x): x for x in v3_rows}
    v4_map = {flat_key(x): x for x in v4_rows}
    changed = []
    unchanged = []
    for key in sorted(v3_map, key=lambda x: (x[0], x[1])):
        before = v3_map[key]
        after = v4_map[key]
        if ast_bytes(before) == ast_bytes(after):
            unchanged.append(key)
        else:
            changed.append(key)
    assert len(changed) == 17, len(changed)
    assert len(unchanged) == 64, len(unchanged)

    v3_bundle = binding.lower_bundle(v3)
    v4_bundle = binding.lower_bundle(v4)
    assert v3_bundle["summary"]["total"] == v4_bundle["summary"]["total"] == 81
    assert v3_bundle["summary"]["accepted"] == 64
    assert v3_bundle["summary"]["rejected_ambiguous"] == 17
    assert v4_bundle["summary"]["accepted"] == 81, v4_bundle["summary"]
    assert v4_bundle["summary"]["rejected_ambiguous"] == 0, v4_bundle["summary"]
    assert v4_bundle["summary"]["implicit_execution_count"] == 0
    assert v4_bundle["summary"]["effect_authority"] == "NONE"
    assert v4_bundle["summary"]["truth_authority"] == "NONE"

    changed_sources = [" ".join(key[1]) for key in changed]
    expected_fragments = [
        "rule diff > 0 => ADD_OR_STRENGTHEN",
        "rule diff < 0 => RETRACT_OR_WEAKEN",
        "rule diff = 0 => NO_CHANGE",
        "rule effect . commit requires possession",
        "rule cross_dialect_transform requires interface_match + semantic_hash_compatibility",
        "rule current_answer_context = AnswerCapsule + relevant",
        "rule reward . material_update requires verified_outcome + causal_credit",
        "rule reward . value_state preserves typed_dimensions + predictions",
        "rule reward . low_prediction_error + low_residual_pressure != automatic_boredom",
        "rule reward . low_prediction_error + high_residual_pressure + low_route_diversity -> STAGNATION_CANDIDATE",
        "rule extraction requires verified_equivalence + target_cost_model",
        "rule permanent_context",
        "rule reader_compaction = persist_canonical_state -> compact -> reload",
        "rule RAE . CHATGPT . endturn -> UsageObservation -> hypothesis + counterhypothesis + candidate",
        "rule Claude_only consumes latest_stack + Claude_only writes task_receipts",
        "rule valid_generation requires count",
        "rule dialect_extension requires interface_conformance + semantic_hash_compatibility + rollback",
    ]
    for fragment in expected_fragments:
        assert any(fragment in source for source in changed_sources), fragment

    report = {
        "status": "PASS",
        "scope": "WP03_G9_V4_EXPLICIT_BINDING_DIFFERENTIAL",
        "v3_clause_count": len(v3_rows),
        "v4_clause_count": len(v4_rows),
        "flat_token_multiset_equal": True,
        "binding_ast_changed": len(changed),
        "binding_ast_unchanged": len(unchanged),
        "v3_accepted": v3_bundle["summary"]["accepted"],
        "v3_ambiguous": v3_bundle["summary"]["rejected_ambiguous"],
        "v4_accepted": v4_bundle["summary"]["accepted"],
        "v4_ambiguous": v4_bundle["summary"]["rejected_ambiguous"],
        "v4_bundle_sha256": v4_bundle["bundle_sha256"],
        "v4_typed_ir_sha256": v4_bundle["source_typed_ir_sha256"],
        "changed_clause_sources": changed_sources,
        "implicit_execution_count": v4_bundle["summary"]["implicit_execution_count"],
        "effect_authority": v4_bundle["summary"]["effect_authority"],
        "truth_authority": v4_bundle["summary"]["truth_authority"],
        "promotion": "NONE",
        "wp03_status": "OPEN_PENDING_EVALUATOR_CONSUMPTION_AND_EXACT_CURRENT_ADJUDICATION",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
