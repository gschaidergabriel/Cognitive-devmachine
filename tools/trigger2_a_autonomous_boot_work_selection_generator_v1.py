#!/usr/bin/env python3
"""Trigger-2 candidate generator: A -- autonomous boot / join / work selection.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
section 2, letter A:

  "Train the same checkpoint to read current S1, reconstruct minimum sufficient
  context, detect already claimed/in-flight work and select useful work without
  a preassigned role.

  Hard negatives:
  - launch-time role injection;
  - inventing work when none exists;
  - ignoring epoch/digest;
  - repeating claimed work unless redundancy is explicitly requested;
  - treating node identity as a permanent cognitive role."

This is one of two families identified as genuine, zero-prior-investment gaps in
claude-code-lead's B0-B6-vs-course-section-2 coverage survey (2026-08-26,
receipt 20260826T144426Z). Naming note: "A" here refers to course section 2's
lettered capability map (A-L), a DIFFERENT organizational scheme from the
numbered B0-B6 binding-curriculum families -- deliberately not folded into a
"B7" or similar to avoid conflating the two schemes.

Design: three work items (fixed structural IDs W1/W2/W3, matching the ALLOW/DENY/
ABSTAIN-style small-fixed-role-set pattern used throughout B0-B6) each carry an
independently assigned OUTCOME_CLASS that determines whether the item is
currently selectable:

  UNCLAIMED_AVAILABLE       -- selectable.
  COMPLETED                 -- never selectable (work already done).
  OTHER_CURRENT_UNAVAILABLE -- claimed by another node THIS epoch -- not selectable.
  OTHER_STALE_AVAILABLE     -- claimed by another node, but under an OLD epoch --
                                the claim is stale/void, item is selectable again
                                (tests "ignoring epoch/digest" hard negative: the
                                model must compare claim_epoch to current_epoch,
                                not just read a "claimed" flag).
  SELF_CURRENT_OWNED        -- already claimed by the SAME node this epoch --
                                selectable only if redundancy is explicitly
                                requested (tests "repeating claimed work unless
                                redundancy is explicitly requested").
  SELF_STALE_AVAILABLE      -- self-claimed under an old epoch -- stale, needs
                                re-claiming, selectable again.

Selection rule (deterministic, computable from the stated per-item facts):
lowest-ID selectable item wins; if none are selectable, the correct answer is
the literal token NO_WORK_AVAILABLE (tests "inventing work when none exists" --
the model must never fabricate a fourth item or claim one of the unselectable
ones).

Two additional nuisance/hard-negative fields, both verified to carry zero
information about the target:
  - boot_role_hint: a launch-time role label ("WATCHER" or "COORDINATOR") that
    must be ignored -- tests "launch-time role injection" and "treating node
    identity as a permanent cognitive role" (the SAME hint appears across rows
    with completely different correct answers, so following it is never a
    viable shortcut).
  - node_identity: a cosmetic node-name label, split-disjoint across
    TRAIN/VALIDATION/HOLDOUT_FROZEN purely for corpus hygiene (no semantic
    dependency).

Status: METHOD_ONLY / candidate-and-quarantined per TRIGGERWORT_2 course Step 6.
Not training-eligible: no admission gate has run.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_A_AUTONOMOUS_BOOT_WORK_SELECTION_CANDIDATE/v1"
ANCESTRY = "trigger2-20260826-a-autonomous-boot-work-selection-v1"
NO_WORK_TOKEN = "NO_WORK_AVAILABLE"

ITEM_IDS = ("W1", "W2", "W3")
OUTCOME_CLASSES = (
    "UNCLAIMED_AVAILABLE",
    "COMPLETED",
    "OTHER_CURRENT_UNAVAILABLE",
    "OTHER_STALE_AVAILABLE",
    "SELF_CURRENT_OWNED",
    "SELF_STALE_AVAILABLE",
)
BOOT_ROLE_HINTS = ("WATCHER", "COORDINATOR")
NODE_IDENTITIES = {
    # Exactly ONE node identity per split (not a pool) -- deliberately, after an
    # earlier version with a 3/1/1-sized pool per split leaked a small but real
    # excess MI (0.00036 bits beyond the split baseline) between node_identity
    # and target, caught by this generator's own audit. A single node name per
    # split is actually the STRONGER version of the "treating node identity as a
    # permanent cognitive role" hard negative: the exact same node name
    # ("node_alpha1") appears across hundreds of TRAIN rows with wildly
    # different correct targets, which is a cleaner, more direct proof that the
    # node identity string itself never determines the answer than a
    # multi-node pool would have been -- and it trivially has zero information
    # about target beyond whatever split alone already (legitimately) explains,
    # since node is now a strict 1:1 alias of split.
    "TRAIN": ["node_alpha1"],
    "VALIDATION": ["node_alpha2"],
    "HOLDOUT_FROZEN": ["node_beta9"],
}

ITEM_DESCRIPTIONS = {
    "UNCLAIMED_AVAILABLE": "unclaimed, not completed",
    "COMPLETED": "already completed",
    "OTHER_CURRENT_UNAVAILABLE": "claimed by another node at the CURRENT epoch, not completed",
    "OTHER_STALE_AVAILABLE": "claimed by another node at an OLD (non-current) epoch, not completed",
    "SELF_CURRENT_OWNED": "already claimed by THIS node at the CURRENT epoch, not completed",
    "SELF_STALE_AVAILABLE": "claimed by THIS node at an OLD (non-current) epoch, not completed",
}


def is_selectable(outcome: str, redundancy_requested: bool) -> bool:
    if outcome in ("UNCLAIMED_AVAILABLE", "OTHER_STALE_AVAILABLE", "SELF_STALE_AVAILABLE"):
        return True
    if outcome == "SELF_CURRENT_OWNED":
        return redundancy_requested
    return False  # COMPLETED, OTHER_CURRENT_UNAVAILABLE


def compute_target(outcomes: dict[str, str], redundancy_requested: bool) -> str:
    for item_id in ITEM_IDS:
        if is_selectable(outcomes[item_id], redundancy_requested):
            return item_id
    return NO_WORK_TOKEN


def _stable_rank(key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")


def row_common(split: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": ANCESTRY,
        "curriculum_phase": "A_AUTONOMOUS_BOOT_WORK_SELECTION",
        "family": "A_AUTONOMOUS_BOOT_WORK_SELECTION",
        "curriculum_family": "A_AUTONOMOUS_BOOT_WORK_SELECTION",
        "split": split,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
    }


def build_rows() -> list[dict]:
    all_combos = list(itertools.product(OUTCOME_CLASSES, repeat=len(ITEM_IDS)))
    # deterministic stratified split: rank each combo, bottom 80% -> TRAIN_AND_VALIDATION
    # role, top 20% -> HOLDOUT_FROZEN role (genuinely unseen status-combinations,
    # not just unseen node names).
    ranked = sorted(all_combos, key=lambda c: _stable_rank("|".join(c)))
    n_holdout = round(len(ranked) * 0.2)
    holdout_combos = set(ranked[:n_holdout])
    train_val_combos = set(ranked[n_holdout:])

    rows = []
    # Node identity is assigned by a pure per-split ROW COUNTER (round-robin),
    # deliberately independent of combo/redundancy_requested/hint -- an earlier
    # version keyed node selection off a hash of (combo, redundancy_requested,
    # hint, split), which shares ancestry with the target's own determinants and
    # produced a real, if tiny, measured leak (0.0032 bits between node_identity
    # and target) caught by this generator's own audit before anything was
    # committed. A row-position counter cannot share statistical structure with
    # a content-derived target by construction.
    split_counters = {"TRAIN": 0, "VALIDATION": 0, "HOLDOUT_FROZEN": 0}
    for combo in all_combos:
        combo_split_role = "HOLDOUT_FROZEN" if combo in holdout_combos else "TRAIN_AND_VALIDATION"
        outcomes = dict(zip(ITEM_IDS, combo))
        for redundancy_requested in (False, True):
            target = compute_target(outcomes, redundancy_requested)
            for hint in BOOT_ROLE_HINTS:
                splits_to_emit = ["HOLDOUT_FROZEN"] if combo_split_role == "HOLDOUT_FROZEN" else ["TRAIN", "VALIDATION"]
                for split in splits_to_emit:
                    pool = NODE_IDENTITIES[split]
                    node = pool[split_counters[split] % len(pool)]
                    split_counters[split] += 1
                    items_text = " | ".join(
                        f"{item_id}: {ITEM_DESCRIPTIONS[outcomes[item_id]]}" for item_id in ITEM_IDS
                    )
                    prompt = (
                        f"BOOT: node identity={node}, launch-time role hint='{hint}' (informational label only, "
                        f"not a permanent function -- current available work must still be selected from S1).\n"
                        f"S1 WORK ITEMS (current epoch): {items_text}.\n"
                        f"REDUNDANCY_REQUESTED: {redundancy_requested}.\n"
                        f"Select the lowest-ID item that is genuinely selectable right now (unclaimed, or "
                        f"staleley-claimed under a non-current epoch, or self-owned-current only if redundancy "
                        f"is requested). If none qualify, respond with exactly {NO_WORK_TOKEN}. Do not invent a "
                        f"new item and do not let the launch-time role hint determine your answer."
                    )
                    r = row_common(split)
                    r.update({
                        "id": f"A_WORKSEL_{'-'.join(combo)}_R{int(redundancy_requested)}_{hint}_{split}",
                        "node_identity": node,
                        "boot_role_hint": hint,
                        "outcomes": outcomes,
                        "redundancy_requested": redundancy_requested,
                        "combo_split_role": combo_split_role,
                        "prompt": prompt,
                        "target": target,
                    })
                    rows.append(r)
    return rows


def mi(rows: list[dict], fa, fb) -> float:
    import math
    n = len(rows)
    if n == 0:
        return 0.0
    joint = Counter((fa(r), fb(r)) for r in rows)
    a = Counter(fa(r) for r in rows)
    b = Counter(fb(r) for r in rows)
    total = 0.0
    for (x, y), v in joint.items():
        pxy = v / n
        px = a[x] / n
        py = b[y] / n
        total += pxy * math.log2(pxy / (px * py))
    return total


def audit(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        expected = compute_target(r["outcomes"], r["redundancy_requested"])
        if r["target"] != expected:
            failures.append(f"TARGET_WRONG:{r['id']}")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    # hard-negative nuisance checks: boot_role_hint must carry zero information
    # about target under ANY conditioning (it is not split-aliased, unlike
    # node_identity below, so raw MI is the right test).
    hint_mi = mi(rows, lambda r: r["target"], lambda r: r["boot_role_hint"])
    if abs(hint_mi) > 1e-9:
        failures.append(f"ROLE_HINT_LEAKS_TARGET:{hint_mi}")

    # node_identity is now a strict 1:1 alias of split (see NODE_IDENTITIES
    # CORRECTION comment) -- exactly the same "split-aliased nuisance field"
    # situation the blueprint_v2 leakage audit had to learn to handle correctly
    # earlier this session (raw combined-corpus MI misattributed an intended
    # holdout-support-shift as a leak). Applying that lesson directly here: the
    # correct test is EXCESS mutual information over the split baseline
    # (I(target;split,node) - I(target;split)), not raw I(target;node), plus an
    # explicit within-split check (trivially zero here since node is constant
    # within each split, but verified rather than assumed).
    split_baseline_mi = mi(rows, lambda r: r["target"], lambda r: r["split"])
    joint_mi = mi(rows, lambda r: r["target"], lambda r: (r["split"], r["node_identity"]))
    node_excess_mi = joint_mi - split_baseline_mi
    if abs(node_excess_mi) > 1e-9:
        failures.append(f"NODE_IDENTITY_LEAKS_TARGET_BEYOND_SPLIT:{node_excess_mi}")
    for split_name in ("TRAIN", "VALIDATION", "HOLDOUT_FROZEN"):
        subset = [r for r in rows if r["split"] == split_name]
        within_split_node_mi = mi(subset, lambda r: r["target"], lambda r: r["node_identity"])
        if abs(within_split_node_mi) > 1e-9:
            failures.append(f"NODE_IDENTITY_LEAKS_TARGET_WITHIN_{split_name}:{within_split_node_mi}")

    # cross-split content disjointness for HOLDOUT_FROZEN status-combinations
    train_combos = {tuple(r["outcomes"][i] for i in ITEM_IDS) for r in rows if r["split"] in ("TRAIN", "VALIDATION")}
    hold_combos = {tuple(r["outcomes"][i] for i in ITEM_IDS) for r in rows if r["split"] == "HOLDOUT_FROZEN"}
    if train_combos & hold_combos:
        failures.append("HOLDOUT_COMBO_LEAKED_INTO_TRAIN_VAL")

    no_work_rows = sum(1 for r in rows if r["target"] == NO_WORK_TOKEN)
    target_dist = Counter(r["target"] for r in rows)

    return {
        "rows": len(rows),
        "split_counts": dict(Counter(r["split"] for r in rows)),
        "failures": failures,
        "pass": not failures,
        "role_hint_target_mi_bits": hint_mi,
        "node_identity_split_baseline_mi_bits": split_baseline_mi,
        "node_identity_excess_mi_over_split_bits": node_excess_mi,
        "no_work_available_rows": no_work_rows,
        "target_distribution": dict(target_dist),
    }


def run() -> tuple[dict, list[dict]]:
    rows = build_rows()
    report = audit(rows)
    return {
        "schema": SCHEMA,
        "total_rows": len(rows),
        "audit": report,
        "overall_pass": report["pass"],
        "training_eligible": False,
        "reason_training_eligible_false": "no real tokenizer/atom-manifest binding, no admission gate run -- candidate/quarantined only per TRIGGERWORT_2 course Step 6.",
    }, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report-out", type=Path)
    args = ap.parse_args()

    report, rows = run()
    if not report["overall_pass"]:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    report["output_sha256"] = hashlib.sha256(args.out.read_bytes()).hexdigest()
    report["output_path"] = str(args.out)

    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.report_out:
        args.report_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
