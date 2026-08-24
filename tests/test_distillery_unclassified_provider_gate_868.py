#!/usr/bin/env python3
from __future__ import annotations

import unittest
from unittest import mock

import tools.run_research_distillery_entry as entry


class DistilleryUnclassifiedProviderGate868Tests(unittest.TestCase):
    def test_unclassified_provider_is_network_blind(self) -> None:
        with mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("network reached")):
            status, headers, body = entry.admitted_request_json(
                "future-llm-provider",
                "test",
                "https://invalid.example/v1/chat/completions",
                key="fake-secret-that-must-not-be-used",
                payload={"model": "future-model"},
            )
        self.assertEqual(status, 412)
        self.assertEqual(headers, {})
        self.assertEqual(body.get("error"), "PROVIDER_NOT_EXPLICITLY_CLASSIFIED")

    def test_public_noncredentialed_github_path_remains_available(self) -> None:
        expected = (200, {}, {"ok": True})
        with mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", return_value=expected) as downstream:
            observed = entry.admitted_request_json(
                "github",
                "test",
                "https://api.github.com/repos/example/example",
            )
        self.assertEqual(observed, expected)
        downstream.assert_called_once()

    def test_typed_free_llm_path_remains_available_after_positive_admission(self) -> None:
        expected = (200, {}, {"ok": True})
        with mock.patch.object(entry, "provider_is_admitted_free", return_value=True), \
             mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", return_value=expected) as downstream:
            observed = entry.admitted_request_json(
                "openrouter",
                "test",
                "https://openrouter.ai/api/v1/chat/completions",
                key="fake-admitted-key",
                payload={"model": "test"},
            )
        self.assertEqual(observed, expected)
        downstream.assert_called_once()


if __name__ == "__main__":
    unittest.main()
