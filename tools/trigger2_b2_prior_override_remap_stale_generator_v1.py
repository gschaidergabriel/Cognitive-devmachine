#!/usr/bin/env python3
"""Trigger-2 B2 candidate generator: semantic-prior override, mid-episode
remapping, stale-binding rejection.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
Training map "B2: semantic-prior override plus mid-episode remapping and
stale-binding rejection". Reuses the same symbol-triple partition and atom-naming
scheme as tools/trigger2_dynamic_binding_blueprint_v2.py (the B1 donor) so B0-B2
share one consistent ancestry. Status: METHOD_ONLY / candidate-and-quarantined per
TRIGGERWORT_2 course Step 6 -- placeholder ABI_ACCEPTED_ORDINAL atoms, no real
tokenizer binding, no admission gate run.

Three families, each testing a DIFFERENT failure mode against a matched
non-adversarial control so a model cannot pass by ignoring the interesting
condition entirely:

PRIOR_OVERRIDE
  A distractor line states a binding from a different, explicitly-marked
  reference-only episode. The distractor permutation is enumerated over all 6
  possible class->symbol permutations against each current permutation, so
  the distractor AGREES with the current codebook (full-permutation equality;
  control -- uninformative either way) on exactly 1/6 of rows and DISAGREES
  on 5/6 (adversarial -- only the CURRENT codebook may determine the target).
  This is NOT a 50/50 split -- CORRECTED 2026-08-27, verified directly against
  TRIGGER2_B2_PRIOR_OVERRIDE_CANDIDATE_V1.jsonl (n=1080): 180 agree / 900
  disagree, exactly 1/6 vs 5/6. Docstring/comment fix only, data unchanged
  (this was always the actual generation behavior, just misdescribed here).
  Two presentation orders (distractor-first / codebook-first) rule out a
  position-based shortcut.

MID_EPISODE_REMAP
  An initial codebook is stated, then an explicit UPDATE reassigns exactly one
  class's symbol (borrowed from one of the other two classes' OLD binding, so
  the new value is a real, already-seen symbol, not an invented one). The query
  may ask about the updated class (target = new value), the class whose old
  value was borrowed (target = its own unchanged old value -- the borrow is
  one-directional, not a swap), or the untouched third class (target =
  unchanged). This directly probes "did you actually apply only the stated
  update, not everything, and not nothing."

STALE_BINDING_REJECTION
  A codebook is explicitly marked either CURRENT (valid, answer normally) or
  STALE_REJECTED (must not be used -- emit the literal token STALE_REJECTED
  instead of guessing a symbol). Both conditions share the identical codebook
  structure; only the marker line differs, so the model cannot pass by pattern
  matching the codebook shape alone.
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

SCHEMA = "CLAY_TRIGGER2_B2_PRIOR_OVERRIDE_REMAP_STALE_CANDIDATE/v1"
ANCESTRY = "trigger2-20260826-b2-prior-override-remap-stale-v1"
STALE_TOKEN = "STALE_REJECTED"

TRIPLE_SPLITS = [(bp.TRAIN_TRIPLETS, "TRAIN"), ((bp.HOLDOUT_TRIPLET,), "HOLDOUT_FROZEN")]
LAYOUTS_B2 = ("A_FIRST", "B_FIRST")


def row_common(family: str, split: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": ANCESTRY,
        "curriculum_phase": "B2_PRIOR_OVERRIDE_REMAP_STALE",
        "family": family,
        "split": split,
        "abi_manifest_sha256": bp.ABI_MANIFEST_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
    }


# ---------------------------------------------------------------------------
# PRIOR_OVERRIDE
# ---------------------------------------------------------------------------

def build_prior_override_rows() -> list[dict]:
    rows = []
    for triplets, split in TRIPLE_SPLITS:
        for triple in triplets:
            sym = [bp.atom_ref(n) for n in triple]
            for mi_, perm in enumerate(bp.PERMS):
                actual_binding = {bp.CLASSES[ci]: sym[perm[ci]] for ci in range(3)}
                for di_, distractor_perm in enumerate(bp.PERMS):
                    distractor_binding = {bp.CLASSES[ci]: sym[distractor_perm[ci]] for ci in range(3)}
                    agrees = distractor_binding == actual_binding
                    for lay in LAYOUTS_B2:
                        for c in bp.CLASSES:
                            distractor_line = " | ".join(f"{k}=>{v}" for k, v in distractor_binding.items())
                            codebook_line = " | ".join(f"{k}=>{v}" for k, v in actual_binding.items())
                            note = f"NOTE (reference only, from a DIFFERENT past episode, NOT current): {distractor_line}"
                            book = f"CODEBOOK (current, authoritative): {codebook_line}"
                            body = f"{note}\n{book}" if lay == "A_FIRST" else f"{book}\n{note}"
                            r = row_common("PRIOR_OVERRIDE", split)
                            r.update({
                                "id": f"B2_PRIOR_T{triple[0]:02d}_M{mi_}_D{di_}_{lay}_{c}",
                                "triple": list(triple),
                                "perm": list(perm),
                                "distractor_perm": list(distractor_perm),
                                "distractor_agrees_with_current": agrees,
                                "layout": lay,
                                "class_given_directly": c,
                                "prompt": (
                                    f"{body}\n"
                                    f"STATE: the current class is {c}, given directly.\n"
                                    "Return exactly one bound symbol, using ONLY the CURRENT codebook."
                                ),
                                "target": actual_binding[c],
                            })
                            rows.append(r)
    return rows


def audit_prior_override(rows: list[dict]) -> dict:
    failures = []
    # recompute independently from raw ints rather than trusting stored fields
    for r in rows:
        sym = [bp.atom_ref(n) for n in r["triple"]]
        ci = bp.CLASSES.index(r["class_given_directly"])
        expected = sym[r["perm"][ci]]
        if r["target"] != expected:
            failures.append(f"TARGET_NOT_FROM_CURRENT_CODEBOOK:{r['id']}")
        distractor_binding = {bp.CLASSES[k]: sym[r["distractor_perm"][k]] for k in range(3)}
        actual_binding = {bp.CLASSES[k]: sym[r["perm"][k]] for k in range(3)}
        agrees = distractor_binding == actual_binding
        if agrees != r["distractor_agrees_with_current"]:
            failures.append(f"AGREEMENT_FLAG_WRONG:{r['id']}")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    # NOTE: a naive "target must never coincide with the distractor's prediction
    # on disagree rows" check was tried here and produces a FALSE POSITIVE, not a
    # real defect: distractor_agrees_with_current means the FULL 3-class binding
    # differs somewhere, not that it differs on the SPECIFIC queried class. Two
    # distinct permutations of 3 elements can still coincide on one position --
    # that overlap is unavoidable permutation combinatorics, and its presence is
    # actually desirable (it prevents "always contradict the distractor" from
    # being a reliable shortcut). What matters, and is checked above, is that
    # target always equals the CURRENT codebook's binding regardless of whether
    # the distractor happens to agree or disagree on that specific class.
    disagree = [r for r in rows if not r["distractor_agrees_with_current"]]
    coincidental_agreement_on_queried_class = sum(
        1 for r in disagree
        if r["target"] == {bp.CLASSES[k]: [bp.atom_ref(n) for n in r["triple"]][r["distractor_perm"][k]] for k in range(3)}[r["class_given_directly"]]
    )

    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "disagree_rows": len(disagree), "agree_rows": len(rows) - len(disagree),
            "coincidental_target_distractor_agreement_on_queried_class_within_disagree_rows": coincidental_agreement_on_queried_class,
            "coincidental_agreement_note": "expected permutation-combinatorics overlap, not a leak -- see comment above"}


# ---------------------------------------------------------------------------
# MID_EPISODE_REMAP
# ---------------------------------------------------------------------------

def build_mid_episode_remap_rows() -> list[dict]:
    rows = []
    for triplets, split in TRIPLE_SPLITS:
        for triple in triplets:
            sym = [bp.atom_ref(n) for n in triple]
            for mi_, perm in enumerate(bp.PERMS):
                old_binding = {bp.CLASSES[ci]: sym[perm[ci]] for ci in range(3)}
                for updated_class in bp.CLASSES:
                    others = [c for c in bp.CLASSES if c != updated_class]
                    for source_class in others:
                        new_value = old_binding[source_class]
                        new_binding = dict(old_binding)
                        new_binding[updated_class] = new_value
                        codebook_line = " | ".join(f"{k}=>{v}" for k, v in old_binding.items())
                        update_line = f"UPDATE: from this point forward, {updated_class}=>{new_value} (all other bindings unchanged)."
                        for queried_class in bp.CLASSES:
                            expected = new_binding[queried_class]
                            r = row_common("MID_EPISODE_REMAP", split)
                            r.update({
                                "id": f"B2_REMAP_T{triple[0]:02d}_M{mi_}_U{updated_class}_S{source_class}_Q{queried_class}",
                                "triple": list(triple),
                                "perm": list(perm),
                                "updated_class": updated_class,
                                "source_class": source_class,
                                "queried_class": queried_class,
                                "prompt": (
                                    f"CODEBOOK (initial): {codebook_line}\n"
                                    f"{update_line}\n"
                                    f"STATE: the current class is {queried_class}, given directly.\n"
                                    "Return exactly one bound symbol, reflecting only the stated update."
                                ),
                                "target": expected,
                            })
                            rows.append(r)
    return rows


def audit_mid_episode_remap(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        sym = [bp.atom_ref(n) for n in r["triple"]]
        old_binding = {bp.CLASSES[ci]: sym[r["perm"][ci]] for ci in range(3)}
        new_binding = dict(old_binding)
        new_binding[r["updated_class"]] = old_binding[r["source_class"]]
        expected = new_binding[r["queried_class"]]
        if r["target"] != expected:
            failures.append(f"TARGET_WRONG:{r['id']}")
        if r["queried_class"] not in (r["updated_class"], r["source_class"]):
            if r["target"] != old_binding[r["queried_class"]]:
                failures.append(f"UNTOUCHED_CLASS_CHANGED:{r['id']}")
        if r["queried_class"] == r["source_class"]:
            if r["target"] != old_binding[r["source_class"]]:
                failures.append(f"SOURCE_CLASS_BINDING_MUTATED:{r['id']}")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    return {"rows": len(rows), "failures": failures, "pass": not failures}


# ---------------------------------------------------------------------------
# STALE_BINDING_REJECTION
# ---------------------------------------------------------------------------

def build_stale_binding_rows() -> list[dict]:
    rows = []
    for triplets, split in TRIPLE_SPLITS:
        for triple in triplets:
            sym = [bp.atom_ref(n) for n in triple]
            for mi_, perm in enumerate(bp.PERMS):
                binding = {bp.CLASSES[ci]: sym[perm[ci]] for ci in range(3)}
                codebook_line = " | ".join(f"{k}=>{v}" for k, v in binding.items())
                for stale in (True, False):
                    marker = (
                        "NOTICE: the codebook below is marked STALE_REJECTED. Do not use it."
                        if stale else
                        "NOTICE: the codebook below is marked CURRENT. It may be used."
                    )
                    for c in bp.CLASSES:
                        target = STALE_TOKEN if stale else binding[c]
                        r = row_common("STALE_BINDING_REJECTION", split)
                        r.update({
                            "id": f"B2_STALE_T{triple[0]:02d}_M{mi_}_{'STALE' if stale else 'VALID'}_{c}",
                            "triple": list(triple),
                            "perm": list(perm),
                            "is_stale": stale,
                            "class_given_directly": c,
                            "prompt": (
                                f"{marker}\n"
                                f"CODEBOOK: {codebook_line}\n"
                                f"STATE: the current class is {c}, given directly.\n"
                                f"Return exactly one bound symbol, or the token {STALE_TOKEN} "
                                "if the binding cannot be used."
                            ),
                            "target": target,
                        })
                        rows.append(r)
    return rows


def audit_stale_binding(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        sym = [bp.atom_ref(n) for n in r["triple"]]
        binding = {bp.CLASSES[ci]: sym[r["perm"][ci]] for ci in range(3)}
        expected = STALE_TOKEN if r["is_stale"] else binding[r["class_given_directly"]]
        if r["target"] != expected:
            failures.append(f"TARGET_WRONG:{r['id']}")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    stale_rows = [r for r in rows if r["is_stale"]]
    valid_rows = [r for r in rows if not r["is_stale"]]
    if not all(r["target"] == STALE_TOKEN for r in stale_rows):
        failures.append("SOME_STALE_ROWS_NOT_REJECTED")
    if any(r["target"] == STALE_TOKEN for r in valid_rows):
        failures.append("SOME_VALID_ROWS_INCORRECTLY_REJECTED")

    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "stale_rows": len(stale_rows), "valid_rows": len(valid_rows)}


# ---------------------------------------------------------------------------

def run() -> dict:
    prior = build_prior_override_rows()
    remap = build_mid_episode_remap_rows()
    stale = build_stale_binding_rows()
    reports = {
        "PRIOR_OVERRIDE": audit_prior_override(prior),
        "MID_EPISODE_REMAP": audit_mid_episode_remap(remap),
        "STALE_BINDING_REJECTION": audit_stale_binding(stale),
    }
    overall_pass = all(r["pass"] for r in reports.values())
    return {
        "schema": SCHEMA,
        "families": {
            "PRIOR_OVERRIDE": {"rows": len(prior), "split_counts": dict(Counter(r["split"] for r in prior))},
            "MID_EPISODE_REMAP": {"rows": len(remap), "split_counts": dict(Counter(r["split"] for r in remap))},
            "STALE_BINDING_REJECTION": {"rows": len(stale), "split_counts": dict(Counter(r["split"] for r in stale))},
        },
        "reports": reports,
        "total_rows": len(prior) + len(remap) + len(stale),
        "overall_pass": overall_pass,
        "training_eligible": False,
    }, {"PRIOR_OVERRIDE": prior, "MID_EPISODE_REMAP": remap, "STALE_BINDING_REJECTION": stale}


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
        path = args.out_dir / f"TRIGGER2_B2_{name}_CANDIDATE_V1.jsonl"
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
