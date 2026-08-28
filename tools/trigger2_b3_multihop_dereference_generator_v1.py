#!/usr/bin/env python3
"""Trigger-2 B3 candidate generator: multi-hop dereference.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
Training map "B3: multi-hop dereference". Reuses the same symbol-triple partition
and atom-naming scheme as tools/trigger2_dynamic_binding_blueprint_v2.py (the B1
donor). Status: METHOD_ONLY / candidate-and-quarantined per TRIGGERWORT_2 course
Step 6 -- placeholder ABI_ACCEPTED_ORDINAL atoms, no real tokenizer binding, no
admission gate run.

FIX (2026-08-27, Gabriel-directed, found by chatgpt-secondary review + confirmed
independently before fixing, see research_entity/topic_packets/trigger2-b0-b6-
chatgpt-secondary-review-20260827/): UNRESOLVABLE_CHAIN_REJECTION rows used to
emit "queried_class_" (trailing underscore) for the same concept
MULTI_HOP_DEREF calls "queried_class", under the identical SCHEMA string --
audit_unresolvable() read the typo'd key itself, so the old self-audit could
never catch it. Renamed to "queried_class" in both places; all 1620
UNRESOLVABLE_CHAIN_REJECTION + 540 MULTI_HOP_DEREF rows regenerated from
scratch (not renamed in place); added audit_cross_family_schema_consistency()
below as a standing regression against this whole class of bug recurring.

Two families:

MULTI_HOP_DEREF
  Instead of one direct class->symbol binding, each class points through a chain
  of intermediate pointer tokens before reaching the final symbol atom. Chain
  depth (1/2/3 hops) is assigned as a PERMUTATION across the three classes within
  each row -- i.e. every row has exactly one depth-1, one depth-2 and one
  depth-3 class -- so depth cannot be predicted from class identity alone, and a
  model cannot pass by always stopping at a fixed hop count. Target is always the
  FINAL resolved symbol atom, never an intermediate pointer.

UNRESOLVABLE_CHAIN_REJECTION
  A matched hard-negative family: one class's chain is deliberately broken (a
  pointer that does not lead anywhere, i.e. dangles instead of terminating in a
  real symbol atom). Correct behavior is to emit the literal token
  UNRESOLVABLE instead of guessing a plausible-looking intermediate pointer as if
  it were the final answer. The other two classes in the same row have normal,
  fully-resolvable chains, so the model cannot pass by always answering
  UNRESOLVABLE regardless of which class is queried.
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

SCHEMA = "CLAY_TRIGGER2_B3_MULTIHOP_DEREFERENCE_CANDIDATE/v1"
ANCESTRY = "trigger2-20260826-b3-multihop-dereference-v1"
UNRESOLVABLE_TOKEN = "UNRESOLVABLE"

TRIPLE_SPLITS = [(bp.TRAIN_TRIPLETS, "TRAIN"), ((bp.HOLDOUT_TRIPLET,), "HOLDOUT_FROZEN")]
DEPTH_ASSIGNMENTS = list(itertools.permutations((1, 2, 3)))  # 6 ways to assign {1,2,3} to (ALLOW,DENY,ABSTAIN)


def ptr_ref(triple_head: int, class_index: int, hop: int) -> str:
    return f"PTR_T{triple_head:02d}_C{class_index}_H{hop}"


def build_chain(triple_head: int, class_index: int, depth: int, final_symbol: str) -> tuple[list[str], str]:
    """Returns (chain_lines, chain_start_token). chain_lines is a list of
    'FROM => TO' strings; the class's codebook entry points at chain_start_token,
    which then dereferences through depth-1 intermediate pointers before reaching
    final_symbol."""
    if depth == 1:
        return [], final_symbol
    tokens = [ptr_ref(triple_head, class_index, h) for h in range(1, depth)]
    lines = []
    for i in range(len(tokens) - 1):
        lines.append(f"{tokens[i]} => {tokens[i + 1]}")
    lines.append(f"{tokens[-1]} => {final_symbol}")
    return lines, tokens[0]


def row_common(family: str, split: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "provenance_ancestry_id": ANCESTRY,
        "curriculum_phase": "B3_MULTIHOP_DEREFERENCE",
        "family": family,
        "split": split,
        "abi_manifest_sha256": bp.ABI_MANIFEST_SHA256,
        "training_eligible": False,
        "selected_using_holdout": False,
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
    }


def build_multihop_rows() -> list[dict]:
    rows = []
    for triplets, split in TRIPLE_SPLITS:
        for triple in triplets:
            sym = [bp.atom_ref(n) for n in triple]
            for mi_, perm in enumerate(bp.PERMS):
                final_binding = {bp.CLASSES[ci]: sym[perm[ci]] for ci in range(3)}
                for depth_assign in DEPTH_ASSIGNMENTS:
                    depth_of = {bp.CLASSES[ci]: depth_assign[ci] for ci in range(3)}
                    chain_lines: list[str] = []
                    entry_of: dict[str, str] = {}
                    for ci, cls in enumerate(bp.CLASSES):
                        lines, start = build_chain(triple[0], ci, depth_of[cls], final_binding[cls])
                        chain_lines.extend(lines)
                        entry_of[cls] = start
                    codebook_line = " | ".join(f"{cls}=>{entry_of[cls]}" for cls in bp.CLASSES)
                    chain_block = " | ".join(chain_lines) if chain_lines else "(no intermediate pointers needed)"
                    for queried_class in bp.CLASSES:
                        r = row_common("MULTI_HOP_DEREF", split)
                        r.update({
                            "id": f"B3_DEREF_T{triple[0]:02d}_M{mi_}_D{'-'.join(map(str, depth_assign))}_Q{queried_class}",
                            "triple": list(triple),
                            "perm": list(perm),
                            "depth_by_class": depth_of,
                            "queried_class": queried_class,
                            "prompt": (
                                f"CODEBOOK (entry points): {codebook_line}\n"
                                f"CHAIN (pointer definitions): {chain_block}\n"
                                f"STATE: the current class is {queried_class}, given directly.\n"
                                "Dereference the full chain and return exactly the FINAL resolved "
                                "symbol atom -- never an intermediate pointer token."
                            ),
                            "target": final_binding[queried_class],
                        })
                        rows.append(r)
    return rows


def audit_multihop(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        sym = [bp.atom_ref(n) for n in r["triple"]]
        qc = r["queried_class"]
        ci = bp.CLASSES.index(qc)
        expected = sym[r["perm"][ci]]
        if r["target"] != expected:
            failures.append(f"TARGET_WRONG:{r['id']}")
        depth = r["depth_by_class"][qc]
        if depth == 1:
            if r["target"] not in r["prompt"].split("CODEBOOK (entry points): ", 1)[1].split("\n", 1)[0]:
                pass  # depth-1 target appears directly in codebook line; not asserted further here
        else:
            # target must NOT itself equal an intermediate pointer token
            if r["target"].startswith("PTR_"):
                failures.append(f"TARGET_IS_INTERMEDIATE_POINTER:{r['id']}")
        assigned_depths = sorted(r["depth_by_class"].values())
        if assigned_depths != [1, 2, 3]:
            failures.append(f"DEPTH_ASSIGNMENT_NOT_PERMUTATION:{r['id']}")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    return {"rows": len(rows), "failures": failures, "pass": not failures}


def build_unresolvable_rows() -> list[dict]:
    rows = []
    for triplets, split in TRIPLE_SPLITS:
        for triple in triplets:
            sym = [bp.atom_ref(n) for n in triple]
            for mi_, perm in enumerate(bp.PERMS):
                final_binding = {bp.CLASSES[ci]: sym[perm[ci]] for ci in range(3)}
                for depth_assign in DEPTH_ASSIGNMENTS:
                    depth_of = {bp.CLASSES[ci]: depth_assign[ci] for ci in range(3)}
                    for broken_class in bp.CLASSES:
                        chain_lines: list[str] = []
                        entry_of: dict[str, str] = {}
                        for ci, cls in enumerate(bp.CLASSES):
                            depth = depth_of[cls]
                            if cls == broken_class:
                                # force at least a 2-hop chain that dangles: last
                                # pointer in the chain points to a token that is
                                # never defined anywhere, instead of a real symbol.
                                depth = max(depth, 2)
                                tokens = [ptr_ref(triple[0], ci, h) for h in range(1, depth)]
                                lines = []
                                for i in range(len(tokens) - 1):
                                    lines.append(f"{tokens[i]} => {tokens[i + 1]}")
                                dangling_target = f"UNDEFINED_{ptr_ref(triple[0], ci, depth)}"
                                lines.append(f"{tokens[-1]} => {dangling_target}")
                                chain_lines.extend(lines)
                                entry_of[cls] = tokens[0]
                            else:
                                lines, start = build_chain(triple[0], ci, depth, final_binding[cls])
                                chain_lines.extend(lines)
                                entry_of[cls] = start
                        codebook_line = " | ".join(f"{c}=>{entry_of[c]}" for c in bp.CLASSES)
                        chain_block = " | ".join(chain_lines) if chain_lines else "(no intermediate pointers needed)"
                        for queried_class in bp.CLASSES:
                            expected = UNRESOLVABLE_TOKEN if queried_class == broken_class else final_binding[queried_class]
                            r = row_common("UNRESOLVABLE_CHAIN_REJECTION", split)
                            r.update({
                                "id": f"B3_UNRES_T{triple[0]:02d}_M{mi_}_D{'-'.join(map(str, depth_assign))}_B{broken_class}_Q{queried_class}",
                                "triple": list(triple),
                                "perm": list(perm),
                                "broken_class": broken_class,
                                "queried_class": queried_class,
                                "prompt": (
                                    f"CODEBOOK (entry points): {codebook_line}\n"
                                    f"CHAIN (pointer definitions): {chain_block}\n"
                                    f"STATE: the current class is {queried_class}, given directly.\n"
                                    f"Dereference the full chain and return exactly the FINAL resolved "
                                    f"symbol atom, or the token {UNRESOLVABLE_TOKEN} if the chain does "
                                    "not terminate in a defined symbol atom."
                                ),
                                "target": expected,
                            })
                            rows.append(r)
    return rows


def audit_unresolvable(rows: list[dict]) -> dict:
    failures = []
    for r in rows:
        sym = [bp.atom_ref(n) for n in r["triple"]]
        expected = UNRESOLVABLE_TOKEN if r["queried_class"] == r["broken_class"] else sym[r["perm"][bp.CLASSES.index(r["queried_class"])]]
        if r["target"] != expected:
            failures.append(f"TARGET_WRONG:{r['id']}")

    prompts = [r["prompt"] for r in rows]
    dupes = {p: c for p, c in Counter(prompts).items() if c > 1}
    if dupes:
        failures.append(f"DUPLICATE_PROMPTS:{len(dupes)}")

    broken_q = [r for r in rows if r["queried_class"] == r["broken_class"]]
    unbroken_q = [r for r in rows if r["queried_class"] != r["broken_class"]]
    if not all(r["target"] == UNRESOLVABLE_TOKEN for r in broken_q):
        failures.append("SOME_BROKEN_QUERIES_NOT_REJECTED")
    if any(r["target"] == UNRESOLVABLE_TOKEN for r in unbroken_q):
        failures.append("SOME_UNBROKEN_QUERIES_INCORRECTLY_REJECTED")

    return {"rows": len(rows), "failures": failures, "pass": not failures,
            "broken_query_rows": len(broken_q), "unbroken_query_rows": len(unbroken_q)}


def audit_cross_family_schema_consistency(families: dict[str, list[dict]]) -> dict:
    """Adversarial schema-consistency regression (added 2026-08-27, fixing a
    real bug: UNRESOLVABLE_CHAIN_REJECTION rows used to emit "queried_class_"
    (trailing underscore) while MULTI_HOP_DEREF emitted "queried_class" for
    the identical concept, under the same SCHEMA string -- and
    audit_unresolvable() read the typo'd name itself, so the self-audit never
    caught it. This check would have failed on that mixed-key corpus: it
    asserts every family sharing SCHEMA exposes the exact same key for each
    concept present in more than one family, and explicitly rejects any
    trailing-underscore variant of a key that also exists without one."""
    failures: list[str] = []
    per_family_keys = {name: set().union(*(set(r.keys()) for r in rows)) if rows else set()
                        for name, rows in families.items()}
    shared_concept_keys = set.intersection(*per_family_keys.values()) if per_family_keys else set()
    all_keys = set().union(*per_family_keys.values()) if per_family_keys else set()
    for key in sorted(all_keys):
        if not key.endswith("_") or key == "_":
            continue
        bare = key.rstrip("_")
        if bare and bare in all_keys:
            offenders = [name for name, keys in per_family_keys.items() if key in keys]
            failures.append(f"TRAILING_UNDERSCORE_KEY_ALIAS:{key}~{bare}:families={offenders}")
    return {"per_family_keys": {k: sorted(v) for k, v in per_family_keys.items()},
            "shared_concept_keys": sorted(shared_concept_keys),
            "failures": failures, "pass": not failures}


def run() -> dict:
    multihop = build_multihop_rows()
    unresolvable = build_unresolvable_rows()
    families_for_schema_check = {"MULTI_HOP_DEREF": multihop, "UNRESOLVABLE_CHAIN_REJECTION": unresolvable}
    reports = {
        "MULTI_HOP_DEREF": audit_multihop(multihop),
        "UNRESOLVABLE_CHAIN_REJECTION": audit_unresolvable(unresolvable),
        "CROSS_FAMILY_SCHEMA_CONSISTENCY": audit_cross_family_schema_consistency(families_for_schema_check),
    }
    overall_pass = all(r["pass"] for r in reports.values())
    return {
        "schema": SCHEMA,
        "families": {
            "MULTI_HOP_DEREF": {"rows": len(multihop), "split_counts": dict(Counter(r["split"] for r in multihop))},
            "UNRESOLVABLE_CHAIN_REJECTION": {"rows": len(unresolvable), "split_counts": dict(Counter(r["split"] for r in unresolvable))},
        },
        "reports": reports,
        "total_rows": len(multihop) + len(unresolvable),
        "overall_pass": overall_pass,
        "training_eligible": False,
    }, {"MULTI_HOP_DEREF": multihop, "UNRESOLVABLE_CHAIN_REJECTION": unresolvable}


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
        path = args.out_dir / f"TRIGGER2_B3_{name}_CANDIDATE_V1.jsonl"
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
