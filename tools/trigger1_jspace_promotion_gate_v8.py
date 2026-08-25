#!/usr/bin/env python3
"""Evidence-object-bound successor promotion gate for Trigger-1 J-Space claims.

v8 composes v7 and closes a narrower remaining self-attestation gap in the promotion-v6
second-order layer.  v6 requires several receipt SHA strings, but a syntactically valid
64-hex digest plus summary booleans is not itself a replayable evidence object.  v8 therefore
requires each v6 receipt used for promotion to be the deterministic digest of an embedded,
candidate-bound evidence packet containing nonempty observations and provenance.

This establishes internal object/digest/claim binding only.  It does not authenticate an
external runtime merely because a referenced artifact digest exists, does not run a model,
and cannot mint canonical semantics, J-Space model runtime, HCU, EntityOS, training, BASE,
or real-effect credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v7 as v7

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v8"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v8"
BINDING_SCHEMA = "CLAY_TRIGGER1_V6_SECOND_ORDER_EVIDENCE_BINDINGS/v1"
PACKET_SCHEMA = "CLAY_TRIGGER1_BOUND_EVIDENCE_PACKET/v1"
NATIVE_CVEC_CLASS = "LOCAL_LLAMA_CPP_CVEC_APPLIED"

# evidence_type -> (candidate summary object, receipt field)
REQUIRED_PACKET_SPECS = {
    "semantic_basis": ("semantic_basis_design", "blocked_basis_receipt_sha256"),
    "semantic_rank": ("semantic_simplex_rank", "analysis_receipt_sha256"),
    "downstream_transport": ("downstream_semantic_transport", "transport_receipt_sha256"),
    "tokenizer_boundary": ("context_valid_dual_readout", "tokenizer_boundary_receipt_sha256"),
    "likelihood_margin": ("context_valid_dual_readout", "likelihood_margin_receipt_sha256"),
    "emitted_decision": ("context_valid_dual_readout", "emitted_decision_receipt_sha256"),
    "causal_matrix": ("class_selective_causal_matrix", "matrix_receipt_sha256"),
}
NATIVE_PACKET_SPEC = {
    "native_carrier_geometry": ("native_carrier_geometry", "geometry_receipt_sha256")
}


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _candidate_core(candidate: dict[str, Any]) -> dict[str, Any]:
    intervention = candidate.get("intervention")
    derivation = candidate.get("vector_derivation")
    calibration = candidate.get("calibration")
    holdout = candidate.get("holdout")
    target = candidate.get("target")
    return {
        "runtime_intervention_class": candidate.get("runtime_intervention_class"),
        "source_identity": candidate.get("source_identity"),
        "intervention": {
            "runtime_intervention_receipt_sha256": intervention.get("runtime_intervention_receipt_sha256"),
            "activation_site": intervention.get("activation_site"),
            "layer_start": intervention.get("layer_start"),
            "layer_end": intervention.get("layer_end"),
            "gain": intervention.get("gain"),
            "residual_norm_ratio": intervention.get("residual_norm_ratio"),
            "token_scope": intervention.get("token_scope"),
        } if isinstance(intervention, dict) else None,
        "vector_derivation": {
            "derivation_family_id": derivation.get("derivation_family_id"),
            "derivation_receipt_sha256": derivation.get("derivation_receipt_sha256"),
        } if isinstance(derivation, dict) else None,
        "calibration_family_id": calibration.get("family_id") if isinstance(calibration, dict) else None,
        "holdout_family_id": holdout.get("family_id") if isinstance(holdout, dict) else None,
        "target": target if isinstance(target, dict) else None,
    }


def _source_identity_ok(candidate: dict[str, Any]) -> bool:
    identity = candidate.get("source_identity")
    if not isinstance(identity, dict):
        return False
    # Require at least the model/runtime identity hashes used throughout the current lane.
    return all(_sha256(identity.get(key)) for key in (
        "runtime_build_sha256",
        "checkpoint_sha256",
        "tokenizer_sha256",
    ))


def _summary_core(candidate: dict[str, Any], object_key: str) -> dict[str, Any] | None:
    value = candidate.get(object_key)
    if not isinstance(value, dict):
        return None
    # Receipt fields are excluded from the summary digest to avoid circularity because the
    # packet digest itself becomes the corresponding receipt value.
    return {k: v for k, v in value.items() if not str(k).endswith("receipt_sha256")}


def _validate_observations(value: Any, *, evidence_type: str) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not isinstance(value, list) or not value:
        return False, [f"BOUND_OBSERVATIONS_REQUIRED:{evidence_type}"]
    seen: set[str] = set()
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            failures.append(f"BOUND_OBSERVATION_OBJECT_REQUIRED:{evidence_type}:{index}")
            continue
        observation_id = row.get("observation_id")
        if not isinstance(observation_id, str) or not observation_id.strip():
            failures.append(f"BOUND_OBSERVATION_ID_REQUIRED:{evidence_type}:{index}")
            continue
        observation_id = observation_id.strip()
        if observation_id in seen:
            failures.append(f"BOUND_OBSERVATION_ID_DUPLICATE:{evidence_type}:{observation_id}")
        seen.add(observation_id)
        provenance = row.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            failures.append(f"BOUND_OBSERVATION_PROVENANCE_REQUIRED:{evidence_type}:{observation_id}")
        value_present = _finite(row.get("value"))
        artifact_present = _sha256(row.get("artifact_sha256"))
        if not value_present and not artifact_present:
            failures.append(f"BOUND_OBSERVATION_VALUE_OR_ARTIFACT_REQUIRED:{evidence_type}:{observation_id}")
    return not failures, failures


def _binding_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    binding = candidate.get("v6_second_order_evidence_bindings")
    if not isinstance(binding, dict) or binding.get("schema") != BINDING_SCHEMA:
        return False, ["V6_SECOND_ORDER_EVIDENCE_BINDINGS_REQUIRED"], {}

    if not _source_identity_ok(candidate):
        failures.append("BOUND_SOURCE_IDENTITY_REQUIRED")

    candidate_core = _candidate_core(candidate)
    candidate_core_sha = canonical_sha256(candidate_core)
    if binding.get("candidate_core_sha256") != candidate_core_sha:
        failures.append("V6_BINDING_CANDIDATE_CORE_DIGEST_MISMATCH")

    packets = binding.get("packets")
    if not isinstance(packets, dict):
        return False, sorted(set(failures + ["V6_BOUND_EVIDENCE_PACKET_MAP_REQUIRED"])), {
            "candidate_core_sha256": candidate_core_sha,
        }

    specs = dict(REQUIRED_PACKET_SPECS)
    if candidate.get("runtime_intervention_class") == NATIVE_CVEC_CLASS:
        specs.update(NATIVE_PACKET_SPEC)

    required_types = set(specs)
    packet_types = set(packets)
    for missing in sorted(required_types - packet_types):
        failures.append(f"BOUND_EVIDENCE_PACKET_REQUIRED:{missing}")
    for undeclared in sorted(packet_types - required_types):
        failures.append(f"BOUND_EVIDENCE_PACKET_UNDECLARED:{undeclared}")

    packet_receipts: dict[str, str] = {}
    for evidence_type, (object_key, receipt_field) in specs.items():
        packet = packets.get(evidence_type)
        if not isinstance(packet, dict):
            continue
        if packet.get("schema") != PACKET_SCHEMA:
            failures.append(f"BOUND_PACKET_SCHEMA_INVALID:{evidence_type}")
        if packet.get("evidence_type") != evidence_type:
            failures.append(f"BOUND_PACKET_TYPE_MISMATCH:{evidence_type}")
        if packet.get("candidate_core_sha256") != candidate_core_sha:
            failures.append(f"BOUND_PACKET_CANDIDATE_CORE_MISMATCH:{evidence_type}")

        summary_core = _summary_core(candidate, object_key)
        if summary_core is None:
            failures.append(f"BOUND_SUMMARY_OBJECT_REQUIRED:{evidence_type}:{object_key}")
            continue
        summary_sha = canonical_sha256(summary_core)
        if packet.get("summary_core_sha256") != summary_sha:
            failures.append(f"BOUND_PACKET_SUMMARY_DIGEST_MISMATCH:{evidence_type}")

        _, observation_failures = _validate_observations(packet.get("observations"), evidence_type=evidence_type)
        failures.extend(observation_failures)
        packet_provenance = packet.get("packet_provenance")
        if not isinstance(packet_provenance, dict) or not packet_provenance:
            failures.append(f"BOUND_PACKET_PROVENANCE_REQUIRED:{evidence_type}")

        receipt = packet.get("receipt_sha256")
        packet_core = {k: v for k, v in packet.items() if k != "receipt_sha256"}
        recomputed_receipt = canonical_sha256(packet_core)
        if receipt != recomputed_receipt:
            failures.append(f"BOUND_PACKET_RECEIPT_RECOMPUTE_MISMATCH:{evidence_type}")
        summary = candidate.get(object_key)
        summary_receipt = summary.get(receipt_field) if isinstance(summary, dict) else None
        if summary_receipt != recomputed_receipt:
            failures.append(f"BOUND_PACKET_SUMMARY_RECEIPT_MISMATCH:{evidence_type}")
        packet_receipts[evidence_type] = recomputed_receipt

    binding_contract = {
        "schema": BINDING_SCHEMA,
        "candidate_core_sha256": candidate_core_sha,
        "packet_receipts": {k: packet_receipts[k] for k in sorted(packet_receipts)},
    }
    expected_binding_sha = canonical_sha256(binding_contract)
    if binding.get("binding_receipt_sha256") != expected_binding_sha:
        failures.append("V6_SECOND_ORDER_BINDING_RECEIPT_MISMATCH")

    details = {
        "candidate_core_sha256": candidate_core_sha,
        "required_packet_types": sorted(required_types),
        "bound_packet_count": len(packet_receipts),
        "binding_receipt_sha256": expected_binding_sha,
        "external_runtime_receipt_authentication": "NOT_PERFORMED_INTERNAL_OBJECT_BINDING_ONLY",
    }
    return not failures, sorted(set(failures)), details


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v7.adjudicate(candidate)
    binding_ok, binding_failures, binding = _binding_evidence(candidate)

    upstream_scientific = base.get("scientifically_independent_vector_candidate") is True
    upstream_owner = base.get("owner_trigger1_goal_credit_candidate") is True
    upstream_modular = base.get("modular_hcu_jspace_control_candidate") is True
    upstream_full_native = base.get("full_native_jspace_vector_control_candidate") is True

    scientific = bool(upstream_scientific and binding_ok)
    owner = bool(upstream_owner and binding_ok)
    modular = bool(upstream_modular and binding_ok)
    full_native = bool(upstream_full_native and binding_ok)

    failures = sorted(set(list(base.get("v7_failures", [])) + binding_failures))
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v7_scientifically_independent_vector_candidate": upstream_scientific,
        "v7_owner_trigger1_goal_credit_candidate": upstream_owner,
        "v7_modular_hcu_jspace_control_candidate": upstream_modular,
        "v6_second_order_evidence_bound_candidate": bool(binding_ok),
        "v6_second_order_binding_failures": binding_failures,
        "v6_second_order_evidence_binding": binding,
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "full_native_jspace_vector_control_candidate": full_native,
        "v8_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v8 composes v7 and additionally requires every promotion-v6 second-order receipt used by the candidate "
            "to be the deterministic digest of a candidate-bound embedded evidence packet with nonempty observations "
            "and provenance. This closes the bare-boolean-plus-syntactic-digest self-attestation class but does not "
            "authenticate external runtime receipt digests or independently prove the observations true. Positive v8 "
            "status remains research adjudication only and mints no canonical semantics, runtime, HCU, EntityOS, "
            "training, BASE, or real-effect credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "v6_second_order_evidence_bound_candidate": False,
            "canonical_credit_minted": False,
            "v8_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        candidate = {}
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "scientifically_independent_vector_candidate": any(v.get("scientifically_independent_vector_candidate") is True for v in verdicts),
        "owner_trigger1_goal_credit_candidate": any(v.get("owner_trigger1_goal_credit_candidate") is True for v in verdicts),
        "modular_hcu_jspace_control_candidate": any(v.get("modular_hcu_jspace_control_candidate") is True for v in verdicts),
        "full_native_jspace_vector_control_candidate": any(v.get("full_native_jspace_vector_control_candidate") is True for v in verdicts),
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = parser.parse_args()
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
