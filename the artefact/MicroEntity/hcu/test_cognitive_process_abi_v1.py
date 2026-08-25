from __future__ import annotations

import pytest

from cognitive_process_abi_v1 import (
    CognitiveABIError,
    create_work,
    claim_work,
    create_result,
    decide_integration,
    create_effect_request,
)

H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64
H4 = "4" * 64


def work(process_id="AZP06", **kw):
    args = dict(
        causal_event_id="causal-1",
        admission_id="admission-A",
        workspace_episode_id="ws-1",
        process_id=process_id,
        objective_ref="blob:objective",
        objective={"goal": "solve", "x": 1},
        input_refs=("state:a", "evidence:b"),
        precondition_refs=("pre:1",),
        completion_criteria_refs=("done:1",),
        semantic_generation=7,
    )
    args.update(kw)
    return create_work(**args)


def claim(w, **kw):
    args = dict(
        route_decision_id="route-1",
        executor_id="node-A",
        executor_runtime_sha256=H1,
        executor_generation=3,
        state_epoch=9,
        state_digest=H2,
        capability_authority_sha256=H3,
        coordinator_lease_id="lease-1",
        attempt=1,
    )
    args.update(kw)
    return claim_work(w, **args)


def result(w, c, **kw):
    args = dict(
        payload_ref="blob:result",
        payload={"answer": 42},
        epistemic_class="CANDIDATE",
        evidence_refs=("ev:1",),
    )
    args.update(kw)
    return create_result(w, c, **args)


def test_work_identity_is_size_and_node_independent():
    a = work()
    b = work()
    assert a.work_id == b.work_id
    assert not hasattr(a, "executor_id")
    assert not hasattr(a, "grid_size")


def test_transport_admission_id_does_not_fork_semantic_work():
    a = work(admission_id="admission-A")
    b = work(admission_id="admission-B")
    assert a.work_id == b.work_id
    assert a.admission_id != b.admission_id


def test_semantic_change_changes_work_id():
    a = work()
    b = work(objective={"goal": "solve", "x": 2})
    c = work(process_id="AZP07")
    assert a.work_id != b.work_id
    assert a.work_id != c.work_id


def test_rejoin_preserves_work_but_changes_claim():
    w = work()
    c1 = claim(w, executor_id="node-A", executor_generation=3, attempt=1)
    c2 = claim(w, executor_id="node-B", executor_generation=4, attempt=2)
    assert c1.work_id == c2.work_id == w.work_id
    assert c1.claim_id != c2.claim_id


def test_claim_binds_external_authority_and_state():
    w = work()
    c1 = claim(w)
    c2 = claim(w, capability_authority_sha256=H4)
    c3 = claim(w, state_epoch=10)
    assert c1.claim_id != c2.claim_id
    assert c1.claim_id != c3.claim_id


def test_result_cannot_self_grant_truth_or_effect():
    w = work()
    c = claim(w)
    with pytest.raises(CognitiveABIError):
        result(w, c, truth_authority=True)
    with pytest.raises(CognitiveABIError):
        result(w, c, effect_authority=True)


def test_unknown_is_not_negative_or_completed():
    w = work()
    c = claim(w)
    r = result(w, c, status="UNKNOWN", epistemic_class="UNKNOWN")
    assert r.status == "UNKNOWN"
    assert r.epistemic_class == "UNKNOWN"
    with pytest.raises(CognitiveABIError):
        result(w, c, status="UNKNOWN", epistemic_class="CANDIDATE")


def test_jspace_must_remain_measurement_counterevidence_or_unknown():
    w = work(process_id="AZP09")
    c = claim(w)
    r = result(w, c, epistemic_class="MEASUREMENT")
    assert r.truth_authority is False
    with pytest.raises(CognitiveABIError):
        result(w, c, epistemic_class="OBSERVED")


def test_parallel_s1_advance_requires_rebase_not_identity_rewrite():
    w = work()
    c = claim(w)
    r = result(w, c)
    d = decide_integration(
        r,
        current_state_epoch=10,
        current_state_digest=H4,
        coordinator_lease_id="lease-current",
        lease_valid=True,
        scope_allows_process=True,
    )
    assert d.action == "REBASE_REQUIRED"
    assert d.result_id == r.result_id
    assert d.s0_truth_authority is False
    assert d.effect_authority is False


def test_exact_base_allows_s1_candidate_admission_only():
    w = work()
    c = claim(w)
    r = result(w, c)
    d = decide_integration(
        r,
        current_state_epoch=c.state_epoch,
        current_state_digest=c.state_digest,
        coordinator_lease_id="lease-current",
        lease_valid=True,
        scope_allows_process=True,
    )
    assert d.action == "ADMIT_S1"
    assert d.s1_only is True
    assert d.s0_truth_authority is False


def test_invalid_coordinator_lease_rejects_even_current_result():
    w = work()
    c = claim(w)
    r = result(w, c)
    d = decide_integration(
        r,
        current_state_epoch=c.state_epoch,
        current_state_digest=c.state_digest,
        coordinator_lease_id="lease-stale",
        lease_valid=False,
        scope_allows_process=True,
    )
    assert d.action == "REJECT"


def test_effect_request_is_azp11_propose_only():
    w = work(process_id="AZP11")
    c = claim(w)
    r = result(w, c)
    e = create_effect_request(
        w,
        r,
        effect_type="WRITE_FILE",
        payload_ref="blob:effect",
        payload={"path": "x", "data": "y"},
        capability_scope_ref="cap:scope",
        generation=7,
    )
    assert e.effect_authority is False
    assert e.process_id == "AZP11"

    w2 = work(process_id="AZP06")
    c2 = claim(w2)
    r2 = result(w2, c2)
    with pytest.raises(CognitiveABIError):
        create_effect_request(
            w2,
            r2,
            effect_type="WRITE_FILE",
            payload_ref="blob:effect",
            payload={"path": "x"},
            capability_scope_ref="cap:scope",
            generation=7,
        )


def test_claim_result_mismatch_fails_closed():
    w1 = work()
    w2 = work(objective={"goal": "different"})
    c = claim(w1)
    with pytest.raises(CognitiveABIError):
        result(w2, c)


def test_duplicate_refs_fail_closed():
    with pytest.raises(CognitiveABIError):
        work(input_refs=("x", "x"))
