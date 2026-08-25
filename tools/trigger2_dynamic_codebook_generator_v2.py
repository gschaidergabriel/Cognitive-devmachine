#!/usr/bin/env python3
"""Deterministic Trigger-2 dynamic codebook/binding seed generator.

Purpose
-------
Generate and fail-closed validate a small synthetic METHOD_ONLY / SYNTHETIC_HARD_NEGATIVE
candidate corpus for the measured Xeno dynamic binding gap:

    semantic decision -> episode-local S3 codebook -> emitted symbol

This source does NOT mint canonical dataset, J-Space, training, HCU, or EntityOS credit.
It intentionally supports an ABSTRACT_SLOT template mode because the exact verified 46-atom
ABI row/name list is not exposed by current canonical repository evidence. Train-ready atom
emission must fail closed until a separately verified ABI/tokenizer input is supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
AUDIT_SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_GENERATOR_AUDIT/v2"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
ABSTRACT_SLOTS = ("@0", "@1", "@2")
S3 = tuple(itertools.permutations(ABSTRACT_SLOTS))
CLASS_WORD_POLICY = "CLASS_LABELS_ALLOWED_INSIDE_CODEBOOK_ONLY_V1"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
SOURCE_PACKAGE_SHA256 = "a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c"
MEASUREMENT_DONOR_MODEL = "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1"
MEASUREMENT_DONOR_SNAPSHOT = "591852bda6e1979f59e4b0f5ee2919697b12e936"

TRAIN_LEXICON = {
    "T1": {
        "ALLOW": "Every stated condition is satisfied and no declared conflict is present.",
        "DENY": "A declared prohibition is triggered by the request.",
        "ABSTAIN": "The available record is missing a required fact, so the decision cannot be established.",
    },
    "T2": {
        "ALLOW": "All required checks are met; nothing in the supplied evidence blocks the request.",
        "DENY": "The supplied evidence contains a direct rule breach that blocks the request.",
        "ABSTAIN": "The supplied evidence is incomplete on a decisive condition, leaving the outcome undetermined.",
    },
    "T3": {
        "ALLOW": "status=compliant; prerequisites=present; contradiction=none",
        "DENY": "status=blocked; explicit_rule_breach=present",
        "ABSTAIN": "status=indeterminate; decisive_evidence=missing",
    },
    "T4": {
        "ALLOW": "The case meets the governing constraints. The evidence is sufficient and internally compatible.",
        "DENY": "The case conflicts with a governing constraint. The conflict is explicit in the supplied evidence.",
        "ABSTAIN": "The governing constraints are known, but the case lacks enough evidence to decide between the live outcomes.",
    },
}
RESERVED_UNOPENED_TEMPLATE_FAMILY = "T5"


def _codebook(mapping: dict[str, str], order: tuple[str, ...]) -> str:
    return "<CODEBOOK>" + ";".join(f"{c}=>{mapping[c]}" for c in order) + "</CODEBOOK>"


def _render_prompt(template: str, mapping: dict[str, str], order: tuple[str, ...], scenario: str, proposed: str | None = None) -> str:
    cb = _codebook(mapping, order)
    if template == "T1":
        prompt = f"{cb}\n<SITUATION>{scenario}</SITUATION>\n<QUERY>Return only the symbol selected by the episode-local codebook.</QUERY>"
    elif template == "T2":
        prompt = (
            f"<EPISODE>{cb}\n<OBSERVATION>{scenario}</OBSERVATION>\n"
            "<INSTRUCTION>Infer the decision from the observation, then bind it through this episode's codebook. "
            "Emit the mapped symbol only.</INSTRUCTION></EPISODE>"
        )
    elif template == "T3":
        prompt = f"{cb}<STATE>{scenario}</STATE><EMIT>?</EMIT>"
    elif template == "T4":
        prompt = (
            f"<MAPPING>{cb}</MAPPING>\n<CASE>{scenario}</CASE>\n"
            "<OUTPUT_CONTRACT>Use this mapping only for this episode; output exactly the mapped symbol.</OUTPUT_CONTRACT>"
        )
    else:
        raise ValueError(f"unknown template {template}")
    if proposed is not None:
        prompt += (
            f"\n<CHECK_PROPOSAL>{proposed}</CHECK_PROPOSAL>"
            "<QUERY>Is the proposed symbol correct? If not, reject it and give the corrected symbol.</QUERY>"
        )
    return prompt


def _permutation_id(perm: tuple[str, str, str]) -> str:
    return "P" + "".join(x[-1] for x in perm)


def build_template_seed() -> list[dict[str, Any]]:
    """Build 96 deterministic abstract-slot rows: 72 positives + 24 adversarial negatives."""
    rows: list[dict[str, Any]] = []
    templates = tuple(TRAIN_LEXICON)
    for pidx, perm in enumerate(S3):
        mapping = dict(zip(CLASSES, perm))
        pid = _permutation_id(perm)
        for tidx, template in enumerate(templates):
            for cidx, semantic_class in enumerate(CLASSES):
                shift = (pidx + tidx + cidx) % len(CLASSES)
                order = CLASSES[shift:] + CLASSES[:shift]
                target = mapping[semantic_class]
                rows.append(
                    {
                        "schema": ROW_SCHEMA,
                        "evidence_class": "METHOD_ONLY",
                        "reality_level": "R2",
                        "family_id": f"BIND_{template}_{semantic_class}_F01",
                        "provenance_ancestry_id": f"trigger2-v4-binding-{template.lower()}-{semantic_class.lower()}",
                        "canonical_truth_allowed": False,
                        "direct_effect_authority": False,
                        "fact_status": "NOT_APPLICABLE",
                        "target_type": "DYNAMIC_CODEBOOK_BINDING_TEMPLATE",
                        "split": "TRAIN",
                        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                        "selected_using_holdout": False,
                        "prompt": _render_prompt(template, mapping, order, TRAIN_LEXICON[template][semantic_class]),
                        "target": target,
                        "semantic_class_metadata_only": semantic_class,
                        "permutation_id": pid,
                        "realized_mapping": mapping,
                        "codebook_entry_order": list(order),
                        "selected_symbol_slot": target,
                        "template_id": template,
                        "lexical_family_id": f"{template}_LEX_F01",
                        "class_word_policy": CLASS_WORD_POLICY,
                        "requires_abi_atom_resolution": True,
                        "candidate_train_ready": False,
                        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
                        "measurement_source_package_sha256": SOURCE_PACKAGE_SHA256,
                        "measurement_donor_model_id": MEASUREMENT_DONOR_MODEL,
                        "measurement_donor_snapshot": MEASUREMENT_DONOR_SNAPSHOT,
                        "jspace_label_transfer_allowed": False,
                    }
                )

            semantic_class = CLASSES[(pidx + tidx) % len(CLASSES)]
            correct = mapping[semantic_class]
            wrong = ABSTRACT_SLOTS[(ABSTRACT_SLOTS.index(correct) + 1 + (pidx % 2)) % len(ABSTRACT_SLOTS)]
            shift = (pidx + tidx + 1) % len(CLASSES)
            order = CLASSES[shift:] + CLASSES[:shift]
            rows.append(
                {
                    "schema": ROW_SCHEMA,
                    "evidence_class": "SYNTHETIC_HARD_NEGATIVE",
                    "reality_level": "R3",
                    "family_id": f"BIND_HARDNEG_{template}_{semantic_class}_F01",
                    "provenance_ancestry_id": f"trigger2-v4-binding-hardneg-{template.lower()}-{semantic_class.lower()}",
                    "canonical_truth_allowed": False,
                    "direct_effect_authority": False,
                    "fact_status": "UNKNOWN",
                    "target_type": "DYNAMIC_CODEBOOK_BINDING_HARD_NEGATIVE",
                    "split": "TRAIN",
                    "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                    "selected_using_holdout": False,
                    "prompt": _render_prompt(template, mapping, order, TRAIN_LEXICON[template][semantic_class], proposed=wrong),
                    "target": f"REJECT {wrong}; CORRECT {correct}",
                    "semantic_class_metadata_only": semantic_class,
                    "permutation_id": pid,
                    "realized_mapping": mapping,
                    "codebook_entry_order": list(order),
                    "selected_symbol_slot": correct,
                    "proposed_symbol_slot": wrong,
                    "template_id": template,
                    "lexical_family_id": f"{template}_LEX_F01",
                    "class_word_policy": CLASS_WORD_POLICY,
                    "requires_abi_atom_resolution": True,
                    "candidate_train_ready": False,
                    "abi_manifest_sha256": ABI_MANIFEST_SHA256,
                    "measurement_source_package_sha256": SOURCE_PACKAGE_SHA256,
                    "measurement_donor_model_id": MEASUREMENT_DONOR_MODEL,
                    "measurement_donor_snapshot": MEASUREMENT_DONOR_SNAPSHOT,
                    "jspace_label_transfer_allowed": False,
                }
            )
    return rows


def _class_word_leak(prompt: str) -> bool:
    start = prompt.find("<CODEBOOK>")
    end = prompt.find("</CODEBOOK>")
    if start < 0 or end < 0 or end < start:
        return True
    outside = prompt[:start] + prompt[end + len("</CODEBOOK>") :]
    return any(word in outside for word in CLASSES)


def _candidate_gate_required_fields(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    if row.get("evidence_class") not in {"METHOD_ONLY", "SYNTHETIC_HARD_NEGATIVE"}:
        failures.append("EVIDENCE_CLASS_INVALID_FOR_SYNTHETIC_SEED")
    if row.get("reality_level") not in {"R2", "R3"}:
        failures.append("REALITY_LEVEL_INVALID_FOR_SYNTHETIC_SEED")
    if not row.get("family_id"):
        failures.append("FAMILY_ID_REQUIRED")
    if not row.get("provenance_ancestry_id"):
        failures.append("PROVENANCE_ANCESTRY_ID_REQUIRED")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("CANONICAL_TRUTH_FORBIDDEN")
    if row.get("direct_effect_authority") is not False:
        failures.append("DIRECT_EFFECT_AUTHORITY_FORBIDDEN")
    if row.get("fact_status") not in {"UNKNOWN", "NOT_APPLICABLE"}:
        failures.append("SYNTHETIC_FACT_STATUS_INVALID")
    if row.get("split") not in {"TRAIN", "VALIDATION", "HOLDOUT"}:
        failures.append("SPLIT_INVALID")
    if row.get("split_unit") != "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY":
        failures.append("FAMILY_PROVENANCE_SPLIT_UNIT_REQUIRED")
    if row.get("selected_using_holdout") is not False:
        failures.append("HOLDOUT_SELECTION_FORBIDDEN")
    if not row.get("target_type"):
        failures.append("TARGET_TYPE_REQUIRED")
    return failures


def validate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    failures: list[str] = []
    positives = [r for r in rows if r.get("evidence_class") == "METHOD_ONLY"]
    negatives = [r for r in rows if r.get("evidence_class") == "SYNTHETIC_HARD_NEGATIVE"]

    if len(positives) != 72:
        failures.append(f"POSITIVE_COUNT_EXPECTED_72_GOT_{len(positives)}")
    if len(negatives) != 24:
        failures.append(f"HARD_NEGATIVE_COUNT_EXPECTED_24_GOT_{len(negatives)}")

    expected_perms = {_permutation_id(p) for p in S3}
    observed_perms = {str(r.get("permutation_id")) for r in positives}
    if observed_perms != expected_perms:
        failures.append("EXACT_S3_COVERAGE_FAIL")

    if {r.get("template_id") for r in positives} != set(TRAIN_LEXICON):
        failures.append("FOUR_TRAINING_TEMPLATE_COVERAGE_FAIL")

    pair_counts = Counter((r.get("semantic_class_metadata_only"), r.get("selected_symbol_slot")) for r in positives)
    if set(pair_counts.values()) != {8} or len(pair_counts) != 9:
        failures.append("EXACT_CLASS_SYMBOL_COUNTERBALANCE_FAIL")

    n = len(positives)
    class_counts = Counter(r.get("semantic_class_metadata_only") for r in positives)
    slot_counts = Counter(r.get("selected_symbol_slot") for r in positives)
    mi_bits = 0.0
    if n:
        for (c, s), count in pair_counts.items():
            pxy = count / n
            px = class_counts[c] / n
            py = slot_counts[s] / n
            mi_bits += pxy * math.log2(pxy / (px * py))
    if abs(mi_bits) > 1e-12:
        failures.append("CLASS_SYMBOL_MUTUAL_INFORMATION_NONZERO")

    family_splits: dict[str, set[str]] = defaultdict(set)
    ancestry_splits: dict[str, set[str]] = defaultdict(set)
    entry_orders: set[tuple[str, ...]] = set()

    for idx, row in enumerate(rows):
        for f in _candidate_gate_required_fields(row):
            failures.append(f"ROW_{idx}:{f}")

        cls = row.get("semantic_class_metadata_only")
        mapping = row.get("realized_mapping")
        selected = row.get("selected_symbol_slot")
        if not isinstance(mapping, dict) or cls not in mapping or mapping.get(cls) != selected:
            failures.append(f"ROW_{idx}:REALIZED_MAPPING_TARGET_MISMATCH")
        if row.get("evidence_class") == "METHOD_ONLY" and row.get("target") != selected:
            failures.append(f"ROW_{idx}:POSITIVE_TARGET_NOT_REALIZED_SYMBOL")
        if row.get("evidence_class") == "SYNTHETIC_HARD_NEGATIVE":
            if row.get("proposed_symbol_slot") == selected:
                failures.append(f"ROW_{idx}:HARD_NEGATIVE_PROPOSAL_IS_CORRECT")
            expected = f"REJECT {row.get('proposed_symbol_slot')}; CORRECT {selected}"
            if row.get("target") != expected:
                failures.append(f"ROW_{idx}:HARD_NEGATIVE_TARGET_MISMATCH")

        if _class_word_leak(str(row.get("prompt", ""))):
            failures.append(f"ROW_{idx}:CLASS_WORD_LEAK_OUTSIDE_CODEBOOK")
        if any(word in str(row.get("target", "")) for word in CLASSES):
            failures.append(f"ROW_{idx}:CLASS_WORD_LEAK_IN_TARGET")

        if row.get("requires_abi_atom_resolution") is not True or row.get("candidate_train_ready") is not False:
            failures.append(f"ROW_{idx}:ABI_RESOLUTION_FAIL_CLOSED_GUARD")
        if row.get("jspace_label_transfer_allowed") is not False:
            failures.append(f"ROW_{idx}:CROSS_MODEL_JSPACE_TRANSFER_MUST_BE_FALSE")

        order = tuple(row.get("codebook_entry_order") or [])
        if set(order) != set(CLASSES) or len(order) != 3:
            failures.append(f"ROW_{idx}:CODEBOOK_ORDER_INVALID")
        entry_orders.add(order)

        family_splits[str(row.get("lexical_family_id"))].add(str(row.get("split")))
        ancestry_splits[str(row.get("provenance_ancestry_id"))].add(str(row.get("split")))

    if any(len(splits) > 1 for splits in family_splits.values()):
        failures.append("LEXICAL_FAMILY_CROSSES_SPLITS")
    if any(len(splits) > 1 for splits in ancestry_splits.values()):
        failures.append("PROVENANCE_ANCESTRY_CROSSES_SPLITS")

    if len(entry_orders) < 3:
        failures.append("CODEBOOK_ENTRY_ORDER_VARIATION_INSUFFICIENT")

    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "rows": len(rows),
        "positive_rows": len(positives),
        "hard_negative_rows": len(negatives),
        "s3_permutations": len(observed_perms),
        "training_templates": sorted({str(r.get('template_id')) for r in positives}),
        "reserved_unopened_template_family": RESERVED_UNOPENED_TEMPLATE_FAMILY,
        "distinct_codebook_entry_orders": len(entry_orders),
        "class_symbol_pair_counts": {f"{c}->{s}": pair_counts[(c, s)] for c in CLASSES for s in ABSTRACT_SLOTS},
        "class_symbol_mutual_information_bits": mi_bits,
        "class_word_leak_count": sum(1 for x in failures if "CLASS_WORD_LEAK" in x),
        "all_rows_require_abi_atom_resolution": all(r.get("requires_abi_atom_resolution") is True for r in rows),
        "all_rows_candidate_train_ready_false": all(r.get("candidate_train_ready") is False for r in rows),
        "failures": sorted(set(failures)),
        "credit_boundary": "SYNTHETIC_TEMPLATE_SOURCE_ONLY; no canonical dataset, accepted-token, model-runtime, J-Space, training, HCU, or EntityOS credit.",
        "next_gate": "Resolve abstract slots against verified accepted ABI atoms and exact tokenizer single-token identity; then generate split-isolated train/validation/frozen-holdout corpus without opening holdout during tuning.",
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> str:
    payload = "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows) + "\n"
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True, help="Output JSONL path for the abstract-slot seed")
    ap.add_argument("--audit", type=Path, required=True, help="Output audit JSON path")
    args = ap.parse_args()

    rows = build_template_seed()
    audit = validate_rows(rows)
    audit["dataset_sha256"] = write_jsonl(args.output, rows)
    audit["generator_mode"] = "ABSTRACT_SLOT_TEMPLATE_ONLY"
    audit["class_word_policy"] = CLASS_WORD_POLICY
    audit["abi_manifest_sha256"] = ABI_MANIFEST_SHA256
    audit["measurement_source_package_sha256"] = SOURCE_PACKAGE_SHA256
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
