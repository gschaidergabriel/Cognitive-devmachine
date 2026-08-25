#!/usr/bin/env python3
"""Deterministic source-only rank discriminator for Trigger-1 semantic activations.

This tool never runs a model and never opens holdout data. It consumes calibration-only,
model-facing-label-free activation vectors grouped into lexically disjoint families and
asks whether the three semantic classes are better described by one stable contrast or a
2-D centered simplex. The verdict is research metrology only; it grants no J-Space,
HCU, training, canonical-semantics, or whole-product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
from pathlib import Path
from typing import Any, Iterable

INPUT_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_SEMANTIC_ACTIVATIONS/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_DISCRIMINATOR/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
PERMS = tuple(itertools.permutations(CLASSES))


def _sha256_text(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _repo_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def canonical_json_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def vector_sha(vector: list[float]) -> str:
    h = hashlib.sha256()
    for value in vector:
        h.update(struct.pack("<d", float(value)))
    return h.hexdigest()


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def scale(a: list[float], s: float) -> list[float]:
    return [x * s for x in a]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: list[float]) -> float:
    return math.sqrt(max(0.0, dot(a, a)))


def normalize(a: list[float]) -> list[float] | None:
    n = norm(a)
    if not math.isfinite(n) or n <= 1e-15:
        return None
    return scale(a, 1.0 / n)


def mean(vectors: Iterable[list[float]]) -> list[float]:
    rows = list(vectors)
    if not rows:
        raise ValueError("MEAN_REQUIRES_NONEMPTY_VECTORS")
    d = len(rows[0])
    out = [0.0] * d
    for row in rows:
        if len(row) != d:
            raise ValueError("VECTOR_DIMENSION_MISMATCH")
        for i, value in enumerate(row):
            out[i] += value
    return [value / len(rows) for value in out]


def quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("QUANTILE_REQUIRES_VALUES")
    ordered = sorted(values)
    idx = int(math.ceil(q * len(ordered))) - 1
    idx = max(0, min(len(ordered) - 1, idx))
    return ordered[idx]


def spectral_stats(class_means: dict[str, list[float]]) -> dict[str, Any]:
    c = mean(class_means[name] for name in CLASSES)
    centered = [sub(class_means[name], c) for name in CLASSES]
    gram = [[dot(a, b) for b in centered] for a in centered]
    trace = sum(gram[i][i] for i in range(3))
    trace_sq = sum(value * value for row in gram for value in row)
    disc = max(0.0, 2.0 * trace_sq - trace * trace)
    lam1 = max(0.0, 0.5 * (trace + math.sqrt(disc)))
    lam2 = max(0.0, 0.5 * (trace - math.sqrt(disc)))
    sigma1 = math.sqrt(lam1)
    sigma2 = math.sqrt(lam2)
    ratio = sigma2 / sigma1 if sigma1 > 1e-15 else 0.0

    h1_raw = sub(class_means["AFFIRMATIVE"], scale(add(class_means["NEGATIVE"], class_means["NEUTRAL"]), 0.5))
    h1 = normalize(h1_raw)
    h2_raw = sub(class_means["NEGATIVE"], class_means["NEUTRAL"])
    if h1 is not None:
        h2_raw = sub(h2_raw, scale(h1, dot(h2_raw, h1)))
    h2 = normalize(h2_raw)
    return {
        "sigma1": sigma1,
        "sigma2": sigma2,
        "sigma2_over_sigma1": ratio,
        "h1": h1,
        "h2": h2,
    }


def _validate_and_group(payload: dict[str, Any]) -> tuple[dict[str, dict[str, list[float]]], int, list[dict[str, Any]]]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("INPUT_SCHEMA_MISMATCH")
    if payload.get("model_facing_label_free") is not True:
        raise ValueError("MODEL_FACING_LABEL_FREE_REQUIRED")
    if payload.get("lexically_disjoint_families") is not True:
        raise ValueError("LEXICALLY_DISJOINT_FAMILIES_REQUIRED")
    if payload.get("holdout_opened") is not False:
        raise ValueError("HOLDOUT_MUST_REMAIN_UNOPENED")
    if not _repo_sha(payload.get("repo_head")):
        raise ValueError("EXACT_REPO_HEAD_REQUIRED")
    for key in ("checkpoint_sha256", "tokenizer_sha256", "runtime_build_sha256"):
        if not _sha256_text(payload.get(key)):
            raise ValueError(f"{key.upper()}_REQUIRED")
    if not isinstance(payload.get("activation_site"), str) or not payload["activation_site"].strip():
        raise ValueError("ACTIVATION_SITE_REQUIRED")
    if not isinstance(payload.get("layer"), int) or payload["layer"] < 0:
        raise ValueError("NONNEGATIVE_LAYER_REQUIRED")

    records = payload.get("records")
    if not isinstance(records, list) or len(records) < 9:
        raise ValueError("AT_LEAST_THREE_COMPLETE_FAMILIES_REQUIRED")
    grouped: dict[str, dict[str, list[float]]] = {}
    bound_rows: list[dict[str, Any]] = []
    dimension: int | None = None
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("RECORD_OBJECT_REQUIRED")
        if any(key in row for key in ("prompt", "text", "model_facing_text", "semantic_label_token")):
            raise ValueError("MODEL_FACING_TEXT_MUST_NOT_ENTER_RANK_ANALYZER")
        family = row.get("family_id")
        semantic = str(row.get("semantic_class") or "").upper()
        vector = row.get("activation")
        if not isinstance(family, str) or not family.strip():
            raise ValueError("FAMILY_ID_REQUIRED")
        if semantic not in CLASSES:
            raise ValueError("SEMANTIC_CLASS_INVALID")
        if not isinstance(vector, list) or len(vector) < 2:
            raise ValueError("ACTIVATION_VECTOR_REQUIRED")
        try:
            parsed = [float(value) for value in vector]
        except (TypeError, ValueError):
            raise ValueError("ACTIVATION_VECTOR_NUMERIC_REQUIRED") from None
        if not all(math.isfinite(value) for value in parsed):
            raise ValueError("ACTIVATION_VECTOR_FINITE_REQUIRED")
        if dimension is None:
            dimension = len(parsed)
        elif len(parsed) != dimension:
            raise ValueError("VECTOR_DIMENSION_MISMATCH")
        slot = grouped.setdefault(family, {})
        if semantic in slot:
            raise ValueError(f"DUPLICATE_CLASS_WITHIN_FAMILY:{family}:{semantic}")
        slot[semantic] = parsed
        bound_rows.append({
            "family_id": family,
            "semantic_class": semantic,
            "activation_sha256_f64le": vector_sha(parsed),
        })

    assert dimension is not None
    if len(grouped) < 3:
        raise ValueError("AT_LEAST_THREE_COMPLETE_FAMILIES_REQUIRED")
    for family, rows in grouped.items():
        if set(rows) != set(CLASSES):
            raise ValueError(f"FAMILY_MUST_CONTAIN_EXACTLY_THREE_CLASSES:{family}")
    return grouped, dimension, sorted(bound_rows, key=lambda x: (x["family_id"], x["semantic_class"]))


def _class_means(grouped: dict[str, dict[str, list[float]]]) -> dict[str, list[float]]:
    return {semantic: mean(rows[semantic] for rows in grouped.values()) for semantic in CLASSES}


def _perm_configs(family_ids: list[str], max_null: int, seed_material: str) -> list[tuple[tuple[str, ...], ...]]:
    total = 6 ** len(family_ids)
    identity = tuple(CLASSES)
    if total <= max_null:
        return list(itertools.product(PERMS, repeat=len(family_ids)))

    configs: list[tuple[tuple[str, ...], ...]] = [tuple(identity for _ in family_ids)]
    seen = {configs[0]}
    counter = 0
    while len(configs) < max_null:
        digest = hashlib.sha256(f"{seed_material}:{counter}".encode("utf-8")).digest()
        counter += 1
        config = []
        for i in range(len(family_ids)):
            idx = digest[i % len(digest)] % len(PERMS)
            config.append(PERMS[idx])
        tup = tuple(config)
        if tup not in seen:
            seen.add(tup)
            configs.append(tup)
    return configs


def _permuted_grouped(grouped: dict[str, dict[str, list[float]]], family_ids: list[str], config: tuple[tuple[str, ...], ...]) -> dict[str, dict[str, list[float]]]:
    out: dict[str, dict[str, list[float]]] = {}
    for family, perm in zip(family_ids, config):
        original = grouped[family]
        out[family] = {target: original[source] for source, target in zip(CLASSES, perm)}
    return out


def _cosine(a: list[float] | None, b: list[float] | None) -> float | None:
    if a is None or b is None:
        return None
    return dot(a, b)


def analyze(payload: dict[str, Any], *, rank2_ratio_threshold: float = 0.15, null_q: float = 0.95, max_null: int = 4096) -> dict[str, Any]:
    if not (0.0 < rank2_ratio_threshold < 1.0):
        raise ValueError("RANK2_RATIO_THRESHOLD_RANGE")
    if not (0.5 <= null_q < 1.0):
        raise ValueError("NULL_Q_RANGE")
    if max_null < 32:
        raise ValueError("MAX_NULL_TOO_SMALL")

    grouped, dimension, bound_rows = _validate_and_group(payload)
    family_ids = sorted(grouped)
    observed = spectral_stats(_class_means(grouped))

    seed_material = canonical_json_sha({
        "repo_head": payload["repo_head"],
        "checkpoint_sha256": payload["checkpoint_sha256"],
        "activation_site": payload["activation_site"],
        "layer": payload["layer"],
        "rows": bound_rows,
    })
    configs = _perm_configs(family_ids, max_null, seed_material)
    null_s1: list[float] = []
    null_s2: list[float] = []
    identity_config = tuple(tuple(CLASSES) for _ in family_ids)
    for config in configs:
        if config == identity_config:
            continue
        stats = spectral_stats(_class_means(_permuted_grouped(grouped, family_ids, config)))
        null_s1.append(float(stats["sigma1"]))
        null_s2.append(float(stats["sigma2"]))
    if not null_s1:
        raise ValueError("NULL_PERMUTATION_SET_EMPTY")

    loo_ratios: list[float] = []
    for held_out in family_ids:
        subset = {family: rows for family, rows in grouped.items() if family != held_out}
        stats = spectral_stats(_class_means(subset))
        loo_ratios.append(float(stats["sigma2_over_sigma1"]))

    h1_cosines: list[float] = []
    h2_cosines: list[float] = []
    for family in family_ids:
        local = spectral_stats(grouped[family])
        c1 = _cosine(observed["h1"], local["h1"])
        c2 = _cosine(observed["h2"], local["h2"])
        if c1 is not None:
            h1_cosines.append(c1)
        if c2 is not None:
            h2_cosines.append(c2)

    q_s1 = quantile(null_s1, null_q)
    q_s2 = quantile(null_s2, null_q)
    ratio = float(observed["sigma2_over_sigma1"])
    h1_mean = sum(h1_cosines) / len(h1_cosines) if h1_cosines else None
    h2_mean = sum(h2_cosines) / len(h2_cosines) if h2_cosines else None

    rank1_signal = float(observed["sigma1"]) > q_s1
    stable_h1 = h1_mean is not None and h1_mean > 0.0
    stable_h2 = h2_mean is not None and h2_mean > 0.0
    rank2_signal = float(observed["sigma2"]) > q_s2 and ratio >= rank2_ratio_threshold
    loo_rank2 = min(loo_ratios) >= rank2_ratio_threshold * 0.5
    loo_rank1 = max(loo_ratios) < rank2_ratio_threshold

    if rank1_signal and rank2_signal and loo_rank2 and stable_h1 and stable_h2:
        verdict = "TWO_DIMENSIONAL_REQUIRED"
    elif rank1_signal and float(observed["sigma2"]) <= q_s2 and ratio < rank2_ratio_threshold and loo_rank1 and stable_h1:
        verdict = "ONE_DIMENSIONAL_SUPPORTED"
    else:
        verdict = "UNRESOLVED"

    output = {
        "schema": OUTPUT_SCHEMA,
        "verdict": verdict,
        "credit_effect": "RESEARCH_METROLOGY_ONLY_NO_RUNTIME_OR_PROMOTION_CREDIT",
        "input_identity": {
            "repo_head": payload["repo_head"],
            "checkpoint_sha256": payload["checkpoint_sha256"],
            "tokenizer_sha256": payload["tokenizer_sha256"],
            "runtime_build_sha256": payload["runtime_build_sha256"],
            "activation_site": payload["activation_site"],
            "layer": payload["layer"],
            "family_count": len(family_ids),
            "activation_dimension": dimension,
            "calibration_only": True,
            "holdout_opened": False,
            "model_facing_label_free": True,
            "lexically_disjoint_families": True,
            "bound_rows_sha256": canonical_json_sha(bound_rows),
        },
        "observed_geometry": {
            "sigma1": observed["sigma1"],
            "sigma2": observed["sigma2"],
            "sigma2_over_sigma1": ratio,
            "family_h1_cosine_mean": h1_mean,
            "family_h2_cosine_mean": h2_mean,
            "leave_one_family_out_sigma2_over_sigma1": loo_ratios,
        },
        "permutation_null": {
            "quantile": null_q,
            "configurations_evaluated": len(null_s1),
            "sigma1_q": q_s1,
            "sigma2_q": q_s2,
            "deterministic_seed_material_sha256": seed_material,
        },
        "decision_rule": {
            "rank2_ratio_threshold": rank2_ratio_threshold,
            "rank1_signal_above_null": rank1_signal,
            "rank2_signal_above_null_and_ratio": rank2_signal,
            "loo_rank2_stable": loo_rank2,
            "loo_rank1_stable": loo_rank1,
            "h1_direction_coherent": stable_h1,
            "h2_direction_coherent": stable_h2,
        },
        "promotion_boundary": "A rank verdict alone does not establish causal steerability. Native class-selective intervention-by-target evidence with fresh holdout and nuisance/off-target controls remains mandatory.",
    }
    output["analysis_sha256"] = canonical_json_sha(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--rank2-ratio-threshold", type=float, default=0.15)
    parser.add_argument("--null-q", type=float, default=0.95)
    parser.add_argument("--max-null", type=int, default=4096)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(payload, rank2_ratio_threshold=args.rank2_ratio_threshold, null_q=args.null_q, max_null=args.max_null)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
