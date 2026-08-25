from __future__ import annotations

from copy import deepcopy

from tools import trigger2_generation_provenance_gate_v1 as gp
from tools import trigger2_hyperposition_state_history_generation_bound_gate_v2 as gate
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator

proof = gate.history


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


def _row(prompt="A provenance-bound DB probe returns MATCH. Update the task-local Hyperposition state."):
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
        "prompt": prompt,
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
        "discriminator_execution_receipts_evaluator_only": [_disc_receipt(world, before, event)],
        "typed_observation_evidence_receipts_evaluator_only": [],
        "state_history_reference_target_evaluator_only": _history_target(world, before, event),
    }
    pre = gp.adjudicate(row)
    assert pre.get("expected_generation_receipt") is not None
    row["generation_receipt_evaluator_only"] = deepcopy(pre["expected_generation_receipt"])
    return row


def test_generation_bound_happy_path_is_candidate_only():
    result = gate.adjudicate(_row())
    assert result["pass"], result
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["second_semantic_authority_created"] is False


def test_T2_GP_01_any_repo_file_path_swap_rejected():
    row = _row()
    bad = proof.base.current_source_binding("tools/trigger2_hyperposition_reference_labelers_v3.py")
    assert bad["pass"]
    row["source_binding"] = {k: v for k, v in bad.items() if k != "pass"}
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("ROW_GENERATOR_PATH_NOT_CURRENT_AUTHORITY" in x for x in result["failures"])


def test_T2_GP_02_legitimate_generator_world_swap_rejected():
    row = _row()
    row["formal_task_world_evaluator_only"]["context"]["scope"] = "swapped-but-internally-valid"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("SUPPLIED_SUBJECT_DIGEST_OR_RECONSTRUCTION_MISMATCH" in x for x in result["failures"])


def test_T2_GP_03_registry_dependence_rewrite_rejected():
    row = _row()
    event_id = row["synthetic_test_event_evaluator_only"]["event_id"]
    row["formal_task_world_evaluator_only"]["event_dependence_registry"]["events"][event_id]["depends_on_event_ids"] = ["forged:prior"]
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("SUPPLIED_SUBJECT_DIGEST_OR_RECONSTRUCTION_MISMATCH" in x for x in result["failures"])


def test_T2_GP_04_event_mutation_same_id_rejected():
    row = _row()
    row["synthetic_test_event_evaluator_only"]["payload_key"] = "same-id-mutated-payload"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("SUPPLIED_SUBJECT_DIGEST_OR_RECONSTRUCTION_MISMATCH" in x for x in result["failures"])


def _reverse_dicts(value):
    if isinstance(value, dict):
        return {k: _reverse_dicts(value[k]) for k in reversed(list(value))}
    if isinstance(value, list):
        return [_reverse_dicts(x) for x in value]
    return value


def test_T2_GP_05_jcs_key_order_invariance():
    row = _row()
    row["formal_task_world_evaluator_only"] = _reverse_dicts(row["formal_task_world_evaluator_only"])
    row["synthetic_test_event_evaluator_only"] = _reverse_dicts(row["synthetic_test_event_evaluator_only"])
    row["hyperposition_state_before_evaluator_only"] = _reverse_dicts(row["hyperposition_state_before_evaluator_only"])
    pre = gp.adjudicate(row)
    assert pre["pass"], pre


def test_T2_GP_06_invocation_parameter_mutation_rejected():
    row = _row()
    row["generation_parameters_evaluator_only"]["case_variant"] = "MUTATED"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("GENERATION_PARAMETERS_NOT_AUTHORIZED" in x for x in result["failures"])


def test_T2_GP_07_material_manifest_mutation_rejected(monkeypatch):
    row = _row()
    original = gp._authority

    def mutated_authority():
        auth = deepcopy(original())
        auth["allowed_cases"][generator.CASE_ID]["materials_manifest"]["materials"] = ["forged-material"]
        return auth

    monkeypatch.setattr(gp, "_authority", mutated_authority)
    result = gp.adjudicate(row)
    assert not result["pass"]
    assert "MATERIALS_MANIFEST_DIGEST_MISMATCH" in result["failures"]


def test_T2_GP_08_prompt_paraphrase_semantic_invariance():
    row = _row("Paraphrased model-visible wording only; evaluator subjects are unchanged.")
    result = gate.adjudicate(row)
    assert result["pass"], result
    assert result["generation_provenance"]["reconstructed_subject_hashes"] == result["generation_provenance"]["supplied_subject_hashes"]


def test_state_before_preseeded_falsification_still_rejected_after_generation_layer():
    row = _row()
    row["hyperposition_state_before_evaluator_only"]["branches"][1]["sigma"] = "FALSIFIED"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("SUPPLIED_SUBJECT_DIGEST_OR_RECONSTRUCTION_MISMATCH" in x for x in result["failures"])


def test_unexecuted_discriminator_still_rejected_after_generation_layer():
    row = _row()
    row["discriminator_execution_receipts_evaluator_only"][0]["executed"] = False
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("DISCRIMINATOR_NOT_EXECUTED" in x for x in result["failures"])
