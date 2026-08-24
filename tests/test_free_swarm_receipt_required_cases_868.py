from __future__ import annotations

import unittest

CANONICAL_BOUNDARY_MODULES = (
    "tests.test_free_swarm_admission_boundary_867",
    "tests.test_free_swarm_admission_boundary_868_malformed",
)

REQUIRED_METHODS = (
    "test_global_attestation_missing_has_zero_secret_and_network_access",
    "test_unknown_paid_subscription_all_fail_before_secret_or_network",
    "test_missing_provider_admission_file_fails_before_secret_or_network",
    "test_authority_epoch_mismatch_fails_closed",
    "test_unlisted_provider_fails_closed",
    "test_malformed_admission_has_zero_secret_lookup_and_zero_network",
)


def _test_ids(suite: unittest.TestSuite) -> list[str]:
    ids: list[str] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            ids.extend(_test_ids(item))
        else:
            ids.append(item.id())
    return ids


class FreeSwarmReceiptRequiredCases868Tests(unittest.TestCase):
    def test_supervisor_868_required_cases_are_discovered(self) -> None:
        suite = unittest.defaultTestLoader.loadTestsFromNames(CANONICAL_BOUNDARY_MODULES)
        ids = _test_ids(suite)
        self.assertGreater(len(ids), 0)
        for method in REQUIRED_METHODS:
            with self.subTest(method=method):
                self.assertTrue(any(test_id.endswith("." + method) for test_id in ids), method)


if __name__ == "__main__":
    unittest.main()
