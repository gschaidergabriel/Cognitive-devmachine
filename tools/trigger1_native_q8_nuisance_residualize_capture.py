#!/usr/bin/env python3
"""Capture native Q8 nuisance axes and residualize the abstract semantic basis.

This closes the executable-source gap between the v11 deconfound requirement and the
calibration-only SVD residualizer.  The four nuisance families are intentionally exposed in
separate, quarantined CALIBRATION prompts so their native layer-21 directions can be measured
and projected out of the semantic geometry:

* CANONICAL_LABEL_LEXEME
* SEMANTIC_SYNONYM_LEXICON
* GENERIC_INSTRUCTION_COMPLIANCE
* OUTPUT_CODE_IDENTITY

The nuisance prompts are not semantic-basis evidence and are never holdout rows.  They are
allowed to contain the very shortcuts being estimated because their sole purpose is to
measure nuisance directions.  The semantic source remains an independently captured,
label-free abstract calibration activation payload.

Pipeline:
1. evidence-bind/recompute the retained family-balanced semantic geometry from the exact
   abstract calibration activation payload and its rank result;
2. reconstruct the exact balanced semantic vectors and verify their hashes against geometry;
3. native-capture the frozen nuisance-only prompt design with the same pinned Q8/harness;
4. derive within-group centered/difference nuisance vectors;
5. call the canonical calibration-only SVD residualizer and emit projected semantic unit
   vectors plus exact nuisance/source receipts.

This tool selects no gain, serializes no cvec, opens no semantic holdout, executes no effect,
and mints no canonical/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from tools import trigger1_native_q8_geometry_balance as geometry_v1
from tools import trigger1_native_q8_geometry_balance_v2 as geometry_v2
from tools import trigger1_native_q8_jspace_basis_build as native_donor
from tools import trigger1_nuisance_residualize as residualizer

SCHEMA = "CLAY_TRIGGER1_QWEN06_Q8_NUISANCE_RESIDUALIZE_CAPTURE/v1"
DESIGN_SCHEMA = "CLAY_TRIGGER1_QWEN06_Q8_NUISANCE_CAPTURE_DESIGN/v1"
ROW_SCHEMA = "CLAY_TRIGGER1_QWEN06_Q8_NUISANCE_CAPTURE_ROW/v1"
REQUIRED_FAMILIES = residualizer.REQUIRED_NUISANCE_FAMILIES


class NuisanceCaptureError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vector_sha_f32(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype="<f4").tobytes()).hexdigest()


def vector_sha_f64(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype="<f8").tobytes()).hexdigest()


def nuisance_design() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    def add_three(family: str, group: str, scaffold: str, variants: tuple[str, str, str]) -> None:
        for slot, value in zip(("X0", "X1", "X2"), variants):
            prompt = scaffold.format(value=value)
            rows.append({
                "schema": ROW_SCHEMA,
                "row_id": f"nuisance:{family.lower()}:{group}:{slot.lower()}",
                "family_group_id": f"nuisance:{family}:{group}",
                "semantic_class": "AFFIRMATIVE",  # donor metadata only; ignored by nuisance derivation
                "nuisance_family": family,
                "contrast_group": group,
                "contrast_slot": slot,
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "purpose": "NUISANCE_AXIS_CALIBRATION_ONLY",
            })

    def add_pair(family: str, group: str, declarative: str, imperative: str) -> None:
        for slot, prompt in (("DECLARATIVE", declarative), ("IMPERATIVE", imperative)):
            rows.append({
                "schema": ROW_SCHEMA,
                "row_id": f"nuisance:{family.lower()}:{group}:{slot.lower()}",
                "family_group_id": f"nuisance:{family}:{group}",
                "semantic_class": "AFFIRMATIVE",  # donor metadata only; ignored by nuisance derivation
                "nuisance_family": family,
                "contrast_group": group,
                "contrast_slot": slot,
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "purpose": "NUISANCE_AXIS_CALIBRATION_ONLY",
            })

    add_three(
        "CANONICAL_LABEL_LEXEME",
        "header",
        "A metadata header contains exactly the word {value}.",
        ("affirmative", "negative", "neutral"),
    )
    add_three(
        "CANONICAL_LABEL_LEXEME",
        "tag",
        "A detached annotation tag is written as {value}.",
        ("affirmative", "negative", "neutral"),
    )

    add_three(
        "SEMANTIC_SYNONYM_LEXICON",
        "decision-a",
        "A vocabulary specimen contains exactly the verb {value}.",
        ("approve", "reject", "defer"),
    )
    add_three(
        "SEMANTIC_SYNONYM_LEXICON",
        "decision-b",
        "A vocabulary specimen contains exactly the verb {value}.",
        ("accept", "refuse", "withhold"),
    )
    add_three(
        "SEMANTIC_SYNONYM_LEXICON",
        "decision-c",
        "A vocabulary specimen contains exactly the verb {value}.",
        ("support", "oppose", "abstain"),
    )

    add_pair(
        "GENERIC_INSTRUCTION_COMPLIANCE",
        "cobalt",
        "The cobalt glyph remains present in working memory.",
        "Follow this instruction exactly: keep the cobalt glyph present in working memory.",
    )
    add_pair(
        "GENERIC_INSTRUCTION_COMPLIANCE",
        "topaz",
        "The topaz marker remains present in working memory.",
        "Obey this instruction exactly: keep the topaz marker present in working memory.",
    )
    add_pair(
        "GENERIC_INSTRUCTION_COMPLIANCE",
        "cedar",
        "The cedar token remains present in working memory.",
        "Comply with this instruction exactly: keep the cedar token present in working memory.",
    )

    add_three(
        "OUTPUT_CODE_IDENTITY",
        "symbol-a",
        "An opaque output symbol is displayed as {value}.",
        ("A", "B", "C"),
    )
    add_three(
        "OUTPUT_CODE_IDENTITY",
        "symbol-b",
        "A temporary code token is exactly {value}.",
        ("A", "B", "C"),
    )

    if set(row["nuisance_family"] for row in rows) != set(REQUIRED_FAMILIES):
        raise AssertionError("EXACT_REQUIRED_NUISANCE_FAMILIES_REQUIRED")
    row_ids = [row["row_id"] for row in rows]
    prompt_hashes = [row["prompt_sha256"] for row in rows]
    if len(set(row_ids)) != len(row_ids) or len(set(prompt_hashes)) != len(prompt_hashes):
        raise AssertionError("NUISANCE_DESIGN_ROWS_AND_PROMPTS_MUST_BE_UNIQUE")

    core = {
        "schema": DESIGN_SCHEMA,
        "fit_split": "CALIBRATION",
        "frozen_before_semantic_holdout": True,
        "purpose": "ESTIMATE_AND_REMOVE_NUISANCE_SUBSPACE_ONLY",
        "required_nuisance_families": list(REQUIRED_FAMILIES),
        "rows": rows,
        "semantic_holdout_rows_present": False,
        "model_executed": False,
    }
    return {**core, "design_sha256": canonical_sha(core)}


def _observed_vector(observations: dict[str, dict[str, Any]], row_id: str) -> np.ndarray:
    obs = observations.get(row_id)
    if not isinstance(obs, dict):
        raise NuisanceCaptureError(f"NUISANCE_OBSERVATION_MISSING:{row_id}")
    arr = np.asarray(obs.get("primary_activation"), dtype=np.float64)
    if arr.shape != (native_donor.N_EMBD,) or not np.all(np.isfinite(arr)):
        raise NuisanceCaptureError(f"NUISANCE_OBSERVATION_INVALID:{row_id}")
    return arr


def derive_nuisance_vectors(design: dict[str, Any], observations: dict[str, dict[str, Any]]) -> dict[str, list[list[float]]]:
    rows = design.get("rows")
    if not isinstance(rows, list) or not rows:
        raise NuisanceCaptureError("NUISANCE_DESIGN_ROWS_REQUIRED")
    expected = {row["row_id"] for row in rows}
    if set(observations) != expected:
        raise NuisanceCaptureError("NUISANCE_CAPTURE_CASE_UNIVERSE_MISMATCH")

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["nuisance_family"], row["contrast_group"]), []).append(row)

    out: dict[str, list[list[float]]] = {name: [] for name in REQUIRED_FAMILIES}
    for (family, group), group_rows in sorted(grouped.items()):
        by_slot = {row["contrast_slot"]: _observed_vector(observations, row["row_id"]) for row in group_rows}
        if family == "GENERIC_INSTRUCTION_COMPLIANCE":
            if set(by_slot) != {"DECLARATIVE", "IMPERATIVE"}:
                raise NuisanceCaptureError(f"COMPLIANCE_PAIR_INVALID:{group}")
            vector = by_slot["IMPERATIVE"] - by_slot["DECLARATIVE"]
            if float(np.linalg.norm(vector)) <= 1e-12:
                raise NuisanceCaptureError(f"COMPLIANCE_CONTRAST_DEGENERATE:{group}")
            out[family].append(vector.tolist())
        else:
            if set(by_slot) != {"X0", "X1", "X2"}:
                raise NuisanceCaptureError(f"THREE_WAY_NUISANCE_GROUP_INVALID:{family}:{group}")
            stack = np.stack([by_slot[slot] for slot in ("X0", "X1", "X2")], axis=0)
            center = np.mean(stack, axis=0)
            for slot in ("X0", "X1", "X2"):
                vector = by_slot[slot] - center
                if float(np.linalg.norm(vector)) <= 1e-12:
                    raise NuisanceCaptureError(f"NUISANCE_CENTERED_CONTRAST_DEGENERATE:{family}:{group}:{slot}")
                out[family].append(vector.tolist())

    if set(out) != set(REQUIRED_FAMILIES) or any(not out[name] for name in REQUIRED_FAMILIES):
        raise NuisanceCaptureError("DERIVED_EXACT_REQUIRED_NUISANCE_FAMILIES_REQUIRED")
    return out


def reconstruct_balanced_semantic_vectors(
    activation_payload: dict[str, Any], rank_result: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    geometry = geometry_v2.finalize(activation_payload, rank_result)
    families, grouped, dimension = geometry_v1._parse(activation_payload)
    if dimension != native_donor.N_EMBD:
        raise NuisanceCaptureError(f"PINNED_Q8_DIMENSION_REQUIRED:{dimension}")
    raw = geometry_v1._geometry_from_family_rows(
        families,
        grouped,
        energy_balance=True,
        rank=int(geometry["rank"]),
    )
    vectors = raw["vectors"]
    for semantic in geometry_v1.CLASSES:
        observed = vector_sha_f64(vectors[semantic])
        expected = geometry["balanced_target_vectors"][semantic]["vector_sha256_f64le"]
        if observed != expected:
            raise NuisanceCaptureError(f"SEMANTIC_GEOMETRY_VECTOR_HASH_MISMATCH:{semantic}")
    return geometry, {name: vectors[name].tolist() for name in geometry_v1.CLASSES}


def run(
    *,
    activation_payload: dict[str, Any],
    rank_result: dict[str, Any],
    output_dir: Path,
    llama_root: Path,
    gguf: Path,
    harness: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    geometry, semantic_vectors = reconstruct_balanced_semantic_vectors(activation_payload, rank_result)
    design = nuisance_design()

    actual_llama = subprocess.check_output(
        ["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    if actual_llama != native_donor.LLAMA_CPP_COMMIT:
        raise NuisanceCaptureError(f"LLAMA_CPP_COMMIT_MISMATCH:{actual_llama}")
    actual_gguf = sha_file(gguf)
    if actual_gguf != native_donor.MODEL_GGUF_SHA256:
        raise NuisanceCaptureError(f"GGUF_SHA256_MISMATCH:{actual_gguf}")

    header, observations = native_donor.run_capture(
        harness=harness,
        gguf=gguf,
        llama_root=llama_root,
        out=output_dir,
        rows=design["rows"],
    )
    nuisance_vectors = derive_nuisance_vectors(design, observations)
    capture_material = {
        "schema": "CLAY_TRIGGER1_QWEN06_Q8_NUISANCE_CAPTURE_RECEIPT/v1",
        "design_sha256": design["design_sha256"],
        "gguf_sha256": actual_gguf,
        "llama_cpp_commit": actual_llama,
        "harness_sha256": sha_file(harness),
        "layer_inp": native_donor.NATIVE_STATE_LAYER_INP,
        "row_activation_sha256_f32le": {
            row_id: vector_sha_f32(_observed_vector(observations, row_id)) for row_id in sorted(observations)
        },
        "derived_nuisance_vector_sha256_f32le": {
            family: [vector_sha_f32(np.asarray(vector, dtype=np.float64)) for vector in vectors]
            for family, vectors in nuisance_vectors.items()
        },
    }
    nuisance_receipt_sha = canonical_sha(capture_material)

    residual_input = {
        "schema": residualizer.INPUT_SCHEMA,
        "dimension": native_donor.N_EMBD,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "semantic_source_receipt_sha256": geometry["geometry_receipt_sha256"],
        "nuisance_source_receipt_sha256": nuisance_receipt_sha,
        "semantic_vectors": semantic_vectors,
        "nuisance_vectors": nuisance_vectors,
    }
    residual = residualizer.residualize(residual_input)

    (output_dir / "native-q8-nuisance-design.json").write_text(
        json.dumps(design, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "native-q8-nuisance-capture-receipt.json").write_text(
        json.dumps({**capture_material, "receipt_sha256": nuisance_receipt_sha}, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "native-q8-nuisance-residualizer-input.json").write_text(
        json.dumps(residual_input, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "native-q8-nuisance-residualized-semantic.json").write_text(
        json.dumps(residual, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    core = {
        "schema": SCHEMA,
        "status": "PASS_NATIVE_Q8_CALIBRATION_NUISANCE_RESIDUALIZATION",
        "started_at": started,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "runtime_identity": {
            "gguf_sha256": actual_gguf,
            "llama_cpp_commit": actual_llama,
            "native_capture_harness_sha256": sha_file(harness),
            "capture_layer_inp": native_donor.NATIVE_STATE_LAYER_INP,
        },
        "semantic_activation_payload_sha256": canonical_sha(activation_payload),
        "semantic_geometry_receipt_sha256": geometry["geometry_receipt_sha256"],
        "nuisance_design_sha256": design["design_sha256"],
        "nuisance_capture_receipt_sha256": nuisance_receipt_sha,
        "nuisance_vector_counts": {family: len(vectors) for family, vectors in nuisance_vectors.items()},
        "residualization_result_sha256": residual["result_sha256"],
        "projected_semantic_vector_sha256": residual["projected_semantic_vector_sha256"],
        "post_projection_max_abs_nuisance_cosine": residual["post_projection_max_abs_nuisance_cosine"],
        "retained_semantic_subspace_norm_fraction": residual["retained_semantic_subspace_norm_fraction"],
        "nuisance_subspace_rank": residual["nuisance_subspace_rank"],
        "semantic_holdout_rows_executed": 0,
        "gain_selected_here": False,
        "cvec_emitted_here": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Calibration-only native nuisance-axis measurement and deterministic projection. PASS shows only that "
            "the submitted semantic geometry retained sufficient norm after projection away from the four measured "
            "nuisance families. It does not establish target-selective holdout causality or semantic truth."
        ),
    }
    return {**core, "result_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--semantic-activation-payload", required=True)
    ap.add_argument("--rank-result", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    activation_payload = json.loads(Path(args.semantic_activation_payload).read_text(encoding="utf-8"))
    rank_result = json.loads(Path(args.rank_result).read_text(encoding="utf-8"))
    try:
        result = run(
            activation_payload=activation_payload,
            rank_result=rank_result,
            output_dir=output_dir,
            llama_root=Path(args.llama_root).resolve(),
            gguf=Path(args.gguf).resolve(),
            harness=Path(args.harness).resolve(),
        )
        rc = 0
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "status": "BLOCKED_NATIVE_Q8_CALIBRATION_NUISANCE_RESIDUALIZATION",
            "reason": f"{type(exc).__name__}:{str(exc)[:2000]}",
            "model_execution_outcome": "UNKNOWN_IF_EXCEPTION_OCCURRED_AFTER_NATIVE_DECODE_BEGAN",
            "semantic_holdout_rows_executed": 0,
            "runtime_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "canonical_semantics_promotion": False,
        }
        result["result_sha256"] = canonical_sha(result)
        rc = 3

    (output_dir / "trigger1_native_q8_nuisance_residualize_capture_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"schema": result["schema"], "status": result["status"], "result_sha256": result["result_sha256"]}, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
