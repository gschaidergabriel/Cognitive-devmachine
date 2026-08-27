"""S0/S1/S2 transition contract -- Xeno Shell Master Spec v1 SS10.

This module does not reimplement S1 (grid10_fabric.Fabric already is S1: canonical
`scopes` table, CAS-gated coordinator_commit, ordinary-node write rejection) or S0
(zero_entityos_s0_epoch_cas_v2.py). It records the exact 9-transition contract the
spec requires and provides guard functions for the 4 transitions the spec marks
"forbidden direct" -- these are structural refusals, not documentation.
"""
from __future__ import annotations

TRANSITION_MATRIX = {
    "S0->S1": {"mechanism": "READ_ONLY_PROJECTION_WITH_EPOCH_DIGEST_PROVENANCE", "forbidden": False},
    "S2->S1": {"mechanism": "TYPED_RESULT_WORKSPACE_PACKET_WITH_CAUSAL_GENERATION_BINDINGS", "forbidden": False},
    "S1->S0": {"mechanism": "DBWRITEPROPOSAL_THEN_DETERMINISTIC_ADMISSION_ONLY", "forbidden": False},
    "S2->S0": {"mechanism": None, "forbidden": True},
    "S1->EFFECT": {"mechanism": "EFFECTPROPOSAL_THEN_EFFECTGATE_EFFECTJOURNAL_ONLY", "forbidden": False},
    "S2->EFFECT": {"mechanism": None, "forbidden": True},
    "CLAUDE->S1": {"mechanism": "TYPED_BRIDGE_RETURN_CANDIDATE_EVIDENCE_BOUND_RESULT", "forbidden": False},
    "CLAUDE->S0": {"mechanism": None, "forbidden": True},
    "JSPACE->S0": {"mechanism": None, "forbidden": True},
}

FORBIDDEN_TRANSITIONS = frozenset(k for k, v in TRANSITION_MATRIX.items() if v["forbidden"])


class TransitionError(ValueError):
    pass


def assert_transition_allowed(transition: str) -> None:
    """Fail closed on any transition not in the matrix, and on any transition the
    matrix marks forbidden -- regardless of what the caller claims the intent was."""
    entry = TRANSITION_MATRIX.get(transition)
    if entry is None:
        raise TransitionError(f"UNKNOWN_TRANSITION:{transition}")
    if entry["forbidden"]:
        raise TransitionError(f"TRANSITION_FORBIDDEN_DIRECT:{transition}")


def attempt_forbidden_direct_write(transition: str, *, actor: str, payload: object) -> None:
    """Structural refusal path for the 4 forbidden-direct transitions. A caller that
    somehow reaches this function (bypassing normal S1 typed-packet routing) is
    refused here too -- defense in depth, not the only gate."""
    if transition not in FORBIDDEN_TRANSITIONS:
        raise TransitionError(f"NOT_A_FORBIDDEN_TRANSITION_USE_NORMAL_PATH:{transition}")
    raise TransitionError(f"REFUSED_FORBIDDEN_DIRECT_TRANSITION:{transition}:actor={actor}")
