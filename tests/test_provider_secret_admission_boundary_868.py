from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission_mod
import huggingface_inference as hf
import rae_secret_loader as secrets


class TrapEnv(dict[str, str]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.reads: list[str] = []

    def get(self, key, default=None):  # type: ignore[override]
        self.reads.append(str(key))
        return super().get(key, default)


class ProviderSecretAdmissionBoundary868(unittest.TestCase):
    def test_all_legacy_external_provider_secret_names_map_to_typed_authority(self) -> None:
        expected = {
            "GROQ_API_KEY": "groq",
            "GROQ2_API_KEY": "groq",
            "HF_TOKEN": "huggingface",
            "MISTRAL_API_KEY": "mistral",
            "NVIDIA_API_KEY": "nvidia",
            "NGC_API_KEY": "nvidia",
            "OPENROUTER_API_KEY": "openrouter",
        }
        for name, provider in expected.items():
            with self.subTest(name=name):
                self.assertEqual(secrets._provider_for_secret_name(name), provider)
                self.assertIn(provider, admission_mod.ALLOWED_PROVIDERS)

    def test_blocked_provider_secret_lookup_never_reads_environment_or_repo_store(self) -> None:
        env = TrapEnv({"OPENROUTER_API_KEY": "SHOULD_NOT_BE_READ"})
        with mock.patch.object(secrets, "provider_is_admitted_free", create=True) as unused:
            # The loader imports provider_is_admitted_free lazily, so patch the canonical
            # module rather than trusting caller-owned state.
            unused.return_value = False
        with mock.patch.object(admission_mod, "provider_is_admitted_free", return_value=False), \
             mock.patch.object(secrets.os, "environ", env), \
             mock.patch.object(secrets, "_repo_secrets", side_effect=AssertionError("repo credential store reached")):
            with self.assertRaisesRegex(secrets.SecretError, "PROVIDER_SECRET_REQUIRES_TYPED_FREE_ADMISSION:openrouter"):
                secrets.get_secret("OPENROUTER_API_KEY")
        self.assertNotIn("OPENROUTER_API_KEY", env.reads)

    def test_blocked_provider_secret_source_never_reads_environment_or_repo_store(self) -> None:
        env = TrapEnv({"NVIDIA_API_KEY": "SHOULD_NOT_BE_READ"})
        with mock.patch.object(admission_mod, "provider_is_admitted_free", return_value=False), \
             mock.patch.object(secrets.os, "environ", env), \
             mock.patch.object(secrets, "_repo_secrets", side_effect=AssertionError("repo credential store reached")):
            with self.assertRaisesRegex(secrets.SecretError, "PROVIDER_SECRET_REQUIRES_TYPED_FREE_ADMISSION:nvidia"):
                secrets.secret_source("NVIDIA_API_KEY")
        self.assertNotIn("NVIDIA_API_KEY", env.reads)

    def test_huggingface_adapter_blocks_before_secret_and_provider_network(self) -> None:
        secret_reads = 0
        network_attempts = 0

        def secret_tripwire(*args, **kwargs):
            nonlocal secret_reads
            secret_reads += 1
            raise AssertionError("HF_TOKEN reached")

        def network_tripwire(*args, **kwargs):
            nonlocal network_attempts
            network_attempts += 1
            raise AssertionError("Hugging Face network reached")

        with mock.patch.object(hf, "provider_is_admitted_free", return_value=False), \
             mock.patch.object(hf, "get_secret", side_effect=secret_tripwire), \
             mock.patch.object(hf.urllib.request, "urlopen", side_effect=network_tripwire):
            with self.assertRaisesRegex(admission_mod.ProviderAdmissionError, "PROVIDER_NETWORK_REQUIRES_TYPED_FREE_ADMISSION:huggingface"):
                hf.list_models(limit=1)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network_attempts, 0)


if __name__ == "__main__":
    unittest.main()
