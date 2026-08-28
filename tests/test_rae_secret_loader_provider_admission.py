from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import rae_secret_loader as loader


class BombEnvironment(dict):
    def get(self, key, default=None):
        raise AssertionError(f"environment touched before admission: {key}")

    def __iter__(self):
        raise AssertionError("environment iterated before admission")


class ProviderSecretAdmissionTests(unittest.TestCase):
    def bomb_repo(self):
        raise AssertionError("repository secret store touched before admission")

    def test_blocked_optional_provider_secret_returns_none_before_any_secret_lookup(self):
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=False), \
             mock.patch.object(loader.os, "environ", BombEnvironment()), \
             mock.patch.object(loader, "_repo_secrets", side_effect=self.bomb_repo):
            self.assertIsNone(loader.get_secret("OPENROUTER_API_KEY", required=False))
            self.assertIsNone(loader.get_secret("NVIDIA_API_KEY", required=False))

    def test_blocked_required_provider_secret_raises_before_any_secret_lookup(self):
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=False), \
             mock.patch.object(loader.os, "environ", BombEnvironment()), \
             mock.patch.object(loader, "_repo_secrets", side_effect=self.bomb_repo):
            with self.assertRaisesRegex(loader.SecretError, "denied before lookup"):
                loader.get_secret("GROQ_API_KEY", required=True)

    def test_blocked_provider_secret_source_reports_absent_without_lookup(self):
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=False), \
             mock.patch.object(loader.os, "environ", BombEnvironment()), \
             mock.patch.object(loader, "_repo_secrets", side_effect=self.bomb_repo):
            self.assertIsNone(loader.secret_source("MISTRAL_API_KEY"))

    def test_admitted_provider_may_read_environment_after_admission(self):
        env = {"OPENROUTER_API_KEY": "synthetic-test-value"}
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=True), \
             mock.patch.object(loader.os, "environ", env), \
             mock.patch.object(loader, "_repo_secrets", side_effect=self.bomb_repo):
            self.assertEqual(
                loader.get_secret("OPENROUTER_API_KEY", required=True),
                "synthetic-test-value",
            )

    def test_non_provider_secret_behavior_is_unchanged(self):
        env = {"TAVILY_API_KEY": "synthetic-non-llm-value"}
        with mock.patch.object(loader.os, "environ", env), \
             mock.patch.object(loader, "_repo_secrets", side_effect=self.bomb_repo):
            self.assertEqual(
                loader.get_secret("TAVILY_API_KEY", required=True),
                "synthetic-non-llm-value",
            )

    def test_all_current_llm_provider_secret_names_are_mapped(self):
        self.assertEqual(
            loader.PROVIDER_SECRET_NAMES,
            {
                "GROQ_API_KEY": "groq",
                "MISTRAL_API_KEY": "mistral",
                "NVIDIA_API_KEY": "nvidia",
                "NVIDIA_NIM_API_KEY": "nvidia",
                "NGC_API_KEY": "nvidia",
                "OPENROUTER_API_KEY": "openrouter",
            },
        )


if __name__ == "__main__":
    unittest.main()
