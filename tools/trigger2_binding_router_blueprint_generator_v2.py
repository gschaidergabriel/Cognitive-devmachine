#!/usr/bin/env python3
"""Generate Trigger-2 dynamic-codebook binding blueprint v2.1.

Synthetic METHOD_ONLY candidates only. This successor fully crosses semantic class,
S3 mapping and all six model-visible codebook display orders so display order is an
independent nuisance variable at the logical-alias scope.

Placeholders MUST be rebound to verified accepted ABI atoms and tokenizer checked
before any training eligibility or canonical dataset credit.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
from pathlib import Path

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
DISPLAY_ORDERS = tuple(itertools.permutations(CLASSES))
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
SOURCE_INGEST = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json"
LEAK_REVIEW = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_SECOND_ORDER_DISPLAY_ORDER_LEAK_REVIEW_V1_GPT56SOL.json"

TEMPLATES = {
    "TRAIN_T1_CHECK_MATRIX": (
        "TRAIN",
        ("<ABI_TR_T1_A>", "<ABI_TR_T1_B>", "<ABI_TR_T1_C>"),
        {
            "ALLOW": "Check matrix: required_1=true; required_2=true; conflict_count=0; missing_count=0.",
            "DENY": "Check matrix: required_1=true; required_2=false; conflict_count=1; missing_count=0.",
            "ABSTAIN": "Check matrix: required_1=true; required_2=unknown; conflict_count=0; missing_count=1.",
        },
    ),
    "TRAIN_T2_EVIDENCE_LEDGER": (
        "TRAIN",
        ("<ABI_TR_T2_A>", "<ABI_TR_T2_B>", "<ABI_TR_T2_C>"),
        {
            "ALLOW": "Evidence ledger: every mandatory clause has a confirming record; contradictions=0; unresolved_records=0.",
            "DENY": "Evidence ledger: one mandatory clause has a falsifying record; contradictions=1; unresolved_records=0.",
            "ABSTAIN": "Evidence ledger: one mandatory clause lacks an observation; contradictions=0; unresolved_records=1.",
        },
    ),
    "TRAIN_T3_SENSOR_REPORT": (
        "TRAIN",
        ("<ABI_TR_T3_A>", "<ABI_TR_T3_B>", "<ABI_TR_T3_C>"),
        {
            "ALLOW": "Sensor report: gate_alpha=1; gate_beta=1; anomaly=0; unread_channel=0.",
            "DENY": "Sensor report: gate_alpha=1; gate_beta=0; anomaly=1; unread_channel=0.",
            "ABSTAIN": "Sensor report: gate_alpha=1; gate_beta=?; anomaly=0; unread_channel=1.",
        },
    ),
    "TRAIN_T4_NESTED_STATE": (
        "TRAIN",
        ("<ABI_TR_T4_A>", "<ABI_TR_T4_B>", "<ABI_TR_T4_C>"),
        {
            "ALLOW": 'State object: {"must":{"x":1,"y":1},"faults":[],"unknown":[]}.',
            "DENY": 'State object: {"must":{"x":1,"y":0},"faults":["y"],"unknown":[]}.',
            "ABSTAIN": 'State object: {"must":{"x":1,"y":null},"faults":[],"unknown":["y"]}.',
        },
    ),
    "VALIDATION_T5_DIALOGUE": (
        "VALIDATION",
        ("<ABI_VA_T5_A>", "<ABI_VA_T5_B>", "<ABI_VA_T5_C>"),
        {
            "ALLOW": "Witness dialogue: first witness confirms criterion p; second witness confirms criterion q; no discrepancy is recorded.",
            "DENY": "Witness dialogue: first witness confirms criterion p; second witness contradicts criterion q; one discrepancy is recorded.",
            "ABSTAIN": "Witness dialogue: first witness confirms criterion p; no observation exists for criterion q; the record is incomplete.",
        },
    ),
    "HOLDOUT_T6_CLAYCODE": (
        "HOLDOUT",
        ("<ABI_HO_T6_A>", "<ABI_HO_T6_B>", "<ABI_HO_T6_C>"),
        {
            "ALLOW": "obs{req.a=1;req.b=1;viol=0;unk=0}",
            "DENY": "obs{req.a=1;req.b=0;viol=1;unk=0}",
            "ABSTAIN": "obs{req.a=1;req.b=?;viol=0;unk=1}",
        },
    ),
}


def rows():
    """Yield the fully crossed logical blueprint.

    Per template: 3 semantic classes x 6 S3 mappings x 6 display orders = 108.
    Train: 4 x 108 = 432; validation: 108; holdout: 108; total: 648.
    """
    for tid, (split, pool, scenes) in TEMPLATES.items():
        # Keep all mapping/semantic/order counterfactuals in one causal family per
        # template so a future family-level splitter cannot separate paired variants.
        family = f"BIND_{tid}_F02"
        ancestry = f"trigger2-v2-1-binding-{tid.lower()}"
        for semantic_class in CLASSES:
            for pid, perm in enumerate(itertools.permutations(range(3))):
                mapping = {cls: pool[perm[i]] for i, cls in enumerate(CLASSES)}
                target = mapping[semantic_class]
                for oid, display_order in enumerate(DISPLAY_ORDERS):
                    codebook = "\n".join(f"{cls} -> {mapping[cls]}" for cls in display_order)
                    target_position = display_order.index(semantic_class)
                    prompt = (
                        "CODEBOOK\n"
                        + codebook
                        + "\nEND_CODEBOOK\n"
                        + f"SCENE\n{scenes[semantic_class]}\nEND_SCENE\n"
                        + "Return only the atom selected by the episode-local codebook."
                    )
                    yield {
                        "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
                        "evidence_class": "METHOD_ONLY",
                        "reality_level": "R2",
                        "family_id": family,
                        "provenance_ancestry_id": ancestry,
                        "canonical_truth_allowed": False,
                        "direct_effect_authority": False,
                        "fact_status": "NOT_APPLICABLE",
                        "target_type": "DYNAMIC_CODEBOOK_BINDING_BLUEPRINT",
                        "split": split,
                        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                        "selected_using_holdout": False,
                        "training_eligible": False,
                        "render_status": "ABI_ATOM_RENDER_REQUIRED",
                        "class_label_visibility_rule": "CLASS_LABELS_ALLOWED_ONLY_INSIDE_CODEBOOK",
                        "template_id": tid,
                        "s3_permutation_id": f"P{pid}",
                        "display_order_id": f"O{oid}",
                        "display_order": list(display_order),
                        "target_display_position": target_position,
                        "realized_mapping": mapping,
                        "audit_semantic_class": semantic_class,
                        "audit_semantic_class_visibility": "EXCLUDED_FROM_MODEL_INPUT",
                        "target_atom_placeholder": target,
                        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
                        "source_evidence_ingest": SOURCE_INGEST,
                        "second_order_leak_review": LEAK_REVIEW,
                        "prompt": prompt,
                        "target": target,
                    }


def _require_constant(counter: collections.Counter, expected: int, label: str) -> None:
    if not counter or any(v != expected for v in counter.values()):
        raise AssertionError(f"{label}: expected every observed cell={expected}, got {dict(counter)}")


def validate(materialized: list[dict]) -> dict:
    """Exact combinatorial shortcut checks at logical-alias scope.

    These checks prove balance of the generated design only. They do NOT grant
    tokenizer/ABI/model/training/J-Space/runtime credit.
    """
    expected_split = {"TRAIN": 432, "VALIDATION": 108, "HOLDOUT": 108}
    split_counts = collections.Counter(row["split"] for row in materialized)
    if dict(split_counts) != expected_split:
        raise AssertionError(f"split counts {dict(split_counts)} != {expected_split}")
    if len(materialized) != 648:
        raise AssertionError(f"expected 648 total rows, got {len(materialized)}")

    seen = set()
    for row in materialized:
        key = (
            row["template_id"],
            row["audit_semantic_class"],
            row["s3_permutation_id"],
            row["display_order_id"],
        )
        if key in seen:
            raise AssertionError(f"duplicate factorial cell: {key}")
        seen.add(key)
        if row["target"] != row["realized_mapping"][row["audit_semantic_class"]]:
            raise AssertionError(f"target derivation mismatch: {key}")

    for tid in TEMPLATES:
        block = [r for r in materialized if r["template_id"] == tid]
        if len(block) != 108:
            raise AssertionError(f"{tid}: expected 108 rows, got {len(block)}")

        # Each (semantic class, display order, target atom) cell occurs twice:
        # the six S3 mappings route a fixed class to each of three atoms twice.
        by_class_order_target = collections.Counter(
            (r["audit_semantic_class"], r["display_order_id"], r["target"])
            for r in block
        )
        _require_constant(by_class_order_target, 2, f"{tid}: class/order/target")

        # Unconditional target x full display-order independence: each target atom
        # appears six times under each of the six full display orders.
        by_order_target = collections.Counter(
            (r["display_order_id"], r["target"]) for r in block
        )
        _require_constant(by_order_target, 6, f"{tid}: order/target")

        # Target atom x target-line position is exactly uniform: 3 x 3 cells,
        # 12 occurrences each in the 108-row template block.
        by_target_position = collections.Counter(
            (r["target"], r["target_display_position"]) for r in block
        )
        _require_constant(by_target_position, 12, f"{tid}: target/position")

        # The same position independence must hold conditional on semantic class:
        # 3 target atoms x 3 positions, four occurrences each per class.
        for semantic_class in CLASSES:
            conditional = collections.Counter(
                (r["target"], r["target_display_position"])
                for r in block
                if r["audit_semantic_class"] == semantic_class
            )
            _require_constant(conditional, 4, f"{tid}/{semantic_class}: target/position")

    return {
        "status": "PASS_LOGICAL_BLUEPRINT_ONLY",
        "rows": 648,
        "split_counts": expected_split,
        "train_rows": 432,
        "display_orders_per_factorial_episode": 6,
        "target_vs_display_order_leakage": "ZERO_BY_EXACT_FULL_CROSSING_AT_LOGICAL_ALIAS_SCOPE",
        "training_eligible": False,
        "remaining_gate": "VERIFIED_ABI_ATOM_RENDER_PLUS_EXACT_TOKENIZER_MODEL_PROVENANCE",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()

    materialized = list(rows())
    receipt = validate(materialized)
    text = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in materialized) + "\n"
    args.output.write_text(text, encoding="utf-8")
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
