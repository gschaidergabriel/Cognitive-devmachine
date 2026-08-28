#!/usr/bin/env python3
"""Trigger-2 canonical atom-split manifest + cross-family placeholder remap.

Context: SUPERVISOR_INBOX.json flagged trigger2_canonical_tokenizer_abi_binding
as a P1_BLOCKER after the 2026-08-26 claude-code-lead cross-family consolidation
pass found 168 distinct placeholder ABI_ACCEPTED_ORDINAL:NN values across the
B0-B6 candidate families (B0-B3 use 0-14, B4 uses 20-99, B5 uses 200-299ish),
well beyond the course document's declared 46 real accepted atoms
(TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md, section 4).

Scope established before writing any code here (claude-code-lead, verified, not
assumed):
  - No single row in any family shows more than ~24 distinct atoms
    simultaneously (B4's worst case: capacity K<=16 real bindings + up to 8
    distinct decoy fillers). B5's worst case is N<=12. B0-B3 never exceed 3.
    46 is never a per-row capacity constraint for any existing family.
  - The 168-placeholder count is pure cross-family ID bookkeeping over MANY
    different rows/episodes (episode-local meaning, exactly per the course's own
    "meaning is not permanently hardwired to an atom" law), not a structural
    requirement for more than 46 real atoms to exist simultaneously.
  - Therefore: a many-to-few REMAPPING from each family's own placeholder
    ordinals onto a single shared 46-real-atom namespace is feasible without
    touching any family's semantics, splits, templates or already-committed,
    already-audited row content.

The 46 real accepted atom NAMES and the 1 rejected name ("or") are sourced from
research_entity/global/j-space/research/
2026-08-26_TRIGGER2_ABI_SYMBOL_PRIOR_CONTEXTUAL_TOKEN_AUDIT_V1_GPT56SOL.json
(chatgpt-secondary research delta, itself citing the ingested external XENO
vector-language handoff package, abi/MANIFEST.json sha256
0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11 -- the SAME
hash every family's ABI_MANIFEST_SHA256 constant already cites). This is the
best available ground truth in this repo; it is still NOT the actual
atoms_index.json (exact atom-to-token-ID table) or exact tokenizer/renderer
identity, both of which remain explicitly open per that same research delta
("remaining_identity_gaps") -- so this manifest closes the SPLIT/NAMESPACE
design question, not the full real-tokenizer-binding gate. Real rendering
remains a separate, later, still-blocked step (TRIGGER2_ABI_CONTEXTUAL_RENDER_GATE/v1,
SPECIFIED_NOT_EXECUTED in that same delta).

Split design: the 46 atoms are stratified into two groups the source delta
itself flags as needing separate treatment (H_T2_ABI_01: language-bearing atoms
may carry pretrained semantic priors that neutral alphanumeric atoms do not) --
26 letters + 10 digits = 36 "neutral" atoms, and 10 words (yes/no/true/false/
maybe/unknown/if/then/not/and) = 10 "language-bearing" atoms. Each stratum is
independently split roughly 80/20 (matching the ~80/20 TRAIN:HOLDOUT ratio the
existing blueprint_v2 donor already uses, 12:3) via a deterministic hashlib-based
ranking -- not a hand-picked "last few in the list" choice, and not random
(reproducible from the atom names + this file's content alone). This keeps both
strata represented in both TRAIN_AND_VALIDATION and HOLDOUT_FROZEN, so the
source delta's own recommended neutral-vs-language-bearing comparison remains
possible on either side of the split.

VALIDATION reuses the same pool as TRAIN (not a separate 3rd stratum) --
matching blueprint_v2's own train_symbols == validation_symbols design, since
VALIDATION carries no held-out-symbol generalization claim in any existing
family; only HOLDOUT_FROZEN is a disjoint, unseen pool.

Empirically verified (not assumed) against the actual committed data before
this tool was written: of 195 distinct placeholder ordinals used across all
14 committed B0-B6 JSONL files, 132 legitimately appear in both TRAIN and
VALIDATION rows (expected, same as blueprint_v2's donor design) and exactly 20
(B4's ATOM_POOL_DECOY, ordinals 80-99) appear in all three splits -- these are
pure noise/distractor filler atoms that are NEVER a row's actual target in any
family, verified by direct inspection of tools/trigger2_b4_capacity_interference_generator_v1.py.
After excluding that known decoy range, ZERO placeholder ordinals cross the
TRAIN/VALIDATION <-> HOLDOUT_FROZEN boundary -- the split-role of every
remaining placeholder is well-defined and consistent everywhere it is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "CLAY_TRIGGER2_CANONICAL_ATOM_SPLIT_MANIFEST/v1"
SOURCE_DELTA = "research_entity/global/j-space/research/2026-08-26_TRIGGER2_ABI_SYMBOL_PRIOR_CONTEXTUAL_TOKEN_AUDIT_V1_GPT56SOL.json"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"

NEUTRAL_ATOMS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + tuple("0123456789")
LANGUAGE_BEARING_ATOMS = ("yes", "no", "true", "false", "maybe", "unknown", "if", "then", "not", "and")
REJECTED_ATOM = "or"
ALL_ACCEPTED_ATOMS = NEUTRAL_ATOMS + LANGUAGE_BEARING_ATOMS
assert len(ALL_ACCEPTED_ATOMS) == 46
assert len(set(ALL_ACCEPTED_ATOMS)) == 46

# Known "universal decoy" placeholder range: B4's ATOM_POOL_DECOY (ordinals
# 80-99). These appear in filler/nuisance lines regardless of a row's own
# split and are never a row's actual target -- verified directly against
# tools/trigger2_b4_capacity_interference_generator_v1.py before this constant
# was hardcoded here (not assumed).
KNOWN_DECOY_ORDINAL_RANGE = range(80, 100)


def _stable_rank(name: str) -> int:
    return int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:8], "big")


def _split_stratum(stratum: tuple[str, ...], holdout_fraction: float) -> tuple[list[str], list[str]]:
    ranked = sorted(stratum, key=_stable_rank)
    n_holdout = round(len(stratum) * holdout_fraction)
    holdout = sorted(ranked[:n_holdout])
    train_val = sorted(ranked[n_holdout:])
    return train_val, holdout


def build_manifest() -> dict:
    neutral_tv, neutral_hold = _split_stratum(NEUTRAL_ATOMS, 0.2)
    lang_tv, lang_hold = _split_stratum(LANGUAGE_BEARING_ATOMS, 0.2)
    train_val = sorted(neutral_tv + lang_tv)
    holdout = sorted(neutral_hold + lang_hold)
    assert set(train_val) & set(holdout) == set()
    assert set(train_val) | set(holdout) == set(ALL_ACCEPTED_ATOMS)
    return {
        "schema": SCHEMA,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "source_provenance": SOURCE_DELTA,
        "accepted_atom_count": 46,
        "rejected_atom": REJECTED_ATOM,
        "strata": {
            "neutral_alphanumeric": {"atoms": list(NEUTRAL_ATOMS), "count": len(NEUTRAL_ATOMS)},
            "language_bearing": {"atoms": list(LANGUAGE_BEARING_ATOMS), "count": len(LANGUAGE_BEARING_ATOMS)},
        },
        "split": {
            "TRAIN_AND_VALIDATION": train_val,
            "HOLDOUT_FROZEN": holdout,
        },
        "split_counts": {"TRAIN_AND_VALIDATION": len(train_val), "HOLDOUT_FROZEN": len(holdout)},
        "known_decoy_ordinal_range": [KNOWN_DECOY_ORDINAL_RANGE.start, KNOWN_DECOY_ORDINAL_RANGE.stop - 1],
        "training_eligible": False,
        "reason_training_eligible_false": "atom NAMES only; exact atoms_index.json (atom->token-ID table) and exact target tokenizer/renderer identity remain unresolved per the cited source delta -- real rendering is a separate, later, still-blocked gate (TRIGGER2_ABI_CONTEXTUAL_RENDER_GATE/v1).",
    }


def remap_ordinal(family: str, ordinal: int, split_role: str, manifest: dict) -> str:
    """Deterministically maps one family's placeholder ordinal (given its
    empirically-verified split role) onto one canonical real atom name.
    split_role must be 'TRAIN_AND_VALIDATION' or 'HOLDOUT_FROZEN'."""
    if ordinal in KNOWN_DECOY_ORDINAL_RANGE:
        pool = manifest["split"]["TRAIN_AND_VALIDATION"]
        identifier = f"DECOY:{family}:{ordinal}"
    else:
        if split_role not in ("TRAIN_AND_VALIDATION", "HOLDOUT_FROZEN"):
            raise ValueError(f"invalid split_role {split_role!r}")
        pool = manifest["split"][split_role]
        identifier = f"{family}:{ordinal}"
    idx = _stable_rank(identifier) % len(pool)
    return pool[idx]


# ---------------------------------------------------------------------------
# empirical cross-corpus verification
# ---------------------------------------------------------------------------

def scan_committed_ordinal_splits(repo_root: Path) -> dict[int, set[str]]:
    training_dir = repo_root / "research_entity" / "claycode" / "training"
    ordinal_splits: dict[int, set[str]] = {}
    for path in sorted(training_dir.glob("*.jsonl")):
        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                split = row.get("split")
                if not split:
                    continue
                blob = json.dumps(row)
                for m in re.finditer(r"ABI_ACCEPTED_ORDINAL:(\d+)", blob):
                    ordinal_splits.setdefault(int(m.group(1)), set()).add(split)
    return ordinal_splits


def verify_no_split_crossing(repo_root: Path) -> dict:
    ordinal_splits = scan_committed_ordinal_splits(repo_root)
    crossings = []
    for ordinal, splits in ordinal_splits.items():
        if ordinal in KNOWN_DECOY_ORDINAL_RANGE:
            continue
        if "HOLDOUT_FROZEN" in splits and ({"TRAIN", "VALIDATION"} & splits):
            crossings.append({"ordinal": ordinal, "splits": sorted(splits)})
    return {
        "total_distinct_ordinals": len(ordinal_splits),
        "decoy_ordinals_excluded": sum(1 for o in ordinal_splits if o in KNOWN_DECOY_ORDINAL_RANGE),
        "crossings": crossings,
        "pass": not crossings,
    }


def verify_remap_preserves_split_integrity(repo_root: Path, manifest: dict) -> dict:
    """For every placeholder ordinal actually used in the committed corpus,
    determine its real split role (HOLDOUT_FROZEN if it ever appears in a
    HOLDOUT_FROZEN row and is not a known decoy, else TRAIN_AND_VALIDATION),
    remap it under every family name that plausibly touches that ordinal range,
    and verify TRAIN_AND_VALIDATION-role placeholders never land on a
    HOLDOUT_FROZEN-role real atom and vice versa."""
    ordinal_splits = scan_committed_ordinal_splits(repo_root)
    failures = []
    checked = 0
    for ordinal, splits in ordinal_splits.items():
        if ordinal in KNOWN_DECOY_ORDINAL_RANGE:
            role = None  # decoys always map into TRAIN_AND_VALIDATION regardless
        elif "HOLDOUT_FROZEN" in splits:
            role = "HOLDOUT_FROZEN"
        else:
            role = "TRAIN_AND_VALIDATION"
        for family in ("B0", "B1", "B2", "B3", "B4", "B5"):
            checked += 1
            if role is None:
                atom = remap_ordinal(family, ordinal, "TRAIN_AND_VALIDATION", manifest)
                if atom not in manifest["split"]["TRAIN_AND_VALIDATION"]:
                    failures.append({"family": family, "ordinal": ordinal, "reason": "decoy mapped outside TRAIN_AND_VALIDATION pool"})
                continue
            atom = remap_ordinal(family, ordinal, role, manifest)
            if atom not in manifest["split"][role]:
                failures.append({"family": family, "ordinal": ordinal, "role": role, "mapped_atom": atom, "reason": "landed outside its own split pool"})
    return {"checked": checked, "failures": failures, "pass": not failures}


def run(repo_root: Path) -> dict:
    manifest = build_manifest()
    crossing_check = verify_no_split_crossing(repo_root)
    remap_check = verify_remap_preserves_split_integrity(repo_root, manifest)
    overall_pass = crossing_check["pass"] and remap_check["pass"]
    return {
        "manifest": manifest,
        "empirical_crossing_check": crossing_check,
        "remap_integrity_check": remap_check,
        "overall_pass": overall_pass,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--manifest-out", type=Path)
    ap.add_argument("--report-out", type=Path)
    args = ap.parse_args()

    report = run(args.repo_root)
    if args.manifest_out:
        args.manifest_out.write_text(json.dumps(report["manifest"], indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.report_out:
        args.report_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
