from __future__ import annotations

from tools import trigger2_b1_train_balanced_2order_selector_v1 as sel


def test_row_counts_match_chatgpt_secondary_recommendation():
    """2304 TRAIN (chatgpt-secondary's explicit recommended tier, conversation
    c/6a8ed518) + full untouched VALIDATION (1728) + HOLDOUT_FROZEN (432)."""
    materialized, _audit, stats = sel.run()
    from collections import Counter

    counts = Counter(r["split"] for r in materialized)
    assert dict(counts) == {"TRAIN": 2304, "VALIDATION": 1728, "HOLDOUT_FROZEN": 432}
    assert stats["train_rows_full"] == 6912
    assert stats["train_rows_reduced"] == 2304


def test_reduced_audit_passes_fail_closed():
    """The selector must actually refuse to write output on a failing audit -- this
    is not hypothetical: two earlier keying schemes (template x triplet; then
    class x polarity x layout) were tried and rejected by this exact gate during
    development, see the module's CORRECTION docstring."""
    materialized, audit_report, _stats = sel.run(fail_closed=True)
    assert audit_report["overall_pass"] is True
    assert len(materialized) == 4464


def test_order_carries_no_target_information_within_train():
    _materialized, audit_report, _stats = sel.run()
    c = audit_report["checks"]["order_mapping_decoupling"]
    assert c["pass"] is True
    assert abs(c["order_target_mi_bits"]) < 1e-9
    assert c["all_six_mappings_present_at_every_surviving_order"] is True


def test_all_six_orders_present_at_least_once():
    """Coverage need not be perfectly even (only 4 template groups feeding 6 order
    slots), but every order value must still appear somewhere in TRAIN, otherwise
    the reduced set silently drops an entire codebook-order condition."""
    _materialized, _audit, stats = sel.run()
    coverage = stats["order_coverage_across_cells"]
    assert {int(k) for k in coverage} == {0, 1, 2, 3, 4, 5}
    assert all(v >= 1 for v in coverage.values())


def test_validation_and_holdout_left_fully_untouched():
    materialized, _audit, _stats = sel.run()
    import trigger2_dynamic_binding_blueprint_v2 as bp

    full_rows = bp.build_rows()
    full_val = [r for r in full_rows if r["split"] == "VALIDATION"]
    full_hold = [r for r in full_rows if r["split"] == "HOLDOUT_FROZEN"]
    reduced_val = [r for r in materialized if r["split"] == "VALIDATION"]
    reduced_hold = [r for r in materialized if r["split"] == "HOLDOUT_FROZEN"]
    assert len(reduced_val) == len(full_val)
    assert len(reduced_hold) == len(full_hold)
