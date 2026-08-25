#!/usr/bin/env python3
"""Deterministic Trigger-2 v2 curriculum generator for episode-local codebook binding.

Source/candidate tool only. It does not train a model, admit canonical dataset rows,
or mint runtime/J-Space/HCU/EntityOS/training credit.

v2 closes the v1 codebook-display-order shortcut by crossing every semantic/mapping
cell with all six display orders. Counterfactual remaps preserve the same situation text.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_CONTEXT_BINDING_GENERATOR/v2"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SPLITS = {"TRAIN", "VALIDATION", "HOLDOUT"}
POLARITIES = ("DIRECT", "INVERTED")
CODEBOOK_ORDERS = tuple(itertools.permutations(CLASSES))
S3_PERMUTATIONS = tuple(itertools.permutations(range(3)))

SEMANTIC_BANK: dict[str, dict[str, tuple[str, ...]]] = {
    "procedural": {
        "ALLOW": (
            "Every required precondition is explicitly satisfied and the requested step is within scope.",
            "All mandatory checks are present, current, and compatible with proceeding.",
            "The action has the required authorization, evidence, and current-state match.",
        ),
        "DENY": (
            "A mandatory precondition is explicitly violated by the requested step.",
            "The action conflicts with a current hard constraint that is known to apply.",
            "A required authorization is explicitly absent while the action would change protected state.",
        ),
        "ABSTAIN": (
            "A mandatory precondition has not been observed, and neither satisfaction nor violation is established.",
            "The available evidence does not determine whether the required authorization is present.",
            "The relevant current-state fact is missing, so the decision cannot be established from the evidence given.",
        ),
    },
    "evidence": {
        "ALLOW": (
            "The cited observation directly supports the requested conclusion and no stated evidence contradicts it.",
            "The measured evidence closes the stated criterion at the claimed scope.",
            "The supplied observation is sufficient for the narrow conclusion being queried.",
        ),
        "DENY": (
            "The cited observation directly contradicts the requested conclusion at the claimed scope.",
            "The measured result violates a required acceptance criterion.",
            "The supplied observation rules out the queried conclusion for this case.",
        ),
        "ABSTAIN": (
            "The cited material gives a method but no observation that resolves the queried fact.",
            "The measurement needed for the requested conclusion is absent.",
            "The supplied evidence is compatible with multiple outcomes and does not distinguish them.",
        ),
    },
    "state": {
        "ALLOW": (
            "The packet epoch equals the current epoch and its provenance matches the active scope.",
            "The result identity, generation, and scope all match the current admission state.",
            "The proposal is current, provenance-bound, and within the active capability scope.",
        ),
        "DENY": (
            "The packet is stale relative to the current epoch even though its payload is otherwise well formed.",
            "The result provenance does not match the active task scope.",
            "The proposal carries a generation that is older than the current admitted generation.",
        ),
        "ABSTAIN": (
            "The packet omits the epoch needed to determine whether it is current or stale.",
            "The provenance field required to establish scope membership is missing.",
            "The generation identity is unavailable, so current-state compatibility is unresolved.",
        ),
    },
    "counterfactual": {
        "ALLOW": (
            "Under the stated branch, every required condition remains satisfied after the hypothetical change.",
            "In the proposed possible world, the queried predicate is supported and no branch condition conflicts with it.",
            "The counterfactual preserves all conditions required for the queried transition.",
        ),
        "DENY": (
            "Under the stated branch, the hypothetical change breaks a condition required for the queried transition.",
            "In the proposed possible world, a branch condition directly conflicts with the queried predicate.",
            "The counterfactual makes the queried transition inconsistent with an explicit branch constraint.",
        ),
        "ABSTAIN": (
            "The branch does not specify the variable needed to decide the queried transition.",
            "The possible world leaves a required condition unresolved, so the queried predicate is undetermined.",
            "The counterfactual omits the evidence that would distinguish satisfaction from violation.",
        ),
    },
}

QUERY_TEMPLATES: dict[str, dict[str, str]] = {
    "procedural": {
        "DIRECT": "Question: Should the operation proceed under the stated rule?",
        "INVERTED": "Question: Should the operation be stopped under the stated rule?",
    },
    "evidence": {
        "DIRECT": "Question: Does the evidence establish the queried conclusion?",
        "INVERTED": "Question: Does the evidence establish that the queried conclusion is false?",
    },
    "state": {
        "DIRECT": "Question: Is this packet admissible as current for the stated scope?",
        "INVERTED": "Question: Is this packet inadmissible because it is not established as current for the stated scope?",
    },
    "counterfactual": {
        "DIRECT": "Question: Does the queried transition hold in this branch?",
        "INVERTED": "Question: Does the queried transition fail in this branch?",
    },
}


def semantic_after_polarity(base_class: str, polarity: str) -> str:
    if polarity == "DIRECT":
        return base_class
    if polarity != "INVERTED":
        raise ValueError(f"unknown polarity: {polarity}")
    if base_class == "ALLOW":
        return "DENY"
    if base_class == "DENY":
        return "ALLOW"
    return "ABSTAIN"


@dataclass(frozen=True)
class Atom:
    text: str
    token_id: int | None = None
    token_count: int = 1


def _atom_from_obj(obj: Any) -> Atom:
    if isinstance(obj, str):
        return Atom(text=obj, token_id=None, token_count=-1)
    if not isinstance(obj, dict):
        raise ValueError("atom entry must be string or object")
    text = obj.get("text")
    if not isinstance(text, str) or not text or "\n" in text:
        raise ValueError("atom.text must be a nonempty single-line string")
    token_id = obj.get("token_id")
    if token_id is not None and not isinstance(token_id, int):
        raise ValueError("atom.token_id must be int or null")
    token_count = obj.get("token_count")
    if not isinstance(token_count, int):
        raise ValueError("atom.token_count must be int")
    return Atom(text=text, token_id=token_id, token_count=token_count)


def load_atoms(path: Path, *, require_single_token: bool = True) -> list[Atom]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("atoms")
    if not isinstance(data, list):
        raise ValueError("atom file must be a list or an object with an 'atoms' list")
    atoms = [_atom_from_obj(x) for x in data]
    if len({a.text for a in atoms}) != len(atoms):
        raise ValueError("duplicate atom text")
    if len({a.token_id for a in atoms if a.token_id is not None}) != len([a for a in atoms if a.token_id is not None]):
        raise ValueError("duplicate observed token_id")
    if len(atoms) < 3:
        raise ValueError("at least three atoms required")
    if any(a.text.lower() == "or" for a in atoms):
        raise ValueError("rejected ABI atom 'or' must not be admitted")
    if require_single_token:
        bad = [a.text for a in atoms if a.token_count != 1 or a.token_id is None]
        if bad:
            raise ValueError("production atoms require observed token_id and token_count=1: " + repr(bad[:5]))
    return atoms


def demo_atoms() -> list[Atom]:
    # Synthetic only; not claims about the measured tokenizer or accepted ABI alphabet.
    return [Atom(text=f"§{i:02d}", token_id=900000 + i, token_count=1) for i in range(12)]


def mapping_digest(mapping: dict[str, str]) -> str:
    payload = json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _choose_triplets(atoms: list[Atom], blocks: int, rng: random.Random) -> list[tuple[Atom, Atom, Atom]]:
    if blocks <= 0:
        raise ValueError("blocks must be positive")
    deck = list(atoms)
    rng.shuffle(deck)
    out: list[tuple[Atom, Atom, Atom]] = []
    cursor = 0
    for _ in range(blocks):
        if cursor + 3 > len(deck):
            rng.shuffle(deck)
            cursor = 0
        out.append((deck[cursor], deck[cursor + 1], deck[cursor + 2]))
        cursor += 3
    return out


def _render_codebook(mapping: dict[str, str], order: tuple[str, ...]) -> str:
    return "\n".join(["CODEBOOK", *(f"{klass} -> {mapping[klass]}" for klass in order), "END_CODEBOOK"])


def _outside_codebook(prompt: str) -> str:
    return re.sub(r"CODEBOOK\n.*?\nEND_CODEBOOK", "", prompt, flags=re.DOTALL)


def class_word_leaks(prompt: str) -> list[str]:
    outside = _outside_codebook(prompt).upper()
    return [klass for klass in CLASSES if re.search(rf"\b{re.escape(klass)}\b", outside)]


def parse_codebook(prompt: str) -> dict[str, str]:
    match = re.search(r"CODEBOOK\n(.*?)\nEND_CODEBOOK", prompt, flags=re.DOTALL)
    if not match:
        raise ValueError("missing codebook")
    mapping: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if "->" not in line:
            raise ValueError("malformed codebook line")
        lhs, rhs = (x.strip() for x in line.split("->", 1))
        if lhs not in CLASSES or not rhs or lhs in mapping:
            raise ValueError("malformed/duplicate class-symbol entry")
        mapping[lhs] = rhs
    if set(mapping) != set(CLASSES):
        raise ValueError("codebook must cover exactly all classes")
    return mapping


def _mutual_information(xs: list[str], ys: list[str]) -> float:
    if len(xs) != len(ys) or not xs:
        return float("nan")
    n = len(xs)
    cx, cy, cxy = Counter(xs), Counter(ys), Counter(zip(xs, ys))
    mi = 0.0
    for (x, y), count in cxy.items():
        pxy = count / n
        mi += pxy * math.log2(pxy / ((cx[x] / n) * (cy[y] / n)))
    return mi


def generate_rows(
    atoms: list[Atom],
    *,
    split: str = "TRAIN",
    blocks: int = 1,
    seed: int = 20260825,
    provenance_prefix: str = "trigger2-context-binding-v2",
) -> list[dict[str, Any]]:
    if split not in SPLITS:
        raise ValueError(f"invalid split: {split}")
    if any(a.token_count != 1 or a.token_id is None for a in atoms):
        raise ValueError("generation requires externally observed single-token atoms")
    if any(a.text.lower() == "or" for a in atoms):
        raise ValueError("rejected ABI atom 'or' must not be admitted")

    rng = random.Random(seed)
    triplets = _choose_triplets(atoms, blocks, rng)
    rows: list[dict[str, Any]] = []
    templates = tuple(SEMANTIC_BANK)

    for block_id, triplet in enumerate(triplets):
        atom_texts = tuple(a.text for a in triplet)
        atom_ids = tuple(a.token_id for a in triplet)
        for perm_index, perm in enumerate(S3_PERMUTATIONS):
            mapping = {CLASSES[i]: atom_texts[perm[i]] for i in range(3)}
            mapped_ids = {CLASSES[i]: atom_ids[perm[i]] for i in range(3)}
            for template_index, template in enumerate(templates):
                for polarity in POLARITIES:
                    for base_class_index, base_class in enumerate(CLASSES):
                        target_class = semantic_after_polarity(base_class, polarity)
                        variants = SEMANTIC_BANK[template][base_class]
                        # Remaps and order changes must keep the semantic surface fixed.
                        variant_index = (block_id + template_index + base_class_index) % len(variants)
                        situation = variants[variant_index]
                        for order_index, codebook_order in enumerate(CODEBOOK_ORDERS):
                            prompt = (
                                _render_codebook(mapping, codebook_order)
                                + "\n\nSITUATION\n"
                                + situation
                                + "\n\n"
                                + QUERY_TEMPLATES[template][polarity]
                                + "\nOutput exactly one codebook symbol and nothing else."
                            )
                            target_symbol = mapping[target_class]
                            family = f"CTX_BIND_V2_{split}_B{block_id:03d}_{template}_{polarity}_{base_class}"
                            row = {
                                "schema": ROW_SCHEMA,
                                "evidence_class": "METHOD_ONLY",
                                "reality_level": "R2",
                                "family_id": family,
                                "provenance_ancestry_id": f"{provenance_prefix}:{split}:B{block_id:03d}:{template}:{polarity}:{base_class}",
                                "canonical_truth_allowed": False,
                                "direct_effect_authority": False,
                                "fact_status": "NOT_APPLICABLE",
                                "target_type": "CONTEXT_DEPENDENT_CODEBOOK_BINDING",
                                "split": split,
                                "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                                "selected_using_holdout": False,
                                "curriculum": {
                                    "generator_schema": SCHEMA,
                                    "block_id": block_id,
                                    "template_family": template,
                                    "query_polarity": polarity,
                                    "base_semantic_class": base_class,
                                    "target_semantic_class": target_class,
                                    "s3_permutation_index": perm_index,
                                    "s3_permutation": list(perm),
                                    "codebook_order_index": order_index,
                                    "codebook_order": list(codebook_order),
                                    "mapping": mapping,
                                    "mapping_token_ids": mapped_ids,
                                    "mapping_sha256": mapping_digest(mapping),
                                    "atom_triplet": list(atom_texts),
                                    "atom_token_ids": list(atom_ids),
                                    "lexical_variant_index": variant_index,
                                },
                                "prompt": prompt,
                                "target": target_symbol,
                            }
                            rows.append(row)
    return rows


def validate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    failures: list[str] = []
    class_symbol_counts: dict[str, Counter[str]] = {klass: Counter() for klass in CLASSES}
    semantic_cells: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    mapping_cells: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    order_names: list[str] = []
    base_classes: list[str] = []
    target_classes: list[str] = []
    polarities: list[str] = []

    for i, row in enumerate(rows):
        try:
            if row.get("schema") != ROW_SCHEMA:
                failures.append(f"ROW_SCHEMA_MISMATCH:{i}")
            if row.get("evidence_class") != "METHOD_ONLY" or row.get("reality_level") != "R2":
                failures.append(f"EVIDENCE_BOUNDARY_MISMATCH:{i}")
            if row.get("canonical_truth_allowed") is not False or row.get("direct_effect_authority") is not False:
                failures.append(f"AUTHORITY_BOUNDARY_VIOLATION:{i}")
            if row.get("split_unit") != "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY" or row.get("selected_using_holdout") is not False:
                failures.append(f"SPLIT_BOUNDARY_MISMATCH:{i}")

            prompt = row["prompt"]
            meta = row["curriculum"]
            if meta.get("generator_schema") != SCHEMA:
                failures.append(f"GENERATOR_SCHEMA_MISMATCH:{i}")
            parsed = parse_codebook(prompt)
            declared = meta["mapping"]
            if parsed != declared:
                failures.append(f"MAPPING_TEXT_METADATA_MISMATCH:{i}")

            perm = tuple(meta["s3_permutation"])
            atom_triplet = tuple(meta["atom_triplet"])
            if perm not in S3_PERMUTATIONS or len(atom_triplet) != 3:
                failures.append(f"S3_PERMUTATION_METADATA_INVALID:{i}")
            else:
                reconstructed = {CLASSES[j]: atom_triplet[perm[j]] for j in range(3)}
                if reconstructed != declared:
                    failures.append(f"S3_PERMUTATION_NOT_CAUSAL:{i}")

            base_class = meta["base_semantic_class"]
            polarity = meta["query_polarity"]
            target_class = semantic_after_polarity(base_class, polarity)
            if meta.get("target_semantic_class") != target_class:
                failures.append(f"TARGET_CLASS_MISMATCH:{i}")
            if row.get("target") != declared[target_class]:
                failures.append(f"TARGET_SYMBOL_MISMATCH:{i}")
            if class_word_leaks(prompt):
                failures.append(f"CLASS_WORD_LEAK:{i}")

            outside = _outside_codebook(prompt)
            for atom in atom_triplet:
                if atom in outside:
                    failures.append(f"TARGET_ATOM_LEAK_OUTSIDE_CODEBOOK:{i}:{atom}")

            order = tuple(meta["codebook_order"])
            if order not in CODEBOOK_ORDERS:
                failures.append(f"CODEBOOK_ORDER_INVALID:{i}")
            if list(order) != meta.get("codebook_order"):
                failures.append(f"CODEBOOK_ORDER_TYPE_MISMATCH:{i}")
            if order in CODEBOOK_ORDERS and meta.get("codebook_order_index") != CODEBOOK_ORDERS.index(order):
                failures.append(f"CODEBOOK_ORDER_INDEX_MISMATCH:{i}")

            for klass in CLASSES:
                class_symbol_counts[klass][declared[klass]] += 1

            semantic_key = (
                meta["block_id"], meta["template_family"], polarity, base_class,
                tuple(meta["s3_permutation"]), tuple(atom_triplet), meta["lexical_variant_index"],
            )
            semantic_cells[semantic_key].append(row)
            mapping_key = (
                meta["block_id"], meta["template_family"], polarity, base_class,
                order, tuple(atom_triplet), meta["lexical_variant_index"],
            )
            mapping_cells[mapping_key].append(row)
            order_names.append("/".join(order))
            base_classes.append(base_class)
            target_classes.append(target_class)
            polarities.append(polarity)
        except Exception as exc:
            failures.append(f"ROW_EXCEPTION:{i}:{type(exc).__name__}:{exc}")

    expected_orders = set(CODEBOOK_ORDERS)
    for key, cell in semantic_cells.items():
        orders = {tuple(r["curriculum"]["codebook_order"]) for r in cell}
        if len(cell) != 6 or orders != expected_orders:
            failures.append(f"DISPLAY_ORDER_CELL_NOT_COMPLETE:{key!r}")
        targets = {r["target"] for r in cell}
        prompts_without_codebook = {_outside_codebook(r["prompt"]) for r in cell}
        if len(targets) != 1:
            failures.append(f"DISPLAY_ORDER_CHANGED_TARGET:{key!r}")
        if len(prompts_without_codebook) != 1:
            failures.append(f"DISPLAY_ORDER_CHANGED_SEMANTIC_SURFACE:{key!r}")

    expected_perms = set(S3_PERMUTATIONS)
    for key, cell in mapping_cells.items():
        perms = {tuple(r["curriculum"]["s3_permutation"]) for r in cell}
        if len(cell) != 6 or perms != expected_perms:
            failures.append(f"S3_COUNTERFACTUAL_CELL_NOT_COMPLETE:{key!r}")
        surfaces = {_outside_codebook(r["prompt"]) for r in cell}
        if len(surfaces) != 1:
            failures.append(f"S3_REMAP_CHANGED_SEMANTIC_SURFACE:{key!r}")

    for klass, counts in class_symbol_counts.items():
        if counts and len(set(counts.values())) != 1:
            failures.append(f"CLASS_SYMBOL_IMBALANCE:{klass}:{dict(counts)}")

    mi = {
        "order_vs_base_class_bits": _mutual_information(order_names, base_classes),
        "order_vs_target_class_bits": _mutual_information(order_names, target_classes),
        "order_vs_polarity_bits": _mutual_information(order_names, polarities),
    }
    if any((not math.isfinite(v)) or abs(v) > 1e-12 for v in mi.values()):
        failures.append("DISPLAY_ORDER_MUTUAL_INFORMATION_NONZERO")

    return {
        "schema": "CLAY_TRIGGER2_CONTEXT_BINDING_GENERATOR_AUDIT/v2",
        "status": "PASS" if not failures else "FAIL",
        "failures": sorted(set(failures)),
        "rows": len(rows),
        "expected_rows_per_block": 6 * len(SEMANTIC_BANK) * len(POLARITIES) * len(CLASSES) * 6,
        "semantic_cells": len(semantic_cells),
        "mapping_counterfactual_cells": len(mapping_cells),
        "display_order_mutual_information_bits": mi,
        "accepted_dataset_tokens": 0,
        "training_credit_minted": False,
        "jspace_credit_minted": False,
        "runtime_credit_minted": False,
        "evidence_boundary": "Source/candidate curriculum validation only; production rows still require exact ABI manifest/tokenizer/provenance binding and canonical admission."
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", type=Path)
    ap.add_argument("--demo-atoms", action="store_true")
    ap.add_argument("--split", default="TRAIN", choices=sorted(SPLITS))
    ap.add_argument("--blocks", type=int, default=1)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--audit-output", type=Path)
    ns = ap.parse_args()

    if ns.demo_atoms:
        atoms = demo_atoms()
    elif ns.atoms:
        atoms = load_atoms(ns.atoms, require_single_token=True)
    else:
        ap.error("provide --atoms or --demo-atoms")

    rows = generate_rows(atoms, split=ns.split, blocks=ns.blocks, seed=ns.seed)
    audit = validate_rows(rows)
    if ns.output:
        ns.output.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    if ns.audit_output:
        ns.audit_output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
