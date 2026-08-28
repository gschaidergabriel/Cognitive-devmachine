#!/usr/bin/env python3
"""Selects a balanced B1 TRAIN mix-tier from the full B1 factorial pool.

Context: chatgpt-secondary review (2026-08-26, conversation c/6a8ed518), requested
by claude-code-lead after materializing the full B1 pool
(tools/trigger2_b1_binding_materializer_v1.py, 9072 rows). Verbatim recommendation:

  "6912 as final train share: RED. 2304 balanced subset: GREEN-CANDIDATE after its
  own audit." Reasoning: if "10k training examples" means gradient-bearing TRAIN
  rows, 6912 B1 rows would be 69% of the whole mix -- pool size would silently
  become loss weighting, and B1 would outvote the sibling families (B2/B3, B4/B5,
  B6) purely by repetition, not by any actual difficulty/information argument.

Selection rule (as specified by chatgpt-secondary, reproduced here in code):
  - Mapping (6x S3): causally essential for arbitrary local binding -- keep full.
  - Codebook order (6x S3): mostly nuisance/invariance presentation -- reduce here
    first, from 6 to 2 orders per (template, triplet) structural cell.
  - Layout (2), class (3), polarity (2), templates (4), triplets (4): keep full.
  - Explicit constraint: do NOT couple mapping and order selection (e.g. never
    derive "which order" from "which mapping index" -- that would silently reduce
    mapping diversity at each surviving order and reintroduce exactly the kind of
    structural correlation the corrected leakage audit had to rule out). For every
    surviving order in a cell, all six mappings remain fully crossed.

  4 templates x 4 triplets x 6 mappings x 2 selected orders x 2 layouts x 3 classes
  x 2 polarities = 2304.

VALIDATION (1728) and HOLDOUT_FROZEN (432) are left completely untouched per the
same recommendation: they carry no gradient, so pool-size dominance does not apply,
and the full factorial there is valuable precisely because it can detect whether
the reduced TRAIN mix actually learned S3/order generalization rather than a
sampling artifact.

CORRECTION during implementation (same session, caught by this tool's own
fail-closed re-audit before anything was written -- not by chatgpt-secondary this
time): the originally-specified selection key was (template, triplet), rotating by
cell_index % 6 across the 16 (template, triplet) cells. Running the mandatory
reduced-set re-audit on that version FAILED: within TRAIN, I(target;order) = 0.079
bits and I(target;order x template) = 1.5 bits, both nonzero. Root cause: every
symbol is unique to exactly one triplet (triplets are disjoint by construction), so
the target symbol deterministically reveals which triplet produced it; keying the
order-pair choice by (template, triplet) therefore let the target symbol partially
predict which 2 orders were used in its own cell -- a real, measurable, WITHIN-TRAIN
leak, not a false positive. This is exactly the confound chatgpt-secondary warned
about, just introduced one level down from where they warned about it (they warned
against keying on mapping; keying on triplet has the same effect via a different
visible-vs-hidden channel).

SECOND ATTEMPT, also caught by the same re-audit before writing: keying the
order-pair by (class, polarity, layout) instead removed the target/triplet leak but
introduced a different one -- since order-pair became a near-bijective function of
class specifically, MI(class; order x layout) and MI(class; order x polarity) both
became large (~0.58 bits). class directly co-determines target
(target = triple[perm[class_index]]), so making a nuisance field (order) an
informative proxy for class defeats the entire point of counterbalancing, even
though class is separately visible in the prompt text -- two redundant channels
predicting the same semantic quantity is exactly the failure mode this audit exists
to catch, not a false alarm.

FINAL fix: the order-pair is keyed ONLY by TEMPLATE (4 values, not template x
triplet and not class/polarity/layout). This is the one grouping variable that is
PROVABLY marginally independent of target within TRAIN: every TRAIN template is
crossed with every triplet, every mapping, every class, every polarity and every
layout (see build_rows()/the blueprint's own selftest, and this audit's own
template_baseline_mi_bits, which was already 0 for the full pool). Since order-pair
is a deterministic function of template alone, and template carries zero marginal
information about target, order can carry no information about target either
(I(target;order) <= I(target;template) = 0, by the data-processing inequality --
verified numerically anyway rather than relied upon). template_index 0..3 selects
start = template_index % 4, kept orders = {start, (start + 3) % 6} (four of the
resulting six possible order values are used as first slot; start=3 lands on the
pair {3,0}, which coincides with template_index 0's pair {0,3} -- not perfectly
even coverage across all six orders, but every order still appears at least once
and, crucially, with zero measured target/class leakage -- see the re-audit output
for the exact coverage counts rather than assuming even distribution here.

The reduced set is NOT training-eligible any more than the full pool was: same
placeholder-atom / no-tokenizer-binding boundary applies. It is a candidate
TRAIN-mix-tier selection, subject to the SAME leakage-audit rigor as the full pool
-- this tool refuses to write output if the reduced set does not pass a rerun of
every leakage-audit-v1.1 check, exactly like the materializer's fail-closed gate.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trigger2_dynamic_binding_blueprint_v2 as bp  # noqa: E402
import trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1 as audit  # noqa: E402
import trigger2_b1_binding_materializer_v1 as materializer  # noqa: E402

SCHEMA = "CLAY_TRIGGER2_B1_TRAIN_BALANCED_2ORDER_SELECTION/v1"
ANCESTRY = "trigger2-20260826-b1-train-balanced-2order-v1"
ORDERS_KEPT_PER_CELL = 2


def cell_order_selection() -> dict[str, set[int]]:
    """Returns {template: {order_index, order_index}} for the 4 TRAIN templates,
    using the template-index-mod-4 opposite-pair rule. Deliberately independent of
    triplet/class/polarity/layout/mapping -- see module CORRECTION docstring for
    why keying on (template, triplet) and on (class, polarity, layout) both leaked."""
    selection = {}
    for template_index, t in enumerate(bp.TRAIN_TEMPLATES):
        start = template_index % 4
        selection[t] = {start, (start + 3) % 6}
    return selection


def select_balanced_train(rows: list[dict]) -> list[dict]:
    selection = cell_order_selection()
    kept = []
    for r in rows:
        if r["split"] != "TRAIN":
            continue
        order_index = _order_index_of(r["ord"])
        if order_index in selection[r["t"]]:
            kept.append(r)
    return kept


def _order_index_of(order_tuple_as_list: list[int]) -> int:
    return bp.PERMS.index(tuple(order_tuple_as_list))


def build_full_and_reduced() -> tuple[list[dict], list[dict], dict]:
    rows = bp.build_rows()
    train_reduced = select_balanced_train(rows)
    non_train = [r for r in rows if r["split"] != "TRAIN"]
    reduced_rows = train_reduced + non_train

    selection = cell_order_selection()
    order_coverage = Counter()
    for orders in selection.values():
        for o in orders:
            order_coverage[o] += 1

    stats = {
        "cells": len(selection),
        "orders_kept_per_cell": ORDERS_KEPT_PER_CELL,
        "order_coverage_across_cells": dict(sorted(order_coverage.items())),
        "train_rows_full": sum(1 for r in rows if r["split"] == "TRAIN"),
        "train_rows_reduced": len(train_reduced),
        "validation_rows": sum(1 for r in rows if r["split"] == "VALIDATION"),
        "holdout_rows": sum(1 for r in rows if r["split"] == "HOLDOUT_FROZEN"),
    }
    return rows, reduced_rows, stats


def audit_reduced(reduced_rows: list[dict]) -> dict:
    """Rerun every leakage-audit-v1.1 check against the reduced row set directly
    (not the full 9072), so the reduction itself is empirically verified, not just
    argued for."""
    rendered = []
    for row in reduced_rows:
        eq_text, full = audit.render_prompt(row)
        rendered.append({"row": row, "split": row["split"], "eq_text": eq_text, "full_prompt": full})

    checks = {
        "uniqueness": audit.check_uniqueness(rendered),
        "cross_split_disjointness": audit.check_cross_split_disjointness(rendered),
        "text_conditional_target_uniformity": audit.check_text_conditional_target_uniformity(rendered),
        "higher_order_joint_mi": audit.check_higher_order_joint_mi(reduced_rows),
        "intended_split_support_shift": audit.check_intended_split_support_shift(reduced_rows),
        "bag_of_words_shortcut_probe": audit.bow_shortcut_probe(rendered),
    }

    # extra check specific to this reduction: within TRAIN, order must still carry
    # zero information about target (it never determined target to begin with, but
    # confirm explicitly on the REDUCED set, not just inherited from the full pool),
    # and mapping must remain fully represented (all 6 values) at every surviving
    # order value -- the actual "did we accidentally couple mapping and order" test.
    train_rows = [r for r in reduced_rows if r["split"] == "TRAIN"]
    order_mi = audit.mi(train_rows, lambda r: r["target"], lambda r: tuple(r["ord"]))
    mapping_by_order: dict[tuple, set] = {}
    for r in train_rows:
        mapping_by_order.setdefault(tuple(r["ord"]), set()).add(tuple(r["perm"]))
    all_mappings_present_at_every_order = all(
        mappings == set(bp.PERMS) for mappings in mapping_by_order.values()
    )
    checks["order_mapping_decoupling"] = {
        "order_target_mi_bits": order_mi,
        "distinct_orders_present_in_train": len(mapping_by_order),
        "all_six_mappings_present_at_every_surviving_order": all_mappings_present_at_every_order,
        "pass": abs(order_mi) < 1e-9 and all_mappings_present_at_every_order,
    }

    overall_pass = all(c.get("pass") for c in checks.values())
    return {"checks": checks, "overall_pass": overall_pass}


def run(fail_closed: bool = True) -> tuple[list[dict], dict, dict]:
    _full_rows, reduced_rows, stats = build_full_and_reduced()
    reduced_audit = audit_reduced(reduced_rows)
    if fail_closed and not reduced_audit["overall_pass"]:
        raise SystemExit(
            "REFUSING to write B1 balanced-2order selection: reduced-set audit did "
            "not pass. See reduced_audit for details."
        )
    materialized = [materializer.materialize_row(r) for r in reduced_rows]
    for r in materialized:
        r["schema"] = SCHEMA
        r["provenance_ancestry_id"] = ANCESTRY
        r["mix_tier"] = "B1_BALANCED_2ORDER" if r["split"] == "TRAIN" else r["split"]
    return materialized, reduced_audit, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--audit-out", type=Path)
    ap.add_argument("--report-out", type=Path)
    ap.add_argument("--no-fail-closed", action="store_true")
    args = ap.parse_args()

    materialized, reduced_audit, stats = run(fail_closed=not args.no_fail_closed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as f:
        for r in materialized:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    output_sha256 = hashlib.sha256(args.out.read_bytes()).hexdigest()

    report = {
        "schema": SCHEMA,
        "rows_total": len(materialized),
        "split_counts": dict(Counter(r["split"] for r in materialized)),
        "selection_stats": stats,
        "reduced_audit_overall_pass": reduced_audit["overall_pass"],
        "output_path": str(args.out),
        "output_sha256": output_sha256,
        "output_bytes": args.out.stat().st_size,
        "training_eligible": False,
        "reason_training_eligible_false": "placeholder ABI_ACCEPTED_ORDINAL atoms, no real tokenizer/atom-manifest binding, no admission gate run -- candidate/quarantined only per TRIGGERWORT_2 course Step 6.",
    }
    if args.audit_out:
        args.audit_out.write_text(json.dumps(reduced_audit, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.report_out:
        args.report_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if reduced_audit["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
