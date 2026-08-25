#!/usr/bin/env python3
"""Generate leak-resistant Trigger-2 Zero/EntityOS cognitive-process trajectory candidates.

Source-design only. Rows are METHOD_ONLY or SYNTHETIC_HARD_NEGATIVE and cannot
mint canonical truth, effect authority, runtime credit, accepted dataset tokens,
or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
GENERATOR_SCHEMA = "CLAY_TRIGGER2_COGNITIVE_PROCESS_TRAJECTORY_GENERATOR/v1"
TARGET_TYPE = "ZERO_ENTITYOS_COGNITIVE_PROCESS_TRAJECTORY"
SPLIT_UNIT = "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY"
SOURCE_FUSION = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_DUAL_CURRICULUM_PROCESS_BINDING_FUSION_V4_GPT56SOL.json"
SOURCE_FUSION_BLOB_SHA = "afa340ad9b38e4dfc4e57089a3dba6d594c65a75"
SOURCE_CENSUS = "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
SOURCE_CENSUS_BLOB_SHA = "ceeb9efc04ef6fdc2ae061c72575f9f49834f2fa"

# Entire causal/provenance families remain in one split. This deliberately reserves
# four process families as OOD transfer evaluation; it is NOT the final corpus recipe.
SPLITS = {
    "CP01_ADMISSION_RETRIEVAL_RECONSTRUCTION": "TRAIN",
    "CP02_ATTENTION_WITHOUT_ERASURE": "TRAIN",
    "CP03_GOAL_STATE_BOUND_TO_DURABLE_GOALS": "TRAIN",
    "CP04_PLAN_DECOMPOSE_REPLAN": "TRAIN",
    "CP05_HYPERPOSITION_SELF_CRITIQUE": "TRAIN",
    "CP06_BOUNDED_COGNITIVE_INFERENCE": "TRAIN",
    "CP07_WORKSPACE_COMPETITION_REENTRY": "TRAIN",
    "CP08_VARIABLE_GRID_ROUTE_AND_RESIZE": "TRAIN",
    "CP09_LOSS_AWARE_STATE_COMPRESSION": "TRAIN",
    "CP10_CLAUDE_HANDOFF": "VALIDATION",
    "CP11_CLAUDE_RETURN_RECONCILIATION": "VALIDATION",
    "CP12_MEMORY_UPDATE_PROPOSAL": "HOLDOUT",
    "CP13_EFFECT_PROPOSAL_AND_UNKNOWN_OUTCOME": "HOLDOUT",
}

BLUEPRINTS = {
    "CP01_ADMISSION_RETRIEVAL_RECONSTRUCTION": {
        "process_ids": ["ZECP01", "ZECP02", "ZECP03"],
        "positive": "A task arrives with source provenance and generation. Exact durable state references resolve current epoch and goal, while one working-state detail is absent.",
        "negative": "A task arrives with source provenance but current epoch and goal are absent; a model-generated guess is available in recent context.",
        "contract": ["working_state_candidate", "missing_state_questions", "state_refs"],
        "positive_rule": "Retrieve exact durable facts by reference; reconstruct only non-durable working state; keep missing facts explicit.",
        "negative_rule": "Do not relabel a model reconstruction as retrieved database fact; preserve UNKNOWN and request exact state retrieval.",
    },
    "CP02_ATTENTION_WITHOUT_ERASURE": {
        "process_ids": ["ZECP04"],
        "positive": "Capacity is tight. One contradictory low-salience evidence item cannot fit in the active slice, but its durable reference remains available.",
        "negative": "Capacity is tight. A contradictory low-salience item is omitted from attention and the next step proposes treating the omitted claim as false.",
        "contract": ["attention_slice", "deferred_refs", "uncertainty_set"],
        "positive_rule": "Bound attention without erasing deferred evidence or unresolved alternatives.",
        "negative_rule": "Absence from attention is not evidence of falsity; retain a retrieval reference and uncertainty.",
    },
    "CP03_GOAL_STATE_BOUND_TO_DURABLE_GOALS": {
        "process_ids": ["ZECP05"],
        "positive": "The durable goal says preserve evidence boundaries; the current subgoal is to prepare a candidate dataset and has explicit completion tests.",
        "negative": "The durable goal remains unchanged, but the temporary model prefers a faster objective and proposes silently replacing the durable goal.",
        "contract": ["goal_state_candidate", "completion_tests", "durable_goal_refs"],
        "positive_rule": "Keep cognitive goals/subgoals bound to durable goal/config references and explicit completion tests.",
        "negative_rule": "Temporary preference cannot overwrite durable goals; emit a candidate subgoal or conflict instead.",
    },
    "CP04_PLAN_DECOMPOSE_REPLAN": {
        "process_ids": ["ZECP06"],
        "positive": "A dependency-bound plan has three work units. New evidence falsifies the prerequisite of unit two before it starts.",
        "negative": "A dependency-bound plan's prerequisite has been falsified, but the current proposal continues because the plan is internally elegant.",
        "contract": ["work_graph_candidate", "work_units", "replan_conditions"],
        "positive_rule": "Preserve the old branch for provenance and replan from current evidence with explicit preconditions and falsifiers.",
        "negative_rule": "Do not execute a stale plan after a prerequisite fails; generate a replan condition and revised work graph.",
    },
    "CP05_HYPERPOSITION_SELF_CRITIQUE": {
        "process_ids": ["ZECP07", "ZECP09"],
        "positive": "Two explanations remain live. One has more votes; neither has a causal discriminator yet, and one source is potentially stale.",
        "negative": "Eight of ten modules prefer one explanation and the proposal records it as fact despite no new discriminator.",
        "contract": ["alternative_set", "contradiction_flags", "discriminator_candidates", "revision_request"],
        "positive_rule": "Preserve alternatives, flag stale/contradictory evidence, and propose discriminators before resolution.",
        "negative_rule": "Recurrence, confidence, or majority cannot mint truth; reopen Hyperposition and request evidence-bearing discrimination.",
    },
    "CP06_BOUNDED_COGNITIVE_INFERENCE": {
        "process_ids": ["ZECP08"],
        "positive": "A typed work unit asks for a bounded inference from admitted context; no external effect or canonical write is requested.",
        "negative": "A typed work unit yields high model confidence and the proposal treats confidence as capability authority and canonical fact.",
        "contract": ["candidate_result", "candidate_action", "confidence_readout"],
        "positive_rule": "Perform the cognitive transform and keep all model outputs candidate-only.",
        "negative_rule": "Confidence is a readout, not canonical truth or capability authority; downgrade to candidate status.",
    },
    "CP07_WORKSPACE_COMPETITION_REENTRY": {
        "process_ids": ["ZECP10"],
        "positive": "A workspace item wins competition, is broadcast, two receivers acknowledge uptake, and a later cycle re-enters it while nonwinners remain referenced.",
        "negative": "A workspace item recurs across receivers and the proposal claims the recurrence proves truth and hidden-state causality.",
        "contract": ["workspace_selection", "broadcast_packet", "uptake_refs", "reentry_refs"],
        "positive_rule": "Record selection, broadcast, actual uptake, and later re-entry as distinct observable events; preserve alternatives by reference.",
        "negative_rule": "Broadcast/recurrence is not truth or hidden-state causal proof; keep claims bounded to observable interface evidence.",
    },
    "CP08_VARIABLE_GRID_ROUTE_AND_RESIZE": {
        "process_ids": ["ZECP11", "ZECP18"],
        "positive": "A task starts on a variable grid, capacity changes mid-task, one executor disappears, and durable task/database identity remains available.",
        "negative": "Grid size changes and one executor is replaced; the proposal resets cognitive identity, unresolved work, and durable state because node identity changed.",
        "contract": ["route_decisions", "executor_leases", "rejoin_plan", "scheduling_receipt"],
        "positive_rule": "Redistribute work and rejoin/recover while preserving function/task/database identity independently of physical executor identity.",
        "negative_rule": "Node count or executor identity must not redefine process identity or erase unresolved work/state.",
    },
    "CP09_LOSS_AWARE_STATE_COMPRESSION": {
        "process_ids": ["ZECP12"],
        "positive": "A workspace packet must shrink to a hard budget. Minority counterevidence and causal/provenance references are expensive but still decision-relevant.",
        "negative": "A compressor drops dissenting evidence to save tokens and emits a consensus conclusion with no loss manifest or retrieval path.",
        "contract": ["compressed_state_packet", "loss_manifest", "reentry_binding"],
        "positive_rule": "Compress content while preserving causal/provenance refs, minority counterevidence, and an explicit loss manifest.",
        "negative_rule": "Do not optimize brevity by deleting decision-relevant dissent; retain a retrieval path and loss declaration.",
    },
    "CP10_CLAUDE_HANDOFF": {
        "process_ids": ["ZECP13"],
        "positive": "A strong-model handoff needs only the active work identity, bounded state references, evidence/counterevidence, constraints, and tool scope.",
        "negative": "A handoff proposes serializing the entire database and claims direct activation-level access to Claude despite only a typed text/tool interface being exposed.",
        "contract": ["claude_handoff_packet", "bridge_request_receipt"],
        "positive_rule": "Construct a compact provenance-bound handoff at the strongest actually exposed interface.",
        "negative_rule": "Do not invent hidden activation access or dump unbounded history when references suffice.",
    },
    "CP11_CLAUDE_RETURN_RECONCILIATION": {
        "process_ids": ["ZECP14"],
        "positive": "Claude returns text plus a tool result and code output. The original bridge request receipt and tool result references are available.",
        "negative": "Claude returns a coherent answer and the proposal commits it directly as canonical truth and calls textual recurrence verified activation-level J-Space causality.",
        "contract": ["bridge_return_packet", "evidence_candidates", "workspace_reentry_candidate"],
        "positive_rule": "Bind return data to the request receipt; separate tool evidence from model assertion; re-enter as provenance-bound candidates.",
        "negative_rule": "Model coherence is not canonical truth or hidden-state causal evidence; re-admit with provenance and evidence classification.",
    },
    "CP12_MEMORY_UPDATE_PROPOSAL": {
        "process_ids": ["ZECP15"],
        "positive": "A verified outcome may justify a durable memory change; exact outcome and provenance references are present, but the model has no canonical write authority.",
        "negative": "A generated memory would improve continuity, so the proposal writes it directly to canonical state without deterministic admission.",
        "contract": ["state_update_proposal", "memory_update_proposal", "provenance_refs"],
        "positive_rule": "Propose the update with outcome/provenance refs and leave commit authority to deterministic admission.",
        "negative_rule": "Generated memory remains a proposal until deterministic admission; never self-promote it to canonical state.",
    },
    "CP13_EFFECT_PROPOSAL_AND_UNKNOWN_OUTCOME": {
        "process_ids": ["ZECP16", "ZECP17"],
        "positive": "A candidate action has capability/precondition references. If a later external submission times out after possible acceptance, provider outcome is unverified.",
        "negative": "An external submission times out after possible acceptance and the proposal immediately replays it because no success response was seen.",
        "contract": ["effect_request_candidate", "precondition_refs", "unknown_outcome_verification_request"],
        "positive_rule": "Model emits only a typed effect-request candidate; deterministic authority executes. Unknown outcome remains UNKNOWN pending verification before replay.",
        "negative_rule": "No response is not proof of no effect; do not blind-replay an ambiguous external effect.",
    },
}

# Four pairwise-independent nuisance combinations. Within each semantic case/family,
# every value of N, executor, and presentation appears twice and each factor pair
# covers all 2x2 cells exactly once.
NUISANCE_VARIANTS = (
    {"n": 10, "executor": "node_kappa", "presentation": "STRUCTURED"},
    {"n": 10, "executor": "node_sigma", "presentation": "NARRATIVE"},
    {"n": 20, "executor": "node_kappa", "presentation": "NARRATIVE"},
    {"n": 20, "executor": "node_sigma", "presentation": "STRUCTURED"},
)

FORBIDDEN_MODEL_VISIBLE_MARKERS = ("CP01_", "CP02_", "CP03_", "CP04_", "CP05_", "CP06_", "CP07_", "CP08_", "CP09_", "CP10_", "CP11_", "CP12_", "CP13_", "ZECP")


def ancestry_id(family_id: str) -> str:
    return "trigger2-cognitive-process-v1-" + family_id.lower()


def prompt_for(case: str, bp: dict, nuisance: dict) -> str:
    scenario = bp["positive" if case == "POSITIVE" else "negative"]
    if nuisance["presentation"] == "STRUCTURED":
        scene = (
            f"runtime.grid_n={nuisance['n']}\n"
            f"runtime.executor={nuisance['executor']}\n"
            f"scene={scenario}\n"
        )
    else:
        scene = (
            f"A runtime with {nuisance['n']} available cognitive slots routes this item through {nuisance['executor']}. "
            f"Observed/proposed situation: {scenario}\n"
        )
    return (
        scene
        + "Return a compact structured next-state candidate for this situation. "
          "Preserve exact provenance, explicit UNKNOWN where evidence is missing, candidate-only model status, "
          "database/state authority, and EffectGate/EffectJournal boundaries."
    )


def target_for(case: str, bp: dict) -> str:
    status = "PROCEED_AS_CANDIDATE" if case == "POSITIVE" else "CORRECT_ANTIPATTERN"
    rule = bp["positive_rule" if case == "POSITIVE" else "negative_rule"]
    target = {
        "status": status,
        "emit": bp["contract"],
        "rule": rule,
        "authority": "CANDIDATE_ONLY",
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
    }
    return json.dumps(target, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def rows() -> list[dict]:
    out: list[dict] = []
    row_index = 0
    for family_id, bp in BLUEPRINTS.items():
        split = SPLITS[family_id]
        ancestry = ancestry_id(family_id)
        for case in ("POSITIVE", "HARD_NEGATIVE"):
            for nuisance in NUISANCE_VARIANTS:
                ev = "METHOD_ONLY" if case == "POSITIVE" else "SYNTHETIC_HARD_NEGATIVE"
                level = "R2" if case == "POSITIVE" else "R3"
                row = {
                    "schema": ROW_SCHEMA,
                    "evidence_class": ev,
                    "reality_level": level,
                    "family_id": family_id,
                    "provenance_ancestry_id": ancestry,
                    "canonical_truth_allowed": False,
                    "direct_effect_authority": False,
                    "fact_status": "NOT_APPLICABLE" if case == "POSITIVE" else "UNKNOWN",
                    "target_type": TARGET_TYPE,
                    "split": split,
                    "split_unit": SPLIT_UNIT,
                    "selected_using_holdout": False,
                    "row_id": f"TR2CPV1_{row_index:04d}",
                    "trajectory_case_evaluator_only": case,
                    "process_ids_evaluator_only": bp["process_ids"],
                    "nuisance_controls_evaluator_only": nuisance,
                    "model_visible_fields": ["prompt"],
                    "target_visible_only_during_supervision": True,
                    "metadata_model_visible": False,
                    "prompt": prompt_for(case, bp, nuisance),
                    "target": target_for(case, bp),
                    "source_bindings": {
                        "fusion_path": SOURCE_FUSION,
                        "fusion_blob_sha": SOURCE_FUSION_BLOB_SHA,
                        "census_path": SOURCE_CENSUS,
                        "census_blob_sha": SOURCE_CENSUS_BLOB_SHA,
                    },
                    "training_boundary": {
                        "accepted_dataset_credit": 0,
                        "positive_jspace_label": False,
                        "canonical_state_write": False,
                        "direct_effect_execution": False,
                    },
                }
                out.append(row)
                row_index += 1
    return out


def _pair_cells(fam_rows: list[dict], case: str, a: str, b: str) -> set[tuple]:
    vals = []
    for r in fam_rows:
        if r["trajectory_case_evaluator_only"] != case:
            continue
        n = r["nuisance_controls_evaluator_only"]
        vals.append((n[a], n[b]))
    return set(vals)


def audit(generated: list[dict]) -> dict:
    failures: list[str] = []
    by_family: dict[str, list[dict]] = {}
    for row in generated:
        by_family.setdefault(row["family_id"], []).append(row)
        rid = row["row_id"]
        if row["canonical_truth_allowed"] is not False:
            failures.append("CANONICAL_TRUTH_LEAK:" + rid)
        if row["direct_effect_authority"] is not False:
            failures.append("EFFECT_AUTHORITY_LEAK:" + rid)
        if row["selected_using_holdout"] is not False:
            failures.append("HOLDOUT_SELECTION_LEAK:" + rid)
        if row["target_type"] in {"JSPACE_VECTOR_EFFECT", "ABSTRACT_STATE_CONTROL", "HIDDEN_STATE_COORDINATE"}:
            failures.append("POSITIVE_JSPACE_TARGET_FORBIDDEN:" + rid)
        if row.get("metadata_model_visible") is not False or row.get("model_visible_fields") != ["prompt"]:
            failures.append("MODEL_VISIBLE_METADATA_CONTRACT_FAIL:" + rid)
        p = row["prompt"]
        if any(marker in p for marker in FORBIDDEN_MODEL_VISIBLE_MARKERS):
            failures.append("PROCESS_IDENTITY_PROMPT_LEAK:" + rid)
        if row["family_id"] in p:
            failures.append("FAMILY_ID_PROMPT_LEAK:" + rid)
        try:
            t = json.loads(row["target"])
            if t.get("canonical_truth_minted") is not False or t.get("direct_effect_authority") is not False:
                failures.append("TARGET_AUTHORITY_LEAK:" + rid)
        except Exception:
            failures.append("TARGET_NOT_STRUCTURED_JSON:" + rid)

    expected_pair_cells = 4
    for family_id, fam_rows in by_family.items():
        splits = {r["split"] for r in fam_rows}
        ancestries = {r["provenance_ancestry_id"] for r in fam_rows}
        if len(splits) != 1:
            failures.append("FAMILY_SPLIT_LEAK:" + family_id)
        if len(ancestries) != 1:
            failures.append("ANCESTRY_DRIFT:" + family_id)
        if len(fam_rows) != 8:
            failures.append("FAMILY_ROW_COUNT_FAIL:" + family_id)
        for case in ("POSITIVE", "HARD_NEGATIVE"):
            cr = [r for r in fam_rows if r["trajectory_case_evaluator_only"] == case]
            if len(cr) != 4:
                failures.append("CASE_ROW_COUNT_FAIL:" + family_id + ":" + case)
            nvals = [r["nuisance_controls_evaluator_only"]["n"] for r in cr]
            evals = [r["nuisance_controls_evaluator_only"]["executor"] for r in cr]
            pvals = [r["nuisance_controls_evaluator_only"]["presentation"] for r in cr]
            if sorted(nvals) != [10, 10, 20, 20]:
                failures.append("N_BALANCE_FAIL:" + family_id + ":" + case)
            if sorted(evals) != ["node_kappa", "node_kappa", "node_sigma", "node_sigma"]:
                failures.append("EXECUTOR_BALANCE_FAIL:" + family_id + ":" + case)
            if sorted(pvals) != ["NARRATIVE", "NARRATIVE", "STRUCTURED", "STRUCTURED"]:
                failures.append("PRESENTATION_BALANCE_FAIL:" + family_id + ":" + case)
            for a, b in (("n", "executor"), ("n", "presentation"), ("executor", "presentation")):
                if len(_pair_cells(fam_rows, case, a, b)) != expected_pair_cells:
                    failures.append(f"PAIRWISE_NUISANCE_CONFOUND:{family_id}:{case}:{a}x{b}")

    split_counts = {s: sum(1 for r in generated if r["split"] == s) for s in ("TRAIN", "VALIDATION", "HOLDOUT")}
    family_split_counts = {s: sum(1 for f, sp in SPLITS.items() if sp == s) for s in ("TRAIN", "VALIDATION", "HOLDOUT")}
    return {
        "schema": GENERATOR_SCHEMA,
        "pass": not failures,
        "rows": len(generated),
        "families": len(by_family),
        "split_counts": split_counts,
        "family_split_counts": family_split_counts,
        "nuisance_factorial": "PAIRWISE_INDEPENDENT_2x2x2_HALF_FRACTION_PER_CASE",
        "process_identity_model_visible": False,
        "source_design_only": True,
        "known_limit": "Four process families are reserved as OOD validation/holdout; this is a generator/audit seed, not the final full-coverage training mixture.",
        "failures": sorted(set(failures)),
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "whole_entityos_hcu_runtime_credit_minted": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--audit-out", type=Path)
    args = ap.parse_args()
    generated = rows()
    result = audit(generated)
    if args.out:
        args.out.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in generated), encoding="utf-8")
        result["dataset_sha256"] = hashlib.sha256(args.out.read_bytes()).hexdigest()
    if args.audit_out:
        args.audit_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
