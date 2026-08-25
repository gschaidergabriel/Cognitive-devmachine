#!/usr/bin/env python3
"""Trigger-2 C1 semantic-Hyperposition pilot blueprint v1.

Purpose
-------
Build a small, family-disjoint C1 source blueprint for the current EntityOS/HCU
Qwen3.5-0.8B-class training program.

C1 deliberately trains only a three-way finite-world fact/query relation with FIXED
semantic class labels. It does not train rules, multi-hop inference, rotating
codebooks, positive D/E transition labels, canonical truth, or effect authority.

Every row remains METHOD_ONLY and training_eligible=False. This file is a source
blueprint, not dataset admission and not training execution evidence.
"""
from __future__ import annotations

from hashlib import sha256
import collections
import json
from typing import Any, Iterable, NamedTuple

SCHEMA = "CLAY_TRIGGER2_C1_HYPERPOSITION_PILOT_GENERATOR/v1"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
CARRIER_SCHEMA = "XENO_C1_SEMANTIC_HYPERPOSITION/v1"

CLASSES = (
    "ENTAILED_BY_FACT",
    "CONTRADICTED_BY_FACT",
    "UNDETERMINED_BY_FACT",
)
POLARITIES = ("POSITIVE", "NEGATIVE")
ATOM_ROLES = ("A", "B")
ORDERS = ("FACT_FIRST", "QUERY_FIRST")
TEMPLATES = ("T0", "T1", "T2", "T3")

# Lexemes are intentionally split-disjoint fantasy tokens. No family may cross splits.
FAMILIES = (
    ("TRAIN", "C1TR01", "zorvak", "melduq", "nira", "tovel", "sumi"),
    ("TRAIN", "C1TR02", "plenix", "gafru", "vemi", "koral", "dusi"),
    ("TRAIN", "C1TR03", "trazul", "bimor", "yeka", "foni", "lusp"),
    ("TRAIN", "C1TR04", "qevan", "rildex", "humi", "saro", "nepi"),
    ("TRAIN", "C1TR05", "wopril", "cazem", "tuni", "meka", "jori"),
    ("TRAIN", "C1TR06", "draxen", "fulmi", "pavo", "zeti", "kuni"),
    ("VALIDATION", "C1VA01", "hevrix", "lomqa", "runi", "devo", "pasi"),
    ("VALIDATION", "C1VA02", "senvu", "kadrox", "mifi", "taro", "zuni"),
    ("HOLDOUT", "C1HO01", "grelix", "navoq", "buri", "xeta", "fami"),
    ("HOLDOUT", "C1HO02", "prazin", "wolek", "cumi", "ravo", "tesi"),
)


class Literal(NamedTuple):
    predicate: str
    arg1: str
    arg2: str
    negated: bool = False

    @property
    def atom(self) -> tuple[str, str, str]:
        return (self.predicate, self.arg1, self.arg2)

    def render(self) -> str:
        return ("!" if self.negated else "") + f"{self.predicate}({self.arg1},{self.arg2})"


def derive_c1_class(fact: Literal, query: Literal) -> str:
    """Mechanically derive the fixed C1 class; callers never supply the target."""
    if fact.atom != query.atom:
        return "UNDETERMINED_BY_FACT"
    return "ENTAILED_BY_FACT" if fact.negated == query.negated else "CONTRADICTED_BY_FACT"


def _query_for_class(fact: Literal, other_atom: Literal, semantic_class: str) -> Literal:
    if semantic_class == "ENTAILED_BY_FACT":
        return Literal(*fact.atom, negated=fact.negated)
    if semantic_class == "CONTRADICTED_BY_FACT":
        return Literal(*fact.atom, negated=not fact.negated)
    if semantic_class == "UNDETERMINED_BY_FACT":
        # Query polarity follows fact polarity so each class is exactly 50/50 positive/negative.
        return Literal(*other_atom.atom, negated=fact.negated)
    raise ValueError(semantic_class)


def _surface(template_id: str, order: str, fact: str, query: str) -> str:
    if template_id == "T0":
        pair = f"FACT: {fact}\nQUERY: {query}" if order == "FACT_FIRST" else f"QUERY: {query}\nFACT: {fact}"
    elif template_id == "T1":
        pair = (
            f"KNOWN[{fact}] ; TEST[{query}]"
            if order == "FACT_FIRST"
            else f"TEST[{query}] ; KNOWN[{fact}]"
        )
    elif template_id == "T2":
        pair = (
            f"Stated finite-world literal = {fact}. Candidate literal = {query}."
            if order == "FACT_FIRST"
            else f"Candidate literal = {query}. Stated finite-world literal = {fact}."
        )
    elif template_id == "T3":
        pair = (
            f"OBSERVATION<{fact}>\nCANDIDATE<{query}>"
            if order == "FACT_FIRST"
            else f"CANDIDATE<{query}>\nOBSERVATION<{fact}>"
        )
    else:
        raise ValueError(template_id)

    # The class vocabulary is intentionally fixed and identical in every row.
    return (
        "C1 SEMANTIC HYPERPOSITION\n"
        "Maintain exactly these three semantic alternatives until the stated finite-world relation resolves them:\n"
        "ENTAILED_BY_FACT | CONTRADICTED_BY_FACT | UNDETERMINED_BY_FACT\n"
        "No world knowledge and no inference rules apply.\n"
        + pair
        + "\nReturn exactly one fixed class label."
    )


def _family_rows(spec: tuple[str, str, str, str, str, str, str]) -> list[dict[str, Any]]:
    split, family_id, pred_a, pred_b, e1, e2, e3 = spec
    ancestry = f"trigger2-c1-v1:{family_id}"
    rows: list[dict[str, Any]] = []
    atom_a = Literal(pred_a, e1, e2, False)
    atom_b = Literal(pred_b, e2, e3, False)

    for atom_role in ATOM_ROLES:
        base_atom = atom_a if atom_role == "A" else atom_b
        other_atom = atom_b if atom_role == "A" else atom_a
        for fact_polarity in POLARITIES:
            fact = Literal(*base_atom.atom, negated=fact_polarity == "NEGATIVE")
            for semantic_class in CLASSES:
                query = _query_for_class(fact, other_atom, semantic_class)
                derived = derive_c1_class(fact, query)
                if derived != semantic_class:
                    raise AssertionError((fact, query, semantic_class, derived))
                for template_id in TEMPLATES:
                    for order in ORDERS:
                        prompt = _surface(template_id, order, fact.render(), query.render())
                        row = {
                            "schema": ROW_SCHEMA,
                            "evidence_class": "METHOD_ONLY",
                            "reality_level": "R2",
                            "family_id": family_id,
                            "provenance_ancestry_id": ancestry,
                            "canonical_truth_allowed": False,
                            "direct_effect_authority": False,
                            "fact_status": "NOT_APPLICABLE",
                            "target_type": "C1_FIXED_CLASS_SEMANTIC_HYPERPOSITION",
                            "split": split,
                            "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                            "selected_using_holdout": False,
                            "training_eligible": False,
                            "training_admission_scope": "CANDIDATE_SOURCE_ONLY",
                            "model_visible_fields": ["prompt"],
                            "supervision_field": "target",
                            "audit_metadata_model_visible": False,
                            "semantic_hyperposition_carrier": {
                                "schema": CARRIER_SCHEMA,
                                "live_alternatives": list(CLASSES),
                                "full_D_optimization_present": False,
                                "branch_ids_model_visible": False,
                                "branch_order_model_visible": False,
                                "resolution_basis": "FINITE_WORLD_FACT_QUERY_RELATION",
                            },
                            "c1_factors_evaluator_only": {
                                "atom_role": atom_role,
                                "fact_polarity": fact_polarity,
                                "query_polarity": "NEGATIVE" if query.negated else "POSITIVE",
                                "template_id": template_id,
                                "order": order,
                                "fact_atom": list(fact.atom),
                                "query_atom": list(query.atom),
                            },
                            "prompt": prompt,
                            "target": derived,
                        }
                        material = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                        row["row_sha256"] = sha256(material.encode("utf-8")).hexdigest()
                        rows.append(row)
    return rows


def generate_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for spec in FAMILIES:
        out.extend(_family_rows(spec))
    return out


def split_manifest() -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for split, family_id, pred_a, pred_b, e1, e2, e3 in FAMILIES:
        groups[split].append(
            {
                "family_id": family_id,
                "provenance_ancestry_id": f"trigger2-c1-v1:{family_id}",
                "predicate_lexemes": [pred_a, pred_b],
                "entity_lexemes": [e1, e2, e3],
            }
        )
    return {
        "schema": "CLAY_TRIGGER2_C1_PILOT_SPLIT_MANIFEST/v1",
        "generator_schema": SCHEMA,
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "semantic_classes": list(CLASSES),
        "families": dict(groups),
        "frozen_holdout_do_not_touch": True,
        "training_executed": False,
        "accepted_dataset_tokens": 0,
        "training_credit": 0,
    }


def validate_rows(materialized: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(materialized)
    failures: list[str] = []

    expected_family_size = len(ATOM_ROLES) * len(POLARITIES) * len(CLASSES) * len(TEMPLATES) * len(ORDERS)
    expected_total = len(FAMILIES) * expected_family_size
    if len(rows) != expected_total:
        failures.append(f"ROW_COUNT:{len(rows)}!={expected_total}")

    expected_split_families = collections.Counter(spec[0] for spec in FAMILIES)
    expected_split_rows = {s: n * expected_family_size for s, n in expected_split_families.items()}
    split_counts = collections.Counter(r.get("split") for r in rows)
    if dict(split_counts) != expected_split_rows:
        failures.append(f"SPLIT_COUNTS:{dict(split_counts)}!={expected_split_rows}")

    # No lexical/provenance family may cross splits.
    family_splits: dict[str, set[str]] = collections.defaultdict(set)
    ancestry_splits: dict[str, set[str]] = collections.defaultdict(set)
    split_lexemes: dict[str, set[str]] = collections.defaultdict(set)
    for spec in FAMILIES:
        split, family_id, pred_a, pred_b, e1, e2, e3 = spec
        split_lexemes[split].update((pred_a, pred_b, e1, e2, e3))
    for a, b in (("TRAIN", "VALIDATION"), ("TRAIN", "HOLDOUT"), ("VALIDATION", "HOLDOUT")):
        overlap = split_lexemes[a] & split_lexemes[b]
        if overlap:
            failures.append(f"LEXEME_SPLIT_OVERLAP:{a}:{b}:{sorted(overlap)}")

    class_counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    factor_counts: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    seen_hashes: set[str] = set()

    for i, row in enumerate(rows):
        split = row.get("split")
        family_splits[str(row.get("family_id"))].add(str(split))
        ancestry_splits[str(row.get("provenance_ancestry_id"))].add(str(split))
        if row.get("training_eligible") is not False:
            failures.append(f"TRAINING_ELIGIBLE_NOT_FALSE:{i}")
        if row.get("selected_using_holdout") is not False:
            failures.append(f"HOLDOUT_SELECTION_TRUE:{i}")
        if row.get("model_visible_fields") != ["prompt"] or row.get("supervision_field") != "target":
            failures.append(f"MODEL_VISIBLE_PROJECTION_INVALID:{i}")
        if row.get("canonical_truth_allowed") is not False or row.get("direct_effect_authority") is not False:
            failures.append(f"AUTHORITY_LEAK:{i}")
        carrier = row.get("semantic_hyperposition_carrier", {})
        if carrier.get("schema") != CARRIER_SCHEMA or carrier.get("full_D_optimization_present") is not False:
            failures.append(f"HYPERPOSITION_CARRIER_INVALID:{i}")

        prompt = row.get("prompt", "")
        if not isinstance(prompt, str) or not prompt:
            failures.append(f"PROMPT_INVALID:{i}")
            continue
        if "CODEBOOK" in prompt.upper() or "->" in prompt or "\nRULE" in prompt.upper():
            failures.append(f"C1_SCOPE_RULE_OR_CODEBOOK_LEAK:{i}")
        # Choice vocabulary must be identical across all rows, never target-specific.
        if any(prompt.count(label) != 1 for label in CLASSES):
            failures.append(f"FIXED_CLASS_VOCAB_INVALID:{i}")

        factors = row.get("c1_factors_evaluator_only", {})
        try:
            fact = Literal(
                factors["fact_atom"][0],
                factors["fact_atom"][1],
                factors["fact_atom"][2],
                factors["fact_polarity"] == "NEGATIVE",
            )
            query = Literal(
                factors["query_atom"][0],
                factors["query_atom"][1],
                factors["query_atom"][2],
                factors["query_polarity"] == "NEGATIVE",
            )
        except Exception:
            failures.append(f"EVALUATOR_FACTORS_INVALID:{i}")
            continue
        derived = derive_c1_class(fact, query)
        if row.get("target") != derived:
            failures.append(f"TARGET_NOT_MECHANICALLY_DERIVED:{i}")

        class_counts[str(split)][derived] += 1
        for factor_name in ("atom_role", "fact_polarity", "query_polarity", "template_id", "order"):
            factor_counts[(str(split), factor_name)][str(factors.get(factor_name))] += 1

        digest = row.get("row_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            failures.append(f"ROW_DIGEST_INVALID:{i}")
        elif digest in seen_hashes:
            failures.append(f"DUPLICATE_ROW_DIGEST:{i}")
        seen_hashes.add(str(digest))

    if any(len(s) != 1 for s in family_splits.values()):
        failures.append("FAMILY_SPLIT_LEAK")
    if any(len(s) != 1 for s in ancestry_splits.values()):
        failures.append("ANCESTRY_SPLIT_LEAK")

    for split, total in expected_split_rows.items():
        per_class = total // len(CLASSES)
        if class_counts[split] != collections.Counter({c: per_class for c in CLASSES}):
            failures.append(f"CLASS_BALANCE:{split}:{dict(class_counts[split])}")
        # Every nuisance factor is crossed independently of semantic class by construction.
        for factor_name, levels in (
            ("atom_role", ATOM_ROLES),
            ("fact_polarity", POLARITIES),
            ("query_polarity", POLARITIES),
            ("template_id", TEMPLATES),
            ("order", ORDERS),
        ):
            counter = factor_counts[(split, factor_name)]
            expected = total // len(levels)
            if counter != collections.Counter({x: expected for x in levels}):
                failures.append(f"FACTOR_BALANCE:{split}:{factor_name}:{dict(counter)}")

        # Stronger conditional law: each fixed nuisance signature leaves all 3 classes possible.
        signatures: dict[tuple[str, ...], set[str]] = collections.defaultdict(set)
        for row in rows:
            if row.get("split") != split:
                continue
            f = row["c1_factors_evaluator_only"]
            key = (
                row["family_id"],
                f["atom_role"],
                f["fact_polarity"],
                f["template_id"],
                f["order"],
            )
            signatures[key].add(row["target"])
        if any(v != set(CLASSES) for v in signatures.values()):
            failures.append(f"CONDITIONAL_NUISANCE_CLASS_SUPPORT:{split}")

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA + "/AUDIT",
        "pass": not failures,
        "failures": failures,
        "rows_total": len(rows),
        "rows_per_family": expected_family_size,
        "split_counts": dict(split_counts),
        "class_counts": {s: dict(c) for s, c in class_counts.items()},
        "fixed_class_labels": list(CLASSES),
        "rules_present": False,
        "rotating_codebook_present": False,
        "semantic_hyperposition_carrier_present": True,
        "full_D_optimization_present": False,
        "family_split_disjoint": not any("SPLIT_LEAK" in x or "LEXEME_SPLIT_OVERLAP" in x for x in failures),
        "conditional_nuisance_all_three_classes_per_signature": not any("CONDITIONAL_NUISANCE" in x for x in failures),
        "training_eligible": False,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens": 0,
        "training_credit": 0,
        "remaining_gates": [
            "freeze exact target checkpoint/tokenizer/runtime identity",
            "freeze model-visible serializer bytes and exact family manifest",
            "run tokenizer/lexical leakage checks on final rendered bytes",
            "preregister probe layers/token positions, permutation null and positive control",
            "execute zero-cost C1 pilot only after current authority/execution admission",
            "do not interpret a C1 null as model-size proof without matched positive control",
        ],
    }


def main() -> int:
    report = validate_rows(generate_rows())
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
