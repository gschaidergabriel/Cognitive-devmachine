import tempfile
import time
import unittest
from pathlib import Path

import free_swarm_quota as quota


class FreeSwarmQuotaTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        quota.DB_PATH = Path(self.tempdir.name) / "provider_budget.sqlite3"
        self.original_billing_cooldown = quota.DEFAULT_BILLING_LIMIT_COOLDOWN_S
        quota.DEFAULT_BILLING_LIMIT_COOLDOWN_S = 120.0

    def tearDown(self):
        quota.DEFAULT_BILLING_LIMIT_COOLDOWN_S = self.original_billing_cooldown
        self.tempdir.cleanup()

    def test_named_billing_limit_denial_sets_fail_closed_cooldown(self):
        quota.observe("vercel.logs", "test", "ExceedsBillingLimitError")
        state = quota.snapshot()["providers"]["vercel.logs"]
        self.assertGreater(state["cooldown_seconds"], 100.0)
        self.assertEqual(state["total_errors"], 1)
        self.assertEqual(state["last_status"], "ExceedsBillingLimitError")
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            quota.acquire("vercel.logs", "test", timeout_s=0.5)
        self.assertLess(time.monotonic() - started, 1.5)

    def test_http_402_sets_fail_closed_cooldown(self):
        quota.observe("provider", "test", 402, retry_after_s=90)
        state = quota.snapshot()["providers"]["provider"]
        self.assertGreater(state["cooldown_seconds"], 75.0)
        self.assertEqual(state["total_errors"], 1)
        self.assertEqual(state["last_status"], "402")

    def test_generic_500_remains_error_without_cooldown(self):
        quota.observe("provider", "test", 500)
        state = quota.snapshot()["providers"]["provider"]
        self.assertEqual(state["cooldown_seconds"], 0.0)
        self.assertEqual(state["total_errors"], 1)

    def test_429_retains_existing_rate_limit_cooldown(self):
        quota.observe("provider", "test", 429, retry_after_s=2)
        state = quota.snapshot()["providers"]["provider"]
        self.assertGreater(state["cooldown_seconds"], 1.0)
        self.assertEqual(state["total_429"], 1)
        self.assertEqual(state["total_errors"], 0)

    def test_insufficient_quota_alias_is_billing_limit_denial(self):
        quota.observe("provider", "test", "insufficient_quota")
        state = quota.snapshot()["providers"]["provider"]
        self.assertGreater(state["cooldown_seconds"], 100.0)
        self.assertEqual(state["total_errors"], 1)


if __name__ == "__main__":
    unittest.main()
