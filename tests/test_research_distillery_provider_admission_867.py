from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_research_distillery_entry as entry


class ResearchDistilleryProviderAdmissionTests(unittest.TestCase):
    def test_each_provider_secret_is_blocked_before_underlying_secret_loader(self) -> None:
        with mock.patch.object(entry, "_provider_admitted", return_value=False), \
             mock.patch.object(entry, "_ORIGINAL_SECRET", side_effect=AssertionError("secret loader touched")):
            for name in sorted(entry.SECRET_PROVIDER):
                with self.subTest(name=name):
                    self.assertEqual(entry.typed_secret(name), "")

    def test_unknown_secret_name_fails_closed(self) -> None:
        with mock.patch.object(entry, "_provider_admitted", return_value=True), \
             mock.patch.object(entry, "_ORIGINAL_SECRET", side_effect=AssertionError("untyped secret loader touched")):
            self.assertEqual(entry.typed_secret("FUTURE_PROVIDER_API_KEY"), "")

    def test_protected_provider_network_rechecks_admission_at_last_boundary(self) -> None:
        with mock.patch.object(entry, "_provider_admitted", return_value=False), \
             mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("provider socket touched")):
            for provider in sorted(entry.PROTECTED_PROVIDER_NETWORK):
                with self.subTest(provider=provider):
                    status, _headers, body = entry.typed_request_json(
                        provider, "test", "https://example.invalid/provider")
                    self.assertEqual(status, 412)
                    self.assertEqual(body["error"], "TYPED_FREE_PROVIDER_ADMISSION_REQUIRED")

    def test_chat_blocked_before_secret_and_network(self) -> None:
        with mock.patch.object(entry, "_provider_admitted", return_value=False), \
             mock.patch.object(entry, "_ORIGINAL_SECRET", side_effect=AssertionError("secret loader touched")), \
             mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("provider socket touched")):
            for provider in ("openrouter", "nvidia", "mistral", "groq"):
                with self.subTest(provider=provider):
                    ok, text, usage, state = entry.d.chat(provider, "synthetic-model", "prompt", max_tokens=1)
                    self.assertFalse(ok)
                    self.assertEqual(text, "")
                    self.assertEqual(usage, {})
                    self.assertEqual(state, "NO_KEY")

    def test_openrouter_catalog_blocked_before_secret_and_network(self) -> None:
        with mock.patch.object(entry, "_provider_admitted", return_value=False), \
             mock.patch.object(entry, "_ORIGINAL_SECRET", side_effect=AssertionError("secret loader touched")), \
             mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("provider socket touched")):
            self.assertEqual(entry.d.openrouter_catalog(), [])

    def test_tavily_and_exa_collectors_block_before_secret_and_network(self) -> None:
        with mock.patch.object(entry, "_provider_admitted", return_value=False), \
             mock.patch.object(entry, "_ORIGINAL_SECRET", side_effect=AssertionError("secret loader touched")), \
             mock.patch.object(entry, "_ORIGINAL_REQUEST_JSON", side_effect=AssertionError("provider socket touched")):
            self.assertEqual(entry.d.tavily_collect(None, None, 0, "query"), [])
            self.assertEqual(entry.d.exa_collect(None, None, 0, "query"), [])

    def test_reviewer_override_calls_captured_original_not_itself(self) -> None:
        with mock.patch.object(entry, "_ORIGINAL_SELECT_REVIEWERS", return_value=[]):
            self.assertEqual(entry.select_reviewers([]), [])

    def test_current_control_plane_keeps_distillery_providers_unadmitted(self) -> None:
        for provider in ("openrouter", "tavily", "exa"):
            self.assertFalse(entry._provider_admitted(provider))


if __name__ == "__main__":
    unittest.main()
