#!/usr/bin/env python3
"""Finite evaluator-readiness audit for the stateful Frank reward update contract.

This checker does NOT define reward dynamics. It asks whether the authoritative candidate source
contains enough explicit transition/receipt semantics to make a deterministic evaluator possible
without importing numerical choices from a research-only reference implementation.

A declared symbol is not automatically a scientifically validated mechanism. This gate is only a
necessary completeness condition. Missing definitions keep runtime binding and execution closed.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Callable, Any

SCHEMA = "ClayCodeRewardTransitionReadiness/v1-research"
DOMAIN = b"ClayCodeRewardTransitionReadiness/v1-research\x00"


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    category: str
    description: str
    predicate: Callable[[str], bool]


def _definition(name: str) -> Callable[[str], bool]:
    pat = re.compile(rf"(?m)^\s*(?:rule|fn|parameter)\s+{re.escape(name)}(?:\s*\(|\s*\[|\s*=|\s+)")
    return lambda text: bool(pat.search(text))


def _regex(pattern: str) -> Callable[[str], bool]:
    rx = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
    return lambda text: bool(rx.search(text))


OBLIGATIONS = (
    Obligation("material_admission", "ADMISSION", "verified outcome + causal-credit admission predicate", _definition("material_reward_admitted")),
    Obligation("material_learning_weight", "ADMISSION", "deterministic material learning weight", _definition("material_learning_weight")),
    Obligation("horizon_rates", "PREDICTION", "FAST/MEDIUM/SLOW learning rates", _regex(r"parameter\s+rate\[FAST\]\s*=\s*[-+0-9.]+[\s\S]*parameter\s+rate\[MEDIUM\]\s*=\s*[-+0-9.]+[\s\S]*parameter\s+rate\[SLOW\]\s*=\s*[-+0-9.]+")),
    Obligation("phasic_mix_weights", "PHASIC", "explicit horizon mixture weights", _definition("phasic_mix")),
    Obligation("observed_value", "PREDICTION", "exact mapping from admitted evidence/state to observed value", _definition("observed_value")),
    Obligation("bounded_update", "PREDICTION", "exact prediction-mean update operator", _definition("bounded_update")),
    Obligation("bounded_distribution_update", "PREDICTION", "exact uncertainty/variance update operator", _definition("bounded_distribution_update")),
    Obligation("normalize_by_prediction_uncertainty", "PHASIC", "exact uncertainty normalization including floors/clamps", _definition("normalize_by_prediction_uncertainty")),
    Obligation("robust_mix", "PHASIC", "exact robust horizon mixing operator", _definition("robust_mix")),
    Obligation("clamp01", "STDLIB", "exact clamp01 semantics or explicitly bound stdlib contract", _definition("clamp01")),
    Obligation("exploration_nudge", "CONTROL", "deterministic exploration-nudge function, not only an upper bound", _definition("exploration_nudge")),
    Obligation("tonic_transition", "STATE_TRANSITION", "exact tonic state transition", _regex(r"^\s*(?:rule|fn)\s+[^\n]*tonic[^\n]*(?:<-|=)[^\n]+$")),
    Obligation("habituation_transition", "STATE_TRANSITION", "exact habituation update and recovery transition", _regex(r"^\s*(?:rule|fn)\s+habituation(?:_transition|_update|\s*\()[^\n]*(?:<-|=)[^\n]+$")),
    Obligation("opponent_transition", "STATE_TRANSITION", "exact opponent-process state transition", _regex(r"^\s*(?:rule|fn)\s+opponent(?:_process)?(?:_transition|_update|\s*\()[^\n]*(?:<-|=)[^\n]+$")),
    Obligation("admitted_events_transition", "STATE_TRANSITION", "exact admitted_events counter transition", _regex(r"^\s*(?:rule|fn)\s+[^\n]*admitted_events[^\n]*(?:<-|next|increment|\+\s*1)[^\n]*$")),
    Obligation("last_phasic_transition", "STATE_TRANSITION", "exact last_phasic state transition", _regex(r"^\s*(?:rule|fn)\s+[^\n]*last_phasic[^\n]*(?:<-|=)[^\n]+$")),
    Obligation("state_epoch_transition", "STATE_IDENTITY", "post-update state_epoch successor/increment rule", _regex(r"^\s*(?:rule|fn)\s+[^\n]*state_epoch[^\n]*(?:<-|next_epoch|successor|increment|\+\s*1)[^\n]*$")),
    Obligation("veto_threshold", "CONTROL", "numerically or externally bound safety veto threshold", _definition("veto_threshold")),
    Obligation("brake_threshold", "CONTROL", "numerically or externally bound resource brake threshold", _definition("brake_threshold")),
    Obligation("receipt_projection", "RECEIPT", "deterministic RewardPlasticityReceipt construction/projection", _regex(r"^\s*(?:rule|fn)\s+(?:reward_plasticity_receipt|build_reward_plasticity_receipt|receipt_projection)\b")),
    Obligation("receipt_provenance", "RECEIPT", "exact provenance construction for RewardPlasticityReceipt", _regex(r"^\s*(?:rule|fn)\s+[^\n]*provenance[^\n]*(?:<-|=)[^\n]+$")),
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def audit(authoritative_source: str, *, reference_source: str | None = None) -> dict[str, Any]:
    rows = []
    for obligation in OBLIGATIONS:
        declared = bool(obligation.predicate(authoritative_source))
        rows.append({
            "obligation_id": obligation.obligation_id,
            "category": obligation.category,
            "description": obligation.description,
            "status": "EXPLICITLY_DECLARED" if declared else "MISSING_EXACT_DEFINITION",
        })
    missing = [r for r in rows if r["status"] != "EXPLICITLY_DECLARED"]
    core = {
        "schema": SCHEMA,
        "authoritative_source_sha256": _sha(authoritative_source),
        "obligations": rows,
        "summary": {
            "required": len(rows),
            "explicitly_declared": len(rows) - len(missing),
            "missing_exact_definition": len(missing),
            "deterministic_evaluator_ready": not missing,
            "runtime_binding_admitted": False,
            "execution_admitted": False,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
        "reference_evidence": {
            "present": reference_source is not None,
            "source_sha256": _sha(reference_source) if reference_source is not None else None,
            "classification": "RESEARCH_REFERENCE_NONAUTHORITATIVE" if reference_source is not None else "NONE",
            "may_fill_missing_authoritative_definitions": False,
            "signals_concrete_candidate_choices": {
                "variance_alpha": bool(reference_source and "VAR_ALPHA" in reference_source),
                "tonic_alpha": bool(reference_source and "TONIC_ALPHA" in reference_source),
                "uncertainty_floor_or_mix": bool(reference_source and "0.65 * err" in reference_source),
                "safety_veto_numeric": bool(reference_source and "< -0.18" in reference_source),
                "resource_brake_numeric": bool(reference_source and "< -0.22" in reference_source),
            },
        },
        "invariants": {
            "research_reference_mints_production_semantics": "FORBIDDEN",
            "missing_transition_definition_executes": "FORBIDDEN",
            "stateful_call_without_epoch_transition_executes": "FORBIDDEN",
            "bounded_only_nondeterminism_counts_as_exact_evaluator": "FORBIDDEN",
        },
        "promotion": "NONE",
    }
    receipt_hash = hashlib.sha256(DOMAIN + _stable(core)).hexdigest()
    return {**core, "readiness_receipt_sha256": receipt_hash}


def require_evaluator_ready(report: dict[str, Any]) -> None:
    summary = report.get("summary") or {}
    if not summary.get("deterministic_evaluator_ready"):
        missing = [r.get("obligation_id") for r in report.get("obligations", []) if r.get("status") != "EXPLICITLY_DECLARED"]
        raise ValueError(f"reward evaluator remains fail-closed; missing exact definitions: {missing}")
    if summary.get("runtime_binding_admitted") or summary.get("execution_admitted"):
        raise ValueError("readiness audit cannot mint runtime/execution authority")
