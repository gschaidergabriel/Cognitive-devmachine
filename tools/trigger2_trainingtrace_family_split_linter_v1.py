#!/usr/bin/env python3
"""Dataset-wide leakage linter for Trigger-2 TrainingTrace candidates.

This is a source/candidate validation tool only. It does not write the canonical
dataset and cannot mint factual, runtime, J-Space, training, HCU, or EntityOS
credit.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from tools import entityos_hcu_trainingtrace_candidate_gate_v1 as row_gate

SCHEMA = "TRIGGER2_TRAININGTRACE_FAMILY_SPLIT_LINTER/v1"
SPLITS = {"TRAIN", "VALIDATION", "HOLDOUT"}


def _load_jsonl(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_no, raw in enumerate(f, 1):
                if not raw.strip():
                    continue
                obj = json.loads(raw)
                if not isinstance(obj, dict):
                    raise ValueError(f"{path}:{line_no}: JSON object required")
                obj = dict(obj)
                obj["__source_path"] = str(path)
                obj["__source_line"] = line_no
                rows.append(obj)
    return rows


def adjudicate(rows: Any) -> dict[str, Any]:
    failures: list[str] = []
    row_failures: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        rows = []
        failures.append("ROWS_LIST_REQUIRED")

    family_splits: dict[str, set[str]] = defaultdict(set)
    ancestry_splits: dict[str, set[str]] = defaultdict(set)
    family_ancestries: dict[str, set[str]] = defaultdict(set)
    ancestry_families: dict[str, set[str]] = defaultdict(set)

    for i, row in enumerate(rows):
        result = row_gate.adjudicate(row)
        if not result["candidate_admission_pass"]:
            row_failures.append({
                "index": i,
                "source_path": row.get("__source_path") if isinstance(row, dict) else None,
                "source_line": row.get("__source_line") if isinstance(row, dict) else None,
                "failures": result["failures"],
            })
            failures.append(f"ROW_GATE_FAIL:{i}")
            continue

        family = row["family_id"]
        ancestry = row["provenance_ancestry_id"]
        split = row["split"]
        if split not in SPLITS:
            failures.append(f"INVALID_SPLIT:{i}")
            continue
        family_splits[family].add(split)
        ancestry_splits[ancestry].add(split)
        family_ancestries[family].add(ancestry)
        ancestry_families[ancestry].add(family)

    family_leaks = {
        k: sorted(v) for k, v in family_splits.items() if len(v) > 1
    }
    ancestry_leaks = {
        k: sorted(v) for k, v in ancestry_splits.items() if len(v) > 1
    }
    for family, splits in family_leaks.items():
        failures.append("FAMILY_SPLIT_LEAK:" + family + ":" + ",".join(splits))
    for ancestry, splits in ancestry_leaks.items():
        failures.append("PROVENANCE_ANCESTRY_SPLIT_LEAK:" + ancestry + ":" + ",".join(splits))

    # A connected family<->ancestry component must remain in one split. The
    # direct family/ancestry checks above already imply this mathematically,
    # but computing components makes the accepted split unit explicit and
    # guards future schema extensions from silently weakening the invariant.
    nodes: set[tuple[str, str]] = set()
    graph: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    node_splits: dict[tuple[str, str], set[str]] = defaultdict(set)
    for family, ancestries in family_ancestries.items():
        fn = ("family", family)
        nodes.add(fn)
        node_splits[fn].update(family_splits[family])
        for ancestry in ancestries:
            an = ("ancestry", ancestry)
            nodes.add(an)
            graph[fn].add(an)
            graph[an].add(fn)
            node_splits[an].update(ancestry_splits[ancestry])

    component_leaks: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for start in sorted(nodes):
        if start in seen:
            continue
        stack = [start]
        component: list[tuple[str, str]] = []
        splits: set[str] = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            component.append(node)
            splits.update(node_splits[node])
            stack.extend(graph[node] - seen)
        if len(splits) > 1:
            component_leaks.append({
                "nodes": [list(n) for n in sorted(component)],
                "splits": sorted(splits),
            })
            failures.append("CONNECTED_FAMILY_PROVENANCE_COMPONENT_SPLIT_LEAK")

    return {
        "schema": SCHEMA,
        "dataset_split_pass": not failures,
        "rows_total": len(rows),
        "rows_row_gate_pass": len(rows) - len(row_failures),
        "rows_row_gate_fail": len(row_failures),
        "row_failures": row_failures,
        "family_split_leaks": family_leaks,
        "provenance_ancestry_split_leaks": ancestry_leaks,
        "connected_component_split_leaks": component_leaks,
        "failures": sorted(set(failures)),
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": "Dataset-wide candidate leakage validation only; evidence-qualified canonical admission remains downstream.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("jsonl", nargs="+", type=Path)
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()
    result = adjudicate(_load_jsonl(args.jsonl))
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["dataset_split_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
