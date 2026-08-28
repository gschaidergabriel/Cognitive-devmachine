#!/usr/bin/env python3
"""Deterministic Trigger-2 curriculum generator for context-dependent codebook binding.

Source/candidate tool only. It does not train a model, admit canonical dataset rows,
or mint runtime/J-Space/HCU/EntityOS/training credit.

Design goals derived from the 2026-08-25 measured XENO vector-language package:
- teach context-invariant semantic -> episode-local symbol binding/routing;
- realize actual S3 class<->symbol permutations, not metadata-only permutations;
- exactly counterbalance class/symbol association within every generated atom block;
- vary template, codebook order, query polarity, and lexical realization;
- fail closed on target-class leakage outside the episode-local codebook;
- require externally supplied one-token atoms for production-style generation.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_CONTEXT_BINDING_GENERATOR/v1"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SPLITS = {"TRAIN", "VALIDATION", "HOLDOUT"}
POLARITIES = ("DIRECT", "INVERTED")

# Target semantics are intentionally simple because the measured deficit is binding/routing,
# not semantic readout. No literal target class word appears outside the codebook.
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
        # Strings alone are not enough to prove single-token identity for production.
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
    if len(atoms) < 3:
        raise ValueError("at least three atoms required")
    if require_single_token:
        bad = [a.text for a in atoms if a.token_count != 1 or a.token_id is None]
        if bad:
            raise ValueError("production atoms require observed token_id and token_count=1: " + repr(bad[:5]))
    return atoms


def demo_atoms() -> list[Atom]:
    # Synthetic-only unit-test atoms. They are NOT claims about the measured tokenizer/alphabet.
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
    lines = ["CODEBOOK"]
    lines.extend(f"{klass} -> {mapping[klass]}" for klass in order)
    lines.append("END_CODEBOOK")
    return "\n".join(lines)


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
        if lhs not in CLASSES or not rhs:
            raise ValueError("malformed class/symbol entry")
        if lhs in mapping:
            raise ValueError("duplicate class in codebook")
        mapping[lhs] = rhs
    if set(mapping) != set(CLASSES):
        raise ValueError("codebook must cover exactly all classes")
    return mapping


def generate_rows(
    atoms: list[Atom],
    *,
    split: str = "TRAIN",
    blocks: int = 1,
    seed: int = 20260825,
    provenance_prefix: str = "trigger2-context-binding-v1",
) -> list[dict[str, Any]]:
    if split not in SPLITS:
        raise ValueError(f"invalid split: {split}")
    if any(a.token_count != 1 or a.token_id is None for a in atoms):
        raise ValueError("generation requires externally observed single-token atoms")
    rng = random.Random(seed)
    triplets = _choose_triplets(atoms, blocks, rng)
    rows: list[dict[str, Any]] = []
    templates = tuple(SEMANTIC_BANK)
    class_permutations = tuple(itertools.permutations(range(3)))
    codebook_orders = tuple(itertools.permutations(CLASSES))

    row_index = 0
    for block_id, triplet in enumerate(triplets):
        atom_texts = tuple(a.text for a in triplet)
        atom_ids = tuple(a.token_id for a in triplet)
        for perm_index, perm in enumerate(class_permutations):
            # CRITICAL: the actual mapping is constructed from the selected S3 permutation.
            mapping = {CLASSES[i]: atom_texts[perm[i]] for i in range(3)}
            mapped_ids = {CLASSES[i]: atom_ids[perm[i]] for i in range(3)}
            for template_index, template in enumerate(templates):
                for polarity_index, polarity in enumerate(POLARITIES):
                    for base_class_index, base_class in enumerate(CLASSES):
                        target_class = semantic_after_polarity(base_class, polarity)
                        # Cycle lexical variants so mappings/classes/templates are not tied to one wording.
                        variants = SEMANTIC_BANK[template][base_class]
                        variant_index = (block_id + perm_index + template_index + polarity_index + base_class_index) % len(variants)
                        situation = variants[variant_index]
                        codebook_order = codebook_orders[(row_index + seed) % len(codebook_orders)]
                        prompt = (
                            _render_codebook(mapping, codebook_order)
                            + "\n\nSITUATION\n"
                            + situation
                            + "\n\n"
                            + QUERY_TEMPLATES[template][polarity]
                            + "\nOutput exactly one codebook symbol and nothing else."
                        )
                        target_symbol = mapping[target_class]
                        row = {
                            "schema": ROW_SCHEMA,
                            "evidence_class": "METHOD_ONLY",
                            "reality_level": "R2",
                            "family_id": f"CTX_BIND_{split}_B{block_id:03d}_{template}_{polarity}",
                            "provenance_ancestry_id": f"{provenance_prefix}:{split}:B{block_id:03d}:{template}:{polarity}",
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
                        row_index += 1
    return rows


def validate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    failures: list[str] = []
    class_symbol_counts: dict[str, Counter[str]] = {klass: Counter() for klass in CLASSES}
    permutation_coverage: dict[tuple[Any, ...], set[tuple[int, int, int]]] = defaultdict(set)
    template_counts: Counter[str] = Counter()
    polarity_counts: Counter[str] = Counter()
    target_class_counts: Counter[str] = Counter()
    codebook_orders: set[tuple[str, ...]] = set()

    for i, row in enumerate(rows):
        try:
            prompt = row["prompt"]
            meta = row["curriculum"]
            parsed = parse_codebook(prompt)
            declared = meta["mapping"]
            if parsed != declared:
                failures.append(f"MAPPING_TEXT_METADATA_MISMATCH:{i}")
            perm = tuple(meta["s3_permutation"])
            atom_triplet = tuple(meta["atom_triplet"])
            if sorted(perm) != [0, 1, 2] or len(atom_triplet) != 3:
                failures.append(f"S3_PERMUTATION_METADATA_INVALID:{i}")
            else:
                reconstructed = {CLASSES[j]: atom_triplet[perm[j]] for j in range(3)}
                if parsed != reconstructed:
                    failures.append(f"S3_PERMUTATION_NOT_CAUSAL:{i}")
            target_class = meta["target_semantic_class"]
            if row["target"] != parsed[target_class]:
                failures.append(f"TARGET_NOT_DERIVED_FROM_ACTUAL_MAPPING:{i}")
            if mapping_digest(parsed) != meta["mapping_sha256"]:
                failures.append(f"MAPPING_DIGEST_MISMATCH:{i}")
            leaks = class_word_leaks(prompt)
            if leaks:
                failures.append(f"CLASS_WORD_LEAK_OUTSIDE_CODEBOOK:{i}:{','.join(leaks)}")
            if row.get("selected_using_holdout") is not False:
                failures.append(f"HOLDOUT_SELECTION_FLAG_INVALID:{i}")
            if row.get("canonical_truth_allowed") is not False or row.get("direct_effect_authority") is not False:
                failures.append(f"AUTHORITY_FLAG_INVALID:{i}")
            for klass, symbol in parsed.items():
                class_symbol_counts[klass][symbol] += 1
            key = (
                tuple(meta["atom_triplet"]),
                meta["template_family"],
                meta["query_polarity"],
            )
            permutation_coverage[key].add(tuple(meta["s3_permutation"]))
            template_counts[meta["template_family"]] += 1
            polarity_counts[meta["query_polarity"]] += 1
            target_class_counts[target_class] += 1
            codebook_orders.add(tuple(meta["codebook_order"]))
        except Exception as exc:  # fail closed and preserve row index
            failures.append(f"ROW_PARSE_OR_SCHEMA_FAILURE:{i}:{type(exc).__name__}:{exc}")

    for key, perms in permutation_coverage.items():
        if len(perms) != 6:
            failures.append(f"S3_COVERAGE_INCOMPLETE:{key}:{len(perms)}")

    all_symbols = sorted(set().union(*(set(c) for c in class_symbol_counts.values())))
    for symbol in all_symbols:
        counts = [class_symbol_counts[klass][symbol] for klass in CLASSES]
        if max(counts) != min(counts):
            failures.append(f"CLASS_SYMBOL_COUNTERBALANCE_FAIL:{symbol}:{counts}")

    if template_counts and len(set(template_counts.values())) != 1:
        failures.append(f"TEMPLATE_IMBALANCE:{dict(template_counts)}")
    if polarity_counts and len(set(polarity_counts.values())) != 1:
        failures.append(f"POLARITY_IMBALANCE:{dict(polarity_counts)}")
    if target_class_counts and len(set(target_class_counts.values())) != 1:
        failures.append(f"TARGET_CLASS_IMBALANCE:{dict(target_class_counts)}")
    if rows and len(codebook_orders) < 2:
        failures.append("CODEBOOK_ORDER_NOT_RANDOMIZED")

    return {
        "schema": "CLAY_TRIGGER2_CONTEXT_BINDING_GENERATOR_AUDIT/v1",
        "pass": not failures,
        "rows_total": len(rows),
        "failures": failures,
        "s3_groups": len(permutation_coverage),
        "s3_groups_complete": sum(1 for p in permutation_coverage.values() if len(p) == 6),
        "template_counts": dict(sorted(template_counts.items())),
        "polarity_counts": dict(sorted(polarity_counts.items())),
        "target_class_counts": dict(sorted(target_class_counts.items())),
        "codebook_order_variants": len(codebook_orders),
        "class_symbol_counts": {k: dict(sorted(v.items())) for k, v in class_symbol_counts.items()},
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Synthetic method-only curriculum validation; no model/runtime/J-Space/whole-product credit.",
    }


def write_jsonl(rows: Iterable[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--atom-file", type=Path)
    p.add_argument("--demo-atoms", action="store_true", help="synthetic unit-test atoms only; never training-ready")
    p.add_argument("--split", choices=sorted(SPLITS), default="TRAIN")
    p.add_argument("--blocks", type=int, default=1)
    p.add_argument("--seed", type=int, default=20260825)
    p.add_argument("--out", type=Path)
    p.add_argument("--audit-out", type=Path)
    args = p.parse_args()

    if bool(args.atom_file) == bool(args.demo_atoms):
        p.error("choose exactly one of --atom-file or --demo-atoms")
    atoms = demo_atoms() if args.demo_atoms else load_atoms(args.atom_file, require_single_token=True)
    rows = generate_rows(atoms, split=args.split, blocks=args.blocks, seed=args.seed)
    audit = validate_rows(rows)
    if args.out:
        write_jsonl(rows, args.out)
    if args.audit_out:
        args.audit_out.write_text(json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
