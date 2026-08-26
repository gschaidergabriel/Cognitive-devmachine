from __future__ import annotations

from tools import trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1 as audit


def test_schema_and_row_count():
    report = audit.run()
    assert report["schema"] == audit.SCHEMA
    assert report["rows_audited"] == 9072
    assert report["training_eligible"] is False


def test_uniqueness_holds():
    report = audit.run()
    assert report["checks"]["uniqueness"]["pass"] is True
    assert report["checks"]["uniqueness"]["duplicate_prompt_count"] == 0


def test_cross_split_disjointness_holds():
    report = audit.run()
    c = report["checks"]["cross_split_disjointness"]
    assert c["pass"] is True
    assert c["pairwise_overlaps"] == {}


def test_text_conditional_target_uniformity_holds():
    """No pure lexical (evidence+query text, codebook excluded) shortcut can beat
    chance: for every fixed rendered text, the routed target symbol is exactly
    uniform across the full mapping x codebook-order product."""
    report = audit.run()
    c = report["checks"]["text_conditional_target_uniformity"]
    assert c["pass"] is True
    assert c["groups_checked"] == 72
    assert c["failures"] == []


def test_higher_order_joint_mi_is_clean_within_split_and_excess_over_template():
    """CORRECTED (2026-08-26, same session): v1 of this test asserted a "leak" that
    was actually a misattributed measurement -- see the module's CORRECTION
    docstring and the superseding receipt in research_entity/00_CURRENT/updates/
    trigger2-training/. chatgpt-secondary reviewed commit ece5a0d, showed the
    ~0.276-bit combined-corpus signal is exactly I(target;template) alone (from
    HOLDOUT_FROZEN's intentional disjoint unseen-symbol pool under template T6,
    not a nuisance-field leak), and claude-code-lead independently reproduced this
    before accepting it. The real leak tests are: (a) within each split separately,
    joint nuisance MI must be exactly 0; (b) over the combined corpus, adding a
    nuisance field to `template` must add exactly 0 EXCESS information beyond the
    template baseline alone. Both hold cleanly for the current blueprint v2.1.
    """
    report = audit.run()
    c = report["checks"]["higher_order_joint_mi"]
    assert c["pass"] is True
    assert c["within_split_failures"] == []
    assert c["excess_failures"] == []
    for split in ("TRAIN", "VALIDATION", "HOLDOUT_FROZEN"):
        for value in c["within_split_joint_mi_bits"][split].values():
            assert abs(value) < 1e-9
    for value in c["excess_mi_over_template_baseline_bits"].values():
        assert abs(value) < 1e-9
    # The informational (intentionally NOT pass-gating) combined-corpus number is
    # retained for provenance/regression tracking and should still read ~0.276 bits
    # for target (by design) and exactly 0 for the semantic class.
    combined = c["informational_combined_corpus_joint_mi_bits"]
    assert combined["target__permxt"] > 0.25
    assert abs(combined["c__permxt"]) < 1e-9


def test_intended_split_support_shift_is_documented_and_holds():
    report = audit.run()
    c = report["checks"]["intended_split_support_shift"]
    assert c["pass"] is True
    assert c["train_equals_validation_symbols"] is True
    assert c["holdout_disjoint_from_train"] is True


def test_overall_pass_true_after_correction():
    report = audit.run()
    assert report["overall_pass"] is True
