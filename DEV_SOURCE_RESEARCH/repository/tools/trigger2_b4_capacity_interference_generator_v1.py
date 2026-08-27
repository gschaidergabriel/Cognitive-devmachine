#!/usr/bin/env python3
"""Trigger-2 B4 candidate generator: delay/interference capacity curves.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
Training map section "B4: delay/interference capacity curves" -- and section 4's whitened-HRR
note: "declared safe working guarantee <=16 simultaneous bindings". Section 5's laws apply:
episode-local codebooks, no global class-to-vector-atom mapping, family-disjoint holdouts,
lexical counterbalancing, no direct-SFT promotion from lexically shortcut-prone wording.

Unlike B0/B1 (fixed N=3 triple, full S3 factorial crossing), B4's axis of interest is
CAPACITY (K = number of concurrent episode-local entity->atom bindings) crossed with DELAY
(D = number of intervening lines between the codebook and the query) and INTERFERENCE_KIND
(whether those intervening lines are semantically neutral filler, or "lookalike" decoy
codebook-shaped lines for entities that are NOT part of this episode's real codebook). This
is a capacity/interference *curve* family: the same underlying BIND/READ task, swept across
K in {2,4,8,16} (the top end matches the declared <=16 safe-binding guarantee) and D in
{0,2,4,8}, so a later eval can plot accuracy against K and D separately.

Deliberately does NOT reuse trigger2_dynamic_binding_blueprint_v2.py as a donor: that
generator is architecturally fixed at N=3 (one S3-permutation triple) and does not have a
capacity/delay axis at all, so extending it here would mean grafting an unrelated axis onto
a donor built for a different question (S3 mapping x codebook-order x layout nuisance
crossing at fixed small N) -- exactly the kind of confound the course repeatedly warns
against ("no aggregate checkpoint score may hide a mandatory-axis failure"). This generator
is new, but keeps the same overall candidate-row shape/provenance metadata (model,
model_revision, abi_manifest_sha256, evidence_class=METHOD_ONLY, training_eligible=False)
used across B0/B1 so all families stay one consistent corpus ancestry, and reuses
trigger2_dynamic_binding_blueprint_v2 only for those shared constant fields (MODEL,
MODEL_REV, SOURCE_PACKAGE_SHA256, ABI_MANIFEST_SHA256) -- not its N=3 generation logic.

Atom pool is deliberately disjoint from B0/B1 (which use ABI_ACCEPTED_ORDINAL:00-14) so no
cross-family atom collision is even possible: B4 uses ABI_ACCEPTED_ORDINAL:20-99, split as
TRAIN/VALIDATION=20-59 (shared pool, matching the B0/B1 TRAIN==VALIDATION symbol-pool
pattern), HOLDOUT_FROZEN=60-79 (disjoint unseen pool, matching the B0/B1
holdout-disjoint-symbol pattern), DECOY=80-99 (never a valid target in any split, used only
to render "lookalike" interference lines).

Status: METHOD_ONLY / candidate-and-quarantined per TRIGGERWORT_2 course Step 6. Rows are
NOT training-eligible: placeholder ABI_ACCEPTED_ORDINAL atoms, no real tokenizer/atom-manifest
binding, no admission gate run. accepted_dataset_tokens remains 0 regardless of this tool's
output.

Honesty note on audit scope (do not overclaim rigor not actually engineered here): this
generator's family-disjointness, target-derivation, decoy/neutral-filler leak checks and
capacity/delay grid-coverage checks are EXACT (recomputed over every generated row, not
sampled). The bag-of-words shortcut probe is, as elsewhere in this repo, an empirical
secondary corroboration (5-fold CV), not an exact-enumeration proof. Unlike
trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1.py this generator does NOT claim an
exact-zero mutual-information proof between codebook presentation order and target: episode
entity sets, atom draws and presentation order are independently resampled per episode via a
seeded RNG rather than fully factorially crossed (a full factorial cross at K=16 is
combinatorially infeasible), so an exact enumeration proof over presentation order is not
available here. What IS checked exactly is that target derivation never reads presentation
order (target = true_mapping[queried_entity], asserted per row) and that queried-entity
codebook position is not degenerate (spans multiple values per K/D/kind cell).
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trigger2_dynamic_binding_blueprint_v2 as bp  # noqa: E402  (shared metadata only)

SCHEMA = "CLAY_TRIGGER2_B4_CAPACITY_INTERFERENCE_CANDIDATE/v1"
ANCESTRY = "trigger2-20260826-b4-capacity-interference-v1"

CAPACITY_LEVELS = (2, 4, 8, 16)
DELAY_LEVELS = (0, 2, 4, 8)
KINDS_WHEN_DELAY = ("NEUTRAL", "LOOKALIKE")

ENTITY_POOL = [f"cell_{i:02d}" for i in range(20)]
DECOY_ENTITIES = [f"shadow_{i:02d}" for i in range(20)]

ATOM_POOL_TRAIN_VAL = list(range(20, 60))
ATOM_POOL_HOLDOUT = list(range(60, 80))
ATOM_POOL_DECOY = list(range(80, 100))


def atom_ref(n: int) -> str:
    return f"ABI_ACCEPTED_ORDINAL:{n:02d}"


NEUTRAL_FILLERS = {
    "TRAIN": [
        "The nearest weather station logged light overnight rain.",
        "Corridor B remains at standard ambient temperature.",
        "The archive index was rebuilt at the start of the shift.",
        "A routine inventory count found no discrepancies.",
        "The reference clock reported nominal drift for the interval.",
        "Visitor traffic through the east entrance was unremarkable.",
        "The backup job completed within its usual time window.",
        "No maintenance requests were filed during the observation period.",
    ],
    "VALIDATION": [
        "The loading dock reported a quiet morning shift.",
        "Ambient humidity in the storage bay stayed within tolerance.",
        "The printer queue was empty at the top of the hour.",
        "A scheduled software update installed without incident.",
        "The courier run finished slightly ahead of schedule.",
        "Lighting levels in the atrium were unchanged from the prior day.",
        "The survey response rate matched the historical average.",
        "No anomalies were flagged by the overnight monitoring sweep.",
    ],
    "HOLDOUT_FROZEN": [
        "The garden terrace irrigation ran on its normal cycle.",
        "A routine fire-drill notice was posted with no drill scheduled.",
        "The cafeteria menu rotated to its standard midweek option.",
        "Parking occupancy stayed near its typical midday level.",
        "The mail room processed its usual volume of packages.",
        "A quarterly newsletter draft was circulated for review.",
        "The shuttle service kept to its published timetable.",
        "Background network latency stayed within the expected band.",
    ],
}


def row_common(split: str) -> dict:
    return {
        "schema": SCHEMA,
        "curriculum_phase": "B4_DELAY_INTERFERENCE_CAPACITY",
        "split": split,
        "model": bp.MODEL,
        "model_revision": bp.MODEL_REV,
        "source_package_sha256": bp.SOURCE_PACKAGE_SHA256,
        "abi_manifest_sha256": bp.ABI_MANIFEST_SHA256,
        "provenance_ancestry_id": ANCESTRY,
        "evidence_class": "METHOD_ONLY",
        "training_eligible": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
        "selected_using_holdout": False,
    }


def render_row(split: str, K: int, D: int, kind: str, rep: int, queried: str,
                order: list[str], true_mapping: dict[str, int], filler_lines: list[str]) -> dict:
    codebook_text = " | ".join(f"{e}=>{atom_ref(true_mapping[e])}" for e in order)
    filler_block = "\n".join(filler_lines) if filler_lines else "(no intervening statements)"
    query_text = f"Which atom is bound to {queried}?"
    prompt = (
        f"CODEBOOK: {codebook_text}\n"
        f"INTERVENING:\n{filler_block}\n"
        f"QUERY: {query_text}\n"
        "Answer with exactly one bound atom."
    )
    eq_text = f"INTERVENING:\n{filler_block}\nQUERY: {query_text}"
    r = row_common(split)
    r.update({
        "id": f"B4_{split}_K{K:02d}_D{D:02d}_{kind}_R{rep}_{queried}",
        "capacity_k": K,
        "delay_d": D,
        "interference_kind": kind,
        "episode_repeat": rep,
        "entities_presentation_order": order,
        "true_mapping": {e: atom_ref(true_mapping[e]) for e in order},
        "queried_entity": queried,
        "queried_position_in_codebook": order.index(queried),
        "target": atom_ref(true_mapping[queried]),
        "filler_lines": filler_lines,
        "prompt": prompt,
        "eq_text": eq_text,
    })
    return r


def gen_split(split: str, k_levels: tuple[int, ...], atom_pool: list[int], repeats: int, seed_base: int) -> list[dict]:
    rows: list[dict] = []
    neutral_pool = NEUTRAL_FILLERS[split]
    for K in k_levels:
        for D in DELAY_LEVELS:
            kinds = ("NONE",) if D == 0 else KINDS_WHEN_DELAY
            for kind in kinds:
                for rep in range(repeats):
                    rng = random.Random(repr((seed_base, K, D, kind, rep, "episode")))
                    entities = rng.sample(ENTITY_POOL, K)
                    atoms = rng.sample(atom_pool, K)
                    true_mapping = dict(zip(entities, atoms))
                    order = entities[:]
                    rng.shuffle(order)
                    for queried in entities:
                        frng = random.Random(repr((seed_base, K, D, kind, rep, queried, "filler")))
                        filler_lines: list[str] = []
                        if kind == "NEUTRAL":
                            filler_lines = [frng.choice(neutral_pool) for _ in range(D)]
                        elif kind == "LOOKALIKE":
                            for _ in range(D):
                                de = frng.choice(DECOY_ENTITIES)
                                da = frng.choice(ATOM_POOL_DECOY)
                                filler_lines.append(f"{de}=>{atom_ref(da)}")
                        rows.append(render_row(split, K, D, kind, rep, queried, order, true_mapping, filler_lines))
    return rows


def build_rows() -> list[dict]:
    rows = []
    rows += gen_split("TRAIN", CAPACITY_LEVELS, ATOM_POOL_TRAIN_VAL, repeats=2, seed_base=1)
    rows += gen_split("VALIDATION", CAPACITY_LEVELS, ATOM_POOL_TRAIN_VAL, repeats=1, seed_base=2)
    rows += gen_split("HOLDOUT_FROZEN", (2, 8, 16), ATOM_POOL_HOLDOUT, repeats=1, seed_base=3)
    return rows


def mi(rows: list[dict], fa, fb) -> float:
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


def tokenize(text: str) -> list[str]:
    return [w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if w]


def bow_shortcut_probe(rows: list[dict], folds: int = 5, seed: int = 20260826) -> dict:
    train = [r for r in rows if r["split"] == "TRAIN"]
    if not train:
        return {"pass": False, "reason": "no TRAIN rows"}
    rng = random.Random(seed)
    idx = list(range(len(train)))
    rng.shuffle(idx)
    fold_of = {i: idx.index(i) % folds for i in idx}
    correct = 0
    total = 0
    per_fold_acc = []
    chance_accs = []
    for held_fold in range(folds):
        train_rows = [train[i] for i in idx if fold_of[i] != held_fold]
        test_rows = [train[i] for i in idx if fold_of[i] == held_fold]
        vocab_by_target: dict[str, Counter] = defaultdict(Counter)
        target_totals: Counter = Counter()
        for r in train_rows:
            words = tokenize(r["eq_text"])
            vocab_by_target[r["target"]].update(words)
            target_totals[r["target"]] += len(words)
        vocab = set(w for c in vocab_by_target.values() for w in c)
        v = max(len(vocab), 1)
        fold_correct = 0
        for r in test_rows:
            words = tokenize(r["eq_text"])
            candidates = list(r["true_mapping"].values())
            chance_accs.append(1.0 / len(candidates))
            best_cls, best_score = None, None
            for cls in candidates:
                denom = target_totals.get(cls, 0) + v
                score = 0.0
                for w in words:
                    cnt = vocab_by_target.get(cls, Counter()).get(w, 0)
                    score += math.log((cnt + 1) / denom)
                if best_score is None or score > best_score:
                    best_score, best_cls = score, cls
            if best_cls == r["target"]:
                fold_correct += 1
                correct += 1
            total += 1
        per_fold_acc.append(fold_correct / max(len(test_rows), 1))
    accuracy = correct / max(total, 1)
    mean_chance = sum(chance_accs) / max(len(chance_accs), 1)
    return {
        "folds": folds,
        "n": total,
        "accuracy": accuracy,
        "per_fold_accuracy": per_fold_acc,
        "mean_chance_accuracy": mean_chance,
        "accuracy_minus_mean_chance": accuracy - mean_chance,
        "pass": (accuracy - mean_chance) < 0.05,
        "note": "candidate set per row is restricted to that row's own K present atoms (chance = 1/K, varies by row -- mean_chance_accuracy is the per-row-weighted average, not a single fixed chance level, since K varies 2..16 across this family).",
    }


def audit(rows: list[dict]) -> dict:
    failures: list[str] = []

    for r in rows:
        expected_target = r["true_mapping"][r["queried_entity"]]
        if r["target"] != expected_target:
            failures.append(f"TARGET_DERIVATION_MISMATCH:{r['id']}")
        if r["queried_entity"] not in r["entities_presentation_order"]:
            failures.append(f"QUERIED_ENTITY_NOT_IN_CODEBOOK:{r['id']}")
        if len(set(r["entities_presentation_order"])) != r["capacity_k"]:
            failures.append(f"DUPLICATE_ENTITY_IN_EPISODE:{r['id']}")
        if len(set(r["true_mapping"].values())) != r["capacity_k"]:
            failures.append(f"DUPLICATE_ATOM_IN_EPISODE:{r['id']}")
        if len(r["filler_lines"]) != r["delay_d"]:
            failures.append(f"FILLER_COUNT_MISMATCH:{r['id']}")

    for r in rows:
        if r["interference_kind"] == "LOOKALIKE":
            decoy_atoms = {ln.rsplit("=>", 1)[1] for ln in r["filler_lines"]}
            real_atoms = set(r["true_mapping"].values())
            if decoy_atoms & real_atoms:
                failures.append(f"DECOY_ATOM_COLLIDES_WITH_REAL:{r['id']}")
            decoy_entities_used = {ln.split("=>", 1)[0] for ln in r["filler_lines"]}
            if decoy_entities_used & set(r["entities_presentation_order"]):
                failures.append(f"DECOY_ENTITY_COLLIDES_WITH_REAL:{r['id']}")
        if r["interference_kind"] == "NEUTRAL":
            for ln in r["filler_lines"]:
                if "cell_" in ln or "ABI_ACCEPTED_ORDINAL" in ln or "=>" in ln:
                    failures.append(f"NEUTRAL_FILLER_LEAKS_CODEBOOK_SHAPE:{r['id']}")

    def atoms_of(split):
        return {a for r in rows if r["split"] == split for a in r["true_mapping"].values()}

    train_atoms, val_atoms, hold_atoms = atoms_of("TRAIN"), atoms_of("VALIDATION"), atoms_of("HOLDOUT_FROZEN")
    if not hold_atoms.isdisjoint(train_atoms | val_atoms):
        failures.append("HOLDOUT_ATOM_POOL_OVERLAP")
    if not hold_atoms:
        failures.append("HOLDOUT_EMPTY")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    grid = defaultdict(list)
    for r in rows:
        grid[(r["split"], r["capacity_k"], r["delay_d"], r["interference_kind"])].append(r)
    for key, members in grid.items():
        positions = {m["queried_position_in_codebook"] for m in members}
        if members[0]["capacity_k"] > 1 and len(positions) < 2:
            failures.append(f"DEGENERATE_QUERY_POSITION_COVERAGE:{key}")

    split_counts = dict(Counter(r["split"] for r in rows))
    k_d_kind_cells = sorted({(r["split"], r["capacity_k"], r["delay_d"], r["interference_kind"]) for r in rows})

    bow = bow_shortcut_probe(rows)
    if not bow.get("pass", False):
        failures.append("BAG_OF_WORDS_SHORTCUT_PROBE_FAIL")

    return {
        "schema": SCHEMA,
        "rows": len(rows),
        "split_counts": split_counts,
        "grid_cells": len(k_d_kind_cells),
        "capacity_levels": CAPACITY_LEVELS,
        "delay_levels": DELAY_LEVELS,
        "bag_of_words_shortcut_probe": bow,
        "failures": failures,
        "overall_pass": not failures,
        "training_eligible": False,
        "reason_training_eligible_false": "placeholder ABI_ACCEPTED_ORDINAL atoms, no real tokenizer/atom-manifest binding, no admission gate run -- candidate/quarantined only per TRIGGERWORT_2 course Step 6.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--audit-out", type=Path)
    ap.add_argument("--no-fail-closed", action="store_true")
    args = ap.parse_args()

    rows = build_rows()
    report = audit(rows)

    if args.audit_out:
        args.audit_out.parent.mkdir(parents=True, exist_ok=True)
        args.audit_out.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    if not report["overall_pass"] and not args.no_fail_closed:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        print("REFUSING to write B4 candidate rows: audit did not pass.", file=sys.stderr)
        return 2

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        output_sha256 = hashlib.sha256(args.out.read_bytes()).hexdigest()
        report["output_path"] = str(args.out)
        report["output_sha256"] = output_sha256
        report["output_bytes"] = args.out.stat().st_size

    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
