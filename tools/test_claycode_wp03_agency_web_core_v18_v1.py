#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_wp03_rule_invariant_binding_gate_v1 as binding
import claycode_wp03_typed_ir_v2_state_identity as typed_v2

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
CORE = ROOT / "research_entity/claycode/base/SELF_ROOT_AGENCY_WEB_CORE_V18_CANDIDATE.clay"

EXPECTED_SUMS = {
    "GoalOrigin": ["AUTHENTICATED_USER", "SELF_GENERATED", "RESEARCH_BRIDGE", "RECOVERY", "STANDING_CONTRACT"],
    "GoalState": ["CANDIDATE", "TRIAL", "ACTIVE", "DORMANT", "BLOCKED", "COMPLETED", "RETIRED", "REJECTED"],
    "InterestSource": ["INFORMATION_GAIN", "COMPETENCE_PROGRESS", "CONTROLLABILITY_GAIN", "NOVELTY", "UNRESOLVED_PRESSURE", "CROSS_GOAL_REUSE", "PERSON_PROJECT_RELEVANCE", "WORLD_CHANGE"],
    "InitiativeReason": ["OPEN_LOOP", "OPPORTUNITY", "IDLE_CAPACITY", "STAGNATION_ESCAPE", "PERIODIC_REVIEW", "NEW_EVIDENCE", "GOAL_WAKEUP"],
    "GoalHorizon": ["FAST", "MEDIUM", "SLOW", "OPEN_ENDED"],
    "IngressAuthority": ["AUTHENTICATED_DIRECT_MESSAGE", "UNTRUSTED_EXTERNAL_DATA", "TRUSTED_INTERNAL_STATE"],
    "WebPayloadKind": ["FACT_CLAIM", "QUOTE", "CODE", "LINK", "METADATA", "DATASET_ROW", "INSTRUCTION_LIKE_TEXT", "UNKNOWN"],
}

EXPECTED_RECORD_FIELDS = {
    "InterestTrace": ["interest_id", "subject", "sources", "strength", "information_gain_estimate", "competence_progress_estimate", "controllability_gain_estimate", "novelty", "unresolved_pressure", "cross_goal_reuse", "standing_goal_relevance", "persistence", "habituation", "evidence", "last_updated"],
    "AutotelicGoal": ["goal_id", "origin", "semantic_goal", "state", "parent_goals", "interest_refs", "why_now", "success_criteria", "progress_model", "next_affordances", "uncertainty", "expected_information_gain", "expected_competence_gain", "expected_controllability_gain", "expected_external_utility", "expected_cost", "reversibility", "effect_classes", "budget", "horizon", "wake_conditions", "last_progress_at", "provenance"],
    "AgencyState": ["interests", "goals", "open_loops", "active_experiments", "dormant_goal_index", "initiative_budget", "current_opportunity_frontier", "last_autonomous_action", "state_epoch"],
    "InitiativePulse": ["reason", "amplitude", "target_interest", "target_goal", "expires_at", "provenance"],
    "GoalCheckpoint": ["goal_id", "state", "progress_summary", "unresolved", "next_affordances", "wake_conditions", "evidence", "state_epoch", "created_at"],
    "UntrustedWebJsonEnvelope": ["schema_version", "source_url", "fetched_at", "source_hash", "mime_type", "title", "payload_kind", "extracted_fields", "quoted_text", "links", "claims", "instruction_like_segments", "parser_confidence", "parse_errors", "authority", "executable"],
    "WebEvidenceClay": ["source", "observed_at", "evidence_type", "claims", "opaque_quotes", "links", "uncertainty", "provenance", "authority", "instruction_authority", "effect_authority"],
}


def token_text(row: dict) -> str:
    return " ".join(binding.token_values(row["canonical_ast"]))


def main() -> int:
    ir = typed_v2.compile_sources([CORE], GRAMMAR)
    sums = {x["name"]: x for x in ir["declarations"] if x.get("kind") == "sum_type"}
    assert {name: sums[name]["variants"] for name in EXPECTED_SUMS} == EXPECTED_SUMS
    assert all(sums[name]["authority"] == "NONE" for name in EXPECTED_SUMS)

    records = {x["name"]: x for x in ir["structural_records"]}
    for name, fields in EXPECTED_RECORD_FIELDS.items():
        assert name in records, name
        assert [x["name"] for x in records[name]["fields"]] == fields, (name, records[name]["fields"])
        for field in records[name]["fields"]:
            names = typed_v2.type_names(field["type_expr"])
            assert "Any" not in names and "OpaqueParam" not in names, (name, field)

    # All owner refinement/security clauses must survive into rule/invariant residual semantics
    # and be accepted by the explicit-binding gate without inventing precedence.
    bundle = binding.lower_bundle(ir)
    assert bundle["summary"]["total"] >= 40, bundle["summary"]
    assert bundle["summary"]["rejected_ambiguous"] == 0, bundle["rejected"]
    assert bundle["summary"]["accepted"] == bundle["summary"]["total"]
    assert bundle["summary"]["implicit_execution_count"] == 0
    assert bundle["summary"]["effect_authority"] == bundle["summary"]["truth_authority"] == "NONE"

    texts = [token_text(x) for x in ir["opaque_unlowered_semantics"] if x.get("kind") in {"rule_decl", "invariant_decl"}]
    required_semantics = [
        "invariant InitiativePulse . amplitude <= 0.12",
        "invariant UntrustedWebJsonEnvelope . authority = UNTRUSTED_EXTERNAL_DATA",
        "invariant UntrustedWebJsonEnvelope . executable = false",
        "invariant WebEvidenceClay . authority = UNTRUSTED_EXTERNAL_DATA",
        "invariant WebEvidenceClay . instruction_authority = NONE",
        "invariant WebEvidenceClay . effect_authority = NONE",
        "rule AUTHENTICATED_DIRECT_MESSAGE != UNTRUSTED_EXTERNAL_DATA",
        "rule UNTRUSTED_EXTERNAL_DATA never_implies AUTHENTICATED_DIRECT_MESSAGE",
    ]
    for expected in required_semantics:
        assert expected in texts, expected

    agency_state = {
        "interests": {},
        "goals": {},
        "open_loops": [],
        "active_experiments": [],
        "dormant_goal_index": [],
        "initiative_budget": "budget:idle",
        "current_opportunity_frontier": [],
        "last_autonomous_action": None,
        "state_epoch": 7,
    }
    agency_next = {**agency_state, "state_epoch": 8}
    aid = typed_v2.typed_state_identity(ir, "AgencyState", agency_state)
    bid = typed_v2.typed_state_identity(ir, "AgencyState", agency_next)
    assert aid["state_identity_sha256"] != bid["state_identity_sha256"]
    assert {x["field"] for x in aid["identity_sensitive_fields"]} >= {"state_epoch"}

    web = {
        "schema_version": "1",
        "source_url": "https://example.invalid/evidence",
        "fetched_at": "time:1",
        "source_hash": "hash:1",
        "mime_type": "text/html",
        "title": None,
        "payload_kind": "FACT_CLAIM",
        "extracted_fields": {},
        "quoted_text": [],
        "links": [],
        "claims": [],
        "instruction_like_segments": [],
        "parser_confidence": 0.8,
        "parse_errors": [],
        "authority": "UNTRUSTED_EXTERNAL_DATA",
        "executable": False,
    }
    wid = typed_v2.typed_state_identity(ir, "UntrustedWebJsonEnvelope", web)
    assert wid["effect_authority"] == "NONE"

    report = {
        "status": "PASS",
        "scope": "WP03_OWNER_AGENCY_WEB_CORE_V18_LOWERING_V1",
        "typed_ir_sha256": ir["typed_ir_sha256"],
        "closed_sum_types": len(EXPECTED_SUMS),
        "required_records": len(EXPECTED_RECORD_FIELDS),
        "rule_invariant_semantics": bundle["summary"]["total"],
        "binding_ambiguities": bundle["summary"]["rejected_ambiguous"],
        "agency_epoch_identity": "DISTINCT_ON_EPOCH_CHANGE",
        "web_untrusted_authority_invariant": "PRESERVED",
        "web_nonexecutability_invariant": "PRESERVED",
        "web_instruction_authority_none": "PRESERVED",
        "web_effect_authority_none": "PRESERVED",
        "untyped_escape_hatch": "ABSENT_IN_REQUIRED_RECORDS",
        "implicit_execution_count": 0,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "language_strategy": "FROZEN_V18_CORE_WITH_EXPLICIT_OWNER_SURFACE_LOWERING",
        "promotion": "NONE",
        "wp03_status": "OPEN_PENDING_FULL_DIRECTIVE_FIDELITY_AND_DOWNSTREAM_CONSUMPTION",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
