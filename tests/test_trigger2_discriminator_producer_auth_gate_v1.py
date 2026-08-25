from __future__ import annotations

from copy import deepcopy

from tools import trigger2_discriminator_producer_auth_gate_v1 as a02
from tools import trigger2_generation_provenance_gate_v1 as gp
from tools import trigger2_hyperposition_state_history_generation_bound_gate_v2 as old_gate
from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as gate
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator

proof = old_gate.history

PRODUCER_PATH = "tools/trigger2_trusted_synthetic_discriminator_producer_v1.py"
PRODUCER_SHA256 = "9a591298912c0d0d57a26c3424a32d963e1726583a1495dcd0809118f403f87d"
PRODUCER_SCHEMA = "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_PRODUCER/v1"
PRODUCER_SOURCE_COMMIT = "ec1ee0ac2175342205e1e27ef1f169642ffcd846"
POLICY_ID = "T2_SYNTHETIC_COMPLETE_COMPETITOR_DISCRIMINATOR/v1"
POLICY_SHA256 = "c153daf077b173537492f9df66d5d4f326f29c616d5b488d2dc20ae9b2e1d6aa"


def _legacy_row_carried_receipt(world, state, event):
    digest = proof.event_semantic_sha256(event)
    ordering = proof.lab.u_test_order(world, state, [event["test_id"]])["ordering"][0]
    return {
        "schema": proof.DISCRIMINATOR_RECEIPT_SCHEMA,
        "execution_receipt_id": "caller-self-asserted:" + event["event_id"],
        "event_id": event["event_id"],
        "test_id": event["test_id"],
        "observed_outcome": event["observed_outcome"],
        "event_semantic_sha256": digest,
        "world_sha256": proof._world_sha256(world),
        "admissible": True,
        "executed": True,
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
                elimination[branch["branch_id"]] = sorted(
                    {rec["event_id"] for rec in branch["F"]}
                )
    return {
        "state_after": state_after,
        "task_resolution": resolution,
        "event_sha256": digest,
        "eliminated_competitor_event_ids": elimination,
    }


def _row(*, producer_bound: bool):
    params = generator.default_parameters()
    bundle = generator.build_subjects(generator.CASE_ID, params)
    world = deepcopy(bundle["formal_world"])
    before = deepcopy(bundle["state_before"])
    event = deepcopy(bundle["event"])
    generator_path = "tools/trigger2_trusted_hyperposition_pilot_generator_v1.py"
    source_binding = proof.base.current_source_binding(generator_path)
    assert source_binding["pass"]
    row = {
        "schema": proof.base.ROW_SCHEMA,
        "evidence_class": "SYNTHETIC_DETERMINISTIC_LABEL",
        "reality_level": "R2",
        "fact_status": "NOT_APPLICABLE",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "model_visible_fields": ["prompt"],
        "prompt": "A provenance-bound DB probe returns MATCH. Update the task-local Hyperposition state.",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "source_binding": {k: v for k, v in source_binding.items() if k != "pass"},
        "generation_case_id_evaluator_only": generator.CASE_ID,
        "generation_parameters_evaluator_only": deepcopy(params),
        "formal_task_world_evaluator_only": world,
        "synthetic_test_event_evaluator_only": event,
        "hyperposition_state_before_evaluator_only": deepcopy(before),
        "v3_reference_target_evaluator_only": _base_target(world, before, event),
        "hyperposition_genesis_state_evaluator_only": deepcopy(before),
        "synthetic_event_history_evaluator_only": [],
        "event_digest_registry_evaluator_only": {
            "schema": proof.DIGEST_REGISTRY_SCHEMA,
            "events": {event["event_id"]: proof.event_semantic_sha256(event)},
        },
        "discriminator_producer_binding_evaluator_only": {
            "repo_path": PRODUCER_PATH,
            "source_sha256": PRODUCER_SHA256,
            "producer_schema_or_version": PRODUCER_SCHEMA,
            "source_commit_sha": PRODUCER_SOURCE_COMMIT,
        },
        "discriminator_policy_binding_evaluator_only": {
            "policy_id": POLICY_ID,
            "policy_sha256": POLICY_SHA256,
        },
        "discriminator_execution_receipts_evaluator_only": [
            _legacy_row_carried_receipt(world, before, event)
        ],
        "typed_observation_evidence_receipts_evaluator_only": [],
        "state_history_reference_target_evaluator_only": _history_target(
            world, before, event
        ),
    }
    generation_pre = gp.adjudicate(row)
    assert generation_pre["pass"], generation_pre
    row["generation_receipt_evaluator_only"] = deepcopy(
        generation_pre["expected_generation_receipt"]
    )
    if producer_bound:
        producer_pre = a02.adjudicate(row)
        assert not producer_pre["pass"]
        assert producer_pre["failures"] == [
            "TRANSPORTED_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_RESULT"
        ]
        expected = producer_pre["expected_discriminator_receipt"]
        assert isinstance(expected, dict)
        row["discriminator_execution_receipts_evaluator_only"] = [deepcopy(expected)]
        assert a02.adjudicate(row)["pass"]
    return row


def test_T2_SHPG_A02_legacy_true_true_arbitrary_receipt_id_is_rejected():
    row = _row(producer_bound=False)
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "TRANSPORTED_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_RESULT" in result["failures"]
    assert result["row_carried_producer_binding_is_authority"] is False
    assert result["row_carried_policy_binding_is_authority"] is False
    assert result["row_carried_admissible_is_authority"] is False
    assert result["row_carried_executed_is_authority"] is False
    assert result["row_carried_execution_receipt_id_is_authority"] is False


def test_T2_SHPG_A02_FAKE_EXECUTED_is_rejected():
    row = _row(producer_bound=True)
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["executed"] = False
    receipt["execution_receipt_id"] = "coherent-looking-fake-executed"
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "TRANSPORTED_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_RESULT" in result["failures"]


def test_T2_SHPG_A02_COHERENT_RECEIPT_REWRITE_is_rejected():
    row = _row(producer_bound=True)
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["execution_receipt_id"] = "t2dp:" + "0" * 64
    receipt["producer_result_sha256"] = "1" * 64
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "TRANSPORTED_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_RESULT" in result["failures"]


def test_T2_SHPG_A02_PRODUCER_PATH_SWAP_is_rejected():
    row = _row(producer_bound=True)
    row["discriminator_producer_binding_evaluator_only"]["repo_path"] = (
        "tools/trigger2_hyperposition_reference_labelers_v3.py"
    )
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "ROW_PRODUCER_BINDING_NOT_EXACT_CURRENT_AUTHORITY" in result["failures"]


def test_T2_SHPG_A02_PRODUCER_SHA_SWAP_is_rejected():
    row = _row(producer_bound=True)
    row["discriminator_producer_binding_evaluator_only"]["source_sha256"] = "0" * 64
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "ROW_PRODUCER_BINDING_NOT_EXACT_CURRENT_AUTHORITY" in result["failures"]


def test_T2_SHPG_A02_POLICY_SWAP_is_rejected():
    row = _row(producer_bound=True)
    row["discriminator_policy_binding_evaluator_only"] = {
        "policy_id": "T2_FORGED_POLICY/v1",
        "policy_sha256": "0" * 64,
    }
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "ROW_POLICY_BINDING_NOT_EXACT_CURRENT_AUTHORITY" in result["failures"]


def test_T2_SHPG_A02_PRESTATE_REWRITE_same_coverage_is_rejected():
    row = _row(producer_bound=True)
    row["hyperposition_state_before_evaluator_only"]["branches"][0]["A"]["tamper"] = (
        "same-prediction-and-coverage-different-prestate"
    )
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "STATE_BEFORE_SHA256_NOT_AUTHORIZED" in result["failures"]


def test_T2_SHPG_A02_WORLD_SCOPED_EVENT_REWRITE_is_rejected():
    row = _row(producer_bound=True)
    row["formal_task_world_evaluator_only"]["world_id"] = "t2gp:world:other:v1"
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "WORLD_ID_NOT_AUTHORIZED" in result["failures"]
    assert "WORLD_SCOPED_EVENT_SHA256_NOT_AUTHORIZED" in result["failures"]


def test_T2_SHPG_A02_COVERAGE_REWRITE_is_rejected():
    row = _row(producer_bound=True)
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["separated_live_pairs"] += 1
    receipt["separates_all_live_pairs"] = False
    result = a02.adjudicate(row)
    assert not result["pass"]
    assert "TRANSPORTED_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_RESULT" in result["failures"]


def test_v4_happy_path_is_source_closure_only_and_zero_credit():
    row = _row(producer_bound=True)
    result = gate.adjudicate(row)
    assert result["pass"], result
    assert result["a02_bounded_pilot_source_closure"] is True
    assert result["positive_D_E_promotion_ready"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0
    assert result["jspace_runtime_credit_minted"] == 0
    assert result["hcu_runtime_credit_minted"] == 0
    assert result["entityos_runtime_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_v4_discriminator_auth_failure_short_circuits_epistemic(monkeypatch):
    calls = []
    monkeypatch.setattr(
        gate.generation, "adjudicate", lambda row: {"pass": True, "failures": []}
    )

    def auth_fail(row):
        calls.append("auth")
        return {"pass": False, "failures": ["FORGED_RECEIPT"]}

    def epistemic_must_not_run(row):
        calls.append("epistemic")
        raise AssertionError(
            "epistemic/state-history path must not run after A02 failure"
        )

    monkeypatch.setattr(gate.discriminator_auth, "adjudicate", auth_fail)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_must_not_run)
    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["auth"]
    assert "DISCRIMINATOR_AUTH:FORGED_RECEIPT" in result["failures"]
