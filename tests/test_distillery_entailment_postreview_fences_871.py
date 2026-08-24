from __future__ import annotations

import json
from unittest import mock

import tools.run_research_distillery_entry as entry


def _row():
    return {
        "question": "q",
        "root_problem": "root",
        "question_id": "q-1",
        "signature": "approach",
        "source_chunk_ids_json": json.dumps(["s-1"]),
    }


def _evidence(text: str):
    return [{
        "id": "s-1",
        "source_type": "test",
        "source_id": "src",
        "title": "title",
        "url": "https://example.invalid",
        "author": "",
        "published": "",
        "license": "",
        "chunk_sha256": "a" * 64,
        "approx_tokens": 1,
        "metadata_json": "{}",
        "chunk_text": text,
    }]


def test_review_budget_overflow_fails_closed_without_silent_evidence_truncation():
    con=mock.MagicMock()
    evidence=_evidence("x" * (entry.MAX_REVIEW_EVIDENCE_CHARS + 1))
    reviewers=[("nvidia_reviewer","nvidia","nvidia/model")]
    with mock.patch.object(entry,"provider_is_admitted_free",return_value=True), \
         mock.patch.object(entry,"_candidate_evidence",return_value=(_row(),{"source_ids":["s-1"]},["s-1"],evidence,"OK")), \
         mock.patch.object(entry.d,"chat",side_effect=AssertionError("review transport must not run")), \
         mock.patch.object(entry.d,"emit"):
        accepted,agg=entry.review_candidate(con,"c-1",reviewers)
    assert accepted is False
    assert agg["evidence_state"]=="CITED_EVIDENCE_REVIEW_BUDGET_EXCEEDED"
    assert agg["canonical_acceptance"] is False
    assert any(
        call.args and "REJECTED_EVIDENCE_BOUNDARY" in str(call.args[0])
        for call in con.execute.call_args_list
    )


def test_commit_is_deterministic_and_never_calls_post_review_model_compression():
    con=mock.MagicMock()
    con.execute.return_value.fetchone.return_value=("ACCEPTED",)
    row=_row()
    packet={
        "claim":"supported claim","mechanism":"m","grf_relation":"g","falsifier":"f",
        "predicted_architecture_delta":"d","counterevidence":"none","source_ids":["s-1"],
    }
    agg={
        "canonical_acceptance":True,"fact_credit":0,"supported_source_ids":["s-1"],
        "intrinsic":0.95,"grf":0.95,"fit":0.95,"novelty":0.95,
    }
    with mock.patch.object(entry,"_candidate_evidence",return_value=(row,packet,["s-1"],_evidence("bounded evidence"),"OK")), \
         mock.patch.object(entry,"_bump"), \
         mock.patch.object(entry.d,"chat",side_effect=AssertionError("post-review model rewrite forbidden")):
        kid=entry.compress_and_commit(con,"c-1",agg,["openrouter/free"])
    assert kid and kid.startswith("k-")
    inserts=[call for call in con.execute.call_args_list if call.args and "INSERT OR REPLACE INTO knowledge_packets" in str(call.args[0])]
    assert len(inserts)==1
    metadata=json.loads(inserts[0].args[1][4])
    assert metadata["post_review_model_compression"] is False
    assert metadata["fact_credit"]==0
