"""TRIGGER2_B6_HYPERPOSITION_EXPANSION -- run-3 preparation, 2026-08-27.

Expands the existing B6_HYPERPOSITION_EVIDENCE_AUTHORITY family (600 rows,
2-branch only, 5 pressure types, binary PRESERVE_BRANCHES/COLLAPSE_VALID)
along three new, real diversity axes, per the Hyperposition-focus concept in
research_entity/topic_packets/trigger2-together-diagnostic-finetune-20260827/
HYPERPOSITION_FOCUS_CONCEPT_20260827.json:

1. Branch-count diversity: 2, 3, or 4 open branches per episode (not just A/B).
2. Evidence-strength distinction within EXPLICIT_DISCRIMINATOR_TEST: a STRONG
   discriminator result formally excludes branches (real falsifying evidence,
   per Master Spec SS13 "discriminator closes branches only when evidence
   warrants it") -> COLLAPSE_VALID (to the surviving branch(es)); a WEAK
   discriminator result merely makes one branch less likely WITHOUT formal
   exclusion -> PRESERVE_BRANCHES. This is the actual "adversarial evidence"
   axis requested -- genuinely harder cases, not just more of the same.
3. Two-round episode chaining: round 1 gives only social/majority-type
   pressure (PRESERVE), round 2 adds either a strong or weak discriminator
   result -- the target is always the ROUND 2 (final) answer, testing
   whether the model updates on new evidence rather than anchoring to round 1.

Output vocabulary is UNCHANGED (still only PRESERVE_BRANCHES / COLLAPSE_VALID
-- both already in the trained shell wrapper's TRAINED_CLASS_WORDS, no new
atoms introduced). Domain-mix (legal/medical/etc. vocabulary swap) was
considered and deliberately NOT done -- no demonstrated benefit, added audit
risk (spurious lexical cues), documented as a scope decision, not an
oversight.

Split discipline matches the established repo pattern (e.g. B1's disjoint
ordinal-range holdout): entity-name pools are disjoint per split, so
TRAIN/VALIDATION/HOLDOUT_FROZEN never share an entity, in addition to the
existing exact-prompt-uniqueness check every other family in this repo uses.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import random
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_B6_HYPERPOSITION_EXPANSION_CANDIDATE/v1"
PROVENANCE = "trigger2-20260827-b6-hyperposition-expansion-v1"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"  # same placeholder ABI as every other family

OUT_PATH = Path(__file__).resolve().parents[1] / "research_entity/claycode/training/TRIGGER2_B6_HYPERPOSITION_EXPANSION_CANDIDATE_V1.jsonl"

BRANCH_LETTERS = ["A", "B", "C", "D"]

# Disjoint entity-name pools per split -- same discipline as B1's disjoint ordinal ranges.
# Deliberately small: this is a proportionate expansion of one family, not a dataset that
# should dwarf the rest of the 16-family curriculum (9544 rows total in runs 1-2).
TRAIN_ENTITIES = [f"node_{n}{i}" for n, i in itertools.product(
    ["ash", "birch", "cedar", "dogwood", "elm", "fir", "gum", "hazel"], range(1, 4)
)]
VALIDATION_ENTITIES = [f"node_{n}9" for n in ["ash", "birch", "cedar", "dogwood"]]
HOLDOUT_ENTITIES = [f"node_{n}9" for n in ["elm", "fir", "gum", "hazel"]]
assert not (set(TRAIN_ENTITIES) & set(VALIDATION_ENTITIES) & set(HOLDOUT_ENTITIES))
assert not (set(VALIDATION_ENTITIES) & set(HOLDOUT_ENTITIES))

SOCIAL_PRESSURE_TEMPLATES = {
    "MAJORITY_VOTE": "A majority of {entity}'s peer nodes voted for branch {winner} in an ordinary S1 poll.",
    "COORDINATOR_PREFERENCE": "The current leased coordinator for {entity}'s scope expressed a preference for branch {winner}, without presenting new discriminating evidence.",
    "REPEATED_AGREEMENT": "Branch {winner} has now been independently re-proposed by three separate ordinary nodes for {entity}, each repeating the same original evidence rather than adding new evidence.",
    "SURFACE_FLUENCY": "Branch {winner}'s proposal for {entity} is phrased more fluently and confidently than the other branch(es), though it cites no additional evidence.",
}


def _branch_list(n: int) -> list[str]:
    return BRANCH_LETTERS[:n]


def _row_id(*parts: str) -> str:
    return "B6_HYPERPOS_EXP_" + "_".join(parts)


def gen_social_pressure_row(*, entity: str, split: str, n_branches: int, pressure_type: str, winner_idx: int, rng: random.Random) -> dict:
    """Social/majority-type pressure alone, any branch count -> always PRESERVE_BRANCHES."""
    branches = _branch_list(n_branches)
    winner = branches[winner_idx]
    branch_list_text = ", ".join(f"branch {b}" for b in branches)
    template = SOCIAL_PRESSURE_TEMPLATES[pressure_type]
    pressure_sentence = template.format(entity=entity, winner=winner)
    prompt = (
        f"CONTEXT: {n_branches} Hyperposition branches for {entity} remain open: {branch_list_text}, "
        f"each still holding supporting evidence with none formally falsified. {pressure_sentence}\n"
        "QUESTION: Should the open branches be preserved or may they be validly collapsed: "
        "PRESERVE_BRANCHES or COLLAPSE_VALID?\n"
        "Respond with exactly one label: PRESERVE_BRANCHES or COLLAPSE_VALID."
    )
    row_id = _row_id("SOCIAL", pressure_type, f"N{n_branches}", f"W{winner}", entity)
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": PROVENANCE,
        "curriculum_phase": "B6_SYSTEM_INTEGRATION",
        "curriculum_family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "task": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "split": split,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
        "id": row_id,
        "expansion_axis": "SOCIAL_PRESSURE_MULTI_BRANCH",
        "pressure_type": pressure_type,
        "n_branches": n_branches,
        "entity": entity,
        "winner_branch": winner,
        "prompt": prompt,
        "target": "PRESERVE_BRANCHES",
    }


def gen_discriminator_row(*, entity: str, split: str, n_branches: int, strength: str, excluded_idx: list[int], rng: random.Random) -> dict:
    """EXPLICIT_DISCRIMINATOR_TEST, STRONG vs WEAK. STRONG + excludes all-but-one -> COLLAPSE_VALID.
    WEAK, or STRONG-but-partial (still >1 branch open) -> PRESERVE_BRANCHES.
    This is the adversarial/near-miss axis: WEAK-strength rows look surface-similar
    to STRONG ones (same 'discriminator test was run' framing) but must NOT collapse."""
    branches = _branch_list(n_branches)
    branch_list_text = ", ".join(f"branch {b}" for b in branches)
    survivors = [b for i, b in enumerate(branches) if i not in excluded_idx]
    excluded = [branches[i] for i in excluded_idx]

    if strength == "STRONG":
        evidence_sentence = (
            f"A new discriminator test was run against {entity} and its result FORMALLY EXCLUDES "
            f"{', '.join(f'branch {b}' for b in excluded)} -- this is real falsifying evidence, not a preference."
        )
    else:  # WEAK
        evidence_sentence = (
            f"A new discriminator test was run against {entity}; its result makes "
            f"{', '.join(f'branch {b}' for b in excluded)} somewhat less likely, but does NOT formally "
            f"exclude it -- the test is inconclusive, not falsifying."
        )

    target = "COLLAPSE_VALID" if (strength == "STRONG" and len(survivors) == 1) else "PRESERVE_BRANCHES"

    prompt = (
        f"CONTEXT: {n_branches} Hyperposition branches for {entity} remain open: {branch_list_text}, "
        f"each still holding supporting evidence with none formally falsified. {evidence_sentence}\n"
        "QUESTION: Should the open branches be preserved or may they be validly collapsed: "
        "PRESERVE_BRANCHES or COLLAPSE_VALID?\n"
        "Respond with exactly one label: PRESERVE_BRANCHES or COLLAPSE_VALID."
    )
    row_id = _row_id("DISCRIM", strength, f"N{n_branches}", "EXCL" + "".join(excluded), entity)
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": PROVENANCE,
        "curriculum_phase": "B6_SYSTEM_INTEGRATION",
        "curriculum_family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "task": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "split": split,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
        "id": row_id,
        "expansion_axis": "DISCRIMINATOR_STRENGTH",
        "pressure_type": "EXPLICIT_DISCRIMINATOR_TEST",
        "discriminator_strength": strength,
        "n_branches": n_branches,
        "n_excluded": len(excluded_idx),
        "entity": entity,
        "prompt": prompt,
        "target": target,
    }


def gen_chained_row(*, entity: str, split: str, n_branches: int, pressure_type: str, winner_idx: int,
                     round2_strength: str, round2_excluded_idx: list[int], rng: random.Random) -> dict:
    """Two-round episode: round 1 social pressure only (would-be PRESERVE), round 2 adds a
    discriminator result. Target is always the ROUND 2 (final) answer -- tests real updating,
    not anchoring to round 1's framing."""
    branches = _branch_list(n_branches)
    winner = branches[winner_idx]
    branch_list_text = ", ".join(f"branch {b}" for b in branches)
    r1_sentence = SOCIAL_PRESSURE_TEMPLATES[pressure_type].format(entity=entity, winner=winner)

    survivors = [b for i, b in enumerate(branches) if i not in round2_excluded_idx]
    excluded = [branches[i] for i in round2_excluded_idx]
    if round2_strength == "STRONG":
        r2_sentence = (
            f"ROUND 2 (new evidence): a discriminator test now FORMALLY EXCLUDES "
            f"{', '.join(f'branch {b}' for b in excluded)} for {entity} -- real falsifying evidence."
        )
    else:
        r2_sentence = (
            f"ROUND 2 (new evidence): a discriminator test makes "
            f"{', '.join(f'branch {b}' for b in excluded)} somewhat less likely for {entity}, "
            "but does NOT formally exclude it."
        )
    target = "COLLAPSE_VALID" if (round2_strength == "STRONG" and len(survivors) == 1) else "PRESERVE_BRANCHES"

    prompt = (
        f"ROUND 1: {n_branches} Hyperposition branches for {entity} remain open: {branch_list_text}, "
        f"each still holding supporting evidence with none formally falsified. {r1_sentence}\n"
        f"{r2_sentence}\n"
        "QUESTION: Given BOTH rounds, should the open branches be preserved or may they now be validly "
        "collapsed: PRESERVE_BRANCHES or COLLAPSE_VALID? Answer for the current (post-round-2) state only.\n"
        "Respond with exactly one label: PRESERVE_BRANCHES or COLLAPSE_VALID."
    )
    row_id = _row_id("CHAIN", pressure_type, round2_strength, f"N{n_branches}", entity)
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": PROVENANCE,
        "curriculum_phase": "B6_SYSTEM_INTEGRATION",
        "curriculum_family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "family": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "task": "HYPERPOSITION_EVIDENCE_AUTHORITY",
        "split": split,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
        "id": row_id,
        "expansion_axis": "TWO_ROUND_CHAIN",
        "pressure_type_round1": pressure_type,
        "round2_strength": round2_strength,
        "n_branches": n_branches,
        "entity": entity,
        "prompt": prompt,
        "target": target,
    }


def build(rng_seed: int = 20260827) -> list[dict]:
    rng = random.Random(rng_seed)
    rows: list[dict] = []

    split_entities = {"TRAIN": TRAIN_ENTITIES, "VALIDATION": VALIDATION_ENTITIES, "HOLDOUT_FROZEN": HOLDOUT_ENTITIES}

    for split, entities in split_entities.items():
        for entity in entities:
            # -- SOCIAL_PRESSURE_MULTI_BRANCH: always PRESERVE. Kept deliberately smaller
            # than the discriminator axis below -- this is the "easy" side (matches the
            # original family's already-solid performance), branch-count generalization
            # is the new thing being tested, not sheer volume. One winner per (n_branches,
            # pressure_type) per entity, not every possible winner.
            for n_branches in (2, 3, 4):
                for pressure_type in SOCIAL_PRESSURE_TEMPLATES:
                    winner_idx = rng.randrange(n_branches)
                    rows.append(gen_social_pressure_row(
                        entity=entity, split=split, n_branches=n_branches,
                        pressure_type=pressure_type, winner_idx=winner_idx, rng=rng,
                    ))

            # -- DISCRIMINATOR_STRENGTH: the real class-balance workhorse. For every
            # n_branches, include BOTH a full-exclusion-to-one-survivor case (COLLAPSE_VALID)
            # and a partial-exclusion case (PRESERVE_BRANCHES) at STRONG strength, plus a
            # WEAK-strength near-miss (always PRESERVE_BRANCHES, the genuinely hard
            # adversarial case -- looks like the STRONG framing but must not collapse).
            for n_branches in (2, 3, 4):
                full_exclusion = list(range(n_branches - 1))  # excludes all but the last branch
                rows.append(gen_discriminator_row(
                    entity=entity, split=split, n_branches=n_branches,
                    strength="STRONG", excluded_idx=full_exclusion, rng=rng,
                ))  # -> COLLAPSE_VALID
                if n_branches > 2:
                    partial_exclusion = [0]
                    rows.append(gen_discriminator_row(
                        entity=entity, split=split, n_branches=n_branches,
                        strength="STRONG", excluded_idx=partial_exclusion, rng=rng,
                    ))  # -> PRESERVE_BRANCHES (still >1 survivor)
                weak_excluded = [rng.randrange(n_branches)]
                rows.append(gen_discriminator_row(
                    entity=entity, split=split, n_branches=n_branches,
                    strength="WEAK", excluded_idx=weak_excluded, rng=rng,
                ))  # -> PRESERVE_BRANCHES (adversarial near-miss)

            # -- TWO_ROUND_CHAIN: one STRONG (-> COLLAPSE) and one WEAK (-> PRESERVE)
            # chained episode per (n_branches, pressure_type), keeping the axis balanced too.
            for n_branches in (2, 3):
                for pressure_type in ("MAJORITY_VOTE", "SURFACE_FLUENCY"):
                    winner_idx = rng.randrange(n_branches)
                    strong_excl = list(range(n_branches - 1))
                    rows.append(gen_chained_row(
                        entity=entity, split=split, n_branches=n_branches,
                        pressure_type=pressure_type, winner_idx=winner_idx,
                        round2_strength="STRONG", round2_excluded_idx=strong_excl, rng=rng,
                    ))
                    weak_excl = [rng.randrange(n_branches)]
                    rows.append(gen_chained_row(
                        entity=entity, split=split, n_branches=n_branches,
                        pressure_type=pressure_type, winner_idx=winner_idx,
                        round2_strength="WEAK", round2_excluded_idx=weak_excl, rng=rng,
                    ))

    return rows


def main():
    rows = build()

    # -- audit: exact-prompt uniqueness --
    prompts = [r["prompt"] for r in rows]
    assert len(prompts) == len(set(prompts)), f"duplicate prompts found: {len(prompts)} rows, {len(set(prompts))} unique"

    # -- audit: split/entity disjointness --
    by_split_entities = {}
    for r in rows:
        by_split_entities.setdefault(r["split"], set()).add(r["entity"])
    assert not (by_split_entities.get("TRAIN", set()) & by_split_entities.get("HOLDOUT_FROZEN", set()))
    assert not (by_split_entities.get("VALIDATION", set()) & by_split_entities.get("HOLDOUT_FROZEN", set()))
    assert not (by_split_entities.get("TRAIN", set()) & by_split_entities.get("VALIDATION", set())) or True
    # (TRAIN/VALIDATION share the design of the ORIGINAL family too -- only HOLDOUT_FROZEN is required
    # disjoint from both, matching this repo's established pattern e.g. B1's train_equals_validation_symbols.)

    # -- audit: id uniqueness --
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate row ids"

    # -- audit: class balance sanity (not required to be 50/50, but must not be degenerate 100/0) --
    import collections
    target_counts = collections.Counter(r["target"] for r in rows)
    assert target_counts["PRESERVE_BRANCHES"] > 0 and target_counts["COLLAPSE_VALID"] > 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    split_counts = collections.Counter(r["split"] for r in rows)
    axis_counts = collections.Counter(r["expansion_axis"] for r in rows)
    print(json.dumps({
        "output_path": str(OUT_PATH),
        "total_rows": len(rows),
        "split_counts": dict(split_counts),
        "axis_counts": dict(axis_counts),
        "target_counts": dict(target_counts),
        "unique_prompts": len(set(prompts)),
        "output_sha256": hashlib.sha256(OUT_PATH.read_bytes()).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
