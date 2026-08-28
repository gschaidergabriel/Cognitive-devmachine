#!/usr/bin/env python3
"""Rendered-byte leakage/shortcut audit for trigger2_dynamic_binding_blueprint_v2.

Context (see research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md
and TRIGGERWORT_2_TRAINING_COURSE_DELTA_V35_SUPERVISOR_8_81_2026-08-26.md, hypothesis H5):

The blueprint's own selftest (trigger2_dynamic_binding_blueprint_v2.selftest) only checks
PAIRWISE mutual information between the target/class and individual nuisance fields
(codebook order, layout, polarity, template) on unrendered STRUCTURED ROWS. H5's own
counterhypothesis explicitly warns that "pairwise zero-MI alone is insufficient" -- a
higher-order interaction, a tokenizer-level artifact, or a purely lexical (bag-of-words)
shortcut on the actual RENDERED PROMPT TEXT could still leak the target even when every
pairwise MI is exactly zero on the structured fields.

This tool closes that specific gap. It does NOT materialize training-eligible rows (the
blueprint remains render_status=BLOCKED_UNTIL_EXACT_ABI_ATOM_SURFACE_AND_PINNED_TOKENIZER_BINDING;
this audit renders placeholder ABI_ACCEPTED_ORDINAL atoms, which is sufficient to test the
GENERATION METHOD for structural leakage -- it is not sufficient to bind real tokenizer
identity, which remains a separate, later gate per the same course document, Step 1/Step 6).

Checks performed on rendered prompt bytes:
  1. Exact prompt-string uniqueness (no accidental duplicate rendered rows).
  2. Cross-split content disjointness: TRAIN vs VALIDATION vs HOLDOUT_FROZEN must not share
     any exact evidence+query text (they are constructed from disjoint template families, so
     this should hold trivially -- proving it directly is still required, not assumed).
  3. Text-conditional target uniformity: for every fixed (template, class, polarity, layout)
     cell -- i.e. every distinct EVIDENCE+QUERY text a model could see -- the bound TARGET
     symbol must be exactly uniformly distributed across the full codebook-order x mapping
     product. This is an EXACT enumeration proof (not a sampled estimate) that no amount of
     memorizing evidence/query phrasing alone can out-predict chance on the routed symbol.
  4. Higher-order joint-nuisance MI: extends the blueprint's pairwise checks to 2-way joint
     nuisance combinations (perm x layout, ord x layout, perm x polarity, ord x polarity,
     template x layout) against both the semantic class and the routed target symbol.
  5. A dependency-free bag-of-words shortcut probe: a Laplace-smoothed word-count log-odds
     classifier is fit on TRAIN evidence+query text (words only, codebook block excluded) to
     predict the target symbol via 5-fold cross-validation within TRAIN. Accuracy is compared
     against chance (1/3, since exactly 3 candidate symbols per row). This is the closest
     thing to an actual "shallow classifier" probe from H5's discriminator list, implemented
     without any external ML dependency so it runs anywhere this repo's Python does.

Honesty note: this audit renders PLACEHOLDER atoms (ABI_ACCEPTED_ORDINAL:NN), not the real
pinned Qwen3.5 tokenizer's accepted single-token atoms. It therefore tests the *generation
method* for nuisance/lexical leakage, not exact tokenizer-boundary leakage (e.g. subword
splits of a real atom string). A tokenizer-identity-bound rerun remains a separate, later
gate once the exact ABI atom manifest + pinned tokenizer are admitted (see Q35/Qwen3.5
identity-metrology chain) -- this is recorded explicitly in the output, not silently assumed
away.

CORRECTION (2026-08-26, same session, chatgpt-secondary review of commit ece5a0d, reproduced
independently by claude-code-lead before accepting): v1's check_higher_order_joint_mi()
computed joint MI over ALL 9072 rows combined (TRAIN+VALIDATION+HOLDOUT_FROZEN together).
The observed ~0.276-bit "leak" between target and (perm|ord|layout|polarity) x template is
NOT a within-split nuisance leak. It is exactly and entirely I(target;template) alone --
because HOLDOUT_FROZEN intentionally uses a disjoint, unseen symbol pool (12-14) exclusively
under template T6, template identity alone already predicts which 3-symbol pool the target
comes from. That is the INTENDED unseen-symbol-holdout design, not a defect. Reproduced
directly: I(target;perm x template) split-scoped inside TRAIN/VALIDATION/HOLDOUT_FROZEN
separately is exactly 0.0 in all three; and over the combined corpus,
I(target;template x nuisance) - I(target;template) = ~1.1e-16 (numerically zero) for every
nuisance field. The nuisance field adds ZERO information beyond what the (by-design)
cross-split symbol-support shift already explains. H5 ("pairwise zero-MI alone is
insufficient") remains a correct general warning, but this specific experiment does not
confirm it -- the original classification was TOOLING PASS / INTERPRETATION FAIL /
GENERATOR NOT CONVICTED. check_higher_order_joint_mi() is now split-scoped (the actual leak
test) plus an explicit excess-MI check against the template baseline (the correct
generalization for cross-split MI); the old combined-corpus number is retained as a
documented, correctly-labeled EXPECTED_HOLDOUT_SUPPORT_SHIFT informational field, not a
failure condition. See the corrected receipt superseding
research_entity/00_CURRENT/updates/trigger2-training/20260826T105610Z-trigger2-blueprint-v2-leakage-audit-claude-code-lead.json.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trigger2_dynamic_binding_blueprint_v2 as bp  # noqa: E402

SCHEMA = "CLAY_TRIGGER2_DYNAMIC_BINDING_BLUEPRINT_V2_LEAKAGE_AUDIT/v1"
SOURCE_MODULE_SHA256 = hashlib.sha256(
    Path(bp.__file__).read_bytes()
).hexdigest()
CHANCE_ACCURACY = 1.0 / 3.0


def render_codebook(row: dict) -> str:
    entries = []
    for oi in row["ord"]:
        cls = bp.CLASSES[oi]
        ci = bp.CLASSES.index(cls)
        sym = row["sym"][row["perm"][ci]]
        entries.append(f"{cls}=>{sym}")
    return " | ".join(entries)


def render_prompt(row: dict) -> tuple[str, str]:
    """Returns (evidence_query_text, full_prompt_text). Evidence/query text excludes
    the codebook block entirely, so it can be probed in isolation for lexical leakage."""
    codebook = render_codebook(row)
    if row["lay"] == "EVIDENCE_THEN_QUERY":
        eq_text = f"EVIDENCE: {row['e']}\nQUERY: {row['q']}"
    else:
        eq_text = f"QUERY: {row['q']}\nEVIDENCE: {row['e']}"
    full = f"CODEBOOK: {codebook}\n{eq_text}\nAnswer with exactly one bound symbol."
    return eq_text, full


def mi(rows: list[dict], fa: Callable[[dict], object], fb: Callable[[dict], object]) -> float:
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


def check_uniqueness(rendered: list[dict]) -> dict:
    full_texts = [r["full_prompt"] for r in rendered]
    counts = Counter(full_texts)
    dupes = {t: c for t, c in counts.items() if c > 1}
    return {
        "total_rendered": len(rendered),
        "unique_full_prompts": len(counts),
        "duplicate_prompt_count": len(dupes),
        "pass": len(dupes) == 0,
    }


def check_cross_split_disjointness(rendered: list[dict]) -> dict:
    by_split: dict[str, set[str]] = defaultdict(set)
    for r in rendered:
        by_split[r["split"]].add(r["eq_text"])
    splits = sorted(by_split)
    overlaps = {}
    for a, b in itertools.combinations(splits, 2):
        inter = by_split[a] & by_split[b]
        if inter:
            overlaps[f"{a}|{b}"] = len(inter)
    return {
        "splits": {s: len(v) for s, v in by_split.items()},
        "pairwise_overlaps": overlaps,
        "pass": not overlaps,
    }


def check_text_conditional_target_uniformity(rendered: list[dict]) -> dict:
    """For every fixed (template, class, polarity, layout) -- i.e. every distinct
    evidence+query text a model could ever see -- verify the routed target symbol is
    EXACTLY uniform across the full mapping x codebook-order product. Enumerated
    exactly, not sampled."""
    groups: dict[tuple, Counter] = defaultdict(Counter)
    for r in rendered:
        row = r["row"]
        key = (row["t"], row["c"], row["p"], row["lay"])
        groups[key][row["target"]] += 1

    failures = []
    cell_sizes = set()
    for key, counter in groups.items():
        vals = set(counter.values())
        cell_sizes.add(sum(counter.values()))
        if len(vals) != 1:
            failures.append({"cell": key, "target_counts": dict(counter)})
    return {
        "groups_checked": len(groups),
        "cell_sizes_seen": sorted(cell_sizes),
        "failures": failures,
        "pass": not failures,
    }


def check_higher_order_joint_mi(rows: list[dict]) -> dict:
    """Corrected v1.1 (see module docstring CORRECTION note). Two separate, properly
    scoped questions, not one combined-corpus number:

    (a) WITHIN-SPLIT leakage: for each of TRAIN/VALIDATION/HOLDOUT_FROZEN separately,
        joint MI between target/class and every 2-way nuisance-field combination must
        be exactly 0. This is the actual "does the generator leak inside the split a
        model would actually train/eval on" test.
    (b) CROSS-CORPUS excess MI: combined over all rows, does adding a nuisance field to
        `template` explain any MORE about the target than `template` alone already does
        (I(target;template x nuisance) - I(target;template))? template alone is expected
        to carry real information (HOLDOUT_FROZEN's disjoint symbol pool is intentional,
        documented separately in check_intended_split_support_shift below) -- the excess
        over that baseline is the actual leak signal, and must be exactly 0.

    The old (v1) combined-corpus raw joint-MI number is retained under
    `informational_combined_corpus_joint_mi_bits` for provenance/regression tracking,
    explicitly labeled as EXPECTED_HOLDOUT_SUPPORT_SHIFT, and does NOT gate `pass`.
    """
    fields = {
        "perm": lambda r: tuple(r["perm"]),
        "ord": lambda r: tuple(r["ord"]),
        "lay": lambda r: r["lay"],
        "p": lambda r: r["p"],
        "t": lambda r: r["t"],
    }
    nuisance_fields = {k: v for k, v in fields.items() if k != "t"}
    targets = {
        "c": lambda r: r["c"],
        "target": lambda r: r["target"],
    }

    def joint_of(fa, fb):
        return lambda r: (fa(r), fb(r))

    # (a) within-split
    within_split: dict[str, dict[str, float]] = {}
    within_split_failures = []
    for split in ("TRAIN", "VALIDATION", "HOLDOUT_FROZEN"):
        subset = [r for r in rows if r["split"] == split]
        split_results = {}
        for (fa_name, fb_name) in itertools.combinations(fields, 2):
            fa, fb = fields[fa_name], fields[fb_name]
            for tgt_name, tgt_fn in targets.items():
                key = f"{tgt_name}__{fa_name}x{fb_name}"
                v = mi(subset, tgt_fn, joint_of(fa, fb))
                split_results[key] = v
                if abs(v) > 1e-9:
                    within_split_failures.append(f"{split}:{key}={v}")
        within_split[split] = split_results

    # (b) cross-corpus excess over the template baseline
    template_baseline = {
        tgt_name: mi(rows, tgt_fn, fields["t"]) for tgt_name, tgt_fn in targets.items()
    }
    excess_mi: dict[str, float] = {}
    excess_failures = []
    for nf_name, nf_fn in nuisance_fields.items():
        for tgt_name, tgt_fn in targets.items():
            key = f"{tgt_name}__templatex{nf_name}"
            joint_val = mi(rows, tgt_fn, joint_of(fields["t"], nf_fn))
            excess = joint_val - template_baseline[tgt_name]
            excess_mi[key] = excess
            if abs(excess) > 1e-9:
                excess_failures.append(f"{key}={excess}")

    # retained for provenance/regression only, NOT a pass/fail gate (see CORRECTION note)
    informational_combined = {}
    for (fa_name, fb_name) in itertools.combinations(fields, 2):
        fa, fb = fields[fa_name], fields[fb_name]
        for tgt_name, tgt_fn in targets.items():
            key = f"{tgt_name}__{fa_name}x{fb_name}"
            informational_combined[key] = mi(rows, tgt_fn, joint_of(fa, fb))

    failures = within_split_failures + excess_failures
    return {
        "within_split_joint_mi_bits": within_split,
        "within_split_failures": within_split_failures,
        "template_baseline_mi_bits": template_baseline,
        "excess_mi_over_template_baseline_bits": excess_mi,
        "excess_failures": excess_failures,
        "informational_combined_corpus_joint_mi_bits": informational_combined,
        "informational_note": "combined-corpus numbers above are EXPECTED_HOLDOUT_SUPPORT_SHIFT (HOLDOUT_FROZEN's intentional disjoint symbol pool under template T6), not a leak; see module CORRECTION docstring. They are informational/regression-tracking only and do not gate pass.",
        "failures": failures,
        "pass": not failures,
    }


def tokenize(text: str) -> list[str]:
    return [w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if w]


def bow_shortcut_probe(rendered: list[dict], folds: int = 5, seed: int = 20260826) -> dict:
    """Laplace-smoothed word-count log-odds classifier, k-fold CV within TRAIN,
    predicting the routed target symbol from evidence+query text alone (codebook
    excluded). No external ML dependency."""
    train = [r for r in rendered if r["split"] == "TRAIN"]
    if not train:
        return {"pass": False, "reason": "no TRAIN rows"}

    rng = random.Random(seed)
    idx = list(range(len(train)))
    rng.shuffle(idx)
    fold_of = {i: idx.index(i) % folds for i in idx}

    correct = 0
    total = 0
    per_fold_acc = []
    for held_fold in range(folds):
        train_rows = [train[i] for i in idx if fold_of[i] != held_fold]
        test_rows = [train[i] for i in idx if fold_of[i] == held_fold]

        vocab_by_class: dict[str, Counter] = defaultdict(Counter)
        class_totals: Counter = Counter()
        for r in train_rows:
            words = tokenize(r["eq_text"])
            vocab_by_class[r["row"]["target"]].update(words)
            class_totals[r["row"]["target"]] += len(words)
        vocab = set(w for c in vocab_by_class.values() for w in c)
        v = max(len(vocab), 1)

        # Restrict candidates to the row's OWN valid triple (the 3 symbols the real
        # codebook could ever bind for this row) -- matching the real task, where the
        # model is never choosing among all 12 train symbols, only its local 3. Using
        # the full 12-way class set here would silently redefine chance to 1/12 and
        # make the accuracy-vs-chance comparison meaningless.
        fold_correct = 0
        for r in test_rows:
            words = tokenize(r["eq_text"])
            candidates = r["row"]["sym"]
            best_cls, best_score = None, None
            for cls in candidates:
                denom = class_totals.get(cls, 0) + v
                score = 0.0
                for w in words:
                    cnt = vocab_by_class.get(cls, Counter()).get(w, 0)
                    score += math.log((cnt + 1) / denom)
                if best_score is None or score > best_score:
                    best_score, best_cls = score, cls
            if best_cls == r["row"]["target"]:
                fold_correct += 1
                correct += 1
            total += 1
        per_fold_acc.append(fold_correct / max(len(test_rows), 1))

    accuracy = correct / max(total, 1)
    return {
        "folds": folds,
        "n": total,
        "accuracy": accuracy,
        "per_fold_accuracy": per_fold_acc,
        "chance_accuracy": CHANCE_ACCURACY,
        "accuracy_minus_chance": accuracy - CHANCE_ACCURACY,
        # One-sided: a SHORTCUT means beating chance, so only above-chance deviation
        # fails this check. Below-chance is classifier noise/weakness (Laplace-smoothed
        # NB on short texts, 5-fold CV), not evidence of a leak -- and is independently
        # ruled out anyway by check_text_conditional_target_uniformity's exact
        # enumeration proof that text alone carries exactly zero information here.
        "pass": (accuracy - CHANCE_ACCURACY) < 0.05,
        "note": "PASS means the bag-of-words shortcut probe could not beat chance by more than 5pp (one-sided; below-chance is classifier noise, not a leak signal). It does not by itself prove zero information -- check_text_conditional_target_uniformity is the exact proof for that; this probe is a secondary, weaker corroboration.",
    }


def check_intended_split_support_shift(rows: list[dict]) -> dict:
    """Documents, explicitly and separately from the leakage checks, that
    TRAIN/VALIDATION intentionally share their symbol pool and HOLDOUT_FROZEN
    intentionally uses a disjoint unseen pool. This is the designed unseen-symbol
    evaluation, not a leak -- stating it as its own checked fact (rather than letting
    it hide inside an unscoped MI number, which is exactly what v1 got wrong) prevents
    the next reader from re-deriving the same misattribution."""
    train_syms = {r["target"] for r in rows if r["split"] == "TRAIN"}
    val_syms = {r["target"] for r in rows if r["split"] == "VALIDATION"}
    hold_syms = {r["target"] for r in rows if r["split"] == "HOLDOUT_FROZEN"}
    ok = train_syms == val_syms and train_syms.isdisjoint(hold_syms) and bool(hold_syms)
    return {
        "train_symbols": sorted(train_syms),
        "validation_symbols": sorted(val_syms),
        "holdout_symbols": sorted(hold_syms),
        "train_equals_validation_symbols": train_syms == val_syms,
        "holdout_disjoint_from_train": train_syms.isdisjoint(hold_syms),
        "pass": ok,
        "note": "This IS the intended unseen-symbol holdout design (not a leak). It is exactly what makes template alone informative about target in the combined corpus -- see check_higher_order_joint_mi's informational_combined_corpus_joint_mi_bits.",
    }


def run() -> dict:
    rows = bp.build_rows()
    rendered = []
    for row in rows:
        eq_text, full = render_prompt(row)
        rendered.append({"row": row, "split": row["split"], "eq_text": eq_text, "full_prompt": full})

    checks = {
        "uniqueness": check_uniqueness(rendered),
        "cross_split_disjointness": check_cross_split_disjointness(rendered),
        "text_conditional_target_uniformity": check_text_conditional_target_uniformity(rendered),
        "higher_order_joint_mi": check_higher_order_joint_mi(rows),
        "intended_split_support_shift": check_intended_split_support_shift(rows),
        "bag_of_words_shortcut_probe": bow_shortcut_probe(rendered),
    }
    overall_pass = all(c.get("pass") for c in checks.values())

    return {
        "schema": SCHEMA,
        "source_module": {"path": "tools/trigger2_dynamic_binding_blueprint_v2.py", "sha256": SOURCE_MODULE_SHA256},
        "blueprint_schema": bp.SCHEMA,
        "rows_audited": len(rows),
        "render_note": "PLACEHOLDER ABI_ACCEPTED_ORDINAL atoms; tests generation-method leakage, not real-tokenizer boundary leakage (see module docstring).",
        "checks": checks,
        "overall_pass": overall_pass,
        "training_eligible": False,
        "reason_training_eligible_false": "audit passing does not admit rows; real ABI atom manifest + pinned tokenizer binding + separate admission gate remain required per TRIGGERWORT_2 course Step 6/1.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    report = run()
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
