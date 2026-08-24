from __future__ import annotations

import json
from unittest import mock

import tools.run_research_distillery_entry as entry


def _high_vote():
    return {
        "intrinsic_consistency": 0.95,
        "grf_compatibility": 0.95,
        "project_fit": 0.95,
        "novelty": 0.95,
        "evidence_support": 0.95,
        "supported_source_ids": ["s-1"],
        "unsupported_claims": [],
        "hard_contradiction": False,
        "reason": "supported",
    }


def test_goodman_collapsed_fallback_is_provisional_but_never_canonically_accepted():
    con = mock.MagicMock()
    row = {"question": "q", "signature": "a"}
    evidence = [{
        "id": "s-1", "chunk_sha256": "a" * 64, "source_type": "test",
        "title": "t", "url": "https://example.invalid", "chunk_text": "bounded evidence",
    }]
    reviewers = [
        ("nvidia_reviewer", "nvidia", "nvidia/model"),
        ("fallback_reviewer_1", "openrouter", "openrouter/free"),
        ("fallback_reviewer_2", "openrouter", "openrouter/free"),
    ]
    replies = [json.dumps(_high_vote()) for _ in reviewers]

    def chat(*args, **kwargs):
        return True, replies.pop(0), {}, "OK"

    with mock.patch.object(entry, "provider_is_admitted_free", return_value=True), \
         mock.patch.object(entry, "_candidate_evidence", return_value=(row, {"source_ids": ["s-1"]}, ["s-1"], evidence, "OK")), \
         mock.patch.object(entry.d, "chat", side_effect=chat), \
         mock.patch.object(entry.d, "emit"):
        accepted, agg = entry.review_candidate(con, "c-1", reviewers)

    assert accepted is False
    assert agg["panel_class"] == "PROVISIONAL_NON_MISTRAL_FALLBACK"
    assert agg["independence_class"] == "GOODMAN_COLLAPSED_FREE_ROUTER_FALLBACK"
    assert agg["canonical_acceptance"] is False
    assert agg["fact_credit"] == 0
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
        "fact_credit": 0,
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
