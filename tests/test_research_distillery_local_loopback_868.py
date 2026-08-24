from __future__ import annotations

from pathlib import Path
import sys
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_research_distillery_local as local


class LocalDistilleryLoopbackFenceTests(unittest.TestCase):
    def test_accepts_literal_ipv4_and_ipv6_loopback_origins(self):
        self.assertEqual(
            local._validated_loopback_base("http://127.0.0.1:8088/"),
            "http://127.0.0.1:8088",
        )
        self.assertEqual(
            local._validated_loopback_base("http://[::1]:8088"),
            "http://[::1]:8088",
        )

    def test_rejects_non_loopback_and_name_based_hosts(self):
        for value in (
            "http://example.com:8088",
            "http://10.0.0.5:8088",
            "http://192.168.1.2:8088",
            "http://localhost:8088",
        ):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    local._validated_loopback_base(value)

    def test_rejects_ambiguous_or_broadened_origins(self):
        for value in (
            "https://127.0.0.1:8088",
            "http://user@127.0.0.1:8088",
            "http://127.0.0.1:8088/path",
            "http://127.0.0.1:8088/?next=http://example.com",
            "http://127.0.0.1:8088/#fragment",
            "http://[::1%25lo]:8088",
            "http://127.0.0.1:bad",
            "",
        ):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    local._validated_loopback_base(value)

    def test_redirect_handler_never_creates_followup_request(self):
        request = urllib.request.Request("http://127.0.0.1:8088/health")
        redirected = local._NoLocalRedirect().redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "http://example.com/exfiltrate",
        )
        self.assertIsNone(redirected)

    def test_local_opener_has_no_nonempty_proxy_handler(self):
        nonempty_proxy_handlers = [
            handler
            for handler in local._LOCAL_OPENER.handlers
            if isinstance(handler, urllib.request.ProxyHandler) and handler.proxies
        ]
        self.assertEqual(nonempty_proxy_handlers, [])


if __name__ == "__main__":
    unittest.main()
