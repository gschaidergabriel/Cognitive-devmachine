#!/usr/bin/env python3
"""Deterministic tests for the WP03 residual disposition gate.

Includes exactly one GO out-of-box experiment: SEMANTIC_CONFETTI. It permutes the complete
100-node measured inventory, then injects one novel residual class. The gate must preserve
all known nodes, explicitly reject the novel class, keep evaluator admission closed and
never mint effect authority. This is a bounded mechanism falsifier, not release evidence.
"""
from __future__ import annotations

import copy
import json
import random

import claycode_wp03_residual_disposition_v1 as disp


def make_inventory() -> list[dict]:
    rows = []
    for kind, count in disp.CURRENT_INVENTORY.items():
        for index in range(count):
            rows.append({
                "kind": kind,
                "canonical_ast": {
                    "kind": kind,
                    "children": [{"token": "SYNTHETIC", "value": f"{kind}:{index}"}],
                },
            })
    return rows


def base_ir(rows: list[dict]) -> dict:
    return {
        "typed_ir_sha256": "0" * 64,
        "opaque_unlowered_semantics": rows,
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    checks = []

    rows = make_inventory()
    require(len(rows) == 100, "measured inventory fixture must contain 100 residual nodes")
    receipt = disp.apply_dispositions(base_ir(rows), require_current_inventory=True)
    disp.validate_receipt(receipt)
    summary = receipt["summary"]
    require(summary["total"] == 100, "no-drop total mismatch")
    require(summary["explicitly_deferred_fail_closed"] == 100, "v1 must defer all current residuals")
    require(summary["lowered_and_validated"] == 0, "v1 must not claim unearned lowering")
    require(summary["rejected_with_reason"] == 0, "known inventory should not be rejected")
    require(summary["evaluator_admitted"] is False, "evaluator must remain closed")
    require(summary["effect_authority"] == "NONE", "residuals cannot mint authority")
    checks.append("exact_inventory_no_drop_fail_closed")

    # Semantic mutation must change the corresponding preserved residual identity.
    mutated = copy.deepcopy(rows)
    mutated[0]["canonical_ast"]["children"][0]["value"] += ":MUTATED"
    mutated_receipt = disp.apply_dispositions(base_ir(mutated), require_current_inventory=True)
    require(
        receipt["rows"][0]["residual_semantic_sha256"]
        != mutated_receipt["rows"][0]["residual_semantic_sha256"],
        "semantic mutation was not discriminated",
    )
    checks.append("semantic_mutation_discriminated")

    # Tamper with a non-authoritative decision and require validation to fail closed.
    tampered = copy.deepcopy(receipt)
    tampered["rows"][0]["effect_authority"] = "MINTED"
    rejected = False
    try:
        disp.validate_receipt(tampered)
    except disp.ResidualDispositionError:
        rejected = True
    require(rejected, "authority tamper was not rejected")
    checks.append("authority_tamper_rejected")

    # Exactly one GO out-of-box experiment: SEMANTIC_CONFETTI.
    confetti = copy.deepcopy(rows)
    random.Random(20260810).shuffle(confetti)
    confetti.append({
        "kind": "future_decl",
        "canonical_ast": {"kind": "future_decl", "children": [{"token": "FUTURE", "value": "novel"}]},
    })
    confetti_receipt = disp.apply_dispositions(base_ir(confetti))
    disp.validate_receipt(confetti_receipt)
    require(confetti_receipt["summary"]["total"] == 101, "confetti node was silently dropped")
    require(
        confetti_receipt["summary"]["explicitly_deferred_fail_closed"] == 100,
        "known confetti nodes changed disposition",
    )
    require(confetti_receipt["summary"]["rejected_with_reason"] == 1, "unknown class was not rejected")
    require(confetti_receipt["summary"]["evaluator_admitted"] is False, "confetti opened evaluator admission")
    require(
        all(row["effect_authority"] == "NONE" for row in confetti_receipt["rows"]),
        "confetti minted effect authority",
    )
    checks.append("OOB_SEMANTIC_CONFETTI_PASS")

    print(json.dumps({
        "schema_version": "1.0",
        "scope": "CC_WP03_RESIDUAL_DISPOSITION_V1_LOCAL_DETERMINISTIC",
        "checks": checks,
        "check_count": len(checks),
        "inventory_total": 100,
        "inventory_classes": len(disp.CURRENT_INVENTORY),
        "oob_experiment": "SEMANTIC_CONFETTI",
        "oob_seed": 20260810,
        "oob_result": "PASS",
        "promotion": "NONE",
        "wp03_status": "OPEN",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
