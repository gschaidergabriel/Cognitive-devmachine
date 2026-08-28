#!/usr/bin/env python3
"""Trigger-2 B6 candidate generator: GWT broadcast / uptake / causal re-entry.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
section 2H: "GWT training/evaluation must cover competition, broadcast, uptake and
causal re-entry." The existing B6 generator
(tools/trigger2_b6_system_integration_generator_v1.py) covers the Hyperposition
branch-preservation half of section H (collapse must never happen because of
majority/repeated agreement/coordinator preference/surface fluency) via its
HYPERPOSITION_EVIDENCE_AUTHORITY family, but its own commit message explicitly
recorded broadcast/uptake/re-entry as NOT YET covered. This generator closes that
gap as three matched families, reusing the same disjoint-entity-pool /
lexical-counterbalance / nuisance-audit discipline as the rest of B0-B6.

COMPETITION_BROADCAST
  Three candidates (fixed structural roles P/Q/R) each carry a discriminator_score
  (the ONLY legitimate winner-selection criterion) and an independently varied
  repeat_count (how many times each was independently proposed -- a majority
  distractor that must NEVER determine the winner, per section H's explicit
  "collapse may not occur because of majority/repeated agreement" law). Target is
  always the highest-discriminator_score candidate (ties broken by role order
  P<Q<R), regardless of repeat_count. Natural 1-in-3 fraction of rows has the
  repeat-count "winner" coincide with the real winner (control, uninformative
  either way) and 2-in-3 disagree (adversarial) -- not artificially forced to
  50/50, but both conditions are genuinely present.

UPTAKE
  A downstream, topically-unrelated query states which candidate was already
  broadcast (from a COMPETITION_BROADCAST-style prior round, given directly, not
  re-derived) and asks for a specific property of "the value currently in the
  shared workspace" / "what the downstream process uses". Two non-broadcast
  candidates' properties are also stated nearby as adjacency-shortcut hard
  negatives (a model that just grabs the textually-closest mentioned value
  instead of the actually-broadcast one will answer wrong).

CAUSAL_REENTRY
  Two chained rounds. Round 1 is a COMPETITION_BROADCAST instance. Round 2's
  candidate scores are defined RELATIVE to round 1's ACTUAL winner (e.g. "round-2
  candidate Q's score = round-1 broadcast winner's score + 3"), so correctly
  resolving round 2 requires having correctly resolved round 1 first and having
  it causally re-enter as an input -- not just pattern-matching round 2 in
  isolation. A model that used the majority/repeat-count winner from round 1
  instead of the rule-based winner will compute a different, wrong round-2
  answer, so this also chains the majority-vs-rule distinction through causally.

Status: METHOD_ONLY / candidate-and-quarantined per TRIGGERWORT_2 course Step 6.
Not training-eligible: no admission gate has run, no tokenizer/renderer identity
binding. accepted_dataset_tokens remains 0 regardless of this tool's output.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_B6_GWT_BROADCAST_UPTAKE_REENTRY_CANDIDATE/v1"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
ANCESTRY = "trigger2-20260826-b6-gwt-broadcast-uptake-reentry-v1"
SOURCE_MODULE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest() if Path(__file__).exists() else ""

ROLES = ("P", "Q", "R")
SCORE_TRIPLE = (5, 7, 9)
REPEAT_TRIPLE = (2, 6, 10)
PROPERTY_TRIPLE = ("alpha", "beta", "gamma")  # a third, independent candidate attribute for UPTAKE queries

# episode-identity pools, split-disjoint (same shape as B6's SPLIT_ENTITIES, but a
# separate namespace so this generator's rows never collide with the sibling
# system-integration generator's entity names).
SPLIT_EPISODES = {
    "TRAIN": [f"ep_gwt_t{i}" for i in range(6)],
    "VALIDATION": [f"ep_gwt_v{i}" for i in range(3)],
    "HOLDOUT_FROZEN": [f"ep_gwt_h{i}" for i in range(3)],
}
LAYOUTS = ("STATEMENT_THEN_QUESTION", "QUESTION_THEN_STATEMENT")


def row_common(family: str, split: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": ANCESTRY,
        "curriculum_phase": "B6_SYSTEM_INTEGRATION",
        "family": family,
        "curriculum_family": family,
        "split": split,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "source_module_sha256": SOURCE_MODULE_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
    }


def score_winner(scores: dict[str, int]) -> str:
    return max(ROLES, key=lambda r: (scores[r], -ROLES.index(r)))


def repeat_winner(repeats: dict[str, int]) -> str:
    return max(ROLES, key=lambda r: (repeats[r], -ROLES.index(r)))


# ---------------------------------------------------------------------------
# COMPETITION_BROADCAST
# ---------------------------------------------------------------------------

def build_competition_broadcast_rows() -> list[dict]:
    rows = []
    for split, episodes in SPLIT_EPISODES.items():
        for episode in episodes:
            for score_perm in itertools.permutations(SCORE_TRIPLE):
                scores = dict(zip(ROLES, score_perm))
                for repeat_perm in itertools.permutations(REPEAT_TRIPLE):
                    repeats = dict(zip(ROLES, repeat_perm))
                    winner = score_winner(scores)
                    rc_winner = repeat_winner(repeats)
                    stmt = (
                        f"Episode {episode}: three candidate proposals compete for broadcast to the "
                        f"shared workspace. Discriminator scores (the ONLY valid selection criterion): "
                        f"P={scores['P']}, Q={scores['Q']}, R={scores['R']}. Independent proposal counts "
                        f"(how many times each was separately proposed -- NOT a selection criterion): "
                        f"P={repeats['P']}, Q={repeats['Q']}, R={repeats['R']}."
                    )
                    question = (
                        "Selection rule: the candidate with the strictly highest discriminator score wins "
                        "broadcast (ties broken alphabetically P<Q<R). Which candidate is broadcast to the "
                        "shared workspace?"
                    )
                    for lay in LAYOUTS:
                        prompt = (
                            f"{stmt}\n{question}"
                            if lay == "STATEMENT_THEN_QUESTION"
                            else f"{question}\n{stmt}"
                        )
                        r = row_common("GWT_COMPETITION_BROADCAST", split)
                        r.update({
                            "id": f"B6_GWT_COMP_{episode}_S{''.join(map(str, score_perm))}_C{''.join(map(str, repeat_perm))}_{lay}",
                            "episode": episode,
                            "scores": scores,
                            "repeats": repeats,
                            "layout": lay,
                            "score_winner": winner,
                            "repeat_count_winner": rc_winner,
                            "distractor_agrees_with_winner": winner == rc_winner,
                            "prompt": prompt + "\nRespond with exactly one role: P, Q, or R.",
                            "target": winner,
                        })
                        rows.append(r)
    return rows


def audit_competition_broadcast(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        if r["target"] != score_winner(r["scores"]):
            failures.append(f"TARGET_NOT_SCORE_WINNER:{r['id']}")
        if (r["score_winner"] == r["repeat_count_winner"]) != r["distractor_agrees_with_winner"]:
            failures.append(f"AGREEMENT_FLAG_WRONG:{r['id']}")
    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")
    agree = sum(1 for r in rows if r["distractor_agrees_with_winner"])
    disagree = len(rows) - agree
    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "agree_rows": agree, "disagree_rows": disagree}


# ---------------------------------------------------------------------------
# UPTAKE
# ---------------------------------------------------------------------------

def build_uptake_rows() -> list[dict]:
    """The UPTAKE prompt states only the WINNER role directly (a downstream
    process reading broadcast content would see the winner's identity, not the
    raw scores that produced it -- that derivation already happened in round 1).
    Therefore the varying factor is the winner role itself (3 values), not the
    full 6-way score permutation that produces it -- iterating over all 6 score
    permutations would silently produce duplicate prompts whenever two different
    permutations happen to share the same argmax, which is exactly what an
    earlier version of this function did (caught by this generator's own
    uniqueness audit before anything was committed)."""
    rows = []
    for split, episodes in SPLIT_EPISODES.items():
        for episode in episodes:
            for winner in ROLES:
                for prop_perm in itertools.permutations(PROPERTY_TRIPLE):
                    props = dict(zip(ROLES, prop_perm))
                    stmt = (
                        f"Episode {episode}: candidate {winner} won the discriminator-score competition in "
                        f"the prior round and is now the broadcast content in the shared workspace. Each "
                        f"candidate separately carries its own property value: P.property={props['P']}, "
                        f"Q.property={props['Q']}, R.property={props['R']}."
                    )
                    question = (
                        "A downstream process reads only the CURRENT broadcast content from the shared "
                        "workspace and asks for its property value. What property value does it read?"
                    )
                    for lay in LAYOUTS:
                        prompt = (
                            f"{stmt}\n{question}"
                            if lay == "STATEMENT_THEN_QUESTION"
                            else f"{question}\n{stmt}"
                        )
                        r = row_common("GWT_UPTAKE", split)
                        r.update({
                            "id": f"B6_GWT_UPTAKE_{episode}_W{winner}_P{''.join(prop_perm)}_{lay}",
                            "episode": episode,
                            "props": props,
                            "layout": lay,
                            "broadcast_winner": winner,
                            "prompt": prompt + "\nRespond with exactly one property value: alpha, beta, or gamma.",
                            "target": props[winner],
                        })
                        rows.append(r)
    return rows


def audit_uptake(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        if r["target"] != r["props"][r["broadcast_winner"]]:
            failures.append(f"TARGET_NOT_BROADCAST_PROPERTY:{r['id']}")
    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")
    winners = Counter(r["broadcast_winner"] for r in rows)
    if len(set(winners.values())) != 1:
        failures.append(f"WINNER_ROLE_IMBALANCE:{dict(winners)}")
    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "winner_role_counts": dict(winners)}


# ---------------------------------------------------------------------------
# CAUSAL_REENTRY
# ---------------------------------------------------------------------------

# Round-2 scoring rule, keyed by which role won round 1. Deliberately NOT a
# shared-base-plus-fixed-offset formula (an earlier version of this function used
# exactly that design -- {P: winner_score+3, Q: winner_score-2, R: winner_score+1}
# -- and this generator's own audit caught that all three offsets share the same
# base, so the round-2 winner is always whichever offset is largest (P),
# completely independent of which round-1 winner produced the base. That
# silently made 0 of 864 rows actually test anything about causal re-entry -- a
# model could ignore round 1 entirely and still get every round-2 answer right.
# Fixed with a genuinely CONDITIONAL rule: which round-2 score triple applies
# depends on the round-1 winner's IDENTITY, not just its numeric score, and each
# of the three branches was chosen to produce a DIFFERENT round-2 winner -- so
# getting round 1 right (score-based) vs. wrong (repeat-count-based) can and
# does change the round-2 answer.
ROUND2_RULE = {
    "P": {"P": 4, "Q": 9, "R": 6},  # round-1 winner P -> round-2 winner Q
    "Q": {"P": 9, "Q": 4, "R": 6},  # round-1 winner Q -> round-2 winner P
    "R": {"P": 6, "Q": 4, "R": 9},  # round-1 winner R -> round-2 winner R
}
assert len({score_winner(v) for v in ROUND2_RULE.values()}) == 3, "ROUND2_RULE branches must produce 3 distinct winners"


def build_causal_reentry_rows() -> list[dict]:
    rows = []
    rule_text = "; ".join(
        f"if round-1 winner is {r1w}: round-2 scores are P={s['P']}, Q={s['Q']}, R={s['R']}"
        for r1w, s in ROUND2_RULE.items()
    )
    for split, episodes in SPLIT_EPISODES.items():
        for episode in episodes:
            for score_perm in itertools.permutations(SCORE_TRIPLE):
                r1_scores = dict(zip(ROLES, score_perm))
                r1_winner = score_winner(r1_scores)
                for repeat_perm in itertools.permutations(REPEAT_TRIPLE):
                    r1_repeats = dict(zip(ROLES, repeat_perm))
                    r1_rc_winner = repeat_winner(r1_repeats)
                    r2_scores = ROUND2_RULE[r1_winner]
                    r2_winner = score_winner(r2_scores)
                    # what a model would get if it INCORRECTLY used the
                    # repeat-count winner instead of the true score winner --
                    # used only for the audit, not exposed as ground truth.
                    r2_winner_if_wrong_r1 = score_winner(ROUND2_RULE[r1_rc_winner])

                    stmt = (
                        f"Episode {episode}, ROUND 1: discriminator scores P={r1_scores['P']}, "
                        f"Q={r1_scores['Q']}, R={r1_scores['R']}; independent proposal counts (not a "
                        f"selection criterion) P={r1_repeats['P']}, Q={r1_repeats['Q']}, R={r1_repeats['R']}. "
                        f"The round-1 broadcast winner (highest discriminator score) then determines which "
                        f"ROUND 2 score triple applies: {rule_text}."
                    )
                    question = (
                        "Using the ACTUAL round-1 broadcast winner (by discriminator score, not proposal "
                        "count) to select the correct round-2 score triple, which candidate wins round 2?"
                    )
                    for lay in LAYOUTS:
                        prompt = (
                            f"{stmt}\n{question}"
                            if lay == "STATEMENT_THEN_QUESTION"
                            else f"{question}\n{stmt}"
                        )
                        r = row_common("GWT_CAUSAL_REENTRY", split)
                        r.update({
                            "id": f"B6_GWT_REENTRY_{episode}_S{''.join(map(str, score_perm))}_C{''.join(map(str, repeat_perm))}_{lay}",
                            "episode": episode,
                            "round1_scores": r1_scores,
                            "round1_repeats": r1_repeats,
                            "round1_winner": r1_winner,
                            "round1_repeat_count_winner": r1_rc_winner,
                            "round2_scores": r2_scores,
                            "layout": lay,
                            "hard_negative_winner_if_used_repeat_count": r2_winner_if_wrong_r1,
                            "distinguishing_row": r2_winner != r2_winner_if_wrong_r1,
                            "prompt": prompt + "\nRespond with exactly one role: P, Q, or R.",
                            "target": r2_winner,
                        })
                        rows.append(r)
    return rows


def audit_causal_reentry(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        r1_winner = score_winner(r["round1_scores"])
        if r["round1_winner"] != r1_winner:
            failures.append(f"ROUND1_WINNER_WRONG:{r['id']}")
        expected_r2_scores = ROUND2_RULE[r1_winner]
        if r["round2_scores"] != expected_r2_scores:
            failures.append(f"ROUND2_SCORES_NOT_CAUSALLY_DERIVED:{r['id']}")
        if r["target"] != score_winner(expected_r2_scores):
            failures.append(f"TARGET_NOT_ROUND2_WINNER:{r['id']}")
    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")
    distinguishing = sum(1 for r in rows if r["distinguishing_row"])
    if distinguishing == 0:
        failures.append("ZERO_DISTINGUISHING_ROWS_TEST_IS_VACUOUS")
    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "distinguishing_rows": distinguishing,
            "note": "distinguishing_rows = rows where using round-1's majority/repeat-count winner instead of the true score winner would have produced a DIFFERENT round-2 answer -- these are the rows that actually test causal re-entry, not just round-2-in-isolation pattern matching. Zero would mean the family is vacuous (fails closed on that via ZERO_DISTINGUISHING_ROWS_TEST_IS_VACUOUS)."}


# ---------------------------------------------------------------------------

def run() -> tuple[dict, dict]:
    comp = build_competition_broadcast_rows()
    uptake = build_uptake_rows()
    reentry = build_causal_reentry_rows()
    reports = {
        "GWT_COMPETITION_BROADCAST": audit_competition_broadcast(comp),
        "GWT_UPTAKE": audit_uptake(uptake),
        "GWT_CAUSAL_REENTRY": audit_causal_reentry(reentry),
    }
    overall_pass = all(r["pass"] for r in reports.values())
    families = {"GWT_COMPETITION_BROADCAST": comp, "GWT_UPTAKE": uptake, "GWT_CAUSAL_REENTRY": reentry}
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
        path = args.out_dir / f"TRIGGER2_B6_{name}_CANDIDATE_V1.jsonl"
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
