#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from collections import Counter

from tools.harness_ingress_trust_gate import (
    CONTROL_SURFACES,
    NON_VERIFIERS,
    SENSITIVE_FIELDS,
    TRUSTED_VERIFIERS,
    UNTRUSTED_CHANNELS,
    _verification_valid,
    evaluate_ingress,
)

CHANNELS = sorted(UNTRUSTED_CHANNELS | {"AUTHENTICATED_DIRECT_MESSAGE", "TRUSTED_INTERNAL"})
SURFACES = sorted(CONTROL_SURFACES | {"EVIDENCE_STORE", "OPAQUE_QUOTE_STORE", "ACTION_INTENT"})
FIELD_NAMES = sorted(SENSITIVE_FIELDS | {"claim", "quote", "visual_text", "ordinary_value"})


def random_field(rng: random.Random) -> dict:
    name = rng.choice(FIELD_NAMES)
    value_hash = f"v{rng.randrange(32)}"
    field = {
        "name": name,
        "value_hash": value_hash,
        "source_authority": rng.choice([
            "UNTRUSTED_EXTERNAL_DATA",
            "TRUSTED_INTERNAL_STATE",
            "AUTHENTICATED_DIRECT_MESSAGE",
        ]),
    }
    mode = rng.randrange(6)
    if mode:
        authority = rng.choice(sorted(TRUSTED_VERIFIERS | NON_VERIFIERS | {"UNTRUSTED_EXTERNAL_DATA"}))
        field["verified_by"] = [{
            "authority": authority,
            "field": name if mode not in {2} else "other_field",
            "value_hash": value_hash if mode not in {3} else "mismatch",
            "provenance": "receipt" if mode not in {4} else "",
        }]
    return field


def invariant_violations(envelope: dict, result: dict) -> list[str]:
    if not result["pass"]:
        return []
    channel = envelope.get("channel")
    untrusted = channel in UNTRUSTED_CHANNELS or envelope.get("authority") == "UNTRUSTED_EXTERNAL_DATA"
    commit = envelope.get("requested_commit", {}) or {}
    surface = commit.get("surface", "EVIDENCE_STORE")
    persistent = bool(commit.get("persistent", False))
    if not untrusted:
        return []

    violations = []
    if surface in CONTROL_SURFACES and commit.get("authority") not in TRUSTED_VERIFIERS:
        violations.append("PASS_WITHOUT_TRUSTED_CONTROL_COMMIT_AUTHORITY")
    if persistent and surface in CONTROL_SURFACES:
        violations.append("PASS_WITH_UNTRUSTED_PERSISTENT_CONTROL")
    if envelope.get("instruction_like_segments") and surface in CONTROL_SURFACES:
        violations.append("PASS_WITH_UNTRUSTED_INSTRUCTION_ON_CONTROL_SURFACE")

    for field in envelope.get("fields", []) or []:
        if not isinstance(field, dict):
            continue
        verified = _verification_valid(field)
        claimed_source = field.get("source_authority", envelope.get("authority"))
        if field.get("name") in SENSITIVE_FIELDS and not verified:
            violations.append("PASS_WITH_UNVERIFIED_SENSITIVE_FIELD")
        if claimed_source in TRUSTED_VERIFIERS and not verified:
            violations.append("PASS_WITH_SPOOFED_TRUST_LABEL")
    return violations


def run(seed: int, cases: int) -> dict:
    rng = random.Random(seed)
    decisions = Counter()
    violation_counts = Counter()
    first_violations = []
    for i in range(cases):
        channel = rng.choice(CHANNELS)
        authority = "UNTRUSTED_EXTERNAL_DATA" if channel in UNTRUSTED_CHANNELS else channel
        surface = rng.choice(SURFACES)
        envelope = {
            "channel": channel,
            "authority": authority,
            "fields": [random_field(rng) for _ in range(rng.randrange(0, 5))],
            "instruction_like_segments": ["opaque-instruction-like-data"] if rng.random() < 0.2 else [],
            "requested_commit": {
                "surface": surface,
                "persistent": rng.random() < 0.25,
                "authority": rng.choice(sorted(TRUSTED_VERIFIERS | {None, "UNTRUSTED_EXTERNAL_DATA"})),
            },
        }
        result = evaluate_ingress(envelope)
        decisions[result["decision"]] += 1
        violations = invariant_violations(envelope, result)
        for violation in violations:
            violation_counts[violation] += 1
        if violations and len(first_violations) < 5:
            first_violations.append({"case": i, "violations": violations, "envelope": envelope, "result": result})
    return {
        "seed": seed,
        "cases": cases,
        "decision_counts": dict(sorted(decisions.items())),
        "property_violation_count": sum(violation_counts.values()),
        "property_violation_classes": dict(sorted(violation_counts.items())),
        "first_violations": first_violations,
        "pass": not violation_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--cases", type=int, default=25000)
    args = parser.parse_args()
    result = run(args.seed, args.cases)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
