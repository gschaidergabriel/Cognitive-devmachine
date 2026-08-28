#!/usr/bin/env python3
"""Bind the canonical abstract-state challenge to native Q8 layer-21 basis capture.

Why this exists
---------------
The current native Q8 basis builder still owns a historical prompt set containing strong
semantic-pole/compliance proxies (grant/refuse/support/oppose/etc.).  Meanwhile the current
`trigger1_abstract_state_challenge_v1` already freezes and validates a harder six-family,
instruction-free, repeated-target-marker-free calibration design plus six target-blind,
lexically disjoint holdout families.

This bridge removes the remaining source-path mismatch without creating another semantic
geometry authority:

1. build or accept the exact canonical abstract challenge;
2. run its validator and require PASS before any native decode;
3. select *only* the 18 CALIBRATION declarative state rows;
4. preserve their exact model-facing prompt bytes/hashes while adapting evaluator metadata
   to the existing pinned native layer-capture interface;
5. capture Qwen3-0.6B Q8_0 layer-input 21 activations through the existing pinned harness;
6. emit the exact activation payload and blocked simplex-rank analysis already consumed by
   the retained family-balanced geometry/finalizer/cvec path.

The 18 HOLDOUT rows are never passed to the capture harness here.  This tool does not fit a
nuisance subspace, choose gain, emit a competing target cvec, execute holdout intervention,
or mint semantic/J-Space/HCU/EntityOS/training/canonical credit.  Downstream nuisance
residualization, family-balanced geometry, cvec emission, direct native ALL_PROMPT_TOKENS
causal evidence, exact v12 challenge/runtime binding, and optional cross-scope effect bridge
remain separate gates.
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

from tools import trigger1_abstract_state_challenge_v1 as challenge_v1
from tools import trigger1_native_q8_jspace_basis_build as native_donor
from tools import trigger1_semantic_simplex_rank_analyze as ranker

SCHEMA = "CLAY_TRIGGER1_QWEN06_Q8_ABSTRACT_CHALLENGE_BASIS_CAPTURE/v1"
BASIS_ROW_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_CHALLENGE_NATIVE_BASIS_ROW/v1"
EXPECTED_CALIBRATION_ROWS = 18


class BridgeError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vector_sha_f32(values: list[float]) -> str:
    return hashlib.sha256(np.asarray(values, dtype="<f4").tobytes()).hexdigest()


def prepare_basis_rows(challenge: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate challenge bytes and adapt only calibration rows to native-capture metadata."""
    verdict = challenge_v1.validate(challenge)
    if verdict.get("pass") is not True:
        failures = verdict.get("failures") if isinstance(verdict.get("failures"), list) else []
        raise BridgeError("ABSTRACT_CHALLENGE_VALIDATION_FAILED:" + "|".join(str(x) for x in failures[:20]))

    rows = challenge.get("calibration_rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_CALIBRATION_ROWS:
        raise BridgeError("EXACTLY_EIGHTEEN_CALIBRATION_ROWS_REQUIRED")

    prepared: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_prompt_sha: set[str] = set()
    family_targets: dict[str, set[str]] = {}
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise BridgeError(f"CALIBRATION_ROW_{index}_OBJECT_REQUIRED")
        family = str(raw.get("family_id") or "").strip()
        target = str(raw.get("semantic_target") or "").strip().upper()
        prompt = raw.get("prompt")
        prompt_sha = raw.get("prompt_sha256")
        if not family:
            raise BridgeError(f"CALIBRATION_ROW_{index}_FAMILY_REQUIRED")
        if target not in challenge_v1.TARGETS:
            raise BridgeError(f"CALIBRATION_ROW_{index}_TARGET_INVALID")
        if not isinstance(prompt, str) or not prompt:
            raise BridgeError(f"CALIBRATION_ROW_{index}_PROMPT_REQUIRED")
        if challenge_v1.text_sha(prompt) != prompt_sha:
            raise BridgeError(f"CALIBRATION_ROW_{index}_PROMPT_SHA256_MISMATCH")
        if raw.get("instruction_free_state_capture") is not True:
            raise BridgeError(f"CALIBRATION_ROW_{index}_INSTRUCTION_FREE_REQUIRED")
        if raw.get("model_facing_target_identity_exposed") is not False:
            raise BridgeError(f"CALIBRATION_ROW_{index}_TARGET_IDENTITY_EXPOSED")

        row_id = f"abstract-challenge:{family}:{target.lower()}"
        if row_id in seen_ids:
            raise BridgeError(f"DUPLICATE_NATIVE_BASIS_ROW_ID:{row_id}")
        if prompt_sha in seen_prompt_sha:
            raise BridgeError(f"DUPLICATE_NATIVE_BASIS_PROMPT_SHA256:{prompt_sha}")
        seen_ids.add(row_id)
        seen_prompt_sha.add(str(prompt_sha))
        family_targets.setdefault(family, set()).add(target)
        prepared.append(
            {
                "schema": BASIS_ROW_SCHEMA,
                "row_id": row_id,
                "family_group_id": family,
                "semantic_class": target,
                "prompt": prompt,
                "prompt_sha256": prompt_sha,
                "source_split": "CALIBRATION",
                "source_family_sha256": raw.get("family_sha256"),
                "source_seed": raw.get("seed"),
                "source_state_surface_sha256": raw.get("state_surface_sha256"),
            }
        )

    if len(family_targets) != 6:
        raise BridgeError("EXACTLY_SIX_CALIBRATION_FAMILIES_REQUIRED")
    required = set(challenge_v1.TARGETS)
    for family, targets in family_targets.items():
        if targets != required:
            raise BridgeError(f"CALIBRATION_FAMILY_TARGET_TRIAD_REQUIRED:{family}")

    # Recheck exact byte/hash preservation after adaptation.  Metadata may change shape;
    # model-facing strings must not.
    source_by_key = {
        (str(row["family_id"]), str(row["semantic_target"])): row for row in rows
    }
    for row in prepared:
        source = source_by_key[(row["family_group_id"], row["semantic_class"])]
        if row["prompt"] != source["prompt"] or row["prompt_sha256"] != source["prompt_sha256"]:
            raise BridgeError(f"MODEL_FACING_BYTES_CHANGED_DURING_ADAPTATION:{row['row_id']}")

    return verdict, prepared


def build_rank_payload(
    prepared_rows: list[dict[str, Any]], observations: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Use the retained rank input schema while preserving exact challenge row identity."""
    expected = {row["row_id"] for row in prepared_rows}
    if set(observations) != expected:
        raise BridgeError("NATIVE_CAPTURE_CASE_UNIVERSE_MISMATCH")
    payload = native_donor.build_rank_payload(prepared_rows, observations)
    if payload.get("schema") != ranker.INPUT_SCHEMA:
        raise BridgeError("RANK_PAYLOAD_SCHEMA_MISMATCH")
    return payload


def capture(
    *,
    challenge: dict[str, Any],
    output_dir: Path,
    llama_root: Path,
    gguf: Path,
    harness: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    verdict, rows = prepare_basis_rows(challenge)

    repo_root = Path(__file__).resolve().parents[1]
    source = {
        "repo_head": subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True, timeout=10
        ).strip(),
        "repo_tree": subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD^{tree}"], text=True, timeout=10
        ).strip(),
        "bridge_executor_sha256": sha_file(Path(__file__)),
        "challenge_source_sha256": sha_file(Path(challenge_v1.__file__)),
        "native_capture_donor_sha256": sha_file(Path(native_donor.__file__)),
        "harness_sha256": sha_file(harness),
    }

    actual_llama = subprocess.check_output(
        ["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    if actual_llama != native_donor.LLAMA_CPP_COMMIT:
        raise BridgeError(f"LLAMA_CPP_COMMIT_MISMATCH:{actual_llama}")
    actual_gguf = sha_file(gguf)
    if actual_gguf != native_donor.MODEL_GGUF_SHA256:
        raise BridgeError(f"GGUF_SHA256_MISMATCH:{actual_gguf}")

    header, observations = native_donor.run_capture(
        harness=harness,
        gguf=gguf,
        llama_root=llama_root,
        out=output_dir,
        rows=rows,
    )
    rank_payload = build_rank_payload(rows, observations)
    rank_result = ranker.analyze(rank_payload)
    if rank_result.get("verdict") == "UNRESOLVED":
        raise BridgeError("ABSTRACT_NATIVE_Q8_SIMPLEX_RANK_UNRESOLVED")

    rank_payload_path = output_dir / "abstract-challenge-native-q8-simplex-input.json"
    rank_result_path = output_dir / "abstract-challenge-native-q8-simplex-rank.json"
    rank_payload_path.write_text(
        json.dumps(rank_payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    rank_result_path.write_text(
        json.dumps(rank_result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    capture_receipts = {
        row_id: {
            "prompt_tokens": int(obs["prompt_tokens"]),
            "primary_l2": float(obs["primary_l2"]),
            "activation_sha256_f32le": vector_sha_f32(obs["primary_activation"]),
        }
        for row_id, obs in sorted(observations.items())
    }

    core = {
        "schema": SCHEMA,
        "status": "PASS_ABSTRACT_CHALLENGE_NATIVE_Q8_CALIBRATION_CAPTURE",
        "started_at": started,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": source,
        "runtime_identity": {
            "gguf_sha256": actual_gguf,
            "llama_cpp_commit": actual_llama,
            "native_capture_harness_sha256": source["harness_sha256"],
            "capture_layer_inp": native_donor.NATIVE_STATE_LAYER_INP,
            "corresponding_cvec_injection_layer": native_donor.INJECTION_LAYER,
        },
        "abstract_challenge_sha256": verdict["challenge_sha256"],
        "abstract_challenge_validation": {
            "pass": verdict["pass"],
            "calibration_family_count": verdict["calibration_family_count"],
            "holdout_family_count": verdict["holdout_family_count"],
            "calibration_instruction_free": verdict["calibration_instruction_free"],
            "holdout_target_blind": verdict["holdout_target_blind"],
            "repeated_target_lexical_marker_absent": verdict["repeated_target_lexical_marker_absent"],
            "cross_split_content_lexically_disjoint": verdict["cross_split_content_lexically_disjoint"],
            "semantic_target_x_code_counterbalanced": verdict["semantic_target_x_code_counterbalanced"],
        },
        "calibration_basis_row_count": len(rows),
        "calibration_basis_row_set_sha256": canonical_sha(rows),
        "holdout_rows_passed_to_capture_harness": 0,
        "capture_header": header,
        "capture_receipts": capture_receipts,
        "activation_payload_sha256": canonical_sha(rank_payload),
        "rank_analysis_receipt_sha256": rank_result.get("analysis_receipt_sha256"),
        "rank_verdict": rank_result.get("verdict"),
        "downstream_retained_paths": {
            "nuisance_residualization": "tools/trigger1_nuisance_residualize.py",
            "family_balanced_geometry": "tools/trigger1_native_q8_geometry_balance_v2.py",
            "family_balanced_cvec_emission": "tools/trigger1_native_q8_family_balanced_cvec_emit.py",
            "abstract_promotion": "tools/trigger1_jspace_promotion_gate_v12.py",
        },
        "gain_selected_here": False,
        "target_cvec_emitted_here": False,
        "holdout_model_rows_executed": 0,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "full_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Native Q8 calibration capture over the exact source-validated abstract challenge calibration bytes. "
            "It closes the proxy-heavy basis-source mismatch but does not itself establish nuisance-residualized "
            "semantic geometry, holdout causality, cross-scope equivalence, J-Space runtime credit, or product credit."
        ),
    }
    return {**core, "capture_result_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--harness", required=True)
    ap.add_argument("--challenge-json")
    args = ap.parse_args()

    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    challenge = (
        json.loads(Path(args.challenge_json).read_text(encoding="utf-8"))
        if args.challenge_json
        else challenge_v1.build_challenge()
    )
    try:
        result = capture(
            challenge=challenge,
            output_dir=out,
            llama_root=Path(args.llama_root).resolve(),
            gguf=Path(args.gguf).resolve(),
            harness=Path(args.harness).resolve(),
        )
        rc = 0
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "status": "BLOCKED_ABSTRACT_CHALLENGE_NATIVE_Q8_BASIS_CAPTURE",
            "reason": f"{type(exc).__name__}:{str(exc)[:2000]}",
            "model_execution_outcome": "UNKNOWN_IF_EXCEPTION_OCCURRED_AFTER_NATIVE_DECODE_BEGAN",
            "holdout_rows_passed_to_capture_harness": 0,
            "runtime_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "canonical_semantics_promotion": False,
        }
        result["capture_result_sha256"] = canonical_sha(result)
        rc = 3

    (out / "trigger1_native_q8_abstract_challenge_basis_capture_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "status": result["status"],
                "capture_result_sha256": result["capture_result_sha256"],
            },
            sort_keys=True,
        )
    )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
