from __future__ import annotations

from tools import trigger2_b6_gwt_broadcast_uptake_reentry_generator_v1 as gwt


def test_schema_and_total():
    report, families = gwt.run()
    assert report["schema"] == gwt.SCHEMA
    assert report["training_eligible"] is False
    assert report["overall_pass"] is True
    assert report["total_rows"] == 2160


def test_competition_broadcast_never_follows_majority():
    """Section 2H hard negative: collapse/selection may not occur because of
    majority/repeated agreement. Winner must always be the discriminator-score
    winner, and both agree/disagree-with-repeat-count conditions must be present
    (otherwise the majority-avoidance property is untested)."""
    report, families = gwt.run()
    r = report["reports"]["GWT_COMPETITION_BROADCAST"]
    assert r["pass"] is True
    assert r["agree_rows"] > 0
    assert r["disagree_rows"] > 0
    for row in families["GWT_COMPETITION_BROADCAST"]:
        assert row["target"] == gwt.score_winner(row["scores"])


def test_uptake_reads_broadcast_content_not_adjacent_distractors():
    report, families = gwt.run()
    r = report["reports"]["GWT_UPTAKE"]
    assert r["pass"] is True
    for row in families["GWT_UPTAKE"]:
        assert row["target"] == row["props"][row["broadcast_winner"]]
        # every role appears equally often as the broadcast winner
    assert len(set(r["winner_role_counts"].values())) == 1


def test_causal_reentry_actually_tests_reentry_not_vacuous():
    """The critical regression test: an earlier version of this generator had a
    round-2 rule design bug (shared-base-plus-fixed-offset) that made the
    round-2 answer completely independent of the round-1 winner -- 0 of 864 rows
    would have caught a model that ignored round 1 entirely. This test pins the
    fixed behavior: a large fraction of rows must be "distinguishing" (using the
    wrong round-1 winner produces a different round-2 answer)."""
    report, families = gwt.run()
    r = report["reports"]["GWT_CAUSAL_REENTRY"]
    assert r["pass"] is True
    assert r["distinguishing_rows"] > 0
    # more than half the rows should actually discriminate correct vs.
    # majority-based round-1 resolution
    assert r["distinguishing_rows"] / report["families"]["GWT_CAUSAL_REENTRY"]["rows"] > 0.5
    for row in families["GWT_CAUSAL_REENTRY"]:
        assert row["round2_scores"] == gwt.ROUND2_RULE[row["round1_winner"]]
        assert row["target"] == gwt.score_winner(row["round2_scores"])


def test_round2_rule_produces_three_distinct_winners():
    winners = {gwt.score_winner(v) for v in gwt.ROUND2_RULE.values()}
    assert winners == {"P", "Q", "R"}


def test_no_duplicate_prompts_within_any_family():
    _report, families = gwt.run()
    for name, rows in families.items():
        prompts = [r["prompt"] for r in rows]
        assert len(prompts) == len(set(prompts)), f"{name} has duplicate prompts"


def test_family_and_curriculum_family_keys_both_present():
    """Cross-family consolidation convention (see the sibling B6 system-
    integration generator's fix): both 'family' and 'curriculum_family' keys
    must be present so downstream code can group rows either way."""
    _report, families = gwt.run()
    for rows in families.values():
        for row in rows[:5]:
            assert row["family"] == row["curriculum_family"]
