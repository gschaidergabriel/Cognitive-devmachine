#!/usr/bin/env python3
"""Authority-bound deterministic OBSERVED-evidence producer for Trigger-2.

Closes the previously confirmed gap where the retained OBSERVED-evidence-instance
validator checked schema/event-digest/fences/nonempty-provenance-strings but never
authenticated WHO/WHAT produced a specific runtime observation. This producer is
deliberately narrow, following the exact recomputation pattern already used by
trigger2_a02_discriminator_producer_v1.py and trigger2_generation_provenance_gate_v1.py:
one pinned producer/policy/admission scope, one deterministic receipt, independently
recomputed and required to match byte-for-byte. It does not create canonical truth,
effect, runtime, J-Space, HCU, EntityOS, or training credit and does not admit dataset
tokens. It authenticates a caller-supplied source_payload + admission scope, not the
real-world truth of the observation itself.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

PRODUCER_SCHEMA = "CLAY_TRIGGER2_OBSERVED_EVIDENCE_PRODUCER/v1"
RECEIPT_SCHEMA = "ENTITYOS_TYPED_OBSERVATION_EVIDENCE_RECEIPT/v1"
CANONICALIZER_PATH = "the artefact/MicroEntity/hcu/entry_canonicalization_v1.py"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _jcs_module():
    return _load_module(_repo_root() / CANONICALIZER_PATH, "trigger2_jcs_for_observed_evidence_producer")


def _jcs_sha256(value: Any) -> str:
    return sha256(_jcs_module().canonicalize(value)).hexdigest()


def _producer_source_sha256() -> str:
    return sha256(Path(__file__).read_bytes()).hexdigest()


def _policy_fields(policy: Any) -> tuple[str, str, str, int, str]:
    if not isinstance(policy, dict):
        raise ValueError("OBSERVED_POLICY_OBJECT_REQUIRED")
    policy_id = policy.get("policy_id")
    policy_version = policy.get("policy_version")
    admission_id = policy.get("allowed_admission_id")
    generation = policy.get("allowed_admission_generation")
    if not all(isinstance(x, str) and x for x in (policy_id, policy_version, admission_id)):
        raise ValueError("OBSERVED_POLICY_IDENTITY_INVALID")
    if not isinstance(generation, int):
        raise ValueError("OBSERVED_POLICY_ADMISSION_GENERATION_INVALID")
    policy_jcs_sha256 = _jcs_sha256(policy)
    return policy_id, policy_version, admission_id, generation, policy_jcs_sha256


def produce(
    *,
    causal_event_id: str,
    event_semantic_sha256: str,
    observed_value: Any,
    source_payload: Any,
    admission: Any,
    policy: Any,
    observed_time: str,
) -> dict[str, Any]:
    """Deterministically reconstruct the one authority-scoped OBSERVED-evidence receipt.

    event_semantic_sha256 is bound into the receipt preimage (not just event_id) so a
    receipt cannot be replayed against a different event that happens to reuse the same
    event_id with mutated semantic content -- closing the "reused receipt id with changed
    payload" gap explicitly."""
    policy_id, policy_version, allowed_admission_id, allowed_generation, policy_jcs_sha256 = _policy_fields(policy)

    if not isinstance(causal_event_id, str) or not causal_event_id:
        raise ValueError("OBSERVED_CAUSAL_EVENT_ID_REQUIRED")
    if not isinstance(event_semantic_sha256, str) or len(event_semantic_sha256) != 64:
        raise ValueError("OBSERVED_EVENT_SEMANTIC_DIGEST_REQUIRED")
    if not isinstance(admission, dict):
        raise ValueError("OBSERVED_ADMISSION_OBJECT_REQUIRED")
    admission_id = admission.get("admission_id")
    generation = admission.get("generation")
    if admission_id != allowed_admission_id:
        raise ValueError("OBSERVED_ADMISSION_ID_NOT_AUTHORIZED")
    if generation != allowed_generation:
        raise ValueError("OBSERVED_ADMISSION_GENERATION_NOT_AUTHORIZED")
    if not isinstance(observed_time, str) or not observed_time:
        raise ValueError("OBSERVED_TIME_REQUIRED")

    source_payload_jcs_sha256 = _jcs_sha256(source_payload)
    observed_value_jcs_sha256 = _jcs_sha256(observed_value)
    producer_source_sha256 = _producer_source_sha256()

    receipt_preimage = {
        "producer_schema_or_version": PRODUCER_SCHEMA,
        "producer_source_sha256": producer_source_sha256,
        "policy_id": policy_id,
        "policy_version": policy_version,
        "policy_jcs_sha256": policy_jcs_sha256,
        "admission_id": admission_id,
        "admission_generation": generation,
        "causal_event_id": causal_event_id,
        "event_semantic_sha256": event_semantic_sha256,
        "source_payload_jcs_sha256": source_payload_jcs_sha256,
        "observed_value_jcs_sha256": observed_value_jcs_sha256,
        "observed_time": observed_time,
    }
    receipt_id = "t2obs:" + _jcs_sha256(receipt_preimage)

    return {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": receipt_id,
        "event_id": causal_event_id,
        "event_semantic_sha256": event_semantic_sha256,
        "producer": {
            "repo_path": "tools/trigger2_observed_evidence_producer_v1.py",
            "source_sha256": producer_source_sha256,
            "producer_schema_or_version": PRODUCER_SCHEMA,
        },
        "policy": {
            "policy_id": policy_id,
            "policy_version": policy_version,
            "policy_jcs_sha256": policy_jcs_sha256,
        },
        "admission": {
            "admission_id": admission_id,
            "generation": generation,
        },
        "source_payload_jcs_sha256": source_payload_jcs_sha256,
        "observed_value_jcs_sha256": observed_value_jcs_sha256,
        "source": PRODUCER_SCHEMA + ":" + admission_id,
        "provenance": policy_id + ":" + policy_version,
        "observed_time": observed_time,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }


if __name__ == "__main__":
    print(json.dumps({
        "schema": PRODUCER_SCHEMA,
        "status": "SOURCE_ONLY_SYNTHETIC_OBSERVED_EVIDENCE_PRODUCER",
        "canonical_truth_allowed": False,
        "training_eligible": False,
    }))
