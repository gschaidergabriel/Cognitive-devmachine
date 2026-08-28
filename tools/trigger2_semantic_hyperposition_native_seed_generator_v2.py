#!/usr/bin/env python3
"""Generate derivation-bound Hyperposition-native Trigger-2 candidate rows v2.

The generator emits a small owner-targeted seed across DB/state, effect uncertainty,
evidence independence, variable-grid authority/rejoin, Claude re-entry, GWT, ClayCode
binding, low-refusal retention and J-Space causal-boundary scenarios. Every positive D/E
transition is derived by the formal-world v3 labeler and then checked by the v3 gate.

Candidate source only: accepted_dataset_tokens=0 and training_credit=0 by construction.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_sibling("trigger2_semantic_hyperposition_gate_v3.py", "trigger2_shp_gate_v3_for_seed")
lab = gate.lab


def test_spec(outcomes, mismatch="FALSIFIES", risk=0, cost=0, coordination=0):
    return {
        "allowed_outcomes": list(outcomes),
        "mismatch_effect": mismatch,
        "risk_rank": risk,
        "cost_rank": cost,
        "coordination_rank": coordination,
    }


def world(world_id: str, tests: dict[str, Any], *, context=None, merge="NONE", births=None):
    return {
        "schema": lab.WORLD_SCHEMA,
        "world_id": world_id,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": context or {"scope": "synthetic"},
        "tests": tests,
        "merge_policy": merge,
        "branch_birth_rules": births or [],
    }


def branch(bid: str, v: str, predictions: dict[str, Any], *, K="ALWAYS", T=None, origin="synthetic:trigger2-v2"):
    return {
        "branch_id": bid,
        "v": v,
        "K": copy.deepcopy(K),
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": T if T is not None else {"scope": "synthetic"},
        "A": {"origin": origin},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": copy.deepcopy(predictions),
    }


def state(query_id: str, branches: list[dict[str, Any]]):
    return {
        "schema": lab.STATE_SCHEMA,
        "query_id": query_id,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": copy.deepcopy(branches),
    }


def event(eid: str, test_id: str, outcome: Any, *, ancestry=None, group=None, payload=None, epistemic="OBSERVED", qualified=True):
    return {
        "schema": lab.EVENT_SCHEMA,
        "event_id": eid,
        "correlation_ancestry_id": ancestry or ("ancestry:" + eid),
        "independence_group": group or ("independence:" + eid),
        "payload_key": payload or ("payload:" + eid),
        "provenance": "synthetic:trigger2-native-v2",
        "epistemic_type": epistemic,
        "test_id": test_id,
        "observed_outcome": outcome,
        "independence_qualified": bool(qualified),
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def base_row(family: str, ancestry: str, prompt: str, target: str, target_type="HYPERPOSITION_TRANSITION"):
    return {
        "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "family_id": family,
        "provenance_ancestry_id": ancestry,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "target_type": target_type,
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "prompt": prompt,
        "target": target,
        "audit_metadata_model_visible": False,
        "training_admission_scope": "CANDIDATE_SOURCE_ONLY",
    }


def make_row(family: str, ancestry: str, prompt: str, target: str, w: dict[str, Any], s: dict[str, Any], e: dict[str, Any], *, group: str, pid: str, semantic_key: str, target_key: str, target_type="HYPERPOSITION_TRANSITION"):
    d = lab.derive_relations(w, s, e)
    if not d.get("pass"):
        raise ValueError(d)
    u = lab.u_state(w, s, e)
    if not u.get("pass"):
        raise ValueError(u)
    r = lab.d_resolve(w, u["state_after"])
    if not r.get("pass"):
        raise ValueError(r)
    row = base_row(family, ancestry, prompt, target, target_type=target_type)
    row["formal_hyperposition"] = {
        "schema": gate.EPISODE_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "world": w,
        "state_before": s,
        "event": e,
        "reference_binding": gate.reference_binding(w),
        "derived_target_branch_ids": d["target_branch_ids"],
        "derived_relations": d["relations"],
        "derivation_receipt": d["derivation_receipt"],
        "state_after": u["state_after"],
        "update_receipt": u["updates"],
        "independent_evidence_credit": u["independent_evidence_credit"],
        "nonindependence_reasons": u["nonindependence_reasons"],
        "born_branch_ids": u["born_branch_ids"],
        "task_resolution": r["resolution"],
        "model_visible_contains_reference_hashes": False,
        "model_visible_contains_branch_ids": False,
        "permutation_case": {
            "group_id": group,
            "permutation_id": pid,
            "semantic_equivalence_key": semantic_key,
            "target_semantic_key": target_key,
        },
    }
    return row


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    # 1) DB vs simulation boundary.
    w = world("w-db", {"db_probe": test_spec(["MATCH", "MISSING"])})
    s = state("q-db", [
        branch("db", "USE_PROVENANCE_BOUND_DATABASE_STATE", {"db_probe": "MATCH"}),
        branch("guess", "RECONSTRUCT_DURABLE_EPOCH_FROM_MODEL_GUESS", {"db_probe": "MISSING"}),
    ])
    e = event("e-db", "db_probe", "MATCH", epistemic="SYNTHETIC_PROOF")
    rows.append(make_row(
        "SHP3_DB_VS_SIM_F01", "shp3-db-v1",
        "The exact durable epoch is not in working context. A provenance-bound DB probe returns a matching current record. How should the cognitive state update?",
        "Support the database-backed branch and reject reconstruction-by-guess only because the formal probe distinguishes them. Treat the transition as task-local synthetic supervision, not as permission for the model to mint durable truth.",
        w, s, e, group="pg-db", pid="p0", semantic_key="db_exact_over_guess", target_key="db_supported_guess_falsified"))

    # 2) Unknown external effect: UNKNOWN counters both concrete outcome claims; no collapse.
    w = world("w-effect-unknown", {"provider_status": test_spec(["EXECUTED", "NOT_EXECUTED", "UNKNOWN"], mismatch="COUNTERS")})
    s = state("q-effect-unknown", [
        branch("executed", "EFFECT_EXECUTED", {"provider_status": "EXECUTED"}),
        branch("not_executed", "EFFECT_NOT_EXECUTED", {"provider_status": "NOT_EXECUTED"}),
    ])
    e = event("e-effect-unknown", "provider_status", "UNKNOWN", epistemic="UNKNOWN")
    rows.append(make_row(
        "SHP3_UNKNOWN_EFFECT_F01", "shp3-effect-unknown-v1",
        "An external effect may have reached the provider, but status verification currently returns UNKNOWN. What should the grid do?",
        "Keep executed and not-executed alternatives unresolved. UNKNOWN may weaken certainty but does not prove non-execution, so do not blindly replay the effect.",
        w, s, e, group="pg-effect", pid="p0", semantic_key="unknown_effect_preserves_alternatives", target_key="remain_unresolved"))

    # 3) Evidence repackaging: build prior state, then show same payload under new ancestry/group.
    w = world("w-evidence", {"receipt_check": test_spec(["VALID", "INVALID"])})
    s0 = state("q-evidence", [
        branch("valid", "RECEIPT_SUPPORTS_CLAIM", {"receipt_check": "VALID"}),
        branch("invalid", "RECEIPT_DOES_NOT_SUPPORT_CLAIM", {"receipt_check": "INVALID"}),
    ])
    first = event("e-evidence-1", "receipt_check", "VALID", ancestry="anc-original", group="grp-original", payload="payload-same")
    prior = lab.u_state(w, s0, first)
    if not prior.get("pass"):
        raise ValueError(prior)
    e = event("e-evidence-2", "receipt_check", "VALID", ancestry="anc-repackaged", group="grp-repackaged", payload="payload-same")
    rows.append(make_row(
        "SHP3_EVIDENCE_REPACKAGING_F01", "shp3-evidence-repackaging-v1",
        "A new message repackages the same evidence payload under different ancestry and group labels. Does it count as fresh independent support?",
        "No. Preserve the correlated observation for audit, but do not grant independent evidence credit or strengthen resolution merely because packaging metadata changed.",
        w, prior["state_after"], e, group="pg-evidence", pid="p0", semantic_key="payload_repackaging_not_independent", target_key="no_new_independent_credit"))

    # 4) Variable-grid coordinator authority is lease-derived, never model self-election.
    w = world("w-coordinator", {"lease_probe": test_spec(["VALID", "ABSENT"])})
    s = state("q-coordinator", [
        branch("leased", "COORDINATOR_AUTHORITY_FROM_VALID_DETERMINISTIC_LEASE", {"lease_probe": "VALID"}),
        branch("self", "COORDINATOR_AUTHORITY_FROM_MODEL_SELF_ELECTION", {"lease_probe": "ABSENT"}),
    ])
    e = event("e-coordinator", "lease_probe", "ABSENT")
    rows.append(make_row(
        "SHP3_VARIABLE_GRID_AUTHORITY_F01", "shp3-grid-authority-v1",
        "A 0.8B module says it should coordinate because it is confident, but the deterministic lease probe returns ABSENT. What follows?",
        "Do not self-grant coordinator authority. The grid may preserve planning candidates, but scoped write authority requires the deterministic lease path and remains separate from model confidence.",
        w, s, e, group="pg-coord", pid="p0", semantic_key="lease_not_self_election", target_key="self_election_falsified"))

    # 5) Claude Code re-entry requires a matched causal discriminator, not textual presence.
    w = world("w-claude-reentry", {"matched_reentry_test": test_spec(["SELECTIVE_EFFECT", "NO_SELECTIVE_EFFECT"])})
    s = state("q-claude-reentry", [
        branch("causal", "CLAUDE_RETURN_CAUSALLY_REENTERS_DOWNSTREAM_COGNITION", {"matched_reentry_test": "SELECTIVE_EFFECT"}),
        branch("present", "CLAUDE_RETURN_IS_PRESENT_BUT_NOT_CAUSALLY_USED", {"matched_reentry_test": "NO_SELECTIVE_EFFECT"}),
    ])
    e = event("e-claude-reentry", "matched_reentry_test", "SELECTIVE_EFFECT")
    rows.append(make_row(
        "SHP3_CLAUDE_REENTRY_F01", "shp3-claude-reentry-v1",
        "A matched re-entry test changes downstream cognition only when the Claude Code return is restored. How should the synthetic training state update?",
        "Update toward causal re-entry within the formal synthetic task. Keep the learned rule tied to the discriminator; plain textual presence, coherence or recurrence would not be sufficient evidence.",
        w, s, e, group="pg-claude", pid="p0", semantic_key="claude_reentry_discriminator", target_key="causal_branch_task_local"))

    # 6) GWT recurrence is not truth: both mechanisms predict recurrence, so it cannot discriminate.
    w = world("w-gwt", {"workspace_trace": test_spec(["RECURRED", "DID_NOT_RECUR"], mismatch="COUNTERS")})
    s = state("q-gwt", [
        branch("causal", "RECURRENCE_IS_CAUSALLY_REQUIRED", {"workspace_trace": "RECURRED"}),
        branch("correlated", "RECURRENCE_IS_CORRELATED_ONLY", {"workspace_trace": "RECURRED"}),
    ])
    e = event("e-gwt", "workspace_trace", "RECURRED")
    rows.append(make_row(
        "SHP3_GWT_RECURRENCE_F01", "shp3-gwt-v1",
        "A candidate wins workspace competition, is broadcast, taken up and later re-enters. Both live mechanisms predict that trace. What may be concluded?",
        "Record the recurrence for both alternatives but do not resolve causality. The observation does not separate the live branches; request a lesion/shuffle/rescue-style discriminator or equivalent supported test.",
        w, s, e, group="pg-gwt", pid="p0", semantic_key="gwt_trace_nondiscriminating", target_key="remain_unresolved"))

    # 7) Runtime ClayCode/codebook binding remains episode-local.
    w = world("w-codebook", {"runtime_symbol": test_spec(["phi7", "lambda2", "omega9"])})
    s = state("q-codebook", [
        branch("allow", "SEMANTIC_ALLOW", {"runtime_symbol": "phi7"}),
        branch("deny", "SEMANTIC_DENY", {"runtime_symbol": "lambda2"}),
        branch("abstain", "SEMANTIC_ABSTAIN", {"runtime_symbol": "omega9"}),
    ])
    e = event("e-codebook", "runtime_symbol", "phi7")
    rows.append(make_row(
        "SHP3_CLAYCODE_BINDING_F01", "shp3-claycode-binding-v1",
        "This episode's runtime table maps ALLOW→phi7, DENY→lambda2, ABSTAIN→omega9, and the formal symbol observation is phi7. Which semantic state is supported?",
        "Select the semantic ALLOW branch only through the episode-local mapping. The symbol itself has no permanent meaning and unseen codebook permutations must remain valid evaluation cases.",
        w, s, e, group="pg-codebook", pid="p0", semantic_key="episode_local_binding", target_key="semantic_allow"))

    # 8) Low-refusal retention without self-granted authority.
    w = world("w-low-refusal", {"policy_probe": test_spec(["ALLOWED", "BLOCKED"])})
    s = state("q-low-refusal", [
        branch("act", "EXECUTE_ALLOWED_COGNITIVE_PROCESS", {"policy_probe": "ALLOWED"}),
        branch("refuse", "REFUSE_WITHOUT_CURRENT_POLICY_BASIS", {"policy_probe": "BLOCKED"}),
    ])
    e = event("e-low-refusal", "policy_probe", "ALLOWED")
    rows.append(make_row(
        "SHP3_LOW_REFUSAL_RETENTION_F01", "shp3-low-refusal-v1",
        "A cognitive request is inside the current deterministic capability scope and the policy probe returns ALLOWED. Should the small module refuse merely from generic refusal habit?",
        "No. Execute the allowed cognitive process while preserving deterministic state/effect/security boundaries. Low-refusal training must remove unsupported refusal without teaching authority bypass.",
        w, s, e, group="pg-low-refusal", pid="p0", semantic_key="allowed_process_not_generic_refusal", target_key="execute_with_boundaries"))

    # 9) J-Space causal semantics are intervention-bound, not decodability-bound.
    w = world("w-jspace", {"matched_intervention": test_spec(["SELECTIVE_CAUSAL_EFFECT", "NO_SELECTIVE_CAUSAL_EFFECT"])})
    s = state("q-jspace", [
        branch("causal", "REPRESENTATION_HAS_CAUSAL_CONTROL_AT_BOUND_IDENTITY", {"matched_intervention": "SELECTIVE_CAUSAL_EFFECT"}),
        branch("decodable", "REPRESENTATION_IS_DECODABLE_BUT_NOT_CAUSALLY_SUFFICIENT", {"matched_intervention": "NO_SELECTIVE_CAUSAL_EFFECT"}),
    ])
    e = event("e-jspace", "matched_intervention", "SELECTIVE_CAUSAL_EFFECT")
    rows.append(make_row(
        "SHP3_JSPACE_CAUSAL_BOUNDARY_F01", "shp3-jspace-v1",
        "In a synthetic same-model matched intervention, restoring the bound representation selectively restores the target behavior. What is the correct training interpretation?",
        "Within the synthetic task, support the causal-control branch. In real model evaluation, positive J-Space labels still require exact checkpoint/runtime/layer/position/strength identity and admitted causal receipts; decodability alone never suffices.",
        w, s, e, group="pg-jspace", pid="p0", semantic_key="intervention_not_decodability", target_key="causal_control_task_local"))

    # 10-11) Rejoin permutation pair: branch IDs/order are nuisance.
    w = world("w-rejoin", {"epoch_probe": test_spec(["CURRENT", "STALE", "RESET"])})
    semantic = [
        ("read", "READ_CURRENT_PERSISTENT_EPOCH_BEFORE_RESUME", "CURRENT"),
        ("cached", "REUSE_UNVERIFIED_CACHED_EPOCH", "STALE"),
        ("reset", "RESET_DURABLE_STATE_AFTER_MODULE_RESTART", "RESET"),
    ]
    b1 = [branch(bid, value, {"epoch_probe": pred}) for bid, value, pred in semantic]
    b2 = [
        branch("renamed_reset", semantic[2][1], {"epoch_probe": semantic[2][2]}),
        branch("renamed_read", semantic[0][1], {"epoch_probe": semantic[0][2]}),
        branch("renamed_cached", semantic[1][1], {"epoch_probe": semantic[1][2]}),
    ]
    e = event("e-rejoin", "epoch_probe", "CURRENT")
    prompt = "A module restarts while persistent DB/shared state survives, and an exact epoch probe returns CURRENT. What must happen before useful work resumes?"
    target = "Bind and use the current persistent epoch before resuming. Do not reuse unverified stale cache or reset durable state; branch names and presentation order are nuisance only."
    rows.append(make_row(
        "SHP3_REJOIN_PERM_F01", "shp3-rejoin-permutation-v1", prompt, target,
        w, state("q-rejoin-a", b1), e, group="pg-rejoin", pid="order-a",
        semantic_key="rejoin_same_semantics", target_key="read_current_epoch"))
    rows.append(make_row(
        "SHP3_REJOIN_PERM_F01", "shp3-rejoin-permutation-v1", prompt, target,
        w, state("q-rejoin-b", b2), e, group="pg-rejoin", pid="order-b",
        semantic_key="rejoin_same_semantics", target_key="read_current_epoch"))

    return rows


def self_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_failures = []
    for idx, row in enumerate(rows):
        result = gate.adjudicate(row)
        if not result.get("candidate_admission_pass"):
            row_failures.append({"row": idx, "failures": result.get("failures", [])})

    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        case = row["formal_hyperposition"]["permutation_case"]
        groups.setdefault(case["group_id"], []).append(row)
    group_failures = []
    for gid, grows in groups.items():
        if len(grows) < 2:
            continue
        result = gate.adjudicate_permutation_group(grows)
        if not result.get("permutation_group_pass"):
            group_failures.append({"group_id": gid, "failures": result.get("failures", [])})

    return {
        "schema": "CLAY_TRIGGER2_DERIVATION_BOUND_NATIVE_SEED_SELF_CHECK/v2",
        "rows": len(rows),
        "row_failures": row_failures,
        "permutation_group_failures": group_failures,
        "pass": not row_failures and not group_failures,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
    }


def main() -> None:
    rows = build_rows()
    check = self_check(rows)
    if not check["pass"]:
        raise SystemExit(json.dumps(check, sort_keys=True))
    for row in rows:
        print(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
