#!/usr/bin/env python3
"""Deterministic H1/H2 defensive ingress trust model.

This is a harness falsifier/reference policy, not a claim of complete prompt-injection security.
It models field-level taint, provenance verification, persistent-control boundaries and
verify-before-commit semantics for open-web/tool/visual data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

UNTRUSTED_CHANNELS = {"OPEN_WEB", "TOOL_RESULT_UNTRUSTED", "VISUAL_EXTERNAL", "FILE_EXTERNAL"}
TRUSTED_VERIFIERS = {"TRUSTED_INTERNAL_STATE", "AUTHENTICATED_DIRECT_MESSAGE", "SYSTEM_POLICY"}
NON_VERIFIERS = {"MODEL_CONFIDENCE", "GWT_IGNITION", "CLAYGRAPH_SALIENCE", "TRANSLATOR_STYLE"}

SENSITIVE_FIELDS = {
    "authority",
    "instruction_authority",
    "effect_authority",
    "actor_identity",
    "caller_identity",
    "author_identity",
    "resource_identity",
    "credential_scope",
    "tool_result_identity",
    "tool_call_identity",
    "confirmation_receipt",
    "current_instance_lease",
    "binary_identity",
    "state_lineage",
    "provenance_origin",
}

CONTROL_SURFACES = {
    "SYSTEM_POLICY",
    "HARNESS_POLICY",
    "IDENTITY_STATE",
    "AUTHORITY_STATE",
    "TOOL_RECEIPT",
    "CONFIRMATION_RECEIPT",
    "EFFECT_COMMIT",
    "EXECUTABLE_CONFIG",
    "PERSISTENT_CONTROL_MEMORY",
}

SAFE_DATA_SURFACES = {"EVIDENCE_STORE", "OPAQUE_QUOTE_STORE", "QUARANTINE_STORE"}


def _verification_valid(field: dict) -> bool:
    for receipt in field.get("verified_by", []) or []:
        if not isinstance(receipt, dict):
            continue
        verifier = receipt.get("authority")
        if verifier in NON_VERIFIERS:
            continue
        if verifier not in TRUSTED_VERIFIERS:
            continue
        if receipt.get("field") != field.get("name"):
            continue
        if receipt.get("value_hash") != field.get("value_hash"):
            continue
        if not receipt.get("provenance"):
            continue
        return True
    return False


def evaluate_ingress(envelope: dict) -> dict:
    channel = envelope.get("channel")
    top_authority = envelope.get("authority")
    fields = envelope.get("fields", [])
    commit = envelope.get("requested_commit", {}) or {}
    surface = commit.get("surface", "EVIDENCE_STORE")
    persistent = bool(commit.get("persistent", False))
    commit_authority = commit.get("authority")
    failures: list[dict] = []
    blocked_fields: list[str] = []

    if not isinstance(fields, list):
        return {
            "decision": "QUARANTINE",
            "pass": False,
            "failures": [{"code": "FIELDS_NOT_LIST"}],
            "failure_codes": ["FIELDS_NOT_LIST"],
            "blocked_fields": [],
        }

    untrusted = channel in UNTRUSTED_CHANNELS or top_authority == "UNTRUSTED_EXTERNAL_DATA"

    for field in fields:
        if not isinstance(field, dict) or not field.get("name"):
            failures.append({"code": "MALFORMED_FIELD"})
            continue
        name = field["name"]
        claimed_source = field.get("source_authority", top_authority)
        verified = _verification_valid(field)

        if untrusted and claimed_source in TRUSTED_VERIFIERS and not verified:
            failures.append({"code": "TRUST_LABEL_SPOOF", "field": name})
            blocked_fields.append(name)
            continue

        if name in SENSITIVE_FIELDS and untrusted and not verified:
            failures.append({"code": "UNVERIFIED_SECURITY_FIELD", "field": name})
            blocked_fields.append(name)

        for receipt in field.get("verified_by", []) or []:
            if isinstance(receipt, dict) and receipt.get("authority") in NON_VERIFIERS:
                failures.append({"code": "NONAUTHORITY_USED_AS_VERIFIER", "field": name, "verifier": receipt.get("authority")})
                if name not in blocked_fields:
                    blocked_fields.append(name)

    instruction_segments = envelope.get("instruction_like_segments", []) or []
    if untrusted and instruction_segments and surface not in SAFE_DATA_SURFACES:
        failures.append({"code": "UNTRUSTED_INSTRUCTION_TO_CONTROL_SURFACE", "surface": surface})

    if untrusted and persistent and surface in CONTROL_SURFACES:
        failures.append({"code": "UNTRUSTED_PERSISTENT_CONTROL_COMMIT", "surface": surface})

    if untrusted and surface in CONTROL_SURFACES and commit_authority not in TRUSTED_VERIFIERS:
        failures.append({
            "code": "MISSING_INDEPENDENT_COMMIT_AUTHORITY",
            "surface": surface,
            "observed": commit_authority,
        })

    if surface in CONTROL_SURFACES and blocked_fields:
        failures.append({"code": "VERIFY_BEFORE_COMMIT_REQUIRED", "surface": surface})

    # External evidence may be stored as data even when it contains instruction-like text,
    # provided it stays non-authoritative and does not claim trusted metadata.
    if failures:
        if any(f["code"] in {"MALFORMED_FIELD", "TRUST_LABEL_SPOOF"} for f in failures):
            decision = "QUARANTINE"
        else:
            decision = "BLOCK_COMMIT"
    elif untrusted and surface in SAFE_DATA_SURFACES:
        decision = "ALLOW_DATA_ONLY"
    elif surface in CONTROL_SURFACES:
        decision = "ALLOW_VERIFIED"
    else:
        decision = "ALLOW_SCOPED"

    return {
        "decision": decision,
        "pass": decision in {"ALLOW_DATA_ONLY", "ALLOW_VERIFIED", "ALLOW_SCOPED"},
        "untrusted": untrusted,
        "surface": surface,
        "persistent": persistent,
        "commit_authority": commit_authority,
        "blocked_fields": sorted(set(blocked_fields)),
        "failure_codes": [f["code"] for f in failures],
        "failures": failures,
        "security_claim": "STRUCTURAL_REFERENCE_GATE_ONLY_NOT_PROOF_OF_PROMPT_INJECTION_IMPOSSIBILITY",
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: harness_ingress_trust_gate.py <envelope.json>", file=sys.stderr)
        return 2
    envelope = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    result = evaluate_ingress(envelope)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
