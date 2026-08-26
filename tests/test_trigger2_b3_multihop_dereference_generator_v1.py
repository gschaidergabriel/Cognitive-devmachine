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
        if row["queried_class_"] == row["broken_class"]:
            assert row["target"] == gen.UNRESOLVABLE_TOKEN
        else:
            assert row["target"] != gen.UNRESOLVABLE_TOKEN


def test_no_duplicate_prompts_within_any_family():
    _report, families = gen.run()
    for name, rows in families.items():
        prompts = [r["prompt"] for r in rows]
        assert len(prompts) == len(set(prompts)), f"{name} has duplicate prompts"
