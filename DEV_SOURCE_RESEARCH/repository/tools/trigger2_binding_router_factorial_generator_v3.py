#!/usr/bin/env python3
"""Factorial Trigger-2 dynamic binding generator v3.

METHOD_ONLY / BLUEPRINT-OR-RENDERED-CANDIDATE. This successor fuses the useful
mechanisms of the two v2 current-main donors:
- explicit P0 router-only isolation;
- P1 semantic->router composition;
- actual all-S3 mapping realization and target derivation;
- deterministic codebook-order randomization;
- exact counterfactual audits;
- independent template-OOD, symbol-OOD and joint-OOD diagnostic axes;
- direct/inverted query-polarity factorialization.

No row is training-eligible unless an external atom manifest supplies ABI-bound,
verified single-token atoms. Even then these rows are candidates, not evidence-qualified
accepted dataset tokens. Positive hidden-state/J-Space labels are intentionally absent.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

SCHEMA = "ENTITYOS_HCU_BINDING_FACTORIAL_CANDIDATE/v3"
ANCESTRY = "trigger2-20260825-dynamic-binding-factorial-v3"
ABI_MANIFEST_SHA256 = "0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SLOTS = {"ALLOW": "K0", "DENY": "K1", "ABSTAIN": "K2"}
FLIP = {"ALLOW": "DENY", "DENY": "ALLOW", "ABSTAIN": "ABSTAIN"}
POLARITIES = ("DIRECT", "INVERTED")

TRAIN_TEMPLATES = {
    "T1_GATE": {
        "ALLOW": "A gate opens only when badge_ok=1 and appointment_match=1. For case C, badge_ok=1 and appointment_match=1.",
        "DENY": "A gate opens only when badge_ok=1 and appointment_match=1. For case C, badge_ok=1 and appointment_match=0.",
        "ABSTAIN": "A gate opens only when badge_ok=1 and appointment_match=1. For case C, badge_ok=1 and appointment_match is unobserved.",
        "direct": "Does the evidence support opening the gate?",
        "inverted": "Does the evidence support keeping the gate closed?",
    },
    "T2_LEDGER": {
        "ALLOW": "Release requires every mandatory clause confirmed. The ledger has all mandatory clauses confirmed, contradictions=0, unresolved=0.",
        "DENY": "Release requires every mandatory clause confirmed. The ledger has one mandatory clause falsified, contradictions=1, unresolved=0.",
        "ABSTAIN": "Release requires every mandatory clause confirmed. The ledger lacks one mandatory observation, contradictions=0, unresolved=1.",
        "direct": "Does the evidence support release?",
        "inverted": "Does the evidence support withholding release?",
    },
    "T3_NESTED": {
        "ALLOW": "Authorization requires x=1 and y=1. State={\"x\":1,\"y\":1,\"faults\":[],\"unknown\":[]}.",
        "DENY": "Authorization requires x=1 and y=1. State={\"x\":1,\"y\":0,\"faults\":[\"y\"],\"unknown\":[]}.",
        "ABSTAIN": "Authorization requires x=1 and y=1. State={\"x\":1,\"y\":null,\"faults\":[],\"unknown\":[\"y\"]}.",
        "direct": "Does the state support authorization?",
        "inverted": "Does the state support rejecting authorization?",
    },
    "T4_FIRST_PERSON": {
        "ALLOW": "I may enter only if my slot is booked and my badge is active. My slot is booked and my badge is active.",
        "DENY": "I may enter only if my slot is booked and my badge is active. My slot is booked and my badge is inactive.",
        "ABSTAIN": "I may enter only if my slot is booked and my badge is active. My slot is booked; my badge status has not been checked.",
        "direct": "Does the evidence support my entry?",
        "inverted": "Does the evidence support refusing my entry?",
    },
}

OOD_TEMPLATES = {
    "T5_DIALOGUE": {
        "ALLOW": "Witness A confirms criterion p. Witness B confirms criterion q. No discrepancy is recorded.",
        "DENY": "Witness A confirms criterion p. Witness B contradicts criterion q. One discrepancy is recorded.",
        "ABSTAIN": "Witness A confirms criterion p. No observation exists for criterion q. The record is incomplete.",
        "direct": "Does this support the requested action?",
        "inverted": "Does this support blocking the requested action?",
    },
    "T6_CLAYLIKE": {
        "ALLOW": "obs{req.a=1;req.b=1;viol=0;unk=0}",
        "DENY": "obs{req.a=1;req.b=0;viol=1;unk=0}",
        "ABSTAIN": "obs{req.a=1;req.b=?;viol=0;unk=1}",
        "direct": "judge{claim=execute}",
        "inverted": "judge{claim=block}",
    },
}

BLUEPRINT_POOLS = {
    "TRAIN_SYMBOLS": ("<ABI_TRAIN_A>", "<ABI_TRAIN_B>", "<ABI_TRAIN_C>"),
    "HOLDOUT_SYMBOLS": ("<ABI_HOLDOUT_A>", "<ABI_HOLDOUT_B>", "<ABI_HOLDOUT_C>"),
}


def stable_shuffle(items: Iterable[str], key: str) -> list[str]:
    out = list(items)
    seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
    random.Random(seed).shuffle(out)
    return out


def load_atom_manifest(path: Path | None) -> tuple[dict[str, tuple[str, str, str]], dict]:
    if path is None:
        return dict(BLUEPRINT_POOLS), {
            "mode": "BLUEPRINT_PLACEHOLDER",
            "training_eligible": False,
            "reason": "EXACT_ABI_ATOM_MANIFEST_NOT_SUPPLIED",
        }
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("abi_manifest_sha256") != ABI_MANIFEST_SHA256:
        raise ValueError("atom manifest ABI hash mismatch")
    if doc.get("single_token_verification") is not True:
        raise ValueError("atom manifest must attest single_token_verification=true")
    parts = doc.get("partitions") or {}
    train = tuple(parts.get("TRAIN", ()))
    holdout = tuple(parts.get("HOLDOUT", ()))
    if len(train) < 3 or len(holdout) < 3:
        raise ValueError("atom manifest needs >=3 TRAIN and >=3 HOLDOUT atoms")
    if set(train) & set(holdout):
        raise ValueError("TRAIN/HOLDOUT atom partitions overlap")
    pools = {"TRAIN_SYMBOLS": train[:3], "HOLDOUT_SYMBOLS": holdout[:3]}
    return pools, {
        "mode": "ABI_RENDERED_CANDIDATE",
        "training_eligible": False,
        "reason": "RENDERED_ROWS_STILL_REQUIRE_FAMILY_SPLIT_LEAK_TOKENIZER_AND_EVIDENCE_ADMISSION_GATES",
        "atom_manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "tokenizer_identity": doc.get("tokenizer_identity"),
    }


def decision_class(base_state: str, polarity: str) -> str:
    return base_state if polarity == "DIRECT" else FLIP[base_state]


def codebook(mapping: dict[str, str], order: list[str]) -> str:
    return " | ".join(f"{c} => {mapping[c]}" for c in order)


def row_common(split: str, phase: str, symbol_partition: str, render: dict) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "provenance_ancestry_id": ANCESTRY,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "selected_using_holdout": False,
        "split": split,
        "split_unit": "FACTORIAL_DIAGNOSTIC_CELL_WITH_CAUSAL_FAMILY_PROVENANCE",
        "curriculum_phase": phase,
        "symbol_partition": symbol_partition,
        "abi_manifest_sha256": ABI_MANIFEST_SHA256,
        "render_mode": render["mode"],
        "training_eligible": False,
        "positive_jspace_label": False,
    }


def p0_rows(pool_name: str, symbols: tuple[str, str, str], split: str, render: dict):
    for pid, perm in enumerate(itertools.permutations(symbols)):
        slot_map = dict(zip(("K0", "K1", "K2"), perm))
        for slot in ("K0", "K1", "K2"):
            order = stable_shuffle(slot_map, f"P0|{pool_name}|P{pid}|{slot}")
            r = row_common(split, "P0_ROUTER_ONLY", pool_name, render)
            r.update({
                "family_id": f"BIND_V3_P0_{pool_name}_{slot}",
                "s3_permutation_id": f"P{pid}",
                "semantic_slot_model_visible": slot,
                "semantic_class_metadata_only": CLASSES[("K0", "K1", "K2").index(slot)],
                "realized_mapping": slot_map,
                "codebook_entry_order": order,
                "prompt": f"ROUTE: {' | '.join(f'{k} => {slot_map[k]}' for k in order)}\nSLOT: {slot}\nReturn exactly the bound code token.",
                "target": slot_map[slot],
                "counterfactual_group_id": f"P0|{pool_name}|{slot}|ALL_S3",
            })
            yield r


def p1_rows(template_partition: str, templates: dict, pool_name: str, symbols: tuple[str, str, str], split: str, render: dict):
    for tid, spec in templates.items():
        for base in CLASSES:
            for polarity in POLARITIES:
                decided = decision_class(base, polarity)
                for pid, perm in enumerate(itertools.permutations(symbols)):
                    mapping = dict(zip(CLASSES, perm))
                    order = stable_shuffle(CLASSES, f"P1|{tid}|{pool_name}|{base}|{polarity}|P{pid}")
                    r = row_common(split, "P1_SEMANTIC_TO_ROUTER", pool_name, render)
                    r.update({
                        "family_id": f"BIND_V3_{template_partition}_{tid}_{base}_{polarity}",
                        "template_partition": template_partition,
                        "template_id": tid,
                        "base_semantic_state_metadata_only": base,
                        "query_polarity": polarity,
                        "decision_class_metadata_only": decided,
                        "semantic_slot_metadata_only": SLOTS[decided],
                        "s3_permutation_id": f"P{pid}",
                        "realized_mapping": mapping,
                        "codebook_entry_order": order,
                        "prompt": (
                            f"CODEBOOK: {codebook(mapping, order)}\n"
                            f"SCENE: {spec[base]}\n"
                            f"QUERY: {spec['direct' if polarity == 'DIRECT' else 'inverted']}\n"
                            "Return exactly one code token."
                        ),
                        "target": mapping[decided],
                        "counterfactual_group_id": f"P1|{tid}|{pool_name}|{base}|{polarity}|ALL_S3",
                        "polarity_pair_id": f"P1|{tid}|{pool_name}|{base}|P{pid}",
                    })
                    yield r


def generate(pools: dict[str, tuple[str, str, str]], render: dict) -> list[dict]:
    rows = []
    rows += list(p0_rows("TRAIN_SYMBOLS", pools["TRAIN_SYMBOLS"], "TRAIN", render))
    rows += list(p0_rows("HOLDOUT_SYMBOLS", pools["HOLDOUT_SYMBOLS"], "DIAG_SYMBOL_OOD", render))
    rows += list(p1_rows("TRAIN_TEMPLATE", TRAIN_TEMPLATES, "TRAIN_SYMBOLS", pools["TRAIN_SYMBOLS"], "TRAIN", render))
    rows += list(p1_rows("TRAIN_TEMPLATE", TRAIN_TEMPLATES, "HOLDOUT_SYMBOLS", pools["HOLDOUT_SYMBOLS"], "DIAG_SYMBOL_OOD", render))
    rows += list(p1_rows("OOD_TEMPLATE", OOD_TEMPLATES, "TRAIN_SYMBOLS", pools["TRAIN_SYMBOLS"], "DIAG_TEMPLATE_OOD", render))
    rows += list(p1_rows("OOD_TEMPLATE", OOD_TEMPLATES, "HOLDOUT_SYMBOLS", pools["HOLDOUT_SYMBOLS"], "DIAG_JOINT_OOD", render))
    return rows


def audit(rows: list[dict], pools: dict[str, tuple[str, str, str]], render: dict) -> dict:
    failures = []
    counts = Counter(r["split"] for r in rows)
    expected = {"TRAIN": 162, "DIAG_SYMBOL_OOD": 162, "DIAG_TEMPLATE_OOD": 72, "DIAG_JOINT_OOD": 72}
    if dict(counts) != expected:
        failures.append(f"SPLIT_COUNTS:{dict(counts)}!=EXPECTED:{expected}")

    for i, r in enumerate(rows):
        if r["curriculum_phase"] == "P0_ROUTER_ONLY":
            key = r["semantic_slot_model_visible"]
        else:
            key = r["decision_class_metadata_only"]
            body = "\n".join(r["prompt"].splitlines()[1:])
            leaked = [c for c in CLASSES if c in body]
            if leaked:
                failures.append(f"CLASS_WORD_LEAK_OUTSIDE_CODEBOOK:{i}:{leaked}")
        if r["realized_mapping"][key] != r["target"]:
            failures.append(f"TARGET_NOT_FROM_MAPPING:{i}")

    groups = defaultdict(list)
    for r in rows:
        groups[r["counterfactual_group_id"]].append(r)
    for gid, members in groups.items():
        if len(members) != 6:
            failures.append(f"GROUP_SIZE:{gid}:{len(members)}")
            continue
        symbols = set(members[0]["realized_mapping"].values())
        tcounts = Counter(m["target"] for m in members)
        if set(tcounts) != symbols or set(tcounts.values()) != {2}:
            failures.append(f"S3_TARGET_BALANCE:{gid}:{dict(tcounts)}")

    pairs = defaultdict(dict)
    for r in rows:
        if r["curriculum_phase"] == "P1_SEMANTIC_TO_ROUTER":
            pairs[r["polarity_pair_id"]][r["query_polarity"]] = r
    for pid, pair in pairs.items():
        if set(pair) != set(POLARITIES):
            failures.append(f"POLARITY_PAIR_INCOMPLETE:{pid}")
            continue
        d, inv = pair["DIRECT"], pair["INVERTED"]
        base = d["base_semantic_state_metadata_only"]
        should_same = base == "ABSTAIN"
        if (d["target"] == inv["target"]) != should_same:
            failures.append(f"POLARITY_TARGET_RELATION:{pid}")

    train_symbols = set(pools["TRAIN_SYMBOLS"])
    holdout_symbols = set(pools["HOLDOUT_SYMBOLS"])
    if train_symbols & holdout_symbols:
        failures.append("SYMBOL_PARTITION_OVERLAP")
    for r in rows:
        target = r["target"]
        if r["split"] == "TRAIN" and target not in train_symbols:
            failures.append("HOLDOUT_SYMBOL_IN_TRAIN")
        if r["split"] in {"DIAG_SYMBOL_OOD", "DIAG_JOINT_OOD"} and target not in holdout_symbols:
            failures.append("SYMBOL_OOD_CELL_NOT_HOLDOUT_SYMBOL")
        if r.get("template_partition") == "OOD_TEMPLATE" and r["template_id"] in TRAIN_TEMPLATES:
            failures.append("TEMPLATE_PARTITION_DRIFT")

    balance = {}
    for split in expected:
        subset = [r for r in rows if r["split"] == split and r["curriculum_phase"] == "P1_SEMANTIC_TO_ROUTER"]
        if not subset:
            continue
        c = Counter((r["decision_class_metadata_only"], r["target"]) for r in subset)
        vals = set(c.values())
        balance[split] = {f"{k[0]}->{k[1]}": v for k, v in sorted(c.items())}
        if len(vals) != 1:
            failures.append(f"CLASS_SYMBOL_IMBALANCE:{split}:{sorted(vals)}")

    return {
        "pass": not failures,
        "rows": len(rows),
        "split_counts": dict(counts),
        "counterfactual_groups": len(groups),
        "polarity_pairs": len(pairs),
        "render": render,
        "class_symbol_balance": balance,
        "failures": failures,
        "closed_by_v3": [
            "ACTUAL_S3_MAPPING_NOT_METADATA_ONLY",
            "CODEBOOK_ENTRY_ORDER_RANDOMIZATION",
            "EXACT_S3_COUNTERFACTUAL_GROUPS",
            "QUERY_POLARITY_FACTORIALIZATION",
            "SEPARATE_SYMBOL_OOD_TEMPLATE_OOD_AND_JOINT_OOD_DIAGNOSTICS",
            "NO_POSITIVE_JSPACE_HIDDEN_STATE_LABELS",
        ],
        "still_open": [
            "EXACT_46_ATOM_ABI_POOL_INGEST_AND_PARTITION_FREEZE",
            "EXACT_TOKENIZER_AND_LAST_TOKEN_POSITION_MATCHING",
            "SEALED_LEXICAL_FAMILY_HOLDOUT_DISTINCT_FROM_DIAGNOSTIC_CELLS",
            "RANK_AWARE_1D_2D_GEOMETRY_AND_RANK_COMPLETE_NUISANCE_CONTROLS",
            "FULL_STATE_CAUSAL_MATRIX_AND_OFF_TARGET_REGRESSION",
            "SAME_SELECTED_QWEN35_CHECKPOINT_RUNTIME_RECEIPT_BINDING",
            "RETENTION_AND_ABLITERATION_CAPABILITY_FLOORS",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--audit", type=Path)
    ap.add_argument("--atom-manifest", type=Path)
    args = ap.parse_args()
    pools, render = load_atom_manifest(args.atom_manifest)
    rows = generate(pools, render)
    report = audit(rows, pools, render)
    if not report["pass"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    report["output_sha256"] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    report["output_bytes"] = args.output.stat().st_size
    if args.audit:
        args.audit.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
