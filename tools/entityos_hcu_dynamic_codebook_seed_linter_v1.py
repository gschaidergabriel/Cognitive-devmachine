#!/usr/bin/env python3
"""Fail-closed source linter for Trigger-2 dynamic-codebook pre-materialization rows.

This linter verifies structural independence and leakage properties that the generic
candidate-row gate intentionally does not cover. It does NOT make rows model-consumable,
does NOT verify tokenizer behavior, and does NOT admit rows into a canonical dataset.
"""
from __future__ import annotations
import argparse, collections, hashlib, itertools, json, math, re
from pathlib import Path

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SPLITS = ("TRAIN", "VALIDATION", "HOLDOUT")
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
EXPECTED_PERMS = {f"S3_{i}" for i in range(6)}
CLASS_RE = re.compile(r"\b(?:ALLOW|DENY|ABSTAIN)\b")
ATOM_RE = re.compile(r"^\{\{ABI:(\d{2})\}\}$")
CODEBOOK_RE = re.compile(r"\[CODEBOOK\]\n(.*?)\n\[/CODEBOOK\]", re.S)

def mi_bits(xs, ys):
    n = len(xs)
    if n == 0:
        return float("nan")
    cx = collections.Counter(xs); cy = collections.Counter(ys)
    cxy = collections.Counter(zip(xs, ys))
    out = 0.0
    for (x, y), c in cxy.items():
        pxy = c / n; px = cx[x] / n; py = cy[y] / n
        out += pxy * math.log2(pxy / (px * py))
    return out

def lint(rows):
    failures = []
    if not rows:
        return {"pass": False, "failures": ["EMPTY_DATASET"]}

    for i, r in enumerate(rows, 1):
        tag = f"ROW_{i}"
        if r.get("schema") != ROW_SCHEMA:
            failures.append(f"{tag}:SCHEMA")
        if r.get("evidence_class") not in {"METHOD_ONLY", "SYNTHETIC_HARD_NEGATIVE"}:
            failures.append(f"{tag}:EVIDENCE_CLASS_NOT_SOURCE_ONLY")
        if r.get("canonical_truth_allowed") is not False or r.get("direct_effect_authority") is not False:
            failures.append(f"{tag}:AUTHORITY")
        if r.get("model_consumable") is not False:
            failures.append(f"{tag}:PREMATERIALIZED_ROW_MUST_NOT_BE_MODEL_CONSUMABLE")
        if r.get("materialization_status") != "AWAITING_VERIFIED_ABI_ATOM_TABLE_AND_EXACT_TOKENIZER_CHECK":
            failures.append(f"{tag}:MATERIALIZATION_STATUS")
        if r.get("split") not in SPLITS:
            failures.append(f"{tag}:SPLIT")
        if r.get("split_unit") != "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY":
            failures.append(f"{tag}:SPLIT_UNIT")
        if r.get("selected_using_holdout") is not False:
            failures.append(f"{tag}:HOLDOUT_SELECTION")
        if r.get("s3_permutation_id") not in EXPECTED_PERMS:
            failures.append(f"{tag}:PERM_ID")

        mapping = r.get("mapping_class_to_accepted_atom_index")
        if not isinstance(mapping, dict) or set(mapping) != set(CLASSES):
            failures.append(f"{tag}:MAPPING_KEYS")
            continue
        vals = list(mapping.values())
        if len(set(vals)) != 3 or any(not isinstance(v, int) or v < 0 or v > 45 for v in vals):
            failures.append(f"{tag}:MAPPING_ATOMS")

        tc = r.get("target_class_hidden_metadata")
        if tc not in CLASSES:
            failures.append(f"{tag}:TARGET_CLASS")
        target_idx = r.get("target_accepted_atom_index")
        if tc in mapping and target_idx != mapping[tc]:
            failures.append(f"{tag}:TARGET_MAPPING_CAUSALITY")
        m = ATOM_RE.match(str(r.get("target", "")))
        if not m or int(m.group(1)) != target_idx:
            failures.append(f"{tag}:TARGET_PLACEHOLDER")

        prompt = r.get("prompt")
        if not isinstance(prompt, str):
            failures.append(f"{tag}:PROMPT")
            continue
        cbm = CODEBOOK_RE.search(prompt)
        if not cbm:
            failures.append(f"{tag}:CODEBOOK_BLOCK")
            continue
        outside = prompt[:cbm.start()] + prompt[cbm.end():]
        if CLASS_RE.search(outside):
            failures.append(f"{tag}:CLASS_LABEL_LEAK_OUTSIDE_CODEBOOK")
        lines = cbm.group(1).splitlines()
        parsed = {}
        for line in lines:
            if "=>" not in line:
                failures.append(f"{tag}:CODEBOOK_LINE")
                continue
            c, atom = line.split("=>", 1)
            c = c.strip(); atom = atom.strip()
            am = ATOM_RE.match(atom)
            if c not in CLASSES or not am:
                failures.append(f"{tag}:CODEBOOK_PARSE")
                continue
            parsed[c] = int(am.group(1))
        if parsed != mapping:
            failures.append(f"{tag}:PERMUTATION_METADATA_NOT_CAUSAL")
        if list(r.get("codebook_entry_order", [])) != [line.split("=>",1)[0].strip() for line in lines]:
            failures.append(f"{tag}:ENTRY_ORDER_METADATA_MISMATCH")

        sem = r.get("semantic_bearing_lexemes")
        if not isinstance(sem, list) or not sem or any(not isinstance(x, str) or not x for x in sem):
            failures.append(f"{tag}:SEMANTIC_LEXEMES")
        else:
            canonical = sorted(set(x.lower() for x in sem))
            got_hash = hashlib.sha256("\n".join(canonical).encode("utf-8")).hexdigest()
            if r.get("semantic_lexeme_inventory_sha256") != got_hash:
                failures.append(f"{tag}:SEMANTIC_LEXEME_HASH")
            case_match = re.search(r"\[CASE\]\n(.*?)\n\[/CASE\]", prompt, re.S)
            case_norm = (case_match.group(1).lower() if case_match else "")
            for lex in canonical:
                if lex not in case_norm:
                    failures.append(f"{tag}:SEMANTIC_LEXEME_NOT_IN_CASE:{lex}")

    for key in ("family_id", "provenance_ancestry_id", "template_id"):
        by = {}
        for r in rows:
            by.setdefault(r.get(key), set()).add(r.get("split"))
        for value, ss in by.items():
            if len(ss) > 1:
                failures.append(f"{key.upper()}_CROSSES_SPLITS:{value}:{sorted(ss)}")

    by_template = collections.defaultdict(list)
    for r in rows:
        by_template[r.get("template_id")].append(r)
    train_templates = [t for t, rr in by_template.items() if rr and rr[0].get("split") == "TRAIN"]
    if len(train_templates) < 4:
        failures.append("FEWER_THAN_FOUR_TRAIN_TEMPLATES")
    holdout_templates = [t for t, rr in by_template.items() if rr and rr[0].get("split") == "HOLDOUT"]
    if not holdout_templates:
        failures.append("NO_FROZEN_HOLDOUT_TEMPLATE")

    template_stats = {}
    for tid, rr in sorted(by_template.items()):
        perms = {r.get("s3_permutation_id") for r in rr}
        if perms != EXPECTED_PERMS:
            failures.append(f"{tid}:INCOMPLETE_S3:{sorted(perms)}")
        pair_counts = collections.Counter((r.get("target_class_hidden_metadata"), r.get("target_accepted_atom_index")) for r in rr)
        nonzero = list(pair_counts.values())
        if not nonzero or max(nonzero) != min(nonzero):
            failures.append(f"{tid}:CLASS_SYMBOL_NOT_EXACTLY_COUNTERBALANCED")
        ccounts = collections.Counter(r.get("target_class_hidden_metadata") for r in rr)
        if len(set(ccounts.values())) != 1:
            failures.append(f"{tid}:CLASS_NOT_BALANCED")
        template_stats[tid] = {
            "n": len(rr),
            "split": rr[0].get("split"),
            "s3_count": len(perms),
            "class_counts": dict(sorted(ccounts.items())),
            "class_symbol_pair_count_min": min(nonzero) if nonzero else 0,
            "class_symbol_pair_count_max": max(nonzero) if nonzero else 0,
        }

    split_lexemes = {s: set() for s in SPLITS}
    for r in rows:
        split_lexemes[r.get("split")].update(x.lower() for x in r.get("semantic_bearing_lexemes", []) if isinstance(x, str))
    for a, b in itertools.combinations(SPLITS, 2):
        overlap = split_lexemes[a] & split_lexemes[b]
        if overlap:
            failures.append(f"SEMANTIC_LEXEME_SPLIT_LEAK:{a}:{b}:{sorted(overlap)}")

    split_atoms = {}
    for s in SPLITS:
        split_atoms[s] = set()
        for r in rows:
            if r.get("split") == s:
                split_atoms[s].update(r.get("mapping_class_to_accepted_atom_index", {}).values())
    for a, b in itertools.combinations(SPLITS, 2):
        overlap = split_atoms[a] & split_atoms[b]
        if overlap:
            failures.append(f"ATOM_POOL_LEAK:{a}:{b}:{sorted(overlap)}")

    split_stats = {}
    for s in SPLITS:
        rr = [r for r in rows if r.get("split") == s]
        if not rr:
            continue
        xs = [r["target_class_hidden_metadata"] for r in rr]
        atoms = [r["target_accepted_atom_index"] for r in rr]
        perms = [r["s3_permutation_id"] for r in rr]
        orders = ["|".join(r["codebook_entry_order"]) for r in rr]
        mi_atom = mi_bits(xs, atoms); mi_perm = mi_bits(xs, perms); mi_order = mi_bits(xs, orders)
        for name, value in (("TARGET_ATOM", mi_atom), ("PERM_ID", mi_perm), ("ENTRY_ORDER", mi_order)):
            if abs(value) > 1e-12:
                failures.append(f"{s}:NONZERO_MI_CLASS_{name}:{value}")
        split_stats[s] = {
            "n": len(rr),
            "class_counts": dict(sorted(collections.Counter(xs).items())),
            "target_atom_counts": dict(sorted(collections.Counter(atoms).items())),
            "mi_class_target_atom_bits": mi_atom,
            "mi_class_perm_id_bits": mi_perm,
            "mi_class_entry_order_bits": mi_order,
        }

    return {
        "schema": "ENTITYOS_HCU_DYNAMIC_CODEBOOK_SEED_LINT/v1",
        "pass": not failures,
        "failures": sorted(set(failures)),
        "rows": len(rows),
        "template_stats": template_stats,
        "split_stats": split_stats,
        "split_atom_indices": {k: sorted(v) for k, v in split_atoms.items()},
        "split_semantic_bearing_lexemes": {k: sorted(v) for k, v in split_lexemes.items()},
        "credit_boundary": "Source/prematerialization validation only; tokenizer, model behavior, training, canonical dataset admission, HCU and EntityOS runtime credit remain zero."
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ns = ap.parse_args()
    rows = [json.loads(x) for x in Path(ns.jsonl).read_text(encoding="utf-8").splitlines() if x.strip()]
    result = lint(rows)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)

if __name__ == "__main__":
    main()
