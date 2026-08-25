from __future__ import annotations

from copy import deepcopy

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as gate
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator

proof = gate.epistemic.base


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


def _row():
    params = generator.default_parameters()
    bundle = generator.build_subjects(generator.CASE_ID, params)
    world = deepcopy(bundle["formal_world"])
    before = deepcopy(bundle["state_before"])
    event = deepcopy(bundle["event"])

    generator_path = "tools/trigger2_trusted_hyperposition_pilot_generator_v1.py"
    binding = proof.base.current_source_binding(generator_path)
    assert binding["pass"]

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
        "source_binding": {k: v for k, v in binding.items() if k != "pass"},
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
        "discriminator_execution_receipts_evaluator_only": [],
        "typed_observation_evidence_receipts_evaluator_only": [],
        "state_history_reference_target_evaluator_only": _history_target(world, before, event),
    }

    gp = gate.generation.adjudicate(row)
    assert gp["pass"] is False  # generation receipt is intentionally absent on first pass
    assert gp.get("expected_generation_receipt") is not None
    row["generation_receipt_evaluator_only"] = deepcopy(gp["expected_generation_receipt"])

    gp = gate.generation.adjudicate(row)
    assert gp["pass"], gp
    authority = gate._authority()
    producer, binding, failures = gate._load_bound_producer(authority)
    assert not failures, failures
    receipt = producer.produce(
        case_id=generator.CASE_ID,
        world=world,
        state_before=before,
        event=event,
        producer_binding=binding,
        policy=authority["policy"],
    )
    row["discriminator_execution_receipts_evaluator_only"] = [receipt]
    return row


def _assert_exact_receipt_reject(row):
    result = gate.adjudicate(row)
    assert not result["pass"], result
    assert "ROW_DISCRIMINATOR_RECEIPT_NOT_EXACT_AUTHORITY_DERIVATION" in result["failures"]


def test_a02_happy_path_is_candidate_only_and_zero_credit():
    result = gate.adjudicate(_row())
    assert result["pass"], result
    assert result["candidate_pre_admission_pass"]
    assert result["a02_contract_status"] == "SOURCE_IMPLEMENTED_EXECUTION_UNOBSERVED"
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0
    assert result["jspace_runtime_credit_minted"] == 0
    assert result["hcu_runtime_credit_minted"] == 0
    assert result["entityos_runtime_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_T2_SHPG_A02_FAKE_EXECUTED_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["executed"] = True
    receipt["admissible"] = True
    receipt["execution_receipt_id"] = "invented:row-carried-proof"
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_COHERENT_RECEIPT_REWRITE_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["execution_receipt_id"] = "t2disc:" + ("0" * 64)
    receipt["producer_result_jcs_sha256"] = "1" * 64
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_PRODUCER_PATH_OR_SHA_SWAP_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["producer"]["repo_path"] = "tools/trigger2_hyperposition_reference_labelers_v3.py"
    receipt["producer"]["source_sha256"] = "0" * 64
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_POLICY_SWAP_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["policy"]["policy_id"] = "forged-policy/v999"
    receipt["policy"]["policy_version"] = "999"
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_PRESTATE_REWRITE_rejected_even_if_pair_count_can_remain_one():
    row = _row()
    row["hyperposition_state_before_evaluator_only"]["query_id"] = "rewritten:same-pair-count"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any(
        "SUPPLIED_SUBJECT_DIGEST_OR_RECONSTRUCTION_MISMATCH" in failure
        or "A02_V1_EMPTY_HISTORY_GENESIS_MUST_EQUAL_STATE_BEFORE" in failure
        for failure in result["failures"]
    )


def test_T2_SHPG_A02_WORLD_SCOPED_EVENT_REWRITE_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["world_scoped_event_jcs_sha256"] = "f" * 64
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_COVERAGE_REWRITE_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["separated_live_pairs"] = 999
    receipt["separates_all_live_pairs"] = True
    _assert_exact_receipt_reject(row)


def test_authority_source_sha_swap_fails_before_producer_invocation(monkeypatch):
    row = _row()
    original = gate._authority

    def tampered_authority():
        authority = deepcopy(original())
        authority["producer"]["source_sha256"] = "0" * 64
        return authority

    monkeypatch.setattr(gate, "_authority", tampered_authority)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_PRODUCER_SOURCE_SHA256_MISMATCH" in result["failures"]


def test_authority_policy_formal_spec_swap_fails_closed(monkeypatch):
    row = _row()
    original = gate._authority

    def tampered_authority():
        authority = deepcopy(original())
        authority["policy"]["formal_spec"]["risk_rank"] = 999
        return authority

    monkeypatch.setattr(gate, "_authority", tampered_authority)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("POLICY_REJECTED" in failure for failure in result["failures"])
