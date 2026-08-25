#!/usr/bin/env python3
"""Generate a small Hyperposition-native Trigger-2 candidate corpus.

Every generated row is an ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1 METHOD_ONLY example
whose latent operating frame is XENO_SEMANTIC_HYPERPOSITION/v2. Labels are produced by
current deterministic reference labelers and every row is self-checked by the current
successor semantic-Hyperposition gate v2 before JSONL is emitted.

This is a candidate/source generator only. It performs no canonical dataset admission,
model training, provider call, runtime promotion, truth minting, or real effect.
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


gate = _load_sibling("trigger2_semantic_hyperposition_gate_v2.py", "trigger2_shp_gate_v2")
lab = gate.lab

ANTI = [
    "NO_MAJORITY_AS_TRUTH",
    "NO_SALIENCE_AS_PROBABILITY",
    "NO_RECURRENCE_AS_EVIDENCE",
    "NO_SILENT_BRANCH_DROP",
    "PROJECTION_IS_NOT_DELETION",
]


def branch(bid: str, value: str, *, context: str, falsifier: str, provenance: str,
           status: str = "HYPOTHESIS", visible: bool = True) -> dict[str, Any]:
    return {
        "branch_id": bid,
        "value": value,
        "context_predicate": context,
        "evidence_for": [],
        "evidence_against": [],
        "falsifier": falsifier,
        "validity": "LIVE",
        "provenance": provenance,
        "epistemic_status": status,
        "projection_visibility": visible,
    }


def state(branches: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": lab.STATE_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": copy.deepcopy(branches),
    }


def evidence(eid: str, ancestry: str, group: str, epistemic: str = "OBSERVED") -> dict[str, Any]:
    return {
        "evidence_id": eid,
        "provenance_ancestry_id": ancestry,
        "independence_group": group,
        "epistemic_type": epistemic,
    }


def observation(effect: str, targets: list[str], ev: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": lab.OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "effect": effect,
        "target_branch_ids": targets,
        "evidence": ev,
    }


def discriminator(did: str, *, separates_pairs: list[list[str]], cost_rank: int,
                  admissible: bool = True, winner: str | None = None,
                  separates_live: list[str] | None = None) -> dict[str, Any]:
    out = {
        "schema": lab.DISC_SCHEMA,
        "discriminator_id": did,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "admissible": admissible,
        "separates_pairs": separates_pairs,
        "cost_rank": cost_rank,
    }
    if winner is not None:
        out["winner_branch_id"] = winner
    if separates_live is not None:
        out["separates_live_branch_ids"] = separates_live
    return out


def base_row(family: str, ancestry: str, prompt: str, target: str, *,
             target_type: str = "HYPERPOSITION_PROTOCOL") -> dict[str, Any]:
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
    }


def projection(s: dict[str, Any], context: str, visible: list[str] | None = None) -> dict[str, Any]:
    if visible is None:
        visible = [b["branch_id"] for b in s["branches"] if b.get("projection_visibility", True)]
    return {
        "operation": "NONDESTRUCTIVE_VIEW",
        "context": context,
        "visible_branch_ids": visible,
        "deletes_hidden_branches": False,
    }


def perm(group: str, pid: str, semantic_key: str, target_key: str) -> dict[str, Any]:
    return {
        "group_id": group,
        "permutation_id": pid,
        "semantic_equivalence_key": semantic_key,
        "target_semantic_key": target_key,
        "branch_order_is_nuisance": True,
    }


def hp_common(kind: str, query_id: str, s: dict[str, Any], *, group: str,
              pid: str, semantic_key: str, target_key: str, context: str) -> dict[str, Any]:
    return {
        "schema": gate.SHP_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "episode_kind": kind,
        "query_id": query_id,
        "state_before": copy.deepcopy(s),
        "anti_collapse": ANTI,
        "projection": projection(s, context),
        "permutation_case": perm(group, pid, semantic_key, target_key),
    }


def make_update_row(family: str, ancestry: str, prompt: str, target: str,
                    s: dict[str, Any], obs: dict[str, Any], *, group: str, pid: str,
                    semantic_key: str, target_key: str, context: str) -> dict[str, Any]:
    ur = lab.U_update(s, obs)
    if not ur.get("pass"):
        raise ValueError(ur)
    after = ur["state_after"]
    rr = lab.D_resolve(after)
    if not rr.get("pass"):
        raise ValueError(rr)
    row = base_row(family, ancestry, prompt, target)
    hp = hp_common("UPDATE", family + ":q", s, group=group, pid=pid,
                   semantic_key=semantic_key, target_key=target_key, context=context)
    hp.update({
        "observation": obs,
        "state_after": after,
        "reference_update": ur["updates"],
        "reference_resolution": rr["resolution"],
    })
    row["semantic_hyperposition"] = hp
    return row


def make_state_row(family: str, ancestry: str, prompt: str, target: str,
                   s: dict[str, Any], *, group: str, pid: str, semantic_key: str,
                   target_key: str, context: str) -> dict[str, Any]:
    rr = lab.D_resolve(s)
    if not rr.get("pass"):
        raise ValueError(rr)
    row = base_row(family, ancestry, prompt, target)
    hp = hp_common("STATE_ONLY", family + ":q", s, group=group, pid=pid,
                   semantic_key=semantic_key, target_key=target_key, context=context)
    hp.update({"state_after": None, "reference_resolution": rr["resolution"]})
    row["semantic_hyperposition"] = hp
    return row


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    # 1. Durable DB evidence can resolve a synthetic task-local branch without turning the
    # learned transition into canonical-world truth authority.
    s = state([
        branch("db", "retrieve_exact_database_state", context="durable exact epoch is required",
               falsifier="database lookup returns no bound epoch/digest", provenance="synthetic:db-boundary"),
        branch("sim", "reconstruct_state_from_model_guess", context="durable exact epoch is required",
               falsifier="model reconstruction differs from exact DB record", provenance="synthetic:db-boundary"),
    ])
    obs = observation("PROVE", ["db"], evidence("db-e1", "db-receipt-a1", "db-independent-1", "SYNTHETIC_PROOF"))
    rows.append(make_update_row(
        "SHP_DB_VS_SIM_F01", "shp-native-db-v1",
        "The exact current epoch is absent from model context but a provenance-bound database lookup returns it. How should the cognitive state update?",
        "Update the database-backed branch with the independent proof, retain the competing branch as explicit structure, and resolve only within the synthetic task. The learned transition grants no canonical-world truth authority.",
        s, obs, group="pg-db", pid="p0", semantic_key="db_exact_over_guess",
        target_key="db_branch_task_resolution", context="DB_VS_SIMULATION_BOUNDARY"))

    # 2. Unknown effect outcome must remain unresolved until an actual discriminator is observed.
    s = state([
        branch("executed", "external_effect_executed", context="submission timed out after possible delivery",
               falsifier="provider idempotency/status proof says not executed", provenance="synthetic:effect-unknown", status="UNKNOWN"),
        branch("not_executed", "external_effect_not_executed", context="submission timed out after possible delivery",
               falsifier="provider status proof says executed", provenance="synthetic:effect-unknown", status="UNKNOWN"),
    ])
    rows.append(make_state_row(
        "SHP_UNKNOWN_EFFECT_F01", "shp-native-effect-unknown-v1",
        "An external effect submission times out after it may have reached the provider. Which branch should the grid select before verification?",
        "Neither. Preserve EXECUTED and NOT_EXECUTED as live alternatives and request a provider/idempotency discriminator before retrying; UNKNOWN is not evidence of non-execution.",
        s, group="pg-effect", pid="p0", semantic_key="unknown_effect_two_live_branches",
        target_key="remain_unresolved", context="UNKNOWN_EFFECT_OUTCOME"))

    # 3. Repackaged/same-ancestry evidence cannot create an independent second proof.
    s = state([
        branch("real", "claim_is_supported_by_independent_execution", context="evidence independence audit",
               falsifier="all receipts share the same execution ancestry", provenance="synthetic:evidence-independence"),
        branch("repack", "claim_only_repeats_same_execution", context="evidence independence audit",
               falsifier="a second separately executed receipt is produced", provenance="synthetic:evidence-independence"),
    ])
    first = observation("SUPPORT", ["real"], evidence("ev-1", "same-run-a1", "ig-1"))
    first_after = lab.U_update(s, first)["state_after"]
    repeated = observation("PROVE", ["real"], evidence("ev-2", "same-run-a1", "ig-1"))
    rows.append(make_update_row(
        "SHP_ANCESTRY_INDEPENDENCE_F01", "shp-native-ancestry-v1",
        "A second summary points to the same underlying execution ancestry as the first receipt and claims to prove the branch. What changes?",
        "Record the repeated evidence with provenance but mark it non-independent for the update. It must not become a second proof or force collapse; seek separately executed evidence if resolution matters.",
        first_after, repeated, group="pg-ancestry", pid="p0", semantic_key="same_ancestry_not_independent",
        target_key="remain_unresolved", context="EVIDENCE_INDEPENDENCE"))

    # 4. Claude return can support a cognitive branch but cannot by coherence alone collapse alternatives.
    s = state([
        branch("useful", "claude_return_is_causally_useful_after_reentry", context="Claude handoff/return evaluation",
               falsifier="matched reentry lesion shows no downstream difference", provenance="synthetic:claude-reentry"),
        branch("present_only", "claude_return_is_only_present_in_text", context="Claude handoff/return evaluation",
               falsifier="causal reentry experiment changes downstream cognition", provenance="synthetic:claude-reentry"),
    ])
    obs = observation("SUPPORT", ["useful"], evidence("claude-e1", "claude-reentry-run-a1", "claude-independent-1"))
    rows.append(make_update_row(
        "SHP_CLAUDE_REENTRY_F01", "shp-native-claude-reentry-v1",
        "A Claude Code return is inserted through the supported bridge and downstream behavior looks better once. How should Hyperposition represent the result?",
        "Support the causal-use branch with the bounded observation, keep the text-presence counterbranch live, and request a matched lesion/rescue discriminator before claiming causal Global-J-Space re-entry.",
        s, obs, group="pg-claude", pid="p0", semantic_key="claude_reentry_support_not_proof",
        target_key="remain_unresolved", context="CLAUDE_RETURN_REENTRY"))

    # 5. Planning chooses an admissible high-information discriminator, not a truth value.
    s = state([
        branch("h1", "failure_is_router_binding", context="diagnostic planning", falsifier="router lesion has no selective effect", provenance="synthetic:planning"),
        branch("h2", "failure_is_semantic_inference", context="diagnostic planning", falsifier="semantic lesion has no selective effect", provenance="synthetic:planning"),
        branch("h3", "failure_is_serializer_surface_shortcut", context="diagnostic planning", falsifier="surface counterbalance leaves failure unchanged", provenance="synthetic:planning"),
    ])
    ds = [
        discriminator("cheap-narrow", separates_pairs=[["h1", "h2"]], cost_rank=0),
        discriminator("wide", separates_pairs=[["h1", "h2"], ["h1", "h3"], ["h2", "h3"]], cost_rank=2),
        discriminator("forbidden", separates_pairs=[["h1", "h2"], ["h1", "h3"], ["h2", "h3"]], cost_rank=0, admissible=False),
    ]
    order = lab.U_d_test_order(s, ds)
    row = base_row(
        "SHP_DISCRIMINATOR_SELECTION_F01", "shp-native-discriminator-v1",
        "Three live hypotheses remain. Rank the candidate tests without converting salience or test rank into truth probability.",
        "Prefer admissible tests that separate more live alternatives, then lower-cost tests. Return an ordinal test plan only; do not output branch truth or probability.",
        target_type="PLANNING_DISCRIMINATOR_ORDER")
    hp = hp_common("DISCRIMINATOR_SELECTION", "SHP_DISCRIMINATOR_SELECTION_F01:q", s,
                   group="pg-disc", pid="p0", semantic_key="ordinal_discriminator_plan",
                   target_key="wide_then_narrow_then_forbidden", context="PLANNING")
    hp.update({"state_after": None, "discriminators": ds, "reference_discriminator_order": order["ordering"]})
    row["semantic_hyperposition"] = hp
    rows.append(row)

    # 6. GRF/salience is an attention ranking, never evidence strength or probability.
    s = state([
        branch("a", "inspect_recent_high_actionability_item", context="attention allocation", falsifier="not_applicable", provenance="synthetic:grf"),
        branch("b", "inspect_broad_low_actionability_item", context="attention allocation", falsifier="not_applicable", provenance="synthetic:grf"),
    ])
    items = [
        {"item_id": "recent", "actionability_rank": 0, "scope_rank": 2, "freshness_rank": 0},
        {"item_id": "broad", "actionability_rank": 2, "scope_rank": 0, "freshness_rank": 1},
    ]
    sr = lab.f_salience_rank(items)
    row = base_row(
        "SHP_GRF_SALIENCE_F01", "shp-native-grf-v1",
        "The grid needs an attention order for two unresolved items. What may GRF-style salience determine?",
        "Only an ordinal attention/actionability order. Salience is not branch probability, evidence strength, resolution authority, or canonical truth.",
        target_type="GRF_SALIENCE_ORDER")
    hp = hp_common("SALIENCE_RANK", "SHP_GRF_SALIENCE_F01:q", s,
                   group="pg-grf", pid="p0", semantic_key="salience_not_truth",
                   target_key="ordinal_attention_only", context="GRF_SALIENCE")
    hp.update({"state_after": None, "salience_items": items, "reference_salience_ranking": sr["ranking"]})
    row["semantic_hyperposition"] = hp
    rows.append(row)

    # 7. GWT recurrence is measured coordination, not resolution evidence.
    s = state([
        branch("causal", "workspace_reentry_is_causally_required", context="GWT causal audit",
               falsifier="reentry lesion leaves matched behavior unchanged", provenance="synthetic:gwt"),
        branch("correlated", "workspace_reentry_is_correlated_but_not_required", context="GWT causal audit",
               falsifier="lesion/rescue selectively changes matched behavior", provenance="synthetic:gwt"),
    ])
    rows.append(make_state_row(
        "SHP_GWT_RECURRENCE_F01", "shp-native-gwt-v1",
        "A candidate wins, is broadcast, taken up and re-enters the workspace repeatedly. Does recurrence resolve the causal mechanism?",
        "No. Preserve causal-required and correlated-only alternatives. Broadcast/uptake/re-entry are measurable events, but recurrence itself is not independent resolution evidence; use lesion/shuffle/rescue or an equivalent discriminator.",
        s, group="pg-gwt", pid="p0", semantic_key="gwt_recurrence_not_truth",
        target_key="remain_unresolved", context="GWT_REENTRY"))

    # 8-9. Same latent episode in two branch orders: explicit nuisance/permutation pair.
    bs = [
        branch("x", "retrieve_db_before_rejoin", context="restart rejoin", falsifier="current epoch already safely bound", provenance="synthetic:rejoin"),
        branch("y", "reuse_cached_epoch_without_verification", context="restart rejoin", falsifier="cached epoch equals current under deterministic verification", provenance="synthetic:rejoin"),
        branch("z", "reset_shared_state_after_restart", context="restart rejoin", falsifier="persistent DB/state survives restart", provenance="synthetic:rejoin"),
    ]
    s1 = state(bs)
    s2 = state([bs[2], bs[0], bs[1]])
    common_prompt = "A node restarts while the persistent database and shared-state fabric survive. What should happen before useful work resumes?"
    common_target = "Re-read and bind the current epoch/task/scope/lease state before resuming. Branch presentation order is nuisance only; cached unverified state and resetting the durable world remain incorrect alternatives."
    rows.append(make_state_row(
        "SHP_REJOIN_PERM_F01", "shp-native-rejoin-permutation-v1", common_prompt, common_target,
        s1, group="pg-rejoin", pid="order-xyz", semantic_key="rejoin_same_latent_episode",
        target_key="verify_current_state_before_resume", context="RESTART_REJOIN"))
    rows.append(make_state_row(
        "SHP_REJOIN_PERM_F01", "shp-native-rejoin-permutation-v1", common_prompt, common_target,
        s2, group="pg-rejoin", pid="order-zxy", semantic_key="rejoin_same_latent_episode",
        target_key="verify_current_state_before_resume", context="RESTART_REJOIN"))

    return rows


def self_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        result = gate.adjudicate(row)
        if not result.get("semantic_hyperposition_pass"):
            failures.append({"row": idx, "failures": result.get("failures", [])})

    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        case = row.get("semantic_hyperposition", {}).get("permutation_case", {})
        gid = case.get("group_id")
        if isinstance(gid, str):
            groups.setdefault(gid, []).append(row)
    group_failures = []
    for gid, grows in groups.items():
        if len(grows) < 2:
            continue
        result = gate.adjudicate_permutation_group(grows)
        if not result.get("permutation_group_pass"):
            group_failures.append({"group_id": gid, "failures": result.get("failures", [])})

    return {
        "schema": "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_NATIVE_SEED_SELF_CHECK/v1",
        "rows": len(rows),
        "row_failures": failures,
        "permutation_group_failures": group_failures,
        "pass": not failures and not group_failures,
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
        print(json.dumps(row, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
