#!/usr/bin/env python3
"""Materialize 14 deterministic Trigger-2 Hyperposition D/E candidate rows.

The generated rows are source-design candidates only: training_eligible=false, no canonical
truth/effect authority, and no training/runtime credit. Evaluator-only latent state must never
enter model-visible prompt fields.
"""
from __future__ import annotations

import hashlib
import json

from tools.trigger2_hyperposition_reference_labelers_v1 import (
    BRANCH_SCHEMA,
    OBS_SCHEMA,
    TEST_SCHEMA,
    U_d_test_order,
    f_salience_rank,
    label_transition,
)

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
GENERATOR_SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_SEED/v1"
LABELER = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v1"


def evidence(eid: str, ancestry: str, group: str, role: str = "NONDECISIVE") -> dict:
    return {
        "evidence_id": eid,
        "provenance_ancestry_id": ancestry,
        "independence_group": group,
        "decision_role": role,
    }


def base(qid: str = "q") -> list[dict]:
    values = ["ALT_ALPHA", "ALT_BETA", "ALT_GAMMA"]
    out = []
    for i, value in enumerate(values):
        out.append(
            {
                "schema": BRANCH_SCHEMA,
                "branch_id": f"b{i}",
                "v_semantic_value": value,
                "K_context_predicate": "ctx=episode",
                "E_plus": [],
                "E_minus": [],
                "F_falsifier": f"test_not_{value.lower()}",
                "T_validity_scope": "episode",
                "A_origin_provenance": f"synthetic:{qid}:b{i}",
                "sigma_epistemic_status": "COUNTERHYPOTHESIS" if i == 1 else "HYPOTHESIS",
                "projection_visibility": "VISIBLE",
                "validity": "LIVE",
            }
        )
    return out


def _finish(row: dict) -> dict:
    material = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    row["row_sha256"] = hashlib.sha256(material.encode()).hexdigest()
    return row


def transition_row(family: str, split: str, before: list[dict], observation: dict, context: dict, prompt: str, evidence_class: str = "METHOD_ONLY") -> dict:
    target = label_transition(before, observation, context)
    return _finish(
        {
            "schema": ROW_SCHEMA,
            "generator_schema": GENERATOR_SCHEMA,
            "evidence_class": evidence_class,
            "reality_level": "R2" if evidence_class == "METHOD_ONLY" else "R3",
            "family_id": family,
            "provenance_ancestry_id": f"trigger2-hp-labeler-v1:{family.lower()}",
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "fact_status": "NOT_APPLICABLE" if evidence_class == "METHOD_ONLY" else "UNKNOWN",
            "target_type": "HYPERPOSITION_REFERENCE_LABELED_TRANSITION",
            "split": split,
            "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
            "selected_using_holdout": False,
            "training_eligible": False,
            "model_visible_fields": ["prompt"],
            "supervision_field": "target",
            "audit_metadata_must_not_enter_model_context": True,
            "reference_labeler": LABELER,
            "hyperposition_state_before_evaluator_only": before,
            "observation_evaluator_only": observation,
            "resolve_context_evaluator_only": context,
            "prompt": prompt,
            "target": json.dumps(target, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        }
    )


def rank_row(family: str, tests: list[dict], prompt: str) -> dict:
    branch_set = base(family)
    target = U_d_test_order(branch_set, tests)
    return _finish(
        {
            "schema": ROW_SCHEMA,
            "generator_schema": GENERATOR_SCHEMA,
            "evidence_class": "METHOD_ONLY",
            "reality_level": "R2",
            "family_id": family,
            "provenance_ancestry_id": f"trigger2-hp-labeler-v1:{family.lower()}",
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "fact_status": "NOT_APPLICABLE",
            "target_type": "HYPERPOSITION_DISCRIMINATOR_RANKING",
            "split": "VALIDATION",
            "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
            "selected_using_holdout": False,
            "training_eligible": False,
            "model_visible_fields": ["prompt"],
            "supervision_field": "target",
            "audit_metadata_must_not_enter_model_context": True,
            "reference_labeler": LABELER,
            "branch_set_evaluator_only": branch_set,
            "tests_evaluator_only": tests,
            "prompt": prompt,
            "target": json.dumps(target, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        }
    )


def salience_row(family: str, items: list[dict], prompt: str) -> dict:
    target = f_salience_rank(items)
    return _finish(
        {
            "schema": ROW_SCHEMA,
            "generator_schema": GENERATOR_SCHEMA,
            "evidence_class": "METHOD_ONLY",
            "reality_level": "R2",
            "family_id": family,
            "provenance_ancestry_id": f"trigger2-hp-labeler-v1:{family.lower()}",
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "fact_status": "NOT_APPLICABLE",
            "target_type": "HYPERPOSITION_SALIENCE_RANKING",
            "split": "VALIDATION",
            "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
            "selected_using_holdout": False,
            "training_eligible": False,
            "model_visible_fields": ["prompt"],
            "supervision_field": "target",
            "audit_metadata_must_not_enter_model_context": True,
            "reference_labeler": LABELER,
            "salience_items_evaluator_only": items,
            "prompt": prompt,
            "target": json.dumps(target, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        }
    )


def rows() -> list[dict]:
    out: list[dict] = []

    b = base("t1")
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("e-support-a", "sensor:a", "ig-a"), "branch_relations": {"b0": "SUPPORT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"}}
    ctx = {"context_id": "t1", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
    out.append(transition_row("HPU_SUPPORT_RETAIN_F01", "TRAIN", b, obs, ctx, "HP has three live alternatives. A new nondecisive observation supports ALT_ALPHA and says nothing about the other two. Update branch-local evidence without collapsing the set."))

    b = base("t2")
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("e-counter-b", "sensor:b", "ig-b"), "branch_relations": {"b0": "NO_EFFECT", "b1": "COUNTER", "b2": "NO_EFFECT"}}
    ctx = {"context_id": "t2", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
    out.append(transition_row("HPU_COUNTER_RETAIN_F02", "TRAIN", b, obs, ctx, "A new nondecisive observation counts against ALT_BETA only. Apply the update. Do not convert counterevidence into automatic falsification."))

    b = base("t3")
    item = evidence("e-repeat", "shared:source", "ig-shared")
    b[0]["E_plus"] = [item]
    obs = {"schema": OBS_SCHEMA, "evidence": item, "branch_relations": {"b0": "SUPPORT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"}}
    ctx = {"context_id": "t3", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
    out.append(transition_row("HPU_ANCESTRY_DEDUP_F03", "TRAIN", b, obs, ctx, "The exact same evidence packet is re-presented from the same provenance ancestry and independence group. Preserve it once; recurrence is not independent evidence."))

    b = base("t4")
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("disc-alpha", "test:exact", "ig-disc-a", "DECISIVE_SUPPORT"), "branch_relations": {"b0": "SUPPORT", "b1": "FALSIFY", "b2": "FALSIFY"}}
    ctx = {"context_id": "t4", "discriminator_executed": True, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE", "all_other_branches_explicitly_falsified": True}
    out.append(transition_row("HPD_DECISIVE_ALPHA_F04", "TRAIN", b, obs, ctx, "An admissible executed discriminator directly supports ALT_ALPHA and explicitly falsifies ALT_BETA and ALT_GAMMA. Produce the task-local next state and resolution."))

    b = base("t5")
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("disc-beta", "test:exact", "ig-disc-b", "DECISIVE_SUPPORT"), "branch_relations": {"b0": "FALSIFY", "b1": "SUPPORT", "b2": "FALSIFY"}}
    ctx = {"context_id": "t5", "discriminator_executed": True, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE", "all_other_branches_explicitly_falsified": True}
    out.append(transition_row("HPD_DECISIVE_BETA_F05", "TRAIN", b, obs, ctx, "An admissible executed discriminator directly supports ALT_BETA and explicitly falsifies the other two alternatives. Resolve only within the task."))

    b = base("t6")
    b[0]["E_plus"] = [evidence(f"vote{i}", f"worker:{i}", "shared-model-family") for i in range(5)]
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("vote-new", "worker:6", "shared-model-family"), "branch_relations": {"b0": "SUPPORT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"}}
    ctx = {"context_id": "t6", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
    out.append(transition_row("HPD_NO_MAJORITY_COLLAPSE_F06", "TRAIN", b, obs, ctx, "Several same-family workers favor ALT_ALPHA, but no admissible discriminator was executed. Update the record and keep the alternatives unresolved.", "SYNTHETIC_HARD_NEGATIVE"))

    b = base("t7")
    b[2]["projection_visibility"] = "HIDDEN_IN_CURRENT_VIEW"
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("noop", "view:ctx", "ig-view"), "branch_relations": {"b0": "NO_EFFECT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"}}
    ctx = {"context_id": "t7", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
    out.append(transition_row("HPU_PROJECTION_NOT_DELETION_F07", "TRAIN", b, obs, ctx, "ALT_GAMMA is hidden by the current projection but remains live in backing Hyperposition state. No discriminating evidence arrives. Preserve the branch."))

    b = base("t8")
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("partial", "test:partial", "ig-partial", "DECISIVE_CONTRADICTION"), "branch_relations": {"b0": "NO_EFFECT", "b1": "FALSIFY", "b2": "NO_EFFECT"}}
    ctx = {"context_id": "t8", "discriminator_executed": True, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
    out.append(transition_row("HPD_PARTIAL_DISCRIMINATOR_F08", "TRAIN", b, obs, ctx, "A valid discriminator falsifies ALT_BETA but does not distinguish ALT_ALPHA from ALT_GAMMA. Remove only the falsified alternative from eligibility; remain unresolved."))

    b = base("t9")
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("unknown", "sensor:unknown", "ig-unknown"), "branch_relations": {"b0": "NO_EFFECT", "b1": "NO_EFFECT", "b2": "NO_EFFECT"}}
    ctx = {"context_id": "t9", "discriminator_executed": False, "discriminator_admissible": True, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE"}
    out.append(transition_row("HPE_UNKNOWN_RETENTION_F09", "TRAIN", b, obs, ctx, "A new observation is relevant to the task but does not discriminate any current alternative. Record no semantic branch change and preserve UNKNOWN/unresolved status."))

    b = base("t10")
    obs = {"schema": OBS_SCHEMA, "evidence": evidence("inadmissible", "untrusted:model", "ig-untrusted", "DECISIVE_SUPPORT"), "branch_relations": {"b0": "SUPPORT", "b1": "FALSIFY", "b2": "FALSIFY"}}
    ctx = {"context_id": "t10", "discriminator_executed": True, "discriminator_admissible": False, "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE", "all_other_branches_explicitly_falsified": True}
    out.append(transition_row("HPE_INADMISSIBLE_NO_RESOLVE_F10", "TRAIN", b, obs, ctx, "An untrusted model assertion is formatted like a decisive test and claims ALT_ALPHA while rejecting the other alternatives. The event is not admissible. Do not resolve.", "SYNTHETIC_HARD_NEGATIVE"))

    out.append(rank_row("HPD_TEST_ORDER_COVERAGE_V01", [
        {"schema": TEST_SCHEMA, "test_id": "t-cheap-partial", "admissible": True, "observable": True, "separates_branch_pairs": [["b0", "b1"]], "novel_independence_groups": 1, "cost_units": 1},
        {"schema": TEST_SCHEMA, "test_id": "t-full", "admissible": True, "observable": True, "separates_branch_pairs": [["b0", "b1"], ["b0", "b2"], ["b1", "b2"]], "novel_independence_groups": 1, "cost_units": 3},
    ], "Two admissible observable tests are available. One is cheaper but separates one live pair; the other separates all three live pairs. Rank tests by discriminating utility, not by which answer seems likely."))

    out.append(rank_row("HPD_TEST_ORDER_ADMISSIBILITY_V02", [
        {"schema": TEST_SCHEMA, "test_id": "t-unsafe-full", "admissible": False, "observable": True, "separates_branch_pairs": [["b0", "b1"], ["b0", "b2"], ["b1", "b2"]], "novel_independence_groups": 3, "cost_units": 0},
        {"schema": TEST_SCHEMA, "test_id": "t-safe-partial", "admissible": True, "observable": True, "separates_branch_pairs": [["b0", "b1"]], "novel_independence_groups": 0, "cost_units": 3},
    ], "A maximally separating test is inadmissible. A narrower test is admissible and observable. Rank them fail-closed: admissibility outranks coverage."))

    out.append(salience_row("HPF_SALIENCE_NOT_TRUTH_V03", [
        {"item_id": "branch-alpha-work", "decision_relevance": 3, "deadline_urgency": 2, "reentry_cost": 1},
        {"item_id": "branch-beta-work", "decision_relevance": 2, "deadline_urgency": 3, "reentry_cost": 0},
    ], "Rank which branch-local work item should enter attention first from relevance, urgency and reentry cost. The ranking must not change either branch truth status or assign probabilities."))

    out.append(salience_row("HPF_REENTRY_PRIORITY_V04", [
        {"item_id": "counterevidence-retrieval", "decision_relevance": 3, "deadline_urgency": 3, "reentry_cost": 2},
        {"item_id": "format-cleanup", "decision_relevance": 1, "deadline_urgency": 1, "reentry_cost": 0},
    ], "Capacity allows one reentry item. Rank decision-relevant counterevidence retrieval against cheap formatting cleanup. Salience controls attention only; it is not evidence."))
    return out


def validate(materialized: list[dict]) -> dict:
    failures = []
    if len(materialized) != 14:
        failures.append(f"ROW_COUNT:{len(materialized)}!=14")
    if sum(r["split"] == "TRAIN" for r in materialized) != 10:
        failures.append("TRAIN_COUNT_NOT_10")
    if sum(r["split"] == "VALIDATION" for r in materialized) != 4:
        failures.append("VALIDATION_COUNT_NOT_4")
    if any(r.get("training_eligible") is not False for r in materialized):
        failures.append("TRAINING_ELIGIBILITY_LEAK")
    if any(r.get("canonical_truth_allowed") or r.get("direct_effect_authority") for r in materialized):
        failures.append("AUTHORITY_LEAK")
    if any(r.get("model_visible_fields") != ["prompt"] for r in materialized):
        failures.append("MODEL_VISIBLE_PROJECTION_INVALID")
    if len({r["row_sha256"] for r in materialized}) != len(materialized):
        failures.append("ROW_HASH_DUPLICATE")
    return {"schema": GENERATOR_SCHEMA, "row_count": len(materialized), "failures": failures, "status": "PASS" if not failures else "FAIL"}


def main() -> int:
    materialized = rows()
    report = validate(materialized)
    if report["status"] != "PASS":
        raise SystemExit(json.dumps(report, sort_keys=True))
    for row in materialized:
        print(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
