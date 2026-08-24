from __future__ import annotations

from pathlib import Path
import sys
import tempfile
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
    def bomb_repo(self, *args, **kwargs):
        raise AssertionError("repository secret store touched before admission")

    def test_blocked_optional_provider_secret_returns_none_before_any_secret_lookup(self):
        names = ("OPENROUTER_API_KEY", "NVIDIA_API_KEY", "GROQ_API_KEYS", "GROQ2_API_KEY", "MISTRAL_API_KEY_1", "MISTRAL_API_KEY_32", "NVIDIA2_API_KEY", "OPENROUTER_API_KEYS", "HF_TOKEN", "HUGGINGFACE_API_KEY", "TOGETHER_API_KEY")
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=False), mock.patch.object(loader.os, "environ", BombEnvironment()), mock.patch.object(loader, "_lookup_repo_secret", side_effect=self.bomb_repo):
            for name in names:
                with self.subTest(name=name):
                    self.assertIsNone(loader.get_secret(name, required=False))

    def test_blocked_required_provider_secret_raises_before_any_secret_lookup(self):
        names = ("GROQ_API_KEY", "GROQ3_API_KEY", "MISTRAL2_API_KEY", "MISTRAL_API_KEY_17", "NVIDIA_API_KEYS", "NVIDIA3_API_KEY", "OPENROUTER_API_KEY_2", "HF_TOKEN", "HUGGINGFACE_API_KEY", "TOGETHER_API_KEY")
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=False), mock.patch.object(loader.os, "environ", BombEnvironment()), mock.patch.object(loader, "_lookup_repo_secret", side_effect=self.bomb_repo):
            for name in names:
                with self.subTest(name=name):
                    with self.assertRaisesRegex(loader.SecretError, "denied before lookup"):
                        loader.get_secret(name, required=True)

    def test_blocked_provider_secret_source_reports_absent_without_lookup(self):
        names = ("MISTRAL_API_KEY", "MISTRAL_API_KEY_9", "NVIDIA_NIM_API_KEY", "NGC_API_KEY", "HF_TOKEN", "TOGETHER_API_KEY")
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=False), mock.patch.object(loader.os, "environ", BombEnvironment()), mock.patch.object(loader, "_lookup_repo_secret", side_effect=self.bomb_repo):
            for name in names:
                with self.subTest(name=name):
                    self.assertIsNone(loader.secret_source(name))

    def test_admitted_provider_may_read_environment_after_boundary(self):
        env = {"OPENROUTER_API_KEY": "synthetic-test-value"}
        with mock.patch.object(loader, "_provider_secret_is_admitted", return_value=True), mock.patch.object(loader.os, "environ", env), mock.patch.object(loader, "_lookup_repo_secret", side_effect=self.bomb_repo):
            self.assertEqual(loader.get_secret("OPENROUTER_API_KEY", required=True), "synthetic-test-value")

    def test_non_provider_secret_behavior_is_unchanged(self):
        env = {"TAVILY_API_KEY": "synthetic-non-llm-value"}
        with mock.patch.object(loader.os, "environ", env), mock.patch.object(loader, "_lookup_repo_secret", side_effect=self.bomb_repo):
            self.assertEqual(loader.get_secret("TAVILY_API_KEY", required=True), "synthetic-non-llm-value")

    def test_repository_fallback_returns_only_requested_secret_from_mixed_store(self):
        with tempfile.TemporaryDirectory() as td:
            store = Path(td) / "mixed.env"
            store.write_text(
                "OPENROUTER_API_KEY=blocked-provider-sentinel\n"
                "TAVILY_API_KEY=allowed-nonprovider-sentinel\n"
                "GROQ_API_KEY=other-provider-sentinel\n",
                encoding="utf-8",
            )
            with mock.patch.object(loader, "PRIVATE_STORES", [store]):
                value, source = loader._lookup_repo_secret("TAVILY_API_KEY")
            self.assertEqual(value, "allowed-nonprovider-sentinel")
            self.assertEqual(source, "mixed.env")
            self.assertNotIsInstance(value, dict)
            self.assertNotIn("blocked-provider-sentinel", value)
            self.assertNotIn("other-provider-sentinel", value)

    def test_repository_fallback_conflict_is_scoped_to_requested_identity(self):
        with tempfile.TemporaryDirectory() as td:
            first = Path(td) / "first.env"
            second = Path(td) / "second.env"
            first.write_text("TAVILY_API_KEY=one\nGROQ_API_KEY=alpha\n", encoding="utf-8")
            second.write_text("TAVILY_API_KEY=one\nGROQ_API_KEY=beta\n", encoding="utf-8")
            with mock.patch.object(loader, "PRIVATE_STORES", [first, second]):
                value, source = loader._lookup_repo_secret("TAVILY_API_KEY")
            self.assertEqual(value, "one")
            self.assertEqual(source, "second.env")

    def test_repository_fallback_rejects_conflict_for_requested_identity(self):
        with tempfile.TemporaryDirectory() as td:
            first = Path(td) / "first.env"
            second = Path(td) / "second.env"
            first.write_text("TAVILY_API_KEY=one\n", encoding="utf-8")
            second.write_text("TAVILY_API_KEY=two\n", encoding="utf-8")
            with mock.patch.object(loader, "PRIVATE_STORES", [first, second]):
                with self.assertRaisesRegex(loader.SecretError, "conflicting values"):
                    loader._lookup_repo_secret("TAVILY_API_KEY")

    def test_all_current_llm_provider_secret_aliases_are_mapped(self):
        expected = {
            "GROQ_API_KEY": "groq", "GROQ_API_KEYS": "groq", "GROQ2_API_KEY": "groq", "GROQ3_API_KEY": "groq", "GROQ_API_KEY_7": "groq",
            "MISTRAL_API_KEY": "mistral", "MISTRAL_API_KEYS": "mistral", "MISTRAL2_API_KEY": "mistral", "MISTRAL3_API_KEY": "mistral", "MISTRAL_API_KEY_1": "mistral", "MISTRAL_API_KEY_32": "mistral",
            "NVIDIA_API_KEY": "nvidia", "NVIDIA_API_KEYS": "nvidia", "NVIDIA_NIM_API_KEY": "nvidia", "NGC_API_KEY": "nvidia", "NVIDIA2_API_KEY": "nvidia", "NVIDIA3_API_KEY": "nvidia", "NVIDIA_API_KEY_4": "nvidia",
            "OPENROUTER_API_KEY": "openrouter", "OPENROUTER_API_KEYS": "openrouter", "OPENROUTER_API_KEY_3": "openrouter",
            "HF_TOKEN": "huggingface", "HUGGINGFACE_API_KEY": "huggingface", "TOGETHER_API_KEY": "together",
        }
        for name, provider in expected.items():
            with self.subTest(name=name):
                self.assertEqual(loader.provider_for_secret_name(name), provider)

    def test_general_provider_configuration_is_not_misclassified_as_secret(self):
        for name in ("MISTRAL_KEY_POOL", "MISTRAL_API_BASE", "NVIDIA_API_BASE", "OPENROUTER_API_BASE"):
            with self.subTest(name=name):
                self.assertIsNone(loader.provider_for_secret_name(name))


if __name__ == "__main__":
    unittest.main()
