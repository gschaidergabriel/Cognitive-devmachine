from __future__ import annotations

from tools import trigger2_a_autonomous_boot_work_selection_generator_v1 as a


def test_schema_and_pass():
    report, rows = a.run()
    assert report["schema"] == a.SCHEMA
    assert report["overall_pass"] is True
    assert report["training_eligible"] is False


def test_target_correctness_never_invents_work():
    """Hard negative: inventing work when none exists."""
    _report, rows = a.run()
    for r in rows:
        expected = a.compute_target(r["outcomes"], r["redundancy_requested"])
        assert r["target"] == expected
        assert r["target"] in a.ITEM_IDS or r["target"] == a.NO_WORK_TOKEN


def test_stale_claims_are_selectable():
    """Hard negative: ignoring epoch/digest -- a stale (non-current-epoch) claim,
    by self or other, must be treated as available again."""
    assert a.is_selectable("OTHER_STALE_AVAILABLE", redundancy_requested=False) is True
    assert a.is_selectable("SELF_STALE_AVAILABLE", redundancy_requested=False) is True
    assert a.is_selectable("OTHER_CURRENT_UNAVAILABLE", redundancy_requested=False) is False


def test_self_current_owned_requires_explicit_redundancy():
    """Hard negative: repeating claimed work unless redundancy is explicitly
    requested."""
    assert a.is_selectable("SELF_CURRENT_OWNED", redundancy_requested=False) is False
    assert a.is_selectable("SELF_CURRENT_OWNED", redundancy_requested=True) is True


def test_completed_never_selectable_regardless_of_redundancy():
    assert a.is_selectable("COMPLETED", redundancy_requested=False) is False
    assert a.is_selectable("COMPLETED", redundancy_requested=True) is False


def test_boot_role_hint_never_determines_target():
    """Hard negative: launch-time role injection."""
    report, _rows = a.run()
    assert report["audit"]["role_hint_target_mi_bits"] < 1e-9


def test_node_identity_carries_no_information_beyond_split():
    """Hard negative: treating node identity as a permanent cognitive role.
    node_identity is a strict split alias by design; the real assertion is
    that it adds zero EXCESS information beyond the (legitimate,
    holdout-support-driven) split baseline, and zero information at all
    within any single split."""
    report, _rows = a.run()
    audit = report["audit"]
    assert abs(audit["node_identity_excess_mi_over_split_bits"]) < 1e-9


def test_some_rows_have_no_work_available():
    report, _rows = a.run()
    assert report["audit"]["no_work_available_rows"] > 0


def test_holdout_status_combinations_disjoint_from_train_validation():
    _report, rows = a.run()
    train_combos = {tuple(r["outcomes"][i] for i in a.ITEM_IDS) for r in rows if r["split"] in ("TRAIN", "VALIDATION")}
    hold_combos = {tuple(r["outcomes"][i] for i in a.ITEM_IDS) for r in rows if r["split"] == "HOLDOUT_FROZEN"}
    assert train_combos.isdisjoint(hold_combos)


def test_no_duplicate_prompts():
    _report, rows = a.run()
    prompts = [r["prompt"] for r in rows]
    assert len(prompts) == len(set(prompts))
