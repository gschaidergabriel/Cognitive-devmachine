from copy import deepcopy

from tools.assert_clayverse_execution_boundary import (
    BRIDGE_ENTITYOS_POLICY,
    BRIDGE_PROVIDER_POLICY,
    BRIDGE_REBIND_POLICY,
    CURRENT_OWNER_DIRECTIVE,
    EXPECTED_EXECUTION_GATE,
    EXPECTED_VERCEL_BRIDGE,
    VERCEL_EXECUTION_PATH,
    execution_frontier_errors,
)


VERCEL_CURRENT = f"""
Status: BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / RUNTIME GITHUB TOKEN INGRESS IMPLEMENTED
Current owner directive: {CURRENT_OWNER_DIRECTIVE}
Sandbox.create is not the blocker.
Runtime one-shot ingress accepts GITHUB_READ_TOKEN through the owner-started POST path.
{BRIDGE_PROVIDER_POLICY}
{BRIDGE_ENTITYOS_POLICY}
{BRIDGE_REBIND_POLICY}
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


def test_stale_mandatory_provider_contract_fails_closed():
    poisoned = VERCEL_CURRENT + "\nMistral is mandatory for this final test as an inference provider only.\n"
    assert "VERCEL_BRIDGE_STALE_MANDATORY_PROVIDER" in execution_frontier_errors(current_program(), poisoned)


def test_missing_entityos_conditionality_fails_closed():
    poisoned = VERCEL_CURRENT.replace(BRIDGE_ENTITYOS_POLICY + "\n", "")
    assert "VERCEL_BRIDGE_ENTITYOS_CONDITIONALITY_MISSING" in execution_frontier_errors(current_program(), poisoned)


def test_missing_pr810_semantic_rebind_fence_fails_closed():
    poisoned = VERCEL_CURRENT.replace(BRIDGE_REBIND_POLICY + "\n", "")
    assert "VERCEL_BRIDGE_PR810_SEMANTIC_REBIND_FENCE_MISSING" in execution_frontier_errors(current_program(), poisoned)
