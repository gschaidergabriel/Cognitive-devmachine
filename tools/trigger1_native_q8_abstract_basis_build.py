#!/usr/bin/env python3
"""Build a native Q8_0 layer-20 cvec basis from the hard abstract-state BASIS split.

Unlike trigger1_native_q8_jspace_basis_build.py's current natural-language decision
triplets, this successor consumes a PASSed
CLAY_TRIGGER1_ABSTRACT_STATE_DECONFOUND_RECEIPT/v1 bundle produced from the exact tokenizer.
The model-facing basis therefore has identical lexical/model-token multisets within each
state triplet and no decision/compliance proxy vocabulary.

Only the BASIS split is captured here. CALIBRATION/HOLDOUT stay unopened for gain selection
and the later causal test. The native capture/rank/geometry/cvec machinery is reused rather
than forked.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_abstract_state_deconfound_gate_v1 as deconf
from tools import trigger1_native_q8_jspace_basis_build as native
from tools import trigger1_semantic_simplex_rank_analyze as ranker

SCHEMA = "CLAY_TRIGGER1_NATIVE_Q8_ABSTRACT_STATE_BASIS/v1"


def canonical_sha(value: Any) -> str:
    return native.canonical_sha(value)


def verify_deconfound_receipt(receipt: Any) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != deconf.RECEIPT_SCHEMA or receipt.get("pass") is not True:
        return False
    claimed = receipt.get("receipt_sha256")
    core = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    return isinstance(claimed, str) and claimed == deconf.canonical_sha(core)


def load_bundle(path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(bundle, dict):
        raise ValueError("CASE_BUNDLE_OBJECT_REQUIRED")
    payload = bundle.get("payload")
    receipt = bundle.get("deconfound_receipt")
    if not isinstance(payload, dict) or payload.get("schema") != deconf.SCHEMA:
        raise ValueError("ABSTRACT_STATE_PAYLOAD_INVALID")
    if not verify_deconfound_receipt(receipt):
        raise ValueError("ABSTRACT_STATE_DECONFOUND_RECEIPT_INVALID")
    if receipt.get("input_sha256") != deconf.canonical_sha(payload):
        raise ValueError("ABSTRACT_STATE_RECEIPT_INPUT_BINDING_MISMATCH")
    basis = payload.get("partitions", {}).get("BASIS")
    if not isinstance(basis, list) or len(basis) != 18:
        raise ValueError("EXACT_SIX_BASIS_TRIPLETS_REQUIRED")
    rows: list[dict[str, Any]] = []
    for row in basis:
        rows.append(
            {
                "row_id": row["row_id"],
                "family_group_id": row["family_id"],
                "semantic_class": row["semantic_target"],
                "prompt": row["prompt"],
                "prompt_sha256": row["prompt_sha256"],
                "content_text_sha256": hashlib.sha256(row["content_text"].encode("utf-8")).hexdigest(),
                "content_token_ids_sha256": deconf.canonical_sha(row["content_token_ids"]),
            }
        )
    if {r["semantic_class"] for r in rows} != set(native.CLASSES):
        raise ValueError("BASIS_TARGET_UNIVERSE_INVALID")
    return payload, receipt, rows


def run(args: argparse.Namespace) -> dict[str, Any]:
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    llama_root = Path(args.llama_root).resolve()
    gguf = Path(args.gguf).resolve()
    harness = Path(args.harness).resolve()
    bundle_path = Path(args.case_bundle).resolve()
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    actual_llama = subprocess.check_output(["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if actual_llama != native.LLAMA_CPP_COMMIT:
        raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{actual_llama}")
    actual_gguf = native.sha_file(gguf)
    if actual_gguf != native.MODEL_GGUF_SHA256:
        raise RuntimeError(f"GGUF_SHA256_MISMATCH:{actual_gguf}")

    payload, deconf_receipt, rows = load_bundle(bundle_path)
    design = {
        "schema": "CLAY_TRIGGER1_NATIVE_Q8_ABSTRACT_MATCHED_TRIPLETS/v1",
        "case_bundle_sha256": native.sha_file(bundle_path),
        "deconfound_receipt_sha256": deconf_receipt["receipt_sha256"],
        "tokenizer_json_sha256": payload["tokenizer_identity"]["tokenizer_json_sha256"],
        "basis_rows": rows,
        "matched_family_count": len({r["family_group_id"] for r in rows}),
        "capture_layer_inp": native.NATIVE_STATE_LAYER_INP,
        "corresponding_cvec_injection_layer": native.INJECTION_LAYER,
        "calibration_opened": False,
        "holdout_opened": False,
    }
    design["design_sha256"] = canonical_sha(design)
    (out / "native-q8-abstract-basis-design.json").write_text(json.dumps(design, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    header, observations = native.run_capture(harness=harness, gguf=gguf, llama_root=llama_root, out=out, rows=rows)
    rank_payload = native.build_rank_payload(rows, observations)
    (out / "native-q8-abstract-simplex-input.json").write_text(json.dumps(rank_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rank_result = ranker.analyze(rank_payload)
    (out / "native-q8-abstract-simplex-rank.json").write_text(json.dumps(rank_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if rank_result.get("verdict") == "UNRESOLVED":
        raise RuntimeError("ABSTRACT_NATIVE_Q8_SIMPLEX_RANK_UNRESOLVED")

    geometry = native.native_geometry(rows, observations, rank_result)
    cvec_dir = out / "native-q8-abstract-cvec-basis"
    cvec_dir.mkdir(parents=True, exist_ok=True)
    target_receipts = {
        name: native.write_cvec(cvec_dir / f"target-{name.lower()}.cvec.f32le", geometry["geometry_vectors"][name])
        for name in native.CLASSES
    }
    axis_receipts = {"H1": native.write_cvec(cvec_dir / "axis-h1.cvec.f32le", geometry["axis_h1"])}
    if geometry["axis_h2"] is not None:
        axis_receipts["H2"] = native.write_cvec(cvec_dir / "axis-h2.cvec.f32le", geometry["axis_h2"])

    basis_packet = {
        "schema": "JSPACE_NATIVE_Q8_ABSTRACT_STATE_BASIS/v1",
        "carrier": "Qwen/Qwen3-0.6B-GGUF:Q8_0",
        "gguf_sha256": actual_gguf,
        "llama_cpp_commit": actual_llama,
        "source_design_sha256": design["design_sha256"],
        "deconfound_receipt_sha256": deconf_receipt["receipt_sha256"],
        "rank_analysis_receipt_sha256": rank_result["analysis_receipt_sha256"],
        "dimension": native.N_EMBD,
        "injection_layer": native.INJECTION_LAYER,
        "native_state_layer_inp": native.NATIVE_STATE_LAYER_INP,
        "rank": geometry["rank"],
        "rank_verdict": geometry["rank_verdict"],
        "basis_semantics": "lexically/token-counterbalanced structural ternary relation state",
        "axis_h1_sha256_f32le": native.vector_sha_f32(geometry["axis_h1"]),
        "axis_h2_sha256_f32le": native.vector_sha_f32(geometry["axis_h2"]) if geometry["axis_h2"] is not None else None,
        "target_vectors": {
            name: {
                "vector_sha256_f32le": native.vector_sha_f32(geometry["geometry_vectors"][name]),
                "vector_l2": float(np.linalg.norm(geometry["geometry_vectors"][name])),
                "coordinates": geometry["semantic_coordinates"][name],
            }
            for name in native.CLASSES
        },
        "target_cvec_receipts": target_receipts,
        "axis_cvec_receipts": axis_receipts,
        "calibration_opened": False,
        "holdout_opened": False,
        "intervention_executed": False,
        "canonical_credit_minted": False,
    }
    basis_packet["basis_packet_sha256"] = canonical_sha(basis_packet)
    (out / "native-q8-abstract-jspace-basis.json").write_text(json.dumps(basis_packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    core = {
        "schema": SCHEMA,
        "status": "PASS_ABSTRACT_NATIVE_Q8_BASIS_READY_FOR_CALIBRATION",
        "started_at": started,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "case_bundle_sha256": native.sha_file(bundle_path),
        "design_sha256": design["design_sha256"],
        "deconfound_receipt_sha256": deconf_receipt["receipt_sha256"],
        "capture_header": header,
        "rank_analysis_receipt_sha256": rank_result["analysis_receipt_sha256"],
        "basis_packet_sha256": basis_packet["basis_packet_sha256"],
        "calibration_opened": False,
        "holdout_opened": False,
        "intervention_executed": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": "Native Q8 calibration-basis reconstruction from the hard abstract-state design only; no calibration gain selection or holdout intervention is performed here.",
    }
    return {**core, "result_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case-bundle", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "trigger1_native_q8_abstract_basis_result.json"
    try:
        result = run(args)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"schema": SCHEMA, "status": result["status"], "result_sha256": result["result_sha256"]}, sort_keys=True))
        return 0
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_ABSTRACT_NATIVE_Q8_BASIS_BUILD",
            "reason": f"{type(exc).__name__}:{str(exc)[:2000]}",
            "calibration_opened": False,
            "holdout_opened": False,
            "intervention_executed": False,
            "runtime_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "canonical_semantics_promotion": False,
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"schema": SCHEMA, "status": blocked["status"], "reason": blocked["reason"]}, sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
