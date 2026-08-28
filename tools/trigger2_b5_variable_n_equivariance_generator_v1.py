#!/usr/bin/env python3
"""Trigger-2 B5 candidate generator: variable-N and cell-permutation equivariance.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
Training map section "B5: variable-N and cell-permutation equivariance". Directly targets
section 2.F ("Variable-N role flexibility ... process identity must remain independent of
node ID, N, resident model-copy count and decode concurrency. No fixed planner/critic/memory
personalities.") and section 4/5's laws: episode-local codebooks, no global class-to-
vector-atom mapping, family-disjoint holdouts.

B0/B1 fix N=3 (one symbol triple) and cross the full S3 group over mapping/order/layout. B4
sweeps CAPACITY (K, up to the declared <=16 safe-binding guarantee) crossed with DELAY. B5's
distinct axis is EQUIVARIANCE: for a fixed underlying set of N episode-local (entity, atom)
bindings, the correct answer for "what is entity E bound to" must be IDENTICAL no matter
which of several presentation-order PERMUTATIONS of the same codebook the model sees, and
this must hold across a wide range of N (2..12), not just the fixed N=3 case B0/B1 already
cover. This is the literal group-theoretic property the family name promises: the task is
correctly one where permuting the presentation order of the K "cells" leaves the correct
targets invariant (an equivariant map from presentation to codebook structure, invariant on
the readout), and this must NOT degrade or change functional form as N grows.

Deliberately does NOT reuse trigger2_dynamic_binding_blueprint_v2.py: that donor is
architecturally pinned to N=3 via its S3-only permutation machinery (PERMS =
itertools.permutations(range(3))) and provides no way to vary N without rewriting its core
loop -- at which point it would no longer be "the same donor", just code with the same name.
This generator is new but shares the same provenance metadata fields (MODEL, MODEL_REV,
SOURCE_PACKAGE_SHA256, ABI_MANIFEST_SHA256) pulled from trigger2_dynamic_binding_blueprint_v2
for corpus-wide ancestry consistency, matching the B0/B4 pattern.

For N in {2,3} every one of the N! presentation-order permutations is used (exact, matching
the B0/B1 full-S3-crossing rigor bar at the N sizes where that's tractable). For N in
{4,6,8,12} a fixed set of R=6 DISTINCT presentation-order permutations is sampled via a
seeded RNG per episode (N! is combinatorially infeasible to fully cross at N=12: 12! =
479001600) -- distinctness is checked exactly (no permutation reused within one episode), and
target-invariance across those R presentations is checked exactly per episode/queried-entity
pair. This is a real, if partial (sampled, not exhaustive), equivariance test at large N, not
a padded approximation: every row is a genuine distinct presentation that must resolve to the
same answer.

Atom pool is disjoint from B0/B1 (ABI_ACCEPTED_ORDINAL:00-14) and from B4
(ABI_ACCEPTED_ORDINAL:20-99): B5 uses a 3-digit ordinal range ABI_ACCEPTED_ORDINAL:200-299,
split TRAIN/VALIDATION=200-259 (shared pool), HOLDOUT_FROZEN=260-299 (disjoint unseen pool).
Entity labels use their own "unit_NN" namespace, also disjoint from B4's "cell_NN"/"shadow_NN".

Status: METHOD_ONLY / candidate-and-quarantined per TRIGGERWORT_2 course Step 6. Rows are NOT
training-eligible: placeholder ABI_ACCEPTED_ORDINAL atoms, no real tokenizer/atom-manifest
binding, no admission gate run. accepted_dataset_tokens remains 0 regardless of this tool's
output.
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

SCHEMA = "CLAY_TRIGGER2_B5_VARIABLE_N_EQUIVARIANCE_CANDIDATE/v1"
ANCESTRY = "trigger2-20260826-b5-variable-n-equivariance-v1"

N_LEVELS_TRAIN_VAL = (2, 3, 4, 6, 8, 12)
N_LEVELS_HOLDOUT = (3, 6, 12)
EXACT_FULL_PERM_N = (2, 3)
SAMPLED_PERM_COUNT = 6

# Entity SETS are canonical (fixed slice, not re-sampled) per N-level and REUSED across
# every episode repeat at that N. This is deliberate: it is what forces each entity name to
# be queried across many different episodes with independently fresh atom draws each time,
# which is required so that entity-name-alone (the only thing eq_text/QUERY exposes) carries
# no aggregate information about target -- otherwise, with too few episodes reusing each
# entity, an entity name can accidentally look like a near-deterministic predictor of its
# (usually singular) observed target across the whole split, which is exactly the kind of
# lexical shortcut the bag-of-words probe below is built to catch (and did catch, in an
# earlier version of this generator that resampled a fresh entity subset per episode instead
# -- see commit history / TRIGGER2_B5_LEAKAGE_AUDIT_REPORT_V1.json for the caught failure).
# HOLDOUT_FROZEN uses an entirely disjoint entity namespace (unit_hNN vs unit_NN), not just a
# disjoint atom pool -- a stricter family-disjointness bar than B0/B1/B4, which only enforce
# atom-pool disjointness.
ENTITY_POOL_TRAIN_VAL = [f"unit_{i:02d}" for i in range(16)]
ENTITY_POOL_HOLDOUT = [f"unit_h{i:02d}" for i in range(16)]

ATOM_POOL_TRAIN_VAL = list(range(200, 260))
ATOM_POOL_HOLDOUT = list(range(260, 300))


def atom_ref(n: int) -> str:
    return f"ABI_ACCEPTED_ORDINAL:{n:03d}"


def row_common(split: str) -> dict:
    return {
        "schema": SCHEMA,
        "curriculum_phase": "B5_VARIABLE_N_CELL_PERMUTATION_EQUIVARIANCE",
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


def presentation_orders(entities: list[str], n: int, rng: random.Random) -> list[tuple[str, ...]]:
    """Returns a list of distinct presentation orders (tuples of entity names) for one
    episode. Exact full S_n for n in EXACT_FULL_PERM_N; SAMPLED_PERM_COUNT distinct random
    permutations otherwise (identity permutation always included as one of them, so the
    canonical order is itself one tested presentation, not skipped)."""
    if n in EXACT_FULL_PERM_N:
        return [tuple(p) for p in itertools.permutations(entities)]
    orders: set[tuple[str, ...]] = {tuple(entities)}
    guard = 0
    while len(orders) < SAMPLED_PERM_COUNT and guard < 10000:
        guard += 1
        cand = entities[:]
        rng.shuffle(cand)
        orders.add(tuple(cand))
    # Sort for byte-reproducible output: set iteration order depends on PYTHONHASHSEED,
    # which is randomized per process by default -- without this, two runs of this exact
    # generator with identical seeded RNGs would emit the SAME rows in a DIFFERENT order
    # (different output bytes/hash), which happened during development (caught by an
    # explicit cross-run determinism check, not assumed).
    return sorted(orders)


def render_row(split: str, episode_id: str, n: int, order: tuple[str, ...],
               true_mapping: dict[str, int], queried: str) -> dict:
    codebook_text = " | ".join(f"{e}=>{atom_ref(true_mapping[e])}" for e in order)
    query_text = f"Which atom is bound to {queried}?"
    prompt = (
        f"CODEBOOK: {codebook_text}\n"
        f"QUERY: {query_text}\n"
        "Answer with exactly one bound atom."
    )
    eq_text = f"QUERY: {query_text}"
    r = row_common(split)
    order_tag = hashlib.sha256("|".join(order).encode("utf-8")).hexdigest()[:8]
    r.update({
        "id": f"B5_{episode_id}_ORD{order_tag}_{queried}",
        "episode_id": episode_id,
        "n": n,
        "entities_presentation_order": list(order),
        "true_mapping": {e: atom_ref(true_mapping[e]) for e in order},
        "queried_entity": queried,
        "queried_position_in_codebook": order.index(queried),
        "target": atom_ref(true_mapping[queried]),
        "prompt": prompt,
        "eq_text": eq_text,
    })
    return r


def gen_split(split: str, n_levels: tuple[int, ...], entity_pool: list[str], atom_pool: list[int], episodes_per_n: int, seed_base: int) -> list[dict]:
    rows: list[dict] = []
    for n in n_levels:
        entities = entity_pool[:n]
        for ep in range(episodes_per_n):
            episode_id = f"{split}_N{n:02d}_E{ep}"
            erng = random.Random(repr((seed_base, n, ep, "episode")))
            atoms = erng.sample(atom_pool, n)
            true_mapping = dict(zip(entities, atoms))
            orng = random.Random(repr((seed_base, n, ep, "orders")))
            orders = presentation_orders(entities, n, orng)
            qrng = random.Random(repr((seed_base, n, ep, "queries")))
            query_count = min(3, n)
            queried_entities = qrng.sample(entities, query_count)
            for order in orders:
                for queried in queried_entities:
                    rows.append(render_row(split, episode_id, n, order, true_mapping, queried))
    return rows


def build_rows() -> list[dict]:
    rows = []
    rows += gen_split("TRAIN", N_LEVELS_TRAIN_VAL, ENTITY_POOL_TRAIN_VAL, ATOM_POOL_TRAIN_VAL, episodes_per_n=10, seed_base=101)
    rows += gen_split("VALIDATION", N_LEVELS_TRAIN_VAL, ENTITY_POOL_TRAIN_VAL, ATOM_POOL_TRAIN_VAL, episodes_per_n=6, seed_base=102)
    rows += gen_split("HOLDOUT_FROZEN", N_LEVELS_HOLDOUT, ENTITY_POOL_HOLDOUT, ATOM_POOL_HOLDOUT, episodes_per_n=6, seed_base=103)
    return rows


def tokenize(text: str) -> list[str]:
    return [w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split() if w]


def dedupe_by_episode_entity(rows: list[dict]) -> list[dict]:
    """Collapse to one row per (episode_id, queried_entity). Presentation order is
    deliberately excluded from eq_text (only the QUERY line survives, and by the
    equivariance property target is identical across all of an episode's presentation
    orders) -- so a single episode contributes multiple STRUCTURALLY IDENTICAL
    (eq_text, target) observations, one per tested presentation order. Feeding those
    duplicates into row-level k-fold CV would let near-duplicate rows leak across the
    train/test fold boundary (same eq_text/target pair seen in both), which is a CV
    methodology bug, not evidence of a real shortcut. Dedupe first; the shortcut probe
    must run on genuinely distinct (episode, queried_entity) observations only."""
    seen: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["episode_id"], r["queried_entity"])
        if key not in seen:
            seen[key] = r
    return list(seen.values())


def bow_shortcut_probe(rows: list[dict], folds: int = 5, seed: int = 20260826) -> dict:
    train = dedupe_by_episode_entity([r for r in rows if r["split"] == "TRAIN"])
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
        "note": "eq_text excludes the codebook block entirely (only the QUERY line remains), so this probe can only ever see which entity is asked about -- it directly tests whether entity NAME alone (independent of codebook content) predicts target, which it must not since atom assignment is freshly resampled per episode.",
    }


def audit(rows: list[dict]) -> dict:
    failures: list[str] = []

    for r in rows:
        expected_target = r["true_mapping"][r["queried_entity"]]
        if r["target"] != expected_target:
            failures.append(f"TARGET_DERIVATION_MISMATCH:{r['id']}")
        if r["queried_entity"] not in r["entities_presentation_order"]:
            failures.append(f"QUERIED_ENTITY_NOT_IN_CODEBOOK:{r['id']}")
        if len(set(r["entities_presentation_order"])) != r["n"]:
            failures.append(f"DUPLICATE_ENTITY_IN_EPISODE:{r['id']}")
        if len(set(r["true_mapping"].values())) != r["n"]:
            failures.append(f"DUPLICATE_ATOM_IN_EPISODE:{r['id']}")

    # Core equivariance property: for a fixed (episode, queried_entity), target must be
    # IDENTICAL across every distinct presentation order tested for that episode.
    by_episode_entity: dict[tuple[str, str], set[str]] = defaultdict(set)
    by_episode_orders: dict[str, set[tuple[str, ...]]] = defaultdict(set)
    episode_n: dict[str, int] = {}
    for r in rows:
        by_episode_entity[(r["episode_id"], r["queried_entity"])].add(r["target"])
        by_episode_orders[r["episode_id"]].add(tuple(r["entities_presentation_order"]))
        episode_n[r["episode_id"]] = r["n"]
    for (episode_id, entity), targets in by_episode_entity.items():
        if len(targets) != 1:
            failures.append(f"EQUIVARIANCE_VIOLATION:{episode_id}:{entity}:{sorted(targets)}")

    # Presentation-order distinctness / expected coverage per episode.
    for episode_id, orders in by_episode_orders.items():
        n = episode_n[episode_id]
        expected = math.factorial(n) if n in EXACT_FULL_PERM_N else SAMPLED_PERM_COUNT
        if len(orders) != expected:
            failures.append(f"PRESENTATION_ORDER_COVERAGE:{episode_id}:got={len(orders)}:expected={expected}")

    def atoms_of(split):
        return {a for r in rows if r["split"] == split for a in r["true_mapping"].values()}

    train_atoms, val_atoms, hold_atoms = atoms_of("TRAIN"), atoms_of("VALIDATION"), atoms_of("HOLDOUT_FROZEN")
    if not hold_atoms.isdisjoint(train_atoms | val_atoms):
        failures.append("HOLDOUT_ATOM_POOL_OVERLAP")
    if not hold_atoms:
        failures.append("HOLDOUT_EMPTY")

    def entities_of(split):
        return {e for r in rows if r["split"] == split for e in r["entities_presentation_order"]}

    train_entities, val_entities, hold_entities = entities_of("TRAIN"), entities_of("VALIDATION"), entities_of("HOLDOUT_FROZEN")
    if not hold_entities.isdisjoint(train_entities | val_entities):
        failures.append("HOLDOUT_ENTITY_NAMESPACE_OVERLAP")
    if not hold_entities:
        failures.append("HOLDOUT_ENTITIES_EMPTY")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    n_coverage = sorted({r["n"] for r in rows})
    split_counts = dict(Counter(r["split"] for r in rows))
    episodes_by_split = {s: len({r["episode_id"] for r in rows if r["split"] == s}) for s in split_counts}

    bow = bow_shortcut_probe(rows)
    if not bow.get("pass", False):
        failures.append("BAG_OF_WORDS_SHORTCUT_PROBE_FAIL")

    return {
        "schema": SCHEMA,
        "rows": len(rows),
        "split_counts": split_counts,
        "episodes_by_split": episodes_by_split,
        "n_levels_covered": n_coverage,
        "exact_full_permutation_n": EXACT_FULL_PERM_N,
        "sampled_permutation_count": SAMPLED_PERM_COUNT,
        "holdout_entity_namespace_disjoint_from_train_val": hold_entities.isdisjoint(train_entities | val_entities),
        "holdout_atom_pool_disjoint_from_train_val": hold_atoms.isdisjoint(train_atoms | val_atoms),
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
        print("REFUSING to write B5 candidate rows: audit did not pass.", file=sys.stderr)
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
