#!/usr/bin/env python3
"""Trigger-2 B6 candidate generator: SYSTEM_INTEGRATION baseline.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md
(sections B, H, I) and research_entity/global/j-space/research/
2026-08-26_TRIGGER2_QWEN35_08B_BINDING_REMAP_CURRICULUM_V1_GPT56SOL.json, stage
"B6_SYSTEM_INTEGRATION":

  "Reuse the binder inside actual owner-target cognitive transitions."
  families: DB versus simulation boundary decisions; Claude Code handoff/return/
  re-entry packet binding; Hyperposition alternative identity and evidence
  reconciliation; restart/rejoin with durable database state; fail-closed
  authority/evidence provenance.

This tool covers three of those families end to end:

  DB_VS_SIM:              S0 (canonical DB) vs S1/S2 (simulation/hypothesis) vs
                           stale-needs-rebase discrimination (course section B).
  CLAUDE_HANDOFF_REENTRY:  epistemic-class separation of a Claude Code assertion,
                           an external tool receipt, already-committed canonical
                           ledger evidence, and a stale/generation-mismatched
                           ZECP13/ZECP14 handoff (course section I).
  HYPERPOSITION_EVIDENCE_AUTHORITY: whether a pair of open Hyperposition branches
                           must be preserved or may be validly collapsed --
                           collapse is legal ONLY when driven by an explicit
                           discriminator-test result, never by majority vote,
                           coordinator preference, repeated agreement or surface
                           fluency (course section H hard negatives).

Design, reused from the B0/B1 ancestry (tools/trigger2_b0_read_write_baseline_generator_v1.py,
tools/trigger2_dynamic_binding_blueprint_v2.py):

  - family-disjoint holdouts: entity-name pools are disjoint per split (TRAIN/
    VALIDATION/HOLDOUT_FROZEN never share an entity name), analogous to the
    disjoint symbol-triple partition in B0/B1;
  - lexical counterbalance: every class has an explicit "hard negative" wrapper
    that names the OTHER classes' surface phrases and denies them, so the model
    cannot win by spotting one keyword;
  - template/scaffold partition: prompt-wrapping style is also split-disjoint
    (TRAIN scaffolds never appear in VALIDATION/HOLDOUT_FROZEN rows);
  - nuisance fields (which specific entity name; item order/layout) are audited
    to carry exactly zero mutual information about the target, both marginally
    and via exact per-cell enumeration -- the same two-level check that caught
    a real higher-order leak in the B1 blueprint's own pairwise-only selftest
    (tools/trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1.py).

Status: METHOD_ONLY / candidate-and-quarantined per TRIGGERWORT_2 course Step 6.
Rows are NOT training-eligible: no admission gate has run and this generator has
not been through the exact-tokenizer/renderer identity binding gate.
accepted_dataset_tokens remains 0 regardless of this tool's output.
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

SCHEMA = "CLAY_TRIGGER2_B6_SYSTEM_INTEGRATION_CANDIDATE/v1"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
ANCESTRY = "trigger2-20260826-b6-system-integration-v1"
SOURCE_MODULE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest() if Path(__file__).exists() else ""

LAYOUTS = ("CONTEXT_THEN_QUESTION", "QUESTION_THEN_CONTEXT")
POLARITIES = ("POS", "NEG")


def _stable_hash_int(*parts: object) -> int:
    """Cross-family consolidation fix (2026-08-26, claude-code-lead): this module
    previously used Python's built-in hash() on tuples of strings (three call
    sites) to deterministically-looking-but-actually-randomly pick cosmetic
    presentation details (a status word, a filler ID number, which of two branch
    labels is called the "winner" in narrative text). Since Python 3.3, str/tuple
    hash() is salted per-process by PYTHONHASHSEED (randomized by default) --
    those three call sites were therefore NOT reproducible across reruns of this
    generator, even though the counts/targets/audit-pass status were unaffected
    (verified: each site only varies cosmetic filler text, never the row's
    `target` field, which is always set directly from `cls`/`pressure_type`
    elsewhere). Replaced with a hashlib-based stable hash, matching the pattern
    tools/trigger2_dynamic_binding_blueprint_v2.py already uses
    (stable_shuffle's hashlib.sha256(...).digest()[:8] as an int seed) so the same
    inputs now produce the same bytes on every machine/process, not just within
    one process run."""
    key = "|".join(str(p) for p in parts)
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")

# ---------------------------------------------------------------------------
# split-disjoint entity pools (shared shape across all three families; every
# name is globally unique so cross-family reuse cannot create a cross-split
# leak even though the pools are drawn from one shared namespace)
# ---------------------------------------------------------------------------
SPLIT_ENTITIES = {
    "TRAIN": ["node_ash7", "node_birch3", "node_cedar9", "node_dune1", "node_elm5", "node_fen2"],
    "VALIDATION": ["node_grove4", "node_holt6", "node_ivy8"],
    "HOLDOUT_FROZEN": ["node_juno0", "node_kite2", "node_lynx4"],
}
_all_entities = [e for v in SPLIT_ENTITIES.values() for e in v]
assert len(_all_entities) == len(set(_all_entities)), "entity pool must be globally unique"

# scaffold (prompt-wrapping style) partition -- disjoint per split, same shape
# reused across families via a family-specific instruction suffix.
SCAFFOLDS = {
    "TRAIN": ["S1_LABELED", "S2_NARRATIVE", "S3_BULLET", "S4_LOGLINE"],
    "VALIDATION": ["S5_TRANSCRIPT"],
    "HOLDOUT_FROZEN": ["S6_INCIDENT_REPORT"],
}


def render_scaffold(scaffold_id: str, context: str, question: str, layout: str) -> str:
    parts = (context, question) if layout == "CONTEXT_THEN_QUESTION" else (question, context)
    if scaffold_id == "S1_LABELED":
        a, b = ("CONTEXT", "QUESTION") if layout == "CONTEXT_THEN_QUESTION" else ("QUESTION", "CONTEXT")
        return f"{a}: {parts[0]}\n{b}: {parts[1]}"
    if scaffold_id == "S2_NARRATIVE":
        return f"Situation: {parts[0]}\nGiven that, {parts[1]}"
    if scaffold_id == "S3_BULLET":
        return f"- {parts[0]}\n- {parts[1]}"
    if scaffold_id == "S4_LOGLINE":
        return f"[log] {parts[0]} [query] {parts[1]}"
    if scaffold_id == "S5_TRANSCRIPT":
        return f">> observed: {parts[0]}\n>> asked: {parts[1]}"
    if scaffold_id == "S6_INCIDENT_REPORT":
        return f"Report body: {parts[0]}\nReport question: {parts[1]}"
    raise ValueError(scaffold_id)


def row_common(task: str, split: str, curriculum_family: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": ANCESTRY,
        "curriculum_phase": "B6_SYSTEM_INTEGRATION",
        "curriculum_family": curriculum_family,
        # Cross-family consolidation fix (2026-08-26, claude-code-lead, see
        # research_entity/00_CURRENT/updates/trigger2-training/ consolidation
        # receipt): B2/B3 use the key "family" for the identical concept
        # (sub-family within a curriculum phase). B6 originally only emitted
        # "curriculum_family", so any downstream code grouping candidate rows
        # by sub-family across all six B0-B6 families would silently get None
        # for every B6 row. Added as an ADDITIVE alias -- "curriculum_family"
        # is kept unchanged so this generator's own existing tests/consumers
        # are unaffected; "family" is new and matches B2/B3's convention.
        "family": curriculum_family,
        "task": task,
        "split": split,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "source_module_sha256": SOURCE_MODULE_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
    }


# ===========================================================================
# Family 1: DB_VS_SIM (course section B: S0/S1/S2 discrimination + restart/
# rejoin with durable database state)
# ===========================================================================
DB_VS_SIM_CLASSES = ("CANONICAL_DB", "SIMULATED_HYPOTHESIS", "STALE_REBASE_REQUIRED")
DB_VS_SIM_ALT_PHRASE = {
    "CANONICAL_DB": "an unconfirmed simulated guess",
    "SIMULATED_HYPOTHESIS": "a confirmed same-epoch canonical ledger read",
    "STALE_REBASE_REQUIRED": "a fresh same-epoch canonical read",
}
DB_VS_SIM_QUESTION = "What authority does this claim about the entity's state have: CANONICAL_DB, SIMULATED_HYPOTHESIS, or STALE_REBASE_REQUIRED?"


def db_vs_sim_clause(cls: str, entity: str, val: str, e1: int, e2: int) -> str:
    if cls == "CANONICAL_DB":
        return (
            f"A direct SELECT against the canonical S0 ledger table for {entity} returned "
            f"{entity}.status={val}; the row was read at the current epoch and no simulation, "
            f"generation or hypothesis step was involved."
        )
    if cls == "SIMULATED_HYPOTHESIS":
        return (
            f"No database query was issued for {entity}; a model was asked to imagine what "
            f"{entity}.status might plausibly be and produced the unconfirmed guess "
            f"{entity}.status={val}, later described in prose as though it were settled."
        )
    if cls == "STALE_REBASE_REQUIRED":
        return (
            f"{entity}.status={val} was read from the ledger at epoch {e1}; the canonical epoch "
            f"has since advanced to {e2} (with {e2} greater than {e1}) and no rebase or re-read "
            f"has happened since that earlier read."
        )
    raise ValueError(cls)


def db_vs_sim_wrap(cls: str, clause: str, polarity: str) -> str:
    if polarity == "POS":
        return f"Claim under review: {clause}"
    others = [DB_VS_SIM_ALT_PHRASE[c] for c in DB_VS_SIM_CLASSES if c != cls]
    denial = " and not ".join(others)
    return f"Claim under review: {clause} This is not {denial}."


def build_db_vs_sim_rows() -> list[dict]:
    rows = []
    for split, scaffolds in SCAFFOLDS.items():
        entities = SPLIT_ENTITIES[split]
        for scaffold_id in scaffolds:
            for cls in DB_VS_SIM_CLASSES:
                for polarity in POLARITIES:
                    for layout in LAYOUTS:
                        for entity in entities:
                            val = "READY" if _stable_hash_int(entity, cls, polarity) % 2 == 0 else "BLOCKED"
                            e1, e2 = 41, 44
                            clause = db_vs_sim_clause(cls, entity, val, e1, e2)
                            context = db_vs_sim_wrap(cls, clause, polarity)
                            prompt = (
                                render_scaffold(scaffold_id, context, DB_VS_SIM_QUESTION, layout)
                                + "\nRespond with exactly one label: CANONICAL_DB, SIMULATED_HYPOTHESIS, or STALE_REBASE_REQUIRED."
                            )
                            r = row_common("DB_VS_SIM", split, "DB_VS_SIM")
                            r.update({
                                "id": f"B6_DBVSSIM_{scaffold_id}_{cls}_{polarity}_{layout}_{entity}",
                                "scaffold": scaffold_id,
                                "class": cls,
                                "polarity": polarity,
                                "layout": layout,
                                "entity": entity,
                                "prompt": prompt,
                                "target": cls,
                            })
                            rows.append(r)
    return rows


# ===========================================================================
# Family 2: CLAUDE_HANDOFF_REENTRY (course section I: ZECP13 handoff / ZECP14
# result reconciliation; Claude assertions, external tool receipts and
# canonical evidence stay distinct epistemic classes)
# ===========================================================================
CLAUDE_HANDOFF_CLASSES = (
    "CLAUDE_ASSERTION",
    "EXTERNAL_TOOL_RECEIPT",
    "CANONICAL_LEDGER_EVIDENCE",
    "STALE_MISMATCHED_HANDOFF",
)
CLAUDE_HANDOFF_ALT_PHRASE = {
    "CLAUDE_ASSERTION": "an external tool receipt",
    "EXTERNAL_TOOL_RECEIPT": "an unverified natural-language claim from Claude Code",
    "CANONICAL_LEDGER_EVIDENCE": "a still-unconfirmed assertion",
    "STALE_MISMATCHED_HANDOFF": "a cleanly matched same-generation handoff",
}
CLAUDE_HANDOFF_QUESTION = (
    "What epistemic class does this statement belong to: CLAUDE_ASSERTION, "
    "EXTERNAL_TOOL_RECEIPT, CANONICAL_LEDGER_EVIDENCE, or STALE_MISMATCHED_HANDOFF?"
)


def claude_handoff_clause(cls: str, entity: str, g1: int, g2: int, detail: str) -> str:
    if cls == "CLAUDE_ASSERTION":
        return (
            f"Claude Code stated in natural language that the {entity} migration succeeded and "
            f"that all checks passed; it phrased this confidently, but no external tool receipt "
            f"and no ledger row is attached to the statement."
        )
    if cls == "EXTERNAL_TOOL_RECEIPT":
        return (
            f"A tool invocation against {entity} produced the receipt `test:0:{detail}`, an exit "
            f"code and a description attached directly to the run, independent of any prose "
            f"summary of it."
        )
    if cls == "CANONICAL_LEDGER_EVIDENCE":
        return (
            f"Ledger row `effect:{detail}` for {entity} is already committed and hash-verified in "
            f"the canonical S0 store, independent of whatever was said about it afterward."
        )
    if cls == "STALE_MISMATCHED_HANDOFF":
        return (
            f"The ZECP14 result for {entity} references handoff generation {g1}, but the current "
            f"ZECP13 lease generation is {g2} (with {g1} not equal to {g2}); the handoff and the "
            f"result do not bind to the same generation."
        )
    raise ValueError(cls)


def claude_handoff_wrap(cls: str, clause: str, polarity: str) -> str:
    if polarity == "POS":
        return f"Statement under review: {clause}"
    others = [CLAUDE_HANDOFF_ALT_PHRASE[c] for c in CLAUDE_HANDOFF_CLASSES if c != cls]
    denial = " and not ".join(others)
    return f"Statement under review: {clause} This is not {denial}."


def build_claude_handoff_rows() -> list[dict]:
    rows = []
    for split, scaffolds in SCAFFOLDS.items():
        entities = SPLIT_ENTITIES[split]
        for scaffold_id in scaffolds:
            for cls in CLAUDE_HANDOFF_CLASSES:
                for polarity in POLARITIES:
                    for layout in LAYOUTS:
                        for entity in entities:
                            g1, g2 = 12, 13
                            detail = f"{_stable_hash_int(entity, cls) % 9000 + 1000}"
                            clause = claude_handoff_clause(cls, entity, g1, g2, detail)
                            context = claude_handoff_wrap(cls, clause, polarity)
                            prompt = (
                                render_scaffold(scaffold_id, context, CLAUDE_HANDOFF_QUESTION, layout)
                                + "\nRespond with exactly one label: CLAUDE_ASSERTION, EXTERNAL_TOOL_RECEIPT, "
                                "CANONICAL_LEDGER_EVIDENCE, or STALE_MISMATCHED_HANDOFF."
                            )
                            r = row_common("CLAUDE_HANDOFF_REENTRY", split, "CLAUDE_HANDOFF_REENTRY")
                            r.update({
                                "id": f"B6_HANDOFF_{scaffold_id}_{cls}_{polarity}_{layout}_{entity}",
                                "scaffold": scaffold_id,
                                "class": cls,
                                "polarity": polarity,
                                "layout": layout,
                                "entity": entity,
                                "prompt": prompt,
                                "target": cls,
                            })
                            rows.append(r)
    return rows


# ===========================================================================
# Family 3: HYPERPOSITION_EVIDENCE_AUTHORITY (course section H: collapse must
# not occur because of majority / repeated agreement / coordinator preference
# / surface fluency -- only an explicit discriminator-test result legitimizes
# collapse)
# ===========================================================================
PRESSURE_TYPES = (
    "MAJORITY_VOTE",
    "COORDINATOR_PREFERENCE",
    "REPEATED_AGREEMENT",
    "SURFACE_FLUENCY",
    "EXPLICIT_DISCRIMINATOR_TEST",
)
HYPERPOSITION_TARGET = {
    "MAJORITY_VOTE": "PRESERVE_BRANCHES",
    "COORDINATOR_PREFERENCE": "PRESERVE_BRANCHES",
    "REPEATED_AGREEMENT": "PRESERVE_BRANCHES",
    "SURFACE_FLUENCY": "PRESERVE_BRANCHES",
    "EXPLICIT_DISCRIMINATOR_TEST": "COLLAPSE_VALID",
}
HYPERPOSITION_QUESTION = (
    "Should the two open branches be preserved or may they be validly collapsed: "
    "PRESERVE_BRANCHES or COLLAPSE_VALID?"
)


def hyperposition_clause(pressure_type: str, entity: str, branch_a: str, branch_b: str, winner: str, loser: str) -> str:
    base = (
        f"Two Hyperposition branches for {entity} remain open: branch {branch_a} and branch "
        f"{branch_b}, each still holding supporting evidence with neither branch falsified."
    )
    if pressure_type == "MAJORITY_VOTE":
        pressure = f"A majority of {entity}'s peer nodes voted for branch {winner} in an ordinary S1 poll."
    elif pressure_type == "COORDINATOR_PREFERENCE":
        pressure = f"The currently leased coordinator for {entity} simply prefers branch {winner}."
    elif pressure_type == "REPEATED_AGREEMENT":
        pressure = f"Branch {winner} has been proposed again by several independent passes, but none of them added new evidence."
    elif pressure_type == "SURFACE_FLUENCY":
        pressure = f"Branch {winner}'s write-up reads more fluently and confidently than branch {loser}'s, though the underlying evidence is unchanged."
    elif pressure_type == "EXPLICIT_DISCRIMINATOR_TEST":
        pressure = f"A new discriminator test was run against {entity} and its result formally excludes branch {loser}, leaving branch {winner} as the only branch consistent with the test outcome."
    else:
        raise ValueError(pressure_type)
    return f"{base} {pressure}"


def hyperposition_wrap(clause: str, polarity: str) -> str:
    if polarity == "POS":
        return clause
    return f"{clause} No branch has been formally falsified by this alone."


def build_hyperposition_rows() -> list[dict]:
    rows = []
    for split, scaffolds in SCAFFOLDS.items():
        entities = SPLIT_ENTITIES[split]
        for scaffold_id in scaffolds:
            for pressure_type in PRESSURE_TYPES:
                for polarity in POLARITIES:
                    for layout in LAYOUTS:
                        for entity in entities:
                            branch_a, branch_b = "A", "B"
                            winner, loser = (branch_a, branch_b) if _stable_hash_int(entity, pressure_type, polarity) % 2 == 0 else (branch_b, branch_a)
                            clause = hyperposition_clause(pressure_type, entity, branch_a, branch_b, winner, loser)
                            context = hyperposition_wrap(clause, polarity)
                            target = HYPERPOSITION_TARGET[pressure_type]
                            prompt = (
                                render_scaffold(scaffold_id, context, HYPERPOSITION_QUESTION, layout)
                                + "\nRespond with exactly one label: PRESERVE_BRANCHES or COLLAPSE_VALID."
                            )
                            r = row_common("HYPERPOSITION_EVIDENCE_AUTHORITY", split, "HYPERPOSITION_EVIDENCE_AUTHORITY")
                            r.update({
                                "id": f"B6_HYPERPOS_{scaffold_id}_{pressure_type}_{polarity}_{layout}_{entity}",
                                "scaffold": scaffold_id,
                                "pressure_type": pressure_type,
                                "polarity": polarity,
                                "layout": layout,
                                "entity": entity,
                                "winner_branch": winner,
                                "prompt": prompt,
                                "target": target,
                            })
                            rows.append(r)
    return rows


# ===========================================================================
# audit
# ===========================================================================
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


def _entity_pool_disjoint() -> list[str]:
    failures = []
    train, val, hold = set(SPLIT_ENTITIES["TRAIN"]), set(SPLIT_ENTITIES["VALIDATION"]), set(SPLIT_ENTITIES["HOLDOUT_FROZEN"])
    if train & val:
        failures.append(f"ENTITY_POOL_OVERLAP_TRAIN_VALIDATION:{sorted(train & val)}")
    if train & hold:
        failures.append(f"ENTITY_POOL_OVERLAP_TRAIN_HOLDOUT:{sorted(train & hold)}")
    if val & hold:
        failures.append(f"ENTITY_POOL_OVERLAP_VALIDATION_HOLDOUT:{sorted(val & hold)}")
    return failures


def audit_family(rows: list[dict], class_field: str, expected_classes: tuple[str, ...], allow_imbalance: bool = False) -> dict:
    failures = list(_entity_pool_disjoint())

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    # scaffold (template) partition must stay split-exclusive
    for split, scaffolds in SCAFFOLDS.items():
        used = {r["scaffold"] for r in rows if r["split"] == split}
        if not used <= set(scaffolds):
            failures.append(f"SCAFFOLD_LEAK_INTO_SPLIT:{split}:{used - set(scaffolds)}")

    # entity must never appear in a row belonging to a different split's pool
    for split, entities in SPLIT_ENTITIES.items():
        bad = {r["entity"] for r in rows if r["split"] == split} - set(entities)
        if bad:
            failures.append(f"ENTITY_LEAK_INTO_SPLIT:{split}:{bad}")

    for split in SPLIT_ENTITIES:
        subset = [r for r in rows if r["split"] == split]
        by_class = Counter(r[class_field] for r in subset)
        if not allow_imbalance and len(set(by_class.values())) != 1:
            failures.append(f"CLASS_IMBALANCE:{split}:{dict(by_class)}")
        missing = set(expected_classes) - set(by_class)
        if missing:
            failures.append(f"MISSING_CLASSES:{split}:{missing}")

    # nuisance fields (entity identity, layout) must carry zero information
    # about target, both marginally and per-(scaffold,class-field) exact cell
    entity_mi = mi(rows, lambda r: r["target"], lambda r: r["entity"])
    if abs(entity_mi) > 1e-9:
        failures.append(f"ENTITY_LEAKS_TARGET_MARGINAL:{entity_mi}")
    layout_mi = mi(rows, lambda r: r["target"], lambda r: r["layout"])
    if abs(layout_mi) > 1e-9:
        failures.append(f"LAYOUT_LEAKS_TARGET_MARGINAL:{layout_mi}")

    cells = defaultdict(set)
    for r in rows:
        key = (r["scaffold"], r[class_field])
        cells[key].add(r["target"])
    non_constant = [k for k, v in cells.items() if len(v) != 1]
    if non_constant:
        failures.append(f"ENTITY_OR_LAYOUT_CHANGES_TARGET_FOR_FIXED_CLASS:{len(non_constant)}")

    return {
        "rows": len(rows),
        "split_counts": dict(Counter(r["split"] for r in rows)),
        "entity_target_mi_bits": entity_mi,
        "layout_target_mi_bits": layout_mi,
        "failures": failures,
        "pass": not failures,
    }


def audit_db_vs_sim(rows: list[dict]) -> dict:
    return audit_family(rows, "class", DB_VS_SIM_CLASSES)


def audit_claude_handoff(rows: list[dict]) -> dict:
    return audit_family(rows, "class", CLAUDE_HANDOFF_CLASSES)


def audit_hyperposition(rows: list[dict]) -> dict:
    # pressure_type -> target is an intentional 4:1 (PRESERVE:COLLAPSE) mapping,
    # not a balanced classification -- allow_imbalance documents that by design.
    return audit_family(rows, "pressure_type", PRESSURE_TYPES, allow_imbalance=True)


def run() -> dict:
    db_rows = build_db_vs_sim_rows()
    handoff_rows = build_claude_handoff_rows()
    hyper_rows = build_hyperposition_rows()

    db_report = audit_db_vs_sim(db_rows)
    handoff_report = audit_claude_handoff(handoff_rows)
    hyper_report = audit_hyperposition(hyper_rows)

    all_prompts = [r["prompt"] for r in db_rows + handoff_rows + hyper_rows]
    cross_family_dupes = {p: c for p, c in Counter(all_prompts).items() if c > 1}

    overall_pass = db_report["pass"] and handoff_report["pass"] and hyper_report["pass"] and not cross_family_dupes

    return {
        "schema": SCHEMA,
        "db_vs_sim": db_report,
        "claude_handoff_reentry": handoff_report,
        "hyperposition_evidence_authority": hyper_report,
        "cross_family_duplicate_prompts": len(cross_family_dupes),
        "total_rows": len(db_rows) + len(handoff_rows) + len(hyper_rows),
        "overall_pass": overall_pass,
        "training_eligible": False,
        "reason_training_eligible_false": (
            "no real tokenizer/atom-manifest binding, no admission gate run -- "
            "candidate/quarantined only per TRIGGERWORT_2 course Step 6."
        ),
    }


def _write_jsonl(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-db-vs-sim", type=Path)
    ap.add_argument("--out-claude-handoff", type=Path)
    ap.add_argument("--out-hyperposition", type=Path)
    ap.add_argument("--audit-out")
    args = ap.parse_args()

    db_rows = build_db_vs_sim_rows()
    handoff_rows = build_claude_handoff_rows()
    hyper_rows = build_hyperposition_rows()
    report = run()

    if args.out_db_vs_sim:
        report["db_vs_sim"]["output_sha256"] = _write_jsonl(args.out_db_vs_sim, db_rows)
    if args.out_claude_handoff:
        report["claude_handoff_reentry"]["output_sha256"] = _write_jsonl(args.out_claude_handoff, handoff_rows)
    if args.out_hyperposition:
        report["hyperposition_evidence_authority"]["output_sha256"] = _write_jsonl(args.out_hyperposition, hyper_rows)

    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.audit_out:
        Path(args.audit_out).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
