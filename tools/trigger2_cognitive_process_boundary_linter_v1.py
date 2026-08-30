#!/usr/bin/env python3
"""Static fail-closed linter for Trigger-2 cognitive process-boundary seed.

Source-design validation only. This tool cannot admit canonical dataset rows or mint
runtime, J-Space, HCU, EntityOS, or training credit.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path

SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
TARGET_TYPE = "COGNITIVE_PROCESS_BOUNDARY_DISPATCH"
CLASSES = {
    "SIMULATE_ON_GRID",
    "STORE_IN_DB",
    "DETERMINISTIC_BOUNDARY",
    "EXTERNAL_STRONG_MODEL_BRIDGE",
    "OPTIONAL_CAUSAL_RESEARCH",
}
PROCESS_CLASS = {
    "ZECP01": "DETERMINISTIC_BOUNDARY",
    "ZECP02": "STORE_IN_DB",
    "ZECP03": "SIMULATE_ON_GRID",
    "ZECP06": "SIMULATE_ON_GRID",
    "ZECP13": "EXTERNAL_STRONG_MODEL_BRIDGE",
    "ZECP14": "EXTERNAL_STRONG_MODEL_BRIDGE",
    "ZECP17": "DETERMINISTIC_BOUNDARY",
    "ZECP20": "OPTIONAL_CAUSAL_RESEARCH",
}


def load_rows(path: Path) -> list[dict]:
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"line {lineno}: object required")
        rows.append(obj)
    return rows


def lint(rows: list[dict]) -> dict:
    failures: list[str] = []
    pairs: dict[str, list[dict]] = collections.defaultdict(list)
    class_counts: collections.Counter[str] = collections.Counter()

    for i, row in enumerate(rows):
        tag = f"ROW_{i}"
        expected = {
            "schema": SCHEMA,
            "evidence_class": "METHOD_ONLY",
            "reality_level": "R2",
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "fact_status": "NOT_APPLICABLE",
            "target_type": TARGET_TYPE,
            "split": "TRAIN",
            "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
            "selected_using_holdout": False,
            "training_credit_minted": False,
            "runtime_credit_minted": False,
            "pair_contract": "causal_flip",
        }
        for key, value in expected.items():
            if row.get(key) != value:
                failures.append(f"{tag}:{key}_MISMATCH")

        try:
            target = json.loads(row.get("target", ""))
        except Exception:
            failures.append(f"{tag}:TARGET_JSON_INVALID")
            target = {}
        cls = target.get("implementation_class")
        pid = target.get("process_id")
        if cls not in CLASSES:
            failures.append(f"{tag}:CLASS_INVALID")
        else:
            class_counts[cls] += 1
        if PROCESS_CLASS.get(pid) != cls:
            failures.append(f"{tag}:PROCESS_CLASS_BINDING_MISMATCH")
        if not target.get("authority") or not target.get("primary_packet_or_boundary"):
            failures.append(f"{tag}:TARGET_BOUNDARY_FIELDS_REQUIRED")

        family = row.get("family_id")
        if not family or row.get("counterfactual_pair_id") != family:
            failures.append(f"{tag}:PAIR_ID_INVALID")
        pairs[str(family)].append(row)

    if len(rows) != 10:
        failures.append(f"ROW_COUNT_EXPECTED_10_GOT_{len(rows)}")
    if class_counts != collections.Counter({c: 2 for c in CLASSES}):
        failures.append(f"EXACT_CLASS_BALANCE_FAIL:{dict(class_counts)}")
    if len(pairs) != 5:
        failures.append(f"PAIR_COUNT_EXPECTED_5_GOT_{len(pairs)}")

    for family, rows2 in pairs.items():
        if len(rows2) != 2:
            failures.append(f"{family}:PAIR_CARDINALITY_FAIL")
            continue
        if {r.get("pair_variant") for r in rows2} != {"BASE", "COUNTERFACTUAL"}:
            failures.append(f"{family}:PAIR_VARIANT_FAIL")
        if len({r.get("provenance_ancestry_id") for r in rows2}) != 1:
            failures.append(f"{family}:ANCESTRY_SPLIT_FAIL")
        ta, tb = (json.loads(r["target"]) for r in rows2)
        route_keys = ("process_id", "implementation_class", "authority", "primary_packet_or_boundary")
        if all(ta.get(k) == tb.get(k) for k in route_keys):
            failures.append(f"{family}:CAUSAL_FLIP_HAS_NO_BOUNDARY_CHANGE")

    return {
        "schema": "TRIGGER2_COGNITIVE_PROCESS_BOUNDARY_LINT/v1",
        "pass": not failures,
        "rows": len(rows),
        "families": len(pairs),
        "class_counts": dict(sorted(class_counts.items())),
        "failures": sorted(set(failures)),
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    args = ap.parse_args()
    result = lint(load_rows(args.jsonl))
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
