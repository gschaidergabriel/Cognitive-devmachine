#!/usr/bin/env python3
"""Fail-closed Trigger-2 dynamic codebook/binding candidate gate v3.

v3 preserves v2's exact-byte provenance and pre-holdout isolation checks and adds two
new adversarial controls:

1. CODEBOOK POSITION CONTROL
   The prompt's actual class-entry order is parsed, bound to a declared order id, and
   TRAIN must counterbalance target class/symbol against target line position. This
   prevents a model from passing a causally-realized S3 task by learning a residual
   first/second/third-line shortcut.

2. TOKENIZER-BOUND ATOM CONTROL
   An external atom-tokenization audit is hash-bound as provenance. Every episode atom
   must be present in that audit and be exactly one token for the exact bound tokenizer.
   A tokenizer hash or historical single-token claim alone is insufficient.

This remains source/candidate validation only. It cannot admit canonical training data
or mint runtime, J-Space, HCU, EntityOS, Distillery, or training credit.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
from pathlib import Path

SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_GATE/v3"
ROW_SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_CANDIDATE/v3"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
S3 = {
    "P012": (0, 1, 2),
    "P021": (0, 2, 1),
    "P102": (1, 0, 2),
    "P120": (1, 2, 0),
    "P201": (2, 0, 1),
    "P210": (2, 1, 0),
}
CODEBOOK_ORDERS = {
    "O012": ("ALLOW", "DENY", "ABSTAIN"),
    "O021": ("ALLOW", "ABSTAIN", "DENY"),
    "O102": ("DENY", "ALLOW", "ABSTAIN"),
    "O120": ("DENY", "ABSTAIN", "ALLOW"),
    "O201": ("ABSTAIN", "ALLOW", "DENY"),
    "O210": ("ABSTAIN", "DENY", "ALLOW"),
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
PAIR_RE = re.compile(r"\b(ALLOW|DENY|ABSTAIN)\b\s*=>\s*([^\s;,\]\[]+)", re.I)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PROVENANCE_INPUT_FIELDS = {
    "abi_manifest_sha256": "abi_manifest",
    "atom_inventory_sha256": "atom_inventory",
    "generator_sha256": "generator_source",
    "forbidden_lexeme_inventory_sha256": "forbidden_lexemes",
    "model_identity_sha256": "model_identity",
    "tokenizer_identity_sha256": "tokenizer_identity",
    "atom_tokenization_audit_sha256": "atom_tokenization_audit",
}


def _sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mi_bits(pairs):
    if not pairs:
        return float("inf")
    n = len(pairs)
    joint = collections.Counter(pairs)
    left = collections.Counter(a for a, _ in pairs)
    right = collections.Counter(b for _, b in pairs)
    return sum(
        (k / n) * math.log2((k / n) / ((left[a] / n) * (right[b] / n)))
        for (a, b), k in joint.items()
    )


def _strip_exactly_one_codebook(prompt: str):
    matches = list(CODEBOOK_RE.finditer(prompt))
    if len(matches) != 1:
        return None, prompt, [], len(matches)
    m = matches[0]
    body = m.group(1)
    outside = prompt[: m.start()] + prompt[m.end() :]
    pairs = [(c.upper(), atom) for c, atom in PAIR_RE.findall(body)]
    return body, outside, pairs, 1


def _load_lexemes(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
        raise ValueError("forbidden lexeme file must be a non-empty JSON string array")
    lowered = [x.casefold() for x in value]
    if len(lowered) != len(set(lowered)):
        raise ValueError("forbidden lexeme inventory contains case-insensitive duplicates")
    return value


def _load_tokenization_audit(path: Path, tokenizer_identity_sha256: str):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("atom tokenization audit must be a JSON object")
    if value.get("schema") != "TRIGGER2_ATOM_TOKENIZATION_AUDIT/v1":
        raise ValueError("atom tokenization audit schema mismatch")
    if value.get("tokenizer_identity_sha256") != tokenizer_identity_sha256:
        raise ValueError("atom tokenization audit is not bound to supplied tokenizer identity bytes")
    counts = value.get("atom_token_counts")
    if not isinstance(counts, dict) or not counts:
        raise ValueError("atom tokenization audit must contain atom_token_counts")
    if not all(isinstance(k, str) and k and isinstance(v, int) and v > 0 for k, v in counts.items()):
        raise ValueError("atom tokenization audit contains invalid atom/count entries")
    return counts


def _target_position(pairs, target_class):
    labels = [label for label, _ in pairs]
    if len(labels) != 3 or set(labels) != set(CLASSES):
        return None
    return labels.index(target_class)


def validate(rows, forbidden_lexemes, expected_hashes, atom_token_counts):
    global_failures = []
    row_failures = []
    family_split = {}
    ancestry_split = {}
    seen_row_ids = set()

    for i, r in enumerate(rows):
        failures = []
        row_id = r.get("row_id")
        if not isinstance(row_id, str) or not row_id:
            failures.append("ROW_ID")
        elif row_id in seen_row_ids:
            failures.append("ROW_ID_DUPLICATE")
        else:
            seen_row_ids.add(row_id)

        if r.get("schema") != ROW_SCHEMA:
            failures.append("ROW_SCHEMA")
        if r.get("status") != "CANDIDATE_NOT_ADMITTED":
            failures.append("CANDIDATE_STATUS_REQUIRED")
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
        if (
            not isinstance(atoms, list)
            or len(atoms) != 3
            or not all(isinstance(atom, str) and atom for atom in atoms)
            or len(set(atoms)) != 3
        ):
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
        pairs = []
        if not isinstance(prompt, str):
            failures.append("PROMPT")
        else:
            codebook, outside, pairs, codebook_count = _strip_exactly_one_codebook(prompt)
            if codebook_count != 1:
                failures.append("EXACTLY_ONE_CODEBOOK_SPAN_REQUIRED")
            elif isinstance(mapping, dict):
                if len(pairs) != 3 or set(c for c, _ in pairs) != set(CLASSES):
                    failures.append("EXACT_THREE_CODEBOOK_PAIRS_REQUIRED")
                else:
                    pair_map = dict(pairs)
                    if len(pair_map) != 3:
                        failures.append("DUPLICATE_CODEBOOK_CLASS")
                    elif pair_map != mapping:
                        failures.append("PROMPT_CODEBOOK_MISMATCH")
            for lexeme in list(CLASSES) + forbidden_lexemes:
                if lexeme and re.search(
                    rf"(?<!\w){re.escape(lexeme)}(?!\w)", outside, flags=re.I
                ):
                    failures.append("SEMANTIC_LABEL_LEAK:" + lexeme.casefold())

        order_id = r.get("codebook_order_id")
        expected_order = CODEBOOK_ORDERS.get(order_id)
        realized_order = tuple(c for c, _ in pairs)
        if expected_order is None:
            failures.append("CODEBOOK_ORDER_ID")
        elif realized_order != expected_order:
            failures.append("CODEBOOK_ORDER_NOT_CAUSALLY_REALIZED")

        if cls in CLASSES and pairs:
            pos = _target_position(pairs, cls)
            if pos is None:
                failures.append("TARGET_POSITION_UNRESOLVED")
            elif r.get("target_codebook_position") != pos:
                failures.append("TARGET_POSITION_METADATA_MISMATCH")

        if isinstance(atoms, list):
            for atom in atoms:
                if not isinstance(atom, str) or not atom:
                    continue
                count = atom_token_counts.get(atom)
                if count is None:
                    failures.append("ATOM_MISSING_FROM_TOKENIZATION_AUDIT:" + atom)
                elif count != 1:
                    failures.append("ATOM_NOT_SINGLE_TOKEN_AT_BOUND_TOKENIZER:" + atom)

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

        for row_field, input_name in PROVENANCE_INPUT_FIELDS.items():
            value = r.get(row_field)
            if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                failures.append("PROVENANCE_SHA:" + row_field)
            elif value != expected_hashes[input_name]:
                failures.append("PROVENANCE_BYTES_MISMATCH:" + row_field)

        review = r.get("review")
        required_reviews = (
            "architect",
            "evidence_boundary",
            "leakage",
            "causal",
            "adversarial",
            "minimality",
        )
        if not isinstance(review, dict):
            failures.append("REVIEW")
        else:
            for key in required_reviews:
                if not str(review.get(key, "")).startswith("PASS"):
                    failures.append("REVIEW:" + key)

        if failures:
            row_failures.append(
                {"row": i, "row_id": row_id, "failures": sorted(set(failures))}
            )

    train = [
        r
        for r in rows
        if r.get("eval_family") == "TRAIN_CORE"
        and r.get("target_semantic_class") in CLASSES
        and isinstance(r.get("target"), str)
        and isinstance(r.get("target_codebook_position"), int)
    ]

    mi_class_symbol = _mi_bits(
        [(r["target_semantic_class"], r["target"]) for r in train]
    )
    mi_class_position = _mi_bits(
        [(r["target_semantic_class"], r["target_codebook_position"]) for r in train]
    )
    mi_symbol_position = _mi_bits(
        [(r["target"], r["target_codebook_position"]) for r in train]
    )

    per_symbol = collections.defaultdict(collections.Counter)
    per_class_position = collections.defaultdict(collections.Counter)
    for r in train:
        per_symbol[r["target"]][r["target_semantic_class"]] += 1
        per_class_position[r["target_semantic_class"]][r["target_codebook_position"]] += 1

    symbol_imbalance = {
        symbol: dict(counts)
        for symbol, counts in per_symbol.items()
        if max(counts.get(c, 0) for c in CLASSES)
        - min(counts.get(c, 0) for c in CLASSES)
        > 1
    }
    position_imbalance = {
        cls: dict(counts)
        for cls, counts in per_class_position.items()
        if max(counts.get(p, 0) for p in (0, 1, 2))
        - min(counts.get(p, 0) for p in (0, 1, 2))
        > 1
    }

    if symbol_imbalance:
        global_failures.append("TRAIN_CLASS_SYMBOL_COUNTERBALANCE")
    if position_imbalance:
        global_failures.append("TRAIN_CLASS_POSITION_COUNTERBALANCE")
    if not math.isfinite(mi_class_symbol) or mi_class_symbol > 1e-6:
        global_failures.append("TRAIN_CLASS_SYMBOL_MI_NONZERO")
    if not math.isfinite(mi_class_position) or mi_class_position > 1e-6:
        global_failures.append("TRAIN_CLASS_POSITION_MI_NONZERO")
    if not math.isfinite(mi_symbol_position) or mi_symbol_position > 1e-6:
        global_failures.append("TRAIN_SYMBOL_POSITION_MI_NONZERO")

    all_perm = {r.get("permutation_id") for r in rows}
    pre_holdout_perm = {
        r.get("permutation_id") for r in rows if r.get("split") in {"TRAIN", "VALIDATION"}
    }
    holdout_perm = {
        r.get("permutation_id") for r in rows if r.get("eval_family") == "HOLDOUT_PERM"
    }
    if all_perm != set(S3):
        global_failures.append("FULL_S3_CORPUS_COVERAGE_REQUIRED")
    if not holdout_perm or pre_holdout_perm & holdout_perm:
        global_failures.append("UNSEEN_PERM_HOLDOUT_NOT_ISOLATED_FROM_PRE_HOLDOUT")

    train_orders = {
        r.get("codebook_order_id") for r in rows if r.get("eval_family") == "TRAIN_CORE"
    }
    if train_orders != set(CODEBOOK_ORDERS):
        global_failures.append("TRAIN_FULL_CODEBOOK_ORDER_COVERAGE_REQUIRED")

    pre_holdout_atoms = {
        atom
        for r in rows
        if r.get("split") in {"TRAIN", "VALIDATION"}
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

    return {
        "schema": SCHEMA,
        "candidate_binding_gate_pass": not global_failures and not row_failures,
        "failures": sorted(set(global_failures)),
        "row_failures": row_failures,
        "metrics": {
            "rows": len(rows),
            "train_rows": len(train),
            "train_class_symbol_mi_bits": mi_class_symbol,
            "train_class_position_mi_bits": mi_class_position,
            "train_symbol_position_mi_bits": mi_symbol_position,
            "full_s3_ids": sorted(x for x in all_perm if x),
            "pre_holdout_permutation_ids": sorted(x for x in pre_holdout_perm if x),
            "holdout_permutation_ids": sorted(x for x in holdout_perm if x),
            "train_codebook_order_ids": sorted(x for x in train_orders if x),
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
        "boundary": (
            "Specialized source/candidate validation only. Exact-byte provenance and a "
            "tokenization-audit digest do not by themselves constitute target-model runtime evidence."
        ),
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
    ap.add_argument("--atom-tokenization-audit", required=True)
    ns = ap.parse_args()

    paths = {
        "forbidden_lexemes": Path(ns.forbidden_lexemes),
        "abi_manifest": Path(ns.abi_manifest),
        "atom_inventory": Path(ns.atom_inventory),
        "generator_source": Path(ns.generator_source),
        "model_identity": Path(ns.model_identity),
        "tokenizer_identity": Path(ns.tokenizer_identity),
        "atom_tokenization_audit": Path(ns.atom_tokenization_audit),
    }
    for name, path in paths.items():
        if not path.is_file():
            raise SystemExit(f"required provenance input missing: {name}={path}")

    try:
        lexemes = _load_lexemes(paths["forbidden_lexemes"])
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    expected_hashes = {name: _sha256_bytes(path) for name, path in paths.items()}
    try:
        atom_token_counts = _load_tokenization_audit(
            paths["atom_tokenization_audit"], expected_hashes["tokenizer_identity"]
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    rows = [
        json.loads(x)
        for x in Path(ns.jsonl).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    result = validate(rows, lexemes, expected_hashes, atom_token_counts)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["candidate_binding_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
