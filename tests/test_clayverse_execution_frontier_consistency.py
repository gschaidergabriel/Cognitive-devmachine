from copy import deepcopy
import json
from pathlib import Path

from tools.assert_clayverse_execution_boundary import (
    EXPECTED_EXECUTION_GATE,
    EXPECTED_VERCEL_BRIDGE,
    VERCEL_EXECUTION_PATH,
    execution_frontier_errors,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
VERCEL_CURRENT = """
Status: BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / RUNTIME GITHUB TOKEN INGRESS IMPLEMENTED
Sandbox.create is not the blocker.
Runtime one-shot ingress accepts GITHUB_READ_TOKEN through the owner-started POST path.
At the next real owner-started one-shot run:
refresh exact current Research main + retained admitted lanes once
-> rebind retained #810 controller once
-> owner supplies scoped read-only GITHUB_READ_TOKEN through runtime POST/start panel
"""


def _rebind_precedes_owner_token(text: str) -> bool:
    lower = text.lower()
    rebind = lower.find("rebind retained")
    owner = lower.find("owner-start", rebind + 1)
    token = lower.find("github_read_token", owner + 1)
    return rebind >= 0 and owner > rebind and token > owner and "#810" in text


def current_program():
    return {
        "dynamic_targets": {
            "next": "refresh exact current Research main -> rebind retained Vercel controller PR #810 -> owner-start retained one-shot with GITHUB_READ_TOKEN"
        },
        "stage_gates": {
            "CLAYVERSE_EXACT_OCI_ACCEPTANCE": {"status": EXPECTED_EXECUTION_GATE}
        },
        "execution_policy": {
            "vercel_sandbox_bridge": EXPECTED_VERCEL_BRIDGE,
            "execution_frontier_binding": VERCEL_EXECUTION_PATH,
        },
        "current_frontier": "refresh exact current Research main, rebind retained Vercel controller PR #810, then owner-start the retained Vercel Sandbox runtime POST with scoped GITHUB_READ_TOKEN for ClayVerse",
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


def test_current_program_orders_exact_controller_rebind_before_owner_token():
    program = json.loads((REPO_ROOT / "research_entity/rooms/PROGRAM_STATE.json").read_text(encoding="utf-8"))
    assert _rebind_precedes_owner_token(program["current_frontier"])
    assert _rebind_precedes_owner_token(program["dynamic_targets"]["next"])
    assert program["runtime_credit"]["whole_clayverse"] == 0


def test_current_vercel_continuity_orders_rebind_before_owner_token():
    continuity = (REPO_ROOT / VERCEL_EXECUTION_PATH).read_text(encoding="utf-8")
    assert _rebind_precedes_owner_token(continuity)


def test_owner_token_first_work_selector_is_rejected_by_order_fence():
    stale = "owner-start the retained Vercel Sandbox runtime POST with scoped GITHUB_READ_TOKEN, then rebind retained #810 controller"
    assert not _rebind_precedes_owner_token(stale)
