#!/usr/bin/env python3
"""Model-visible nuisance + semantic-ablation gate for Trigger-2 binder rows.

The gate intentionally derives its nuisance representation from the rendered prompt,
not hidden audit metadata. It masks only semantic record payloads (R1/R2/R3) while
preserving every other model-visible field: codebook mapping/order, proof topology,
focus routing, query polarity, template-specific symbol pool, and serialization.

If the ablated prompt predicts the target above the episode-local chance rate, the
corpus permits a nonsemantic shortcut and is rejected.

Source/dataset validation only. No canonical dataset, runtime, J-Space, HCU,
EntityOS, or training credit is minted.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_BINDING_VISIBLE_NUISANCE_GATE/v1"
_SCENE_LINE = re.compile(r"(?m)^(R[123]):[^\n]*$")
_CODEBOOK = re.compile(r"CODEBOOK\n(.*?)\nEND_CODEBOOK", re.DOTALL)


def ablate_semantic_scene(prompt: str) -> str:
    """Mask semantic record payloads while retaining their model-visible positions."""
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    seen = _SCENE_LINE.findall(prompt)
    if collections.Counter(seen) != collections.Counter({"R1": 1, "R2": 1, "R3": 1}):
        raise ValueError(f"expected exactly one R1/R2/R3 semantic line, got {seen!r}")
    return _SCENE_LINE.sub(lambda m: f"{m.group(1)}:<SEMANTIC_MASK>", prompt)


def codebook_symbols(prompt: str) -> tuple[str, ...]:
    """Read the three episode-local symbols from the rendered model-visible codebook."""
    m = _CODEBOOK.search(prompt)
    if not m:
        raise ValueError("missing CODEBOOK/END_CODEBOOK")
    out: list[str] = []
    for line in m.group(1).splitlines():
        if "->" not in line:
            raise ValueError(f"malformed codebook line: {line!r}")
        _, rhs = line.split("->", 1)
        symbol = rhs.strip()
        if not symbol:
            raise ValueError("empty codebook symbol")
        out.append(symbol)
    if len(out) != 3 or len(set(out)) != 3:
        raise ValueError(f"expected exactly three distinct symbols, got {out!r}")
    return tuple(out)


def _lookup_accuracy(keys: list[str], targets: list[str]) -> float:
    groups: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for key, target in zip(keys, targets):
        groups[key][target] += 1
    if not targets:
        return 0.0
    return sum(max(c.values()) for c in groups.values()) / len(targets)


def analyze(rows: Iterable[dict[str, Any]], *, tolerance: float = 1e-12) -> dict[str, Any]:
    rows = list(rows)
    failures: list[str] = []
    ablated_keys: list[str] = []
    full_keys: list[str] = []
    targets: list[str] = []
    group_symbol_sets: dict[str, tuple[str, ...]] = {}

    for i, row in enumerate(rows):
        try:
            prompt = row["prompt"]
            target = row["target"]
            if not isinstance(target, str) or not target:
                raise ValueError("target must be a nonempty string")
            ablated = ablate_semantic_scene(prompt)
            symbols = codebook_symbols(prompt)
            if target not in symbols:
                raise ValueError("target is not one of the rendered codebook symbols")
            prior = group_symbol_sets.setdefault(ablated, symbols)
            if set(prior) != set(symbols):
                raise ValueError("same ablated prompt key resolved to different codebook symbol sets")
            full_keys.append(prompt)
            ablated_keys.append(ablated)
            targets.append(target)
        except Exception as exc:
            failures.append(f"ROW_PARSE_FAILURE:{i}:{type(exc).__name__}:{exc}")

    if failures:
        return {
            "schema": SCHEMA,
            "pass": False,
            "rows_total": len(rows),
            "failures": failures,
            "model_visible_only": True,
            "canonical_dataset_write_performed": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": False,
        }

    groups: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for key, target in zip(ablated_keys, targets):
        groups[key][target] += 1

    unequal_groups = 0
    incomplete_groups = 0
    for key, counts in groups.items():
        expected_symbols = set(group_symbol_sets[key])
        if set(counts) != expected_symbols:
            incomplete_groups += 1
            failures.append("SEMANTIC_ABLATION_TARGET_SUPPORT_INCOMPLETE")
            continue
        if len(set(counts.values())) != 1:
            unequal_groups += 1
            failures.append("SEMANTIC_ABLATION_TARGET_COUNTS_IMBALANCED")

    ablated_acc = _lookup_accuracy(ablated_keys, targets)
    full_acc = _lookup_accuracy(full_keys, targets)
    chance = 1.0 / 3.0
    if ablated_acc > chance + tolerance:
        failures.append(f"MODEL_VISIBLE_NUISANCE_DECODER_ABOVE_CHANCE:{ablated_acc:.15g}>{chance:.15g}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "rows_total": len(rows),
        "ablated_prompt_groups": len(groups),
        "incomplete_target_support_groups": incomplete_groups,
        "imbalanced_target_groups": unequal_groups,
        "full_prompt_lookup_accuracy": full_acc,
        "semantic_ablated_lookup_accuracy": ablated_acc,
        "episode_local_chance_accuracy": chance,
        "semantic_dependency_accuracy_gap": full_acc - ablated_acc,
        "model_visible_only": True,
        "hidden_audit_metadata_used": False,
        "failures": sorted(set(failures)),
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Rendered-prompt nuisance/semantic-ablation validation only; no model or mechanism credit.",
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
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    audit = analyze(read_jsonl(args.jsonl))
    text = json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
