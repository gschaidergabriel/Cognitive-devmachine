"""The real 'computational unit' test: given an arbitrary prompt from the full
B0-B6 curriculum with NO prior knowledge of which family it belongs to, does the
unified classify -> resolve pipeline produce the exactly correct answer, always?
Checked against the COMPLETE real population across all 16 families (16,172 rows,
including both real Hyperposition files), not a sample."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from xeno_resolver_dispatch_v1 import resolve  # noqa: E402

TRAINING_DIR = Path(__file__).resolve().parents[1] / "research_entity/claycode/training"

ALL_FAMILY_FILES = [
    "TRIGGER2_B0_READ_BASELINE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B0_WRITE_BASELINE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B1_TRAIN_BALANCED_2ORDER_V2.jsonl",
    "TRIGGER2_B2_MID_EPISODE_REMAP_CANDIDATE_V2.jsonl",
    "TRIGGER2_B2_PRIOR_OVERRIDE_CANDIDATE_V2.jsonl",
    "TRIGGER2_B2_STALE_BINDING_REJECTION_CANDIDATE_V1.jsonl",
    "TRIGGER2_B3_MULTI_HOP_DEREF_CANDIDATE_V2.jsonl",
    "TRIGGER2_B3_UNRESOLVABLE_CHAIN_REJECTION_CANDIDATE_V2.jsonl",
    "TRIGGER2_B4_CAPACITY_INTERFERENCE_CANDIDATE_V2.jsonl",
    "TRIGGER2_B5_VARIABLE_N_EQUIVARIANCE_CANDIDATE_V2.jsonl",
    "TRIGGER2_B6_GWT_COMPETITION_BROADCAST_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_GWT_CAUSAL_REENTRY_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_GWT_UPTAKE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_DB_VS_SIM_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_CLAUDE_HANDOFF_REENTRY_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_HYPERPOSITION_EVIDENCE_AUTHORITY_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_HYPERPOSITION_EXPANSION_CANDIDATE_V1.jsonl",
]


def test_100pct_exact_answer_across_entire_real_population_no_prior_family_knowledge():
    total = 0
    wrong = []
    for fname in ALL_FAMILY_FILES:
        rows = [json.loads(line) for line in open(TRAINING_DIR / fname)]
        for row in rows:
            total += 1
            _, answer = resolve(row["prompt"])
            if answer != row["target"]:
                wrong.append((fname, row["id"], row["target"], answer))
    assert total == 16172, f"expected 16172 rows across all 16 families, got {total}"
    assert wrong == [], f"{len(wrong)}/{total} wrong: {wrong[:5]}"


def test_dispatch_correctly_prioritizes_stale_marker_over_plain_codebook_shape():
    """The specific gap this dispatcher closes: a B2_STALE prompt that IS actually
    stale must never be answered by the plain CODEBOOK_LOOKUP logic (which would
    ignore the STALE_REJECTED marker and return a wrong ordinal)."""
    prompt = (
        "NOTICE: the codebook below is marked STALE_REJECTED. Do not use it.\n"
        "CODEBOOK: ALLOW=>ABI_ACCEPTED_ORDINAL:00 | DENY=>ABI_ACCEPTED_ORDINAL:01 | "
        "ABSTAIN=>ABI_ACCEPTED_ORDINAL:02\nSTATE: the current class is ALLOW, given directly.\n"
        "Return exactly one bound symbol, or the token STALE_REJECTED if the binding cannot be used."
    )
    fam, answer = resolve(prompt)
    assert fam == "B2_STALE_BINDING_REJECTION"
    assert answer == "STALE_REJECTED"


def test_unrecognized_prompt_fails_closed_not_a_guess():
    fam, answer = resolve("This is a completely novel prompt with no known template shape.")
    assert fam is None
    assert answer is None
