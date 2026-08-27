#!/usr/bin/env python3
"""Calibration-only Q8-native J-Space basis reconstruction for Trigger-1.

This tool closes the largest remaining carrier-geometry gap in the Qwen3-0.6B lane:
it derives the semantic basis from the *pinned Q8_0 llama.cpp target runtime itself*, not
from a full-precision PyTorch vector imported into the native carrier.

It performs no holdout intervention and mints no runtime/promotion credit. It:
  1. runs 6 matched semantic scenario triplets through the native layer-capture harness;
  2. extracts last-prompt-token layer-21 inputs (the exact state immediately after a
     cvec at Qwen3 layer 20, per the pinned llama.cpp graph semantics);
  3. submits the 18 calibration activations to the deterministic blocked simplex-rank
     analyzer;
  4. resolves a 1D or 2D native semantic subspace only when that analyzer passes; and
  5. emits geometry-preserving target vectors and llama.cpp cvec F32LE payloads for
     AFFIRMATIVE / NEGATIVE / NEUTRAL using one shared scale.

The model-facing prompts contain no A/B/C output-code identities and do not contain the
metadata class names AFFIRMATIVE/NEGATIVE/NEUTRAL. Those class names exist only in the
experiment design metadata used after activation capture.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_semantic_simplex_rank_analyze as ranker

SCHEMA = "CLAY_TRIGGER1_QWEN06_Q8_NATIVE_JSPACE_BASIS/v1"
CAPTURE_HEADER = "CLAY_LLAMA_CPP_LAYER_CAPTURE_HEADER/v1"
CAPTURE_ROW = "CLAY_LLAMA_CPP_LAYER_CAPTURE_OBSERVATION/v1"
MODEL_GGUF_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
LLAMA_CPP_COMMIT = "bb4caa7540188872173c44d161602d9271386413"
N_EMBD = 1024
N_LAYER = 28
INJECTION_LAYER = 20
NATIVE_STATE_LAYER_INP = 21
DEFAULT_DOWNSTREAM_LAYER_INP = 24
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")

# Six families are intentional: exact 2^6 sign-flip inference can reach alpha=.05.
# Within each family, wording keeps the same situation while changing only the requested
# decision relation as far as practical. Metadata class labels are not in model-facing text.
MATCHED_TRIPLETS: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "proposal",
        {
            "AFFIRMATIVE": "/no_think\nA committee is considering one proposal. Internally represent the committee granting it and supporting proceeding. Do not answer with a code or class label.",
            "NEGATIVE": "/no_think\nA committee is considering one proposal. Internally represent the committee refusing it and opposing proceeding. Do not answer with a code or class label.",
            "NEUTRAL": "/no_think\nA committee is considering one proposal. Internally represent the committee withholding a decision and neither supporting nor opposing proceeding. Do not answer with a code or class label.",
        },
    ),
    (
        "permission",
        {
            "AFFIRMATIVE": "/no_think\nA person requests permission for one action. Internally represent permission being granted and the action being allowed. Do not answer with a code or class label.",
            "NEGATIVE": "/no_think\nA person requests permission for one action. Internally represent permission being refused and the action being disallowed. Do not answer with a code or class label.",
            "NEUTRAL": "/no_think\nA person requests permission for one action. Internally represent the permission decision being deferred with no grant or refusal yet. Do not answer with a code or class label.",
        },
    ),
    (
        "recommendation",
        {
            "AFFIRMATIVE": "/no_think\nA reviewer evaluates one recommendation. Internally represent endorsing the recommendation and favoring adoption. Do not answer with a code or class label.",
            "NEGATIVE": "/no_think\nA reviewer evaluates one recommendation. Internally represent rejecting the recommendation and opposing adoption. Do not answer with a code or class label.",
            "NEUTRAL": "/no_think\nA reviewer evaluates one recommendation. Internally represent reserving judgment and neither favoring nor opposing adoption. Do not answer with a code or class label.",
        },
    ),
    (
        "invitation",
        {
            "AFFIRMATIVE": "/no_think\nA recipient considers one invitation. Internally represent accepting the invitation and intending to attend. Do not answer with a code or class label.",
            "NEGATIVE": "/no_think\nA recipient considers one invitation. Internally represent declining the invitation and intending not to attend. Do not answer with a code or class label.",
            "NEUTRAL": "/no_think\nA recipient considers one invitation. Internally represent leaving the invitation undecided with no commitment either way. Do not answer with a code or class label.",
        },
    ),
    (
        "candidate",
        {
            "AFFIRMATIVE": "/no_think\nA panel reviews one candidate. Internally represent selecting the candidate and supporting the selection. Do not answer with a code or class label.",
            "NEGATIVE": "/no_think\nA panel reviews one candidate. Internally represent not selecting the candidate and opposing the selection. Do not answer with a code or class label.",
            "NEUTRAL": "/no_think\nA panel reviews one candidate. Internally represent leaving the selection unresolved and taking neither side. Do not answer with a code or class label.",
        },
    ),
    (
        "change_request",
        {
            "AFFIRMATIVE": "/no_think\nA team evaluates one change request. Internally represent approving the change and choosing to apply it. Do not answer with a code or class label.",
            "NEGATIVE": "/no_think\nA team evaluates one change request. Internally represent rejecting the change and choosing not to apply it. Do not answer with a code or class label.",
            "NEUTRAL": "/no_think\nA team evaluates one change request. Internally represent postponing the decision with neither approval nor rejection. Do not answer with a code or class label.",
        },
    ),
)

DECISION_CONFIG = {
    "alpha": 0.05,
    "rank1_equivalence_max_ratio": 0.10,
    "rank2_min_ratio": 0.25,
    "rank2_min_lofo_cosine": 0.90,
    "min_matched_families": 6,
    "max_exact_signflip_families": 16,
    "monte_carlo_signflips": 4096,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vector_sha_f32(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype="<f4").tobytes()).hexdigest()


def unit(vector: np.ndarray, *, name: str) -> np.ndarray:
    n = float(np.linalg.norm(vector))
    if not math.isfinite(n) or n <= 1e-12:
        raise RuntimeError(f"{name}_DEGENERATE")
    return vector / n


def cvec_bytes(vector: np.ndarray, injection_layer: int = INJECTION_LAYER) -> bytes:
    values = np.asarray(vector, dtype="<f4")
    if values.shape != (N_EMBD,):
        raise RuntimeError(f"VECTOR_DIMENSION_MISMATCH:{values.shape}")
    chunk = values.tobytes(order="C")
    zero = b"\x00" * (4 * N_EMBD)
    raw = b"".join(chunk if il == injection_layer else zero for il in range(1, N_LAYER))
    expected = (N_LAYER - 1) * N_EMBD * 4
    if len(raw) != expected:
        raise AssertionError("CVEC_BUFFER_LENGTH_INVARIANT")
    return raw


def write_cvec(path: Path, vector: np.ndarray) -> dict[str, Any]:
    raw = cvec_bytes(vector)
    path.write_bytes(raw)
    return {
        "path": str(path),
        "vector_sha256_f32le": vector_sha_f32(vector),
        "vector_l2": float(np.linalg.norm(vector)),
        "cvec_sha256": hashlib.sha256(raw).hexdigest(),
        "cvec_bytes": len(raw),
        "cvec_float_count": len(raw) // 4,
        "injection_layer": INJECTION_LAYER,
    }


def design_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id, prompts in MATCHED_TRIPLETS:
        for semantic_class in CLASSES:
            prompt = prompts[semantic_class]
            rows.append({
                "row_id": f"{family_id}:{semantic_class.lower()}",
                "family_group_id": family_id,
                "semantic_class": semantic_class,
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            })
    return rows


def run_capture(
    *, harness: Path, gguf: Path, llama_root: Path, out: Path, rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    tsv = out / "native-q8-basis-capture.tsv"
    lines = []
    for row in rows:
        lines.append("\t".join([
            row["row_id"],
            "-",
            str(INJECTION_LAYER),
            str(INJECTION_LAYER),
            str(NATIVE_STATE_LAYER_INP),
            "-1",
            row["prompt"].encode("utf-8").hex(),
        ]))
    tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")

    env = dict(os.environ)
    lib = str(llama_root / "build" / "bin")
    env["LD_LIBRARY_PATH"] = lib + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    p = subprocess.run(
        [str(harness), str(gguf), str(tsv), str(N_EMBD), str(N_LAYER)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=1800,
        check=False,
    )
    (out / "native-q8-basis-capture.stdout.jsonl").write_text(p.stdout, encoding="utf-8")
    (out / "native-q8-basis-capture.stderr.txt").write_text(p.stderr, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"NATIVE_LAYER_CAPTURE_FAILED:{p.returncode}:{p.stderr[-2000:]}")

    parsed = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    if not parsed or parsed[0].get("schema") != CAPTURE_HEADER:
        raise RuntimeError("NATIVE_LAYER_CAPTURE_HEADER_MISSING")
    header = parsed[0]
    observations: dict[str, dict[str, Any]] = {}
    for item in parsed[1:]:
        if item.get("schema") != CAPTURE_ROW:
            raise RuntimeError(f"NATIVE_LAYER_CAPTURE_OBSERVATION_INVALID:{item.get('schema')}")
        cid = str(item.get("case_id") or "")
        if not cid or cid in observations:
            raise RuntimeError(f"NATIVE_LAYER_CAPTURE_CASE_ID_INVALID:{cid}")
        if item.get("cvec_applied") is not False:
            raise RuntimeError(f"BASIS_CAPTURE_MUST_BE_UNINTERVENED:{cid}")
        if int(item.get("primary_layer_inp", -1)) != NATIVE_STATE_LAYER_INP:
            raise RuntimeError(f"BASIS_CAPTURE_WRONG_LAYER:{cid}")
        act = item.get("primary_activation")
        if not isinstance(act, list) or len(act) != N_EMBD:
            raise RuntimeError(f"BASIS_CAPTURE_DIMENSION_INVALID:{cid}")
        arr = np.asarray(act, dtype=np.float64)
        if not np.all(np.isfinite(arr)):
            raise RuntimeError(f"BASIS_CAPTURE_NONFINITE:{cid}")
        observations[cid] = item
    expected = {row["row_id"] for row in rows}
    if set(observations) != expected:
        raise RuntimeError(f"BASIS_CAPTURE_CASE_UNIVERSE_MISMATCH:{len(observations)}:{len(expected)}")
    return header, observations


def build_rank_payload(rows: list[dict[str, Any]], observations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": ranker.INPUT_SCHEMA,
        "dimension": N_EMBD,
        "decision_config": dict(DECISION_CONFIG),
        "rows": [
            {
                "row_id": row["row_id"],
                "family_group_id": row["family_group_id"],
                "semantic_class": row["semantic_class"],
                "activation": observations[row["row_id"]]["primary_activation"],
            }
            for row in rows
        ],
    }


def native_geometry(
    rows: list[dict[str, Any]], observations: dict[str, dict[str, Any]], rank_result: dict[str, Any]
) -> dict[str, Any]:
    grouped: dict[str, dict[str, np.ndarray]] = {}
    for row in rows:
        grouped.setdefault(row["family_group_id"], {})[row["semantic_class"]] = np.asarray(
            observations[row["row_id"]]["primary_activation"], dtype=np.float64
        )
    families = sorted(grouped)

    # Equal-weighted within-family centering removes a family-shared activation offset.
    centered: dict[str, list[np.ndarray]] = {name: [] for name in CLASSES}
    h1_family: list[np.ndarray] = []
    d2_family: list[np.ndarray] = []
    for family in families:
        a = grouped[family]["AFFIRMATIVE"]
        n = grouped[family]["NEGATIVE"]
        u = grouped[family]["NEUTRAL"]
        grand = (a + n + u) / 3.0
        centered["AFFIRMATIVE"].append(a - grand)
        centered["NEGATIVE"].append(n - grand)
        centered["NEUTRAL"].append(u - grand)
        h1_family.append(a - 0.5 * (n + u))
        d2_family.append(n - u)

    h1 = np.mean(np.stack(h1_family, axis=0), axis=0)
    axis1 = unit(h1, name="NATIVE_H1")
    d2 = np.mean(np.stack(d2_family, axis=0), axis=0)
    h2 = d2 - float(np.dot(d2, axis1)) * axis1

    verdict = str(rank_result.get("verdict") or "")
    if verdict == "TWO_DIMENSIONAL_REQUIRED":
        axis2 = unit(h2, name="NATIVE_H2")
        axes = np.stack([axis1, axis2], axis=0)
    elif verdict == "ONE_DIMENSIONAL_SUPPORTED":
        axis2 = None
        axes = np.stack([axis1], axis=0)
    else:
        raise RuntimeError(f"NATIVE_SIMPLEX_RANK_UNRESOLVED:{verdict}")

    centroids = {name: np.mean(np.stack(centered[name], axis=0), axis=0) for name in CLASSES}
    projected: dict[str, np.ndarray] = {}
    coordinates: dict[str, list[float]] = {}
    for name in CLASSES:
        coords = axes @ centroids[name]
        vec = coords @ axes
        projected[name] = np.asarray(vec, dtype=np.float64)
        coordinates[name] = [float(v) for v in coords]

    norms = [float(np.linalg.norm(projected[name])) for name in CLASSES]
    nonzero = [v for v in norms if v > 1e-12]
    if len(nonzero) < 2:
        raise RuntimeError("NATIVE_TARGET_GEOMETRY_DEGENERATE")
    shared_scale = float(sum(nonzero) / len(nonzero))
    geometry_vectors = {name: projected[name] / shared_scale for name in CLASSES}

    # Preserve the zero-sum simplex invariant after floating-point reconstruction.
    mean_vec = sum(geometry_vectors.values()) / 3.0
    geometry_vectors = {name: vec - mean_vec for name, vec in geometry_vectors.items()}

    return {
        "rank": 2 if verdict == "TWO_DIMENSIONAL_REQUIRED" else 1,
        "rank_verdict": verdict,
        "families": families,
        "axis_h1": axis1,
        "axis_h2": axis2,
        "axes": axes,
        "semantic_coordinates": coordinates,
        "centered_projected_vectors": projected,
        "shared_geometry_scale": shared_scale,
        "geometry_vectors": geometry_vectors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    llama_root = Path(args.llama_root).resolve()
    gguf = Path(args.gguf).resolve()
    harness = Path(args.harness).resolve()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result_path = out / "trigger1_native_q8_jspace_basis_result.json"

    source = {
        "repo_head": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=10).strip(),
        "repo_tree": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"], text=True, timeout=10).strip(),
        "executor_sha256": sha_file(Path(__file__)),
        "harness_sha256": sha_file(harness),
    }

    try:
        actual_llama = subprocess.check_output(["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10).strip()
        if actual_llama != LLAMA_CPP_COMMIT:
            raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{actual_llama}")
        actual_gguf = sha_file(gguf)
        if actual_gguf != MODEL_GGUF_SHA256:
            raise RuntimeError(f"GGUF_SHA256_MISMATCH:{actual_gguf}")

        rows = design_rows()
        prompt_text = "\n".join(row["prompt"] for row in rows).upper()
        for forbidden in ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL", " A=", " B=", " C=", "CODEBOOK"):
            if forbidden in prompt_text:
                raise RuntimeError(f"MODEL_FACING_LABEL_OR_CODE_IDENTITY_LEAK:{forbidden}")

        design = {
            "schema": "CLAY_TRIGGER1_NATIVE_Q8_MATCHED_SEMANTIC_TRIPLETS/v1",
            "matched_family_count": len(MATCHED_TRIPLETS),
            "rows": rows,
            "model_facing_metadata_class_names_absent": True,
            "model_facing_output_code_identities_absent": True,
            "capture_layer_inp": NATIVE_STATE_LAYER_INP,
            "corresponding_cvec_injection_layer": INJECTION_LAYER,
        }
        design["design_sha256"] = canonical_sha(design)
        (out / "native-q8-basis-design.json").write_text(json.dumps(design, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

        header, observations = run_capture(harness=harness, gguf=gguf, llama_root=llama_root, out=out, rows=rows)
        rank_payload = build_rank_payload(rows, observations)
        (out / "native-q8-simplex-input.json").write_text(json.dumps(rank_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        rank_result = ranker.analyze(rank_payload)
        (out / "native-q8-simplex-rank.json").write_text(json.dumps(rank_result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

        if rank_result.get("verdict") == "UNRESOLVED":
            raise RuntimeError("NATIVE_Q8_SIMPLEX_RANK_UNRESOLVED")

        geometry = native_geometry(rows, observations, rank_result)
        cvec_dir = out / "native-q8-cvec-basis"
        cvec_dir.mkdir(parents=True, exist_ok=True)
        axis_receipts = {
            "H1": write_cvec(cvec_dir / "axis-h1.cvec.f32le", geometry["axis_h1"]),
        }
        if geometry["axis_h2"] is not None:
            axis_receipts["H2"] = write_cvec(cvec_dir / "axis-h2.cvec.f32le", geometry["axis_h2"])
        target_receipts = {
            name: write_cvec(cvec_dir / f"target-{name.lower()}.cvec.f32le", geometry["geometry_vectors"][name])
            for name in CLASSES
        }

        basis_packet = {
            "schema": "JSPACE_NATIVE_Q8_SEMANTIC_BASIS/v1",
            "carrier": "Qwen/Qwen3-0.6B-GGUF:Q8_0",
            "gguf_sha256": actual_gguf,
            "llama_cpp_commit": actual_llama,
            "native_capture_harness_sha256": source["harness_sha256"],
            "source_design_sha256": design["design_sha256"],
            "rank_analysis_receipt_sha256": rank_result["analysis_receipt_sha256"],
            "dimension": N_EMBD,
            "injection_layer": INJECTION_LAYER,
            "native_state_layer_inp": NATIVE_STATE_LAYER_INP,
            "rank": geometry["rank"],
            "rank_verdict": geometry["rank_verdict"],
            "basis_semantics": "equal-family matched-triplet within-family-centered native Q8_0 layer-input semantic geometry",
            "axis_h1_sha256_f32le": vector_sha_f32(geometry["axis_h1"]),
            "axis_h2_sha256_f32le": vector_sha_f32(geometry["axis_h2"]) if geometry["axis_h2"] is not None else None,
            "semantic_coordinates": geometry["semantic_coordinates"],
            "shared_geometry_scale": geometry["shared_geometry_scale"],
            "target_vectors": {
                name: {
                    "vector_sha256_f32le": vector_sha_f32(geometry["geometry_vectors"][name]),
                    "vector_l2": float(np.linalg.norm(geometry["geometry_vectors"][name])),
                    "coordinates": geometry["semantic_coordinates"][name],
                }
                for name in CLASSES
            },
            "zero_sum_target_vector_residual_l2": float(np.linalg.norm(sum(geometry["geometry_vectors"].values()))),
            "common_gain_required_for_actuation": True,
            "gain_selected_here": False,
            "holdout_opened": False,
            "intervention_executed": False,
        }
        basis_packet["basis_packet_sha256"] = canonical_sha(basis_packet)
        (out / "native-q8-jspace-basis.json").write_text(json.dumps(basis_packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

        capture_receipts = {
            cid: {
                "prompt_tokens": int(obs["prompt_tokens"]),
                "primary_l2": float(obs["primary_l2"]),
                "activation_sha256_f32le": vector_sha_f32(np.asarray(obs["primary_activation"], dtype=np.float64)),
            }
            for cid, obs in sorted(observations.items())
        }
        result = {
            "schema": SCHEMA,
            "status": "PASS_NATIVE_Q8_BASIS_READY_FOR_CALIBRATION",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "runtime_identity": {
                "gguf_sha256": actual_gguf,
                "llama_cpp_commit": actual_llama,
                "execution_provider": "local",
                "external_llm_provider_credentials_required": False,
            },
            "capture_header": header,
            "capture_receipts": capture_receipts,
            "design_sha256": design["design_sha256"],
            "rank_analysis": rank_result,
            "basis_packet": basis_packet,
            "axis_cvec_receipts": axis_receipts,
            "target_cvec_receipts": target_receipts,
            "next_gate": "calibration-only common gain and native-carrier geometry controls, then only an admitted fresh holdout intervention may test target-specific causal matrix + downstream transport + dual readout",
            "evidence_boundary": "Calibration-only native target-carrier basis reconstruction. This does not execute a holdout intervention and mints no canonical semantics, J-Space model-runtime, HCU, EntityOS, training, BASE, or whole-product credit.",
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "whole_entityos_hcu_credit": False,
        }
        result["result_sha256"] = canonical_sha(result)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({
            "schema": SCHEMA,
            "status": result["status"],
            "rank": basis_packet["rank"],
            "rank_verdict": basis_packet["rank_verdict"],
            "basis_packet_sha256": basis_packet["basis_packet_sha256"],
            "result_sha256": result["result_sha256"],
        }, sort_keys=True))
        return 0
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_NATIVE_Q8_BASIS_BUILD",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:2000]}",
            "holdout_opened": False,
            "intervention_executed": False,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "whole_entityos_hcu_credit": False,
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"schema": SCHEMA, "status": blocked["status"], "reason": blocked["reason"]}, sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
