"""Full-dataset verification for xeno_structured_prompt_resolver_v1 -- every one of
the 14 deterministic families checked against its complete real training file
(14,244 rows total), not a sample. Offline, no model, no network."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import xeno_structured_prompt_resolver_v1 as resolver  # noqa: E402

TRAINING_DIR = Path(__file__).resolve().parents[1] / "research_entity/claycode/training"

FAMILY_FILES = {
    "B0_READ_BASELINE": "TRIGGER2_B0_READ_BASELINE_CANDIDATE_V1.jsonl",
    "B0_WRITE_BASELINE": "TRIGGER2_B0_WRITE_BASELINE_CANDIDATE_V1.jsonl",
    "B1_TRAIN_BALANCED_2ORDER": "TRIGGER2_B1_TRAIN_BALANCED_2ORDER_V2.jsonl",
    "B2_MID_EPISODE_REMAP": "TRIGGER2_B2_MID_EPISODE_REMAP_CANDIDATE_V2.jsonl",
    "B2_PRIOR_OVERRIDE": "TRIGGER2_B2_PRIOR_OVERRIDE_CANDIDATE_V2.jsonl",
    "B2_STALE_BINDING_REJECTION": "TRIGGER2_B2_STALE_BINDING_REJECTION_CANDIDATE_V1.jsonl",
    "B3_MULTI_HOP_DEREF": "TRIGGER2_B3_MULTI_HOP_DEREF_CANDIDATE_V2.jsonl",
    "B3_UNRESOLVABLE_CHAIN_REJECTION": "TRIGGER2_B3_UNRESOLVABLE_CHAIN_REJECTION_CANDIDATE_V2.jsonl",
    "B4_CAPACITY_INTERFERENCE": "TRIGGER2_B4_CAPACITY_INTERFERENCE_CANDIDATE_V2.jsonl",
    "B5_VARIABLE_N_EQUIVARIANCE": "TRIGGER2_B5_VARIABLE_N_EQUIVARIANCE_CANDIDATE_V2.jsonl",
    "B6_GWT_COMPETITION_BROADCAST": "TRIGGER2_B6_GWT_COMPETITION_BROADCAST_CANDIDATE_V1.jsonl",
    "B6_GWT_CAUSAL_REENTRY": "TRIGGER2_B6_GWT_CAUSAL_REENTRY_CANDIDATE_V1.jsonl",
    "B6_GWT_UPTAKE": "TRIGGER2_B6_GWT_UPTAKE_CANDIDATE_V1.jsonl",
    "B6_DB_VS_SIM": "TRIGGER2_B6_DB_VS_SIM_CANDIDATE_V1.jsonl",
    "B6_CLAUDE_HANDOFF_REENTRY": "TRIGGER2_B6_CLAUDE_HANDOFF_REENTRY_CANDIDATE_V1.jsonl",
}


def _check_family(fam, fname):
    resolve = resolver.FAMILY_RESOLVERS[fam]
    rows = [json.loads(line) for line in open(TRAINING_DIR / fname)]
    wrong = [r["id"] for r in rows if resolve(r["prompt"]) != r["target"]]
    assert wrong == [], f"{fam}: {len(wrong)}/{len(rows)} misclassified: {wrong[:5]}"
    return len(rows)


def test_all_14_families_100pct_against_full_real_datasets():
    total = 0
    for fam, fname in FAMILY_FILES.items():
        total += _check_family(fam, fname)
    assert total == 14676, f"expected 14676 total rows across 15 families, got {total}"
