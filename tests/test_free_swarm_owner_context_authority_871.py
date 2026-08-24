from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_6000_free_swarm_v3 as v3


class FreeSwarmOwnerContextAuthorityTests(unittest.TestCase):
    def test_active_v3_worker_context_uses_current_free_swarm_owner_authority(self) -> None:
        expected = ROOT / "governance/CLAY_FREE_SWARM_OWNER_ADMISSION_2026-08-24.md"
        stale = ROOT / "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md"
        self.assertEqual(v3.fabric.base.OWNER_DIRECTIVE_PATH, expected)
        self.assertNotEqual(v3.fabric.base.OWNER_DIRECTIVE_PATH, stale)
        self.assertTrue(expected.exists())

    def test_fast_and_v4_share_same_base_context_through_v3(self) -> None:
        # Both active launch surfaces import the same v3 fabric/base module, so
        # the authority correction is inherited instead of creating a second
        # execution or state authority.
        self.assertIs(v3.fabric.base, v3.fabric.opt.base)
        self.assertEqual(
            v3.fabric.base.OWNER_DIRECTIVE_PATH.name,
            "CLAY_FREE_SWARM_OWNER_ADMISSION_2026-08-24.md",
        )


if __name__ == "__main__":
    unittest.main()
