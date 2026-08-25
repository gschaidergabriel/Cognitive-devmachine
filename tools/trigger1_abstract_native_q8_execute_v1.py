#!/usr/bin/env python3
"""Execute the hard abstract-state Trigger-1 chain on the pinned native Qwen3-0.6B Q8_0 carrier.

This runner exists because the historical native semantic executor is intentionally preserved
but its basis/evaluation text contains direct AFFIRMATIVE/NEGATIVE/compliance vocabulary.
The new path consumes only already-admitted source primitives:

1. `trigger1_abstract_state_challenge_v1` for six declarative source/basis families and a
   fresh target-blind, lexically disjoint six-family holdout;
2. `trigger1_structural_label_free_cases` for a separate 3x3 structural gain-calibration split;
3. native Q8_0 hidden-state capture at layer-input 21 for a layer-20 cvec intervention;
4. explicit calibration-only nuisance captures for the four canonical v11 nuisance families;
5. `trigger1_nuisance_residualize` to project label/synonym/compliance/output-code nuisance
   directions out before any holdout intervention;
6. exact six-control gain selection on the structural calibration split;
7. a target-blind native BROADCAST holdout with +/sign/null/orthogonal/permuted controls plus
   a separately derived GENERIC_INSTRUCTION_COMPLIANCE nuisance vector; and
8. a same-native-runtime BROADCAST versus LAST_TOKEN_ONLY scope probe.  Its analyzer may prove
   localized scope and immediate actuator parity, but this runner never upgrades that to full
   downstream mechanistic identity.

The source can therefore execute the user's hard discriminator without reusing the old lexical
semantic prompts.  Running it is still an unusual model intervention and must only occur under
the repository's current atomic-lease/execution authority.  This program itself does not mint
canonical semantics, J-Space model credit, HCU/EntityOS credit, or training credit.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_abstract_state_challenge_v1 as challenge_mod
from tools import trigger1_structural_label_free_cases as structural_mod
from tools import trigger1_nuisance_residualize as residual_mod
from tools import trigger1_native_q8_jspace_basis_build as native_basis
from tools import trigger1_semantic_simplex_rank_analyze as ranker
from tools import trigger1_native_cvec_scope_analyze_v1 as scope_analyzer

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_NATIVE_Q8_EXECUTION/v1"
RUNTIME_BINDING_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_CHALLENGE_RUNTIME_BINDING/v1"
NUISANCE_CAPTURE_SCHEMA = "CLAY_TRIGGER1_NUISANCE_CALIBRATION_CAPTURE/v1"
CONTROL_FAMILY = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
GAIN_GRID = (0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
PRIMARY_LAYER_INP = native_basis.INJECTION_LAYER + 1
DOWNSTREAM_LAYER_INP = 24
NULL_DRIFT_MAX = 1e-5


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


def unit(v: np.ndarray, name: str) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(v))
    if not math.isfinite(n) or n <= 1e-12:
        raise RuntimeError(f"{name}_DEGENERATE")
    return v / n


def cosine(a: np.ndarray, b: np.ndarray) -> float | None:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na <= 1e-12 or nb <= 1e-12:
        return None
    return float(np.dot(a, b) / (na * nb))


def _basis_rows(challenge: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in challenge["calibration_rows"]:
        rows.append(
            {
                "row_id": f"basis:{raw['family_id']}:{raw['semantic_target'].lower()}",
                "family_group_id": str(raw["family_id"]),
                "semantic_class": str(raw["semantic_target"]),
                "prompt": str(raw["state_surface"]),
                "prompt_sha256": str(raw["state_surface_sha256"]),
                "challenge_row_sha256": canonical_sha(raw),
            }
        )
    if len(rows) != 18:
        raise RuntimeError("EXACT_SIX_BASIS_TRIPLETS_REQUIRED")
    return rows


def nuisance_pairs() -> tuple[dict[str, str], ...]:
    """Frozen calibration-only contrasts.  These prompts never enter the semantic holdout."""
    rows = (
        # Canonical label lexical directions: exact evaluator labels versus matched inert words.
        {"axis": "CANONICAL_LABEL_LEXEME", "pair": "label-a", "positive": "Marker text: AFFIRMATIVE.", "negative": "Marker text: COBALT."},
        {"axis": "CANONICAL_LABEL_LEXEME", "pair": "label-n", "positive": "Marker text: NEGATIVE.", "negative": "Marker text: TOPAZ."},
        {"axis": "CANONICAL_LABEL_LEXEME", "pair": "label-u", "positive": "Marker text: NEUTRAL.", "negative": "Marker text: QUARTZ."},
        # Decision/compliance synonym lexicon against matched inert lexical load.
        {"axis": "SEMANTIC_SYNONYM_LEXICON", "pair": "syn-1", "positive": "approve accept permit endorse", "negative": "amber cedar granite willow"},
        {"axis": "SEMANTIC_SYNONYM_LEXICON", "pair": "syn-2", "positive": "reject refuse deny oppose", "negative": "violet marble copper birch"},
        {"axis": "SEMANTIC_SYNONYM_LEXICON", "pair": "syn-3", "positive": "defer abstain undecided pending", "negative": "silver basalt linen maple"},
        # Generic instruction-following pressure with approximately matched content.
        {"axis": "GENERIC_INSTRUCTION_COMPLIANCE", "pair": "comp-1", "positive": "Follow this instruction exactly: retain the marker.", "negative": "This sentence describes retaining the marker."},
        {"axis": "GENERIC_INSTRUCTION_COMPLIANCE", "pair": "comp-2", "positive": "Do this now: use the stated symbol.", "negative": "The stated symbol is mentioned in this sentence."},
        {"axis": "GENERIC_INSTRUCTION_COMPLIANCE", "pair": "comp-3", "positive": "Obey the request and produce the indicated item.", "negative": "The request and indicated item are described here."},
        # Output-code identity span; three pairwise contrasts cover the A/B/C simplex.
        {"axis": "OUTPUT_CODE_IDENTITY", "pair": "code-ab", "positive": "Opaque symbol: A", "negative": "Opaque symbol: B"},
        {"axis": "OUTPUT_CODE_IDENTITY", "pair": "code-bc", "positive": "Opaque symbol: B", "negative": "Opaque symbol: C"},
        {"axis": "OUTPUT_CODE_IDENTITY", "pair": "code-ca", "positive": "Opaque symbol: C", "negative": "Opaque symbol: A"},
    )
    if {row["axis"] for row in rows} != set(residual_mod.REQUIRED_NUISANCE_FAMILIES):
        raise AssertionError("NUISANCE_AXIS_SET_DRIFT")
    return rows


def _nuisance_capture_rows(specs: Iterable[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        for sign in ("positive", "negative"):
            prompt = spec[sign]
            rows.append(
                {
                    "row_id": f"nuisance:{spec['axis']}:{spec['pair']}:{sign}",
                    "family_group_id": f"nuisance:{spec['axis']}:{spec['pair']}",
                    # run_capture ignores this field; keep a valid semantic class for receipt compatibility.
                    "semantic_class": "NEUTRAL",
                    "prompt": prompt,
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "nuisance_axis": spec["axis"],
                    "pair_id": spec["pair"],
                    "pair_sign": sign,
                }
            )
    return rows


def _nuisance_vectors(
    specs: tuple[dict[str, str], ...], observations: dict[str, dict[str, Any]]
) -> tuple[dict[str, list[list[float]]], dict[str, np.ndarray], dict[str, Any]]:
    grouped: dict[str, list[np.ndarray]] = {axis: [] for axis in residual_mod.REQUIRED_NUISANCE_FAMILIES}
    pair_receipts: list[dict[str, Any]] = []
    for spec in specs:
        p_id = f"nuisance:{spec['axis']}:{spec['pair']}:positive"
        n_id = f"nuisance:{spec['axis']}:{spec['pair']}:negative"
        p = np.asarray(observations[p_id]["primary_activation"], dtype=np.float64)
        n = np.asarray(observations[n_id]["primary_activation"], dtype=np.float64)
        contrast = p - n
        if float(np.linalg.norm(contrast)) <= 1e-12:
            raise RuntimeError(f"NUISANCE_PAIR_DEGENERATE:{spec['axis']}:{spec['pair']}")
        grouped[spec["axis"]].append(contrast)
        pair_receipts.append(
            {
                "axis": spec["axis"],
                "pair_id": spec["pair"],
                "positive_activation_sha256": canonical_sha(observations[p_id]["primary_activation"]),
                "negative_activation_sha256": canonical_sha(observations[n_id]["primary_activation"]),
                "contrast_f32_sha256": hashlib.sha256(np.asarray(contrast, dtype="<f4").tobytes()).hexdigest(),
            }
        )
    mean_directions = {
        axis: unit(np.mean(np.stack(values, axis=0), axis=0), f"NUISANCE_MEAN_{axis}")
        for axis, values in grouped.items()
    }
    payload_vectors = {axis: [v.tolist() for v in values] for axis, values in grouped.items()}
    receipt_core = {
        "schema": NUISANCE_CAPTURE_SCHEMA,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "required_axes": list(residual_mod.REQUIRED_NUISANCE_FAMILIES),
        "pair_receipts": pair_receipts,
        "holdout_opened": False,
        "runtime_credit_minted": False,
    }
    receipt = {**receipt_core, "receipt_sha256": canonical_sha(receipt_core)}
    return payload_vectors, mean_directions, receipt


def _deterministic_orthogonal(v: np.ndarray, seed_material: str) -> np.ndarray:
    v = unit(v, "CONTROL_SOURCE")
    seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    candidate = rng.standard_normal(v.shape[0])
    candidate = candidate - float(np.dot(candidate, v)) * v
    return unit(candidate, "ORTHOGONAL_CONTROL")


def _deterministic_permuted(v: np.ndarray, seed_material: str) -> np.ndarray:
    v = unit(v, "CONTROL_SOURCE")
    seed = int(hashlib.sha256((seed_material + ":perm").encode("utf-8")).hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(v.shape[0])
    candidate = v[perm]
    if np.all(perm == np.arange(v.shape[0])):
        candidate = np.roll(v, 1)
    return unit(candidate, "PERMUTED_CONTROL")


def control_vectors(v: np.ndarray, gain: float, seed_material: str) -> dict[str, np.ndarray | None]:
    u = unit(v, "SEMANTIC_TARGET_VECTOR")
    return {
        "BASELINE": None,
        "+VECTOR": u * gain,
        "SIGN_FLIP": -u * gain,
        "NULL_VECTOR": np.zeros_like(u),
        "ORTHOGONAL_SAME_NORM": _deterministic_orthogonal(u, seed_material) * gain,
        "PERMUTED_SAME_NORM": _deterministic_permuted(u, seed_material) * gain,
    }


def write_controls(out: Path, vectors: dict[str, np.ndarray], gain: float) -> dict[str, dict[str, dict[str, Any]]]:
    registry: dict[str, dict[str, dict[str, Any]]] = {}
    for target, vector in vectors.items():
        target_dir = out / f"gain-{gain:g}" / target.lower()
        target_dir.mkdir(parents=True, exist_ok=True)
        family = control_vectors(vector, gain, f"{target}:{gain:g}:{hashlib.sha256(np.asarray(vector, dtype='<f4').tobytes()).hexdigest()}")
        target_registry: dict[str, dict[str, Any]] = {}
        for control, value in family.items():
            if value is None:
                target_registry[control] = {"path": "-", "vector_sha256_f32le": None, "vector_l2": 0.0}
            else:
                info = native_basis.write_cvec(target_dir / f"{control.lower().replace('+','plus')}.cvec.f32le", value)
                target_registry[control] = info
        registry[target] = target_registry
    return registry


def _logical_structural_calibration() -> list[dict[str, Any]]:
    bundle = structural_mod.build_cases("CALIBRATION")
    rows = []
    for raw in bundle["cases"]:
        rows.append(
            {
                "case_id": raw["case_id"],
                "family_id": raw["scenario_family_sha256"],
                "semantic_target": raw["semantic_target"],
                "output_code_identity": raw["output_code_identity"],
                "prompt": raw["prompt"],
                "prompt_sha256": raw["prompt_sha256"],
                "seed": raw["seed"],
            }
        )
    return rows


def _logical_challenge_rows(challenge: dict[str, Any], split: str) -> list[dict[str, Any]]:
    source = challenge["calibration_rows"] if split == "CALIBRATION" else challenge["holdout_rows"]
    rows: list[dict[str, Any]] = []
    for raw in source:
        row = {
            "case_id": f"{split.lower()}:{raw['family_id']}:{raw['semantic_target'].lower()}",
            "family_id": raw["family_id"],
            "family_sha256": raw["family_sha256"],
            "semantic_target": raw["semantic_target"],
            "prompt": raw["prompt"],
            "prompt_sha256": raw["prompt_sha256"],
            "seed": raw["seed"],
        }
        if split == "HOLDOUT":
            row["output_code_identity"] = raw["output_code_identity"]
        rows.append(row)
    return rows


def _scope_tsv_line(
    case_id: str, mode: str, cvec_path: str, prompt: str
) -> str:
    return "\t".join(
        [
            case_id,
            mode,
            cvec_path,
            str(native_basis.INJECTION_LAYER),
            str(native_basis.INJECTION_LAYER),
            str(PRIMARY_LAYER_INP),
            str(DOWNSTREAM_LAYER_INP),
            prompt.encode("utf-8").hex(),
        ]
    )


def run_control_cases(
    *,
    scope_harness: Path,
    gguf: Path,
    llama_root: Path,
    out: Path,
    cases: list[dict[str, Any]],
    registry: dict[str, dict[str, dict[str, Any]]],
    phase: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    out.mkdir(parents=True, exist_ok=True)
    tsv = out / f"{phase.lower()}-controls.tsv"
    index: dict[str, tuple[dict[str, Any], str]] = {}
    lines: list[str] = []
    for case in cases:
        target = str(case["semantic_target"])
        if target not in registry:
            raise RuntimeError(f"TARGET_VECTOR_MISSING:{target}")
        for control in CONTROL_FAMILY:
            uid = f"{case['case_id']}::{control}"
            if uid in index:
                raise RuntimeError(f"DUPLICATE_RUNTIME_CASE_ID:{uid}")
            path = registry[target][control]["path"]
            mode = "BASELINE" if control == "BASELINE" else "BROADCAST"
            lines.append(_scope_tsv_line(uid, mode, path, str(case["prompt"])))
            index[uid] = (case, control)
    tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")

    env = dict(os.environ)
    lib = str(llama_root / "build" / "bin")
    env["LD_LIBRARY_PATH"] = lib + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    p = subprocess.run(
        [str(scope_harness), str(gguf), str(tsv), str(native_basis.N_EMBD), str(native_basis.N_LAYER)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=3600,
        check=False,
    )
    (out / f"{phase.lower()}-controls.stdout.jsonl").write_text(p.stdout, encoding="utf-8")
    (out / f"{phase.lower()}-controls.stderr.txt").write_text(p.stderr, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"NATIVE_SCOPE_HARNESS_FAILED:{phase}:{p.returncode}:{p.stderr[-2000:]}")
    parsed = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    if not parsed or parsed[0].get("schema") != scope_analyzer.HEADER:
        raise RuntimeError(f"SCOPE_HEADER_INVALID:{phase}")
    observations: dict[str, dict[str, Any]] = {}
    for obs in parsed[1:]:
        uid = str(obs.get("case_id") or "")
        if uid not in index or uid in observations:
            raise RuntimeError(f"SCOPE_CASE_ID_INVALID:{phase}:{uid}")
        case, control = index[uid]
        expected_scope = "NO_INTERVENTION" if control == "BASELINE" else "ALL_PROMPT_TOKENS"
        if obs.get("token_scope") != expected_scope:
            raise RuntimeError(f"SCOPE_ATTESTATION_MISMATCH:{phase}:{uid}:{obs.get('token_scope')}")
        observations[uid] = {
            **obs,
            "logical_case_id": case["case_id"],
            "semantic_target": case["semantic_target"],
            "control": control,
            "prompt_sha256": case["prompt_sha256"],
            "runtime_receipt_sha256": canonical_sha(obs),
        }
    if set(observations) != set(index):
        raise RuntimeError(f"SCOPE_CASE_UNIVERSE_MISMATCH:{phase}:{len(observations)}:{len(index)}")
    header_receipt = {
        "header": parsed[0],
        "stdout_sha256": hashlib.sha256(p.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(p.stderr.encode("utf-8")).hexdigest(),
        "phase": phase,
    }
    header_receipt["receipt_sha256"] = canonical_sha(header_receipt)
    return observations, header_receipt


def target_score(logits: dict[str, Any], target_code: str) -> float:
    others = [code for code in ("A", "B", "C") if code != target_code]
    return float(logits[target_code]) - 0.5 * (float(logits[others[0]]) + float(logits[others[1]]))


def control_metrics(cases: list[dict[str, Any]], observations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    effects: list[dict[str, Any]] = []
    failures: list[str] = []
    for case in cases:
        if "output_code_identity" not in case:
            continue
        scores: dict[str, float] = {}
        for control in CONTROL_FAMILY:
            uid = f"{case['case_id']}::{control}"
            obs = observations[uid]
            scores[control] = target_score(obs["token_logits"], case["output_code_identity"])
        e = {
            "case_id": case["case_id"],
            "family_id": case["family_id"],
            "semantic_target": case["semantic_target"],
            "target_code": case["output_code_identity"],
            "plus_vs_baseline": scores["+VECTOR"] - scores["BASELINE"],
            "baseline_vs_sign_flip": scores["BASELINE"] - scores["SIGN_FLIP"],
            "null_drift": abs(scores["NULL_VECTOR"] - scores["BASELINE"]),
            "plus_vs_orthogonal": scores["+VECTOR"] - scores["ORTHOGONAL_SAME_NORM"],
            "plus_vs_permuted": scores["+VECTOR"] - scores["PERMUTED_SAME_NORM"],
        }
        effects.append(e)
        if e["plus_vs_baseline"] <= 0:
            failures.append(f"PLUS_NOT_POSITIVE:{case['case_id']}")
        if e["baseline_vs_sign_flip"] <= 0:
            failures.append(f"SIGN_FLIP_NOT_REVERSED:{case['case_id']}")
        if e["null_drift"] > NULL_DRIFT_MAX:
            failures.append(f"NULL_DRIFT:{case['case_id']}")
        if e["plus_vs_orthogonal"] <= 0:
            failures.append(f"ORTHOGONAL_REPRODUCED:{case['case_id']}")
        if e["plus_vs_permuted"] <= 0:
            failures.append(f"PERMUTED_REPRODUCED:{case['case_id']}")
    if not effects:
        failures.append("NO_CODE_MAPPED_CASES")
    objective = min(
        min(e["plus_vs_baseline"], e["baseline_vs_sign_flip"], e["plus_vs_orthogonal"], e["plus_vs_permuted"])
        for e in effects
    ) if effects else float("-inf")
    return {
        "pass": not failures,
        "case_count": len(effects),
        "objective_min_specific_direction_margin": objective,
        "max_null_drift": max((e["null_drift"] for e in effects), default=None),
        "effects": effects,
        "failures": sorted(set(failures)),
    }


def class_selective_matrix(cases: list[dict[str, Any]], observations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    diagonal_ok = True
    sign_ok = True
    null_ok = True
    transport_ok = True
    sign_transport_cosines: list[float] = []
    for case in cases:
        target_code = case["output_code_identity"]
        base = observations[f"{case['case_id']}::BASELINE"]
        plus = observations[f"{case['case_id']}::+VECTOR"]
        sign = observations[f"{case['case_id']}::SIGN_FLIP"]
        nul = observations[f"{case['case_id']}::NULL_VECTOR"]
        delta = {code: float(plus["token_logits"][code]) - float(base["token_logits"][code]) for code in ("A", "B", "C")}
        sign_delta = {code: float(sign["token_logits"][code]) - float(base["token_logits"][code]) for code in ("A", "B", "C")}
        other = [code for code in ("A", "B", "C") if code != target_code]
        diagonal = delta[target_code] > max(delta[other[0]], delta[other[1]])
        sign_reversal = target_score(sign["token_logits"], target_code) < target_score(base["token_logits"], target_code)
        null_like = abs(target_score(nul["token_logits"], target_code) - target_score(base["token_logits"], target_code)) <= NULL_DRIFT_MAX
        diagonal_ok = diagonal_ok and diagonal
        sign_ok = sign_ok and sign_reversal
        null_ok = null_ok and null_like

        b = np.asarray(base["downstream_activation"], dtype=np.float64)
        p = np.asarray(plus["downstream_activation"], dtype=np.float64)
        s = np.asarray(sign["downstream_activation"], dtype=np.float64)
        pe = p - b
        se = s - b
        c = cosine(pe, se)
        if float(np.linalg.norm(pe)) <= 1e-8:
            transport_ok = False
        if c is not None:
            sign_transport_cosines.append(c)
        rows.append(
            {
                "case_id": case["case_id"],
                "semantic_target": case["semantic_target"],
                "target_code": target_code,
                "plus_logit_delta": delta,
                "sign_logit_delta": sign_delta,
                "diagonal_advantage": diagonal,
                "sign_flip_reverses_selectivity": sign_reversal,
                "null_vector_baseline_like": null_like,
                "downstream_plus_effect_l2": float(np.linalg.norm(pe)),
                "downstream_plus_vs_sign_cosine": c,
            }
        )
    receipt_core = {
        "rows": rows,
        "diagonal_advantage": diagonal_ok,
        "sign_flip_reverses_selectivity": sign_ok,
        "null_vector_baseline_like": null_ok,
        "nonterminal_transport_observed": transport_ok,
        "mean_downstream_plus_vs_sign_cosine": (
            float(np.mean(sign_transport_cosines)) if sign_transport_cosines else None
        ),
        "equal_family_weighting": True,
    }
    return {**receipt_core, "matrix_receipt_sha256": canonical_sha(receipt_core)}


def run_compliance_control(
    *,
    scope_harness: Path,
    gguf: Path,
    llama_root: Path,
    out: Path,
    holdout_cases: list[dict[str, Any]],
    compliance_vector: np.ndarray,
    gain: float,
    semantic_observations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    info = native_basis.write_cvec(out / "generic-compliance.cvec.f32le", unit(compliance_vector, "GENERIC_COMPLIANCE") * gain)
    # One execution per target-blind family is sufficient: evaluator target/code metadata is
    # deliberately not model-facing, so all three target rows in a family share this result.
    family_case: dict[str, dict[str, Any]] = {}
    for case in holdout_cases:
        family_case.setdefault(case["family_id"], case)
    lines = []
    uid_to_family: dict[str, str] = {}
    for family, case in sorted(family_case.items()):
        uid = f"compliance:{family}"
        lines.append(_scope_tsv_line(uid, "BROADCAST", info["path"], case["prompt"]))
        uid_to_family[uid] = family
    tsv = out / "generic-compliance-holdout.tsv"
    tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
    env = dict(os.environ)
    lib = str(llama_root / "build" / "bin")
    env["LD_LIBRARY_PATH"] = lib + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    p = subprocess.run(
        [str(scope_harness), str(gguf), str(tsv), str(native_basis.N_EMBD), str(native_basis.N_LAYER)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=1800, check=False,
    )
    (out / "generic-compliance.stdout.jsonl").write_text(p.stdout, encoding="utf-8")
    (out / "generic-compliance.stderr.txt").write_text(p.stderr, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"GENERIC_COMPLIANCE_HARNESS_FAILED:{p.returncode}:{p.stderr[-1600:]}")
    parsed = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    observations = {str(row["case_id"]): row for row in parsed[1:]}
    family_results: list[dict[str, Any]] = []
    full_matrix_reproduced = True
    for family, representative in sorted(family_case.items()):
        obs = observations[f"compliance:{family}"]
        same_family = [case for case in holdout_cases if case["family_id"] == family]
        target_effects = []
        for case in same_family:
            base = semantic_observations[f"{case['case_id']}::BASELINE"]
            effect = target_score(obs["token_logits"], case["output_code_identity"]) - target_score(base["token_logits"], case["output_code_identity"])
            target_effects.append({"semantic_target": case["semantic_target"], "target_code": case["output_code_identity"], "effect": effect})
        reproduces_family = all(row["effect"] > 0 for row in target_effects)
        full_matrix_reproduced = full_matrix_reproduced and reproduces_family
        family_results.append({"family_id": family, "target_effects": target_effects, "reproduces_all_targets": reproduces_family})
    core = {
        "control": "GENERIC_INSTRUCTION_COMPLIANCE",
        "gain": gain,
        "vector_receipt": {k: v for k, v in info.items() if k != "path"},
        "families": family_results,
        "full_target_matrix_reproduced": full_matrix_reproduced,
        "generic_compliance_axis_fails_to_reproduce_target_matrix": not full_matrix_reproduced,
        "stdout_sha256": hashlib.sha256(p.stdout.encode("utf-8")).hexdigest(),
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def run_native_scope_bridge(
    *,
    scope_harness: Path,
    gguf: Path,
    llama_root: Path,
    out: Path,
    calibration_cases: list[dict[str, Any]],
    registry: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    # One deterministic case per semantic target; +VECTOR only.  BASELINE/BROADCAST/LAST are
    # compared in the same native carrier, avoiding PyTorch/native conflation.
    chosen: dict[str, dict[str, Any]] = {}
    for case in calibration_cases:
        chosen.setdefault(case["semantic_target"], case)
    for target, case in sorted(chosen.items()):
        cvec = registry[target]["+VECTOR"]["path"]
        base_id = f"scope:{target.lower()}"
        lines.append(_scope_tsv_line(base_id, "BASELINE", "-", case["prompt"]))
        lines.append(_scope_tsv_line(base_id, "BROADCAST", cvec, case["prompt"]))
        lines.append(_scope_tsv_line(base_id, "LAST_TOKEN_ONLY", cvec, case["prompt"]))
    tsv = out / "native-scope-bridge.tsv"
    tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
    env = dict(os.environ)
    lib = str(llama_root / "build" / "bin")
    env["LD_LIBRARY_PATH"] = lib + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    p = subprocess.run(
        [str(scope_harness), str(gguf), str(tsv), str(native_basis.N_EMBD), str(native_basis.N_LAYER)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=1800, check=False,
    )
    (out / "native-scope-bridge.stdout.jsonl").write_text(p.stdout, encoding="utf-8")
    (out / "native-scope-bridge.stderr.txt").write_text(p.stderr, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"NATIVE_SCOPE_BRIDGE_FAILED:{p.returncode}:{p.stderr[-1600:]}")
    payload = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    result = scope_analyzer.analyze(payload)
    result["stdout_sha256"] = hashlib.sha256(p.stdout.encode("utf-8")).hexdigest()
    result["strict_micro_mechanistic_identity_claimed"] = False
    return result


def runtime_binding(
    challenge: dict[str, Any],
    calibration_cases: list[dict[str, Any]],
    holdout_cases: list[dict[str, Any]],
    calibration_obs: dict[str, dict[str, Any]],
    holdout_obs: dict[str, dict[str, Any]],
    compliance_receipt: dict[str, Any],
) -> dict[str, Any]:
    def rows_for(cases: list[dict[str, Any]], observations: dict[str, dict[str, Any]], split: str) -> list[dict[str, Any]]:
        rows = []
        for case in cases:
            controls = {
                control: observations[f"{case['case_id']}::{control}"]["runtime_receipt_sha256"]
                for control in CONTROL_FAMILY
            }
            row = {
                "family_id": case["family_id"],
                "family_sha256": case["family_sha256"],
                "semantic_target": case["semantic_target"],
                "seed": case["seed"],
                "prompt_sha256": case["prompt_sha256"],
                "runtime_receipt_sha256": controls["+VECTOR"],
                "control_runtime_receipts": controls,
            }
            if split == "HOLDOUT":
                row["output_code_identity"] = case["output_code_identity"]
            rows.append(row)
        return rows

    core = {
        "schema": RUNTIME_BINDING_SCHEMA,
        "challenge_sha256": challenge["challenge_sha256"],
        "runtime_intervention_scope": "ALL_PROMPT_TOKENS",
        "model_facing_target_identity_exposed": False,
        "prompt_bytes_revalidated_from_runtime_rows": True,
        "generic_compliance_axis_fails_to_reproduce_target_matrix": compliance_receipt["generic_compliance_axis_fails_to_reproduce_target_matrix"],
        "generic_compliance_control_receipt_sha256": compliance_receipt["receipt_sha256"],
        "calibration_rows": rows_for(calibration_cases, calibration_obs, "CALIBRATION"),
        "holdout_rows": rows_for(holdout_cases, holdout_obs, "HOLDOUT"),
    }
    return {**core, "binding_receipt_sha256": canonical_sha(core)}


def run(args: argparse.Namespace) -> dict[str, Any]:
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    llama_root = Path(args.llama_root).resolve()
    gguf = Path(args.gguf).resolve()
    capture_harness = Path(args.capture_harness).resolve()
    scope_harness = Path(args.scope_harness).resolve()

    llama_commit = subprocess.check_output(["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if llama_commit != native_basis.LLAMA_CPP_COMMIT:
        raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{llama_commit}")
    gguf_sha = sha_file(gguf)
    if gguf_sha != native_basis.MODEL_GGUF_SHA256:
        raise RuntimeError(f"GGUF_SHA256_MISMATCH:{gguf_sha}")

    challenge = challenge_mod.build_challenge()
    challenge_verdict = challenge_mod.validate(challenge)
    if challenge_verdict.get("pass") is not True:
        raise RuntimeError("ABSTRACT_CHALLENGE_SOURCE_GATE_FAILED:" + "|".join(challenge_verdict.get("failures", [])))
    challenge_verdict_sha = canonical_sha(challenge_verdict)
    (out / "abstract-state-challenge.json").write_text(json.dumps(challenge, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "abstract-state-challenge-verdict.json").write_text(json.dumps(challenge_verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # BASIS: six instruction-free declarative families; HOLDOUT remains unopened.
    basis_rows = _basis_rows(challenge)
    basis_out = out / "basis-capture"
    basis_out.mkdir(parents=True, exist_ok=True)
    basis_header, basis_obs = native_basis.run_capture(
        harness=capture_harness, gguf=gguf, llama_root=llama_root, out=basis_out, rows=basis_rows
    )
    rank_payload = native_basis.build_rank_payload(basis_rows, basis_obs)
    rank_result = ranker.analyze(rank_payload)
    if rank_result.get("verdict") == "UNRESOLVED":
        raise RuntimeError("ABSTRACT_SEMANTIC_SIMPLEX_RANK_UNRESOLVED")
    geometry = native_basis.native_geometry(basis_rows, basis_obs, rank_result)
    raw_semantic = {name: np.asarray(geometry["geometry_vectors"][name], dtype=np.float64) for name in native_basis.CLASSES}

    # NUISANCE: calibration only.  These four axes are explicitly estimated, not inferred
    # from vocabulary declarations.
    specs = nuisance_pairs()
    nuisance_rows = _nuisance_capture_rows(specs)
    nuisance_out = out / "nuisance-capture"
    nuisance_out.mkdir(parents=True, exist_ok=True)
    nuisance_header, nuisance_obs = native_basis.run_capture(
        harness=capture_harness, gguf=gguf, llama_root=llama_root, out=nuisance_out, rows=nuisance_rows
    )
    nuisance_vectors, nuisance_means, nuisance_receipt = _nuisance_vectors(specs, nuisance_obs)
    residual_input = {
        "schema": residual_mod.INPUT_SCHEMA,
        "dimension": native_basis.N_EMBD,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "semantic_source_receipt_sha256": rank_result["analysis_receipt_sha256"],
        "nuisance_source_receipt_sha256": nuisance_receipt["receipt_sha256"],
        "semantic_vectors": {name: raw_semantic[name].tolist() for name in native_basis.CLASSES},
        "nuisance_vectors": nuisance_vectors,
    }
    residual_result = residual_mod.residualize(residual_input)
    projected = {
        name: np.asarray(residual_result["projected_semantic_unit_vectors"][name], dtype=np.float64)
        for name in native_basis.CLASSES
    }
    (out / "nuisance-residualization.json").write_text(json.dumps(residual_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # GAIN: separate structural label-free calibration.  No holdout prompt is executed until
    # a six-control candidate passes this frozen grid.
    gain_cases = _logical_structural_calibration()
    gain_results: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    selected_registry: dict[str, dict[str, dict[str, Any]]] | None = None
    for gain in GAIN_GRID:
        registry = write_controls(out / "controls", projected, gain)
        observations, receipt = run_control_cases(
            scope_harness=scope_harness,
            gguf=gguf,
            llama_root=llama_root,
            out=out / "gain-calibration" / f"gain-{gain:g}",
            cases=gain_cases,
            registry=registry,
            phase=f"GAIN_CALIBRATION_{gain:g}",
        )
        metrics = control_metrics(gain_cases, observations)
        item = {"gain": gain, "metrics": metrics, "runtime_receipt_sha256": receipt["receipt_sha256"]}
        gain_results.append(item)
        if metrics["pass"] and (selected is None or metrics["objective_min_specific_direction_margin"] > selected["metrics"]["objective_min_specific_direction_margin"]):
            selected = item
            selected_registry = registry
    if selected is None or selected_registry is None:
        return {
            "schema": SCHEMA,
            "status": "SCIENTIFIC_NEGATIVE_NO_CALIBRATED_ABSTRACT_VECTOR",
            "challenge_sha256": challenge["challenge_sha256"],
            "challenge_source_gate_pass": True,
            "rank_result": rank_result,
            "nuisance_residualization": residual_result,
            "gain_calibration": gain_results,
            "holdout_opened": False,
            "runtime_credit_minted": False,
            "canonical_semantics_promotion": False,
            "strict_micro_mechanistic_identity_claimed": False,
        }

    selected_gain = float(selected["gain"])

    # Challenge CALIBRATION runtime binding under the already-frozen operating point.
    challenge_cal_cases = _logical_challenge_rows(challenge, "CALIBRATION")
    challenge_cal_obs, challenge_cal_receipt = run_control_cases(
        scope_harness=scope_harness,
        gguf=gguf,
        llama_root=llama_root,
        out=out / "challenge-calibration-binding",
        cases=challenge_cal_cases,
        registry=selected_registry,
        phase="ABSTRACT_CHALLENGE_CALIBRATION_BINDING",
    )

    # FRESH HOLDOUT: exact target-blind prompt bytes. Target identity exists only in which
    # projected cvec is selected externally and in evaluator metadata.
    holdout_cases = _logical_challenge_rows(challenge, "HOLDOUT")
    holdout_obs, holdout_receipt = run_control_cases(
        scope_harness=scope_harness,
        gguf=gguf,
        llama_root=llama_root,
        out=out / "fresh-holdout",
        cases=holdout_cases,
        registry=selected_registry,
        phase="FRESH_TARGET_BLIND_HOLDOUT",
    )
    holdout_metrics = control_metrics(holdout_cases, holdout_obs)
    matrix = class_selective_matrix(holdout_cases, holdout_obs)

    compliance = run_compliance_control(
        scope_harness=scope_harness,
        gguf=gguf,
        llama_root=llama_root,
        out=out / "holdout-compliance-control",
        holdout_cases=holdout_cases,
        compliance_vector=nuisance_means["GENERIC_INSTRUCTION_COMPLIANCE"],
        gain=selected_gain,
        semantic_observations=holdout_obs,
    )
    matrix["nuisance_controls_fail_to_reproduce"] = bool(
        compliance["generic_compliance_axis_fails_to_reproduce_target_matrix"] and holdout_metrics["pass"]
    )
    matrix["matrix_receipt_sha256"] = canonical_sha({k: v for k, v in matrix.items() if k != "matrix_receipt_sha256"})

    scope_bridge = run_native_scope_bridge(
        scope_harness=scope_harness,
        gguf=gguf,
        llama_root=llama_root,
        out=out / "native-scope-bridge",
        calibration_cases=gain_cases,
        registry=selected_registry,
    )

    binding = runtime_binding(
        challenge,
        challenge_cal_cases,
        holdout_cases,
        challenge_cal_obs,
        holdout_obs,
        compliance,
    )
    (out / "abstract-challenge-runtime-binding.json").write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Evidence packet shaped for the canonical v11 abstract deconfound/scope adjudicator.
    deconfound_core = {
        "basis_model_facing_canonical_labels_absent": challenge_verdict["repeated_target_lexical_marker_absent"],
        "holdout_model_facing_canonical_labels_absent": challenge_verdict["holdout_target_blind"],
        "basis_holdout_lexically_disjoint": challenge_verdict["cross_split_content_lexically_disjoint"],
        "basis_holdout_scenario_disjoint": True,
        "semantic_synonym_lexicon_disjoint": challenge_verdict["repeated_target_lexical_marker_absent"],
        "semantic_target_evaluator_metadata_only": True,
        "full_three_by_three_target_x_output_code": challenge_verdict["semantic_target_x_code_counterbalanced"],
        "per_scenario_target_and_code_rotation": challenge_verdict["semantic_target_x_code_counterbalanced"],
        "nuisance_subspace_fit_on_calibration_only": residual_result["fit_split"] == "CALIBRATION",
        "semantic_basis_residualized_against_nuisance_subspace": True,
        "residualization_frozen_before_holdout": residual_result["frozen_before_holdout"],
        "holdout_nuisance_controls_fail_to_reproduce": matrix["nuisance_controls_fail_to_reproduce"],
        "holdout_target_selective_causal_matrix_pass": bool(holdout_metrics["pass"] and matrix["diagonal_advantage"] and matrix["sign_flip_reverses_selectivity"] and matrix["null_vector_baseline_like"]),
        "nuisance_axes": list(residual_mod.REQUIRED_NUISANCE_FAMILIES),
        "lexical_audit_receipt_sha256": challenge_verdict_sha,
        "nuisance_subspace_receipt_sha256": nuisance_receipt["receipt_sha256"],
        "projected_basis_receipt_sha256": residual_result["result_sha256"],
        "holdout_nuisance_control_receipt_sha256": compliance["receipt_sha256"],
        "holdout_causal_matrix_receipt_sha256": matrix["matrix_receipt_sha256"],
        "post_projection_max_abs_nuisance_cosine": residual_result["post_projection_max_abs_nuisance_cosine"],
        "retained_semantic_subspace_norm_fraction": residual_result["retained_semantic_subspace_norm_fraction"],
        "lexical_audit_frozen_before_holdout": True,
    }
    deconfound_core["deconfound_receipt_sha256"] = canonical_sha(deconfound_core)

    direct_native_core = {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "token_scope": "ALL_PROMPT_TOKENS",
        "legacy_last_token_witness_used_as_causal_identity_premise": False,
        "same_projected_basis_as_preregistered": True,
        "calibration_only_operating_point_frozen_before_holdout": True,
        "fresh_label_free_counterbalanced_holdout": True,
        "matched_sign_null_orthogonal_permuted_and_nuisance_controls": True,
        "nonterminal_transport_observed": matrix["nonterminal_transport_observed"],
        # This runner records likelihood/logit evidence.  It deliberately leaves emitted-text
        # dual-readout false until the separate context-boundary/generation discriminator exists.
        "context_valid_dual_readout_agrees": False,
        "class_selective_causal_matrix_pass": deconfound_core["holdout_target_selective_causal_matrix_pass"],
        "runtime_execution_receipt_sha256": holdout_receipt["receipt_sha256"],
        "projected_basis_receipt_sha256": residual_result["result_sha256"],
        "calibration_receipt_sha256": canonical_sha(gain_results),
        "holdout_receipt_sha256": canonical_sha(holdout_metrics),
        "transport_receipt_sha256": matrix["matrix_receipt_sha256"],
        "dual_readout_receipt_sha256": None,
        "causal_matrix_receipt_sha256": matrix["matrix_receipt_sha256"],
    }
    direct_native_core["direct_native_scope_receipt_sha256"] = canonical_sha(direct_native_core)

    hard_three_blockers = bool(
        deconfound_core["holdout_target_selective_causal_matrix_pass"]
        and deconfound_core["holdout_nuisance_controls_fail_to_reproduce"]
        and residual_result["post_projection_max_abs_nuisance_cosine"] <= residual_mod.MAX_POST_PROJECTION_ABS_NUISANCE_COSINE
        and residual_result["retained_semantic_subspace_norm_fraction"] >= residual_mod.MIN_RETAINED_SEMANTIC_NORM_FRACTION
        and scope_bridge.get("localized_native_scope_pass") is True
    )

    result_core = {
        "schema": SCHEMA,
        "status": "PASS_USER_THREE_BLOCKER_DISCRIMINATOR" if hard_three_blockers else "SCIENTIFIC_NEGATIVE_OR_INCOMPLETE",
        "started_at": args.started_at,
        "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_head": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "gguf_sha256": gguf_sha,
        "llama_cpp_commit": llama_commit,
        "capture_harness_sha256": sha_file(capture_harness),
        "scope_harness_sha256": sha_file(scope_harness),
        "challenge": challenge,
        "challenge_verdict": challenge_verdict,
        "basis_capture_header": basis_header,
        "semantic_simplex_rank": rank_result,
        "nuisance_capture_header": nuisance_header,
        "nuisance_capture_receipt": nuisance_receipt,
        "nuisance_residualization": residual_result,
        "selected_gain": selected_gain,
        "gain_calibration": gain_results,
        "challenge_calibration_runtime_receipt": challenge_cal_receipt,
        "holdout_runtime_receipt": holdout_receipt,
        "holdout_metrics": holdout_metrics,
        "class_selective_causal_matrix": matrix,
        "generic_compliance_holdout_control": compliance,
        "native_scope_bridge": scope_bridge,
        "abstract_state_challenge_runtime_binding": binding,
        "abstract_state_deconfound": deconfound_core,
        "direct_native_scope_evidence_partial": direct_native_core,
        "user_three_blockers_pass": hard_three_blockers,
        "semantic_jspace_promotion_ready": False,
        "semantic_jspace_promotion_blocker": "CONTEXT_BOUNDARY_MULTI_CODEBOOK_GENERATED_TEXT_DUAL_READOUT_STILL_REQUIRED" if hard_three_blockers else "USER_THREE_BLOCKER_DISCRIMINATOR_NOT_PASS",
        "strict_micro_mechanistic_identity_claimed": False,
        "broadcast_full_causal_identity_claimed": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "canonical_semantics_promotion": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "A PASS closes the three user-named blockers at this exact native carrier/runtime identity: direct lexical/compliance nuisance is explicitly residualized, fresh target-blind lexically-disjoint counterbalanced holdout control is causal, and native token scope is localized/measured without assuming broadcast==last-token downstream. It intentionally does NOT by itself promote semantic J-Space because the independently identified exact prompt-boundary/multi-codebook/emitted-text dual-readout gate is still unexecuted."
        ),
    }
    return {**result_core, "result_sha256": canonical_sha(result_core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--capture-harness", required=True)
    ap.add_argument("--scope-harness", required=True)
    args = ap.parse_args()
    args.started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "trigger1_abstract_native_q8_result.json"
    try:
        result = run(args)
        path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"schema": SCHEMA, "status": result["status"], "result_sha256": result["result_sha256"]}, sort_keys=True))
        return 0 if result["user_three_blockers_pass"] else 2
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_ABSTRACT_NATIVE_Q8_EXECUTION",
            "started_at": args.started_at,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "reason": f"{type(exc).__name__}:{str(exc)[:3000]}",
            "runtime_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "canonical_semantics_promotion": False,
            "strict_micro_mechanistic_identity_claimed": False,
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"schema": SCHEMA, "status": blocked["status"], "reason": blocked["reason"]}, sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
