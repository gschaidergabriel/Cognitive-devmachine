#!/usr/bin/env python3
"""Production DB_MATCH gold-pilot row assembler.

Deterministically assembles exactly one T2_GP_PILOT_DB_MATCH_V1 (empty-history)
candidate row against the current trusted generator / A02 discriminator-producer
authority / tokenizer-ABI atoms index, binding every *_evaluator_only field so
the row can be run through
tools/trigger2_hyperposition_state_history_generation_bound_gate_v4.adjudicate().

This assembler produces a CANDIDATE row only. It does not write to any
canonical dataset, ledger, or ledger snapshot, and mints zero training/
runtime/dataset/canonical-truth/direct-effect credit -- same credit boundary
as the v4 composer it feeds. Promoting a row's candidate_pre_admission_pass
into canonical_dataset_admission is a separate, not-yet-built step.

Known-good deterministic row-wrapping logic promoted out of an ad hoc test
script (VPS worktree db_match_test2.py, pinned base 3fb6f96bf) per
supervisor 8.89 P0_PRODUCTION_ROW_ASSEMBLY.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools import trigger2_generation_provenance_gate_v1 as gp
from tools import trigger2_hyperposition_state_history_proof_gate_v1 as proof
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator
from tools import trigger2_a02_discriminator_producer_v1 as producer

REPO = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = (
    REPO
    / "research_entity/global/j-space/research/"
      "TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
)

# The DB_MATCH prompt only asserts a binary fact-wins-over-simulation claim.
DEFAULT_TOKENIZER_ATOMS = ["yes", "no"]

DEFAULT_PROMPT = (
    "DB_MATCH gold-pilot candidate: canonical database fact must win over a "
    "contradicting simulation."
)


def _load_authority() -> dict[str, Any]:
    return json.loads(AUTHORITY_PATH.read_text())


def _authorized_generation_fields(bundle: dict, case_id: str, parameters: dict) -> dict:
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
    full_binding = proof.base.current_source_binding(probe["expected_generator_path"])
    if not full_binding["pass"]:
        raise RuntimeError("source binding authority mismatch: " + json.dumps(full_binding, default=str))
    return {
        "source_binding": {k: v for k, v in full_binding.items() if k != "pass"},
        "generation_receipt_evaluator_only": probe["expected_generation_receipt"],
    }


def assemble_db_match_row(
    prompt_text: str | None = None,
    tokenizer_atoms_used: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble exactly one authorized, empty-history DB_MATCH candidate row.

    Uses generator.CASE_ID (T2_GP_PILOT_DB_MATCH_V1) with default_parameters(),
    the pinned A02 discriminator producer authority, and the measured
    tokenizer atoms index. Deterministic for fixed inputs: identical output on
    every call (no randomness, no mutating I/O -- only reads the pinned
    authority JSON file).
    """
    case_id = generator.CASE_ID
    parameters = generator.default_parameters()
    bundle = generator.build_subjects(case_id, parameters)
    world = bundle["formal_world"]
    genesis = bundle["genesis_state"]
    state_before = bundle["state_before"]
    event = bundle["event"]

    authority = _load_authority()
    policy = authority["policy"]
    p = authority["producer"]
    a02_receipt = producer.produce(
        world=world,
        pre_state=state_before,
        event=event,
        generation_case_id=case_id,
        policy=policy,
    )

    indep = proof.base.derive_independence(world, state_before, event)
    event_for_lab = deepcopy(event)
    event_for_lab["independence_qualified"] = bool(indep["derived_independence_qualified"])
    update = proof.lab.u_state(world, state_before, event_for_lab)
    state_after = deepcopy(update["state_after"])
    digest = proof.event_semantic_sha256(event)
    proof._decorate_event_records(state_after, event["event_id"], digest)
    resolution = proof.lab.d_resolve(world, state_after)["resolution"]
    elimination: dict[str, list[str]] = {}
    if resolution["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD":
        winner = resolution["resolved_branch"]
        for branch in state_after["branches"]:
            if branch["branch_id"] != winner and branch["sigma"] == "FALSIFIED":
                elimination[branch["branch_id"]] = sorted({rec["event_id"] for rec in branch["F"]})

    v3_target = {
        "state_after": update.get("state_after"),
        "updates": update.get("updates"),
        "derivation_receipt": update.get("derivation_receipt"),
        "independent_evidence_credit": update.get("independent_evidence_credit"),
        "nonindependence_reasons": update.get("nonindependence_reasons"),
        "task_resolution": proof.lab.d_resolve(world, update["state_after"]).get("resolution"),
    }

    fields = _authorized_generation_fields(bundle, case_id, parameters)

    row: dict[str, Any] = {
        "schema": proof.base.ROW_SCHEMA,
        "evidence_class": "SYNTHETIC_DETERMINISTIC_LABEL",
        "reality_level": "R2",
        "fact_status": "NOT_APPLICABLE",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "model_visible_fields": ["prompt"],
        "prompt": prompt_text or DEFAULT_PROMPT,
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "generation_case_id_evaluator_only": case_id,
        "generation_parameters_evaluator_only": parameters,
        "formal_task_world_evaluator_only": world,
        "synthetic_test_event_evaluator_only": event,
        "hyperposition_state_before_evaluator_only": state_before,
        "v3_reference_target_evaluator_only": v3_target,
        "hyperposition_genesis_state_evaluator_only": genesis,
        "synthetic_event_history_evaluator_only": [],
        "event_digest_registry_evaluator_only": {
            "schema": proof.DIGEST_REGISTRY_SCHEMA,
            "events": {event["event_id"]: digest},
        },
        "discriminator_execution_receipts_evaluator_only": [a02_receipt],
        "typed_observation_evidence_receipts_evaluator_only": [],
        "state_history_reference_target_evaluator_only": {
            "state_after": state_after,
            "task_resolution": resolution,
            "event_sha256": digest,
            "eliminated_competitor_event_ids": elimination,
        },
        "discriminator_producer_binding_evaluator_only": {
            "repo_path": p["repo_path"],
            "source_sha256": p["source_sha256"],
            "producer_schema_or_version": p["producer_schema_or_version"],
            "source_lineage": deepcopy(p["source_lineage"]),
            "policy_id": policy["policy_id"],
            "policy_version": policy["policy_version"],
            "policy_jcs_sha256": authority["policy_jcs_sha256"],
            "formal_discriminator_spec_jcs_sha256": policy["formal_discriminator_spec_jcs_sha256"],
        },
        "tokenizer_atoms_used": list(tokenizer_atoms_used or DEFAULT_TOKENIZER_ATOMS),
    }
    row.update(fields)
    return row


if __name__ == "__main__":
    from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as v4

    r = assemble_db_match_row()
    result = v4.adjudicate(r)
    print(json.dumps({"pass": result["pass"], "failures": result["failures"]}, indent=2))
