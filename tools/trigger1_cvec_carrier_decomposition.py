#!/usr/bin/env python3
"""Evaluate native cvec carrier-position decomposition without claiming causal identity.

The evaluator expects repeated observations for the same semantic case under six native
llama.cpp position modes:

  BASELINE_FULL, BASELINE_SPLIT,
  BROADCAST_FULL, BROADCAST_SPLIT,
  LAST_TOKEN_ONLY_SPLIT, PREFIX_ONLY_SPLIT.

It separates cvec effects from batch-schedule drift and reports a paired decomposition.
It is deliberately non-promoting: source or metric output cannot mint J-Space semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER1_CVEC_CARRIER_DECOMPOSITION/v1"
OBS_SCHEMA = "CLAY_LLAMA_CPP_CVEC_CARRIER_OBSERVATION/v1"
REQUIRED_MODES = (
    "BASELINE_FULL",
    "BASELINE_SPLIT",
    "BROADCAST_FULL",
    "BROADCAST_SPLIT",
    "LAST_TOKEN_ONLY_SPLIT",
    "PREFIX_ONLY_SPLIT",
)
CODES = ("A", "B", "C")


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _margin(logits: dict[str, Any], code: str) -> float:
    if code not in CODES:
        raise ValueError(f"OUTPUT_CODE_INVALID:{code}")
    vals = {c: float(logits[c]) for c in CODES}
    other = [c for c in CODES if c != code]
    return vals[code] - 0.5 * (vals[other[0]] + vals[other[1]])


def _finite(x: float, name: str) -> float:
    if not math.isfinite(x):
        raise ValueError(f"NONFINITE:{name}")
    return x


def evaluate(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    metadata: dict[str, dict[str, str]] = {}
    failures: list[str] = []

    for index, row in enumerate(records):
        if not isinstance(row, dict) or row.get("schema") != OBS_SCHEMA:
            failures.append(f"ROW_{index}_SCHEMA_INVALID")
            continue
        cid = str(row.get("case_id") or "")
        mode = str(row.get("position_mode") or "")
        code = str(row.get("output_code_identity") or "").upper()
        target = str(row.get("semantic_target") or "").upper()
        if not cid or mode not in REQUIRED_MODES or code not in CODES:
            failures.append(f"ROW_{index}_IDENTITY_INVALID")
            continue
        if mode in grouped[cid]:
            failures.append(f"DUPLICATE_CASE_MODE:{cid}:{mode}")
            continue
        logits = row.get("token_logits")
        if not isinstance(logits, dict) or any(c not in logits for c in CODES):
            failures.append(f"ROW_{index}_LOGITS_INVALID")
            continue
        grouped[cid][mode] = row
        prior = metadata.setdefault(cid, {"output_code_identity": code, "semantic_target": target})
        if prior != {"output_code_identity": code, "semantic_target": target}:
            failures.append(f"CASE_METADATA_DRIFT:{cid}")

    cases: list[dict[str, Any]] = []
    for cid in sorted(grouped):
        rows = grouped[cid]
        missing = [m for m in REQUIRED_MODES if m not in rows]
        if missing:
            failures.append(f"CASE_MISSING_MODES:{cid}:{','.join(missing)}")
            continue
        code = metadata[cid]["output_code_identity"]
        target = metadata[cid]["semantic_target"]
        margins = {m: _finite(_margin(rows[m]["token_logits"], code), f"{cid}:{m}") for m in REQUIRED_MODES}
        base_full = margins["BASELINE_FULL"]
        base_split = margins["BASELINE_SPLIT"]
        all_full = margins["BROADCAST_FULL"]
        all_split = margins["BROADCAST_SPLIT"]
        last = margins["LAST_TOKEN_ONLY_SPLIT"]
        prefix = margins["PREFIX_ONLY_SPLIT"]
        deltas = {
            "batch_baseline_drift": base_split - base_full,
            "batch_broadcast_drift": all_split - all_full,
            "broadcast_full_vs_baseline_full": all_full - base_full,
            "broadcast_split_vs_baseline_split": all_split - base_split,
            "last_only_vs_baseline_split": last - base_split,
            "prefix_only_vs_baseline_split": prefix - base_split,
        }
        deltas["split_nonadditive_interaction"] = (
            deltas["broadcast_split_vs_baseline_split"]
            - deltas["last_only_vs_baseline_split"]
            - deltas["prefix_only_vs_baseline_split"]
        )
        broadcast = deltas["broadcast_split_vs_baseline_split"]
        last_delta = deltas["last_only_vs_baseline_split"]
        cases.append(
            {
                "case_id": cid,
                "semantic_target": target,
                "output_code_identity": code,
                "margins": margins,
                "deltas": deltas,
                "broadcast_last_sign_concordant": (broadcast == 0.0 and last_delta == 0.0) or (broadcast * last_delta > 0.0),
                "last_effect_exceeds_same_case_baseline_schedule_drift": abs(last_delta) > abs(deltas["batch_baseline_drift"]),
            }
        )

    def mean(key: str) -> float | None:
        vals = [float(c["deltas"][key]) for c in cases]
        return None if not vals else float(sum(vals) / len(vals))

    summary = {
        "case_count": len(cases),
        "mean_deltas": {k: mean(k) for k in (
            "batch_baseline_drift",
            "batch_broadcast_drift",
            "broadcast_full_vs_baseline_full",
            "broadcast_split_vs_baseline_split",
            "last_only_vs_baseline_split",
            "prefix_only_vs_baseline_split",
            "split_nonadditive_interaction",
        )},
        "broadcast_last_sign_concordance_rate": None if not cases else sum(bool(c["broadcast_last_sign_concordant"]) for c in cases) / len(cases),
        "last_effect_gt_batch_drift_rate": None if not cases else sum(bool(c["last_effect_exceeds_same_case_baseline_schedule_drift"]) for c in cases) / len(cases),
    }
    out = {
        "schema": SCHEMA,
        "status": "PASS_STRUCTURAL_EVALUATION" if not failures and cases else "INVALID_OR_INCOMPLETE",
        "required_modes": list(REQUIRED_MODES),
        "failures": failures,
        "cases": cases,
        "summary": summary,
        "claim_boundary": {
            "causal_identity_between_broadcast_and_last_token": False,
            "carrier_robustness_can_be_assessed": bool(cases) and not failures,
            "canonical_jspace_semantics_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "hcu_runtime_credit_minted": False,
            "training_credit_minted": False,
        },
    }
    out["result_sha256"] = _canonical_sha(out)
    return out


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSONL_PARSE_ERROR:{line_no}:{exc}") from exc
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-jsonl", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    result = evaluate(load_jsonl(Path(args.input_jsonl)))
    text = json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["status"] == "PASS_STRUCTURAL_EVALUATION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
