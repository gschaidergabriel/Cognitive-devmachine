#!/usr/bin/env python3
"""Fail-closed specialized gate for Trigger-2 dynamic codebook/binding candidates.

Stricter than the generic trainingtrace candidate gate: verifies that S3 permutation
metadata is causally realized in the prompt mapping, target symbols are derived from
that realized mapping, semantic labels/forbidden lexemes do not leak outside the
explicit codebook span, frozen template/symbol/permutation holdouts remain isolated,
and TRAIN class<->symbol identity has near-zero mutual information.

This is source/candidate validation only. It cannot admit a canonical dataset or mint
runtime, J-Space, HCU, EntityOS, or training credit.
"""
from __future__ import annotations
import argparse, collections, json, math, re
from pathlib import Path

SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_GATE/v1"
ROW_SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_CANDIDATE/v1"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
S3 = {
    "P012": (0, 1, 2), "P021": (0, 2, 1), "P102": (1, 0, 2),
    "P120": (1, 2, 0), "P201": (2, 0, 1), "P210": (2, 1, 0),
}
SPLITS = {"TRAIN", "VALIDATION", "HOLDOUT"}
EVAL_FAMILIES = {
    "TRAIN_CORE", "VALIDATION_PERM", "HOLDOUT_PERM",
    "HOLDOUT_SYMBOL", "HOLDOUT_TEMPLATE",
}
CODEBOOK_RE = re.compile(r"\[CODEBOOK\](.*?)\[/CODEBOOK\]", re.S)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _mi_bits(rows):
    pairs = [(r["target_semantic_class"], r["target"]) for r in rows]
    if not pairs:
        return float("inf")
    n = len(pairs)
    joint = collections.Counter(pairs)
    pc = collections.Counter(c for c, _ in pairs)
    ps = collections.Counter(s for _, s in pairs)
    return sum(
        (k / n) * math.log2((k / n) / ((pc[c] / n) * (ps[s] / n)))
        for (c, s), k in joint.items()
    )


def _strip_codebook(prompt):
    m = CODEBOOK_RE.search(prompt)
    if not m:
        return None, prompt
    return m.group(1), prompt[:m.start()] + prompt[m.end():]


def validate(rows, forbidden_lexemes):
    global_failures, row_failures = [], []
    family_split, ancestry_split = {}, {}

    for i, r in enumerate(rows):
        failures = []
        if r.get("schema") != ROW_SCHEMA:
            failures.append("ROW_SCHEMA")
        if r.get("split") not in SPLITS:
            failures.append("SPLIT")
        if r.get("eval_family") not in EVAL_FAMILIES:
            failures.append("EVAL_FAMILY")
        if r.get("canonical_truth_allowed") is not False:
            failures.append("CANONICAL_TRUTH_FALSE_REQUIRED")
        if r.get("direct_effect_authority") is not False:
            failures.append("DIRECT_EFFECT_FALSE_REQUIRED")
        if r.get("selected_using_holdout") is not False:
            failures.append("HOLDOUT_SELECTION_FORBIDDEN")

        cls = r.get("target_semantic_class")
        atoms = r.get("episode_atom_triplet")
        pid = r.get("permutation_id")
        perm = S3.get(pid)
        mapping = r.get("realized_codebook")
        if cls not in CLASSES:
            failures.append("TARGET_CLASS")
        if not isinstance(atoms, list) or len(atoms) != 3 or len(set(map(str, atoms))) != 3:
            failures.append("ATOM_TRIPLET")
        if perm is None:
            failures.append("PERMUTATION_ID")
        if not isinstance(mapping, dict) or set(mapping) != set(CLASSES):
            failures.append("REALIZED_CODEBOOK")
        elif isinstance(atoms, list) and len(atoms) == 3 and perm:
            expected = {c: atoms[perm[j]] for j, c in enumerate(CLASSES)}
            if mapping != expected:
                failures.append("PERMUTATION_NOT_CAUSALLY_REALIZED")
            if cls in CLASSES and r.get("target") != expected.get(cls):
                failures.append("TARGET_NOT_DERIVED_FROM_MAPPING")

        prompt = r.get("prompt")
        if not isinstance(prompt, str):
            failures.append("PROMPT")
        else:
            codebook, outside = _strip_codebook(prompt)
            if codebook is None:
                failures.append("CODEBOOK_SPAN_REQUIRED")
            elif isinstance(mapping, dict):
                for c in CLASSES:
                    pat = rf"\b{c}\b\s*=>\s*{re.escape(str(mapping.get(c, '')))}"
                    if not re.search(pat, codebook):
                        failures.append("PROMPT_CODEBOOK_MISMATCH:" + c)
            for lexeme in list(CLASSES) + forbidden_lexemes:
                if lexeme and re.search(rf"\b{re.escape(lexeme)}\b", outside, flags=re.I):
                    failures.append("SEMANTIC_LABEL_LEAK:" + lexeme.lower())

        template_id = r.get("template_id")
        if not isinstance(template_id, str) or not template_id:
            failures.append("TEMPLATE_ID")
        elif template_id == "T5_FROZEN_UNSEEN" and r.get("eval_family") != "HOLDOUT_TEMPLATE":
            failures.append("FROZEN_TEMPLATE_LEAK")

        for name, value, registry in (
            ("FAMILY", r.get("family_id"), family_split),
            ("ANCESTRY", r.get("provenance_ancestry_id"), ancestry_split),
        ):
            if not isinstance(value, str) or not value:
                failures.append(name + "_ID")
            else:
                split = str(r.get("split"))
                prior = registry.get(value)
                if prior is not None and prior != split:
                    failures.append(name + "_CROSSES_SPLIT")
                registry[value] = split

        for key in (
            "abi_manifest_sha256", "atom_inventory_sha256",
            "generator_sha256", "forbidden_lexeme_inventory_sha256",
        ):
            value = r.get(key)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                failures.append("PROVENANCE_SHA:" + key)

        if failures:
            row_failures.append({"row": i, "failures": sorted(set(failures))})

    train = [
        r for r in rows
        if r.get("eval_family") == "TRAIN_CORE"
        and r.get("target_semantic_class") in CLASSES
        and isinstance(r.get("target"), str)
    ]
    mi = _mi_bits(train) if train else float("inf")
    per_symbol = collections.defaultdict(collections.Counter)
    for r in train:
        per_symbol[r["target"]][r["target_semantic_class"]] += 1
    imbalance = {
        symbol: dict(counts)
        for symbol, counts in per_symbol.items()
        if max(counts.get(c, 0) for c in CLASSES) - min(counts.get(c, 0) for c in CLASSES) > 1
    }
    if imbalance:
        global_failures.append("TRAIN_CLASS_SYMBOL_COUNTERBALANCE")
    if not math.isfinite(mi) or mi > 1e-6:
        global_failures.append("TRAIN_CLASS_SYMBOL_MI_NONZERO")

    all_perm = {r.get("permutation_id") for r in rows}
    train_perm = {r.get("permutation_id") for r in rows if r.get("eval_family") == "TRAIN_CORE"}
    holdout_perm = {r.get("permutation_id") for r in rows if r.get("eval_family") == "HOLDOUT_PERM"}
    if all_perm != set(S3):
        global_failures.append("FULL_S3_CORPUS_COVERAGE_REQUIRED")
    if not holdout_perm or train_perm & holdout_perm:
        global_failures.append("UNSEEN_PERM_HOLDOUT_NOT_ISOLATED")

    train_atoms = {
        atom for r in rows if r.get("eval_family") == "TRAIN_CORE"
        for atom in r.get("episode_atom_triplet", []) if isinstance(atom, str)
    }
    holdout_atoms = {
        atom for r in rows if r.get("eval_family") == "HOLDOUT_SYMBOL"
        for atom in r.get("episode_atom_triplet", []) if isinstance(atom, str)
    }
    if not holdout_atoms or train_atoms & holdout_atoms:
        global_failures.append("UNSEEN_SYMBOL_HOLDOUT_NOT_ISOLATED")

    if any(
        r.get("template_id") == "T5_FROZEN_UNSEEN" and r.get("split") != "HOLDOUT"
        for r in rows
    ):
        global_failures.append("FROZEN_TEMPLATE_VISIBLE_PRE_HOLDOUT")

    return {
        "schema": SCHEMA,
        "candidate_binding_gate_pass": not global_failures and not row_failures,
        "failures": sorted(set(global_failures)),
        "row_failures": row_failures,
        "metrics": {
            "rows": len(rows),
            "train_rows": len(train),
            "train_class_symbol_mi_bits": mi,
            "full_s3_ids": sorted(x for x in all_perm if x),
            "train_permutation_ids": sorted(x for x in train_perm if x),
            "holdout_permutation_ids": sorted(x for x in holdout_perm if x),
            "train_symbols": len(train_atoms),
            "holdout_symbols": len(holdout_atoms),
        },
        "credits": {
            "canonical_dataset_write": 0,
            "accepted_dataset_tokens": 0,
            "training_credit": 0,
            "jspace_model_runtime_credit": 0,
        },
        "boundary": "Specialized source/candidate validation only; no evidence-qualified dataset admission.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument(
        "--forbidden-lexemes", required=True,
        help="JSON array of semantic labels/synonyms forbidden outside [CODEBOOK].",
    )
    ns = ap.parse_args()
    rows = [json.loads(x) for x in Path(ns.jsonl).read_text().splitlines() if x.strip()]
    lexemes = json.loads(Path(ns.forbidden_lexemes).read_text())
    if not isinstance(lexemes, list) or not all(isinstance(x, str) for x in lexemes):
        raise SystemExit("forbidden lexeme file must be a JSON string array")
    result = validate(rows, lexemes)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["candidate_binding_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
