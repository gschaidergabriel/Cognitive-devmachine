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


def test_higher_order_joint_mi_finds_the_known_open_leak():
    """Documents a real, currently-open finding (2026-08-26, Claude Code Lead
    research event): pairwise MI on the blueprint's own structured-field selftest
    is exactly zero everywhere, but joint (nuisance-field x template) mutual
    information against the routed target symbol is ~0.276 bits -- nonzero. This
    confirms H5's counterhypothesis in
    TRIGGERWORT_2_TRAINING_COURSE_DELTA_V35_SUPERVISOR_8_81_2026-08-26.md:
    "pairwise zero-MI alone is insufficient." This test intentionally asserts the
    CURRENT (leaky) state so a future generator fix is observed as a real
    regression-test flip, not silently re-passed by accident.
    """
    report = audit.run()
    c = report["checks"]["higher_order_joint_mi"]
    assert c["pass"] is False
    expected_leaky = {"target__permxt", "target__ordxt", "target__layxt", "target__pxt"}
    assert set(c["failures"]) == expected_leaky
    for key in expected_leaky:
        assert c["joint_mi_bits"][key] > 0.25
    # Class-level (not target-symbol-level) joint MI remains clean -- the leak is
    # specific to the routed-symbol/template interaction, not the semantic class.
    for key, value in c["joint_mi_bits"].items():
        if key.startswith("c__"):
            assert abs(value) < 1e-9


def test_overall_pass_reflects_open_leak_not_false_confidence():
    report = audit.run()
    assert report["overall_pass"] is False
