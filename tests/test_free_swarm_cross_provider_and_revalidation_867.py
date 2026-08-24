from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission_mod  # noqa: E402
import run_free_go_swarm as base  # noqa: E402


class TrapEnv(dict[str, str]):
    """Count reads of blocked-provider secret values while allowing name scans."""

    BLOCKED = {
        "MISTRAL_API_KEY",
        "MISTRAL_API_KEYS",
        "NVIDIA_API_KEY",
        "NVIDIA_API_KEYS",
        "NGC_API_KEY",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.blocked_value_reads = 0

    def _touch(self, key: object) -> None:
        name = str(key)
        if name in self.BLOCKED or any(name.startswith(prefix + "_") for prefix in self.BLOCKED):
            self.blocked_value_reads += 1

    def get(self, key, default=None):  # type: ignore[override]
        self._touch(key)
        return super().get(key, default)

    def __getitem__(self, key):  # type: ignore[override]
        self._touch(key)
        return super().__getitem__(key)

    def items(self):  # type: ignore[override]
        # A blocked implementation using os.environ.items() materializes every
        # provider value, including providers that were never admitted.
        for key, value in super().items():
            self._touch(key)
            yield key, value


def admission(*, groq: tuple[bool, str]) -> dict:
    admitted, cost_class = groq
    return {
        "schema": admission_mod.SCHEMA,
        "authority_epoch": "8.67",
        "mode": "FREE_ONLY",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "source": "ENTITYOS_HCU_CONTROL_PLANE",
        "providers": {
            "groq": {"admitted": admitted, "cost_class": cost_class, "evidence_ref": "test:groq"},
            "mistral": {"admitted": False, "cost_class": "UNKNOWN", "evidence_ref": "test:mistral"},
            "nvidia": {"admitted": False, "cost_class": "UNKNOWN", "evidence_ref": "test:nvidia"},
        },
    }


class FreeSwarmAdmissionTailTests(unittest.TestCase):
    def test_admitted_groq_collection_does_not_materialize_blocked_provider_values(self) -> None:
        env = TrapEnv(
            {
                "GROQ_API_KEY": "g_fake",
                "MISTRAL_API_KEY": "m_blocked",
                "NVIDIA_API_KEY": "n_blocked",
                "UNRELATED": "ok",
            }
        )
        with mock.patch.object(base.os, "environ", env):
            keys = base.collect_keys(base.PROVIDERS[0], admission(groq=(True, "FREE")))
        self.assertEqual(keys, ["g_fake"])
        self.assertEqual(
            env.blocked_value_reads,
            0,
            "collecting one admitted provider must not read another blocked provider's secret value",
        )

    def test_request_chat_revalidates_revoked_provider_before_socket(self) -> None:
        network_attempts = 0

        def tripwire(*_args, **_kwargs):
            nonlocal network_attempts
            network_attempts += 1
            raise AssertionError("provider socket reached after admission revocation")

        with mock.patch.object(base, "load_provider_admission", return_value=admission(groq=(False, "UNKNOWN"))), \
             mock.patch.object(base.urllib.request, "urlopen", side_effect=tripwire):
            with self.assertRaisesRegex(RuntimeError, "PROVIDER_NOT_FREE_ADMITTED_BEFORE_NETWORK:groq"):
                base.request_chat(base.PROVIDERS[0], "caller-held-key", "fake-model", "probe", 1, 0.01)
        self.assertEqual(network_attempts, 0)

    def test_request_chat_fails_closed_if_live_admission_document_is_invalid(self) -> None:
        network_attempts = 0

        def tripwire(*_args, **_kwargs):
            nonlocal network_attempts
            network_attempts += 1
            raise AssertionError("provider socket reached with invalid live admission")

        with mock.patch.object(
            base,
            "load_provider_admission",
            side_effect=admission_mod.ProviderAdmissionError("TEST_INVALID"),
        ), mock.patch.object(base.urllib.request, "urlopen", side_effect=tripwire):
            with self.assertRaisesRegex(RuntimeError, "PROVIDER_ADMISSION_INVALID_BEFORE_NETWORK:groq"):
                base.request_chat(base.PROVIDERS[0], "caller-held-key", "fake-model", "probe", 1, 0.01)
        self.assertEqual(network_attempts, 0)


if __name__ == "__main__":
    unittest.main()
