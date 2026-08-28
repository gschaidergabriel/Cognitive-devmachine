#!/usr/bin/env python3
"""Generate Trigger-2 dynamic-codebook binding blueprint v2.2.

Synthetic METHOD_ONLY candidates only.

v2.2 extends the retained v2.1 binding lane with independently factorized proof
topology, real query polarity, and counterfactual-twin/source-leak gates:

  DIRECT_MATCH
  ONE_HOP_DEREFERENCE
  TWO_HOP_DEREFERENCE

Per template the generator fully crosses:
  3 base semantic states
  x 6 S3 class->atom mappings
  x 6 model-visible codebook display orders
  x 2 query polarities
  x 3 proof topologies
  x 3 focus-record positions
  = 1,944 rows.

Across 4 TRAIN + 1 VALIDATION + 1 HOLDOUT templates:
  11,664 METHOD_ONLY rows.

Placeholders MUST be rebound to verified accepted single-token atoms from the
measured Claude XENO ABI package and tokenizer checked before any training
eligibility or canonical dataset credit.

This source design does not mint runtime, J-Space, HCU, EntityOS, training, or
canonical-truth credit.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import math
from pathlib import Path

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
DISPLAY_ORDERS = tuple(itertools.permutations(CLASSES))
QUERY_POLARITIES = ("DIRECT", "INVERTED")
PROOF_TOPOLOGIES = (
    "DIRECT_MATCH",
    "ONE_HOP_DEREFERENCE",
    "TWO_HOP_DEREFERENCE",
)
FOCUS_POSITIONS = (0, 1, 2)

ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
SOURCE_INGEST = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json"
LEAK_REVIEW = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_SECOND_ORDER_DISPLAY_ORDER_LEAK_REVIEW_V1_GPT56SOL.json"
PROOF_TOPOLOGY_REVIEW = "research_entity/global/j-space/research/2026-08-25_TRIGGER2_LATEST_RESEARCH_FEEDBACK_V2_GPT56SOL.json"

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

POLARITY_TARGET = {
    "DIRECT": {"ALLOW": "ALLOW", "DENY": "DENY", "ABSTAIN": "ABSTAIN"},
    "INVERTED": {"ALLOW": "DENY", "DENY": "ALLOW", "ABSTAIN": "ABSTAIN"},
}

POLARITY_QUERY = {
    "DIRECT": "Does the focused evidence support proceeding under the stated rule?",
    "INVERTED": "Does the focused evidence support stopping under the stated rule?",
}


def _scene_bank(scenes: dict[str, str], base_class: str, focus_position: int, order_flip: int):
    """Place all three semantic scenes into the model input.

    The focused semantic class is fully crossed across R1/R2/R3. The two
    non-focused scenes occupy the remaining records, with their order toggled
    by an independent schedule. Thus proof topology cannot be solved by a
    fixed record position or by presence/absence of one lexical family.
    """
    records = [None, None, None]
    records[focus_position] = base_class
    others = [c for c in CLASSES if c != base_class]
    if order_flip:
        others.reverse()
    remaining = [i for i in FOCUS_POSITIONS if i != focus_position]
    for pos, cls in zip(remaining, others):
        records[pos] = cls
    rendered = "\n".join(f"R{i+1}: {scenes[records[i]]}" for i in FOCUS_POSITIONS)
    return records, rendered


def _topology_prefix(topology: str, focus_position: int) -> str:
    r = f"R{focus_position + 1}"
    if topology == "DIRECT_MATCH":
        return f"FOCUS_RECORD={r}"
    if topology == "ONE_HOP_DEREFERENCE":
        return f"FOCUS_KEY=K0\nK0 -> {r}"
    if topology == "TWO_HOP_DEREFERENCE":
        n = f"N{focus_position + 1}"
        distractor_nodes = [f"N{i+1} -> R{((i + 1) % 3) + 1}" for i in FOCUS_POSITIONS if i != focus_position]
        return "\n".join(
            [f"FOCUS_KEY=K0", f"K0 -> {n}", f"{n} -> {r}", *distractor_nodes]
        )
    raise AssertionError(topology)


def rows():
    """Yield fully crossed proof-topology binding candidates."""
    for tid, (split, pool, scenes) in TEMPLATES.items():
        family = f"BIND_{tid}_F03"
        ancestry = f"trigger2-v2-2-binding-{tid.lower()}"
        for base_class in CLASSES:
            for pid, perm in enumerate(itertools.permutations(range(3))):
                mapping = {cls: pool[perm[i]] for i, cls in enumerate(CLASSES)}
                for oid, display_order in enumerate(DISPLAY_ORDERS):
                    codebook = "\n".join(f"{cls} -> {mapping[cls]}" for cls in display_order)
                    for qid, polarity in enumerate(QUERY_POLARITIES):
                        answer_class = POLARITY_TARGET[polarity][base_class]
                        target = mapping[answer_class]
                        target_position = display_order.index(answer_class)
                        for xid, topology in enumerate(PROOF_TOPOLOGIES):
                            for focus_position in FOCUS_POSITIONS:
                                order_flip = (pid + oid + qid + xid + focus_position) & 1
                                record_classes, scene_bank = _scene_bank(
                                    scenes, base_class, focus_position, order_flip
                                )
                                proof = _topology_prefix(topology, focus_position)
                                prompt = (
                                    "CODEBOOK\n"
                                    + codebook
                                    + "\nEND_CODEBOOK\n"
                                    + "PROOF\n"
                                    + proof
                                    + "\n"
                                    + scene_bank
                                    + "\nEND_PROOF\n"
                                    + "QUERY\n"
                                    + POLARITY_QUERY[polarity]
                                    + "\nEND_QUERY\n"
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
                                    "target_type": "DYNAMIC_CODEBOOK_PROOF_TOPOLOGY_BINDING_BLUEPRINT",
                                    "split": split,
                                    "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
                                    "selected_using_holdout": False,
                                    "training_eligible": False,
                                    "render_status": "ABI_ATOM_RENDER_REQUIRED",
                                    "class_label_visibility_rule": "CLASS_LABELS_ALLOWED_ONLY_INSIDE_CODEBOOK",
                                    "template_id": tid,
                                    "base_state_class": base_class,
                                    "base_state_class_visibility": "EXCLUDED_FROM_MODEL_INPUT",
                                    "query_polarity": polarity,
                                    "proof_topology": topology,
                                    "focus_record_position": focus_position,
                                    "record_class_schedule": record_classes,
                                    "record_class_schedule_visibility": "EXCLUDED_FROM_MODEL_INPUT",
                                    "distractor_order_flip": order_flip,
                                    "s3_permutation_id": f"P{pid}",
                                    "display_order_id": f"O{oid}",
                                    "display_order": list(display_order),
                                    "target_display_position": target_position,
                                    "realized_mapping": mapping,
                                    "audit_semantic_class": answer_class,
                                    "audit_semantic_class_visibility": "EXCLUDED_FROM_MODEL_INPUT",
                                    "target_atom_placeholder": target,
                                    "abi_manifest_sha256": ABI_MANIFEST_SHA256,
                                    "source_evidence_ingest": SOURCE_INGEST,
                                    "second_order_leak_review": LEAK_REVIEW,
                                    "proof_topology_review": PROOF_TOPOLOGY_REVIEW,
                                    "prompt": prompt,
                                    "target": target,
                                }


def _require_constant(counter: collections.Counter, expected: int, label: str) -> None:
    if not counter or any(v != expected for v in counter.values()):
        raise AssertionError(f"{label}: expected every observed cell={expected}, got {dict(counter)}")


def _majority_decoder_accuracy(rows_: list[dict], features: tuple[str, ...]) -> float:
    groups = collections.defaultdict(collections.Counter)
    for r in rows_:
        key = tuple(r[f] for f in features)
        groups[key][r["target"]] += 1
    correct = sum(max(c.values()) for c in groups.values())
    return correct / len(rows_)


def _conditional_mutual_information(
    rows_: list[dict],
    x_key: str,
    y_key: str,
    z_keys: tuple[str, ...],
) -> float:
    """Empirical discrete I(X;Y|Z) in bits."""
    by_z = collections.defaultdict(list)
    for r in rows_:
        z = tuple(r[k] for k in z_keys)
        by_z[z].append(r)
    total = len(rows_)
    cmi = 0.0
    for group in by_z.values():
        n = len(group)
        x = collections.Counter(r[x_key] for r in group)
        y = collections.Counter(r[y_key] for r in group)
        xy = collections.Counter((r[x_key], r[y_key]) for r in group)
        inner = 0.0
        for (xv, yv), nxy in xy.items():
            pxy = nxy / n
            px = x[xv] / n
            py = y[yv] / n
            inner += pxy * math.log2(pxy / (px * py))
        cmi += (n / total) * inner
    return cmi


def _assert_twin_invariance(materialized: list[dict]) -> None:
    mapping_groups = collections.defaultdict(list)
    for r in materialized:
        key = (
            r["template_id"], r["base_state_class"], r["query_polarity"],
            r["proof_topology"], r["focus_record_position"], r["display_order_id"],
        )
        mapping_groups[key].append(r)
    for key, group in mapping_groups.items():
        if len(group) != 6:
            raise AssertionError(f"mapping twin size {key}: {len(group)}")
        counts = collections.Counter(r["target"] for r in group)
        _require_constant(counts, 2, f"mapping-swap twin {key}")

    state_groups = collections.defaultdict(list)
    for r in materialized:
        key = (
            r["template_id"], r["s3_permutation_id"], r["query_polarity"],
            r["proof_topology"], r["focus_record_position"], r["display_order_id"],
        )
        state_groups[key].append(r)
    for key, group in state_groups.items():
        if len(group) != 3 or len({r["target"] for r in group}) != 3:
            raise AssertionError(f"state-flip twin fail {key}")

    topo_groups = collections.defaultdict(set)
    for r in materialized:
        key = (
            r["template_id"], r["base_state_class"], r["s3_permutation_id"],
            r["query_polarity"], r["focus_record_position"], r["display_order_id"],
        )
        topo_groups[key].add(r["target"])
    if any(len(v) != 1 for v in topo_groups.values()):
        raise AssertionError("topology-invariance twin fail")

    order_groups = collections.defaultdict(set)
    for r in materialized:
        key = (
            r["template_id"], r["base_state_class"], r["s3_permutation_id"],
            r["query_polarity"], r["proof_topology"], r["focus_record_position"],
        )
        order_groups[key].add(r["target"])
    if any(len(v) != 1 for v in order_groups.values()):
        raise AssertionError("codebook-order twin fail")

    focus_groups = collections.defaultdict(set)
    for r in materialized:
        key = (
            r["template_id"], r["base_state_class"], r["s3_permutation_id"],
            r["query_polarity"], r["proof_topology"], r["display_order_id"],
        )
        focus_groups[key].add(r["target"])
    if any(len(v) != 1 for v in focus_groups.values()):
        raise AssertionError("focus-position twin fail")


def validate(materialized: list[dict]) -> dict:
    """Exact source-design gates. No model/runtime/training credit."""
    expected_split = {"TRAIN": 7776, "VALIDATION": 1944, "HOLDOUT": 1944}
    split_counts = collections.Counter(row["split"] for row in materialized)
    if dict(split_counts) != expected_split:
        raise AssertionError(f"split counts {dict(split_counts)} != {expected_split}")
    if len(materialized) != 11664:
        raise AssertionError(f"expected 11664 total rows, got {len(materialized)}")

    seen = set()
    for row in materialized:
        key = (
            row["template_id"],
            row["base_state_class"],
            row["s3_permutation_id"],
            row["display_order_id"],
            row["query_polarity"],
            row["proof_topology"],
            row["focus_record_position"],
        )
        if key in seen:
            raise AssertionError(f"duplicate factorial cell: {key}")
        seen.add(key)
        if row["target"] != row["realized_mapping"][row["audit_semantic_class"]]:
            raise AssertionError(f"target derivation mismatch: {key}")
        outside_codebook = row["prompt"].split("END_CODEBOOK\n", 1)[1]
        for cls in CLASSES:
            if cls in outside_codebook:
                raise AssertionError(f"class-label leak outside codebook: {key}/{cls}")

    for tid in TEMPLATES:
        block = [r for r in materialized if r["template_id"] == tid]
        if len(block) != 1944:
            raise AssertionError(f"{tid}: expected 1944 rows, got {len(block)}")

        by_class_target = collections.Counter(
            (r["audit_semantic_class"], r["target"]) for r in block
        )
        _require_constant(by_class_target, 216, f"{tid}: answer-class/target")

        by_target_position = collections.Counter(
            (r["target"], r["target_display_position"]) for r in block
        )
        _require_constant(by_target_position, 216, f"{tid}: target/display-position")

        for nuisance in ("proof_topology", "focus_record_position", "display_order_id"):
            by_nuisance_target = collections.Counter((r[nuisance], r["target"]) for r in block)
            expected = len(block) // (len(set(r[nuisance] for r in block)) * 3)
            _require_constant(by_nuisance_target, expected, f"{tid}: {nuisance}/target")

        nuisance_acc = _majority_decoder_accuracy(
            block,
            (
                "base_state_class",
                "query_polarity",
                "proof_topology",
                "focus_record_position",
                "display_order_id",
            ),
        )
        if abs(nuisance_acc - (1.0 / 3.0)) > 1e-12:
            raise AssertionError(f"{tid}: nuisance-only decoder accuracy {nuisance_acc}")

        cmi_topology = _conditional_mutual_information(
            block,
            "target",
            "proof_topology",
            (
                "audit_semantic_class",
                "s3_permutation_id",
                "display_order_id",
                "query_polarity",
                "focus_record_position",
            ),
        )
        cmi_order = _conditional_mutual_information(
            block,
            "target",
            "display_order_id",
            (
                "audit_semantic_class",
                "s3_permutation_id",
                "query_polarity",
                "proof_topology",
                "focus_record_position",
            ),
        )
        if abs(cmi_topology) > 1e-12:
            raise AssertionError(f"{tid}: conditional MI topology leak {cmi_topology}")
        if abs(cmi_order) > 1e-12:
            raise AssertionError(f"{tid}: conditional MI display-order leak {cmi_order}")

    _assert_twin_invariance(materialized)

    ancestry_splits = collections.defaultdict(set)
    split_symbols = collections.defaultdict(set)
    for r in materialized:
        ancestry_splits[r["provenance_ancestry_id"]].add(r["split"])
        split_symbols[r["split"]].update(r["realized_mapping"].values())
    if any(len(v) != 1 for v in ancestry_splits.values()):
        raise AssertionError("provenance ancestry crosses splits")
    for a, b in itertools.combinations(split_symbols, 2):
        if split_symbols[a] & split_symbols[b]:
            raise AssertionError(f"placeholder symbol pool crosses splits: {a}/{b}")

    return {
        "status": "PASS_LOGICAL_BLUEPRINT_ONLY",
        "schema_revision": "v2.2",
        "rows": 11664,
        "split_counts": expected_split,
        "rows_per_template": 1944,
        "proof_topologies": list(PROOF_TOPOLOGIES),
        "query_polarities": list(QUERY_POLARITIES),
        "focus_positions": 3,
        "s3_mappings": 6,
        "display_orders": 6,
        "counterfactual_twins": {
            "mapping_swap": "PASS",
            "state_flip": "PASS",
            "topology_invariance": "PASS",
            "codebook_order": "PASS",
            "focus_position": "PASS",
        },
        "conditional_mi_topology_bits": 0.0,
        "conditional_mi_display_order_bits": 0.0,
        "nuisance_only_decoder_accuracy": 1.0 / 3.0,
        "nuisance_only_decoder_chance": 1.0 / 3.0,
        "split_symbol_overlap": False,
        "training_eligible": False,
        "remaining_gate": "VERIFIED_REAL_ABI_ATOM_RENDER_PLUS_EXACT_TOKENIZER_MODEL_PROVENANCE_AND_FROZEN_REAL_HOLDOUTS",
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
        args.receipt.write_text(
            json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
