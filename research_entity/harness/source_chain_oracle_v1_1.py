#!/usr/bin/env python3
"""SourceChainEvidence v1.1: parser-semantics identity extension over v1."""
from __future__ import annotations
import hashlib
import re
from typing import Any
from source_chain_oracle_v1 import (
    build_fixture as _build_fixture_v1,
    differential_oracle as _differential_v1,
    validate_chain as _validate_v1,
)

HASH64 = re.compile(r"^[0-9a-f]{64}$")


def _hash64(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH64.fullmatch(value))


def validate_chain(chain: dict[str, Any]) -> dict[str, Any]:
    result = _validate_v1(chain)
    errors = list(result["errors"])
    parse = chain.get("stages", {}).get("parse", {}) if isinstance(chain.get("stages"), dict) else {}
    if not _hash64(parse.get("parser_semantics_hash")):
        errors.append({
            "code": "PARSER_SEMANTICS_IDENTITY_REQUIRED",
            "path": "$.stages.parse.parser_semantics_hash",
            "detail": "parser precedence/associativity/fallback semantics must be content-addressed separately from grammar syntax",
        })
    return {"valid": not errors, "errors": errors}


def differential_oracle(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    ref_validation = validate_chain(reference)
    cand_validation = validate_chain(candidate)
    if not ref_validation["valid"] or not cand_validation["valid"]:
        return {
            "equivalent": False,
            "reference_validation": ref_validation,
            "candidate_validation": cand_validation,
            "mismatches": [{"stage": "validation", "detail": "both v1.1 chains must validate before differential comparison"}],
        }
    result = _differential_v1(reference, candidate)
    mismatches = list(result["mismatches"])
    rv = reference["stages"]["parse"].get("parser_semantics_hash")
    cv = candidate["stages"]["parse"].get("parser_semantics_hash")
    if rv != cv:
        mismatches.append({
            "stage": "parse",
            "field": "parser_semantics_hash",
            "reference": str(rv),
            "candidate": str(cv),
        })
    return {
        "equivalent": not mismatches,
        "reference_validation": ref_validation,
        "candidate_validation": cand_validation,
        "mismatches": mismatches,
    }


def build_fixture(**kwargs: Any) -> dict[str, Any]:
    fixture = _build_fixture_v1(**kwargs)
    fixture["stages"]["parse"]["parser_semantics_hash"] = hashlib.sha256(b"parser-semantics-v1.1").hexdigest()
    return fixture
