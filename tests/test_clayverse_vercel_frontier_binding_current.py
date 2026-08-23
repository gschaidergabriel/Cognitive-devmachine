#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import assert_clayverse_execution_boundary as boundary


POSITIVE_CONTINUITY = """
# Vercel Sandbox execution path — CURRENT
The authorized bridge has actually created disposable Vercel Sandbox Firecracker microVMs.
Sandbox.create is not the blocker.
The retained controller supports runtime one-shot ingress of GITHUB_READ_TOKEN.
Prior source/OCI runtime credit remains zero until the explicit one-shot run happens.
"""


def admitted_program() -> dict:
    return {
        "stage_gates": {
            "CLAYVERSE_EXACT_OCI_ACCEPTANCE": {
                "status": boundary.EXPECTED_EXECUTION_GATE,
            }
        },
        "execution_policy": {
            "vercel_sandbox_bridge": boundary.EXPECTED_VERCEL_BRIDGE,
            "execution_frontier_binding": boundary.VERCEL_EXECUTION_PATH,
        },
        "current_frontier": (
            "owner-start retained Vercel one-shot with scoped read-only "
            "GITHUB_READ_TOKEN, verify exact source, then exact OCI build"
        ),
        "runtime_credit": {"whole_clayverse": 0},
    }


class ClayVerseVercelFrontierBindingTests(unittest.TestCase):
    def test_positive_bridge_and_precise_zero_credit_frontier_agree(self):
        self.assertEqual(
            boundary.execution_frontier_errors(admitted_program(), POSITIVE_CONTINUITY),
            [],
        )

    def test_positive_bridge_rejects_stale_generic_surface_block(self):
        program = admitted_program()
        program["stage_gates"]["CLAYVERSE_EXACT_OCI_ACCEPTANCE"]["status"] = (
            "BLOCKED_ON_EXECUTION_SURFACE"
        )
        errors = boundary.execution_frontier_errors(program, POSITIVE_CONTINUITY)
        self.assertIn("PROGRAM_EXECUTION_FRONTIER_STALE_GENERIC_SURFACE_BLOCK", errors)

    def test_program_cannot_claim_bridge_if_continuity_is_degraded(self):
        errors = boundary.execution_frontier_errors(
            admitted_program(),
            "Sandbox path historical only; runtime ingress evidence unavailable.",
        )
        self.assertIn("VERCEL_EXECUTION_BRIDGE_EVIDENCE_MISSING_OR_DEGRADED", errors)

    def test_bridge_never_mints_whole_product_runtime_credit(self):
        program = admitted_program()
        program["runtime_credit"]["whole_clayverse"] = 1
        errors = boundary.execution_frontier_errors(program, POSITIVE_CONTINUITY)
        self.assertIn("PROGRAM_VERCEL_BRIDGE_FALSE_RUNTIME_CREDIT", errors)

    def test_partial_program_bridge_binding_fails_closed(self):
        program = admitted_program()
        del program["execution_policy"]["execution_frontier_binding"]
        errors = boundary.execution_frontier_errors(program, POSITIVE_CONTINUITY)
        self.assertIn("PROGRAM_VERCEL_FRONTIER_BINDING_MISSING", errors)

    def test_frontier_must_keep_owner_token_exact_source_and_oci_sequence(self):
        program = copy.deepcopy(admitted_program())
        program["current_frontier"] = "run Vercel when possible"
        errors = boundary.execution_frontier_errors(program, POSITIVE_CONTINUITY)
        self.assertIn("PROGRAM_CURRENT_FRONTIER_TOKEN_INGRESS_MISSING", errors)


if __name__ == "__main__":
    unittest.main()
