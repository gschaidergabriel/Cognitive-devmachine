from __future__ import annotations

from tools import trigger2_b3_multihop_dereference_generator_v1 as gen


def test_schema_and_total():
    report, families = gen.run()
    assert report["schema"] == gen.SCHEMA
    assert report["training_eligible"] is False
    assert report["total_rows"] == 2160
    assert report["overall_pass"] is True


def test_multihop_targets_are_always_final_symbols_never_pointers():
    report, families = gen.run()
    r = report["reports"]["MULTI_HOP_DEREF"]
    assert r["pass"] is True
    assert r["failures"] == []
    for row in families["MULTI_HOP_DEREF"]:
        assert not row["target"].startswith("PTR_")
        assert row["target"].startswith("ABI_ACCEPTED_ORDINAL:")


def test_multihop_depth_assignment_is_always_a_permutation_of_1_2_3():
    _report, families = gen.run()
    for row in families["MULTI_HOP_DEREF"]:
        assert sorted(row["depth_by_class"].values()) == [1, 2, 3]


def test_unresolvable_chain_rejection_discriminates_broken_from_intact():
    report, families = gen.run()
    r = report["reports"]["UNRESOLVABLE_CHAIN_REJECTION"]
    assert r["pass"] is True
    assert r["failures"] == []
    assert r["broken_query_rows"] > 0
    assert r["unbroken_query_rows"] > 0
    for row in families["UNRESOLVABLE_CHAIN_REJECTION"]:
        if row["queried_class"] == row["broken_class"]:
            assert row["target"] == gen.UNRESOLVABLE_TOKEN
        else:
            assert row["target"] != gen.UNRESOLVABLE_TOKEN


def test_no_duplicate_prompts_within_any_family():
    _report, families = gen.run()
    for name, rows in families.items():
        prompts = [r["prompt"] for r in rows]
        assert len(prompts) == len(set(prompts)), f"{name} has duplicate prompts"


def test_queried_class_field_name_is_identical_across_both_families():
    """Regression for the real 2026-08-27 bug: UNRESOLVABLE_CHAIN_REJECTION
    used to emit "queried_class_" (trailing underscore) while MULTI_HOP_DEREF
    emitted "queried_class" for the same concept under the same SCHEMA. This
    must fail loudly if that mixed-key corpus ever recurs."""
    _report, families = gen.run()
    for name, rows in families.items():
        for row in rows:
            assert "queried_class" in row, f"{name} row missing queried_class: {row.get('id')}"
            assert "queried_class_" not in row, f"{name} row has trailing-underscore alias: {row.get('id')}"


def test_cross_family_schema_consistency_audit_passes():
    report, _families = gen.run()
    r = report["reports"]["CROSS_FAMILY_SCHEMA_CONSISTENCY"]
    assert r["pass"] is True
    assert r["failures"] == []
    assert "queried_class" in r["shared_concept_keys"]
