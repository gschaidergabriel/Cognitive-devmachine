from copy import deepcopy

from tools.assert_clayverse_execution_boundary import (
    EXPECTED_EXECUTION_GATE,
    EXPECTED_RUNTIME_FREEZE_STATUS,
    EXPECTED_VERCEL_BRIDGE,
    VERCEL_EXECUTION_PATH,
    execution_frontier_errors,
)


VERCEL_CURRENT = """
Status: BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / RUNTIME GITHUB TOKEN INGRESS IMPLEMENTED
Sandbox.create is not the blocker.
Runtime one-shot ingress accepts GITHUB_READ_TOKEN through the owner-started POST path.
refresh exact current Research main + retained admitted lanes once
rebind retained #810 controller once
"""


def current_program():
    return {
        "stage_gates": {
            "CLAYVERSE_EXACT_OCI_ACCEPTANCE": {"status": EXPECTED_EXECUTION_GATE}
        },
        "execution_policy": {
            "vercel_sandbox_bridge": EXPECTED_VERCEL_BRIDGE,
            "execution_frontier_binding": VERCEL_EXECUTION_PATH,
            "runtime_freeze_status": EXPECTED_RUNTIME_FREEZE_STATUS,
            "controller_rebind_required_before_token_run": True,
        },
        "current_frontier": "publish current freeze, rebind retained Vercel controller #810, then owner-start with scoped GITHUB_READ_TOKEN for ClayVerse",
        "runtime_credit": {"whole_clayverse": 0},
    }


def test_current_bridge_binding_is_consistent():
    assert execution_frontier_errors(current_program(), VERCEL_CURRENT) == []


def test_stale_generic_execution_surface_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["stage_gates"]["CLAYVERSE_EXACT_OCI_ACCEPTANCE"]["status"] = "BLOCKED_ON_EXECUTION_SURFACE"
    assert "PROGRAM_EXECUTION_FRONTIER_STALE_OR_INCOMPLETE" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


def test_premature_token_only_frontier_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["stage_gates"]["CLAYVERSE_EXACT_OCI_ACCEPTANCE"]["status"] = "BLOCKED_ON_OWNER_ONE_SHOT_GITHUB_TOKEN_INGRESS"
    assert "PROGRAM_EXECUTION_FRONTIER_STALE_OR_INCOMPLETE" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


def test_bridge_never_mints_runtime_credit():
    poisoned = deepcopy(current_program())
    poisoned["runtime_credit"]["whole_clayverse"] = 1
    assert "PROGRAM_VERCEL_BRIDGE_FALSE_RUNTIME_CREDIT" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


def test_claimed_bridge_fails_closed_when_continuity_evidence_degrades():
    degraded = VERCEL_CURRENT.replace("Sandbox.create is not the blocker.\n", "")
    errors = execution_frontier_errors(current_program(), degraded)
    assert "VERCEL_EXECUTION_BRIDGE_EVIDENCE_MISSING_OR_DEGRADED" in errors


def test_missing_current_freeze_rebind_evidence_fails_closed():
    degraded = VERCEL_CURRENT.replace("rebind retained #810 controller once\n", "")
    assert "VERCEL_CURRENT_RUNTIME_FREEZE_REBIND_EVIDENCE_MISSING" in execution_frontier_errors(current_program(), degraded)


def test_missing_program_rebind_fence_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["execution_policy"]["controller_rebind_required_before_token_run"] = False
    assert "PROGRAM_CONTROLLER_REBIND_FENCE_MISSING" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


def test_missing_program_freeze_status_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["execution_policy"].pop("runtime_freeze_status")
    assert "PROGRAM_RUNTIME_FREEZE_STATUS_MISSING" in execution_frontier_errors(poisoned, VERCEL_CURRENT)
