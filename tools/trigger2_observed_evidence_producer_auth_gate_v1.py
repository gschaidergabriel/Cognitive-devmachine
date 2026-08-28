#!/usr/bin/env python3
"""Trigger-2 OBSERVED-evidence producer authentication gate v1.

Closes the confirmed gap where a caller-minted OBSERVED evidence receipt (arbitrary
source/provenance/receipt_id strings, otherwise schema-valid) was accepted with zero
authentication. This gate resolves the one authorized producer/policy/admission scope
from a repository authority manifest, verifies the producer's exact source bytes,
deterministically recomputes the expected receipt from the caller-supplied
source_payload/admission/observed_value/event identity, and requires the claimed
receipt to match byte-for-byte -- exactly the recomputation pattern already used by
trigger2_a02_discriminator_producer_auth_gate_v1.py and
trigger2_generation_provenance_gate_v1.py. No second truth store or parallel labeler
is introduced.

Component only. PASS does not mint canonical truth/effect/runtime/J-Space/HCU/EntityOS/
training credit and does not admit dataset tokens.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_OBSERVED_EVIDENCE_PRODUCER_AUTH_GATE/v1"
AUTHORITY_PATH = "research_entity/global/j-space/research/TRIGGER2_OBSERVED_EVIDENCE_PRODUCER_AUTHORITY_V1.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _authority() -> dict[str, Any]:
    return json.loads((_repo_root() / AUTHORITY_PATH).read_text(encoding="utf-8"))


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "observed_producer_auth_pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }
    out.update(extra)
    return out


def adjudicate(
    *,
    claimed_receipt: Any,
    causal_event_id: Any,
    event_semantic_sha256: Any,
    observed_value: Any,
    source_payload: Any,
    admission: Any,
    observed_time: Any,
) -> dict[str, Any]:
    failures: list[str] = []

    try:
        authority = _authority()
    except Exception as exc:
        return _result(["AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if authority.get("schema") != "CLAY_TRIGGER2_OBSERVED_EVIDENCE_PRODUCER_AUTHORITY/v1":
        failures.append("OBSERVED_PRODUCER_AUTHORITY_SCHEMA_MISMATCH")
    fences = authority.get("authority_fences")
    if not isinstance(fences, dict) or fences != {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
    }:
        failures.append("OBSERVED_PRODUCER_AUTHORITY_FENCES_INVALID")

    producer_authority = authority.get("producer")
    if not isinstance(producer_authority, dict):
        return _result(failures + ["OBSERVED_PRODUCER_AUTHORITY_OBJECT_REQUIRED"])
    expected_path = producer_authority.get("repo_path")
    if not isinstance(expected_path, str) or not expected_path:
        return _result(failures + ["EXPECTED_OBSERVED_PRODUCER_PATH_REQUIRED"])
    producer_path = (_repo_root() / expected_path).resolve()
    try:
        producer_path.relative_to(_repo_root().resolve())
    except ValueError:
        return _result(failures + ["EXPECTED_OBSERVED_PRODUCER_PATH_ESCAPES_REPO"])
    if not producer_path.is_file():
        return _result(failures + ["EXPECTED_OBSERVED_PRODUCER_FILE_MISSING"])

    actual_source_sha = _source_sha256(producer_path)
    if actual_source_sha != producer_authority.get("source_sha256"):
        failures.append("EXPECTED_OBSERVED_PRODUCER_SOURCE_SHA256_MISMATCH")

    try:
        producer = _load_module(producer_path, "trigger2_observed_evidence_producer_for_auth_gate")
    except Exception as exc:
        return _result(failures + ["EXPECTED_OBSERVED_PRODUCER_IMPORT_FAILED:" + type(exc).__name__])
    if getattr(producer, "PRODUCER_SCHEMA", None) != producer_authority.get("producer_schema_or_version"):
        failures.append("EXPECTED_OBSERVED_PRODUCER_SCHEMA_MISMATCH")

    policy = authority.get("policy")

    if not isinstance(claimed_receipt, dict):
        return _result(failures + ["OBSERVED_RECEIPT_OBJECT_REQUIRED"], expected_producer_path=expected_path)

    try:
        expected_receipt = producer.produce(
            causal_event_id=causal_event_id,
            event_semantic_sha256=event_semantic_sha256,
            observed_value=observed_value,
            source_payload=source_payload,
            admission=admission,
            policy=policy,
            observed_time=observed_time,
        )
    except Exception as exc:
        failures.append("OBSERVED_RECEIPT_RECOMPUTATION_FAILED:" + type(exc).__name__)
        expected_receipt = None

    if expected_receipt is not None and claimed_receipt != expected_receipt:
        failures.append("OBSERVED_RECEIPT_NOT_EXACTLY_RECOMPUTED")

    return _result(
        failures,
        expected_producer_path=expected_path,
        expected_producer_source_sha256=actual_source_sha,
        expected_receipt=expected_receipt,
    )


if __name__ == "__main__":
    print(json.dumps({"schema": SCHEMA, "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION"}))
