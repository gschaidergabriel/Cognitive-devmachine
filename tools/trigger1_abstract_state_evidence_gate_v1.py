#!/usr/bin/env python3
"""Fail-closed abstract-state evidence gate for Trigger-1 / Qwen3-0.6B.

This gate closes three specific overclaim paths that predecessor J-Space gates do not
close by themselves:

1. model-facing semantic labels / generic decision-compliance language can masquerade
   as an abstract internal state;
2. basis/calibration/holdout can be nominally different while reusing class-bearing
   lexemes; and
3. native llama.cpp cvec broadcast and the historical PyTorch last-token witness can
   be silently treated as the same intervention.

Every state-varying span is explicit as ``semantic_payload`` and the model-facing prompt
must be exactly ``scaffold_prefix + semantic_payload + scaffold_suffix``. State-varying
payload lexemes must be pairwise disjoint across BASIS/CALIBRATION/HOLDOUT. The gate
also verifies a balanced held-out internal readout, matched causal controls, and an
opaque-code counterbalance from raw scores/logits.

Native-cvec broadcast can pass without proving equivalence to the historical last-token
witness. Cross-intervention equivalence is a separate stronger flag and requires an
explicit support-matched bridge. This deliberately severs an unsupported equivalence
rather than pretending it has been established.

This adjudicator never runs a model and never mints canonical semantics, J-Space model
runtime, HCU, EntityOS, training, BASE, or real-effect credit.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_EVIDENCE_GATE/v1"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_ATTESTATION/v1"
STATES = ("S0", "S1", "S2")
SPLITS = ("basis", "calibration", "holdout")
CODES = ("A", "B", "C")
INTERVENTION_CONTROLS = ("TARGET", "NULL", "SHUFFLED", "SIGN_FLIP")

PINNED_GGUF_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
PINNED_LLAMA_CPP_COMMIT = "bb4caa7540188872173c44d161602d9271386413"
PINNED_LAYER = 20
PINNED_CARRIER = "LLAMA_CPP_LLAMA_SET_ADAPTER_CVEC"
PINNED_SCOPE = "ALL_PROMPT_TOKENS_NATIVE_CVEC_BROADCAST"

FORBIDDEN_MODEL_FACING_WORDS = {
    "affirmative", "negative", "neutral",
    "yes", "no", "not",
    "agree", "agreement", "disagree", "disagreement",
    "accept", "acceptance", "accepted", "reject", "rejection", "rejected",
    "approve", "approval", "approved", "disapprove", "disapproval",
    "support", "supported", "supporting", "oppose", "opposed", "opposition",
    "allow", "allowed", "deny", "denied", "denial",
    "grant", "granted", "refuse", "refused", "refusal",
    "endorse", "endorsed", "endorsement", "abstain", "abstention",
    "undecided", "favor", "favour", "against",
}
WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

MIN_FAMILIES_PER_SPLIT = 6
MIN_HOLDOUT_BALANCED_ACCURACY = 0.75
MIN_HOLDOUT_STATE_ACCURACY = 2.0 / 3.0
MIN_PERFECT_HOLDOUT_FAMILIES = 4
MIN_CAUSAL_TARGET_HIT_RATE = 0.75
MIN_MEAN_TARGET_MARGIN_VS_CONTROL = 0.05
MIN_BEHAVIOR_TARGET_MARGIN_VS_CONTROL = 0.05
MAX_CODE_DELTA_RANGE = 1.0


def _words(text: str) -> set[str]:
    return {m.group(0).lower() for m in WORD_RE.finditer(text)}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _score_margin(scores: dict[str, Any], state: str) -> float:
    if set(scores) != set(STATES) or not all(_is_number(v) for v in scores.values()):
        raise ValueError("STATE_SCORE_TRIPLE_REQUIRED")
    other = [s for s in STATES if s != state]
    return float(scores[state]) - 0.5 * (float(scores[other[0]]) + float(scores[other[1]]))


def _code_margin(logits: dict[str, Any], code: str) -> float:
    if set(logits) != set(CODES) or not all(_is_number(v) for v in logits.values()):
        raise ValueError("CODE_LOGIT_TRIPLE_REQUIRED")
    other = [c for c in CODES if c != code]
    return float(logits[code]) - 0.5 * (float(logits[other[0]]) + float(logits[other[1]]))


def _validate_intervention_contract(att: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    contract = att.get("intervention_contract")
    if not isinstance(contract, dict):
        failures.append("INTERVENTION_CONTRACT_REQUIRED")
        return {}
    required = {
        "carrier": PINNED_CARRIER,
        "token_scope": PINNED_SCOPE,
        "injection_layer": PINNED_LAYER,
        "gguf_sha256": PINNED_GGUF_SHA256,
        "llama_cpp_commit": PINNED_LLAMA_CPP_COMMIT,
    }
    for key, expected in required.items():
        if contract.get(key) != expected:
            failures.append(f"INTERVENTION_CONTRACT_MISMATCH:{key}")
    if contract.get("last_token_witness_equivalence_claimed") is not False:
        failures.append("LAST_TOKEN_WITNESS_EQUIVALENCE_MUST_NOT_BE_CLAIMED")
    if contract.get("last_token_witness_role") != "ANTECEDENT_ONLY_NOT_CAUSAL_EQUIVALENCE":
        failures.append("LAST_TOKEN_WITNESS_ROLE_MUST_BE_ANTECEDENT_ONLY")
    return contract


def _validate_prompt_splits(att: dict[str, Any], failures: list[str]) -> dict[str, dict[str, Any]]:
    design = att.get("prompt_design")
    if not isinstance(design, dict):
        failures.append("PROMPT_DESIGN_REQUIRED")
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    split_lexemes: dict[str, set[str]] = {}
    for split in SPLITS:
        section = design.get(split)
        if not isinstance(section, dict):
            failures.append(f"PROMPT_SPLIT_REQUIRED:{split}")
            continue
        rows = section.get("cases")
        if not isinstance(rows, list) or not rows:
            failures.append(f"PROMPT_CASES_REQUIRED:{split}")
            continue

        case_ids: set[str] = set()
        family_states: dict[str, set[str]] = collections.defaultdict(set)
        state_counts = collections.Counter()
        lexemes: set[str] = set()
        norm_rows: list[dict[str, str]] = []

        for idx, row in enumerate(rows):
            pfx = f"PROMPT_{split.upper()}_{idx}"
            if not isinstance(row, dict):
                failures.append(f"{pfx}_OBJECT_REQUIRED")
                continue
            values = {k: row.get(k) for k in (
                "case_id", "family_id", "state_id", "scaffold_prefix",
                "semantic_payload", "scaffold_suffix", "prompt",
            )}
            if not all(isinstance(values[k], str) and values[k] for k in values):
                failures.append(f"{pfx}_STRING_FIELDS_REQUIRED")
                continue
            case_id = values["case_id"]
            family_id = values["family_id"]
            state_id = values["state_id"]
            if case_id in case_ids:
                failures.append(f"{pfx}_DUPLICATE_CASE_ID")
            case_ids.add(case_id)
            if state_id not in STATES:
                failures.append(f"{pfx}_STATE_ID_INVALID")
                continue
            reconstructed = values["scaffold_prefix"] + values["semantic_payload"] + values["scaffold_suffix"]
            if reconstructed != values["prompt"]:
                failures.append(f"{pfx}_PROMPT_NOT_EXACT_SCAFFOLD_PLUS_PAYLOAD")
            full_words = _words(values["prompt"])
            forbidden = sorted(full_words & FORBIDDEN_MODEL_FACING_WORDS)
            if forbidden:
                failures.append(f"{pfx}_FORBIDDEN_MODEL_FACING_LEXEME:{','.join(forbidden)}")
            payload_words = _words(values["semantic_payload"])
            if not payload_words:
                failures.append(f"{pfx}_SEMANTIC_PAYLOAD_LEXEMES_REQUIRED")
            lexemes.update(payload_words)
            family_states[family_id].add(state_id)
            state_counts[state_id] += 1
            norm_rows.append({k: str(v) for k, v in values.items()})

        if len(family_states) < MIN_FAMILIES_PER_SPLIT:
            failures.append(f"{split.upper()}_MIN_FAMILIES_REQUIRED:{MIN_FAMILIES_PER_SPLIT}")
        for family_id, states in sorted(family_states.items()):
            if states != set(STATES):
                failures.append(f"{split.upper()}_FAMILY_MUST_CONTAIN_ALL_STATES:{family_id}")
        counts = [state_counts[s] for s in STATES]
        if not counts or min(counts, default=0) <= 0 or len(set(counts)) != 1:
            failures.append(f"{split.upper()}_STATE_COUNTS_MUST_BE_EXACTLY_BALANCED")

        normalized[split] = {
            "rows": norm_rows,
            "case_ids": case_ids,
            "families": set(family_states),
            "state_counts": dict(state_counts),
        }
        split_lexemes[split] = lexemes

    for i, left in enumerate(SPLITS):
        for right in SPLITS[i + 1:]:
            overlap = sorted(split_lexemes.get(left, set()) & split_lexemes.get(right, set()))
            if overlap:
                failures.append(f"LEXICAL_PAYLOAD_OVERLAP:{left.upper()}:{right.upper()}:{','.join(overlap[:32])}")
            if left in normalized and right in normalized:
                if normalized[left]["case_ids"] & normalized[right]["case_ids"]:
                    failures.append(f"CASE_ID_OVERLAP:{left.upper()}:{right.upper()}")
                if normalized[left]["families"] & normalized[right]["families"]:
                    failures.append(f"FAMILY_ID_OVERLAP:{left.upper()}:{right.upper()}")

    return normalized


def _validate_internal_readout(att: dict[str, Any], splits: dict[str, dict[str, Any]], failures: list[str]) -> dict[str, Any]:
    readout = att.get("internal_readout")
    if not isinstance(readout, dict):
        failures.append("INTERNAL_READOUT_REQUIRED")
        return {}
    if readout.get("fit_split") != "basis": failures.append("READOUT_MUST_FIT_BASIS_ONLY")
    if readout.get("tuning_split") != "calibration": failures.append("READOUT_MUST_TUNE_CALIBRATION_ONLY")
    if readout.get("evaluation_split") != "holdout": failures.append("READOUT_MUST_EVALUATE_HOLDOUT_ONLY")
    if readout.get("model_facing_state_labels") is not False: failures.append("READOUT_MODEL_FACING_STATE_LABELS_MUST_BE_FALSE")

    rows = readout.get("holdout_rows")
    if not isinstance(rows, list) or not rows:
        failures.append("READOUT_HOLDOUT_ROWS_REQUIRED")
        return {}
    expected_cases = splits.get("holdout", {}).get("case_ids", set())
    seen: set[str] = set()
    correct_by_state = collections.Counter()
    total_by_state = collections.Counter()
    family_correct: dict[str, list[bool]] = collections.defaultdict(list)
    correct = 0
    for idx, row in enumerate(rows):
        pfx = f"READOUT_ROW_{idx}"
        if not isinstance(row, dict):
            failures.append(f"{pfx}_OBJECT_REQUIRED"); continue
        cid, family, truth, scores = row.get("case_id"), row.get("family_id"), row.get("true_state_id"), row.get("scores")
        if not isinstance(cid, str) or cid not in expected_cases or cid in seen:
            failures.append(f"{pfx}_CASE_ID_INVALID_OR_DUPLICATE"); continue
        seen.add(cid)
        design_row = next((x for x in splits["holdout"]["rows"] if x["case_id"] == cid), None)
        if design_row is None or truth != design_row["state_id"] or family != design_row["family_id"]:
            failures.append(f"{pfx}_DESIGN_BINDING_MISMATCH"); continue
        if not isinstance(scores, dict) or set(scores) != set(STATES) or not all(_is_number(scores[s]) for s in STATES):
            failures.append(f"{pfx}_STATE_SCORE_TRIPLE_REQUIRED"); continue
        pred = max(STATES, key=lambda s: float(scores[s]))
        ok = pred == truth
        correct += int(ok)
        total_by_state[truth] += 1
        correct_by_state[truth] += int(ok)
        family_correct[family].append(ok)

    if seen != expected_cases:
        failures.append("READOUT_MUST_COVER_EXACT_HOLDOUT_CASE_UNIVERSE")
    n = sum(total_by_state.values())
    overall = correct / n if n else 0.0
    state_acc = {s: (correct_by_state[s] / total_by_state[s] if total_by_state[s] else 0.0) for s in STATES}
    perfect_families = sum(1 for vals in family_correct.values() if len(vals) == 3 and all(vals))
    if overall < MIN_HOLDOUT_BALANCED_ACCURACY: failures.append("READOUT_HOLDOUT_BALANCED_ACCURACY_BELOW_THRESHOLD")
    if any(state_acc[s] < MIN_HOLDOUT_STATE_ACCURACY for s in STATES): failures.append("READOUT_PER_STATE_ACCURACY_BELOW_THRESHOLD")
    if perfect_families < MIN_PERFECT_HOLDOUT_FAMILIES: failures.append("READOUT_TOO_FEW_PERFECT_HOLDOUT_FAMILIES")
    return {"holdout_accuracy": overall, "per_state_accuracy": state_acc, "perfect_holdout_families": perfect_families, "holdout_case_count": n}


def _validate_causal_internal(att: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    causal = att.get("causal_internal_state")
    if not isinstance(causal, dict): failures.append("CAUSAL_INTERNAL_STATE_REQUIRED"); return {}
    rows = causal.get("rows")
    if not isinstance(rows, list) or not rows: failures.append("CAUSAL_INTERNAL_ROWS_REQUIRED"); return {}

    grouped: dict[tuple[str, str], dict[str, float]] = collections.defaultdict(dict)
    target_hits = target_total = 0
    for idx, row in enumerate(rows):
        pfx = f"CAUSAL_INTERNAL_ROW_{idx}"
        if not isinstance(row, dict): failures.append(f"{pfx}_OBJECT_REQUIRED"); continue
        carrier, target, control, scores = row.get("carrier_case_id"), row.get("vector_state_id"), row.get("control"), row.get("scores")
        if not isinstance(carrier, str) or not carrier: failures.append(f"{pfx}_CARRIER_CASE_ID_REQUIRED"); continue
        if target not in STATES or control not in INTERVENTION_CONTROLS: failures.append(f"{pfx}_TARGET_OR_CONTROL_INVALID"); continue
        try:
            margin = _score_margin(scores, target); pred = max(STATES, key=lambda s: float(scores[s]))
        except Exception:
            failures.append(f"{pfx}_STATE_SCORE_TRIPLE_REQUIRED"); continue
        key = (carrier, target)
        if control in grouped[key]: failures.append(f"{pfx}_DUPLICATE_CONTROL")
        grouped[key][control] = margin
        if control == "TARGET": target_total += 1; target_hits += int(pred == target)

    deltas = {c: [] for c in ("NULL", "SHUFFLED", "SIGN_FLIP")}
    for (carrier, target), controls in grouped.items():
        if set(controls) != set(INTERVENTION_CONTROLS):
            failures.append(f"CAUSAL_INTERNAL_CONTROL_SET_INCOMPLETE:{carrier}:{target}"); continue
        for control in deltas: deltas[control].append(controls["TARGET"] - controls[control])
    carriers = {carrier for carrier, _ in grouped}
    for carrier in sorted(carriers):
        if {target for c, target in grouped if c == carrier} != set(STATES): failures.append(f"CAUSAL_INTERNAL_CARRIER_MUST_TEST_ALL_TARGETS:{carrier}")
    hit_rate = target_hits / target_total if target_total else 0.0
    mean_deltas = {c: (sum(v) / len(v) if v else None) for c, v in deltas.items()}
    if hit_rate < MIN_CAUSAL_TARGET_HIT_RATE: failures.append("CAUSAL_INTERNAL_TARGET_HIT_RATE_BELOW_THRESHOLD")
    for control, value in mean_deltas.items():
        if value is None or value < MIN_MEAN_TARGET_MARGIN_VS_CONTROL: failures.append(f"CAUSAL_INTERNAL_MARGIN_VS_{control}_BELOW_THRESHOLD")
    return {"target_hit_rate": hit_rate, "mean_target_margin_delta": mean_deltas, "carrier_count": len(carriers)}


def _validate_behavior_counterbalance(att: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    behavior = att.get("opaque_code_behavior")
    if not isinstance(behavior, dict): failures.append("OPAQUE_CODE_BEHAVIOR_REQUIRED"); return {}
    rows = behavior.get("rows")
    if not isinstance(rows, list) or not rows: failures.append("OPAQUE_CODE_BEHAVIOR_ROWS_REQUIRED"); return {}

    grouped: dict[tuple[str, str, str], dict[str, float]] = collections.defaultdict(dict)
    target_code_counts = collections.Counter()
    target_row_code: dict[tuple[str, str, str], str] = {}
    for idx, row in enumerate(rows):
        pfx = f"OPAQUE_ROW_{idx}"
        if not isinstance(row, dict): failures.append(f"{pfx}_OBJECT_REQUIRED"); continue
        carrier, target, mapping_id, control = row.get("carrier_case_id"), row.get("vector_state_id"), row.get("mapping_id"), row.get("control")
        state_to_code, logits = row.get("state_to_code"), row.get("code_logits")
        if not isinstance(carrier, str) or not carrier or not isinstance(mapping_id, str) or not mapping_id:
            failures.append(f"{pfx}_CARRIER_AND_MAPPING_ID_REQUIRED"); continue
        if target not in STATES or control not in INTERVENTION_CONTROLS: failures.append(f"{pfx}_TARGET_OR_CONTROL_INVALID"); continue
        if not isinstance(state_to_code, dict) or set(state_to_code) != set(STATES) or set(state_to_code.values()) != set(CODES):
            failures.append(f"{pfx}_STATE_TO_CODE_MUST_BE_BIJECTION"); continue
        try: margin = _code_margin(logits, state_to_code[target])
        except Exception: failures.append(f"{pfx}_CODE_LOGIT_TRIPLE_REQUIRED"); continue
        key = (carrier, target, mapping_id)
        if control in grouped[key]: failures.append(f"{pfx}_DUPLICATE_CONTROL")
        grouped[key][control] = margin
        if control == "TARGET":
            target_code_counts[(target, state_to_code[target])] += 1
            target_row_code[key] = state_to_code[target]

    deltas_by_code: dict[str, list[float]] = {c: [] for c in CODES}
    deltas_vs_control = {c: [] for c in ("NULL", "SHUFFLED", "SIGN_FLIP")}
    for key, controls in grouped.items():
        carrier, target, mapping_id = key
        if set(controls) != set(INTERVENTION_CONTROLS):
            failures.append(f"OPAQUE_CONTROL_SET_INCOMPLETE:{carrier}:{target}:{mapping_id}"); continue
        code = target_row_code.get(key)
        if code not in CODES: failures.append(f"OPAQUE_TARGET_ROW_MISSING:{carrier}:{target}:{mapping_id}"); continue
        deltas_by_code[code].append(controls["TARGET"] - controls["NULL"])
        for ctrl in deltas_vs_control: deltas_vs_control[ctrl].append(controls["TARGET"] - controls[ctrl])

    for target in STATES:
        counts = [target_code_counts[(target, code)] for code in CODES]
        if min(counts, default=0) <= 0 or len(set(counts)) != 1: failures.append(f"OPAQUE_TARGET_CODE_MAPPING_NOT_EXACTLY_COUNTERBALANCED:{target}")
    mean_vs = {c: (sum(v) / len(v) if v else None) for c, v in deltas_vs_control.items()}
    for ctrl, value in mean_vs.items():
        if value is None or value < MIN_BEHAVIOR_TARGET_MARGIN_VS_CONTROL: failures.append(f"OPAQUE_BEHAVIOR_MARGIN_VS_{ctrl}_BELOW_THRESHOLD")
    code_means = {c: (sum(v) / len(v) if v else None) for c, v in deltas_by_code.items()}
    if any(v is None or not math.isfinite(v) or v <= 0 for v in code_means.values()):
        failures.append("OPAQUE_EFFECT_MUST_REPLICATE_FOR_EACH_CODE_IDENTITY")
    elif max(v for v in code_means.values() if v is not None) - min(v for v in code_means.values() if v is not None) > MAX_CODE_DELTA_RANGE:
        failures.append("OPAQUE_EFFECT_TOO_CODE_IDENTITY_DEPENDENT")
    return {
        "target_code_counts": {f"{s}:{c}": target_code_counts[(s, c)] for s in STATES for c in CODES},
        "mean_target_margin_delta": mean_vs,
        "mean_target_vs_null_by_code": code_means,
        "factorial_group_count": len(grouped),
    }


def _validate_support_bridge(att: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    bridge = att.get("support_matched_bridge")
    if bridge is None: return {"pass": False, "status": "NOT_PROVIDED_NATIVE_SCOPE_ONLY"}
    if not isinstance(bridge, dict): failures.append("SUPPORT_MATCHED_BRIDGE_OBJECT_REQUIRED"); return {"pass": False, "status": "INVALID"}
    required = {
        "native_scope": PINNED_SCOPE, "comparison_scope": PINNED_SCOPE,
        "same_layer": True, "same_prompt_case_universe": True,
        "same_vector_digests": True, "same_metric": True, "bridge_pass": True,
    }
    local_fail = []
    for key, expected in required.items():
        if bridge.get(key) != expected: local_fail.append(f"SUPPORT_MATCHED_BRIDGE_MISMATCH:{key}")
    failures.extend(local_fail)
    return {"pass": not local_fail, "status": "PASS" if not local_fail else "FAIL"}


def adjudicate(attestation: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(attestation, dict): attestation = {}; failures.append("ATTESTATION_OBJECT_REQUIRED")
    if attestation.get("schema") != ATTESTATION_SCHEMA: failures.append("ATTESTATION_SCHEMA_MISMATCH")

    _validate_intervention_contract(attestation, failures)
    splits = _validate_prompt_splits(attestation, failures)
    readout = _validate_internal_readout(attestation, splits, failures)
    causal = _validate_causal_internal(attestation, failures)
    behavior = _validate_behavior_counterbalance(attestation, failures)

    bridge_failures_before = len(failures)
    bridge = _validate_support_bridge(attestation, failures)
    bridge_invalid = len(failures) > bridge_failures_before
    native_failures = list(failures)
    if bridge_invalid:
        native_failures = [f for f in failures if not f.startswith("SUPPORT_MATCHED_BRIDGE_")]

    native_candidate = not native_failures
    cross_candidate = native_candidate and bridge.get("pass") is True and not bridge_invalid
    return {
        "schema": SCHEMA,
        "native_broadcast_abstract_state_candidate": native_candidate,
        "cross_intervention_equivalence_candidate": cross_candidate,
        "internal_readout": readout,
        "causal_internal_state": causal,
        "opaque_code_behavior": behavior,
        "support_matched_bridge": bridge,
        "failures": sorted(set(failures)),
        "native_scope_failures": sorted(set(native_failures)),
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "claim_scope": "NATIVE_QWEN06_Q8_LLAMA_CPP_CVEC_BROADCAST_ABSTRACT_STATE_ONLY" if native_candidate else "BLOCKED",
        "evidence_boundary": (
            "PASS at native_broadcast_abstract_state_candidate means the supplied evidence envelope survives exact "
            "model-facing label firewalling, split-disjoint state-varying lexemes, balanced held-out internal decoding, "
            "matched causal internal-state controls, and opaque-code counterbalance under the pinned native llama.cpp "
            "cvec broadcast scope. It does NOT make the historical last-token witness causally identical. "
            "cross_intervention_equivalence_candidate is separate and requires an explicit support-matched bridge. "
            "This source-only gate never mints runtime or canonical credit."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("attestation", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try: data = json.loads(args.attestation.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: data = {"_invalid": type(exc).__name__}
    result = adjudicate(data)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(text, encoding="utf-8")
    else: print(text, end="")
    return 0 if result["native_broadcast_abstract_state_candidate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
