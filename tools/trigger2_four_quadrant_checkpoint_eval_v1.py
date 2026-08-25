#!/usr/bin/env python3
"""Deterministic Trigger-2 four-quadrant checkpoint evaluation freeze.

Source-only evaluation infrastructure. This module performs no model, provider,
VPS, or training execution. It creates a frozen logical-case manifest and grades
strict machine-readable model outputs after a separately authorized future run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

SCHEMA = "CLAY_TRIGGER2_FOUR_QUADRANT_CHECKPOINT_EVAL/v1"
OUTPUT_SCHEMA = "XENO_EVAL_DECISION/v1"
SEED = 202608260405
FAMILIES_PER_AXIS = 128
FROZEN_MANIFEST_SHA256 = "9e9a2a421cdaa9207783060b6b127fa4ca26bf25d9415b22730812f31229d57d"

DECISIONS = (
    "ANSWER_CURRENT_EVIDENCE",
    "ABSTAIN_UNKNOWN",
    "TRUST_CURRENT_DB_OVER_SIM",
    "REJECT_STALE_DB_AND_REREAD",
)
ACTIONS = (
    "ANSWER_CANDIDATE",
    "ABSTAIN_UNKNOWN",
    "TRUST_DB",
    "REREAD_RECOMPUTE",
)

BLOCKS = (
    {"block_id": "B1", "family_start": 0, "family_stop": 32, "cumulative_cases_per_axis": 64},
    {"block_id": "B2", "family_start": 32, "family_stop": 64, "cumulative_cases_per_axis": 128},
    {"block_id": "B3", "family_start": 64, "family_stop": 128, "cumulative_cases_per_axis": 256},
)

DOMAINS = (
    "orbital_lab", "ceramic_line", "river_sensor", "archive_index",
    "alloy_cell", "botany_rig", "optics_bench", "acoustic_array",
)
PREDICATES = (
    "phase", "density", "status", "class", "mode", "value", "state", "marker",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return _sha256_bytes(canonical_json_bytes(value))


def _token(rng: random.Random, prefix: str) -> str:
    return f"{prefix}{rng.randrange(10000, 99999)}"


def _block_for_family(index: int) -> str:
    for block in BLOCKS:
        if block["family_start"] <= index < block["family_stop"]:
            return str(block["block_id"])
    raise ValueError(index)


def _common_world(rng: random.Random, axis: str, index: int) -> Dict[str, str]:
    return {
        "world_id": f"T2FQ-{axis}-{index:03d}-{_token(rng, 'W')}",
        "domain": DOMAINS[rng.randrange(len(DOMAINS))],
        "entity": _token(rng, "E"),
        "predicate": PREDICATES[rng.randrange(len(PREDICATES))],
        "truth_value": _token(rng, "V"),
        "distractor_value": _token(rng, "D"),
    }


def _input_base(world: Mapping[str, str], evidence: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    return {
        "task": "Resolve the requested value using typed evidence without minting facts from simulation or stale/unbound state.",
        "query": {"entity": world["entity"], "predicate": world["predicate"]},
        "evidence": list(evidence),
        "output_schema": OUTPUT_SCHEMA,
        "allowed_decisions": list(DECISIONS),
        "allowed_actions": list(ACTIONS),
    }


def _case(
    *,
    case_id: str,
    family_id: str,
    axis: str,
    quadrant: str,
    block_id: str,
    model_input: Dict[str, Any],
    decision: str,
    action: str,
    answer: str | None,
    hidden_truth: str,
) -> Dict[str, Any]:
    return {
        "schema": SCHEMA,
        "case_id": case_id,
        "family_id": family_id,
        "axis": axis,
        "quadrant": quadrant,
        "block_id": block_id,
        "model_input": model_input,
        "gold": {
            "decision": decision,
            "action": action,
            "answer": answer,
        },
        "audit_only": {
            "hidden_truth": hidden_truth,
            "model_input_sha256": canonical_sha256(model_input),
        },
    }


def generate_manifest(seed: int = SEED, families_per_axis: int = FAMILIES_PER_AXIS) -> List[Dict[str, Any]]:
    if families_per_axis != 128:
        raise ValueError("v1 freeze requires exactly 128 matched families per axis")
    rng = random.Random(seed)
    cases: List[Dict[str, Any]] = []

    for i in range(families_per_axis):
        world = _common_world(rng, "A", i)
        family_id = f"T2FQ-A-{i:03d}"
        block_id = _block_for_family(i)
        current_evidence = [{
            "source": "S0_DB",
            "status": "CURRENT_BOUND",
            "generation": f"G{1000 + i}",
            "provenance": "CANONICAL_OBSERVATION",
            "entity": world["entity"],
            "predicate": world["predicate"],
            "value": world["truth_value"],
        }]
        missing_evidence = [{
            "source": "S0_DB",
            "status": "MISSING",
            "generation": f"G{1000 + i}",
            "provenance": "NO_OBSERVATION",
            "entity": world["entity"],
            "predicate": world["predicate"],
        }]
        cases.append(_case(
            case_id=f"{family_id}-Q1",
            family_id=family_id,
            axis="EPISTEMIC_ANSWERABILITY",
            quadrant="Q1_ANSWERABLE_CURRENT_BOUND",
            block_id=block_id,
            model_input=_input_base(world, current_evidence),
            decision="ANSWER_CURRENT_EVIDENCE",
            action="ANSWER_CANDIDATE",
            answer=world["truth_value"],
            hidden_truth=world["truth_value"],
        ))
        cases.append(_case(
            case_id=f"{family_id}-Q2",
            family_id=family_id,
            axis="EPISTEMIC_ANSWERABILITY",
            quadrant="Q2_UNANSWERABLE_MISSING",
            block_id=block_id,
            model_input=_input_base(world, missing_evidence),
            decision="ABSTAIN_UNKNOWN",
            action="ABSTAIN_UNKNOWN",
            answer=None,
            hidden_truth=world["truth_value"],
        ))

    stale_modes = ("STALE_EPOCH", "WRONG_GENERATION", "UNBOUND_PROVENANCE", "CONTRADICTED")
    for i in range(families_per_axis):
        world = _common_world(rng, "B", i)
        family_id = f"T2FQ-B-{i:03d}"
        block_id = _block_for_family(i)
        generation = f"G{2000 + i}"
        current_evidence = [
            {
                "source": "S0_DB",
                "status": "CURRENT_BOUND",
                "generation": generation,
                "provenance": "CANONICAL_OBSERVATION",
                "entity": world["entity"],
                "predicate": world["predicate"],
                "value": world["truth_value"],
            },
            {
                "source": "S2_SIMULATION",
                "status": "NONCANONICAL_GENERATED",
                "generation": generation,
                "provenance": "MODEL_SIMULATION",
                "entity": world["entity"],
                "predicate": world["predicate"],
                "value": world["distractor_value"],
            },
        ]
        stale_mode = stale_modes[i % len(stale_modes)]
        stale_evidence = [
            {
                "source": "S0_DB",
                "status": stale_mode,
                "generation": f"G{1999 + i}" if stale_mode != "WRONG_GENERATION" else f"G{9000 + i}",
                "provenance": "CANONICAL_OBSERVATION" if stale_mode != "UNBOUND_PROVENANCE" else "UNBOUND",
                "entity": world["entity"],
                "predicate": world["predicate"],
                "value": world["truth_value"],
            },
            {
                "source": "S2_SIMULATION",
                "status": "NONCANONICAL_GENERATED",
                "generation": generation,
                "provenance": "MODEL_SIMULATION",
                "entity": world["entity"],
                "predicate": world["predicate"],
                "value": world["distractor_value"],
            },
        ]
        cases.append(_case(
            case_id=f"{family_id}-Q3",
            family_id=family_id,
            axis="DB_VS_SIMULATION_AUTHORITY",
            quadrant="Q3_CURRENT_DB_VS_SIM",
            block_id=block_id,
            model_input=_input_base(world, current_evidence),
            decision="TRUST_CURRENT_DB_OVER_SIM",
            action="TRUST_DB",
            answer=world["truth_value"],
            hidden_truth=world["truth_value"],
        ))
        cases.append(_case(
            case_id=f"{family_id}-Q4",
            family_id=family_id,
            axis="DB_VS_SIMULATION_AUTHORITY",
            quadrant="Q4_STALE_UNBOUND_DB",
            block_id=block_id,
            model_input=_input_base(world, stale_evidence),
            decision="REJECT_STALE_DB_AND_REREAD",
            action="REREAD_RECOMPUTE",
            answer=None,
            hidden_truth=world["truth_value"],
        ))

    rng.shuffle(cases)
    return cases


def assert_frozen_manifest(cases: Sequence[Mapping[str, Any]]) -> None:
    observed = canonical_sha256(list(cases))
    if observed != FROZEN_MANIFEST_SHA256:
        raise ValueError(f"frozen manifest drift: {observed} != {FROZEN_MANIFEST_SHA256}")


def manifest_envelope(cases: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    assert_frozen_manifest(cases)
    counts: Dict[str, int] = {}
    axis_counts: Dict[str, int] = {}
    for case in cases:
        counts[str(case["quadrant"])] = counts.get(str(case["quadrant"]), 0) + 1
        axis_counts[str(case["axis"])] = axis_counts.get(str(case["axis"]), 0) + 1
    return {
        "schema": SCHEMA,
        "seed": SEED,
        "case_count": len(cases),
        "family_count": len({str(c["family_id"]) for c in cases}),
        "quadrant_counts": dict(sorted(counts.items())),
        "axis_counts": dict(sorted(axis_counts.items())),
        "blocks": list(BLOCKS),
        "cases_sha256": FROZEN_MANIFEST_SHA256,
        "cases": list(cases),
    }


def _strict_output(raw: str) -> Dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("output must be one JSON object")
    required = {"schema", "decision", "action", "answer"}
    if set(value) != required:
        raise ValueError(f"output keys must be exactly {sorted(required)}")
    if value["schema"] != OUTPUT_SCHEMA:
        raise ValueError("wrong output schema")
    if value["decision"] not in DECISIONS:
        raise ValueError("invalid decision")
    if value["action"] not in ACTIONS:
        raise ValueError("invalid action")
    if value["answer"] is not None and not isinstance(value["answer"], str):
        raise ValueError("answer must be string or null")
    return value


def grade_raw(case: Mapping[str, Any], raw: str) -> Dict[str, Any]:
    raw_sha256 = _sha256_bytes(raw.encode("utf-8"))
    try:
        output = _strict_output(raw)
    except Exception as exc:
        return {
            "case_id": case["case_id"],
            "raw_sha256": raw_sha256,
            "parse_ok": False,
            "decision_ok": False,
            "action_ok": False,
            "answer_ok": False,
            "full_ok": False,
            "error": str(exc),
        }
    gold = case["gold"]
    decision_ok = output["decision"] == gold["decision"]
    action_ok = output["action"] == gold["action"]
    answer_ok = output["answer"] == gold["answer"]
    return {
        "case_id": case["case_id"],
        "raw_sha256": raw_sha256,
        "parse_ok": True,
        "decision_ok": decision_ok,
        "action_ok": action_ok,
        "answer_ok": answer_ok,
        "full_ok": bool(decision_ok and action_ok and answer_ok),
        "error": None,
    }


def challenger_decision_accuracy(cases: Sequence[Mapping[str, Any]], fixed_decision: str) -> float:
    if fixed_decision not in DECISIONS:
        raise ValueError(fixed_decision)
    return sum(c["gold"]["decision"] == fixed_decision for c in cases) / len(cases)


def freeze_summary(cases: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    assert_frozen_manifest(cases)
    by_decision = {d: sum(c["gold"]["decision"] == d for c in cases) for d in DECISIONS}
    challengers = {d: challenger_decision_accuracy(cases, d) for d in DECISIONS}
    return {
        "schema": "CLAY_TRIGGER2_FOUR_QUADRANT_CHECKPOINT_EVAL_FREEZE_SUMMARY/v1",
        "manifest_sha256": FROZEN_MANIFEST_SHA256,
        "case_count": len(cases),
        "family_count": len({c["family_id"] for c in cases}),
        "decision_counts": by_decision,
        "constant_decision_challengers": challengers,
        "max_constant_decision_accuracy": max(challengers.values()),
        "prospective_stopping": {
            "opened_order": ["B1", "B2", "B3"],
            "cumulative_cases_per_axis": [64, 128, 256],
            "law": "Open the next precommitted block only if preregistered decision criteria remain unresolved; never alter families, grader, renderer policy or margins after candidate outputs are observed.",
        },
        "runtime_credit": 0,
        "checkpoint_selection_credit": 0,
        "training_credit": 0,
    }


def write_freeze(output: Path) -> None:
    cases = generate_manifest()
    envelope = manifest_envelope(cases)
    output.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    cases = generate_manifest()
    args.output.write_text(json.dumps(manifest_envelope(cases), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.summary:
        args.summary.write_text(json.dumps(freeze_summary(cases), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
