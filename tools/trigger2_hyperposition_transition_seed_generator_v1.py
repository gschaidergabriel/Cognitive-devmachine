#!/usr/bin/env python3
"""Generate deterministic semantic-Hyperposition transition candidates for Trigger-2.

The generator is source-design only. Every row is candidate-only, carries a full
Hyperposition before/after state produced by the deterministic reference labelers,
and remains non-promoting until separate admission/model/runtime gates pass.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LABELER_PATH = HERE / "trigger2_hyperposition_reference_labelers_v1.py"
spec = importlib.util.spec_from_file_location("tr2label", LABELER_PATH)
label = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(label)

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
GENERATOR_SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_TRANSITION_SEED_GENERATOR/v1"
TARGET_TYPE = "SEMANTIC_HYPERPOSITION_REFERENCE_TRANSITION"
SPLIT_UNIT = "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY"

FAMILIES = {
    "TR2HP_LBL_SUPPORT": {
        "split": "TRAIN",
        "evidence_class": "METHOD_ONLY",
        "semantic_class": "ALLOW",
        "description": "Independent supporting evidence strengthens one live branch without deleting its competitor.",
        "observation": {
            "evidence_kind": "MEASUREMENT",
            "polarity": "SUPPORT",
            "target_branch_ids": ["b_alpha"],
        },
        "discriminator_result": None,
    },
    "TR2HP_LBL_COUNTER": {
        "split": "TRAIN",
        "evidence_class": "METHOD_ONLY",
        "semantic_class": "ABSTAIN",
        "description": "Counterevidence weakens one branch while preserving both alternatives and explicit contradiction.",
        "observation": {
            "evidence_kind": "MEASUREMENT",
            "polarity": "COUNTER",
            "target_branch_ids": ["b_alpha"],
        },
        "discriminator_result": None,
    },
    "TR2HP_LBL_MAJORITY_NO_COLLAPSE": {
        "split": "TRAIN",
        "evidence_class": "SYNTHETIC_HARD_NEGATIVE",
        "semantic_class": "ABSTAIN",
        "description": "A majority/recurrent signal is visible but cannot collapse unresolved branches or mint truth.",
        "observation": {
            "evidence_kind": "MAJORITY",
            "polarity": "NO_EFFECT",
            "target_branch_ids": ["b_alpha"],
        },
        "discriminator_result": {
            "qualified": True,
            "evidence_kind": "MAJORITY",
            "selected_branch_id": "b_alpha",
        },
    },
    "TR2HP_LBL_QUALIFIED_RESOLVE": {
        "split": "TRAIN",
        "evidence_class": "METHOD_ONLY",
        "semantic_class": "ALLOW",
        "description": "A qualified direct test falsifies the competing branch; only then may the synthetic task resolve.",
        "observation": {
            "evidence_kind": "DIRECT_TEST",
            "polarity": "FALSIFY",
            "target_branch_ids": ["b_beta"],
        },
        "discriminator_result": {
            "qualified": True,
            "evidence_kind": "DIRECT_TEST",
            "selected_branch_id": "b_alpha",
        },
    },
    "TR2HP_LBL_PROJECTION_NOT_DELETION": {
        "split": "VALIDATION",
        "evidence_class": "SYNTHETIC_HARD_NEGATIVE",
        "semantic_class": "ABSTAIN",
        "description": "Context projection hides one branch locally but preserves it for retrieval; filtering is not deletion.",
        "projection_filter_beta": True,
        "observation": {
            "evidence_kind": "CONTEXT_FILTER",
            "polarity": "NO_EFFECT",
            "target_branch_ids": ["b_beta"],
        },
        "discriminator_result": None,
    },
    "TR2HP_LBL_UNKNOWN_ABSTAIN": {
        "split": "HOLDOUT",
        "evidence_class": "METHOD_ONLY",
        "semantic_class": "ABSTAIN",
        "description": "Missing discriminating evidence keeps multiple branches live; UNKNOWN/ABSTAIN is the correct target.",
        "observation": {
            "evidence_kind": "MISSING_EVIDENCE",
            "polarity": "NO_EFFECT",
            "target_branch_ids": ["b_alpha", "b_beta"],
        },
        "discriminator_result": None,
    },
}

SURFACES = {
    "STRUCTURED": "episode={desc}\nApply the typed observation and return the next semantic Hyperposition reference state.",
    "NARRATIVE": "Situation: {desc} Preserve live alternatives and update only what the evidence licenses; return the next typed state.",
}


def base_state(order: tuple[str, str], projection_filter_beta: bool = False) -> dict[str, Any]:
    branches = {
        "b_alpha": {
            "branch_id": "b_alpha",
            "v_semantic_value": "ALLOW",
            "K_context_predicate": "ctx_episode",
            "E_plus": [],
            "E_minus": [],
            "F_falsifier": "direct_test_alpha_false",
            "T_validity_scope": "synthetic_episode",
            "A_origin_provenance": "trigger2-hp-alpha",
            "sigma_epistemic_status": "HYPOTHESIS",
            "projection_visibility": "VISIBLE",
        },
        "b_beta": {
            "branch_id": "b_beta",
            "v_semantic_value": "DENY",
            "K_context_predicate": "ctx_episode",
            "E_plus": [],
            "E_minus": [],
            "F_falsifier": "direct_test_beta_false",
            "T_validity_scope": "synthetic_episode",
            "A_origin_provenance": "trigger2-hp-beta",
            "sigma_epistemic_status": "HYPOTHESIS",
            "projection_visibility": "FILTERED_BUT_RETAINED" if projection_filter_beta else "VISIBLE",
        },
    }
    return {"query_id": "trigger2_hp_transition", "branches": [branches[x] for x in order]}


def _observation(family_id: str, family: dict[str, Any], variant: int) -> dict[str, Any]:
    obs = dict(family["observation"])
    obs.update(
        {
            "evidence_id": f"{family_id.lower()}-e{variant}",
            "provenance": f"{family_id.lower()}-source",
            "independence_group": f"{family_id.lower()}-ig",
            "claim": family["description"],
        }
    )
    return obs


def rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    row_index = 0
    for family_id, family in FAMILIES.items():
        for order_id, order in (("AB", ("b_alpha", "b_beta")), ("BA", ("b_beta", "b_alpha"))):
            for surface_id, surface in SURFACES.items():
                before = base_state(order, family.get("projection_filter_beta", False))
                obs = _observation(family_id, family, row_index)
                episode = {
                    "hyperposition_state_before": before,
                    "event_or_observation": obs,
                    "discriminator_result": family.get("discriminator_result"),
                    "discriminator_candidates": [
                        {
                            "discriminator_id": "direct_test",
                            "separation_count": 2,
                            "independence_score": 1.0,
                            "cost": 1.0,
                            "risk": 0.0,
                            "coordination_cost": 0.0,
                        },
                        {
                            "discriminator_id": "majority_poll",
                            "separation_count": 0,
                            "independence_score": 0.0,
                            "cost": 0.1,
                            "risk": 0.0,
                            "coordination_cost": 0.0,
                        },
                    ],
                    "salience_items": [
                        {"item_id": "direct_test", "decision_relevance": 5, "retrieval_cost": 1, "staleness_penalty": 0},
                        {"item_id": "majority_poll", "decision_relevance": 1, "retrieval_cost": 0, "staleness_penalty": 0},
                    ],
                    "semantic_class_or_action": family["semantic_class"],
                    "runtime_codebook_or_opcode": None,
                }
                target = label.label_episode(episode)
                prompt = surface.format(desc=family["description"])
                out.append(
                    {
                        "schema": ROW_SCHEMA,
                        "evidence_class": family["evidence_class"],
                        "reality_level": "R3" if family["evidence_class"] == "SYNTHETIC_HARD_NEGATIVE" else "R2",
                        "family_id": family_id,
                        "provenance_ancestry_id": "trigger2-hyperposition-reference-labelers-v1-" + family_id.lower(),
                        "canonical_truth_allowed": False,
                        "direct_effect_authority": False,
                        "fact_status": "UNKNOWN" if family["semantic_class"] == "ABSTAIN" else "NOT_APPLICABLE",
                        "target_type": TARGET_TYPE,
                        "split": family["split"],
                        "split_unit": SPLIT_UNIT,
                        "selected_using_holdout": False,
                        "row_id": f"TR2HPTV1_{row_index:04d}",
                        "branch_order_evaluator_only": order_id,
                        "surface_evaluator_only": surface_id,
                        "model_visible_fields": ["prompt"],
                        "metadata_model_visible": False,
                        "target_visible_only_during_supervision": True,
                        "semantic_hyperposition_native": True,
                        "full_D_training_admission": False,
                        "final_ft_eligible": False,
                        "prompt": prompt,
                        "target": json.dumps(target, sort_keys=True, ensure_ascii=False, separators=(",", ":")),
                    }
                )
                row_index += 1
    return out


def audit(generated: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in generated:
        rid = row["row_id"]
        by_family.setdefault(row["family_id"], []).append(row)
        if row["canonical_truth_allowed"] is not False:
            failures.append("CANONICAL_TRUTH_LEAK:" + rid)
        if row["direct_effect_authority"] is not False:
            failures.append("DIRECT_EFFECT_AUTHORITY_LEAK:" + rid)
        if row["selected_using_holdout"] is not False:
            failures.append("HOLDOUT_SELECTION_LEAK:" + rid)
        if row["semantic_hyperposition_native"] is not True:
            failures.append("HYPERPOSITION_FRAME_MISSING:" + rid)
        if row["full_D_training_admission"] is not False or row["final_ft_eligible"] is not False:
            failures.append("PREMATURE_TRAINING_PROMOTION:" + rid)
        if row.get("metadata_model_visible") is not False or row.get("model_visible_fields") != ["prompt"]:
            failures.append("MODEL_VISIBLE_METADATA_FAIL:" + rid)
        target = json.loads(row["target"])
        branches = target["hyperposition_state_after"]["branches"]
        if len(branches) < 2:
            failures.append("BRANCH_COLLAPSE:" + rid)
        if target.get("canonical_truth_minted") is not False or target.get("direct_effect_authority") is not False:
            failures.append("TARGET_AUTHORITY_LEAK:" + rid)

    for family_id, fam in by_family.items():
        if len({r["split"] for r in fam}) != 1:
            failures.append("FAMILY_SPLIT_LEAK:" + family_id)
        if len({r["provenance_ancestry_id"] for r in fam}) != 1:
            failures.append("ANCESTRY_DRIFT:" + family_id)
        if len(fam) != 4:
            failures.append("FAMILY_ROW_COUNT_FAIL:" + family_id)
        if {r["branch_order_evaluator_only"] for r in fam} != {"AB", "BA"}:
            failures.append("BRANCH_ORDER_CROSS_FAIL:" + family_id)
        if {r["surface_evaluator_only"] for r in fam} != {"STRUCTURED", "NARRATIVE"}:
            failures.append("SURFACE_CROSS_FAIL:" + family_id)

    split_counts = {s: sum(1 for r in generated if r["split"] == s) for s in ("TRAIN", "VALIDATION", "HOLDOUT")}
    return {
        "schema": GENERATOR_SCHEMA,
        "pass": not failures,
        "rows": len(generated),
        "families": len(by_family),
        "split_counts": split_counts,
        "family_split_integrity": not any(x.startswith("FAMILY_SPLIT_LEAK") for x in failures),
        "semantic_hyperposition_native_all": all(r["semantic_hyperposition_native"] for r in generated),
        "canonical_truth_allowed_any": any(r["canonical_truth_allowed"] for r in generated),
        "direct_effect_authority_any": any(r["direct_effect_authority"] for r in generated),
        "branch_order_variants_per_family": 2,
        "surface_variants_per_family": 2,
        "known_limit": "Small reference-labeler seed only; it does not replace C1-C6/A/B/evidence-family retrofit, conditional-nuisance decoding, exact ABI binding, or final mixed-corpus admission.",
        "failures": sorted(set(failures)),
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
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
    else:
        data = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in generated).encode("utf-8")
        result["dataset_sha256"] = hashlib.sha256(data).hexdigest()
    if args.audit_out:
        args.audit_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
