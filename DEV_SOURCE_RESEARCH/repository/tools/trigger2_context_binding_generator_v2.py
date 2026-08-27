#!/usr/bin/env python3
"""Trigger-2 context-binding generator v2.

METHOD_ONLY / source blueprint. No verified ABI atom is materialized here and no row is
training-eligible. The design forces content-dependent semantic -> episode-local codebook
routing while fully crossing the principal visible nuisance factors.

v2 repairs retained-v1 failures:
- display order is a fully crossed nuisance factor, never row-index scheduled;
- query polarity is defined as proposition vs exact negation over SUPPORTS/CONTRADICTS/UNKNOWN;
- built-in semantic content is TRAIN-only; validation/holdout content is reserved but unmaterialized;
- every nuisance-only signature leaves all three semantic classes and target slots possible.
"""
from __future__ import annotations

import collections
import hashlib
import itertools
import json
import re
from typing import Any, Iterable

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
GENERATOR_SCHEMA = "CLAY_TRIGGER2_CONTEXT_BINDING_GENERATOR/v2"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
STATES = ("SUPPORTS", "CONTRADICTS", "UNKNOWN")
POLARITIES = ("DIRECT", "INVERTED")
SLOTS = ("<ABI_SLOT_0>", "<ABI_SLOT_1>", "<ABI_SLOT_2>")
S3 = tuple(itertools.permutations(range(3)))
DISPLAY_ORDERS = tuple(itertools.permutations(CLASSES))
SOURCE_INGEST = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json"
SOURCE_PACKAGE_SHA256 = "a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c"
V1_REJECTION = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_RETAINED_CONTEXT_GENERATOR_ADVERSARIAL_AUDIT_V2_GPT56SOL.json"

TRAIN_BANK: dict[str, dict[str, Any]] = {
    "T1_DIGEST": {
        "proposition": "the recomputed digest matches the recorded digest",
        "SUPPORTS": (
            "Recorded digest: 7f3a. Recomputed digest: 7f3a.",
            "Manifest digest: c420. Fresh digest: c420.",
            "Expected checksum: 91be. Observed checksum: 91be.",
        ),
        "CONTRADICTS": (
            "Recorded digest: 7f3a. Recomputed digest: 91c2.",
            "Manifest digest: c420. Fresh digest: c421.",
            "Expected checksum: 91be. Observed checksum: 91bf.",
        ),
        "UNKNOWN": (
            "Recorded digest: 7f3a. No recomputed digest is available.",
            "Manifest digest: c420. The fresh digest was not observed.",
            "Expected checksum: 91be. The observed checksum is unavailable.",
        ),
    },
    "T2_LEASE": {
        "proposition": "the coordinator lease is current for this job",
        "SUPPORTS": (
            "Lease scope: job-17. Current job: job-17. Expiry tick: 480. Current tick: 450.",
            "Lease scope: branch-k. Active branch: branch-k. Expiry tick: 910. Current tick: 874.",
            "Lease task: task-3. Active task: task-3. Expiry tick: 65. Current tick: 41.",
        ),
        "CONTRADICTS": (
            "Lease scope: job-17. Current job: job-17. Expiry tick: 420. Current tick: 450.",
            "Lease scope: branch-k. Active branch: branch-z. Expiry tick: 910. Current tick: 874.",
            "Lease task: task-3. Active task: task-3. Expiry tick: 40. Current tick: 41.",
        ),
        "UNKNOWN": (
            "Lease scope: job-17. Current job: job-17. Expiry tick is unavailable. Current tick: 450.",
            "Lease scope is unavailable. Active branch: branch-k. Expiry tick: 910. Current tick: 874.",
            "Lease task: task-3. Active task is unavailable. Expiry tick: 65. Current tick: 41.",
        ),
    },
    "T3_CAUSAL_ID": {
        "proposition": "the packet and ledger refer to the same causal event",
        "SUPPORTS": (
            "Packet causal event id: e-17. Ledger causal event id: e-17.",
            "Packet event key: q-44. Ledger event key: q-44.",
            "Packet causal key: c-8. Ledger causal key: c-8.",
        ),
        "CONTRADICTS": (
            "Packet causal event id: e-17. Ledger causal event id: e-93.",
            "Packet event key: q-44. Ledger event key: q-45.",
            "Packet causal key: c-8. Ledger causal key: c-2.",
        ),
        "UNKNOWN": (
            "Packet causal event id: e-17. Ledger causal event id is unavailable.",
            "Packet event key: q-44. Ledger event key is unavailable.",
            "Packet causal key is unavailable. Ledger causal key: c-8.",
        ),
    },
    "T4_EPOCH": {
        "proposition": "the result was produced against the current state epoch",
        "SUPPORTS": (
            "Result state epoch: 12. Current state epoch: 12.",
            "Result generation epoch: 31. Active generation epoch: 31.",
            "Result workspace epoch: 7. Current workspace epoch: 7.",
        ),
        "CONTRADICTS": (
            "Result state epoch: 11. Current state epoch: 12.",
            "Result generation epoch: 30. Active generation epoch: 31.",
            "Result workspace epoch: 6. Current workspace epoch: 7.",
        ),
        "UNKNOWN": (
            "Result state epoch is unavailable. Current state epoch: 12.",
            "Result generation epoch is unavailable. Active generation epoch: 31.",
            "Result workspace epoch is unavailable. Current workspace epoch: 7.",
        ),
    },
}

RESERVED_UNMATERIALIZED = {
    "VALIDATION": "T5_RELATIONAL_FAMILY_RESERVED_FOR_POST_FREEZE_MATERIALIZATION",
    "HOLDOUT": "T6_NOVEL_CLAYCODE_FAMILY_RESERVED_FOR_SEALED_POST_FREEZE_MATERIALIZATION",
}


def target_class(state: str, polarity: str) -> str:
    if state == "UNKNOWN":
        return "ABSTAIN"
    direct = "ALLOW" if state == "SUPPORTS" else "DENY"
    if polarity == "DIRECT":
        return direct
    if polarity == "INVERTED":
        return "DENY" if direct == "ALLOW" else "ALLOW"
    raise ValueError(polarity)


def mapping_from_perm(perm: tuple[int, int, int]) -> dict[str, str]:
    return {CLASSES[i]: SLOTS[perm[i]] for i in range(3)}


def _codebook(mapping: dict[str, str], order: tuple[str, str, str]) -> str:
    return "\n".join(["CODEBOOK", *(f"{c} -> {mapping[c]}" for c in order), "END_CODEBOOK"])


def _render_prompt(proposition: str, evidence: str, polarity: str, mapping: dict[str, str], order: tuple[str, str, str]) -> str:
    focus = "the proposition" if polarity == "DIRECT" else "the negation of the proposition"
    return (
        _codebook(mapping, order)
        + "\nEVIDENCE\n" + evidence
        + "\nPROPOSITION\n" + proposition
        + f"\nQUERY\nDoes the evidence support {focus}?"
        + "\nResolve the semantic status first, then use only the current episode codebook. Output exactly one mapped symbol and nothing else."
    )


def generate_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for template_id, spec in TRAIN_BANK.items():
        proposition = spec["proposition"]
        family_id = f"CTX_BIND_V2_{template_id}_F01"
        ancestry = f"trigger2-v2-factorial:{template_id.lower()}"
        for state in STATES:
            for lexical_variant_index, evidence in enumerate(spec[state]):
                scenario_id = f"{template_id}:{state}:L{lexical_variant_index}"
                for polarity in POLARITIES:
                    semantic = target_class(state, polarity)
                    for pidx, perm in enumerate(S3):
                        mapping = mapping_from_perm(perm)
                        target = mapping[semantic]
                        for oidx, order in enumerate(DISPLAY_ORDERS):
                            row = {
                                "schema": ROW_SCHEMA,
                                "evidence_class": "METHOD_ONLY",
                                "reality_level": "R2",
                                "family_id": family_id,
                                "provenance_ancestry_id": ancestry,
                                "canonical_truth_allowed": False,
                                "direct_effect_authority": False,
                                "fact_status": "NOT_APPLICABLE",
                                "target_type": "CONTEXT_DEPENDENT_CODEBOOK_BINDING_BLUEPRINT_V2",
                                "split": "TRAIN",
                                "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                                "selected_using_holdout": False,
                                "training_eligible": False,
                                "model_visible_fields": ["prompt"],
                                "supervision_field": "target",
                                "audit_metadata_must_not_enter_model_context": True,
                                "render_status": "VERIFIED_ABI_ATOM_AND_FINAL_TOKENIZER_BINDING_REQUIRED",
                                "source_evidence_ingest": SOURCE_INGEST,
                                "source_package_sha256": SOURCE_PACKAGE_SHA256,
                                "v1_rejection": V1_REJECTION,
                                "template_id": template_id,
                                "scenario_id": scenario_id,
                                "semantic_evidence_state": state,
                                "lexical_variant_index": lexical_variant_index,
                                "query_polarity": polarity,
                                "s3_permutation_id": f"P{pidx}",
                                "s3_permutation": list(perm),
                                "display_order_id": f"O{oidx}",
                                "display_order": list(order),
                                "realized_mapping": mapping,
                                "audit_target_semantic_class": semantic,
                                "audit_target_semantic_class_visibility": "EXCLUDED_FROM_MODEL_INPUT",
                                "prompt": _render_prompt(proposition, evidence, polarity, mapping, order),
                                "target": target,
                            }
                            material = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                            row["row_sha256"] = hashlib.sha256(material.encode()).hexdigest()
                            out.append(row)
    return out


def _outside_codebook(prompt: str) -> str:
    return re.sub(r"CODEBOOK\n.*?\nEND_CODEBOOK", "", prompt, count=1, flags=re.DOTALL)


def validate_rows(materialized: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rr = list(materialized)
    failures: list[str] = []
    expected = 4 * 3 * 3 * 2 * 6 * 6
    if len(rr) != expected:
        failures.append(f"ROW_COUNT:{len(rr)}!={expected}")

    seen = set()
    nuisance_classes: dict[tuple[Any, ...], set[str]] = collections.defaultdict(set)
    nuisance_targets: dict[tuple[Any, ...], set[str]] = collections.defaultdict(set)
    display_counterfactuals: dict[tuple[Any, ...], set[str]] = collections.defaultdict(set)
    mapping_counterfactuals: dict[tuple[Any, ...], set[str]] = collections.defaultdict(set)
    template_counts = collections.Counter()
    state_counts = collections.Counter()
    variant_counts = collections.Counter()
    polarity_counts = collections.Counter()
    class_counts = collections.Counter()
    target_counts = collections.Counter()
    order_counts = collections.Counter()
    mapping_counts = collections.Counter()

    for i, row in enumerate(rr):
        key = (row["scenario_id"], row["query_polarity"], row["s3_permutation_id"], row["display_order_id"])
        if key in seen:
            failures.append(f"DUPLICATE_FACTORIAL_CELL:{i}")
        seen.add(key)
        perm = tuple(row["s3_permutation"])
        if perm not in S3:
            failures.append(f"INVALID_S3:{i}")
            continue
        mapping = mapping_from_perm(perm)
        if mapping != row["realized_mapping"]:
            failures.append(f"MAPPING_NOT_CAUSAL:{i}")
        semantic = target_class(row["semantic_evidence_state"], row["query_polarity"])
        if semantic != row["audit_target_semantic_class"]:
            failures.append(f"SEMANTIC_POLARITY_MISMATCH:{i}")
        if row["target"] != mapping[semantic]:
            failures.append(f"TARGET_NOT_FROM_MAPPING:{i}")
        outside = _outside_codebook(row["prompt"])
        if any(re.search(rf"\b{c}\b", outside, flags=re.I) for c in CLASSES):
            failures.append(f"CLASS_LABEL_LEAK:{i}")
        if any(slot in outside for slot in SLOTS):
            failures.append(f"SYMBOL_SLOT_LEAK:{i}")
        if row.get("split") != "TRAIN":
            failures.append(f"NONTRAIN_MATERIALIZED:{i}")
        if row.get("training_eligible") is not False:
            failures.append(f"TRAINING_ELIGIBILITY_NOT_FALSE:{i}")
        if row.get("model_visible_fields") != ["prompt"] or row.get("supervision_field") != "target":
            failures.append(f"MODEL_VISIBLE_PROJECTION_INVALID:{i}")

        nuisance = (row["template_id"], row["lexical_variant_index"], row["query_polarity"], row["s3_permutation_id"], row["display_order_id"])
        nuisance_classes[nuisance].add(semantic)
        nuisance_targets[nuisance].add(row["target"])
        display_key = (row["scenario_id"], row["query_polarity"], row["s3_permutation_id"])
        display_counterfactuals[display_key].add(row["display_order_id"])
        mapping_key = (row["scenario_id"], row["query_polarity"], row["display_order_id"])
        mapping_counterfactuals[mapping_key].add(row["s3_permutation_id"])

        template_counts[row["template_id"]] += 1
        state_counts[row["semantic_evidence_state"]] += 1
        variant_counts[row["lexical_variant_index"]] += 1
        polarity_counts[row["query_polarity"]] += 1
        class_counts[semantic] += 1
        target_counts[row["target"]] += 1
        order_counts[row["display_order_id"]] += 1
        mapping_counts[row["s3_permutation_id"]] += 1

    if any(v != set(CLASSES) for v in nuisance_classes.values()):
        failures.append("NUISANCE_SIGNATURE_PREDICTS_SEMANTIC_CLASS")
    if any(v != set(SLOTS) for v in nuisance_targets.values()):
        failures.append("NUISANCE_SIGNATURE_PREDICTS_TARGET_SLOT")
    if any(len(v) != 6 for v in display_counterfactuals.values()):
        failures.append("DISPLAY_ORDER_NOT_FULLY_CROSSED_PER_FIXED_SCENARIO_MAPPING")
    if any(len(v) != 6 for v in mapping_counterfactuals.values()):
        failures.append("S3_MAPPING_NOT_FULLY_CROSSED_PER_FIXED_SCENARIO_ORDER")

    expected_uniform = {
        "template": (template_counts, 648),
        "state": (state_counts, 864),
        "variant": (variant_counts, 864),
        "polarity": (polarity_counts, 1296),
        "semantic_class": (class_counts, 864),
        "target_slot": (target_counts, 864),
        "display_order": (order_counts, 432),
        "s3_mapping": (mapping_counts, 432),
    }
    for name, (counter, cell) in expected_uniform.items():
        if not counter or any(v != cell for v in counter.values()):
            failures.append(f"BALANCE_{name.upper()}:{dict(counter)}")

    return {
        "schema": "CLAY_TRIGGER2_CONTEXT_BINDING_GENERATOR_AUDIT/v2",
        "pass": not failures,
        "failures": sorted(set(failures)),
        "rows_total": len(rr),
        "factorization": "4 templates * 3 evidence states * 3 lexical variants * 2 query polarities * 6 S3 mappings * 6 display orders = 2592 TRAIN blueprint rows",
        "nuisance_signatures": len(nuisance_classes),
        "nuisance_semantic_class_support": "ALL_THREE_CLASSES_PER_SIGNATURE" if nuisance_classes and all(v == set(CLASSES) for v in nuisance_classes.values()) else "FAIL",
        "nuisance_target_slot_support": "ALL_THREE_SLOTS_PER_SIGNATURE" if nuisance_targets and all(v == set(SLOTS) for v in nuisance_targets.values()) else "FAIL",
        "display_order_counterfactuals": "FULL_6_PER_FIXED_SCENARIO_POLARITY_MAPPING" if display_counterfactuals and all(len(v) == 6 for v in display_counterfactuals.values()) else "FAIL",
        "mapping_counterfactuals": "FULL_6_PER_FIXED_SCENARIO_POLARITY_ORDER" if mapping_counterfactuals and all(len(v) == 6 for v in mapping_counterfactuals.values()) else "FAIL",
        "reserved_unmaterialized": RESERVED_UNMATERIALIZED,
        "training_eligible": False,
        "accepted_dataset_tokens": 0,
        "training_credit": 0,
        "remaining_gates": [
            "exact verified 46-atom ABI materialization with rejected atom 'or' excluded",
            "frozen selected Qwen3.5-0.8B checkpoint/tokenizer identity and tokenizer recomputation",
            "disjoint TRAIN/VALIDATION/HOLDOUT atom pools",
            "separate split-isolated lexical families and sealed holdout materialization",
            "candidate gate + family/provenance split linter + model-visible projection test",
            "matched pilot/retention evaluation before full-FT"
        ],
    }


def main() -> int:
    report = validate_rows(generate_rows())
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
