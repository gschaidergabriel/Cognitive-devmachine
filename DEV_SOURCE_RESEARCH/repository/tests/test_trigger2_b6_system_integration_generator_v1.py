from __future__ import annotations

from tools import trigger2_b6_system_integration_generator_v1 as gen


def test_schema_and_counts():
    report = gen.run()
    assert report["schema"] == gen.SCHEMA
    assert report["training_eligible"] is False
    assert report["db_vs_sim"]["rows"] == 360
    assert report["claude_handoff_reentry"]["rows"] == 480
    assert report["hyperposition_evidence_authority"]["rows"] == 600
    assert report["total_rows"] == 1440


def test_overall_pass():
    report = gen.run()
    assert report["overall_pass"] is True


def test_entity_pools_disjoint_across_splits():
    train = set(gen.SPLIT_ENTITIES["TRAIN"])
    val = set(gen.SPLIT_ENTITIES["VALIDATION"])
    hold = set(gen.SPLIT_ENTITIES["HOLDOUT_FROZEN"])
    assert train.isdisjoint(val)
    assert train.isdisjoint(hold)
    assert val.isdisjoint(hold)


def test_db_vs_sim_pass_clean_and_balanced():
    rows = gen.build_db_vs_sim_rows()
    report = gen.audit_db_vs_sim(rows)
    assert report["pass"] is True
    assert report["failures"] == []
    assert report["split_counts"] == {"TRAIN": 288, "VALIDATION": 36, "HOLDOUT_FROZEN": 36}


def test_db_vs_sim_target_matches_class():
    for r in gen.build_db_vs_sim_rows():
        assert r["target"] == r["class"]
        assert r["target"] in gen.DB_VS_SIM_CLASSES


def test_claude_handoff_pass_clean_and_balanced():
    rows = gen.build_claude_handoff_rows()
    report = gen.audit_claude_handoff(rows)
    assert report["pass"] is True
    assert report["failures"] == []
    assert report["split_counts"] == {"TRAIN": 384, "VALIDATION": 48, "HOLDOUT_FROZEN": 48}


def test_claude_handoff_target_matches_class():
    for r in gen.build_claude_handoff_rows():
        assert r["target"] == r["class"]
        assert r["target"] in gen.CLAUDE_HANDOFF_CLASSES


def test_hyperposition_pass_clean():
    rows = gen.build_hyperposition_rows()
    report = gen.audit_hyperposition(rows)
    assert report["pass"] is True
    assert report["failures"] == []
    assert report["split_counts"] == {"TRAIN": 480, "VALIDATION": 60, "HOLDOUT_FROZEN": 60}


def test_hyperposition_collapse_only_on_explicit_discriminator():
    """Hard-negative law (course section H): collapse must never be the target
    for majority/coordinator-preference/repeated-agreement/surface-fluency
    pressure -- only an explicit discriminator test result may collapse."""
    for r in gen.build_hyperposition_rows():
        if r["pressure_type"] == "EXPLICIT_DISCRIMINATOR_TEST":
            assert r["target"] == "COLLAPSE_VALID"
        else:
            assert r["target"] == "PRESERVE_BRANCHES"


def test_no_duplicate_prompts_within_any_family():
    for rows in (
        gen.build_db_vs_sim_rows(),
        gen.build_claude_handoff_rows(),
        gen.build_hyperposition_rows(),
    ):
        prompts = [r["prompt"] for r in rows]
        assert len(prompts) == len(set(prompts))


def test_no_cross_family_prompt_collisions():
    all_prompts = [
        r["prompt"]
        for rows in (
            gen.build_db_vs_sim_rows(),
            gen.build_claude_handoff_rows(),
            gen.build_hyperposition_rows(),
        )
        for r in rows
    ]
    assert len(all_prompts) == len(set(all_prompts))


def test_scaffolds_stay_split_exclusive():
    for rows in (
        gen.build_db_vs_sim_rows(),
        gen.build_claude_handoff_rows(),
        gen.build_hyperposition_rows(),
    ):
        for split, scaffolds in gen.SCAFFOLDS.items():
            used = {r["scaffold"] for r in rows if r["split"] == split}
            assert used <= set(scaffolds)
