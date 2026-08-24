#!/usr/bin/env python3
from __future__ import annotations

import unittest
from unittest import mock

import tools.run_research_distillery_entry as entry


class DistilleryUnclassifiedProviderGate869Tests(unittest.TestCase):
    def test_unclassified_secret_name_is_loader_blind(self) -> None:
        with mock.patch.object(entry, "_ORIGINAL_SECRET", side_effect=AssertionError("secret loader reached")):
            self.assertEqual(entry.admitted_secret("FUTURE_LLM_API_KEY"), "")

    def test_unclassified_provider_is_network_blind(self) -> None:
        with mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("network reached")):
            status, headers, body = entry.admitted_request_json("future-llm-provider", "test", "https://invalid.example/v1/chat/completions", key="fake", payload={"model":"future"})
        self.assertEqual(status, 412)
        self.assertEqual(headers, {})
        self.assertEqual(body.get("error"), "PROVIDER_NOT_EXPLICITLY_CLASSIFIED")

    def test_runtime_quarantined_llm_is_network_blind(self) -> None:
        with mock.patch.object(entry, "provider_call_is_allowed", return_value=False), mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("network reached")):
            status, _, body = entry.admitted_request_json("openrouter", "test", "https://openrouter.ai/api/v1/chat/completions", key="fake", payload={"model":"test"})
        self.assertEqual(status, 412)
        self.assertEqual(body.get("error"), "PROVIDER_CALL_BOUNDARY_BLOCKED")

    def test_public_github_path_is_host_bound_and_credential_blind(self) -> None:
        expected=(200,{}, {"ok":True})
        with mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", return_value=expected) as downstream:
            self.assertEqual(entry.admitted_request_json("github","test","https://api.github.com/repos/example/example"), expected)
        downstream.assert_called_once()
        with mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("network reached")):
            self.assertEqual(entry.admitted_request_json("github","test","https://example.com/repos/example/example")[2].get("error"), "PUBLIC_SOURCE_HOST_NOT_ADMITTED")
            self.assertEqual(entry.admitted_request_json("github","test","https://api.github.com/repos/example/example",key="secret")[2].get("error"), "PUBLIC_SOURCE_CREDENTIALS_FORBIDDEN")
            self.assertEqual(entry.admitted_request_json("github","test","https://api.github.com/repos/example/example",headers={"Authorization":"Bearer secret"})[2].get("error"), "PUBLIC_SOURCE_CREDENTIALS_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
