from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools import trigger2_hyperposition_state_history_proof_gate_v1 as proof
from tools import trigger2_observed_evidence_producer_v1 as observed_producer

REPO = Path(__file__).resolve().parents[1]


def _test_spec():
    return {
        "allowed_outcomes": ["A", "B"],
        "mismatch_effect": "FALSIFIES",
        "risk_rank": 0,
        "cost_rank": 0,
        "coordination_rank": 0,
    }


def _branch(branch_id: str, prediction: str):
    return {
        "branch_id": branch_id,
        "v": branch_id,
        "K": "ALWAYS",
        "E_plus": [], "E_minus": [], "F": [],
        "T": {"scope": "synthetic"},
        "A": {"origin": "trigger2-test"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": {"t1": prediction},
    }


def _state():
    return {
        "schema": proof.lab.STATE_SCHEMA,
        "query_id": "q1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [_branch("winner", "A"), _branch("loser", "B")],
    }


def _event(*, event_id="e1", outcome="A", epistemic="SYNTHETIC_PROOF", qualified=False, payload="p1"):
    return {
        "schema": proof.lab.EVENT_SCHEMA,
        "event_id": event_id,
        "correlation_ancestry_id": "a:" + event_id,
        "independence_group": "g:" + event_id,
        "payload_key": payload,
        "provenance": "synthetic:test",
        "epistemic_type": epistemic,
        "test_id": "t1",
        "observed_outcome": outcome,
        "independence_qualified": qualified,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def _world(events):
    registry_events = {}
    for e in events:
        registry_events[e["event_id"]] = {
            "correlation_ancestry_id": e["correlation_ancestry_id"],
            "independence_group": e["independence_group"],
            "payload_key": e["payload_key"],
            "provenance": e["provenance"],
            "test_id": e["test_id"],
            "observed_outcome": e["observed_outcome"],
            "depends_on_event_ids": [],
        }
    return {
        "schema": proof.lab.WORLD_SCHEMA,
        "world_id": "w1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"scope": "synthetic"},
        "tests": {"t1": _test_spec()},
        "merge_policy": "NONE",
        "branch_birth_rules": [],
        "event_dependence_registry": {
            "schema": proof.base.DEPENDENCE_SCHEMA,
            "events": registry_events,
        },
    }


def _disc_receipt(world, state, event, *, executed=True):
    digest = proof.event_semantic_sha256(event)
    ordering = proof.lab.u_test_order(world, state, [event["test_id"]])["ordering"][0]
    return {
        "schema": proof.DISCRIMINATOR_RECEIPT_SCHEMA,
        "execution_receipt_id": "exec:" + event["event_id"],
        "event_id": event["event_id"],
        "test_id": event["test_id"],
        "observed_outcome": event["observed_outcome"],
        "event_semantic_sha256": digest,
        "world_sha256": proof._world_sha256(world),
        "admissible": True,
        "executed": executed,
        "separated_live_pairs": ordering["separated_live_pairs"],
        "separates_all_live_pairs": ordering["separates_all_live_pairs"],
    }


def _base_target(world, before, event):
    indep = proof.base.derive_independence(world, before, event)
    event2 = deepcopy(event)
    event2["independence_qualified"] = bool(indep["derived_independence_qualified"])
    update = proof.lab.u_state(world, before, event2)
    resolution = proof.lab.d_resolve(world, update["state_after"])
    return {
        "state_after": update.get("state_after"),
        "updates": update.get("updates"),
        "derivation_receipt": update.get("derivation_receipt"),
        "independent_evidence_credit": update.get("independent_evidence_credit"),
        "nonindependence_reasons": update.get("nonindependence_reasons"),
        "task_resolution": resolution.get("resolution"),
    }


def _history_target(world, before, event):
    indep = proof.base.derive_independence(world, before, event)
    event2 = deepcopy(event)
    event2["independence_qualified"] = bool(indep["derived_independence_qualified"])
    update = proof.lab.u_state(world, before, event2)
    state_after = deepcopy(update["state_after"])
    digest = proof.event_semantic_sha256(event)
    proof._decorate_event_records(state_after, event["event_id"], digest)
    resolution = proof.lab.d_resolve(world, state_after)["resolution"]
    elimination = {}
    if resolution["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD":
        winner = resolution["resolved_branch"]
        for branch in state_after["branches"]:
            if branch["branch_id"] != winner and branch["sigma"] == "FALSIFIED":
                elimination[branch["branch_id"]] = sorted({r["event_id"] for r in branch["F"]})
    return {
        "state_after": state_after,
        "task_resolution": resolution,
        "event_sha256": digest,
        "eliminated_competitor_event_ids": elimination,
    }


def _row(*, epistemic="SYNTHETIC_PROOF", qualified=False):
    event = _event(epistemic=epistemic, qualified=qualified)
    world = _world([event])
    genesis = _state()
    binding = proof.base.current_source_binding("tools/trigger2_semantic_hyperposition_native_seed_generator_v2.py")
    assert binding["pass"]
    return {
        "schema": proof.base.ROW_SCHEMA,
        "evidence_class": "SYNTHETIC_DETERMINISTIC_LABEL",
        "reality_level": "R2",
        "fact_status": "NOT_APPLICABLE",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "model_visible_fields": ["prompt"],
        "prompt": "Synthetic discriminator proof test.",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "source_binding": {k: v for k, v in binding.items() if k != "pass"},
        "formal_task_world_evaluator_only": world,
        "synthetic_test_event_evaluator_only": event,
        "hyperposition_state_before_evaluator_only": deepcopy(genesis),
        "v3_reference_target_evaluator_only": _base_target(world, genesis, event),
        "hyperposition_genesis_state_evaluator_only": deepcopy(genesis),
        "synthetic_event_history_evaluator_only": [],
        "event_digest_registry_evaluator_only": {
            "schema": proof.DIGEST_REGISTRY_SCHEMA,
            "events": {event["event_id"]: proof.event_semantic_sha256(event)},
        },
        "discriminator_execution_receipts_evaluator_only": [_disc_receipt(world, genesis, event)],
        "typed_observation_evidence_receipts_evaluator_only": [],
        "state_history_reference_target_evaluator_only": _history_target(world, genesis, event),
    }


def test_happy_path_passes_and_caller_independence_boolean_is_not_authority():
    result = proof.adjudicate(_row(qualified=False))
    assert result["pass"], result
    assert result["caller_independence_boolean_authoritative"] is False
    assert result["replay_matches_supplied_state"] is True


def test_preseeded_falsified_state_without_replay_fails_closed():
    row = _row()
    row["hyperposition_state_before_evaluator_only"]["branches"][1]["sigma"] = "FALSIFIED"
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert "SUPPLIED_STATE_BEFORE_NOT_EXACT_REPLAY_OF_GENESIS_HISTORY" in result["failures"]


def test_same_event_id_different_payload_digest_fails_closed():
    row = _row()
    row["synthetic_test_event_evaluator_only"]["payload_key"] = "mutated"
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert any("EVENT_DIGEST_REGISTRY_MISMATCH" in x for x in result["failures"])


def test_unexecuted_discriminator_fails_closed():
    row = _row()
    row["discriminator_execution_receipts_evaluator_only"][0]["executed"] = False
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_NOT_EXECUTED" in result["failures"]


def test_discriminator_outcome_not_bound_fails_closed():
    row = _row()
    row["discriminator_execution_receipts_evaluator_only"][0]["observed_outcome"] = "B"
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_OUTCOME_MISMATCH" in result["failures"]


def test_discriminator_coverage_mutation_fails_closed():
    row = _row()
    row["discriminator_execution_receipts_evaluator_only"][0]["separated_live_pairs"] = 0
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_COVERAGE_COUNT_MISMATCH" in result["failures"]


def test_observed_event_requires_typed_evidence_receipt():
    result = proof.adjudicate(_row(epistemic="OBSERVED"))
    assert not result["pass"]
    assert "OBSERVED_EVENT_REQUIRES_EXACTLY_ONE_TYPED_EVIDENCE_RECEIPT" in result["failures"]


def _observed_authority_policy():
    return json.loads(
        (REPO / "research_entity/global/j-space/research/TRIGGER2_OBSERVED_EVIDENCE_PRODUCER_AUTHORITY_V1.json")
        .read_text(encoding="utf-8")
    )["policy"]


def _authorized_admission():
    return {"admission_id": "T2_OBS_ADMISSION_SYNTHETIC_PILOT_V1", "generation": 1}


def _observed_row_with_authenticated_receipt(*, source_payload=None, admission=None, tamper=None):
    """Build an OBSERVED-epistemic row whose typed evidence receipt is authenticated via
    the trusted producer/policy/admission scope, not a caller-typed string bundle."""
    row = _row(epistemic="OBSERVED")
    event = row["synthetic_test_event_evaluator_only"]
    digest = proof.event_semantic_sha256(event)
    payload = source_payload if source_payload is not None else {"synthetic_db_row": "value-1"}
    adm = admission if admission is not None else _authorized_admission()
    receipt = observed_producer.produce(
        causal_event_id=event["event_id"],
        event_semantic_sha256=digest,
        observed_value=event["observed_outcome"],
        source_payload=payload,
        admission=adm,
        policy=_observed_authority_policy(),
        observed_time="2026-08-25T00:00:00Z",
    )
    if tamper is not None:
        receipt = tamper(dict(receipt))
    row["typed_observation_evidence_receipts_evaluator_only"] = [receipt]
    row["observed_evidence_source_payloads_evaluator_only"] = {event["event_id"]: payload}
    row["observed_evidence_admissions_evaluator_only"] = {event["event_id"]: adm}
    return row


def test_observed_event_authenticated_receipt_passes():
    row = _observed_row_with_authenticated_receipt()
    result = proof.adjudicate(row)
    assert result["pass"], result


def test_observed_event_caller_forged_receipt_fails_closed():
    """The exact gap Track A confirmed: a schema-valid, well-typed but caller-forged
    receipt (fabricated source/provenance/receipt_id, no producer authentication) must
    now be rejected rather than accepted."""
    row = _row(epistemic="OBSERVED")
    event = row["synthetic_test_event_evaluator_only"]
    row["typed_observation_evidence_receipts_evaluator_only"] = [{
        "schema": proof.OBSERVATION_RECEIPT_SCHEMA,
        "receipt_id": "obs:forged",
        "event_id": event["event_id"],
        "event_semantic_sha256": proof.event_semantic_sha256(event),
        "source": "totally-forged-source",
        "provenance": "totally-forged-provenance",
        "observed_time": "2026-08-25T00:00:00Z",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }]
    row["observed_evidence_source_payloads_evaluator_only"] = {event["event_id"]: {"synthetic_db_row": "value-1"}}
    row["observed_evidence_admissions_evaluator_only"] = {event["event_id"]: _authorized_admission()}
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert any("OBSERVED_PRODUCER_AUTH" in f for f in result["failures"])


def test_observed_event_missing_source_payload_fails_closed():
    row = _observed_row_with_authenticated_receipt()
    event = row["synthetic_test_event_evaluator_only"]
    row["observed_evidence_source_payloads_evaluator_only"] = {}
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert "OBSERVED_EVIDENCE_SOURCE_PAYLOAD_REQUIRED" in result["failures"]


def test_observed_event_wrong_source_payload_fails_closed():
    row = _observed_row_with_authenticated_receipt()
    event = row["synthetic_test_event_evaluator_only"]
    row["observed_evidence_source_payloads_evaluator_only"] = {event["event_id"]: {"synthetic_db_row": "TAMPERED"}}
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert any("OBSERVED_PRODUCER_AUTH" in f for f in result["failures"])


def test_observed_event_wrong_admission_id_fails_closed():
    row = _observed_row_with_authenticated_receipt()
    event = row["synthetic_test_event_evaluator_only"]
    row["observed_evidence_admissions_evaluator_only"] = {
        event["event_id"]: {"admission_id": "UNAUTHORIZED_ADMISSION", "generation": 1}
    }
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert any("OBSERVED_PRODUCER_AUTH" in f for f in result["failures"])


def test_observed_event_wrong_admission_generation_fails_closed():
    row = _observed_row_with_authenticated_receipt()
    event = row["synthetic_test_event_evaluator_only"]
    row["observed_evidence_admissions_evaluator_only"] = {
        event["event_id"]: {"admission_id": "T2_OBS_ADMISSION_SYNTHETIC_PILOT_V1", "generation": 99}
    }
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert any("OBSERVED_PRODUCER_AUTH" in f for f in result["failures"])


def test_observed_event_stale_authority_producer_hash_fails_closed(monkeypatch):
    """If the authority's pinned producer source hash drifts from the actual file on
    disk, the gate must fail closed rather than silently trust either side."""
    authority_path = REPO / "research_entity/global/j-space/research/TRIGGER2_OBSERVED_EVIDENCE_PRODUCER_AUTHORITY_V1.json"
    original = json.loads(authority_path.read_text(encoding="utf-8"))
    tampered = deepcopy(original)
    tampered["producer"]["source_sha256"] = "0" * 64
    authority_path.write_text(json.dumps(tampered), encoding="utf-8")
    try:
        row = _observed_row_with_authenticated_receipt()
        result = proof.adjudicate(row)
    finally:
        authority_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    assert not result["pass"]
    assert any("EXPECTED_OBSERVED_PRODUCER_SOURCE_SHA256_MISMATCH" in f for f in result["failures"])


def test_observed_event_reused_receipt_id_with_changed_observed_value_fails_closed():
    """A receipt authenticated for one observed_value must not validate against a row
    that silently changed the event's observed_outcome afterward -- the receipt is bound
    to the exact observed value, not just the event id."""
    row = _observed_row_with_authenticated_receipt()
    event = row["synthetic_test_event_evaluator_only"]
    event["observed_outcome"] = "B" if event["observed_outcome"] != "B" else "A"
    result = proof.adjudicate(row)
    assert not result["pass"]
    # mutating observed_outcome also changes the event's own semantic digest, so this is
    # caught by digest binding as well as producer-receipt mismatch -- either failure mode
    # proves the reused-receipt-with-changed-payload case is closed.
    assert any(
        "OBSERVED_PRODUCER_AUTH" in f or "EVENT_DIGEST_REGISTRY_MISMATCH" in f or "DISCRIMINATOR_OUTCOME_MISMATCH" in f
        for f in result["failures"]
    )


def test_observed_event_missing_discriminator_receipt_fails_closed():
    """PDF-required negative case: an OBSERVED event still needs its own discriminator
    execution receipt (the 'parent' admissibility proof) -- evidence authentication does
    not substitute for it."""
    row = _observed_row_with_authenticated_receipt()
    row["discriminator_execution_receipts_evaluator_only"] = []
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_EXECUTION_RECEIPT_REQUIRED" in result["failures"]


def test_missing_state_history_claim_fails_closed():
    row = _row()
    row.pop("state_history_reference_target_evaluator_only")
    result = proof.adjudicate(row)
    assert not result["pass"]
    assert "STATE_HISTORY_REFERENCE_TARGET_REQUIRED" in result["failures"]
