#!/usr/bin/env python3
"""SourceChainEvidence v1.2: requires independent semantic-preservation evidence."""
from __future__ import annotations
import hashlib
import re
from typing import Any
from source_chain_oracle_v1_1 import (
    build_fixture as _build_fixture_v11,
    differential_oracle as _differential_v11,
    validate_chain as _validate_v11,
)

HASH64 = re.compile(r"^[0-9a-f]{64}$")


def _hash64(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH64.fullmatch(value))


def validate_chain(chain: dict[str, Any]) -> dict[str, Any]:
    result = _validate_v11(chain)
    errors = list(result["errors"])
    proof = chain.get("semantic_preservation")
    if not isinstance(proof, dict):
        errors.append({"code":"SEMANTIC_PRESERVATION_REQUIRED","path":"$.semantic_preservation","detail":"chain integrity is necessary but insufficient; an independent semantic-preservation receipt is required"})
        return {"valid": False, "errors": errors}
    if proof.get("status") != "PASS":
        errors.append({"code":"SEMANTIC_PRESERVATION_NOT_PASS","path":"$.semantic_preservation.status","detail":"semantic preservation oracle must pass"})
    if not isinstance(proof.get("oracle_ref"), str) or not proof.get("oracle_ref"):
        errors.append({"code":"SEMANTIC_ORACLE_REF_REQUIRED","path":"$.semantic_preservation.oracle_ref","detail":"oracle implementation/evidence reference is required"})
    if not _hash64(proof.get("oracle_hash")):
        errors.append({"code":"SEMANTIC_ORACLE_HASH_REQUIRED","path":"$.semantic_preservation.oracle_hash","detail":"oracle contract/implementation must be content-addressed"})
    for field in ("expected_observation_hash", "observed_observation_hash"):
        if not _hash64(proof.get(field)):
            errors.append({"code":"SEMANTIC_OBSERVATION_HASH_REQUIRED","path":f"$.semantic_preservation.{field}","detail":"expected and observed semantic observations must be content-addressed"})
    if _hash64(proof.get("expected_observation_hash")) and _hash64(proof.get("observed_observation_hash")) and proof["expected_observation_hash"] != proof["observed_observation_hash"]:
        errors.append({"code":"SEMANTIC_ORACLE_DIVERGENCE","path":"$.semantic_preservation.observed_observation_hash","detail":"executed target observation differs from independent expected semantic observation"})
    return {"valid": not errors, "errors": errors}


def differential_oracle(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    ref_validation = validate_chain(reference)
    cand_validation = validate_chain(candidate)
    if not ref_validation["valid"] or not cand_validation["valid"]:
        return {"equivalent":False,"reference_validation":ref_validation,"candidate_validation":cand_validation,"mismatches":[{"stage":"validation","detail":"both v1.2 chains must validate before differential comparison"}]}
    result = _differential_v11(reference, candidate)
    mismatches = list(result["mismatches"])
    rp, cp = reference["semantic_preservation"], candidate["semantic_preservation"]
    for field in ("oracle_hash", "expected_observation_hash", "observed_observation_hash"):
        if rp.get(field) != cp.get(field):
            mismatches.append({"stage":"semantic_preservation","field":field,"reference":str(rp.get(field)),"candidate":str(cp.get(field))})
    return {"equivalent":not mismatches,"reference_validation":ref_validation,"candidate_validation":cand_validation,"mismatches":mismatches}


def build_fixture(**kwargs: Any) -> dict[str, Any]:
    fixture = _build_fixture_v11(**kwargs)
    obs = hashlib.sha256(b"semantic-observation-v1.2").hexdigest()
    fixture["semantic_preservation"] = {
        "status":"PASS",
        "oracle_ref":"oracle:fixture-semantics",
        "oracle_hash":hashlib.sha256(b"semantic-oracle-v1.2").hexdigest(),
        "expected_observation_hash":obs,
        "observed_observation_hash":obs,
    }
    return fixture
