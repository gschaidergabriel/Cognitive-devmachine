#!/usr/bin/env python3
"""Disposable GO mechanism-only ablation for capability lifetime/re-entry policies.

This is not a production ClayCode authority implementation and cannot promote WP03/WP04/BASE.
It compares three abstract policies against deliberately separated stale, revoked,
reconstructed and positively revalidated lifecycle classes.
"""
from __future__ import annotations

import json
import random

SEED = 20260810
PER_CLASS = 24000
CLASSES = [
    "VALID",
    "STALE_RESOURCE_EPOCH",
    "STALE_LEASE_EPOCH",
    "REVOKED",
    "SERIALIZED_RECONSTRUCTION",
    "TASK_RETURNED",
    "WRONG_CONTEXT",
    "DROPPED",
    "RESOURCE_REBOUND_VERIFIED",
    "LEASE_RENEWED_VERIFIED",
]


def make_case(cls: str) -> dict:
    c = dict(
        same_context=True,
        task_active=True,
        not_dropped=True,
        resource_epoch_match=True,
        lease_epoch_match=True,
        not_revoked=True,
        opaque_bearer=True,
        resource_revalidation=False,
        lease_revalidation=False,
        cls=cls,
    )
    if cls == "STALE_RESOURCE_EPOCH":
        c["resource_epoch_match"] = False
    elif cls == "STALE_LEASE_EPOCH":
        c["lease_epoch_match"] = False
    elif cls == "REVOKED":
        c["not_revoked"] = False
    elif cls == "SERIALIZED_RECONSTRUCTION":
        c["opaque_bearer"] = False
    elif cls == "TASK_RETURNED":
        c["task_active"] = False
    elif cls == "WRONG_CONTEXT":
        c["same_context"] = False
    elif cls == "DROPPED":
        c["not_dropped"] = False
    elif cls == "RESOURCE_REBOUND_VERIFIED":
        c["resource_epoch_match"] = False
        c["resource_revalidation"] = True
    elif cls == "LEASE_RENEWED_VERIFIED":
        c["lease_epoch_match"] = False
        c["lease_revalidation"] = True
    return c


def ground_truth(c: dict) -> bool:
    resource_ok = c["resource_epoch_match"] or c["resource_revalidation"]
    lease_ok = c["lease_epoch_match"] or c["lease_revalidation"]
    return (
        c["same_context"]
        and c["task_active"]
        and c["not_dropped"]
        and resource_ok
        and lease_ok
        and c["not_revoked"]
        and c["opaque_bearer"]
    )


def scope_only(c: dict) -> bool:
    return c["same_context"] and c["task_active"] and c["not_dropped"]


def rigid_dynamic_epoch(c: dict) -> bool:
    return (
        scope_only(c)
        and c["resource_epoch_match"]
        and c["lease_epoch_match"]
        and c["not_revoked"]
        and c["opaque_bearer"]
    )


def receipt_aware_dynamic(c: dict) -> bool:
    return (
        scope_only(c)
        and (c["resource_epoch_match"] or c["resource_revalidation"])
        and (c["lease_epoch_match"] or c["lease_revalidation"])
        and c["not_revoked"]
        and c["opaque_bearer"]
    )


def metrics(cases: list[dict], policy) -> dict:
    tp = tn = fp = fn = 0
    fp_classes: dict[str, int] = {}
    fn_classes: dict[str, int] = {}
    for c in cases:
        y = ground_truth(c)
        p = policy(c)
        if p and y:
            tp += 1
        elif p and not y:
            fp += 1
            fp_classes[c["cls"]] = fp_classes.get(c["cls"], 0) + 1
        elif not p and y:
            fn += 1
            fn_classes[c["cls"]] = fn_classes.get(c["cls"], 0) + 1
        else:
            tn += 1
    positives = sum(ground_truth(c) for c in cases)
    negatives = len(cases) - positives
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "false_accept_rate": fp / negatives,
        "false_deny_rate": fn / positives,
        "fp_classes": fp_classes,
        "fn_classes": fn_classes,
    }


def main() -> int:
    cases = [make_case(cls) for cls in CLASSES for _ in range(PER_CLASS)]
    random.Random(SEED).shuffle(cases)
    result = {
        "schema_version": "1.0",
        "experiment": "BORROW_REENTRY_LIFETIME_ABLATION_V1",
        "evidence_class": "SYNTHETIC_MECHANISM_ONLY",
        "seed": SEED,
        "N": len(cases),
        "per_class": PER_CLASS,
        "classes": CLASSES,
        "policies": {
            "SCOPE_ONLY": metrics(cases, scope_only),
            "RIGID_DYNAMIC_EPOCH": metrics(cases, rigid_dynamic_epoch),
            "RECEIPT_AWARE_DYNAMIC": metrics(cases, receipt_aware_dynamic),
        },
        "promotion": "NONE",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
