from __future__ import annotations

from unittest import mock

import tools.run_research_distillery_entry as entry


def _high_fallback_votes():
    return [
        ("nvidia_reviewer", "nvidia", "nvidia/model", 0.95, 0.95, 0.95, 0.95, 0),
        ("fallback_reviewer_1", "openrouter", "openrouter/free", 0.95, 0.95, 0.95, 0.95, 0),
        ("fallback_reviewer_2", "openrouter", "openrouter/free", 0.95, 0.95, 0.95, 0.95, 0),
    ]


def test_goodman_collapsed_fallback_is_provisional_but_never_canonically_accepted():
    con = mock.MagicMock()
    con.execute.return_value.fetchall.return_value = _high_fallback_votes()
    reviewers = [
        ("nvidia_reviewer", "nvidia", "nvidia/model"),
        ("fallback_reviewer_1", "openrouter", "openrouter/free"),
        ("fallback_reviewer_2", "openrouter", "openrouter/free"),
    ]

    with mock.patch.object(entry, "provider_is_admitted_free", return_value=True), \
         mock.patch.object(entry, "_ORIGINAL_REVIEW", return_value=(True, {"votes": 3})), \
         mock.patch.object(entry.d, "emit"):
        accepted, agg = entry.review_candidate(con, "c-1", reviewers)

    assert accepted is False
    assert agg["panel_class"] == "PROVISIONAL_NON_MISTRAL_FALLBACK"
    assert agg["independence_class"] == "GOODMAN_COLLAPSED_FREE_ROUTER_FALLBACK"
    assert agg["canonical_acceptance"] is False
    assert any(
        call.args
        and "UPDATE candidates SET status='PROVISIONAL_ACCEPTED'" in str(call.args[0])
        for call in con.execute.call_args_list
    )
    assert not any(
        call.args and "SET status='ACCEPTED'" in str(call.args[0])
        for call in con.execute.call_args_list
    )


def test_one_cycle_false_review_result_cannot_reach_compress_and_commit():
    con = mock.MagicMock()
    con.execute.return_value.fetchone.return_value = None
    question = {"id": "q-1", "root_problem": "root", "depth": 0, "priority": 1.0}
    provisional = {
        "panel_class": "PROVISIONAL_NON_MISTRAL_FALLBACK",
        "independence_class": "GOODMAN_COLLAPSED_FREE_ROUTER_FALLBACK",
        "canonical_acceptance": False,
    }

    with mock.patch.object(entry.d, "extract_questions_from_workers"), \
         mock.patch.object(entry.d, "choose_question", return_value=question), \
         mock.patch.object(entry.d, "devise_novel_approach", return_value=(1, {})), \
         mock.patch.object(entry.d, "collect_sources", return_value=["s-1"]), \
         mock.patch.object(entry.d, "synthesize", return_value="c-1"), \
         mock.patch.object(entry.d, "add_decompositions"), \
         mock.patch.object(entry.d, "review_candidate", return_value=(False, provisional)), \
         mock.patch.object(entry.d, "compress_and_commit", side_effect=AssertionError("canonical commit reached")) as compress, \
         mock.patch.object(entry.d, "reject_and_purge") as reject, \
         mock.patch.object(entry.d, "emit"):
        accepted = entry.d.one_cycle(con, ["openrouter/free"], [])

    assert accepted is False
    compress.assert_not_called()
    reject.assert_called_once_with(con, "c-1")
