from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission_mod
import run_free_go_swarm as base
import run_24h_entityos_swarm as entityos_driver
import run_research_distillery_entry as distillery_entry


SECRET_ENV_NAMES = {
    "GROQ_API_KEY", "GROQ_API_KEYS", "GROQ2_API_KEY", "GROQ3_API_KEY",
    "MISTRAL_API_KEY", "MISTRAL_API_KEYS", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY",
    "NVIDIA_API_KEY", "NVIDIA_API_KEYS", "NVIDIA_NIM_API_KEY", "NGC_API_KEY",
    "NVIDIA2_API_KEY", "NVIDIA3_API_KEY", "OPENROUTER_API_KEY",
}
PROVIDERS = ("groq", "mistral", "nvidia", "openrouter")
CANONICAL_ADMISSION_REL = Path("research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")


def _authority(root: Path, epoch: str = "8.68") -> Path:
    rel = Path("research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json")
    steering = root / rel
    steering.parent.mkdir(parents=True, exist_ok=True)
    steering.write_text(json.dumps({
        "schema_version": epoch,
        "active_program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "integrated_cognition_compute_architecture": "HCU",
    }), encoding="utf-8")
    inbox = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox.write_text(json.dumps({"schema_version": epoch, "steering": rel.as_posix()}), encoding="utf-8")
    return inbox


def _admission(root: Path, cost_class: str, admitted: bool, epoch: str = "8.68") -> Path:
    # Match load_provider_admission()'s production default resolution exactly.
    target = root / CANONICAL_ADMISSION_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    providers = {
        name: {"admitted": admitted, "cost_class": cost_class, "evidence_ref": f"test:{name}:{cost_class}"}
        for name in PROVIDERS
    }
    target.write_text(json.dumps({
        "schema": admission_mod.SCHEMA,
        "authority_epoch": epoch,
        "mode": "FREE_ONLY",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "source": "ENTITYOS_HCU_CONTROL_PLANE",
        "providers": providers,
    }), encoding="utf-8")
    return target


def _args(output_dir: str) -> argparse.Namespace:
    return argparse.Namespace(
        hours=0.001,
        max_tokens=8,
        context_chars=128,
        timeout=0.1,
        drain_seconds=0.1,
        output_dir=output_dir,
    )


class SocketTripwire:
    """Global stdlib network tripwire; catches new HTTP paths below their wrapper layer."""

    def __init__(self) -> None:
        self.attempts: list[str] = []
        self._patchers = [
            mock.patch.object(socket, "create_connection", side_effect=self._trip("create_connection")),
            mock.patch.object(socket, "getaddrinfo", side_effect=self._trip("getaddrinfo")),
            mock.patch.object(socket.socket, "connect", side_effect=self._trip("socket.connect")),
            mock.patch.object(socket.socket, "connect_ex", side_effect=self._trip("socket.connect_ex")),
        ]

    def _trip(self, name: str):
        def fail(*args, **kwargs):
            self.attempts.append(name)
            raise AssertionError(f"network attempted before typed FREE admission: {name}")
        return fail

    def __enter__(self):
        for patcher in self._patchers:
            patcher.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        for patcher in reversed(self._patchers):
            patcher.stop()
        return False


class FreeProviderSocketBoundaryTests(unittest.TestCase):
    def _patch_authority(self, root: Path, admission_path: Path, inbox_path: Path):
        return (
            mock.patch.object(admission_mod, "ROOT", root),
            mock.patch.object(admission_mod, "ADMISSION_PATH", admission_path),
            mock.patch.object(admission_mod, "SUPERVISOR_INBOX_PATH", inbox_path),
        )

    def _run_base_blocked(self, cost_class: str) -> tuple[int, int, int]:
        secret_reads = 0
        original_getenv = os.getenv

        def guarded_getenv(name: str, default=None):
            nonlocal secret_reads
            if name in SECRET_ENV_NAMES or any(name.startswith(prefix + "_") for prefix in SECRET_ENV_NAMES):
                secret_reads += 1
                raise AssertionError(f"secret lookup before typed FREE admission: {name}")
            return original_getenv(name, default)

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as out:
            root = Path(td)
            adm = _admission(root, cost_class, False)
            inbox = _authority(root)
            p_root, p_adm, p_inbox = self._patch_authority(root, adm, inbox)
            with p_root, p_adm, p_inbox, SocketTripwire() as tripwire, \
                 mock.patch.object(base, "load_protocol", return_value=base.PROTOCOL_BEGIN + "\n" + base.PROTOCOL_END), \
                 mock.patch.object(base.os, "getenv", side_effect=guarded_getenv), \
                 mock.patch.dict(os.environ, {"CLAY_FREE_ONLY_ATTESTED": "1"}, clear=True):
                code = asyncio.run(base.run(_args(out)))
            return code, secret_reads, len(tripwire.attempts)

    def test_fixture_path_matches_production_default_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = _admission(root, "UNKNOWN", False)
            self.assertEqual(target, root / CANONICAL_ADMISSION_REL)
            self.assertTrue(target.is_file())
            self.assertFalse((root / "admission.json").exists())

    def test_unknown_paid_subscription_have_zero_secret_reads_and_zero_socket_activity(self) -> None:
        for cost_class in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost_class=cost_class):
                code, secret_reads, network_attempts = self._run_base_blocked(cost_class)
                self.assertEqual(code, 4)
                self.assertEqual(secret_reads, 0)
                self.assertEqual(network_attempts, 0)

    def test_blocked_catalog_has_zero_socket_activity_without_wrapper_mock(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "UNKNOWN", False)
            inbox = _authority(root)
            p_root, p_adm, p_inbox = self._patch_authority(root, adm, inbox)
            with p_root, p_adm, p_inbox, SocketTripwire() as tripwire, \
                 mock.patch.dict(os.environ, {"CLAY_FREE_ONLY_ATTESTED": "1"}, clear=True), \
                 mock.patch.object(base, "collect_keys", side_effect=AssertionError("credential collection called")):
                report = entityos_driver.discover_and_export(0.1)
            self.assertTrue(report)
            self.assertTrue(all(v["source"] == "typed_admission_blocked" for v in report.values()))
            self.assertEqual(tripwire.attempts, [])

    def test_blocked_distillery_openrouter_has_zero_socket_activity_without_request_wrapper_mock(self) -> None:
        with SocketTripwire() as tripwire, \
             mock.patch.object(distillery_entry, "provider_is_admitted_free", return_value=False), \
             mock.patch.object(distillery_entry, "_ORIGINAL_SECRET", side_effect=AssertionError("secret lookup called")):
            self.assertEqual(distillery_entry.admitted_secret("OPENROUTER_API_KEY"), "")
            status, _, body = distillery_entry.admitted_request_json(
                "openrouter", "test", "https://invalid.example"
            )
        self.assertEqual(status, 412)
        self.assertEqual(body.get("error"), "PROVIDER_NOT_TYPED_FREE_ADMITTED")
        self.assertEqual(tripwire.attempts, [])


if __name__ == "__main__":
    unittest.main()
