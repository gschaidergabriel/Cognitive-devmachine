#!/usr/bin/env python3
"""Evidence-bound successor for native-Q8 family-energy-balanced geometry.

The v1 geometry finalizer solves a real metrology problem (high-energy family domination),
but its public API accepts an externally supplied rank verdict/receipt. v2 removes any
possibility of composing a rank result from activation universe A with geometry payload B:
it deterministically recomputes the canonical simplex-rank analysis from the exact same
payload, requires byte-for-byte-equivalent structured rank evidence, and only then calls
the existing v1 geometry implementation.

No model is executed, no gain is selected, no holdout is opened and no runtime/J-Space/
HCU/EntityOS/training/canonical-semantic credit is minted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools import trigger1_native_q8_geometry_balance as v1
from tools import trigger1_semantic_simplex_rank_analyze as rank_analyzer

SCHEMA = "CLAY_TRIGGER1_NATIVE_Q8_FAMILY_ENERGY_BALANCED_GEOMETRY/v2"


class GeometryBindingError(ValueError):
    pass


def _recompute_and_bind(payload: dict[str, Any], declared_rank: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(declared_rank, dict):
        raise GeometryBindingError("DECLARED_RANK_RESULT_OBJECT_REQUIRED")
    if declared_rank.get("schema") != rank_analyzer.OUTPUT_SCHEMA:
        raise GeometryBindingError("DECLARED_RANK_RESULT_SCHEMA_INVALID")

    payload_sha = rank_analyzer.canonical_sha(payload)
    if declared_rank.get("input_sha256") != payload_sha:
        raise GeometryBindingError("RANK_RESULT_INPUT_PAYLOAD_SHA256_MISMATCH")

    declared_receipt = declared_rank.get("analysis_receipt_sha256")
    if not isinstance(declared_receipt, str) or len(declared_receipt) != 64:
        raise GeometryBindingError("RANK_ANALYSIS_RECEIPT_SHA256_REQUIRED")
    declared_core = dict(declared_rank)
    declared_core.pop("analysis_receipt_sha256", None)
    if rank_analyzer.canonical_sha(declared_core) != declared_receipt:
        raise GeometryBindingError("RANK_ANALYSIS_RECEIPT_RECONSTRUCTION_MISMATCH")

    recomputed = rank_analyzer.analyze(payload)
    if declared_rank != recomputed:
        raise GeometryBindingError("DECLARED_RANK_RESULT_DIFFERS_FROM_EXACT_RECOMPUTATION")
    return recomputed


def finalize(payload: dict[str, Any], declared_rank: dict[str, Any]) -> dict[str, Any]:
    recomputed = _recompute_and_bind(payload, declared_rank)
    geometry = v1.finalize(payload, recomputed)
    core = {
        **geometry,
        "schema": SCHEMA,
        "rank_binding": {
            "exact_payload_sha256": recomputed["input_sha256"],
            "recomputed_rank_analysis_receipt_sha256": recomputed["analysis_receipt_sha256"],
            "declared_equals_recomputed": True,
            "same_activation_universe_required": True,
        },
        "evidence_boundary": (
            "v2 recomputes the canonical rank analysis from the exact geometry payload before "
            "delegating to the v1 family-energy-balanced geometry statistic. This closes rank/geometry "
            "universe drift but remains calibration representation metrology only; it does not establish "
            "causal steerability, runtime authenticity, canonical semantics, or broader system credit."
        ),
    }
    core.pop("geometry_receipt_sha256", None)
    return {**core, "geometry_receipt_sha256": v1.canonical_sha(core)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--rank-result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rank_result = json.loads(Path(args.rank_result).read_text(encoding="utf-8"))
    result = finalize(payload, rank_result)
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
