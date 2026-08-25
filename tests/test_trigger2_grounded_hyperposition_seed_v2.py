import json
from collections import Counter
from tools.trigger2_grounded_hyperposition_seed_generator_v2 import build_rows
from tools.trigger2_semantic_hyperposition_reference_labelers_v2 import U_update, D_resolve


def test_seed_shape_and_split_counts():
    rows = build_rows()
    assert len(rows) == 12
    assert Counter(r["split"] for r in rows) == {"TRAIN": 8, "VALIDATION": 2, "HOLDOUT": 2}
    assert len({r["provenance_ancestry_id"] for r in rows}) == 12


def test_every_target_is_rederived_by_v2_labeler():
    for row in build_rows():
        hp = row["semantic_hyperposition"]
        after = U_update(hp["state_before"], hp["observation"])
        assert after == hp["state_after"]
        assert D_resolve(after) == hp["resolution"]


def test_authority_and_holdout_fences():
    for row in build_rows():
        assert row["canonical_truth_allowed"] is False
        assert row["direct_effect_authority"] is False
        assert row["selected_using_holdout"] is False
        assert row["reference_derivation_domain"] == "SYNTHETIC_ATTRIBUTE_WORLD/v1"


def test_model_input_does_not_contain_training_target_or_resolution():
    for row in build_rows():
        rendered = json.dumps(row["model_input"], sort_keys=True)
        assert "training_target" not in rendered
        assert "resolution_status" not in rendered
        assert "target_atom" not in rendered
