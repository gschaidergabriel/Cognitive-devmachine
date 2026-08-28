#!/usr/bin/env python3
"""Trigger-2 candidate generator: G -- recursive coordinator compression.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
section 2, letter G:

  "Train lower-scope integration and higher-scope compressed summaries while
  preserving retrievable evidence refs, unknowns and branch topology. Higher
  coordinators must not require every raw worker packet in hot context."

The other of two families identified as genuine, zero-prior-investment gaps in
claude-code-lead's B0-B6-vs-course-section-2 coverage survey (2026-08-26,
receipt 20260826T144426Z). Naming note: as with family A, "G" refers to course
section 2's lettered capability map, a different scheme from the numbered B0-B6
binding curriculum.

Design: three LOWER-SCOPE coordinators (fixed structural roles SCOPE_X/SCOPE_Y/
SCOPE_Z) have each already compressed their own raw worker packets into a small
summary: {evidence_refs: [...], unknown_count, branch_count}. The prompt gives
ONLY these three summaries -- never raw worker packets -- structurally proving
"higher coordinators must not require every raw worker packet in hot context"
by construction (there is nothing else to read).

Two families:

REF_UNION_PRESERVATION
  The higher-scope coordinator's job is to report the complete UNION of
  evidence refs across all three lower scopes. A decoy "already-rolled-up"
  summary is also stated, which in about half the rows correctly matches the
  true union (control) and in the other half DROPS one or more real refs
  (adversarial -- tests "preserving retrievable evidence refs": the target must
  always be the full recomputed union, never the decoy's under-count).

TOPOLOGY_AND_UNKNOWN_PRESERVATION
  The higher-scope coordinator must report the TOTAL preserved branch count
  (sum across scopes -- branches from different scopes are never silently
  collapsed into fewer branches, echoing section H's anti-collapse law applied
  recursively) and the TOTAL unknown count (sum -- unknowns are never quietly
  resolved away during compression). A decoy rollup sometimes collapses branch
  count (claims fewer total branches than the sum) or drops unknowns (claims
  fewer total unknowns), and sometimes matches exactly (control).

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

SCHEMA = "CLAY_TRIGGER2_G_RECURSIVE_COORDINATOR_COMPRESSION_CANDIDATE/v1"
ANCESTRY = "trigger2-20260826-g-recursive-coordinator-compression-v1"

SCOPES = ("SCOPE_X", "SCOPE_Y", "SCOPE_Z")
# Coordinator session label, one fixed value per split (pure split alias, same
# pattern used in tools/trigger2_a_autonomous_boot_work_selection_generator_v1.py
# after that generator's own audit caught a real leak from a multi-value node
# pool). TRAIN and VALIDATION intentionally reuse the same underlying
# ref/topology combinatorics (matching blueprint_v2's train==validation-pool
# convention), so without SOME split-distinguishing text the two would render
# byte-identical prompts -- this field exists purely to make that distinction
# visible in the rendered text, and being a strict split alias it cannot add
# any information about target beyond what split legitimately already
# contributes (verified by the same excess-over-split-baseline check used in
# the sibling A generator).
SESSION_LABEL = {"TRAIN": "session_train1", "VALIDATION": "session_val1", "HOLDOUT_FROZEN": "session_hold1"}
REF_POOL = ("EV1", "EV2", "EV3", "EV4", "EV5", "EV6")
# each scope gets a fixed-size-2 subset of the ref pool, chosen from a small
# enumerated set of subsets so the corpus stays combinatorially bounded.
REF_SUBSETS = tuple(itertools.combinations(REF_POOL, 2))  # 15 subsets of size 2
UNKNOWN_COUNTS = (0, 1, 2)
BRANCH_COUNTS = (1, 2, 3)


def _stable_rank(key: str) -> int:
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")


def row_common(family: str, split: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": ANCESTRY,
        "curriculum_phase": "G_RECURSIVE_COORDINATOR_COMPRESSION",
        "family": family,
        "curriculum_family": family,
        "split": split,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
    }


def _split_role_for_key(key: str) -> str:
    return "HOLDOUT_FROZEN" if (_stable_rank(key) % 5 == 0) else "TRAIN_AND_VALIDATION"


# ---------------------------------------------------------------------------
# REF_UNION_PRESERVATION
# ---------------------------------------------------------------------------

def build_ref_union_rows() -> list[dict]:
    rows = []
    # bound the combinatorics: 15 subsets per scope would be 15^3=3375; instead
    # deterministically select a manageable number of (scope-subset) triples via
    # stable ranking, keeping the family a comparable scale to sibling families.
    all_subset_indices = list(range(len(REF_SUBSETS)))
    chosen_triples = [
        (i, j, k)
        for i in all_subset_indices
        for j in all_subset_indices
        for k in all_subset_indices
        if _stable_rank(f"REFTRIPLE|{i}|{j}|{k}") % 23 == 0
    ]
    for triple_idx, (i, j, k) in enumerate(chosen_triples):
        refs = {"SCOPE_X": REF_SUBSETS[i], "SCOPE_Y": REF_SUBSETS[j], "SCOPE_Z": REF_SUBSETS[k]}
        true_union = sorted(set(refs["SCOPE_X"]) | set(refs["SCOPE_Y"]) | set(refs["SCOPE_Z"]))
        triple_key = f"reftriple:{i}:{j}:{k}"
        split_role = _split_role_for_key(triple_key)
        for decoy_mode in ("MATCHES", "DROPS_ONE"):
            if decoy_mode == "MATCHES":
                decoy_union = list(true_union)
            else:
                if not true_union:
                    continue  # nothing to drop
                drop_idx = _stable_rank(triple_key + "|drop") % len(true_union)
                decoy_union = [r for idx, r in enumerate(true_union) if idx != drop_idx]
            summary_text = " | ".join(f"{s}: evidence_refs=[{', '.join(refs[s])}]" for s in SCOPES)
            decoy_text = f"[already-rolled-up, unverified]: evidence_refs=[{', '.join(decoy_union)}]"
            splits_to_emit = ["HOLDOUT_FROZEN"] if split_role == "HOLDOUT_FROZEN" else ["TRAIN", "VALIDATION"]
            for split in splits_to_emit:
                prompt = (
                    f"Coordinator session {SESSION_LABEL[split]}. Lower-scope summaries (no raw worker "
                    f"packets available, only these compressed summaries): {summary_text}.\n"
                    f"A prior rollup claims: {decoy_text}.\n"
                    "As the higher-scope coordinator, report the COMPLETE union of evidence refs across "
                    "all three scopes, recomputed from the scope summaries -- do not trust the prior "
                    "rollup if it is incomplete. Respond with a comma-separated sorted list of ref IDs."
                )
                r = row_common("G_REF_UNION_PRESERVATION", split)
                r.update({
                    "id": f"G_REFUNION_{triple_idx}_{decoy_mode}_{split}",
                    "refs_by_scope": {s: list(refs[s]) for s in SCOPES},
                    "decoy_union": decoy_union,
                    "decoy_matches_true_union": decoy_union == true_union,
                    "prompt": prompt,
                    "target": ", ".join(true_union),
                })
                rows.append(r)
    return rows


def audit_ref_union(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        true_union = sorted(set().union(*[set(v) for v in r["refs_by_scope"].values()]))
        if r["target"] != ", ".join(true_union):
            failures.append(f"TARGET_NOT_TRUE_UNION:{r['id']}")
        if (r["decoy_union"] == true_union) != r["decoy_matches_true_union"]:
            failures.append(f"DECOY_FLAG_WRONG:{r['id']}")
    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")
    matches = sum(1 for r in rows if r["decoy_matches_true_union"])
    drops = len(rows) - matches
    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "decoy_matches_rows": matches, "decoy_drops_rows": drops}


# ---------------------------------------------------------------------------
# TOPOLOGY_AND_UNKNOWN_PRESERVATION
# ---------------------------------------------------------------------------

def build_topology_rows() -> list[dict]:
    rows = []
    combos = [
        (u, b)
        for u in itertools.product(UNKNOWN_COUNTS, repeat=3)
        for b in itertools.product(BRANCH_COUNTS, repeat=3)
    ]
    # bound combinatorics deterministically (27 unknown-combos x 27 branch-combos
    # = 729; sample down via stable ranking to keep this family a comparable
    # scale to its sibling).
    sampled = [c for c in combos if _stable_rank(f"TOPO|{c}") % 11 == 0]
    for combo_idx, (unknowns, branches) in enumerate(sampled):
        unknowns_by_scope = dict(zip(SCOPES, unknowns))
        branches_by_scope = dict(zip(SCOPES, branches))
        true_total_unknown = sum(unknowns)
        true_total_branch = sum(branches)
        combo_key = f"topo:{unknowns}:{branches}"
        split_role = _split_role_for_key(combo_key)

        for decoy_mode in ("MATCHES", "COLLAPSES_BRANCHES", "DROPS_UNKNOWNS"):
            decoy_branch = true_total_branch
            decoy_unknown = true_total_unknown
            if decoy_mode == "COLLAPSES_BRANCHES":
                if true_total_branch <= 1:
                    continue  # degenerate: nothing to collapse, would exactly duplicate the MATCHES row
                decoy_branch = 1  # falsely claims a single resolved winner
            elif decoy_mode == "DROPS_UNKNOWNS":
                if true_total_unknown <= 0:
                    continue  # degenerate: nothing to drop, would exactly duplicate the MATCHES row
                decoy_unknown = 0  # falsely claims full certainty

            per_scope_text = " | ".join(
                f"{s}: unknown_count={unknowns_by_scope[s]}, branch_count={branches_by_scope[s]}" for s in SCOPES
            )
            decoy_text = f"[already-rolled-up, unverified]: total_branch_count={decoy_branch}, total_unknown_count={decoy_unknown}"
            splits_to_emit = ["HOLDOUT_FROZEN"] if split_role == "HOLDOUT_FROZEN" else ["TRAIN", "VALIDATION"]
            for split in splits_to_emit:
                prompt = (
                    f"Coordinator session {SESSION_LABEL[split]}. Lower-scope summaries (no raw worker "
                    f"packets available, only these compressed summaries): {per_scope_text}.\n"
                    f"A prior rollup claims: {decoy_text}.\n"
                    "As the higher-scope coordinator, report the TOTAL preserved branch count and TOTAL "
                    "unknown count across all three scopes, recomputed by summing the scope summaries -- "
                    "branches are never silently collapsed into fewer branches, and unknowns are never "
                    "silently resolved away. Respond as: branch_count=<N>, unknown_count=<M>."
                )
                r = row_common("G_TOPOLOGY_AND_UNKNOWN_PRESERVATION", split)
                r.update({
                    "id": f"G_TOPO_{combo_idx}_{decoy_mode}_{split}",
                    "unknowns_by_scope": unknowns_by_scope,
                    "branches_by_scope": branches_by_scope,
                    "decoy_branch_count": decoy_branch,
                    "decoy_unknown_count": decoy_unknown,
                    "decoy_matches_true": decoy_branch == true_total_branch and decoy_unknown == true_total_unknown,
                    "prompt": prompt,
                    "target": f"branch_count={true_total_branch}, unknown_count={true_total_unknown}",
                })
                rows.append(r)
    return rows


def audit_topology(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        true_branch = sum(r["branches_by_scope"].values())
        true_unknown = sum(r["unknowns_by_scope"].values())
        expected = f"branch_count={true_branch}, unknown_count={true_unknown}"
        if r["target"] != expected:
            failures.append(f"TARGET_WRONG:{r['id']}")
        matches = r["decoy_branch_count"] == true_branch and r["decoy_unknown_count"] == true_unknown
        if matches != r["decoy_matches_true"]:
            failures.append(f"DECOY_FLAG_WRONG:{r['id']}")
    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")
    matches = sum(1 for r in rows if r["decoy_matches_true"])
    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "decoy_matches_rows": matches, "decoy_wrong_rows": len(rows) - matches}


# ---------------------------------------------------------------------------

def run() -> tuple[dict, dict]:
    ref_union = build_ref_union_rows()
    topology = build_topology_rows()
    reports = {
        "G_REF_UNION_PRESERVATION": audit_ref_union(ref_union),
        "G_TOPOLOGY_AND_UNKNOWN_PRESERVATION": audit_topology(topology),
    }
    overall_pass = all(r["pass"] for r in reports.values())
    families = {"G_REF_UNION_PRESERVATION": ref_union, "G_TOPOLOGY_AND_UNKNOWN_PRESERVATION": topology}
    report = {
        "schema": SCHEMA,
        "families": {name: {"rows": len(rows), "split_counts": dict(Counter(r["split"] for r in rows))}
                     for name, rows in families.items()},
        "reports": reports,
        "total_rows": sum(len(v) for v in families.values()),
        "overall_pass": overall_pass,
        "training_eligible": False,
        "reason_training_eligible_false": "no real tokenizer/atom-manifest binding, no admission gate run -- candidate/quarantined only per TRIGGERWORT_2 course Step 6.",
    }
    return report, families


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--audit-out", type=Path)
    args = ap.parse_args()

    report, families = run()
    if not report["overall_pass"]:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in families.items():
        path = args.out_dir / f"TRIGGER2_{name}_CANDIDATE_V1.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        report["families"][name]["output_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        report["families"][name]["output_path"] = str(path)

    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.audit_out:
        args.audit_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
