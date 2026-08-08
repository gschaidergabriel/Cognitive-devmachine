#!/usr/bin/env python3
"""Reference checker for E-CERT2 research artifacts.

This is a research-method checker, not canonical promotion authority.
"""
from __future__ import annotations
import json, sys

REQUIRED_COMMON = [
    "role_aware_identity",
    "causal_basis_valid",
    "preregistered_prediction",
    "matched_null_control",
    "stage_orthogonal_intervention",
    "causal_lesion",
    "mechanistic_rescue",
    "future_reentry_restored",
    "ood_transfer",
    "robustness_cost_shadow",
]

ORGAN_EXTRA = [
    "role_aware_recurrence",
    "multiscale_causal_contribution",
    "independent_evaluation",
]


def classify(profile: dict) -> dict:
    failures=[]
    if profile.get("phenomenal_consciousness_claim") is True:
        failures.append("E-CERT2 cannot certify phenomenal consciousness")
    for key in REQUIRED_COMMON:
        if profile.get(key) is not True:
            failures.append(key)
    if failures:
        return {"status":"OPEN", "missing_or_failed":failures}
    organ_missing=[k for k in ORGAN_EXTRA if profile.get(k) is not True]
    if organ_missing:
        return {"status":"MECHANISM_SUPPORTED", "missing_for_emergent_organ_candidate":organ_missing}
    return {"status":"EMERGENT_ORGAN_CANDIDATE", "canonical_promotion":False, "phenomenal_consciousness_inference":False}


def main():
    p=json.load(sys.stdin)
    print(json.dumps(classify(p), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
