from __future__ import annotations

import importlib.util
from pathlib import Path
import socket
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hcu_jspace_local_activation_probe",
    ROOT / "tools" / "hcu_jspace_local_activation_probe.py",
)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(probe)


class JSpaceLocalActivationProbeNetworkFence868Tests(unittest.TestCase):
    def test_dns_resolution_is_blocked_and_counted(self) -> None:
        original = socket.getaddrinfo
        fence = probe.NetworkFence()
        with fence:
            with self.assertRaisesRegex(probe.ProbeRejected, "NETWORK_ATTEMPT_BLOCKED_OFFLINE_ONLY"):
                socket.getaddrinfo("example.invalid", 443)
            self.assertEqual(fence.attempts, 1)
        self.assertIs(socket.getaddrinfo, original)

    def test_connect_ex_is_blocked_and_counted(self) -> None:
        original = socket.socket.connect_ex
        sock = socket.socket()
        try:
            fence = probe.NetworkFence()
            with fence:
                with self.assertRaisesRegex(probe.ProbeRejected, "NETWORK_ATTEMPT_BLOCKED_OFFLINE_ONLY"):
                    sock.connect_ex(("127.0.0.1", 9))
                self.assertEqual(fence.attempts, 1)
            self.assertIs(socket.socket.connect_ex, original)
        finally:
            sock.close()

    def test_all_python_socket_paths_are_restored(self) -> None:
        originals = {
            "connect": socket.socket.connect,
            "connect_ex": socket.socket.connect_ex,
            "create_connection": socket.create_connection,
            "getaddrinfo": socket.getaddrinfo,
        }
        fence = probe.NetworkFence()
        with fence:
            self.assertIsNot(socket.socket.connect, originals["connect"])
            self.assertIsNot(socket.socket.connect_ex, originals["connect_ex"])
            self.assertIsNot(socket.create_connection, originals["create_connection"])
            self.assertIsNot(socket.getaddrinfo, originals["getaddrinfo"])
        self.assertIs(socket.socket.connect, originals["connect"])
        self.assertIs(socket.socket.connect_ex, originals["connect_ex"])
        self.assertIs(socket.create_connection, originals["create_connection"])
        self.assertIs(socket.getaddrinfo, originals["getaddrinfo"])


if __name__ == "__main__":
    unittest.main()
