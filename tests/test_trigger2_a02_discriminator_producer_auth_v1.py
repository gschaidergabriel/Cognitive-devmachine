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
                elimination[branch["branch_id"]] = sorted(
                    {r["event_id"] for r in branch["F"]}
                )
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

    binding = proof.base.current_source_binding(
        "tools/trigger2_trusted_hyperposition_pilot_generator_v1.py"
    )
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
    assert gp["pass"] is False
    row["generation_receipt_evaluator_only"] = deepcopy(
        gp["expected_generation_receipt"]
    )
    gp = gate.generation.adjudicate(row)
    assert gp["pass"], gp

    expected = gate.producer_auth.expected_receipt(row)
    row["discriminator_execution_receipts_evaluator_only"] = [
        deepcopy(expected["receipt"])
    ]
    return row


def _assert_exact_receipt_reject(row):
    result = gate.adjudicate(row)
    assert not result["pass"], result
    assert any(
        "DISCRIMINATOR_RECEIPT_NOT_EXACT_TRUSTED_PRODUCER_OUTPUT" in failure
        for failure in result["failures"]
    )


def test_a02_happy_path_is_candidate_only_and_zero_credit():
    result = gate.adjudicate(_row())
    assert result["pass"], result
    assert result["candidate_pre_admission_pass"]
    assert result["a02_contract_status"] == (
        "SOURCE_IMPLEMENTED_DEPENDENCY_BOUND_EXECUTION_UNOBSERVED"
    )
    for key in (
        "accepted_dataset_tokens_minted",
        "training_credit_minted",
        "runtime_credit_minted",
        "jspace_runtime_credit_minted",
        "hcu_runtime_credit_minted",
        "entityos_runtime_credit_minted",
    ):
        assert result[key] == 0
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
    receipt["producer"]["source_sha256"] = "0" * 64
    receipt["execution_receipt_id"] = "t2dp:" + ("1" * 64)
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_PRODUCER_PATH_OR_SHA_SWAP_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["producer"]["repo_path"] = "tools/trigger2_hyperposition_reference_labelers_v3.py"
    receipt["producer"]["source_sha256"] = "0" * 64
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_POLICY_SWAP_rejected():
    row = _row()
    row["discriminator_execution_receipts_evaluator_only"][0]["policy_sha256"] = "0" * 64
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_PRESTATE_REWRITE_rejected_even_if_pair_count_can_remain_one():
    row = _row()
    row["hyperposition_state_before_evaluator_only"]["query_id"] = "rewritten:same-pair-count"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any(
        "SUPPLIED_SUBJECT_DIGEST_OR_RECONSTRUCTION_MISMATCH" in failure
        or "ROW_STATE_BEFORE_NOT_TRUSTED_GENERATOR_OUTPUT" in failure
        for failure in result["failures"]
    )


def test_T2_SHPG_A02_WORLD_SCOPED_EVENT_REWRITE_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["world_scoped_event_sha256"] = "f" * 64
    _assert_exact_receipt_reject(row)


def test_T2_SHPG_A02_COVERAGE_REWRITE_rejected():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["separated_live_pairs"] = 999
    _assert_exact_receipt_reject(row)


def test_authority_source_sha_swap_fails_before_producer_invocation(monkeypatch):
    row = _row()
    original = gate.producer_auth._producer_authority

    def tampered():
        authority = deepcopy(original())
        authority["producer"]["source_sha256"] = "0" * 64
        return authority

    monkeypatch.setattr(gate.producer_auth, "_producer_authority", tampered)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("PRODUCER_SOURCE_SHA256_MISMATCH" in failure for failure in result["failures"])


def test_authority_policy_swap_fails_closed(monkeypatch):
    row = _row()
    original = gate.producer_auth._producer_authority

    def tampered():
        authority = deepcopy(original())
        authority["allowed_cases"][generator.CASE_ID]["policy"]["expected_test_id"] = "other"
        return authority

    monkeypatch.setattr(gate.producer_auth, "_producer_authority", tampered)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("DISCRIMINATOR_POLICY_DIGEST_MISMATCH" in failure for failure in result["failures"])


def test_ordering_semantics_blob_swap_fails_before_producer_invocation(monkeypatch):
    row = _row()
    original = gate.producer_auth._producer_authority

    def tampered():
        authority = deepcopy(original())
        authority["ordering_semantics"]["git_blob_sha1"] = "0" * 40
        return authority

    monkeypatch.setattr(gate.producer_auth, "_producer_authority", tampered)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any(
        "ORDERING_SEMANTICS_GIT_BLOB_MISMATCH" in failure
        for failure in result["failures"]
    )
