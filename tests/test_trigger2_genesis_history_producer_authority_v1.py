"""Phase 3 closure tests: immutable genesis/ordered-history producer authority.

Proves the previously open remaining_p0 gap ("immutable genesis/ordered-history producer
authority is required before nonempty-history positives") is now closed: a nonempty history
that was not produced by the authorized trusted generator/case fails generation provenance
closed, and a correctly authorized nonempty history passes end-to-end through the same
replay-bound state-history proof gate every other Trigger-2 row uses. No second semantic
authority is introduced -- this reuses trigger2_generation_provenance_gate_v1 and the single
TRIGGER2_TRUSTED_SYNTHETIC_GENERATOR_AUTHORITY_V1.json authority file.
"""
from __future__ import annotations

from copy import deepcopy

from tools import trigger2_generation_provenance_gate_v1 as gp
from tools import trigger2_hyperposition_state_history_proof_gate_v1 as proof
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator


def _disc_receipt(world, state, event):
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
        "executed": True,
        "separated_live_pairs": ordering["separated_live_pairs"],
        "separates_all_live_pairs": ordering["separates_all_live_pairs"],
    }


def _hist_chain_bundle():
    return generator.build_subjects(generator.HIST_CHAIN_CASE_ID, generator.hist_chain_parameters())


def _authorized_generation_fields(bundle, *, case_id, parameters):
    """Build the exact source_binding + generation_receipt a caller needs so that
    trigger2_generation_provenance_gate_v1.adjudicate(row) passes for this bundle."""
    probe = gp.adjudicate({
        "source_binding": {"generator_path": "tools/trigger2_trusted_hyperposition_pilot_generator_v1.py"},
        "generation_case_id_evaluator_only": case_id,
        "generation_parameters_evaluator_only": parameters,
        "formal_task_world_evaluator_only": bundle["formal_world"],
        "synthetic_test_event_evaluator_only": bundle["event"],
        "hyperposition_state_before_evaluator_only": bundle["state_before"],
        "hyperposition_genesis_state_evaluator_only": bundle["genesis_state"],
        "synthetic_event_history_evaluator_only": bundle["event_history"],
    })
    # trigger2_hyperposition_derivation_bound_gate_v2.current_source_binding() binds BOTH the
    # named generator path and the fixed v3 labeler in one dict; trigger2_generation_provenance
    # only reads the generator_path/generator_sha256 keys out of it, so this one binding value
    # satisfies both gates' source_binding checks on the same row -- no second field needed.
    full_binding = proof.base.current_source_binding(probe["expected_generator_path"])
    assert full_binding["pass"], full_binding
    assert full_binding["generator_sha256"] == probe["expected_generator_source_sha256"]
    return {
        "source_binding": {k: v for k, v in full_binding.items() if k != "pass"},
        "generation_receipt_evaluator_only": probe["expected_generation_receipt"],
    }


def _hist_chain_row():
    bundle = _hist_chain_bundle()
    world = bundle["formal_world"]
    genesis = bundle["genesis_state"]
    step1 = bundle["event_history"][0]
    step2 = bundle["event"]
    state_before = bundle["state_before"]

    r1 = _disc_receipt(world, genesis, step1)
    r2 = _disc_receipt(world, state_before, step2)

    indep2 = proof.base.derive_independence(world, state_before, step2)
    step2_for_lab = deepcopy(step2)
    step2_for_lab["independence_qualified"] = bool(indep2["derived_independence_qualified"])
    update2 = proof.lab.u_state(world, state_before, step2_for_lab)
    state_after2 = deepcopy(update2["state_after"])
    digest2 = proof.event_semantic_sha256(step2)
    proof._decorate_event_records(state_after2, step2["event_id"], digest2)
    resolution = proof.lab.d_resolve(world, state_after2)["resolution"]
    elimination = {}
    if resolution["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD":
        winner = resolution["resolved_branch"]
        for branch in state_after2["branches"]:
            if branch["branch_id"] != winner and branch["sigma"] == "FALSIFIED":
                elimination[branch["branch_id"]] = sorted({rec["event_id"] for rec in branch["F"]})

    v3_target = {
        "state_after": update2.get("state_after"),
        "updates": update2.get("updates"),
        "derivation_receipt": update2.get("derivation_receipt"),
        "independent_evidence_credit": update2.get("independent_evidence_credit"),
        "nonindependence_reasons": update2.get("nonindependence_reasons"),
        "task_resolution": proof.lab.d_resolve(world, update2["state_after"]).get("resolution"),
    }

    generation_fields = _authorized_generation_fields(
        bundle, case_id=generator.HIST_CHAIN_CASE_ID, parameters=generator.hist_chain_parameters(),
    )

    row = {
        "schema": proof.base.ROW_SCHEMA,
        "evidence_class": "SYNTHETIC_DETERMINISTIC_LABEL",
        "reality_level": "R2",
        "fact_status": "NOT_APPLICABLE",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "model_visible_fields": ["prompt"],
        "prompt": "Genesis/ordered-history producer authority closure test.",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "generation_case_id_evaluator_only": generator.HIST_CHAIN_CASE_ID,
        "generation_parameters_evaluator_only": generator.hist_chain_parameters(),
        "formal_task_world_evaluator_only": world,
        "synthetic_test_event_evaluator_only": step2,
        "hyperposition_state_before_evaluator_only": state_before,
        "v3_reference_target_evaluator_only": v3_target,
        "hyperposition_genesis_state_evaluator_only": genesis,
        "synthetic_event_history_evaluator_only": [step1],
        "event_digest_registry_evaluator_only": {
            "schema": proof.DIGEST_REGISTRY_SCHEMA,
            "events": {
                step1["event_id"]: proof.event_semantic_sha256(step1),
                step2["event_id"]: proof.event_semantic_sha256(step2),
            },
        },
        "discriminator_execution_receipts_evaluator_only": [r1, r2],
        "typed_observation_evidence_receipts_evaluator_only": [],
        "state_history_reference_target_evaluator_only": {
            "state_after": state_after2,
            "task_resolution": resolution,
            "event_sha256": digest2,
            "eliminated_competitor_event_ids": elimination,
        },
    }
    row.update(generation_fields)
    return row


def test_hist_chain_generation_provenance_passes_for_authorized_bundle():
    bundle = _hist_chain_bundle()
    fields = _authorized_generation_fields(
        bundle, case_id=generator.HIST_CHAIN_CASE_ID, parameters=generator.hist_chain_parameters(),
    )
    row = {
        "generation_case_id_evaluator_only": generator.HIST_CHAIN_CASE_ID,
        "generation_parameters_evaluator_only": generator.hist_chain_parameters(),
        "formal_task_world_evaluator_only": bundle["formal_world"],
        "synthetic_test_event_evaluator_only": bundle["event"],
        "hyperposition_state_before_evaluator_only": bundle["state_before"],
        "hyperposition_genesis_state_evaluator_only": bundle["genesis_state"],
        "synthetic_event_history_evaluator_only": bundle["event_history"],
        **fields,
    }
    result = gp.adjudicate(row)
    assert result["pass"], result


def test_nonempty_history_without_any_generation_authority_fails_closed():
    """A row that just supplies an arbitrary nonempty event_history/genesis with no
    generation_case_id at all must fail generation provenance -- this is the exact gap
    Track A confirmed open: previously nothing checked this at all."""
    bundle = _hist_chain_bundle()
    row = {
        "formal_task_world_evaluator_only": bundle["formal_world"],
        "synthetic_test_event_evaluator_only": bundle["event"],
        "hyperposition_state_before_evaluator_only": bundle["state_before"],
        "hyperposition_genesis_state_evaluator_only": bundle["genesis_state"],
        "synthetic_event_history_evaluator_only": bundle["event_history"],
    }
    result = gp.adjudicate(row)
    assert not result["pass"]
    assert "GENERATION_CASE_NOT_AUTHORIZED" in result["failures"]


def test_forged_history_event_content_fails_closed():
    """Same authorized case_id/receipt, but the caller mutates one field inside the
    history event after the fact -- must fail on byte/digest mismatch, not silently pass."""
    bundle = _hist_chain_bundle()
    fields = _authorized_generation_fields(
        bundle, case_id=generator.HIST_CHAIN_CASE_ID, parameters=generator.hist_chain_parameters(),
    )
    forged_history = deepcopy(bundle["event_history"])
    forged_history[0]["payload_key"] = "forged-payload"
    row = {
        "generation_case_id_evaluator_only": generator.HIST_CHAIN_CASE_ID,
        "generation_parameters_evaluator_only": generator.hist_chain_parameters(),
        "formal_task_world_evaluator_only": bundle["formal_world"],
        "synthetic_test_event_evaluator_only": bundle["event"],
        "hyperposition_state_before_evaluator_only": bundle["state_before"],
        "hyperposition_genesis_state_evaluator_only": bundle["genesis_state"],
        "synthetic_event_history_evaluator_only": forged_history,
        **fields,
    }
    result = gp.adjudicate(row)
    assert not result["pass"]
    assert any("event_history" in f or "SUBJECT_DIGEST" in f for f in result["failures"])


def test_empty_history_case_cannot_be_reused_to_smuggle_nonempty_history():
    """The DB_MATCH case (empty event_history) must not validate a row that claims a
    nonempty history while citing that case id."""
    bundle = generator.build_subjects(generator.CASE_ID, generator.default_parameters())
    fields = _authorized_generation_fields(bundle, case_id=generator.CASE_ID, parameters=generator.default_parameters())
    hist_bundle = _hist_chain_bundle()
    row = {
        "generation_case_id_evaluator_only": generator.CASE_ID,
        "generation_parameters_evaluator_only": generator.default_parameters(),
        "formal_task_world_evaluator_only": bundle["formal_world"],
        "synthetic_test_event_evaluator_only": bundle["event"],
        "hyperposition_state_before_evaluator_only": bundle["state_before"],
        "hyperposition_genesis_state_evaluator_only": bundle["genesis_state"],
        "synthetic_event_history_evaluator_only": [hist_bundle["event_history"][0]],
        **fields,
    }
    result = gp.adjudicate(row)
    assert not result["pass"]
    assert any("event_history" in f or "SUBJECT_DIGEST" in f or "RECEIPT_NOT_EXACTLY" in f for f in result["failures"])


def test_hist_chain_row_passes_full_replay_bound_state_history_proof_gate():
    """End-to-end positive control: an authorized nonempty-history row passes the same
    structural replay-integrity gate every Trigger-2 row is proven against, in addition to
    now passing generation provenance -- proving the two checks compose."""
    row = _hist_chain_row()
    gen_result = gp.adjudicate(row)
    assert gen_result["pass"], gen_result
    proof_result = proof.adjudicate(row)
    assert proof_result["pass"], proof_result
