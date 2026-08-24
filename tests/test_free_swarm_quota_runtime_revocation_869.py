from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/"tools"
if str(TOOLS) not in sys.path:sys.path.insert(0,str(TOOLS))
import free_swarm_quota as quota


class FreeSwarmQuotaRuntimeRevocation869Tests(unittest.TestCase):
    def test_quarantined_llm_is_blocked_before_quota_db_touch(self):
        with mock.patch("provider_call_boundary.provider_call_is_allowed",return_value=False), mock.patch.object(quota,"ensure_provider",side_effect=AssertionError("quota db touched")):
            with self.assertRaisesRegex(quota.ProviderAuthorityBlocked,"PROVIDER_CALL_BOUNDARY_BLOCKED:openrouter"):
                quota.acquire("openrouter","stale-process",timeout_s=0.1)

    def test_e2b_is_blocked_before_quota_db_touch(self):
        with mock.patch.object(quota,"ensure_provider",side_effect=AssertionError("quota db touched")):
            with self.assertRaisesRegex(quota.ProviderAuthorityBlocked,"EXTERNAL_COMPUTE_NOT_TYPED_FREE_ADMITTED:e2b"):
                quota.acquire("e2b","forge",timeout_s=0.1)

    def test_public_non_llm_lane_keeps_quota_behavior(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(quota,"DB_PATH",Path(td)/"budget.sqlite3"):
            lease=quota.acquire("github","public",timeout_s=0.5,lease_s=1.0)
            self.assertTrue(lease)
            quota.release(lease)


if __name__=="__main__":unittest.main()
