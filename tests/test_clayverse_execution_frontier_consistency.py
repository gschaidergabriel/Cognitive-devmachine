from copy import deepcopy

from tools.assert_clayverse_execution_boundary import (
    EXPECTED_EXECUTION_GATE,
    EXPECTED_VERCEL_BRIDGE,
    VERCEL_EXECUTION_PATH,
    execution_frontier_errors,
)


VERCEL_CURRENT = """
Status: BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / RUNTIME GITHUB TOKEN INGRESS IMPLEMENTED
Sandbox.create is not the blocker.
Runtime one-shot ingress accepts GITHUB_READ_TOKEN through the owner-started POST path.
"""


def current_program():
    return {
        "stage_gates": {
            "CLAYVERSE_EXACT_OCI_ACCEPTANCE": {"status": EXPECTED_EXECUTION_GATE}
        },
        "execution_policy": {
            "vercel_sandbox_bridge": EXPECTED_VERCEL_BRIDGE,
            "execution_frontier_binding": VERCEL_EXECUTION_PATH,
        },
        "current_frontier": "owner-start the retained Vercel Sandbox runtime POST with scoped GITHUB_READ_TOKEN for ClayVerse",
        "runtime_credit": {"whole_clayverse": 0},
    }


def test_current_bridge_binding_is_consistent():
    assert execution_frontier_errors(current_program(), VERCEL_CURRENT) == []


def test_stale_generic_execution_surface_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["stage_gates"]["CLAYVERSE_EXACT_OCI_ACCEPTANCE"]["status"] = "BLOCKED_ON_EXECUTION_SURFACE"
    assert "PROGRAM_EXECUTION_FRONTIER_STALE_GENERIC_SURFACE_BLOCK" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


def test_bridge_never_mints_runtime_credit():
    poisoned = deepcopy(current_program())
    poisoned["runtime_credit"]["whole_clayverse"] = 1
    assert "PROGRAM_VERCEL_BRIDGE_FALSE_RUNTIME_CREDIT" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


def test_claimed_bridge_fails_closed_when_continuity_evidence_degrades():
    degraded = VERCEL_CURRENT.replace("Sandbox.create is not the blocker.\n", "")
    errors = execution_frontier_errors(current_program(), degraded)
    assert "VERCEL_EXECUTION_BRIDGE_EVIDENCE_MISSING_OR_DEGRADED" in errors
