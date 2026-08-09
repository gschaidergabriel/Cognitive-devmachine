#!/usr/bin/env python3
"""Non-promotional red-team probes for current H1 reference integration.

These probes are deliberately small. They do not assert the correct implementation
strategy; they expose semantic disagreements that must be resolved before one H1 oracle
is frozen.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
REF = ROOT / "research_entity" / "harness" / "reference"
if str(REF) not in sys.path:
    sys.path.insert(0, str(REF))

from active_assembly import AssemblyPacket, compile_active_assembly
from loop_dynamics_quality_gate import LoopDynamicsReadout as QualityReadout
from loop_dynamics_quality_gate import decide_recurrence as quality_decide
from loop_dynamics_reference import LoopDynamicsReadout as DynamicsReadout
from loop_dynamics_reference import decide_recurrence as dynamics_decide


def active_assembly_same_ancestry_conflict() -> dict:
    candidates = [
        AssemblyPacket(
            "yes", "famA", "knowledge", .90, .90, .50, .10, 7,
            "claim:k", "yes", "reexpand:yes"
        ),
        AssemblyPacket(
            "no", "famA", "knowledge", .89, .90, .50, .10, 7,
            "claim:k", "no", "reexpand:no"
        ),
    ]
    out = compile_active_assembly(
        candidates, current_epoch=7, max_items=8, max_per_ancestry=1
    )
    selected = [x["packet_id"] for x in out["items"]]
    values = [x.get("claim_value") for x in out["items"] if x.get("claim_key") == "claim:k"]
    both_visible = set(values) == {"yes", "no"}
    return {
        "probe": "active_assembly_same_ancestry_conflict",
        "selected": selected,
        "claim_values_visible": values,
        "both_conflicting_values_visible": both_visible,
        "interpretation": (
            "PASS if both propositions remain cognitively observable directly or through "
            "an explicit deterministic conflict capsule; shared ancestry must suppress "
            "independent-evidence credit, not necessarily proposition visibility."
        ),
    }


def quality_gate_high_delta_low_residual() -> dict:
    r = QualityReadout(
        loop_id="gwt.reentry",
        state_epoch=17,
        state_delta_norm=.90,
        residual_pressure=.01,
        low_delta_streak=0,
        oscillation_indicator=0.0,
        marginal_utility_next=.03,
        residual_estimator_id="residual-v1",
        residual_estimator_version="1",
        residual_uncertainty=.01,
        measurement_age_cycles=0,
    )
    out = quality_decide(r)
    return {
        "probe": "quality_gate_high_delta_low_residual",
        "decision": out.decision,
        "candidate_convergence": out.decision == "HALT_CANDIDATE_CONVERGED",
        "interpretation": "High state delta must not become candidate fixed-point convergence from low residual alone.",
    }


def dynamics_reference_high_uncertainty() -> dict:
    r = DynamicsReadout(
        loop_id="l1",
        loop_family="reasoning",
        timescale="turn",
        state_epoch=7,
        state_delta_norm=.02,
        residual_pressure=.04,
        recurrence_count=2,
        recurrence_budget=8,
        marginal_utility_next=-.02,
        uncertainty=1.0,
    )
    out = dynamics_decide(r)
    return {
        "probe": "dynamics_reference_high_uncertainty",
        "regime": out.regime.value,
        "decision": out.decision.value,
        "candidate_convergence": out.decision.value == "HALT_CANDIDATE_CONVERGED",
        "interpretation": (
            "The fused H1 controller should not permit candidate convergence when the "
            "readout it depends on is maximally uncertain or stale."
        ),
    }


def schema_fork() -> dict:
    quality_fields = set(QualityReadout.__dataclass_fields__)
    dynamics_fields = set(DynamicsReadout.__dataclass_fields__)
    return {
        "probe": "loop_controller_schema_fork",
        "quality_only": sorted(quality_fields - dynamics_fields),
        "dynamics_only": sorted(dynamics_fields - quality_fields),
        "shared": sorted(quality_fields & dynamics_fields),
        "interpretation": "Useful dimensions in either line should be adjudicated into one frozen H1 contract rather than silently dropped.",
    }


def main() -> int:
    result = {
        "schema_version": "1.0",
        "evidence_class": "H1_REFERENCE_INTEGRATION_REDTEAM_NOT_RELEASE_ACCEPTANCE",
        "promotion": "NONE",
        "probes": [
            active_assembly_same_ancestry_conflict(),
            quality_gate_high_delta_low_residual(),
            dynamics_reference_high_uncertainty(),
            schema_fork(),
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    # Probe findings are data, not CI pass/fail policy. Return zero so a caller can
    # compare the output against a versioned acceptance oracle explicitly.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
