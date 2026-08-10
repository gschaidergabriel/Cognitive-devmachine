#!/usr/bin/env python3
"""CC-WP-03 residual semantic disposition gate v1.

Consumes the receipt-bound residual TypedIR produced by the current WP03 bridge and assigns
an explicit downstream disposition to every preserved top-level semantic node. V1 is
intentionally conservative: none of the ten currently observed residual classes is granted
evaluator/lowering admission before WP04/WP05 supplies class-specific semantic validation.

This closes a control-plane ambiguity, not WP03 itself. Preserved opaque semantics remain
visible, non-authoritative and fail closed. An unknown future class is retained and marked
REJECTED_WITH_REASON rather than being silently dropped or implicitly executed.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

SCHEMA = "ClayCodeWP03ResidualDisposition/v1"
DOMAIN = b"ClayCodeWP03ResidualDisposition/v1\x00"

LOWERED_AND_VALIDATED = "LOWERED_AND_VALIDATED"
EXPLICITLY_DEFERRED_FAIL_CLOSED = "EXPLICITLY_DEFERRED_FAIL_CLOSED"
REJECTED_WITH_REASON = "REJECTED_WITH_REASON"
ALLOWED = {
    LOWERED_AND_VALIDATED,
    EXPLICITLY_DEFERRED_FAIL_CLOSED,
    REJECTED_WITH_REASON,
}

# Exact real-Ubuntu inventory from WP03_OPAQUE_SEMANTIC_CLASS_INVENTORY_20260810T1527P0700.
CURRENT_INVENTORY = {
    "cycle_decl": 1,
    "dialect_decl": 9,
    "import_decl": 2,
    "invariant_decl": 14,
    "module_decl": 2,
    "parent_decl": 1,
    "rule_decl": 67,
    "status_decl": 1,
    "tensor_decl": 1,
    "version_decl": 2,
}

# V1 does not pretend that preservation equals semantic validation. Every current class is
# therefore explicitly deferred until its WP04 checker + WP05 evaluator/lowering contract is
# executable. The table exists so downstream code cannot infer acceptance from mere presence.
CURRENT_DISPOSITIONS = {
    kind: {
        "status": EXPLICITLY_DEFERRED_FAIL_CLOSED,
        "checker": "DENY_UNTIL_CLASS_SPECIFIC_VALIDATION_RECEIPT",
        "evaluator_lowering": "DENY",
        "effect_authority": "NONE",
        "reason": "canonical semantics preserved in TypedIR identity but class-specific legality/lowering is not yet verified",
    }
    for kind in CURRENT_INVENTORY
}


class ResidualDispositionError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _kind(row: Any) -> str:
    if not isinstance(row, dict):
        raise ResidualDispositionError("opaque residual row must be an object")
    value = row.get("kind")
    if not isinstance(value, str) or not value:
        raise ResidualDispositionError("opaque residual row is missing a non-empty kind")
    return value


def disposition_for(kind: str) -> dict[str, str]:
    current = CURRENT_DISPOSITIONS.get(kind)
    if current is not None:
        return dict(current)
    return {
        "status": REJECTED_WITH_REASON,
        "checker": "REJECT_UNKNOWN_RESIDUAL_CLASS",
        "evaluator_lowering": "DENY",
        "effect_authority": "NONE",
        "reason": "residual class is outside the receipt-bound ten-class WP03 inventory; explicit migration/review required",
    }


def apply_dispositions(typed_ir: dict[str, Any], *, require_current_inventory: bool = False) -> dict[str, Any]:
    opaque = typed_ir.get("opaque_unlowered_semantics")
    if not isinstance(opaque, list):
        raise ResidualDispositionError("TypedIR must contain opaque_unlowered_semantics list")

    rows = []
    for index, residual in enumerate(opaque):
        kind = _kind(residual)
        decision = disposition_for(kind)
        rows.append({
            "index": index,
            "kind": kind,
            "status": decision["status"],
            "checker": decision["checker"],
            "evaluator_lowering": decision["evaluator_lowering"],
            "effect_authority": decision["effect_authority"],
            "reason": decision["reason"],
            "residual_semantic_sha256": sha256(stable_json(residual)),
        })

    observed = dict(sorted(Counter(row["kind"] for row in rows).items()))
    if require_current_inventory and observed != CURRENT_INVENTORY:
        raise ResidualDispositionError(
            f"residual inventory drift: expected {CURRENT_INVENTORY!r}, observed {observed!r}"
        )

    rejected = sum(row["status"] == REJECTED_WITH_REASON for row in rows)
    deferred = sum(row["status"] == EXPLICITLY_DEFERRED_FAIL_CLOSED for row in rows)
    lowered = sum(row["status"] == LOWERED_AND_VALIDATED for row in rows)
    evaluator_admitted = lowered == len(rows) and len(rows) > 0

    core = {
        "schema": SCHEMA,
        "typed_ir_sha256": typed_ir.get("typed_ir_sha256"),
        "observed_kind_counts": observed,
        "rows": rows,
        "summary": {
            "total": len(rows),
            "lowered_and_validated": lowered,
            "explicitly_deferred_fail_closed": deferred,
            "rejected_with_reason": rejected,
            "evaluator_admitted": evaluator_admitted,
            "effect_authority": "NONE",
        },
    }
    receipt_hash = sha256(DOMAIN + stable_json(core))
    return {
        **core,
        "disposition_receipt_sha256": receipt_hash,
        "invariants": {
            "silent_drop": "FORBIDDEN",
            "implicit_execution": "FORBIDDEN",
            "unknown_residual_class": "REJECT_WITH_REASON",
            "opaque_semantics_effect_authority": "NONE",
            "presence_does_not_imply_legality": True,
            "presence_does_not_imply_evaluator_admission": True,
        },
        "promotion": "NONE",
        "wp03_status": "OPEN",
        "wp04_status": "OPEN",
        "wp05_status": "OPEN",
    }


def validate_receipt(receipt: dict[str, Any]) -> None:
    rows = receipt.get("rows")
    if not isinstance(rows, list):
        raise ResidualDispositionError("disposition receipt rows missing")
    for row in rows:
        status = row.get("status")
        if status not in ALLOWED:
            raise ResidualDispositionError(f"illegal residual status: {status!r}")
        if row.get("effect_authority") != "NONE":
            raise ResidualDispositionError("residual semantics attempted to mint effect authority")
        if status != LOWERED_AND_VALIDATED and row.get("evaluator_lowering") != "DENY":
            raise ResidualDispositionError("non-lowered residual was admitted to evaluator/lowering")
    summary = receipt.get("summary") or {}
    admitted = bool(summary.get("evaluator_admitted"))
    all_lowered = bool(rows) and all(row.get("status") == LOWERED_AND_VALIDATED for row in rows)
    if admitted != all_lowered:
        raise ResidualDispositionError("evaluator admission summary disagrees with per-row dispositions")
