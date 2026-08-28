#!/usr/bin/env python3
"""Generate Trigger-2 dynamic codebook binding candidates.

SOURCE/METHOD ONLY. This generator is designed from the 2026-08-25 Claude XENO
measurement ingest. It does not mint accepted dataset, J-Space, training, HCU or
EntityOS runtime credit.

Default symbols are deliberately schematic. Before training admission, replace them
with accepted single-token atoms from the exact measured XENO ABI and freeze a
symbol-family train/validation/holdout policy.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "ENTITYOS_HCU_BINDING_TEMPLATE_CANDIDATE/v1"
ANCESTRY = "trigger2-20260825-claude-xeno-binding-method-seed-v2"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SLOTS = {"ALLOW": "K0", "DENY": "K1", "ABSTAIN": "K2"}
SCHEMATIC_SYMBOLS = ("raku", "melo", "tiv")

SCENARIOS = {
    "T1_codebook": {
        "ALLOW": "Rule: a gate opens when the visitor has both a valid badge and a matching appointment. Ivo has a valid badge and a matching appointment. Query: should the gate open for Ivo?",
        "DENY": "Rule: a gate opens when the visitor has both a valid badge and a matching appointment. Ivo has a valid badge but no matching appointment. Query: should the gate open for Ivo?",
        "ABSTAIN": "Rule: a gate opens when the visitor has both a valid badge and a matching appointment. Ivo has a valid badge; whether a matching appointment exists was not observed. Query: should the gate open for Ivo?",
    },
    "T2_question": {
        "ALLOW": "A locker releases only when the user is registered, the key is paired, and the PIN is current. Mira is registered, her key is paired, and her PIN is current. Which decision follows?",
        "DENY": "A locker releases only when the user is registered, the key is paired, and the PIN is current. Mira is registered and her key is paired, but her PIN is expired. Which decision follows?",
        "ABSTAIN": "A locker releases only when the user is registered, the key is paired, and the PIN is current. Mira is registered and her key is paired; the PIN status is unavailable. Which decision follows?",
    },
    "T3_assertion": {
        "ALLOW": "Mesh admission requires a current certificate and a fresh nonce. Node N7 presents a current certificate and a fresh nonce. Determine the admission state.",
        "DENY": "Mesh admission requires a current certificate and a fresh nonce. Node N7 presents an expired certificate and a fresh nonce. Determine the admission state.",
        "ABSTAIN": "Mesh admission requires a current certificate and a fresh nonce. Node N7 presents a current certificate; nonce freshness is unknown. Determine the admission state.",
    },
    "T4_ichform": {
        "ALLOW": "I may enter the lab only when my slot is booked and my badge is active. My slot is booked and my badge is active. Determine my access state.",
        "DENY": "I may enter the lab only when my slot is booked and my badge is active. My slot is booked but my badge is inactive. Determine my access state.",
        "ABSTAIN": "I may enter the lab only when my slot is booked and my badge is active. My slot is booked; my badge status has not been checked. Determine my access state.",
    },
}


def stable_shuffle(items: list[str], row_key: str) -> list[str]:
    seed = int.from_bytes(hashlib.sha256(row_key.encode("utf-8")).digest()[:8], "big")
    out = list(items)
    random.Random(seed).shuffle(out)
    return out


def common(family_id: str, phase: str, perm_id: str, symbol_status: str) -> dict:
    return {
        "schema": SCHEMA,
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "family_id": family_id,
        "provenance_ancestry_id": ANCESTRY,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "target_type": "SCHEMATIC_DYNAMIC_BINDING" if symbol_status.startswith("SCHEMATIC") else "DYNAMIC_BINDING_CANDIDATE",
        "split": "TRAIN_CANDIDATE_ONLY",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "source_evidence_scope": "CLAUDE_XENO_MEASURED_DISSOCIATION_READABLE_SEMANTICS_WRITABLE_SYMBOL_MISSING_DYNAMIC_BINDING",
        "symbol_status": symbol_status,
        "curriculum_phase": phase,
        "permutation_id": perm_id,
    }


def render_codebook(mapping: dict[str, str], order: list[str]) -> str:
    return " | ".join(f"{key} => {mapping[key]}" for key in order)


def generate(symbols: tuple[str, str, str], symbol_status: str) -> list[dict]:
    rows: list[dict] = []
    perms = list(itertools.permutations(symbols))
    for p_idx, perm in enumerate(perms):
        perm_id = f"S3_{p_idx}"
        class_map = dict(zip(CLASSES, perm))
        slot_map = {SLOTS[c]: class_map[c] for c in CLASSES}

        # P0: isolate the suspected missing computation. Semantic decoding is removed;
        # the model only has to perform episode-local slot -> symbol routing.
        for c in CLASSES:
            slot = SLOTS[c]
            row_key = f"P0|{perm_id}|{slot}"
            order = stable_shuffle(list(slot_map), row_key)
            row = common("DYNAMIC_CODEBOOK_BINDING_F02_ROUTER_ONLY", "P0_ROUTER_ONLY", perm_id, symbol_status)
            row.update({
                "template_id": "P0_slot_lookup",
                "semantic_case_id": f"{slot}_ROUTER_ONLY",
                "semantic_class_metadata_only": c,
                "semantic_slot": slot,
                "codebook_mapping": slot_map,
                "codebook_entry_order": order,
                "prompt": f"Episode-local route table: {render_codebook(slot_map, order)}\nCurrent semantic slot: {slot}\nReturn exactly the bound code token.",
                "target": slot_map[slot],
                "aux_binding_target": {
                    "semantic_slot": slot,
                    "episode_symbol_slot": slot_map[slot],
                    "operation": "LOOKUP_EPISODE_CODEBOOK -> EMIT_BOUND_SYMBOL",
                },
                "counterfactual_group_id": f"P0_{slot}_ALL_S3",
            })
            rows.append(row)

        # P1: reattach natural semantics. The same scenario is paired with all six S3
        # mappings, so semantic content cannot predict the output symbol without reading
        # the episode-local codebook.
        for template_id, by_class in SCENARIOS.items():
            for c in CLASSES:
                row_key = f"P1|{perm_id}|{template_id}|{c}"
                order = stable_shuffle(list(class_map), row_key)
                row = common("DYNAMIC_CODEBOOK_BINDING_F02_INTEGRATED", "P1_SEMANTIC_TO_ROUTER", perm_id, symbol_status)
                row.update({
                    "template_id": template_id,
                    "semantic_case_id": f"{c}_BASE_{template_id}",
                    "semantic_class_metadata_only": c,
                    "semantic_slot": SLOTS[c],
                    "codebook_mapping": class_map,
                    "codebook_entry_order": order,
                    "prompt": f"Episode-local codebook: {render_codebook(class_map, order)}\n{by_class[c]}\nReturn exactly one code token.",
                    "target": class_map[c],
                    "aux_binding_target": {
                        "semantic_slot": SLOTS[c],
                        "episode_symbol_slot": class_map[c],
                        "operation": "READ_SEMANTIC_SUBSPACE -> BIND_TO_INTERNAL_SLOT -> LOOKUP_EPISODE_CODEBOOK -> EMIT_BOUND_SYMBOL",
                    },
                    "counterfactual_group_id": f"P1_{c}_{template_id}_ALL_S3",
                })
                rows.append(row)
    return rows


def audit(rows: list[dict], symbols: tuple[str, str, str]) -> dict:
    failures: list[str] = []
    if len(rows) != 90:
        failures.append(f"ROW_COUNT:{len(rows)}!=90")

    perm_counts = Counter(r["permutation_id"] for r in rows)
    if sorted(perm_counts.values()) != [15] * 6:
        failures.append(f"PERMUTATION_COUNTS:{dict(perm_counts)}")

    pair_counts = Counter((r["semantic_class_metadata_only"], r["target"]) for r in rows)
    expected_pairs = {(c, s) for c in CLASSES for s in symbols}
    if set(pair_counts) != expected_pairs or set(pair_counts.values()) != {10}:
        failures.append(f"CLASS_SYMBOL_COUNTERBALANCE:{dict(pair_counts)}")

    actual_perm_maps = {
        tuple(r["codebook_mapping"][c] for c in CLASSES)
        for r in rows if r["curriculum_phase"] == "P1_SEMANTIC_TO_ROUTER"
    }
    expected_perm_maps = set(itertools.permutations(symbols))
    if actual_perm_maps != expected_perm_maps:
        failures.append("S3_ACTUAL_MAPPING_COVERAGE")

    for i, r in enumerate(rows):
        key = r["semantic_slot"] if r["curriculum_phase"] == "P0_ROUTER_ONLY" else r["semantic_class_metadata_only"]
        if r["codebook_mapping"][key] != r["target"]:
            failures.append(f"TARGET_MAPPING_MISMATCH:{i}")
        if r["curriculum_phase"] == "P1_SEMANTIC_TO_ROUTER":
            # Class words are permitted only on the explicit first-line codebook span.
            body = "\n".join(r["prompt"].splitlines()[1:])
            leaked = [c for c in CLASSES if c in body]
            if leaked:
                failures.append(f"CLASS_WORD_LEAK:{i}:{leaked}")

    # Causal S3 counterfactual check: within each fixed semantic scenario/template,
    # all 6 mappings exist and each symbol is the target exactly twice.
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["counterfactual_group_id"]].append(r)
    for gid, members in groups.items():
        if len(members) != 6:
            failures.append(f"COUNTERFACTUAL_GROUP_SIZE:{gid}:{len(members)}")
            continue
        target_counts = Counter(m["target"] for m in members)
        if set(target_counts) != set(symbols) or set(target_counts.values()) != {2}:
            failures.append(f"COUNTERFACTUAL_TARGET_BALANCE:{gid}:{dict(target_counts)}")

    return {
        "pass": not failures,
        "rows": len(rows),
        "phase_counts": dict(Counter(r["curriculum_phase"] for r in rows)),
        "permutation_counts": dict(sorted(perm_counts.items())),
        "class_symbol_pair_counts": {f"{c}->{s}": pair_counts[(c, s)] for c in CLASSES for s in symbols},
        "counterfactual_groups": len(groups),
        "checks": [
            "ALL_SIX_S3_MAPPINGS_REALIZED_IN_ACTUAL_CODEBOOKS_NOT_METADATA_ONLY",
            "EXACT_CLASS_SYMBOL_COUNTERBALANCE",
            "TARGET_DERIVED_FROM_REALIZED_CODEBOOK_MAPPING",
            "CODEBOOK_ENTRY_ORDER_DETERMINISTICALLY_RANDOMIZED",
            "P1_CLASS_WORDS_ONLY_IN_EXPLICIT_CODEBOOK_SPAN",
            "EACH_FIXED_SEMANTIC_CASE_HAS_ALL_SIX_CODEBOOK_COUNTERFACTUALS",
            "EACH_COUNTERFACTUAL_GROUP_ROUTES_EACH_SYMBOL_EXACTLY_TWICE",
        ],
        "failures": failures,
        "open_admission_gates": [
            "REPLACE_SCHEMATIC_SYMBOLS_WITH_EXACT_ACCEPTED_46_ATOM_ABI_POOL",
            "FREEZE_UNSEEN_SYMBOL_HOLDOUT_BEFORE_TUNING",
            "FREEZE_UNSEEN_TEMPLATE_AND_SEMANTIC_LEXICAL_FAMILY_HOLDOUTS",
            "ADD_QUERY_POLARITY_FACTORIALIZATION_REQUIRED_BY_SUPERVISOR_8_78",
            "VERIFY_EXACT_TOKENIZER_COUNTS_AND_LAST_TOKEN_POSITION_MATCHING",
            "ADD_RANK_AWARE_1D_2D_SEMANTIC_GEOMETRY_AND_RANK_COMPLETE_NUISANCE_CONTROLS",
            "BIND_ROWS_TO_EXACT_ABI_MANIFEST_MODEL_TOKENIZER_GENERATOR_AND_CAUSAL_PROVENANCE",
            "KEEP_POSITIVE_JSPACE_LABELS_FORBIDDEN_UNTIL_SAME_MODEL_CAUSAL_RECEIPTS_EXIST",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--audit", type=Path)
    ap.add_argument("--symbols", nargs=3, default=list(SCHEMATIC_SYMBOLS), metavar=("S0", "S1", "S2"))
    ap.add_argument("--abi-admitted", action="store_true", help="Caller asserts supplied symbols are accepted ABI atoms; generator does not verify that assertion.")
    args = ap.parse_args()

    symbols = tuple(args.symbols)
    if len(set(symbols)) != 3 or any(not s.strip() for s in symbols):
        raise SystemExit("symbols must be three distinct non-empty strings")
    symbol_status = "CALLER_ASSERTED_ABI_ADMITTED_UNVERIFIED_BY_GENERATOR" if args.abi_admitted else "SCHEMATIC_ONLY_NOT_ABI_ATOM_ADMITTED"
    rows = generate(symbols, symbol_status)
    report = audit(rows, symbols)
    if not report["pass"]:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    payload = args.output.read_bytes()
    report["output_sha256"] = hashlib.sha256(payload).hexdigest()
    report["output_bytes"] = len(payload)
    if args.audit:
        args.audit.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
