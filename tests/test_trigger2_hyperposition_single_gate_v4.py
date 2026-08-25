import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_hyperposition_single_gate_v4.py"
spec = importlib.util.spec_from_file_location("gate4", P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
base = gate.base
lab = gate.lab


def test_spec(outcomes, mismatch="FALSIFIES"):
    return {
        "allowed_outcomes": list(outcomes),
        "mismatch_effect": mismatch,
        "risk_rank": 0,
        "cost_rank": 0,
        "coordination_rank": 0,
    }


def branch(bid, value, predictions):
    return {
        "branch_id": bid,
        "v": value,
        "K": "ALWAYS",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": {"scope": "synthetic:test"},
        "A": {"origin": "test:single-gate-v4"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": copy.deepcopy(predictions),
    }


def state():
    return {
        "schema": lab.STATE_SCHEMA,
        "query_id": "q-v4",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [
            branch("A", "SURVIVING_HYPOTHESIS", {"split": "A", "confirm_a": "YES"}),
            branch("B", "ELIMINATED_HYPOTHESIS", {"split": "B"}),
        ],
    }


def event(eid, test_id, outcome, *, provenance=None, payload=None, group=None, ancestry=None, epistemic="SYNTHETIC_PROOF"):
    return {
        "schema": lab.EVENT_SCHEMA,
        "event_id": eid,
        "correlation_ancestry_id": ancestry or f"anc:{eid}",
        "independence_group": group or f"grp:{eid}",
        "payload_key": payload or f"payload:{eid}",
        "provenance": provenance or "synthetic:test-v4",
        "epistemic_type": epistemic,
        "test_id": test_id,
        "observed_outcome": outcome,
        "independence_qualified": True,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def dependence_entry(ev):
    return {
        "correlation_ancestry_id": ev["correlation_ancestry_id"],
        "independence_group": ev["independence_group"],
        "payload_key": ev["payload_key"],
        "provenance": ev["provenance"],
        "test_id": ev["test_id"],
        "observed_outcome": copy.deepcopy(ev["observed_outcome"]),
        "depends_on_event_ids": [],
    }


def claimed_target(world, before, ev):
    ind = base.derive_independence(world, before, ev)
    assert ind["pass"], ind
    ev2 = copy.deepcopy(ev)
    ev2["independence_qualified"] = bool(ind["derived_independence_qualified"])
    update = lab.u_state(world, before, ev2)
    assert update["pass"], update
    resolution = lab.d_resolve(world, update["state_after"])
    assert resolution["pass"], resolution
    return {
        "state_after": update.get("state_after"),
        "updates": update.get("updates"),
        "derivation_receipt": update.get("derivation_receipt"),
        "independent_evidence_credit": update.get("independent_evidence_credit"),
        "nonindependence_reasons": update.get("nonindependence_reasons"),
        "task_resolution": resolution.get("resolution"),
    }


def base_row(world, before, current, history):
    binding = base.current_source_binding("tools/trigger2_semantic_hyperposition_native_seed_generator_v2.py")
    assert binding["pass"], binding
    return {
        "schema": base.ROW_SCHEMA,
        "evidence_class": "SYNTHETIC_DETERMINISTIC_LABEL",
        "reality_level": "R2",
        "fact_status": "NOT_APPLICABLE",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "model_visible_fields": ["prompt"],
        "prompt": "Choose the branch justified by the formal synthetic evidence chain.",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "source_binding": {k: v for k, v in binding.items() if k != "pass"},
        "formal_task_world_evaluator_only": world,
        "hyperposition_state_before_evaluator_only": before,
        "synthetic_test_event_evaluator_only": current,
        "v3_reference_target_evaluator_only": claimed_target(world, before, current),
        "history_proof_evaluator_only": history,
    }


def fixture():
    genesis = state()
    h1 = event("e-history-1", "split", "A")
    cur = event("e-current-1", "confirm_a", "YES", epistemic="OBSERVED")
    world = {
        "schema": lab.WORLD_SCHEMA,
        "world_id": "w-single-gate-v4",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"scope": "synthetic:test"},
        "tests": {
            "split": test_spec(["A", "B"]),
            "confirm_a": test_spec(["YES", "NO"], mismatch="COUNTERS"),
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
        "event_dependence_registry": {
            "schema": base.DEPENDENCE_SCHEMA,
            "events": {
                h1["event_id"]: dependence_entry(h1),
                cur["event_id"]: dependence_entry(cur),
            },
        },
        "event_integrity_registry": {
            "schema": gate.EVENT_INTEGRITY_SCHEMA,
            "events": {
                h1["event_id"]: {"event_id": h1["event_id"], "event_sha256": gate.immutable_event_sha256(h1)},
                cur["event_id"]: {"event_id": cur["event_id"], "event_sha256": gate.immutable_event_sha256(cur)},
            },
        },
        "discriminator_proof_registry": {
            "schema": gate.DISCRIMINATOR_REGISTRY_SCHEMA,
            "events": {},
        },
    }
    h1_receipt = gate.make_discriminator_receipt(
        world, genesis, h1, execution_id="exec:h1", provenance="synthetic:test-v4:h1"
    )
    world["discriminator_proof_registry"]["events"][h1["event_id"]] = h1_receipt
    ind = base.derive_independence(world, genesis, h1)
    assert ind["pass"], ind
    h1_for_lab = copy.deepcopy(h1)
    h1_for_lab["independence_qualified"] = bool(ind["derived_independence_qualified"])
    first = lab.u_state(world, genesis, h1_for_lab)
    assert first["pass"], first
    before = first["state_after"]
    cur_receipt = gate.make_discriminator_receipt(
        world, before, cur, execution_id="exec:cur", provenance="synthetic:test-v4:cur"
    )
    world["discriminator_proof_registry"]["events"][cur["event_id"]] = cur_receipt
    history = gate.make_history_proof(genesis, [h1])
    return world, genesis, h1, before, cur, history


def test_positive_single_gate_replays_history_and_mints_zero_credit():
    world, _genesis, _h1, before, cur, history = fixture()
    row = base_row(world, before, cur, history)
    result = gate.adjudicate(row)
    assert result["pass"], result
    assert result["history_replay"]["state_before_reconstructed_from_genesis"] is True
    assert result["current_discriminator_proof"]["execution_required"] is True
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_preseeded_falsification_predecessor_passes_but_v4_rejects_history_forgery():
    world, genesis, _h1, _before, cur, _history = fixture()
    forged = copy.deepcopy(genesis)
    forged["branches"][1]["sigma"] = "FALSIFIED"
    world = copy.deepcopy(world)
    world["discriminator_proof_registry"]["events"][cur["event_id"]] = gate.make_discriminator_receipt(
        world, forged, cur, execution_id="exec:forged-current", provenance="synthetic:test-v4:forged"
    )
    empty_history = gate.make_history_proof(genesis, [])
    row = base_row(world, forged, cur, empty_history)
    predecessor = base.adjudicate(row)
    assert predecessor["pass"], predecessor
    current = gate.adjudicate(row)
    assert not current["pass"]
    assert "HISTORY:STATE_BEFORE_NOT_REPLAY_PROVEN" in current["failures"]


def test_same_event_id_changed_content_fails_closed_on_digest_identity():
    world, _genesis, h1, before, _cur, history = fixture()
    mutated = copy.deepcopy(h1)
    mutated["observed_outcome"] = "B"
    integrity = gate.validate_event_integrity(world, before, mutated)
    assert not integrity["pass"]
    assert "EVENT_INTEGRITY_DIGEST_MISMATCH" in integrity["failures"]
    assert "EVENT_ID_DIGEST_CONFLICT" in integrity["failures"]
    assert history["schema"] == gate.HISTORY_SCHEMA


def test_discriminator_receipt_must_be_admitted_executed_and_cover_all_live_alternatives():
    world, genesis, h1, _before, _cur, _history = fixture()
    bad = copy.deepcopy(world)
    receipt = gate.make_discriminator_receipt(
        bad, genesis, h1, execution_id="exec:bad", provenance="synthetic:test-v4:bad",
        execution_status="NOT_EXECUTED",
    )
    bad["discriminator_proof_registry"]["events"][h1["event_id"]] = receipt
    result = gate.validate_discriminator_proof(bad, genesis, h1)
    assert not result["pass"]
    assert "DISCRIMINATOR_NOT_EXECUTED" in result["failures"]

    bad2 = copy.deepcopy(world)
    receipt2 = gate.make_discriminator_receipt(
        bad2, genesis, h1, execution_id="exec:partial", provenance="synthetic:test-v4:partial",
        covered_branch_ids=["A"],
    )
    bad2["discriminator_proof_registry"]["events"][h1["event_id"]] = receipt2
    result2 = gate.validate_discriminator_proof(bad2, genesis, h1)
    assert not result2["pass"]
    assert "DISCRIMINATOR_COVERAGE_INCOMPLETE_OR_MISMATCHED" in result2["failures"]

    bad3 = copy.deepcopy(world)
    receipt3 = gate.make_discriminator_receipt(
        bad3, genesis, h1, execution_id="exec:not-admitted", provenance="synthetic:test-v4:not-admitted",
        admission_status="REJECTED",
    )
    bad3["discriminator_proof_registry"]["events"][h1["event_id"]] = receipt3
    result3 = gate.validate_discriminator_proof(bad3, genesis, h1)
    assert not result3["pass"]
    assert "DISCRIMINATOR_NOT_ADMITTED" in result3["failures"]


def test_grf_observed_promotion_rejects_naked_boolean_and_requires_typed_receipt():
    no_receipt = gate.adjudicate_epistemic_transition("UNKNOWN", "OBSERVED")
    assert not no_receipt["pass"]
    assert "TYPED_OBSERVATION_RECEIPT_REQUIRED" in no_receipt["failures"]
    assert no_receipt["naked_evidence_qualified_boolean_accepted"] is False

    receipt = {
        "schema": gate.OBSERVATION_RECEIPT_SCHEMA,
        "status": "VERIFIED_OBSERVATION",
        "source_type": "UNKNOWN",
        "target_type": "OBSERVED",
        "event_id": "obs-1",
        "event_sha256": "a" * 64,
        "provenance": "synthetic:test-v4:observation",
    }
    receipt["receipt_sha256"] = gate.observation_receipt_sha256(receipt)
    yes = gate.adjudicate_epistemic_transition("UNKNOWN", "OBSERVED", observation_receipt=receipt)
    assert yes["pass"], yes
    assert yes["transition_allowed"] is True


def test_exact_single_gate_identity_is_exposed_for_future_seed_rebinding():
    assert gate.SCHEMA == "CLAY_TRIGGER2_HYPERPOSITION_SINGLE_GATE/v4"
    assert gate.BASE_REPO_PATH == "tools/trigger2_hyperposition_derivation_bound_gate_v2.py"
    assert gate.base.SCHEMA == "CLAY_TRIGGER2_HYPERPOSITION_DERIVATION_BOUND_GATE/v2"
    assert gate.lab.SCHEMA == "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v3"
