#!/usr/bin/env python3
"""GO diagnostic: provenance-broken re-entry must not masquerade as closed GWT re-entry.

Diagnostic only. This intentionally measures the current reference behavior before a repair.
It performs no external effect and mints no execution/truth authority.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "harness" / "reference"))

from workspace_episode import (  # noqa: E402
    BasisWitness,
    ReceiverPolicy,
    WorkspaceCandidate,
    WorkspaceIntervention,
    run_workspace_episode,
)


def episode(*, shuffle: bool):
    return run_workspace_episode(
        episode_id="go-oob-provenance-closure",
        witness=BasisWitness(11, "sem-11", "ver-11", "trace-11"),
        candidates=[WorkspaceCandidate("winner", 0.91, {"intent": "inspect"}, 11, "go-oob")],
        receivers=[ReceiverPolicy("memory"), ReceiverPolicy("planner")],
        ignition_threshold=0.55,
        intervention=WorkspaceIntervention(
            intervention_id="PROVENANCE_BROKEN_FULL_RECEIVER_FALSE_CLOSURE" if shuffle else "MATCHED_TRUTHFUL_CONTROL",
            shuffle_reentry=shuffle,
        ),
    )


def main() -> None:
    control = episode(shuffle=False)
    broken = episode(shuffle=True)

    assert control["outcome"] == broken["outcome"]
    assert control["outcome"]["causal_use_count"] == 2
    assert broken["outcome"]["causal_use_count"] == 2
    assert control["reentry"]["source_binding_status"] == "PROVENANCE_BOUND"
    assert broken["reentry"]["source_binding_status"] == "PROVENANCE_BROKEN"
    assert control["closure_status"] == "REENTRY_CLOSED"

    false_closure_reproduced = broken["closure_status"] == "REENTRY_CLOSED"
    false_fraction_reproduced = broken["integration_readout"]["reentry_fraction"] == 1.0

    result = {
        "schema_version": "1.0",
        "experiment": "PROVENANCE_BROKEN_FULL_RECEIVER_FALSE_CLOSURE",
        "classification": (
            "REPRODUCED_PROVENANCE_BROKEN_FALSE_CLOSURE"
            if false_closure_reproduced and false_fraction_reproduced
            else "NOT_REPRODUCED_OR_ALREADY_REPAIRED"
        ),
        "matched_control": {
            "closure_status": control["closure_status"],
            "source_binding_status": control["reentry"]["source_binding_status"],
            "reentry_fraction": control["integration_readout"]["reentry_fraction"],
        },
        "oob": {
            "closure_status": broken["closure_status"],
            "source_binding_status": broken["reentry"]["source_binding_status"],
            "reentry_fraction": broken["integration_readout"]["reentry_fraction"],
        },
        "same_outcome": control["outcome"] == broken["outcome"],
        "external_effect_performed": False,
        "execution_authority": False,
        "truth_authority": False,
        "promotion": "NONE",
    }
    print(json.dumps(result, sort_keys=True))

    # A successful diagnostic run means we obtained an unambiguous classification,
    # not that the current semantics are correct. The JSON result carries the verdict.
    assert result["classification"] in {
        "REPRODUCED_PROVENANCE_BROKEN_FALSE_CLOSURE",
        "NOT_REPRODUCED_OR_ALREADY_REPAIRED",
    }


if __name__ == "__main__":
    main()
