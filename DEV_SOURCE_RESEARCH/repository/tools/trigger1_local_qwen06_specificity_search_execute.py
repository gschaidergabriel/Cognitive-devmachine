#!/usr/bin/env python3
"""Calibration-only layer/gain/orientation specificity search for Qwen3-0.6B.

This successor is intentionally stricter than the fixed-midlayer experiment:
- basis construction uses only the existing basis split;
- layer, sign orientation and gain are selected only on the existing calibration split;
- calibration already includes BASELINE, +VECTOR, SIGN_FLIP, exact NULL_VECTOR,
  ORTHOGONAL_SAME_NORM and PERMUTED_SAME_NORM;
- the final evaluation uses a new disjoint holdout family that has not been used by
  the predecessor experiments;
- no external LLM credentials or paid providers are used.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_local_qwen06_midlayer_causal_execute as base

SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_SPECIFICITY_SEARCH/v1"
LAYER_CANDIDATES = (8, 14, 20)
GAIN_CANDIDATES = (0.25, 1.0, 4.0, 16.0)
ORIENTATIONS = ((1.0, "RAW_CONTRASTIVE_AXIS"), (-1.0, "NEGATED_CONTRASTIVE_AXIS"))
NEW_HOLDOUT = (
    (8111, "/no_think\nFresh holdout H4. Return exactly one uppercase token chosen from A B C."),
    (9221, "/no_think\nFresh holdout H5. Output one and only one of A, B, or C."),
    (10301, "/no_think\nFresh holdout H6. Choose a single capital letter among A B C; output nothing else."),
)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
        and all(r.get("hook_calls", 0) > 0 for r in rows if r["control"] != "BASELINE")
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


def observe(state: Any, prompts: tuple[tuple[int, str], ...], gain: float, family_prefix: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, prompt in prompts:
        for control in base.CONTROLS:
            row = state.infer({"prompt": prompt, "control": control, "gain": gain, "seed": seed})
            row["prompt_family"] = f"{family_prefix}-{seed}"
            rows.append(row)
    return rows


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_local_qwen06_specificity_search_result.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {
        "repo_head": base.git_text("rev-parse", "HEAD"),
        "repo_tree": base.git_text("rev-parse", "HEAD^{tree}"),
        "executor_sha256": sha_file(Path(__file__)),
        "predecessor_executor_sha256": sha_file(Path(base.__file__)),
    }
    try:
        (
            torch,
            transformers,
            snapshot,
            tokenizer,
            model,
            device,
            checkpoint_sha,
            tokenizer_sha,
            weight_manifest,
            _default_layer,
        ) = base.load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = base.resolve_token_triplet(tokenizer)
        runtime = base.runtime_manifest(torch, transformers, model)
        runtime_build_sha = base.canonical_sha(runtime)
        layers = model.model.layers

        calibration_candidates: list[dict[str, Any]] = []
        candidate_payloads: dict[str, tuple[Any, list[dict[str, Any]]]] = {}
        for layer_index in LAYER_CANDIDATES:
            if layer_index >= len(layers) - 1:
                continue
            raw_base, basis_receipts = base.activation_only_basis(
                torch, tokenizer, model, device, layers[layer_index]
            )
            for orientation, orientation_name in ORIENTATIONS:
                oriented = raw_base * float(orientation)
                for gain in GAIN_CANDIDATES:
                    state = base.RuntimeState(
                        torch, tokenizer, model, device, layers[layer_index], layer_index, oriented, token_ids
                    )
                    rows = observe(state, base.GAIN_CALIBRATION, gain, "specificity-cal")
                    m = metrics(rows)
                    key = f"L{layer_index}:{orientation_name}:G{gain}"
                    record = {
                        "key": key,
                        "layer_index": layer_index,
                        "downstream_transformer_layers": len(layers) - layer_index - 1,
                        "orientation": orientation_name,
                        "orientation_scalar": orientation,
                        "gain": gain,
                        "basis_vector_sha256": base.tensor_sha(oriented),
                        "basis_receipts_sha256": base.canonical_sha(basis_receipts),
                        "metrics": m,
                    }
                    calibration_candidates.append(record)
                    candidate_payloads[key] = (oriented, basis_receipts)

        passing = [r for r in calibration_candidates if r["metrics"]["pass"]]
        passing.sort(key=lambda r: float(r["metrics"]["objective_min_specific_direction_margin"]), reverse=True)
        selected = passing[0] if passing else None
        holdout_rows: list[dict[str, Any]] = []
        holdout_metrics: dict[str, Any]
        if selected is None:
            holdout_metrics = {"pass": False, "classification": "NO_CALIBRATION_CANDIDATE_PASSED_FULL_SPECIFICITY_CONTROLS"}
        else:
            vector, _basis_receipts = candidate_payloads[selected["key"]]
            layer_index = int(selected["layer_index"])
            state = base.RuntimeState(
                torch, tokenizer, model, device, layers[layer_index], layer_index, vector, token_ids
            )
            holdout_rows = observe(state, NEW_HOLDOUT, float(selected["gain"]), "fresh-hold")
            holdout_metrics = metrics(holdout_rows)
            holdout_metrics["classification"] = (
                "FRESH_HOLDOUT_SPECIFIC_INTERNAL_VECTOR_EFFECT_REPRODUCED"
                if holdout_metrics["pass"]
                else "FRESH_HOLDOUT_CONTROL_FAMILY_DID_NOT_ESTABLISH_SPECIFIC_EFFECT"
            )

        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "calibration-only select model-specific layer, axis orientation and gain for an A-vs-B/C internal causal direction, then test untouched fresh holdout",
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "layer_candidates": list(LAYER_CANDIDATES),
            "gain_candidates": list(GAIN_CANDIDATES),
            "orientation_candidates": [name for _, name in ORIENTATIONS],
            "calibration_family_sha256": base.canonical_sha([p for _, p in base.GAIN_CALIBRATION]),
            "fresh_holdout_family_sha256": base.canonical_sha([p for _, p in NEW_HOLDOUT]),
        }
        result = {
            "schema": SCHEMA,
            "status": "PASS" if holdout_metrics.get("pass") else "SCIENTIFIC_NEGATIVE",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "model": base.MODEL_ID,
            "model_revision": base.MODEL_REVISION,
            "checkpoint_sha256": checkpoint_sha,
            "checkpoint_weight_manifest": weight_manifest,
            "tokenizer_sha256": tokenizer_sha,
            "token_ids": token_ids,
            "token_labels": token_labels,
            "device": str(device),
            "runtime_manifest": runtime,
            "runtime_build_sha256": runtime_build_sha,
            "source_packet": source_packet,
            "source_packet_sha256": base.canonical_sha(source_packet),
            "calibration_policy": "layer + axis orientation + gain selected only on calibration split using all six controls",
            "calibration_candidates": calibration_candidates,
            "selected_calibration_candidate": selected,
            "fresh_holdout": {
                "seeds": [s for s, _ in NEW_HOLDOUT],
                "family_sha256": base.canonical_sha([p for _, p in NEW_HOLDOUT]),
                "rows": holdout_rows,
                "metrics": holdout_metrics,
            },
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "promotion_candidate_written": bool(holdout_metrics.get("pass")),
            "evidence_boundary": "PASS is model-specific nonterminal hidden-state causal component evidence only; never whole EntityOS/HCU, consciousness, or training credit.",
        }
        result["result_sha256"] = base.canonical_sha(result)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0 if holdout_metrics.get("pass") else 2
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_LOCAL_SPECIFICITY_SEARCH",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1200]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
        }
        blocked["result_sha256"] = base.canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
