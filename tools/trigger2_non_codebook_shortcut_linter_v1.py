#!/usr/bin/env python3
"""Detect non-codebook lexical shortcuts in Trigger-2 context-binding JSONL.

This is a source/dataset linter only. It does not admit canonical data or mint
runtime, J-Space, HCU, EntityOS, or training credit.
"""
from __future__ import annotations
import argparse, collections, json, math, re
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_NON_CODEBOOK_SHORTCUT_AUDIT/v1"


def _outside_codebook(prompt: str) -> str:
    return re.sub(r"CODEBOOK\n.*?\nEND_CODEBOOK", "", prompt, flags=re.DOTALL).strip()


def _mi(xs: list[Any], ys: list[Any]) -> float:
    if len(xs) != len(ys) or not xs:
        return 0.0
    n = len(xs)
    cx = collections.Counter(xs)
    cy = collections.Counter(ys)
    cxy = collections.Counter(zip(xs, ys))
    out = 0.0
    for (x, y), k in cxy.items():
        pxy = k / n
        out += pxy * math.log2(pxy / ((cx[x] / n) * (cy[y] / n)))
    return out


def _lookup_accuracy(xs: list[Any], ys: list[Any]) -> float:
    groups: dict[Any, collections.Counter[Any]] = collections.defaultdict(collections.Counter)
    for x, y in zip(xs, ys):
        groups[x][y] += 1
    return sum(max(c.values()) for c in groups.values()) / len(xs) if xs else 0.0


def analyze(rows: Iterable[dict[str, Any]], *, mi_tolerance_bits: float = 1e-12) -> dict[str, Any]:
    rows = list(rows)
    failures: list[str] = []
    outside: list[str] = []
    targets: list[str] = []
    predictors: dict[str, list[Any]] = {
        "base_semantic_class": [],
        "target_semantic_class": [],
        "template_family": [],
        "query_polarity": [],
        "lexical_variant_index": [],
        "codebook_order": [],
    }
    for i, row in enumerate(rows):
        try:
            prompt = row["prompt"]
            target = row["target"]
            meta = row["curriculum"]
            if not isinstance(prompt, str) or not isinstance(target, str):
                raise ValueError("prompt/target must be strings")
            outside.append(_outside_codebook(prompt))
            targets.append(target)
            predictors["base_semantic_class"].append(meta["base_semantic_class"])
            predictors["target_semantic_class"].append(meta["target_semantic_class"])
            predictors["template_family"].append(meta["template_family"])
            predictors["query_polarity"].append(meta["query_polarity"])
            predictors["lexical_variant_index"].append(meta["lexical_variant_index"])
            predictors["codebook_order"].append(tuple(meta["codebook_order"]))
        except Exception as exc:
            failures.append(f"ROW_PARSE_FAILURE:{i}:{type(exc).__name__}:{exc}")
    if failures:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": failures,
            "rows_total": len(rows),
            "canonical_dataset_write_performed": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": False,
        }

    surface_mi = _mi(outside, targets)
    surface_lookup = _lookup_accuracy(outside, targets)
    marginal_chance = max(collections.Counter(targets).values()) / len(targets) if targets else 0.0
    feature_mi = {k: _mi(v, targets) for k, v in predictors.items()}
    surface_counts = collections.Counter(outside)
    repeated_counts = collections.Counter(surface_counts.values())

    if surface_mi > mi_tolerance_bits:
        failures.append(f"NON_CODEBOOK_SURFACE_TARGET_MI_NONZERO:{surface_mi:.15g}")
    if surface_lookup > marginal_chance + 1e-12:
        failures.append(
            f"NON_CODEBOOK_SURFACE_LOOKUP_ABOVE_MARGINAL:{surface_lookup:.15g}>{marginal_chance:.15g}"
        )

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "rows_total": len(rows),
        "failures": failures,
        "outside_surface_target_mi_bits": surface_mi,
        "outside_surface_lookup_accuracy": surface_lookup,
        "marginal_target_chance": marginal_chance,
        "predictor_target_mi_bits": feature_mi,
        "outside_surface_repeat_histogram": dict(sorted(repeated_counts.items())),
        "outside_surface_unique": len(surface_counts),
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Statistical shortcut linter over candidate rows only.",
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            raise ValueError(f"invalid JSONL line {line_no}: {exc}") from exc
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("jsonl", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    audit = analyze(read_jsonl(args.jsonl))
    text = json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
