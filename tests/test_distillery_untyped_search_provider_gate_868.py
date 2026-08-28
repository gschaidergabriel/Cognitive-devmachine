#!/usr/bin/env python3
from __future__ import annotations

import unittest
from unittest import mock

import tools.run_research_distillery_entry as entry


class DistilleryUntypedSearchProviderGate868Tests(unittest.TestCase):
    def test_tavily_and_exa_secrets_are_not_read(self) -> None:
        with mock.patch.object(entry, "_ORIGINAL_SECRET", side_effect=AssertionError("secret lookup reached")):
            self.assertEqual(entry.admitted_secret("TAVILY_API_KEY"), "")
            self.assertEqual(entry.admitted_secret("EXA_API_KEY"), "")

    def test_tavily_and_exa_network_are_not_reached(self) -> None:
        with mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("network reached")):
            for provider in ("tavily", "exa"):
                status, headers, body = entry.admitted_request_json(provider, "test", "https://invalid.example")
                self.assertEqual(status, 412)
                self.assertEqual(headers, {})
                self.assertEqual(body.get("error"), "PROVIDER_NOT_IN_TYPED_FREE_ADMISSION_AUTHORITY")

    def test_public_noncredentialed_source_path_remains_available(self) -> None:
        expected = (200, {}, {"ok": True})
        with mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", return_value=expected) as downstream:
            observed = entry.admitted_request_json("github", "test", "https://api.github.com/repos/example/example")
        self.assertEqual(observed, expected)
        downstream.assert_called_once()


if __name__ == "__main__":
    unittest.main()
