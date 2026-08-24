from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools/run_free_swarm_admission_boundary_receipt.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("free_swarm_receipt_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("RUNNER_IMPORT_SPEC_REQUIRED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FreeSwarmAdmissionReceiptRunner868Tests(unittest.TestCase):
    def test_receipt_suite_includes_malformed_admission_module_and_source(self) -> None:
        runner = _load_runner()
        self.assertIn(
            "tests.test_free_swarm_admission_boundary_868_malformed",
            runner.TEST_MODULES,
        )
        self.assertIn(
            "tests/test_free_swarm_admission_boundary_868_malformed.py",
            runner.SOURCE_PATHS,
        )

    def test_required_blocked_case_coverage_contains_supervisor_868_cases(self) -> None:
        runner = _load_runner()
        required = set(runner.REQUIRED_BLOCKED_CASE_TEST_METHODS)
        expected = {
            "test_global_attestation_missing_has_zero_secret_and_network_access",
            "test_unknown_paid_subscription_all_fail_before_secret_or_network",
            "test_missing_provider_admission_file_fails_before_secret_or_network",
            "test_authority_epoch_mismatch_fails_closed",
            "test_unlisted_provider_fails_closed",
            "test_malformed_admission_has_zero_secret_lookup_and_zero_network",
        }
        self.assertTrue(expected.issubset(required))

    def test_required_coverage_fails_closed_when_malformed_case_is_absent(self) -> None:
        runner = _load_runner()
        output = "\n".join(
            method
            for method in runner.REQUIRED_BLOCKED_CASE_TEST_METHODS
            if method != "test_malformed_admission_has_zero_secret_lookup_and_zero_network"
        )
        coverage = runner._required_test_coverage(output)
        self.assertFalse(coverage["test_malformed_admission_has_zero_secret_lookup_and_zero_network"])
        self.assertFalse(all(coverage.values()))

    def test_bootstrap_loads_all_requested_modules(self) -> None:
        runner = _load_runner()
        bootstrap = runner._bootstrap_text()
        self.assertIn("for module_name in sys.argv[1:]", bootstrap)
        self.assertIn("suite.addTests", bootstrap)


if __name__ == "__main__":
    unittest.main()
