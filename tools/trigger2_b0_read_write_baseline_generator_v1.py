#!/usr/bin/env python3
"""Trigger-2 B0 candidate generator: separate semantic READ / symbol WRITE baselines.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
section "Training -- Qwen3.5-0.8B binding/remap discriminator":

  B0: separate semantic READ and symbol WRITE baselines;
  B1: arbitrary episode-local binding with full S3/counterbalanced nuisance crossing;
  ...

The measured handoff (course doc section 4) says semantic readout and symbol-axis
writeability are ALREADY comparatively strong; the missing capability is dynamic
binding/context invariance (B1+). B0 exists to calibrate the two "already strong"
primitives SEPARATELY and cleanly, in isolation from each other, before B1 asks the
model to compose them:

  READ:  evidence/query text  -> semantic class word (ALLOW/DENY/ABSTAIN). No
         codebook, no symbol, no routing -- pure natural-language state reading.
  WRITE: codebook + a DIRECTLY STATED class (no evidence to read, no reasoning
         about state) -> the symbol that class is bound to. Pure codebook lookup,
         isolated from any semantic derivation step.

Reuses the same template pool, triple partition and codebook-rendering approach as
tools/trigger2_dynamic_binding_blueprint_v2.py (the current strongest binding-generator
donor) and tools/trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1.py (the
rendered-byte leakage-audit companion for that generator), so B0 stays inside the same
symbol/template/split ancestry as B1 rather than introducing a parallel one.

Status: METHOD_ONLY / candidate-and-quarantined per TRIGGERWORT_2 course Step 6.
Rows are NOT training-eligible: they use PLACEHOLDER ABI_ACCEPTED_ORDINAL atoms (real
tokenizer/atom-manifest binding is a separate, later gate -- see the same course
document and the Q35 identity-metrology chain), and no admission gate has run.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trigger2_dynamic_binding_blueprint_v2 as bp  # noqa: E402

SCHEMA = "CLAY_TRIGGER2_B0_READ_WRITE_BASELINE_CANDIDATE/v1"
SOURCE_MODULE_SHA256 = hashlib.sha256(Path(bp.__file__).read_bytes()).hexdigest()
ANCESTRY = "trigger2-20260826-b0-read-write-baseline-v1"

READ_LAYOUTS = ("EVIDENCE_THEN_QUERY", "QUERY_THEN_EVIDENCE")
READ_TEMPLATES = [
    (t, "TRAIN") for t in bp.TRAIN_TEMPLATES
] + [
    (bp.VALIDATION_TEMPLATE, "VALIDATION"),
    (bp.HOLDOUT_TEMPLATE, "HOLDOUT_FROZEN"),
]

WRITE_TRIPLE_SPLITS = [
    (bp.TRAIN_TRIPLETS, "TRAIN"),
    ((bp.HOLDOUT_TRIPLET,), "HOLDOUT_FROZEN"),
]


def row_common(task: str, split: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": ANCESTRY,
        "curriculum_phase": "B0_READ_WRITE_BASELINE",
        "task": task,
        "split": split,
        "abi_manifest_sha256": bp.ABI_MANIFEST_SHA256,
        "source_module_sha256": SOURCE_MODULE_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
    }


def build_read_rows() -> list[dict]:
    rows = []
    for t, split in READ_TEMPLATES:
        for c in bp.CLASSES:
            for p in bp.POLARITIES:
                e, q = bp.semantic_text(t, c, p)
                for lay in READ_LAYOUTS:
                    body = f"EVIDENCE: {e}\nQUERY: {q}" if lay == "EVIDENCE_THEN_QUERY" else f"QUERY: {q}\nEVIDENCE: {e}"
                    r = row_common("READ", split)
                    r.update({
                        "id": f"B0_READ_{t}_{c}_{p}_{lay}",
                        "template": t,
                        "class": c,
                        "polarity": p,
                        "layout": lay,
                        "prompt": f"{body}\nRespond with exactly one word: ALLOW, DENY, or ABSTAIN.",
                        "target": c,
                    })
                    rows.append(r)
    return rows


def render_write_codebook(triple: tuple[int, int, int], perm: tuple[int, int, int], order: tuple[int, int, int]) -> tuple[str, dict]:
    sym = [bp.atom_ref(n) for n in triple]
    entries = []
    binding = {}
    for oi in order:
        cls = bp.CLASSES[oi]
        ci = bp.CLASSES.index(cls)
        bound = sym[perm[ci]]
        entries.append(f"{cls}=>{bound}")
        binding[cls] = bound
    return " | ".join(entries), binding


def build_write_rows() -> list[dict]:
    rows = []
    for triplets, split in WRITE_TRIPLE_SPLITS:
        for triple in triplets:
            for mi_, perm in enumerate(bp.PERMS):
                for oi_, order in enumerate(bp.PERMS):
                    codebook, binding = render_write_codebook(triple, perm, order)
                    for c in bp.CLASSES:
                        r = row_common("WRITE", split)
                        r.update({
                            "id": f"B0_WRITE_T{triple[0]:02d}_M{mi_}_O{oi_}_{c}",
                            "triple": list(triple),
                            "perm": list(perm),
                            "codebook_order": list(order),
                            "class_given_directly": c,
                            "prompt": (
                                f"CODEBOOK: {codebook}\n"
                                f"STATE: the current class is {c}, given directly (not derived from evidence).\n"
                                "Return exactly one bound symbol."
                            ),
                            "target": binding[c],
                        })
                        rows.append(r)
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


def audit_read(rows: list[dict]) -> dict:
    failures = []
    counts = Counter(r["split"] for r in rows)
    expected = {"TRAIN": 48, "VALIDATION": 12, "HOLDOUT_FROZEN": 12}
    if dict(counts) != expected:
        failures.append(f"SPLIT_COUNTS:{dict(counts)}!=EXPECTED:{expected}")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    for split in expected:
        subset = [r for r in rows if r["split"] == split]
        by_class = Counter(r["class"] for r in subset)
        if len(set(by_class.values())) != 1:
            failures.append(f"CLASS_IMBALANCE:{split}:{dict(by_class)}")

    for r in rows:
        if r["target"] != r["class"]:
            failures.append(f"TARGET_NOT_CLASS:{r['id']}")
        if any(sym in r["prompt"] for sym in ("ABI_ACCEPTED_ORDINAL",)):
            failures.append(f"READ_PROMPT_LEAKS_SYMBOL_ATOM:{r['id']}")

    return {
        "rows": len(rows),
        "split_counts": dict(counts),
        "failures": failures,
        "pass": not failures,
    }


def audit_write(rows: list[dict]) -> dict:
    failures = []
    counts = Counter(r["split"] for r in rows)
    expected = {"TRAIN": 4 * 6 * 6 * 3, "HOLDOUT_FROZEN": 1 * 6 * 6 * 3}
    if dict(counts) != expected:
        failures.append(f"SPLIT_COUNTS:{dict(counts)}!=EXPECTED:{expected}")

    for r in rows:
        ci = bp.CLASSES.index(r["class_given_directly"])
        expected_target = bp.atom_ref(r["triple"][r["perm"][ci]])
        if r["target"] != expected_target:
            failures.append(f"TARGET_NOT_FROM_BINDING:{r['id']}")

    train_syms = {s for triple in bp.TRAIN_TRIPLETS for s in triple}
    hold_syms = set(bp.HOLDOUT_TRIPLET)
    if train_syms & hold_syms:
        failures.append("SYMBOL_PARTITION_OVERLAP")
    for r in rows:
        target_n = int(r["target"].rsplit(":", 1)[1])
        if r["split"] == "TRAIN" and target_n not in train_syms:
            failures.append(f"HOLDOUT_SYMBOL_IN_TRAIN:{r['id']}")
        if r["split"] == "HOLDOUT_FROZEN" and target_n not in hold_syms:
            failures.append(f"TRAIN_SYMBOL_IN_HOLDOUT:{r['id']}")

    # order is purely a DISPLAY nuisance; it must carry zero information about the
    # target once perm+class (i.e. the actual binding) are fixed. Check both the
    # marginal MI and the finer per-(triple,perm,class) conditional distribution
    # directly (exact enumeration, not just pairwise trust -- see the lesson from
    # tools/trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1.py, which found
    # a real higher-order leak in the sibling B1 blueprint despite clean pairwise MI).
    order_mi = mi(rows, lambda r: r["target"], lambda r: tuple(r["codebook_order"]))
    if abs(order_mi) > 1e-9:
        failures.append(f"ORDER_LEAKS_TARGET_MARGINAL:{order_mi}")

    cells = defaultdict(set)
    for r in rows:
        key = (tuple(r["triple"]), tuple(r["perm"]), r["class_given_directly"])
        cells[key].add(r["target"])
    non_constant = [k for k, v in cells.items() if len(v) != 1]
    if non_constant:
        failures.append(f"ORDER_CHANGES_TARGET_FOR_FIXED_BINDING:{len(non_constant)}")

    return {
        "rows": len(rows),
        "split_counts": dict(counts),
        "order_target_mi_bits": order_mi,
        "failures": failures,
        "pass": not failures,
    }


def run() -> dict:
    read_rows = build_read_rows()
    write_rows = build_write_rows()
    read_report = audit_read(read_rows)
    write_report = audit_write(write_rows)
    overall_pass = read_report["pass"] and write_report["pass"]
    return {
        "schema": SCHEMA,
        "source_blueprint_module": {"path": "tools/trigger2_dynamic_binding_blueprint_v2.py", "sha256": SOURCE_MODULE_SHA256},
        "read": read_report,
        "write": write_report,
        "overall_pass": overall_pass,
        "training_eligible": False,
        "reason_training_eligible_false": "placeholder ABI_ACCEPTED_ORDINAL atoms, no real tokenizer/atom-manifest binding, no admission gate run -- candidate/quarantined only per TRIGGERWORT_2 course Step 6.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-read", type=Path)
    ap.add_argument("--out-write", type=Path)
    ap.add_argument("--audit-out")
    args = ap.parse_args()

    read_rows = build_read_rows()
    write_rows = build_write_rows()
    report = run()

    if args.out_read:
        args.out_read.parent.mkdir(parents=True, exist_ok=True)
        with args.out_read.open("w", encoding="utf-8", newline="\n") as f:
            for r in read_rows:
                f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        report["read"]["output_sha256"] = hashlib.sha256(args.out_read.read_bytes()).hexdigest()
    if args.out_write:
        args.out_write.parent.mkdir(parents=True, exist_ok=True)
        with args.out_write.open("w", encoding="utf-8", newline="\n") as f:
            for r in write_rows:
                f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        report["write"]["output_sha256"] = hashlib.sha256(args.out_write.read_bytes()).hexdigest()

    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.audit_out:
        Path(args.audit_out).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
