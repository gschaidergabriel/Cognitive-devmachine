#!/usr/bin/env python3
"""Diversity/leakage/late-gate validator for claycog-sft/v3.

Structural ClayCode validity remains owned by validate_sft_v1.py; this gate adds exact
v3 cardinality, uniqueness, split isolation, and explicit late-gate negative coverage.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

EXPECTED_TRAIN = 1773
EXPECTED_VALID = 197
REQUIRED_TOTAL = {
    "omega_authority_reject": 80,
    "omega_generation_reject": 80,
    "omega_missing_cfg_reject": 80,
    "recovery_unknown_no_replay": 80,
}


def load(path):
    rows = []
    for no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            ms = row["messages"]
            if [m["role"] for m in ms] != ["system", "user", "assistant"]:
                raise ValueError("role order")
            rows.append(row)
        except Exception as exc:
            raise SystemExit(f"schema error {path}:{no}: {exc}")
    return rows


def canon(row):
    return json.dumps(row["messages"], ensure_ascii=False, separators=(",",":"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(code):
    if 'omega_reject(w,"authority_denied")' in code:
        return "omega_authority_reject"
    if 'omega_reject(w,"stale_generation")' in code:
        return "omega_generation_reject"
    if 'omega_reject(w,"missing_runtime_cfg")' in code:
        return "omega_missing_cfg_reject"
    if 'recovery_state(c,"UNKNOWN_AFTER_CRASH")' in code and 'focus_set(c,"preserve_unknown_effect_outcome")' in code:
        return "recovery_unknown_no_replay"
    return None


def gate_violations(code, family):
    out = []
    if family and "omega_commit_candidate(c,w)" in code:
        out.append("negative_path_commits")
    if family == "omega_authority_reject":
        for gate in ("grammar", "types", "schema", "authority"):
            if f'omega_validate(w,"{gate}")' not in code:
                out.append("authority_path_missing_" + gate)
    elif family == "omega_generation_reject":
        for gate in ("grammar", "types", "schema", "authority", "generation"):
            if f'omega_validate(w,"{gate}")' not in code:
                out.append("generation_path_missing_" + gate)
    elif family == "omega_missing_cfg_reject":
        if 'unknown_preserve(c,' not in code:
            out.append("missing_cfg_not_unknown")
    elif family == "recovery_unknown_no_replay":
        if 'unknown_preserve(c,"effect_outcome"' not in code:
            out.append("crash_outcome_not_unknown")
        if 'policy_select(c,"do_not_replay")' not in code:
            out.append("crash_replay_not_denied")
    return out


def main(train_path, valid_path):
    train = load(train_path)
    valid = load(valid_path)
    tc = [canon(x) for x in train]
    vc = [canon(x) for x in valid]
    tp = {x["messages"][1]["content"] for x in train}
    vp = {x["messages"][1]["content"] for x in valid}

    counts = Counter()
    violations = []
    for split, rows in (("train", train), ("validation", valid)):
        for idx, row in enumerate(rows, 1):
            code = row["messages"][-1]["content"]
            family = classify(code)
            if family:
                counts[family] += 1
                for error in gate_violations(code, family):
                    violations.append(f"{split}:{idx}:{family}:{error}")

    missing = {k: {"have": counts[k], "need": v} for k, v in REQUIRED_TOTAL.items() if counts[k] != v}
    report = {
        "schema": "claycog-corpus-validation/v3",
        "train_lines": len(train),
        "validation_lines": len(valid),
        "train_unique": len(set(tc)),
        "validation_unique": len(set(vc)),
        "exact_cross_split_overlap": len(set(tc) & set(vc)),
        "prompt_cross_split_overlap": len(tp & vp),
        "late_gate_counts": dict(sorted(counts.items())),
        "late_gate_expected": REQUIRED_TOTAL,
        "late_gate_missing_or_wrong": missing,
        "late_gate_violations": violations,
        "train_sha256": sha(train_path),
        "validation_sha256": sha(valid_path),
    }
    report["ok"] = (
        len(train) == EXPECTED_TRAIN
        and len(valid) == EXPECTED_VALID
        and len(set(tc)) == len(tc)
        and len(set(vc)) == len(vc)
        and report["exact_cross_split_overlap"] == 0
        and report["prompt_cross_split_overlap"] == 0
        and not missing
        and not violations
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: validate_corpus_v3.py train_v3.jsonl validation_v3.jsonl")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
