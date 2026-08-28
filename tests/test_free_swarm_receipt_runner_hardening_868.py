from __future__ import annotations

import unittest

import run_free_swarm_admission_boundary_receipt as base
import run_free_swarm_admission_boundary_receipt_hardened_868 as hardened


class FreeSwarmReceiptRunnerHardening868Tests(unittest.TestCase):
    def test_runner_sources_are_manifest_bound(self) -> None:
        self.assertIn(hardened.BASE_REL, base.SOURCE_PATHS)
        self.assertIn(hardened.SELF_REL, base.SOURCE_PATHS)
        self.assertIn(hardened.TEST_REL, base.SOURCE_PATHS)
        self.assertIn(hardened.INHERITED_ENV_TEST_REL, base.SOURCE_PATHS)

    def test_hardening_tests_are_in_execution_set(self) -> None:
        self.assertIn(hardened.TEST_MODULE, base.TEST_MODULES)
        self.assertIn(hardened.ROOT / hardened.TEST_REL, base.TEST_PATHS)
        self.assertIn(hardened.INHERITED_ENV_TEST_MODULE, base.TEST_MODULES)
        self.assertIn(hardened.ROOT / hardened.INHERITED_ENV_TEST_REL, base.TEST_PATHS)

    def test_bootstrap_trips_dns_connect_and_datagram_paths(self) -> None:
        text = base._bootstrap_text()
        required = (
            'socket.socket.connect = guarded_connect',
            'socket.socket.connect_ex = guarded_connect_ex',
            'socket.create_connection = guarded_create_connection',
            'socket.getaddrinfo = guarded_getaddrinfo',
            'socket.socket.sendto = guarded_sendto',
            'socket.socket.sendmsg = guarded_sendmsg',
            'record("socket.connect_ex", address)',
            'record("socket.getaddrinfo", target)',
            'record("socket.sendto", target)',
            'record("socket.sendmsg", target)',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_inherited_environment_fence_is_required_for_receipt_pass(self) -> None:
        self.assertIn(
            "tests.test_go_868_inherited_provider_secret_fence",
            base.TEST_MODULES,
        )
        self.assertTrue(base._CLAY_868_RECEIPT_HARDENING_INSTALLED)

    def test_source_binding_is_not_runtime_credit(self) -> None:
        self.assertTrue(base._CLAY_868_RECEIPT_HARDENING_INSTALLED)
        # The wrapper intentionally delegates promotion to the canonical runtime runner.
        # Merely importing this module must not create any runtime receipt or provider call.
        self.assertEqual(base.SENTINEL, "CLAY_BOUNDARY_SENTINEL_NOT_A_REAL_SECRET")


if __name__ == "__main__":
    unittest.main()
