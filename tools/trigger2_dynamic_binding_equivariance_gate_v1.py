#!/usr/bin/env python3
"""Deterministic Trigger-2 dynamic-binding equivariance/leakage gate v1.

SOURCE/EVAL-ONLY. This gate audits the already-retained fully-factorial
`trigger2_dynamic_binding_blueprint_v2.py` v2.1 donor. It does not render ABI
atoms, admit training rows, execute a model, or mint J-Space/training credit.

The gate checks properties of the realized blueprint distribution rather than
assuming that deterministic/random-looking presentation is independent:

* causal target derivation from the episode-local class->symbol mapping;
* semantic-ablation projected-visible nuisance groups are exactly 3-way and
  target-balanced, giving optimal lookup accuracy exactly 1/3;
* all six codebook entry orders are crossed with invariant targets;
* all six S3 mappings x all six entry orders are crossed, with each target
  symbol occurring exactly 12 times per semantic episode/layout/polarity cell;
* both evidence/query layouts are crossed with invariant targets.

The semantic-ablation signature intentionally excludes hidden generation
metadata (`split`, `t`, `c`, mapping indices) and excludes semantic evidence.
It retains only the projected model-visible codebook, layout and query. This is
still BLUEPRINT-SCOPE evidence: the final serialized Xeno/ClayCode renderer,
exact ABI atoms and tokenizer/input identity require separate gates.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BLUEPRINT_PATH = Path(__file__).with_name("trigger2_dynamic_binding_blueprint_v2.py")
GATE_SCHEMA = "CLAY_TRIGGER2_DYNAMIC_BINDING_EQUIVARIANCE_GATE/v1"


def _load_blueprint_module():
    spec = importlib.util.spec_from_file_location("trigger2_dynamic_binding_blueprint_v2", BLUEPRINT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load blueprint module: {BLUEPRINT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ordered_codebook(row: dict[str, Any], classes: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((classes[i], row["sym"][row["perm"][i]]) for i in row["ord"])


def audit_rows(rows: list[dict[str, Any]], blueprint=None) -> dict[str, Any]:
    bp = blueprint or _load_blueprint_module()
    classes = tuple(bp.CLASSES)
    perms = set(tuple(x) for x in bp.PERMS)
    layouts = set(bp.LAYOUTS)
    failures: list[str] = []

    if not rows:
        return {
            "schema": GATE_SCHEMA,
            "pass": False,
            "failures": ["EMPTY_ROWS"],
            "training_eligible": False,
        }

    # 1) Exact causal target and factor validity.
    for i, row in enumerate(rows):
        try:
            ci = classes.index(row["c"])
            expected_target = row["sym"][row["perm"][ci]]
        except Exception as exc:
            failures.append(f"MALFORMED_ROW:{i}:{type(exc).__name__}")
            continue
        if row.get("target") != expected_target:
            failures.append(f"TARGET_DERIVATION_MISMATCH:{i}")
        if tuple(row.get("perm", ())) not in perms:
            failures.append(f"INVALID_MAPPING_PERMUTATION:{i}")
        if tuple(row.get("ord", ())) not in perms:
            failures.append(f"INVALID_CODEBOOK_ORDER:{i}")
        if row.get("lay") not in layouts:
            failures.append(f"INVALID_LAYOUT:{i}")

    # 2) Model-visible semantic-ablation challenger at BLUEPRINT projection scope.
    # The exact production renderer must later reproduce this gate over serialized bytes.
    ablation_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        signature = (
            _ordered_codebook(row, classes),
            row["lay"],
            row["q"],
        )
        ablation_groups[signature].append(row)

    nuisance_lookup_correct = 0
    for members in ablation_groups.values():
        if len(members) != len(classes):
            failures.append(f"ABLATION_GROUP_SIZE:{len(members)}")
            continue
        target_counts = Counter(x["target"] for x in members)
        expected_symbols = set(members[0]["sym"])
        if set(target_counts) != expected_symbols or set(target_counts.values()) != {1}:
            failures.append(f"ABLATION_TARGET_BALANCE:{dict(target_counts)}")
        nuisance_lookup_correct += max(target_counts.values())

    nuisance_lookup_accuracy = nuisance_lookup_correct / len(rows)
    chance = 1.0 / len(classes)
    if abs(nuisance_lookup_accuracy - chance) > 1e-12:
        failures.append(f"NUISANCE_LOOKUP_ACCURACY:{nuisance_lookup_accuracy:.17g}!=CHANCE:{chance:.17g}")

    # 3) Codebook-order invariance: same mapping/semantics must cross all six orders.
    order_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["split"], row["t"], tuple(row["sym"]), tuple(row["perm"]),
            row["lay"], row["c"], row["p"],
        )
        order_groups[key].append(row)
    for members in order_groups.values():
        if len(members) != len(perms) or {tuple(x["ord"]) for x in members} != perms:
            failures.append(f"ORDER_CROSSING_INCOMPLETE:{len(members)}")
        if len({x["target"] for x in members}) != 1:
            failures.append("ORDER_CHANGED_TARGET")

    # 4) S3 mapping equivariance + mapping/order full crossing.
    mapping_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row["split"], row["t"], tuple(row["sym"]), row["lay"], row["c"], row["p"])
        mapping_groups[key].append(row)
    expected_mapping_order_rows = len(perms) * len(perms)
    expected_target_count = expected_mapping_order_rows // len(classes)
    for members in mapping_groups.values():
        if len(members) != expected_mapping_order_rows:
            failures.append(f"MAPPING_ORDER_CELL_SIZE:{len(members)}")
            continue
        if {tuple(x["perm"]) for x in members} != perms:
            failures.append("MAPPING_COVERAGE_INCOMPLETE")
        target_counts = Counter(x["target"] for x in members)
        if set(target_counts) != set(members[0]["sym"]) or set(target_counts.values()) != {expected_target_count}:
            failures.append(f"MAPPING_EQUIVARIANCE_TARGET_BALANCE:{dict(target_counts)}")

    # 5) Evidence/query layout is a nuisance: target must be invariant across both layouts.
    layout_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["split"], row["t"], tuple(row["sym"]), tuple(row["perm"]),
            tuple(row["ord"]), row["c"], row["p"],
        )
        layout_groups[key].append(row)
    for members in layout_groups.values():
        if len(members) != len(layouts) or {x["lay"] for x in members} != layouts:
            failures.append(f"LAYOUT_CROSSING_INCOMPLETE:{len(members)}")
        if len({x["target"] for x in members}) != 1:
            failures.append("LAYOUT_CHANGED_TARGET")

    return {
        "schema": GATE_SCHEMA,
        "pass": not failures,
        "failures": failures[:200],
        "failure_count": len(failures),
        "rows": len(rows),
        "ablation_groups": len(ablation_groups),
        "ablation_expected_group_size": len(classes),
        "nuisance_lookup_accuracy": nuisance_lookup_accuracy,
        "chance_accuracy": chance,
        "order_groups": len(order_groups),
        "mapping_equivariance_groups": len(mapping_groups),
        "layout_groups": len(layout_groups),
        "scope": "DETERMINISTIC_BLUEPRINT_DISTRIBUTION_ONLY",
        "rendered_byte_gate_required": True,
        "exact_abi_tokenizer_gate_required": True,
        "model_behavior_credit": 0,
        "jspace_credit": 0,
        "accepted_dataset_tokens": 0,
        "training_credit": 0,
        "training_eligible": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    bp = _load_blueprint_module()
    report = audit_rows(list(bp.build_rows()), bp)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
