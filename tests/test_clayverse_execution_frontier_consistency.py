from copy import deepcopy

from tools.assert_clayverse_execution_boundary import (
    BRIDGE_CANONICAL_CLAUDE_MARKER,
    BRIDGE_ENTITYOS_CONDITIONAL_MARKER,
    BRIDGE_RETIRED_PROVIDER_MARKER,
    CURRENT_OWNER_DIRECTIVE,
    EXPECTED_CONTROLLER,
    EXPECTED_CONTROLLER_READY_BINDING,
    EXPECTED_EXECUTION_GATE,
    EXPECTED_VERCEL_BRIDGE,
    VERCEL_EXECUTION_PATH,
    execution_frontier_errors,
)

VERCEL_CURRENT = f"""
Status: BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / RUNTIME GITHUB TOKEN INGRESS IMPLEMENTED
Current product authority: {CURRENT_OWNER_DIRECTIVE}
Sandbox.create is not the blocker.
Runtime one-shot ingress accepts GITHUB_READ_TOKEN through the owner-started POST path.
Current canonical visible runtime uses {BRIDGE_CANONICAL_CLAUDE_MARKER}.
The {BRIDGE_RETIRED_PROVIDER_MARKER} is retired product runtime.
{BRIDGE_ENTITYOS_CONDITIONAL_MARKER}.
"""


def current_program():
    return {
        "stage_gates": {
            "CLAYVERSE_EXACT_OCI_ACCEPTANCE": {"status": EXPECTED_EXECUTION_GATE}
        },
        "execution_policy": {
            "vercel_sandbox_bridge": EXPECTED_VERCEL_BRIDGE,
            "execution_frontier_binding": VERCEL_EXECUTION_PATH,
            "retained_vercel_controller": EXPECTED_CONTROLLER,
            "vercel_controller_ready_binding": EXPECTED_CONTROLLER_READY_BINDING,
        },
        "current_frontier": (
            "rebind retained Vercel controller PR #810 to exact current source and obtain READY; "
            "then owner-start the runtime POST with scoped GITHUB_READ_TOKEN for ClayVerse"
        ),
        "runtime_credit": {"whole_clayverse": 0},
    }


def test_current_bridge_binding_is_consistent():
    assert execution_frontier_errors(current_program(), VERCEL_CURRENT) == []


def test_stale_generic_execution_surface_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["stage_gates"]["CLAYVERSE_EXACT_OCI_ACCEPTANCE"]["status"] = "BLOCKED_ON_EXECUTION_SURFACE"
    assert "PROGRAM_EXECUTION_FRONTIER_STALE_GENERIC_SURFACE_BLOCK" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


def test_token_only_frontier_without_exact_controller_ready_rebind_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["execution_policy"].pop("vercel_controller_ready_binding")
    poisoned["current_frontier"] = "owner-start retained Vercel runtime POST with scoped GITHUB_READ_TOKEN for ClayVerse"
    errors = execution_frontier_errors(poisoned, VERCEL_CURRENT)
    assert "PROGRAM_VERCEL_CONTROLLER_READY_BINDING_MISSING" in errors
    assert "PROGRAM_CURRENT_FRONTIER_CONTROLLER_READY_AND_TOKEN_SEQUENCE_MISSING" in errors


def test_wrong_retained_controller_fails_closed():
    poisoned = deepcopy(current_program())
    poisoned["execution_policy"]["retained_vercel_controller"] = "other/controller#1"
    assert "PROGRAM_RETAINED_VERCEL_CONTROLLER_MISSING" in execution_frontier_errors(poisoned, VERCEL_CURRENT)


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
    poisoned = VERCEL_CURRENT.replace(BRIDGE_ENTITYOS_CONDITIONAL_MARKER + ".\n", "")
    assert "VERCEL_BRIDGE_ENTITYOS_CONDITIONALITY_MISSING" in execution_frontier_errors(current_program(), poisoned)


def test_missing_canonical_claude_path_fails_closed():
    poisoned = VERCEL_CURRENT.replace(BRIDGE_CANONICAL_CLAUDE_MARKER, "retired custom engine")
    assert "VERCEL_BRIDGE_CANONICAL_CLAUDE_PATH_MISSING" in execution_frontier_errors(current_program(), poisoned)


def test_retired_probe_cannot_regain_authority():
    poisoned = VERCEL_CURRENT + "\nfinal_acceptance_probe.py::run_mistral_acceptance_probe\n"
    assert "VERCEL_BRIDGE_STALE_RETIRED_PROBE_AUTHORITY" in execution_frontier_errors(current_program(), poisoned)
