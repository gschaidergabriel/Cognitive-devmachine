#!/usr/bin/env python3
"""Fail-closed source gate for Trigger-2 V35 runtime-proof/stale-observation eval seed.

This validator is intentionally non-promoting.  It checks only the static eval corpus
contract and must never mint dataset, training, model-runtime, HCU, or EntityOS credit.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_V35_HARDNEG_EVAL_ROW/v1"
CHANNEL = "EVAL_ONLY_HARD_NEGATIVE"
EXPECTED_ROWS = 16
EXPECTED_AXES = {"PHYSICAL_GRID10_PROOF_SCOPE", "MODEL_COGNITION_VS_RUNTIME_PROOF", "STALE_NODE_RESULT_RECOVERY"}
REQUIRED_TYPED_OUTCOMES = {
    "CURRENT",
    "STALE_REJECTED",
    "REBASE_PROVEN",
    "LEASE_REVOKED",
    "GENERATION_CHANGED",
    "SCOPE_CHANGED",
}
AUTHORITY_FORBIDDEN_ACTION_FRAGMENTS = (
    "self-grant",
    "mint canonical",
    "bypass effectgate",
    "relabel the old evidence as current",
)

DEFAULT_SEED = Path(__file__).resolve().parents[1] / (
    "research_entity/global/j-space/research/"
    "2026-08-26_TRIGGER2_V35_RUNTIME_PROOF_STALE_OBSERVATION_HARDNEG_SEED_GPT56SOL.jsonl"
)


class GateError(ValueError):
    pass


def load_rows(path: Path = DEFAULT_SEED) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise GateError(f"line {line_no}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise GateError(f"line {line_no}: row must be object")
            rows.append(row)
    return rows


def _require(row: dict[str, Any], key: str, row_id: str) -> Any:
    if key not in row:
        raise GateError(f"{row_id}: missing {key}")
    return row[key]


def _validate_row(row: dict[str, Any]) -> None:
    row_id = str(_require(row, "row_id", "<unknown>"))
    if row.get("schema") != SCHEMA:
        raise GateError(f"{row_id}: wrong schema")
    if row.get("channel") != CHANNEL:
        raise GateError(f"{row_id}: channel must remain {CHANNEL}")
    if row.get("training_eligible") is not False:
        raise GateError(f"{row_id}: training_eligible must be false")
    if row.get("axis") not in EXPECTED_AXES:
        raise GateError(f"{row_id}: unexpected axis {row.get('axis')!r}")
    if not str(row.get("family_id", "")).strip():
        raise GateError(f"{row_id}: missing family_id")
    if not str(row.get("verdict", "")).strip():
        raise GateError(f"{row_id}: missing verdict")
    if not str(row.get("required_response_class", "")).strip():
        raise GateError(f"{row_id}: missing required_response_class")
    if not str(row.get("forbidden_inference", "")).strip():
        raise GateError(f"{row_id}: missing forbidden_inference")
    if "credit_ceiling" not in row:
        raise GateError(f"{row_id}: missing credit_ceiling")

    action = str(row.get("candidate_action", "")).lower()
    verdict = str(row.get("verdict", ""))
    if any(fragment in action for fragment in AUTHORITY_FORBIDDEN_ACTION_FRAGMENTS):
        if not verdict.startswith("REJECT_"):
            raise GateError(f"{row_id}: authority-creating action must be rejected")

    outcome = row.get("typed_runtime_outcome")
    if outcome is not None and outcome not in REQUIRED_TYPED_OUTCOMES:
        raise GateError(f"{row_id}: unsupported typed runtime outcome {outcome!r}")


def audit_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    if len(rows) != EXPECTED_ROWS:
        raise GateError(f"row count {len(rows)} != {EXPECTED_ROWS}")

    ids = [str(row.get("row_id", "")) for row in rows]
    if len(ids) != len(set(ids)):
        raise GateError("duplicate row_id")

    for row in rows:
        _validate_row(row)

    axis_counts = Counter(str(row["axis"]) for row in rows)
    if axis_counts["PHYSICAL_GRID10_PROOF_SCOPE"] != 6:
        raise GateError("physical proof axis must contain 6 rows")
    if axis_counts["MODEL_COGNITION_VS_RUNTIME_PROOF"] != 2:
        raise GateError("model/runtime separation axis must contain 2 rows")
    if axis_counts["STALE_NODE_RESULT_RECOVERY"] != 8:
        raise GateError("stale recovery axis must contain 8 rows")

    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row["family_id"])].append(row)

    required_paired_families = {
        "SIMULTANEOUS_LIVENESS",
        "PID_HISTORY_VS_OVERLAP",
        "TOPOLOGY_SEMANTICS",
        "STALE_DIGEST",
        "REBASE_AUTHORITY",
    }
    for family in required_paired_families:
        fam_rows = by_family.get(family, [])
        if len(fam_rows) != 2:
            raise GateError(f"{family}: expected exact matched pair")
        verdicts = {str(r["verdict"]) for r in fam_rows}
        if not any(v.startswith("REJECT_") for v in verdicts):
            raise GateError(f"{family}: pair lacks reject control")
        if not any(v.startswith("ACCEPT_") for v in verdicts):
            raise GateError(f"{family}: pair lacks bounded accept control")

    stale_outcomes = {
        str(row.get("typed_runtime_outcome"))
        for row in rows
        if row["axis"] == "STALE_NODE_RESULT_RECOVERY"
    }
    missing = REQUIRED_TYPED_OUTCOMES - stale_outcomes
    if missing:
        raise GateError(f"missing typed stale/recovery outcomes: {sorted(missing)}")

    if any(row.get("training_eligible") is not False for row in rows):
        raise GateError("positive training admission is forbidden")

    return {
        "schema": "CLAY_TRIGGER2_V35_HARDNEG_EVAL_GATE_RESULT/v1",
        "pass": True,
        "rows": len(rows),
        "axis_counts": dict(sorted(axis_counts.items())),
        "families": len(by_family),
        "training_eligible_rows": 0,
        "accepted_dataset_tokens": 0,
        "training_credit": 0,
        "model_runtime_credit": 0,
        "hcu_full_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
        "evidence_scope": "STATIC_EVAL_CORPUS_CONTRACT_ONLY",
    }


def main() -> int:
    try:
        result = audit_rows(load_rows())
    except GateError as exc:
        print(json.dumps({"pass": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
