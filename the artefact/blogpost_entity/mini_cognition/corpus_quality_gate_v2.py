#!/usr/bin/env python3
"""Fail-closed leakage/diversity gate for ClayCog chat JSONL corpora."""
import argparse
import hashlib
import json
from pathlib import Path


def load(path):
    rows = []
    for no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        messages = obj.get("messages")
        if not isinstance(messages, list) or [m.get("role") for m in messages] != ["system", "user", "assistant"]:
            raise ValueError(f"{path}:{no}: expected system,user,assistant messages")
        rows.append(messages)
    return rows


def canonical(messages):
    return json.dumps(messages, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stats(rows):
    canonical_rows = [canonical(row) for row in rows]
    prompts = [row[1]["content"] for row in rows]
    targets = [row[2]["content"] for row in rows]
    n = len(rows)
    return {
        "rows": n,
        "exact_unique": len(set(canonical_rows)),
        "exact_unique_rate": len(set(canonical_rows)) / n if n else 0.0,
        "prompt_unique": len(set(prompts)),
        "prompt_unique_rate": len(set(prompts)) / n if n else 0.0,
        "target_unique": len(set(targets)),
        "target_unique_rate": len(set(targets)) / n if n else 0.0,
        "duplicate_rows": n - len(set(canonical_rows)),
    }, set(canonical_rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("train")
    parser.add_argument("validation")
    parser.add_argument("--min-train-unique-rate", type=float, default=0.98)
    parser.add_argument("--min-validation-unique-rate", type=float, default=1.0)
    parser.add_argument("--min-train-prompt-unique-rate", type=float, default=0.95)
    parser.add_argument("--min-validation-prompt-unique-rate", type=float, default=1.0)
    args = parser.parse_args()

    train = load(args.train)
    validation = load(args.validation)
    train_stats, train_set = stats(train)
    validation_stats, validation_set = stats(validation)
    overlap = train_set & validation_set

    failures = []
    if train_stats["exact_unique_rate"] < args.min_train_unique_rate:
        failures.append("train_exact_duplicate_rate")
    if validation_stats["exact_unique_rate"] < args.min_validation_unique_rate:
        failures.append("validation_exact_duplicate_rate")
    if train_stats["prompt_unique_rate"] < args.min_train_prompt_unique_rate:
        failures.append("train_prompt_duplicate_rate")
    if validation_stats["prompt_unique_rate"] < args.min_validation_prompt_unique_rate:
        failures.append("validation_prompt_duplicate_rate")
    if overlap:
        failures.append("exact_train_validation_leakage")

    report = {
        "schema": "claycog-corpus-quality/v2",
        "train": train_stats,
        "validation": validation_stats,
        "exact_cross_split_overlap": len(overlap),
        "overlap_sample_sha256": sorted(digest(row) for row in overlap)[:8],
        "thresholds": {
            "min_train_unique_rate": args.min_train_unique_rate,
            "min_validation_unique_rate": args.min_validation_unique_rate,
            "min_train_prompt_unique_rate": args.min_train_prompt_unique_rate,
            "min_validation_prompt_unique_rate": args.min_validation_prompt_unique_rate,
        },
        "failures": failures,
        "ok": not failures,
    }
    print(json.dumps(report, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
