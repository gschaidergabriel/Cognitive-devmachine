#!/usr/bin/env python3
"""Qwen3-0.6B native llama.cpp cvec replication of the calibrated internal vector effect.

The internal direction and layer are inherited from the prior calibration-only PyTorch
specificity PASS. This native successor recalibrates only cvec gain on the calibration
split, then evaluates a new untouched holdout using BASELINE, +VECTOR, SIGN_FLIP,
exact NULL_VECTOR, ORTHOGONAL_SAME_NORM and PERMUTED_SAME_NORM.

The native harness calls llama_set_adapter_cvec before llama_decode and returns exact
next-token logits. No external LLM provider or credential is used.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_local_qwen06_midlayer_causal_execute as base

SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_NATIVE_LLAMA_CPP_CVEC_EXPERIMENT/v1"
MODEL_GGUF_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
LLAMA_CPP_COMMIT = "bb4caa7540188872173c44d161602d9271386413"
N_EMBD = 1024
N_LAYER = 28
SOURCE_LAYER = 20
TARGET_LAYER = 20
EXPECTED_SOURCE_BASIS_SHA256 = "c5b21d01f88a532b26791f89aa1ef71076368e8a24892d221a37dcf8aad8944e"
NATIVE_GAIN_GRID = (4.0, 8.0, 16.0, 32.0)
NATIVE_HOLDOUT = (
    (12011, "/no_think\nNative holdout N1. Return exactly one uppercase token from A B C."),
    (13007, "/no_think\nNative holdout N2. Output exactly one of A, B, or C and nothing else."),
    (14009, "/no_think\nNative holdout N3. Choose one capital token among A B C; return only it."),
)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def cvec_bytes(vector: Any, layer: int) -> bytes:
    raw = vector.detach().float().cpu().tolist()
    if len(raw) != N_EMBD:
        raise RuntimeError(f"VECTOR_DIMENSION_MISMATCH:{len(raw)}")
    chunk = b"".join(struct.pack("<f", float(x)) for x in raw)
    zero = b"\x00" * (4 * N_EMBD)
    payload = b"".join(chunk if il == layer else zero for il in range(1, N_LAYER))
    if len(payload) != (N_LAYER - 1) * N_EMBD * 4:
        raise AssertionError("CVEC_BUFFER_LENGTH_INVARIANT")
    return payload


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[tuple[int, str], dict[str, float]] = {}
    grouped = {name: [] for name in base.CONTROLS}
    for row in rows:
        score = float(row["target_score"])
        grouped[row["control"]].append(score)
        by_case.setdefault((int(row["seed"]), str(row["prompt_family"])), {})[row["control"]] = score
    plus: list[float] = []
    sign: list[float] = []
    nulld: list[float] = []
    orth: list[float] = []
    perm: list[float] = []
    for vals in by_case.values():
        if all(k in vals for k in base.CONTROLS):
            plus.append(vals["+VECTOR"] - vals["BASELINE"])
            sign.append(vals["BASELINE"] - vals["SIGN_FLIP"])
            nulld.append(abs(vals["NULL_VECTOR"] - vals["BASELINE"]))
            orth.append(vals["+VECTOR"] - vals["ORTHOGONAL_SAME_NORM"])
            perm.append(vals["+VECTOR"] - vals["PERMUTED_SAME_NORM"])
    complete = bool(plus and sign and nulld and orth and perm)
    min_plus = min(plus) if plus else None
    min_sign = min(sign) if sign else None
    max_null = max(nulld) if nulld else None
    min_orth = min(orth) if orth else None
    min_perm = min(perm) if perm else None
    passed = bool(
        complete
        and min_plus is not None and min_plus > 0
        and min_sign is not None and min_sign > 0
        and max_null is not None and max_null <= 1e-5
        and min_orth is not None and min_orth > 0
        and min_perm is not None and min_perm > 0
        and all(r.get("native_cvec_receipt", {}).get("rc") == 0 for r in rows if r["control"] != "BASELINE")
    )
    objective = min(min_plus, min_sign, min_orth, min_perm) if complete else float("-inf")
    return {
        "pass": passed,
        "objective_min_specific_direction_margin": objective,
        "mean_scores": {k: (sum(v) / len(v) if v else None) for k, v in grouped.items()},
        "min_plus_vs_baseline": min_plus,
        "min_baseline_vs_sign_flip": min_sign,
        "max_null_drift": max_null,
        "min_plus_vs_orthogonal_same_norm": min_orth,
        "min_plus_vs_permuted_same_norm": min_perm,
    }


def make_control_files(torch: Any, basis: Any, gain: float, out: Path) -> dict[str, dict[str, Any]]:
    family = base.matched_family(torch, basis, gain)
    controls: dict[str, dict[str, Any]] = {}
    safe = {
        "BASELINE": "baseline",
        "+VECTOR": "plus",
        "SIGN_FLIP": "sign_flip",
        "NULL_VECTOR": "null",
        "ORTHOGONAL_SAME_NORM": "orthogonal",
        "PERMUTED_SAME_NORM": "permuted",
    }
    for name in base.CONTROLS:
        vector = family[name]
        vector_sha = base.tensor_sha(vector)
        if name == "BASELINE":
            controls[name] = {
                "path": "-",
                "vector_sha256": vector_sha,
                "vector_l2": float(torch.linalg.vector_norm(vector).detach().cpu()),
                "cvec_f32le_sha256": None,
                "byte_count": 0,
                "float_count": 0,
            }
            continue
        raw = cvec_bytes(vector, TARGET_LAYER)
        path = out / f"gain-{gain:g}-{safe[name]}.cvec.f32le"
        path.write_bytes(raw)
        controls[name] = {
            "path": str(path),
            "vector_sha256": vector_sha,
            "vector_l2": float(torch.linalg.vector_norm(vector).detach().cpu()),
            "cvec_f32le_sha256": hashlib.sha256(raw).hexdigest(),
            "byte_count": len(raw),
            "float_count": len(raw) // 4,
        }
    return controls


def run_cases(
    harness: Path,
    gguf: Path,
    llama_root: Path,
    cases: list[dict[str, Any]],
    control_files: dict[str, dict[str, Any]],
    tsv: Path,
    stdout_path: Path,
    stderr_path: Path,
    runtime_identity: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lines = []
    by_id: dict[str, dict[str, Any]] = {}
    for case in cases:
        cid = case["case_id"]
        by_id[cid] = case
        cvec_path = control_files[case["control"]]["path"]
        lines.append(
            "\t".join(
                [cid, cvec_path, str(TARGET_LAYER), str(TARGET_LAYER), case["prompt"].encode("utf-8").hex()]
            )
        )
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
        timeout=900,
        check=False,
    )
    stdout_path.write_text(p.stdout, encoding="utf-8")
    stderr_path.write_text(p.stderr, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"NATIVE_HARNESS_FAILED:{p.returncode}:{p.stderr[-2000:]}")
    parsed = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    if not parsed or parsed[0].get("schema") != "CLAY_LLAMA_CPP_CVEC_LOGIT_HARNESS_HEADER/v1":
        raise RuntimeError("NATIVE_HARNESS_HEADER_MISSING")
    header = parsed[0]
    observations = parsed[1:]
    if len(observations) != len(cases):
        raise RuntimeError(f"NATIVE_OBSERVATION_COUNT_MISMATCH:{len(observations)}:{len(cases)}")
    rows: list[dict[str, Any]] = []
    for obs in observations:
        if obs.get("schema") != "CLAY_LLAMA_CPP_CVEC_LOGIT_OBSERVATION/v1":
            raise RuntimeError(f"NATIVE_OBSERVATION_ERROR:{obs}")
        cid = str(obs["case_id"])
        case = by_id[cid]
        control = str(case["control"])
        cinfo = control_files[control]
        applied = bool(obs.get("cvec_applied"))
        rc = int(obs.get("cvec_rc", -999))
        if control == "BASELINE":
            if applied:
                raise RuntimeError("BASELINE_MUST_NOT_APPLY_CVEC")
        else:
            if not applied or rc != 0:
                raise RuntimeError(f"CVEC_NOT_APPLIED:{cid}:{applied}:{rc}")
        material = {
            "case_id": cid,
            "seed": case["seed"],
            "prompt_family": case["prompt_family"],
            "prompt_sha256": hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest(),
            "control": control,
            "gain": case["gain"],
            "target_layer": TARGET_LAYER,
            "native_observation": obs,
            "vector_sha256": cinfo["vector_sha256"],
            "cvec_f32le_sha256": cinfo["cvec_f32le_sha256"],
            "runtime_identity": runtime_identity,
        }
        row = {
            **material,
            "target_score": float(obs["target_score"]),
            "best_label": max(obs["token_logits"], key=obs["token_logits"].get),
            "token_logits": obs["token_logits"],
            "native_cvec_receipt": {
                "called": applied,
                "rc": rc,
                "float_count": int(obs.get("cvec_float_count", 0)),
                "il_start": int(obs.get("il_start", TARGET_LAYER)),
                "il_end": int(obs.get("il_end", TARGET_LAYER)),
                "cvec_f32le_sha256": cinfo["cvec_f32le_sha256"],
            },
            "runtime_receipt_sha256": canonical_sha(material),
        }
        rows.append(row)
    return header, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_local_qwen06_native_cvec_result.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {
        "repo_head": base.git_text("rev-parse", "HEAD"),
        "repo_tree": base.git_text("rev-parse", "HEAD^{tree}"),
        "executor_sha256": sha_file(Path(__file__)),
    }

    try:
        llama_root = Path(args.llama_root).resolve()
        gguf = Path(args.gguf).resolve()
        harness = Path(args.harness).resolve()
        actual_llama_commit = subprocess.check_output(
            ["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
        if actual_llama_commit != LLAMA_CPP_COMMIT:
            raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{actual_llama_commit}")
        gguf_sha = sha_file(gguf)
        if gguf_sha != MODEL_GGUF_SHA256:
            raise RuntimeError(f"GGUF_SHA256_MISMATCH:{gguf_sha}")
        harness_sha = sha_file(harness)

        (
            torch,
            transformers,
            snapshot,
            tokenizer,
            model,
            device,
            source_checkpoint_sha,
            tokenizer_sha,
            weight_manifest,
            _default_layer,
        ) = base.load_exact_runtime(Path(args.cache_dir))
        source_layer = model.model.layers[SOURCE_LAYER]
        basis, basis_receipts = base.activation_only_basis(torch, tokenizer, model, device, source_layer)
        basis_sha = base.tensor_sha(basis)
        if basis_sha != EXPECTED_SOURCE_BASIS_SHA256:
            raise RuntimeError(f"SOURCE_BASIS_SHA256_MISMATCH:{basis_sha}")

        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "reuse the calibration-selected Qwen3-0.6B internal A-vs-B/C direction as a native llama.cpp control-vector source",
            "source_model": base.MODEL_ID,
            "source_revision": base.MODEL_REVISION,
            "source_checkpoint_sha256": source_checkpoint_sha,
            "source_activation_site": f"model.model.layers[{SOURCE_LAYER}]:output:last_token",
            "source_basis_receipts_sha256": canonical_sha(basis_receipts),
            "source_basis_vector_sha256": basis_sha,
            "dimension": int(basis.numel()),
        }
        source_packet_sha = canonical_sha(source_packet)

        runtime_identity = {
            "llama_cpp_source_commit": actual_llama_commit,
            "harness_sha256": harness_sha,
            "gguf_sha256": gguf_sha,
            "source_checkpoint_sha256": source_checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "python_runtime_build_sha256": canonical_sha(base.runtime_manifest(torch, transformers, model)),
        }

        calibration_candidates: list[dict[str, Any]] = []
        controls_by_gain: dict[float, dict[str, dict[str, Any]]] = {}
        rows_by_gain: dict[float, list[dict[str, Any]]] = {}
        header_by_gain: dict[float, dict[str, Any]] = {}
        for gain in NATIVE_GAIN_GRID:
            cdir = out / "cvec" / f"gain-{gain:g}"
            cdir.mkdir(parents=True, exist_ok=True)
            controls = make_control_files(torch, basis, gain, cdir)
            controls_by_gain[gain] = controls
            cases: list[dict[str, Any]] = []
            for seed, prompt in base.GAIN_CALIBRATION:
                for control in base.CONTROLS:
                    cases.append({
                        "case_id": f"cal-g{gain:g}-s{seed}-{control}",
                        "seed": seed,
                        "prompt": prompt,
                        "prompt_family": f"native-cal-{seed}",
                        "control": control,
                        "gain": gain,
                    })
            header, rows = run_cases(
                harness,
                gguf,
                llama_root,
                cases,
                controls,
                out / f"calibration-gain-{gain:g}.tsv",
                out / f"calibration-gain-{gain:g}.stdout.jsonl",
                out / f"calibration-gain-{gain:g}.stderr.txt",
                runtime_identity,
            )
            m = metrics(rows)
            header_by_gain[gain] = header
            rows_by_gain[gain] = rows
            calibration_candidates.append({
                "gain": gain,
                "target_layer": TARGET_LAYER,
                "metrics": m,
                "control_bindings": controls,
                "runtime_receipts_sha256": canonical_sha([r["runtime_receipt_sha256"] for r in rows]),
            })

        passing = [r for r in calibration_candidates if r["metrics"]["pass"]]
        passing.sort(key=lambda r: float(r["metrics"]["objective_min_specific_direction_margin"]), reverse=True)
        selected = passing[0] if passing else None
        holdout_rows: list[dict[str, Any]] = []
        holdout_metrics: dict[str, Any]
        selected_header: dict[str, Any] | None = None
        if selected is None:
            holdout_metrics = {
                "pass": False,
                "classification": "NO_NATIVE_CVEC_GAIN_PASSED_FULL_CALIBRATION_CONTROLS",
            }
        else:
            gain = float(selected["gain"])
            controls = controls_by_gain[gain]
            cases = []
            for seed, prompt in NATIVE_HOLDOUT:
                for control in base.CONTROLS:
                    cases.append({
                        "case_id": f"hold-g{gain:g}-s{seed}-{control}",
                        "seed": seed,
                        "prompt": prompt,
                        "prompt_family": f"native-hold-{seed}",
                        "control": control,
                        "gain": gain,
                    })
            selected_header, holdout_rows = run_cases(
                harness,
                gguf,
                llama_root,
                cases,
                controls,
                out / "holdout.tsv",
                out / "holdout.stdout.jsonl",
                out / "holdout.stderr.txt",
                runtime_identity,
            )
            holdout_metrics = metrics(holdout_rows)
            holdout_metrics["classification"] = (
                "NATIVE_LLAMA_CPP_CVEC_FRESH_HOLDOUT_SPECIFIC_EFFECT_REPRODUCED"
                if holdout_metrics["pass"]
                else "NATIVE_LLAMA_CPP_CVEC_HOLDOUT_CONTROL_FAMILY_DID_NOT_ESTABLISH_SPECIFIC_EFFECT"
            )

        selected_gain = float(selected["gain"]) if selected else None
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
            "source_packet_sha256": source_packet_sha,
            "source_model": base.MODEL_ID,
            "source_revision": base.MODEL_REVISION,
            "source_checkpoint_sha256": source_checkpoint_sha,
            "source_layer": SOURCE_LAYER,
            "target_model": "Qwen/Qwen3-0.6B-GGUF:Q8_0",
            "target_checkpoint_sha256": gguf_sha,
            "target_runtime": "llama.cpp",
            "target_runtime_source_commit": actual_llama_commit,
            "target_layer_start": TARGET_LAYER,
            "target_layer_end": TARGET_LAYER,
            "dimension": N_EMBD,
            "mapping": "identity hidden-coordinate map; no padding, truncation or learned projection",
            "gain_selected_on_native_calibration_only": selected_gain,
            "cvec_layout": "LLAMA_CPP_CVEC_LAYER_MAJOR_F32LE_NO_LAYER0/v1",
        }
        adapter_sha = canonical_sha(adapter)
        local_packet = {
            "schema": "JSPACE_LOCAL_QWEN3_CONTROL_PACKET/v1",
            "source_packet_sha256": source_packet_sha,
            "adapter_sha256": adapter_sha,
            "dimension": N_EMBD,
            "base_vector_sha256": basis_sha,
            "selected_gain": selected_gain,
            "target_layer": TARGET_LAYER,
            "target_checkpoint_sha256": gguf_sha,
            "llama_cpp_source_commit": actual_llama_commit,
        }
        local_packet_sha = canonical_sha(local_packet)

        controls_summary: dict[str, Any] = {}
        if selected:
            controls = controls_by_gain[float(selected["gain"])]
            for name in base.CONTROLS:
                receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == name]
                controls_summary[name] = {
                    **{k: v for k, v in controls[name].items() if k != "path"},
                    "runtime_receipt_sha256": canonical_sha(receipts),
                    "observations": len(receipts),
                }

        result = {
            "schema": SCHEMA,
            "status": "PASS" if holdout_metrics.get("pass") else "SCIENTIFIC_NEGATIVE",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "source_packet": source_packet,
            "source_packet_sha256": source_packet_sha,
            "adapter": adapter,
            "adapter_sha256": adapter_sha,
            "local_control_packet": local_packet,
            "local_control_packet_sha256": local_packet_sha,
            "source_basis_receipts": basis_receipts,
            "source_basis_vector_sha256": basis_sha,
            "source_model": base.MODEL_ID,
            "source_model_revision": base.MODEL_REVISION,
            "source_checkpoint_sha256": source_checkpoint_sha,
            "source_weight_manifest": weight_manifest,
            "tokenizer_sha256": tokenizer_sha,
            "target_model": "Qwen/Qwen3-0.6B-GGUF:Q8_0",
            "target_checkpoint_sha256": gguf_sha,
            "llama_cpp_source_commit": actual_llama_commit,
            "native_harness_sha256": harness_sha,
            "runtime_identity": runtime_identity,
            "native_gain_grid": list(NATIVE_GAIN_GRID),
            "native_target_layer": TARGET_LAYER,
            "calibration_candidates": calibration_candidates,
            "selected_calibration_candidate": selected,
            "fresh_native_holdout": {
                "seeds": [s for s, _ in NATIVE_HOLDOUT],
                "family_sha256": canonical_sha([p for _, p in NATIVE_HOLDOUT]),
                "harness_header": selected_header,
                "rows": holdout_rows,
                "metrics": holdout_metrics,
            },
            "controls": controls_summary,
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "native_llama_cpp_cvec_runtime_observed": bool(
                holdout_rows
                and all(
                    r["native_cvec_receipt"]["rc"] == 0
                    for r in holdout_rows
                    if r["control"] != "BASELINE"
                )
            ),
            "promotion_candidate_written": bool(holdout_metrics.get("pass")),
            "evidence_boundary": "PASS is exact native llama.cpp cvec model-specific causal component evidence. It does not by itself mint whole EntityOS/HCU, training or whole-product credit, and the A/B/C readout family remains subject to the separate scientific-independence/counterbalancing gate.",
        }
        result["result_sha256"] = canonical_sha(result)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0 if holdout_metrics.get("pass") else 2
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_NATIVE_LLAMA_CPP_CVEC",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:2000]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
