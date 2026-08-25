from copy import deepcopy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


D = load("indep", "trigger2_hyperposition_independence_deriver_v1.py")
L = D.V3


def world():
    return {
        "schema": L.WORLD_SCHEMA,
        "world_id": "w1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"mode": "A"},
        "tests": {
            "t_binary": {
                "allowed_outcomes": ["YES", "NO"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 1,
                "coordination_rank": 0,
            }
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
    }


def branch(bid, value, prediction):
    return {
        "branch_id": bid,
        "v": value,
        "K": "ALWAYS",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": {"scope": "synthetic"},
        "A": {"origin": "pytest"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": {"t_binary": prediction},
    }


def state():
    return {
        "schema": L.STATE_SCHEMA,
        "query_id": "q1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [branch("h_yes", "YES_HYP", "YES"), branch("h_no", "NO_HYP", "NO")],
    }


def registry():
    return {
        "src1": {"correlation_ancestry_id": "a1", "independence_group": "g1", "payload_key": "p1"},
        "src_same_ancestry": {"correlation_ancestry_id": "a1", "independence_group": "g2", "payload_key": "p2"},
        "src_same_group": {"correlation_ancestry_id": "a3", "independence_group": "g1", "payload_key": "p3"},
        "src_same_payload": {"correlation_ancestry_id": "a4", "independence_group": "g4", "payload_key": "p1"},
        "src_novel": {"correlation_ancestry_id": "a5", "independence_group": "g5", "payload_key": "p5"},
    }


def history():
    return D.make_history("hist1", registry())


def raw_event(eid="e1", outcome="YES", source_key="src1", **extra):
    row = {
        "schema": L.EVENT_SCHEMA,
        "event_id": eid,
        "source_event_key": source_key,
        "provenance": "synthetic:pytest",
        "epistemic_type": "OBSERVED",
        "test_id": "t_binary",
        "observed_outcome": outcome,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    row.update(extra)
    return row


def first_bound_update():
    return D.bound_update(world(), state(), raw_event(), history())


def test_caller_cannot_assert_independence_or_dependence_identity():
    for field, value in [
        ("independence_qualified", True),
        ("correlation_ancestry_id", "forged"),
        ("independence_group", "forged"),
        ("payload_key", "forged"),
        ("relation", "SUPPORTS"),
    ]:
        row = raw_event(**{field: value})
        try:
            D.derive_independence(state(), row, history())
        except D.IndependenceDerivationError as exc:
            assert "CALLER_ASSERTED_DERIVED_OR_DEPENDENCE_FIELD_FORBIDDEN" in str(exc)
            continue
        raise AssertionError(field + " must fail closed")


def test_first_event_independence_is_derived_true_and_v3_accepts_it():
    result = first_bound_update()
    assert result["pass"] is True
    assert result["derivation"]["independence_qualified"] is True
    assert result["derivation"]["independence_reasons"] == []
    assert result["v3_result"]["independent_evidence_credit"] is True
    assert len(result["history_after"]["receipts"]) == 1
    assert result["training_credit_minted"] is False


def test_exact_replay_is_derived_nonindependent_and_does_not_append_receipt():
    first = first_bound_update()
    second = D.bound_update(world(), first["v3_result"]["state_after"], raw_event(), first["history_after"])
    assert second["pass"] is True
    assert second["derivation"]["exact_replay"] is True
    assert second["derivation"]["independence_qualified"] is False
    assert "EXACT_EVENT_REPLAY" in second["derivation"]["independence_reasons"]
    assert len(second["history_after"]["receipts"]) == 1


def test_same_event_id_with_different_immutable_content_is_collision_not_replay():
    first = first_bound_update()
    changed = raw_event(eid="e1", outcome="NO", source_key="src_novel")
    try:
        D.derive_independence(first["v3_result"]["state_after"], changed, first["history_after"])
    except D.IndependenceDerivationError as exc:
        assert "EVENT_ID_DIGEST_COLLISION" in str(exc)
        return
    raise AssertionError("event-id digest collision must fail closed")


def test_same_ancestry_is_mechanically_nonindependent():
    first = first_bound_update()
    d = D.derive_independence(first["v3_result"]["state_after"], raw_event(eid="e2", source_key="src_same_ancestry"), first["history_after"])
    assert d["independence_qualified"] is False
    assert "CORRELATION_ANCESTRY_REUSE" in d["independence_reasons"]


def test_same_dependence_group_is_mechanically_nonindependent():
    first = first_bound_update()
    d = D.derive_independence(first["v3_result"]["state_after"], raw_event(eid="e2", source_key="src_same_group"), first["history_after"])
    assert d["independence_qualified"] is False
    assert "DEPENDENCE_GROUP_REUSE" in d["independence_reasons"]


def test_payload_repackaging_is_mechanically_nonindependent():
    first = first_bound_update()
    d = D.derive_independence(first["v3_result"]["state_after"], raw_event(eid="e2", source_key="src_same_payload"), first["history_after"])
    assert d["independence_qualified"] is False
    assert "PAYLOAD_REPACKAGING" in d["independence_reasons"]


def test_novel_registry_identity_is_derived_independent_without_caller_bit():
    first = first_bound_update()
    d = D.derive_independence(first["v3_result"]["state_after"], raw_event(eid="e2", source_key="src_novel"), first["history_after"])
    assert d["independence_qualified"] is True
    assert d["independence_reasons"] == []


def test_registry_mutation_breaks_digest_binding():
    h = history()
    h["dependency_registry"]["src1"]["payload_key"] = "tampered"
    try:
        D.validate_history(h)
    except D.IndependenceDerivationError as exc:
        assert "DEPENDENCY_REGISTRY_DIGEST_MISMATCH" in str(exc)
        return
    raise AssertionError("registry mutation must fail closed")


def test_receipt_mutation_breaks_hash_chain():
    first = first_bound_update()
    h = deepcopy(first["history_after"])
    h["receipts"][0]["event_snapshot"]["observed_outcome"] = "NO"
    try:
        D.validate_history(h)
    except D.IndependenceDerivationError as exc:
        assert "RECEIPT_EVENT_DIGEST_MISMATCH" in str(exc)
        return
    raise AssertionError("receipt mutation must fail closed")


def test_state_history_drift_fails_closed():
    first = first_bound_update()
    try:
        D.derive_independence(first["v3_result"]["state_after"], raw_event(eid="e2", source_key="src_novel"), history())
    except D.IndependenceDerivationError as exc:
        assert "STATE_EVENT_HISTORY_DRIFT" in str(exc)
        return
    raise AssertionError("state/history drift must fail closed")


def test_source_hash_binding_mismatch_fails_closed():
    bad = {"hyperposition_labeler_v3_sha256": "0" * 64, "independence_deriver_v1_sha256": "1" * 64}
    try:
        D.bound_update(world(), state(), raw_event(), history(), expected_source_hashes=bad)
    except D.IndependenceDerivationError as exc:
        assert "SOURCE_HASH_BINDING_MISMATCH" in str(exc)
        return
    raise AssertionError("source hash mismatch must fail closed")
