from __future__ import annotations

from tools import trigger2_b2_prior_override_remap_stale_generator_v1 as gen


def test_schema_and_total():
    report, families = gen.run()
    assert report["schema"] == gen.SCHEMA
    assert report["training_eligible"] is False
    assert report["total_rows"] == 1800
    assert report["overall_pass"] is True


def test_prior_override_clean_and_uses_current_codebook_only():
    report, families = gen.run()
    r = report["reports"]["PRIOR_OVERRIDE"]
    assert r["pass"] is True
    assert r["failures"] == []
    # both agreement conditions represented -- otherwise the adversarial arm
    # (distractor disagrees) could be trivially absent
    assert r["agree_rows"] > 0
    assert r["disagree_rows"] > 0


def test_mid_episode_remap_clean_and_only_updated_class_changes():
    report, families = gen.run()
    r = report["reports"]["MID_EPISODE_REMAP"]
    assert r["pass"] is True
    assert r["failures"] == []
    rows = families["MID_EPISODE_REMAP"]
    # spot-check: an untouched class (neither updated nor source) keeps its
    # original binding
    untouched = [row for row in rows if row["queried_class"] not in (row["updated_class"], row["source_class"])]
    assert len(untouched) > 0


def test_stale_binding_rejection_discriminates_stale_from_valid():
    report, families = gen.run()
    r = report["reports"]["STALE_BINDING_REJECTION"]
    assert r["pass"] is True
    assert r["failures"] == []
    assert r["stale_rows"] == r["valid_rows"]
    rows = families["STALE_BINDING_REJECTION"]
    for row in rows:
        if row["is_stale"]:
            assert row["target"] == gen.STALE_TOKEN
        else:
            assert row["target"] != gen.STALE_TOKEN


def test_no_duplicate_prompts_within_any_family():
    _report, families = gen.run()
    for name, rows in families.items():
        prompts = [r["prompt"] for r in rows]
        assert len(prompts) == len(set(prompts)), f"{name} has duplicate prompts"
