"""Tests for trigger2_hyperposition_expansion_generator_v1 -- offline, deterministic,
mirrors the audit checks already run and recorded in
TRIGGER2_B6_HYPERPOSITION_EXPANSION_AUDIT_V1.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import trigger2_hyperposition_expansion_generator_v1 as gen  # noqa: E402


def test_build_is_deterministic():
    rows_a = gen.build()
    rows_b = gen.build()
    assert [r["id"] for r in rows_a] == [r["id"] for r in rows_b]
    assert [r["prompt"] for r in rows_a] == [r["prompt"] for r in rows_b]


def test_no_duplicate_prompts_or_ids():
    rows = gen.build()
    prompts = [r["prompt"] for r in rows]
    ids = [r["id"] for r in rows]
    assert len(prompts) == len(set(prompts))
    assert len(ids) == len(set(ids))


def test_holdout_entities_disjoint_from_train_and_validation():
    rows = gen.build()
    by_split = {}
    for r in rows:
        by_split.setdefault(r["split"], set()).add(r["entity"])
    assert not (by_split["HOLDOUT_FROZEN"] & by_split["TRAIN"])
    assert not (by_split["HOLDOUT_FROZEN"] & by_split["VALIDATION"])


def test_targets_are_only_known_class_words():
    rows = gen.build()
    targets = {r["target"] for r in rows}
    assert targets == {"PRESERVE_BRANCHES", "COLLAPSE_VALID"}


def test_class_balance_not_degenerate():
    rows = gen.build()
    import collections
    counts = collections.Counter(r["target"] for r in rows)
    # not required to be 50/50, but must not collapse to a trivial single-class shortcut
    ratio = counts["PRESERVE_BRANCHES"] / counts["COLLAPSE_VALID"]
    assert 1.5 <= ratio <= 5.0, f"class ratio {ratio} outside a sane range"


def test_scale_is_proportionate_not_curriculum_dwarfing():
    rows = gen.build()
    train_rows = [r for r in rows if r["split"] == "TRAIN"]
    # original family has 480 TRAIN rows; expansion should meaningfully grow it without
    # dwarfing the rest of the 16-family, 9544-row curriculum (run 1/2 comparison baseline).
    assert 400 <= len(train_rows) <= 3000


def test_discriminator_strength_semantics():
    """STRONG discriminator excluding all-but-one branch -> COLLAPSE_VALID;
    WEAK discriminator (or STRONG partial exclusion, >1 survivor) -> PRESERVE_BRANCHES."""
    row = gen.gen_discriminator_row(entity="node_test1", split="TRAIN", n_branches=2,
                                     strength="STRONG", excluded_idx=[0], rng=None)
    assert row["target"] == "COLLAPSE_VALID"

    row = gen.gen_discriminator_row(entity="node_test1", split="TRAIN", n_branches=3,
                                     strength="STRONG", excluded_idx=[0], rng=None)
    assert row["target"] == "PRESERVE_BRANCHES"  # 2 survivors, not fully resolved

    row = gen.gen_discriminator_row(entity="node_test1", split="TRAIN", n_branches=2,
                                     strength="WEAK", excluded_idx=[0], rng=None)
    assert row["target"] == "PRESERVE_BRANCHES"  # weak evidence never collapses


def test_chained_row_target_is_round2_only():
    row = gen.gen_chained_row(entity="node_test1", split="TRAIN", n_branches=2,
                               pressure_type="MAJORITY_VOTE", winner_idx=0,
                               round2_strength="STRONG", round2_excluded_idx=[1], rng=None)
    assert row["target"] == "COLLAPSE_VALID"
    assert "ROUND 1" in row["prompt"] and "ROUND 2" in row["prompt"]
