from __future__ import annotations

import http.server
import pathlib
import sys
import threading
import unittest
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from local_loopback_endpoint import (  # noqa: E402
    LoopbackEndpointError,
    build_loopback_opener,
    validated_loopback_base,
)


class _RedirectOffLoopback(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(302)
        self.send_header("Location", "http://192.0.2.1/should-never-be-contacted")
        self.end_headers()

    def log_message(self, format, *args):
        pass


class LocalLoopbackEndpointTests(unittest.TestCase):
    def test_numeric_ipv4_and_ipv6_loopback_are_admitted(self):
        self.assertEqual(
            validated_loopback_base("http://127.0.0.1:8088/"),
            "http://127.0.0.1:8088",
        )
        self.assertEqual(
            validated_loopback_base("http://127.42.0.9:9000"),
            "http://127.42.0.9:9000",
        )
        self.assertEqual(
            validated_loopback_base("http://[::1]:8088"),
            "http://[::1]:8088",
        )

    def test_hostnames_and_non_loopback_addresses_are_rejected(self):
        bad = (
            "http://localhost:8088",
            "http://example.com:8088",
            "http://192.168.1.2:8088",
            "http://0.0.0.0:8088",
            "http://[2001:db8::1]:8088",
        )
        for value in bad:
            with self.subTest(value=value), self.assertRaises(LoopbackEndpointError):
                validated_loopback_base(value)

    def test_url_smuggling_components_fail_closed(self):
        bad = (
            "https://127.0.0.1:8088",
            " http://127.0.0.1:8088",
            "http://127.0.0.1:8088 ",
            "http://user@127.0.0.1:8088",
            "http://user:pass@127.0.0.1:8088",
            "http://127.0.0.1:8088/api",
            "http://127.0.0.1:8088?next=http://example.com",
            "http://127.0.0.1:8088#example.com",
            "http://127.0.0.1:99999",
        )
        for value in bad:
            with self.subTest(value=value), self.assertRaises(LoopbackEndpointError):
                validated_loopback_base(value)

    def test_redirect_cannot_escape_loopback(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RedirectOffLoopback)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            opener = build_loopback_opener()
            url = f"http://127.0.0.1:{server.server_port}/health"
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                opener.open(url, timeout=2)
            self.assertEqual(ctx.exception.code, 302)
            self.assertEqual(ctx.exception.geturl(), url)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
