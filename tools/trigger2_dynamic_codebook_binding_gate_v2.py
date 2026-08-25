#!/usr/bin/env python3
"""Fail-closed Trigger-2 dynamic codebook/binding candidate gate v2.

v2 closes three high-value gaps found by adversarial review of v1:
1. a HOLDOUT_PERM permutation must be absent from *all* pre-holdout rows, including VALIDATION;
2. HOLDOUT_SYMBOL atoms must be absent from *all* pre-holdout rows, including VALIDATION;
3. provenance hashes are verified against the exact bytes supplied to the gate, not merely checked
   for 64-hex syntax.

It also requires exactly one explicit [CODEBOOK] span per prompt and isolates every template id
used by HOLDOUT_TEMPLATE from every non-HOLDOUT row.

This remains source/candidate validation only. It cannot admit a canonical dataset or mint
runtime, J-Space, HCU, EntityOS, Distillery, or training credit.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
from pathlib import Path

SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_GATE/v2"
ROW_SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_CANDIDATE/v2"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
S3 = {
    "P012": (0, 1, 2),
    "P021": (0, 2, 1),
    "P102": (1, 0, 2),
    "P120": (1, 2, 0),
    "P201": (2, 0, 1),
    "P210": (2, 1, 0),
}
SPLITS = {"TRAIN", "VALIDATION", "HOLDOUT"}
EVAL_FAMILIES = {
    "TRAIN_CORE",
    "VALIDATION_PERM",
    "HOLDOUT_PERM",
    "HOLDOUT_SYMBOL",
    "HOLDOUT_TEMPLATE",
}
CODEBOOK_RE = re.compile(r"\[CODEBOOK\](.*?)\[/CODEBOOK\]", re.S)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PROVENANCE_INPUT_FIELDS = {
    "abi_manifest_sha256": "abi_manifest",
    "atom_inventory_sha256": "atom_inventory",
    "generator_sha256": "generator_source",
    "forbidden_lexeme_inventory_sha256": "forbidden_lexemes",
    "model_identity_sha256": "model_identity",
    "tokenizer_identity_sha256": "tokenizer_identity",
}


def _sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _strip_exactly_one_codebook(prompt: str):
    matches = list(CODEBOOK_RE.finditer(prompt))
    if len(matches) != 1:
        return None, prompt, len(matches)
    m = matches[0]
    return m.group(1), prompt[: m.start()] + prompt[m.end() :], 1


def _load_lexemes(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        raise ValueError("forbidden lexeme file must be a non-empty JSON string array")
    lowered = [x.casefold() for x in value]
    if len(lowered) != len(set(lowered)):
        raise ValueError("forbidden lexeme inventory contains case-insensitive duplicates")
    return value


def validate(rows, forbidden_lexemes, expected_hashes):
    global_failures = []
    row_failures = []
    family_split = {}
    ancestry_split = {}

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
        elif isinstance(atoms, list) and len(atoms) == 3 and perm is not None:
            expected_mapping = {c: atoms[perm[j]] for j, c in enumerate(CLASSES)}
            if mapping != expected_mapping:
                failures.append("PERMUTATION_NOT_CAUSALLY_REALIZED")
            if cls in CLASSES and r.get("target") != expected_mapping.get(cls):
                failures.append("TARGET_NOT_DERIVED_FROM_MAPPING")

        prompt = r.get("prompt")
        if not isinstance(prompt, str):
            failures.append("PROMPT")
        else:
            codebook, outside, codebook_count = _strip_exactly_one_codebook(prompt)
            if codebook_count != 1:
                failures.append("EXACTLY_ONE_CODEBOOK_SPAN_REQUIRED")
            elif isinstance(mapping, dict):
                for c in CLASSES:
                    pat = rf"\b{c}\b\s*=>\s*{re.escape(str(mapping.get(c, '')))}"
                    if not re.search(pat, codebook):
                        failures.append("PROMPT_CODEBOOK_MISMATCH:" + c)
            for lexeme in list(CLASSES) + forbidden_lexemes:
                if lexeme and re.search(rf"\b{re.escape(lexeme)}\b", outside, flags=re.I):
                    failures.append("SEMANTIC_LABEL_LEAK:" + lexeme.casefold())

        template_id = r.get("template_id")
        if not isinstance(template_id, str) or not template_id:
            failures.append("TEMPLATE_ID")
        if r.get("eval_family") == "HOLDOUT_TEMPLATE" and r.get("split") != "HOLDOUT":
            failures.append("HOLDOUT_TEMPLATE_MUST_BE_HOLDOUT")

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

        # v2: bind declared provenance digests to the exact supplied bytes.
        for row_field, input_name in PROVENANCE_INPUT_FIELDS.items():
            value = r.get(row_field)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                failures.append("PROVENANCE_SHA:" + row_field)
            elif value != expected_hashes[input_name]:
                failures.append("PROVENANCE_BYTES_MISMATCH:" + row_field)

        if failures:
            row_failures.append({"row": i, "failures": sorted(set(failures))})

    train = [
        r
        for r in rows
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
        if max(counts.get(c, 0) for c in CLASSES)
        - min(counts.get(c, 0) for c in CLASSES)
        > 1
    }
    if imbalance:
        global_failures.append("TRAIN_CLASS_SYMBOL_COUNTERBALANCE")
    if not math.isfinite(mi) or mi > 1e-6:
        global_failures.append("TRAIN_CLASS_SYMBOL_MI_NONZERO")

    all_perm = {r.get("permutation_id") for r in rows}
    train_perm = {
        r.get("permutation_id") for r in rows if r.get("eval_family") == "TRAIN_CORE"
    }
    validation_perm = {
        r.get("permutation_id") for r in rows if r.get("split") == "VALIDATION"
    }
    holdout_perm = {
        r.get("permutation_id") for r in rows if r.get("eval_family") == "HOLDOUT_PERM"
    }
    pre_holdout_perm = {
        r.get("permutation_id") for r in rows if r.get("split") in {"TRAIN", "VALIDATION"}
    }
    if all_perm != set(S3):
        global_failures.append("FULL_S3_CORPUS_COVERAGE_REQUIRED")
    if not holdout_perm or pre_holdout_perm & holdout_perm:
        global_failures.append("UNSEEN_PERM_HOLDOUT_NOT_ISOLATED_FROM_PRE_HOLDOUT")

    pre_holdout_atoms = {
        atom
        for r in rows
        if r.get("split") in {"TRAIN", "VALIDATION"}
        for atom in r.get("episode_atom_triplet", [])
        if isinstance(atom, str)
    }
    train_atoms = {
        atom
        for r in rows
        if r.get("eval_family") == "TRAIN_CORE"
        for atom in r.get("episode_atom_triplet", [])
        if isinstance(atom, str)
    }
    holdout_atoms = {
        atom
        for r in rows
        if r.get("eval_family") == "HOLDOUT_SYMBOL"
        for atom in r.get("episode_atom_triplet", [])
        if isinstance(atom, str)
    }
    if not holdout_atoms or pre_holdout_atoms & holdout_atoms:
        global_failures.append("UNSEEN_SYMBOL_HOLDOUT_NOT_ISOLATED_FROM_PRE_HOLDOUT")

    holdout_template_ids = {
        r.get("template_id")
        for r in rows
        if r.get("eval_family") == "HOLDOUT_TEMPLATE"
        and isinstance(r.get("template_id"), str)
    }
    pre_holdout_template_ids = {
        r.get("template_id")
        for r in rows
        if r.get("split") in {"TRAIN", "VALIDATION"}
        and isinstance(r.get("template_id"), str)
    }
    if not holdout_template_ids:
        global_failures.append("HOLDOUT_TEMPLATE_REQUIRED")
    elif holdout_template_ids & pre_holdout_template_ids:
        global_failures.append("HOLDOUT_TEMPLATE_ID_VISIBLE_PRE_HOLDOUT")

    # v2 reports validation explicitly so an apparently sealed train split cannot hide leakage there.
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
            "validation_permutation_ids": sorted(x for x in validation_perm if x),
            "holdout_permutation_ids": sorted(x for x in holdout_perm if x),
            "train_symbols": len(train_atoms),
            "pre_holdout_symbols": len(pre_holdout_atoms),
            "holdout_symbols": len(holdout_atoms),
            "holdout_template_ids": sorted(holdout_template_ids),
            "verified_provenance_sha256": expected_hashes,
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
    ap.add_argument("--forbidden-lexemes", required=True)
    ap.add_argument("--abi-manifest", required=True)
    ap.add_argument("--atom-inventory", required=True)
    ap.add_argument("--generator-source", required=True)
    ap.add_argument("--model-identity", required=True)
    ap.add_argument("--tokenizer-identity", required=True)
    ns = ap.parse_args()

    paths = {
        "forbidden_lexemes": Path(ns.forbidden_lexemes),
        "abi_manifest": Path(ns.abi_manifest),
        "atom_inventory": Path(ns.atom_inventory),
        "generator_source": Path(ns.generator_source),
        "model_identity": Path(ns.model_identity),
        "tokenizer_identity": Path(ns.tokenizer_identity),
    }
    for name, path in paths.items():
        if not path.is_file():
            raise SystemExit(f"required provenance input missing: {name}={path}")

    try:
        lexemes = _load_lexemes(paths["forbidden_lexemes"])
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    expected_hashes = {name: _sha256_bytes(path) for name, path in paths.items()}
    rows = [
        json.loads(x)
        for x in Path(ns.jsonl).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    result = validate(rows, lexemes, expected_hashes)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["candidate_binding_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
