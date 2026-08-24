#!/usr/bin/env python3
"""Red-gate regressions for the direct FREE swarm base controller.

Supervisor 8.67 requires typed provider admission before *any* provider-secret
lookup and before *any* provider network I/O.  Hardening only the EntityOS/HCU
wrapper is insufficient because ``tools/run_free_go_swarm.py`` remains directly
executable/importable.

The canonical admission document on this candidate intentionally admits no
provider yet.  Therefore direct calls into the base controller must be secret-
blind and network-blind even when legacy environment attestation flags and fake
credential values are present.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission_v1 as admission  # noqa: E402
import run_free_go_swarm as base  # noqa: E402


SECRET_NAMES = {
    "GROQ_API_KEY",
    "GROQ_API_KEYS",
    "MISTRAL_API_KEY",
    "MISTRAL_API_KEYS",
    "NVIDIA_API_KEY",
    "NVIDIA_API_KEYS",
    "NGC_API_KEY",
}
SECRET_PREFIXES = (
    "GROQ_API_KEY_",
    "MISTRAL_API_KEY_",
    "NVIDIA_API_KEY_",
    "NGC_API_KEY_",
)


def is_secret_name(name: object) -> bool:
    key = str(name)
    return key in SECRET_NAMES or key.startswith(SECRET_PREFIXES)


class TrapEnv(dict[str, str]):
    """Environment mapping that counts provider-secret *value* reads.

    Iterating variable names is allowed; returning a value for a provider key is
    the credential lookup that must be impossible before typed FREE admission.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.secret_lookup_count = 0

    def _touch(self, key: object) -> None:
        if is_secret_name(key):
            self.secret_lookup_count += 1

    def get(self, key, default=None):  # type: ignore[override]
        self._touch(key)
        return super().get(key, default)

    def __getitem__(self, key):  # type: ignore[override]
        self._touch(key)
        return super().__getitem__(key)

    def items(self):  # type: ignore[override]
        # The pre-8.67 base implementation used ``os.environ.items()`` while
        # discovering suffixed keys.  That reads every environment value, so a
        # blocked provider's credential counts as touched even if its name is
        # later filtered out.
        for key, value in super().items():
            self._touch(key)
            yield key, value


class DirectBaseControllerAdmissionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        for provider in admission.PROVIDERS:
            decision = admission.provider_decision(provider)
            self.assertFalse(decision["admitted"], decision)
            self.assertEqual(decision["cost_class"], "UNKNOWN", decision)

    def test_direct_collect_keys_is_secret_blind_for_unadmitted_providers(self) -> None:
        fixtures = {
            "groq": ("GROQ_API_KEY", "g_fake"),
            "mistral": ("MISTRAL_API_KEY", "m_fake"),
            "nvidia": ("NVIDIA_API_KEY", "n_fake"),
        }
        for spec in base.PROVIDERS:
            key_name, fake_value = fixtures[spec.name]
            env = TrapEnv({
                "CLAY_FREE_ONLY_ATTESTED": "1",
                spec.attestation_env: "1",
                key_name: fake_value,
            })
            with self.subTest(provider=spec.name), mock.patch.object(base.os, "environ", env):
                keys = base.collect_keys(spec)
                self.assertEqual(
                    env.secret_lookup_count,
                    0,
                    f"{spec.name} credential value was read before typed FREE admission",
                )
                self.assertEqual(keys, [], f"{spec.name} returned keys without typed FREE admission")

    def test_direct_request_chat_is_network_blind_for_unadmitted_providers(self) -> None:
        for spec in base.PROVIDERS:
            network_attempt_count = 0

            def socket_tripwire(*_args, **_kwargs):
                nonlocal network_attempt_count
                network_attempt_count += 1
                raise AssertionError("provider network reached before typed FREE admission")

            with self.subTest(provider=spec.name), mock.patch.object(
                base.urllib.request, "urlopen", side_effect=socket_tripwire
            ):
                try:
                    base.request_chat(
                        spec,
                        "fake-key-already-in-caller-memory",
                        "fake-model",
                        "probe",
                        1,
                        0.01,
                    )
                except Exception:
                    # A fail-closed admission exception is acceptable.  The
                    # invariant under test is that no provider socket is touched.
                    pass
                self.assertEqual(
                    network_attempt_count,
                    0,
                    f"{spec.name} attempted provider network before typed FREE admission",
                )


if __name__ == "__main__":
    unittest.main()
