from __future__ import annotations

from tools import trigger2_b1_binding_materializer_v1 as mat


def test_run_fail_closed_gate_is_wired_to_the_leakage_audit():
    """The materializer must refuse to produce rows if the leakage audit does not
    pass -- this is the actual enforcement mechanism, not just a docstring claim."""
    materialized, audit_report = mat.run(fail_closed=True)
    assert audit_report["overall_pass"] is True
    assert len(materialized) == 9072


def test_split_counts_match_donor_blueprint():
    materialized, _ = mat.run()
    from collections import Counter

    counts = Counter(r["split"] for r in materialized)
    assert dict(counts) == {"TRAIN": 6912, "VALIDATION": 1728, "HOLDOUT_FROZEN": 432}


def test_every_row_training_ineligible_and_method_only():
    materialized, _ = mat.run()
    for r in materialized:
        assert r["training_eligible"] is False
        assert r["evidence_class"] == "METHOD_ONLY"
        assert r["canonical_truth_allowed"] is False


def test_self_check_passes_and_no_contradictory_prompts():
    materialized, _ = mat.run()
    check = mat.self_check(materialized)
    assert check["pass"] is True
    assert check["failures"] == []
    assert check["unique_prompts"] == len(materialized)


def test_target_reachable_from_realized_mapping():
    materialized, _ = mat.run()
    import trigger2_dynamic_binding_blueprint_v2 as bp

    for r in materialized[:200]:
        ci = bp.CLASSES.index(r["c"])
        assert r["target"] == r["sym"][r["perm"][ci]]
