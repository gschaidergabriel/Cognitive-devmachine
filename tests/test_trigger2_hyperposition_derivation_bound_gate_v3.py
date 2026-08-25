from copy import deepcopy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_hyperposition_derivation_bound_gate_v3.py"
GENERATOR = "tools/trigger2_context_binding_generator_v2.py"
spec = importlib.util.spec_from_file_location("gate", P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def _base_state():
    return {
        "schema": gate.lab.STATE_SCHEMA,
        "query_id": "q1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [
            {
                "branch_id": "b1",
                "v": "YES_BRANCH",
                "K": "ALWAYS",
                "E_plus": [],
                "E_minus": [],
                "F": [],
                "T": {"scope": "synthetic"},
                "A": {"origin": "test"},
                "sigma": "LIVE_UNRESOLVED",
                "projection_visibility": True,
                "predictions": {"t1": "YES"},
            },
            {
                "branch_id": "b2",
                "v": "NO_BRANCH",
                "K": "ALWAYS",
                "E_plus": [],
                "E_minus": [],
                "F": [],
                "T": {"scope": "synthetic"},
                "A": {"origin": "test"},
                "sigma": "LIVE_UNRESOLVED",
                "projection_visibility": True,
                "predictions": {"t1": "NO"},
            },
        ],
    }


def _event(*, epistemic="SYNTHETIC_PROOF", outcome="YES", independent=True):
    return {
        "schema": gate.lab.EVENT_SCHEMA,
        "event_id": "e1",
        "correlation_ancestry_id": "a1",
        "independence_group": "g1",
        "payload_key": "p1",
        "provenance": "synthetic:test",
        "epistemic_type": epistemic,
        "test_id": "t1",
        "observed_outcome": outcome,
        "independence_qualified": independent,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def _registry_entry(event):
    return {
        "correlation_ancestry_id": event["correlation_ancestry_id"],
        "independence_group": event["independence_group"],
        "payload_key": event["payload_key"],
        "provenance": event["provenance"],
        "test_id": event["test_id"],
        "observed_outcome": event["observed_outcome"],
        "depends_on_event_ids": [],
        "event_content_sha256": gate.event_content_sha256(event),
    }


def _receipt(event, *, observation_qualified=False):
    receipt = {
        "schema": gate.DISCRIMINATOR_SCHEMA,
        "receipt_id": "dr1",
        "test_id": event["test_id"],
        "world_id": "w1",
        "event_id": event["event_id"],
        "event_content_sha256": gate.event_content_sha256(event),
        "observed_outcome": event["observed_outcome"],
        "admissible": True,
        "executed": True,
        "coverage_complete": True,
        "covered_branch_ids": ["b1", "b2"],
        "observation_qualified": observation_qualified,
        "execution_identity": {
            "executor_id": "synthetic-evaluator",
            "execution_id": "run-1",
            "source_sha256": "a" * 64,
        },
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    receipt["receipt_sha256"] = gate.discriminator_receipt_sha256(receipt)
    return receipt


def _world(event, *, observation_qualified=False):
    return {
        "schema": gate.lab.WORLD_SCHEMA,
        "world_id": "w1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"scope": "synthetic"},
        "tests": {
            "t1": {
                "allowed_outcomes": ["YES", "NO"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            }
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
        "event_dependence_registry": {
            "schema": gate.DEPENDENCE_SCHEMA,
            "events": {event["event_id"]: _registry_entry(event)},
        },
        "discriminator_receipts": {
            event["test_id"]: _receipt(event, observation_qualified=observation_qualified)
        },
    }


def _claimed(world, state, event):
    base_world = gate._world_for_base(world)
    independence = gate.base.derive_independence(base_world, state, event)
    assert independence["pass"], independence
    event_for_lab = deepcopy(event)
    event_for_lab["independence_qualified"] = independence["derived_independence_qualified"]
    update = gate.lab.u_state(base_world, state, event_for_lab)
    assert update["pass"], update
    resolution = gate.lab.d_resolve(base_world, update["state_after"])
    assert resolution["pass"], resolution
    return {
        "state_after": update["state_after"],
        "updates": update["updates"],
        "derivation_receipt": update["derivation_receipt"],
        "independent_evidence_credit": update["independent_evidence_credit"],
        "nonindependence_reasons": update["nonindependence_reasons"],
        "task_resolution": resolution["resolution"],
    }


def _row(*, event=None, state=None, world=None):
    event = deepcopy(event or _event())
    state = deepcopy(state or _base_state())
    world = deepcopy(world or _world(event, observation_qualified=event["epistemic_type"] == "OBSERVED"))
    binding = gate.current_source_binding(GENERATOR)
    assert binding["pass"], binding
    return {
        "schema": gate.base.ROW_SCHEMA,
        "evidence_class": "SYNTHETIC_DETERMINISTIC_LABEL",
        "reality_level": "R2",
        "fact_status": "NOT_APPLICABLE",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "model_visible_fields": ["prompt"],
        "prompt": "Resolve the synthetic discriminator-bound Hyperposition transition.",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "source_binding": {k: v for k, v in binding.items() if k != "pass"},
        "formal_task_world_evaluator_only": world,
        "synthetic_test_event_evaluator_only": event,
        "hyperposition_state_before_evaluator_only": state,
        "v3_reference_target_evaluator_only": _claimed(world, state, event),
    }


def _rehash_receipt(receipt):
    receipt["receipt_sha256"] = gate.discriminator_receipt_sha256(receipt)


def test_valid_v3_row_passes_and_mints_no_credit():
    row = _row()
    result = gate.adjudicate(row)
    assert result["pass"], result
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0
    assert result["jspace_runtime_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    digest = result["event_identity_binding"]["event_content_sha256"]
    records = []
    for branch in result["identity_bound_state_after"]["branches"]:
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            records.extend(branch.get(field, []))
    current = [r for r in records if r.get("event_id") == "e1"]
    assert current
    assert all(r["event_content_sha256"] == digest for r in current)
    assert all(r["discriminator_receipt_sha256"] for r in current)


def test_event_mutation_with_stale_registry_digest_fails_closed():
    row = _row()
    row["synthetic_test_event_evaluator_only"]["observed_outcome"] = "NO"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("EVENT_CONTENT_DIGEST_MISMATCH" in x for x in result["failures"])


def test_same_event_id_cannot_be_rebound_to_different_content():
    first = gate.adjudicate(_row())
    assert first["pass"], first
    state = first["identity_bound_state_after"]
    changed = _event(outcome="NO")
    world = _world(changed)
    row = _row(event=changed, state=state, world=world)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("EVENT_ID_REBOUND_TO_DIFFERENT_CONTENT" in x for x in result["failures"])


def test_same_id_legacy_record_without_digest_is_not_treated_as_exact_replay():
    first = gate.adjudicate(_row())
    assert first["pass"], first
    state = deepcopy(first["identity_bound_state_after"])
    for branch in state["branches"]:
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for record in branch.get(field, []):
                if record.get("event_id") == "e1":
                    record.pop("event_content_sha256", None)
    row = _row(state=state)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("PRIOR_EVENT_DIGEST_MISSING_FOR_SAME_ID" in x for x in result["failures"])


def test_missing_or_unexecuted_discriminator_receipt_fails_closed():
    row = _row()
    row["formal_task_world_evaluator_only"].pop("discriminator_receipts")
    missing = gate.adjudicate(row)
    assert not missing["pass"]
    assert any("DISCRIMINATOR_RECEIPTS_REQUIRED" in x for x in missing["failures"])

    row = _row()
    receipt = row["formal_task_world_evaluator_only"]["discriminator_receipts"]["t1"]
    receipt["executed"] = False
    _rehash_receipt(receipt)
    unexecuted = gate.adjudicate(row)
    assert not unexecuted["pass"]
    assert any("DISCRIMINATOR_NOT_EXECUTED" in x for x in unexecuted["failures"])


def test_discriminator_must_cover_exact_formal_target_branch_set():
    row = _row()
    receipt = row["formal_task_world_evaluator_only"]["discriminator_receipts"]["t1"]
    receipt["covered_branch_ids"] = ["b1"]
    _rehash_receipt(receipt)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("DISCRIMINATOR_BRANCH_COVERAGE_MISMATCH" in x for x in result["failures"])


def test_observed_event_requires_typed_observation_qualification():
    event = _event(epistemic="OBSERVED")
    world = _world(event, observation_qualified=False)
    row = _row(event=event, world=world)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("OBSERVED_EVENT_REQUIRES_TYPED_OBSERVATION_RECEIPT" in x for x in result["failures"])


def test_caller_independence_boolean_remains_non_authoritative():
    event = _event(independent=False)
    world = _world(event)
    row = _row(event=event, world=world)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("CALLER_INDEPENDENCE_FLAG_MISMATCH_DERIVED_VALUE" in x for x in result["failures"])
