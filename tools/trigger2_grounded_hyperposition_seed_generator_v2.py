import argparse
import json
from pathlib import Path
from trigger2_semantic_hyperposition_reference_labelers_v2 import (
    SCHEMA as LABELER_SCHEMA, DERIVATION_DOMAIN, U_update, D_resolve, U_d_test_order,
)


def branch(bid, value, attributes, provenance, salience=0.0):
    return {
        "branch_id": bid,
        "v_semantic_value": value,
        "K_context_predicate": "synthetic_episode_context",
        "E_plus": [], "E_minus": [],
        "F_falsifier": {"type": "ATTRIBUTE_MISMATCH", "attributes": sorted(attributes)},
        "T_validity_scope": "SYNTHETIC_TASK_ONLY",
        "A_origin_provenance": provenance,
        "sigma_epistemic_status": "HYPOTHESIS",
        "task_world": {"schema": DERIVATION_DOMAIN, "attributes": attributes},
        "salience": salience,
    }


SPECS = [
    ("TRAIN", "HPG01_COLOR_BIND", [("h1", "object_is_red", {"color": "red", "shape": "round"}), ("h2", "object_is_blue", {"color": "blue", "shape": "round"})], "color", "red"),
    ("TRAIN", "HPG02_COLOR_BIND", [("h1", "object_is_red", {"color": "red", "shape": "round"}), ("h2", "object_is_blue", {"color": "blue", "shape": "round"})], "color", "blue"),
    ("TRAIN", "HPG03_SHAPE_BIND", [("h1", "object_is_round", {"color": "red", "shape": "round"}), ("h2", "object_is_square", {"color": "red", "shape": "square"})], "shape", "round"),
    ("TRAIN", "HPG04_SHAPE_BIND", [("h1", "object_is_round", {"color": "red", "shape": "round"}), ("h2", "object_is_square", {"color": "red", "shape": "square"})], "shape", "square"),
    ("TRAIN", "HPG05_NONDISCRIMINATING", [("h1", "cause_alpha", {"color": "red", "temp": "warm"}), ("h2", "cause_beta", {"color": "blue", "temp": "warm"})], "temp", "warm"),
    ("TRAIN", "HPG06_CONTRADICTION", [("h1", "object_is_red", {"color": "red"}), ("h2", "object_is_blue", {"color": "blue"})], "color", "yellow"),
    ("TRAIN", "HPG07_THREE_BRANCH", [("h1", "red", {"color": "red", "shape": "round"}), ("h2", "blue", {"color": "blue", "shape": "round"}), ("h3", "green", {"color": "green", "shape": "square"})], "color", "green"),
    ("TRAIN", "HPG08_THREE_BRANCH", [("h1", "red_round", {"color": "red", "shape": "round"}), ("h2", "blue_round", {"color": "blue", "shape": "round"}), ("h3", "green_square", {"color": "green", "shape": "square"})], "shape", "round"),
    ("VALIDATION", "HPG09_NEW_PREDICATE", [("h1", "signal_high", {"level": "high"}), ("h2", "signal_low", {"level": "low"})], "level", "high"),
    ("VALIDATION", "HPG10_NEW_PREDICATE", [("h1", "signal_high", {"level": "high", "noise": "unknown"}), ("h2", "signal_low", {"level": "low", "noise": "unknown"})], "noise", "unknown"),
    ("HOLDOUT", "HPG11_NEW_OUTCOME_FAMILY", [("h1", "source_east", {"direction": "east"}), ("h2", "source_west", {"direction": "west"})], "direction", "east"),
    ("HOLDOUT", "HPG12_THREEWAY_HOLDOUT", [("h1", "circle", {"geom": "circle"}), ("h2", "square", {"geom": "square"}), ("h3", "triangle", {"geom": "triangle"})], "geom", "triangle"),
]


def build_rows():
    rows = []
    for split, family, branch_defs, attribute, outcome in SPECS:
        state_before = [branch(bid, value, attrs, f"{family}:branch:{bid}") for bid, value, attrs in branch_defs]
        discriminator = {"discriminator_id": f"{family}:d:{attribute}", "kind": "ATTRIBUTE_READ", "attribute": attribute}
        observation = {
            "evidence_id": f"{family}:e1",
            "discriminator": discriminator,
            "observed_outcome": outcome,
            "independence_group": f"{family}:ig1",
            "provenance": f"synthetic-oracle/{family}/v2",
        }
        state_after = U_update(state_before, observation)
        resolution = D_resolve(state_after)
        candidate_attributes = sorted(set.intersection(*[set(b["task_world"]["attributes"]) for b in state_before]))
        candidates = [
            {"candidate_id": f"{family}:test:{a}", "discriminator": {"discriminator_id": f"{family}:d:{a}", "kind": "ATTRIBUTE_READ", "attribute": a}, "independent_of_existing": True, "cost": 1.0}
            for a in candidate_attributes
        ]
        ranking = U_d_test_order(state_before, candidates)
        codebook = {"RESOLVED": "ATOM_K", "UNRESOLVED": "ATOM_M", "CONTRADICTION": "ATOM_Q"}
        if resolution["resolution_status"] == "RESOLVED_BY_DERIVED_DISCRIMINATOR":
            semantic_class = "RESOLVED"
        elif resolution["resolution_status"] == "UNRESOLVED_CONTRADICTION":
            semantic_class = "CONTRADICTION"
        else:
            semantic_class = "UNRESOLVED"
        target_atom = codebook[semantic_class]
        rows.append({
            "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
            "generator_schema": "TRIGGER2_GROUNDED_HYPERPOSITION_LABELER_SEED/v2",
            "reference_labeler_schema": LABELER_SCHEMA,
            "reference_derivation_domain": DERIVATION_DOMAIN,
            "split": split,
            "family_id": family,
            "provenance_ancestry_id": f"trigger2-grounded-hp-v2/{split.lower()}/{family}",
            "evidence_class": "SYNTHETIC_HARD_NEGATIVE" if semantic_class != "RESOLVED" else "METHOD_ONLY",
            "reality_level": "R3" if semantic_class != "RESOLVED" else "R2",
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "selected_using_holdout": False,
            "semantic_hyperposition": {
                "state_before": state_before,
                "observation": observation,
                "state_after": state_after,
                "resolution": resolution,
                "discriminator_ranking": ranking,
                "anti_collapse": ["MAJORITY_NOT_TRUTH", "SALIENCE_NOT_PROBABILITY", "RECURRENCE_NOT_EVIDENCE", "PROJECTION_NOT_DELETION"],
            },
            "semantic_class": semantic_class,
            "runtime_codebook": codebook,
            "target_atom": target_atom,
            "model_input": {
                "branches": [{"branch_id": b["branch_id"], "value": b["v_semantic_value"], "task_world": b["task_world"]} for b in state_before],
                "observation": observation,
                "runtime_codebook": codebook,
                "instruction": "Update branch-local evidence from the task-world observation without deleting alternatives; resolve only after a discriminator leaves exactly one live branch; map the resulting semantic state through the episode-local codebook.",
            },
            "training_target": {"state_after": state_after, "resolution": resolution, "semantic_class": semantic_class, "target_atom": target_atom},
        })
    return rows


def write_rows(path: Path):
    rows = build_rows()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="research_entity/global/j-space/research/trigger2_grounded_hyperposition_labeler_seed_v2.jsonl")
    args = parser.parse_args()
    built = write_rows(Path(args.out))
    print(json.dumps({"rows": len(built), "out": args.out}, sort_keys=True))
