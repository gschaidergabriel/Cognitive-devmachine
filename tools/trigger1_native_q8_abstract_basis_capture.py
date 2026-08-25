#!/usr/bin/env python3
"""Native Q8 capture for the frozen abstract-state Trigger-1 basis.

This is the source-level replacement for the proxy-heavy basis prompt lane.  It reuses the
pinned Qwen3-0.6B llama.cpp layer-capture mechanism, but sources all 18 model-facing basis
prompts from trigger1_abstract_state_design_v1 after the complete basis/calibration/holdout
design has passed the actual-text leakage audit and canonical factorial producer.

The tool stops at exact native layer-21 calibration activations plus simplex-rank analysis.
It intentionally does not serialize a second target-vector implementation: current
family-energy-balanced geometry/finalization/cvec emitters remain the sole downstream
actuation path.  No holdout model row is executed here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from tools import trigger1_abstract_state_design_v1 as design_v1
from tools import trigger1_native_q8_jspace_basis_build as capture_donor
from tools import trigger1_semantic_simplex_rank_analyze as ranker

SCHEMA = "CLAY_TRIGGER1_QWEN06_Q8_ABSTRACT_BASIS_CAPTURE/v1"


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vector_sha_f32(values: list[float]) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<f4").tobytes()).hexdigest()


def capture(*, output_dir: Path, llama_root: Path, gguf: Path, harness: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    repo_root = Path(__file__).resolve().parents[1]
    source = {
        "repo_head": subprocess.check_output(["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True, timeout=10).strip(),
        "repo_tree": subprocess.check_output(["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"], text=True, timeout=10).strip(),
        "executor_sha256": sha_file(Path(__file__)),
        "capture_donor_sha256": sha_file(Path(capture_donor.__file__)),
        "abstract_design_source_sha256": sha_file(Path(design_v1.__file__)),
        "harness_sha256": sha_file(harness),
    }

    actual_llama = subprocess.check_output(
        ["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    if actual_llama != capture_donor.LLAMA_CPP_COMMIT:
        raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{actual_llama}")
    actual_gguf = sha_file(gguf)
    if actual_gguf != capture_donor.MODEL_GGUF_SHA256:
        raise RuntimeError(f"GGUF_SHA256_MISMATCH:{actual_gguf}")

    frozen = design_v1.build_bundle()
    if frozen.get("text_audit", {}).get("pass") is not True:
        raise RuntimeError("ABSTRACT_DESIGN_TEXT_AUDIT_REQUIRED")
    basis = frozen["basis_design"]
    rows = basis["rows"]

    header, observations = capture_donor.run_capture(
        harness=harness,
        gguf=gguf,
        llama_root=llama_root,
        out=output_dir,
        rows=rows,
    )
    rank_payload = capture_donor.build_rank_payload(rows, observations)
    rank_result = ranker.analyze(rank_payload)
    if rank_result.get("verdict") == "UNRESOLVED":
        raise RuntimeError("ABSTRACT_NATIVE_Q8_SIMPLEX_RANK_UNRESOLVED")

    activation_path = output_dir / "abstract-native-q8-simplex-input.json"
    rank_path = output_dir / "abstract-native-q8-simplex-rank.json"
    activation_path.write_text(
        json.dumps(rank_payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    rank_path.write_text(
        json.dumps(rank_result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    capture_receipts = {
        case_id: {
            "prompt_tokens": int(obs["prompt_tokens"]),
            "primary_l2": float(obs["primary_l2"]),
            "activation_sha256_f32le": vector_sha_f32(obs["primary_activation"]),
        }
        for case_id, obs in sorted(observations.items())
    }
    core = {
        "schema": SCHEMA,
        "status": "PASS_ABSTRACT_NATIVE_Q8_CALIBRATION_CAPTURE_READY_FOR_BOUND_GEOMETRY",
        "started_at": started,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": source,
        "runtime_identity": {
            "gguf_sha256": actual_gguf,
            "llama_cpp_commit": actual_llama,
            "native_capture_harness_sha256": source["harness_sha256"],
        },
        "abstract_design_bundle_sha256": frozen["bundle_sha256"],
        "basis_design_sha256": basis["design_sha256"],
        "text_audit_receipt_sha256": frozen["text_audit"]["audit_receipt_sha256"],
        "calibration_plan_sha256": frozen["calibration_plan"]["plan_sha256"],
        "sealed_holdout_plan_sha256": frozen["holdout_plan"]["plan_sha256"],
        "capture_header": header,
        "capture_receipts": capture_receipts,
        "activation_payload_sha256": canonical_sha(rank_payload),
        "rank_analysis_receipt_sha256": rank_result["analysis_receipt_sha256"],
        "rank_verdict": rank_result["verdict"],
        "model_executed": True,
        "basis_calibration_rows_executed": len(rows),
        "holdout_model_rows_executed": 0,
        "holdout_opened_for_operating_point_selection": False,
        "target_cvec_emitted_here": False,
        "next_geometry_path": [
            "tools/trigger1_native_q8_geometry_balance_v2.py",
            "tools/trigger1_native_q8_family_balanced_cvec_emit.py",
        ],
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Native Q8 calibration capture over the frozen abstract-state basis only. This may support native "
            "carrier-geometry reconstruction after authorized execution, but does not itself establish holdout "
            "causality, semantic J-Space promotion, intervention-scope equivalence, HCU/EntityOS runtime, or training credit."
        ),
    }
    return {**core, "capture_result_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()
    out = Path(args.output_dir).resolve()
    try:
        result = capture(
            output_dir=out,
            llama_root=Path(args.llama_root).resolve(),
            gguf=Path(args.gguf).resolve(),
            harness=Path(args.harness).resolve(),
        )
        code = 0
    except Exception as exc:
        out.mkdir(parents=True, exist_ok=True)
        result = {
            "schema": SCHEMA,
            "status": "BLOCKED_ABSTRACT_NATIVE_Q8_BASIS_CAPTURE",
            "reason": f"{type(exc).__name__}:{str(exc)[:2000]}",
            "model_execution_status": "UNKNOWN_ON_EXCEPTION",
            "holdout_model_execution_status": "NO_HOLDOUT_CALL_IS_ISSUED_BY_THIS_TOOL_BEFORE_OR_AFTER_BASIS_CAPTURE",
            "runtime_credit_minted": False,
            "canonical_semantics_promotion": False,
        }
        result["capture_result_sha256"] = canonical_sha(result)
        code = 3
    (out / "trigger1_native_q8_abstract_basis_capture_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "schema": result["schema"],
        "status": result["status"],
        "capture_result_sha256": result["capture_result_sha256"],
    }, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
