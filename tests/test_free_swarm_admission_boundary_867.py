from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
from pathlib import Path
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


SECRET_ENV_NAMES = {
    "GROQ_API_KEY", "GROQ_API_KEYS", "GROQ2_API_KEY", "GROQ3_API_KEY",
    "MISTRAL_API_KEY", "MISTRAL_API_KEYS", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY",
    "NVIDIA_API_KEY", "NVIDIA_API_KEYS", "NVIDIA_NIM_API_KEY", "NGC_API_KEY",
    "NVIDIA2_API_KEY", "NVIDIA3_API_KEY",
}


def _bootstrap(path: Path, epoch: str = "8.67") -> Path:
    target = path / "bootstrap.json"
    target.write_text(json.dumps({"schema_version": epoch}), encoding="utf-8")
    return target


def _admission(path: Path, cost_class: str, admitted: bool, epoch: str = "8.67") -> Path:
    target = path / "admission.json"
    providers = {
        name: {
            "admitted": admitted,
            "cost_class": cost_class,
            "evidence_ref": f"test:{name}:{cost_class}",
        }
        for name in ("groq", "mistral", "nvidia")
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


class FreeProviderAdmissionBoundaryTests(unittest.TestCase):
    def _run_with_tripwires(self, admission_path: Path, bootstrap_path: Path, *, global_attested: bool) -> tuple[int, int, int]:
        secret_reads = 0
        network_attempts = 0
        original_getenv = os.getenv

        def guarded_getenv(name: str, default=None):
            nonlocal secret_reads
            if name in SECRET_ENV_NAMES or any(name.startswith(x + "_") for x in SECRET_ENV_NAMES):
                secret_reads += 1
                raise AssertionError(f"secret lookup before admission: {name}")
            return original_getenv(name, default)

        def network_tripwire(*args, **kwargs):
            nonlocal network_attempts
            network_attempts += 1
            raise AssertionError("network attempted before FREE admission")

        env = {"CLAY_FREE_ONLY_ATTESTED": "1"} if global_attested else {}
        with tempfile.TemporaryDirectory() as out, \
             mock.patch.object(admission_mod, "ADMISSION_PATH", admission_path), \
             mock.patch.object(admission_mod, "BOOTSTRAP_PATH", bootstrap_path), \
             mock.patch.object(base, "load_protocol", return_value=base.PROTOCOL_BEGIN + "\n" + base.PROTOCOL_END), \
             mock.patch.object(base.os, "getenv", side_effect=guarded_getenv), \
             mock.patch.object(base, "request_chat", side_effect=network_tripwire), \
             mock.patch.object(base.urllib.request, "urlopen", side_effect=network_tripwire), \
             mock.patch.dict(os.environ, env, clear=True):
            code = asyncio.run(base.run(_args(out)))
        return code, secret_reads, network_attempts

    def test_global_attestation_missing_has_zero_secret_and_network_access(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "FREE", True)
            boot = _bootstrap(root)
            code, secret_reads, network = self._run_with_tripwires(adm, boot, global_attested=False)
        self.assertEqual(code, 3)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_unknown_paid_subscription_all_fail_before_secret_or_network(self) -> None:
        for cost_class in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost_class=cost_class), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                adm = _admission(root, cost_class, False)
                boot = _bootstrap(root)
                code, secret_reads, network = self._run_with_tripwires(adm, boot, global_attested=True)
                self.assertEqual(code, 4)
                self.assertEqual(secret_reads, 0)
                self.assertEqual(network, 0)

    def test_missing_provider_admission_file_fails_before_secret_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "missing.json"
            boot = _bootstrap(root)
            code, secret_reads, network = self._run_with_tripwires(missing, boot, global_attested=True)
        self.assertEqual(code, 5)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_nonfree_record_cannot_self_admit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "PAID", True)
            boot = _bootstrap(root)
            with self.assertRaises(admission_mod.ProviderAdmissionError):
                admission_mod.load_provider_admission(adm, bootstrap_path=boot)

    def test_authority_epoch_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "FREE", True, epoch="8.67")
            boot = _bootstrap(root, epoch="8.68")
            with self.assertRaisesRegex(admission_mod.ProviderAdmissionError, "AUTHORITY_EPOCH_MISMATCH"):
                admission_mod.load_provider_admission(adm, bootstrap_path=boot)

    def test_collect_keys_does_not_read_key_env_when_provider_not_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "UNKNOWN", False)
            boot = _bootstrap(root)
            with mock.patch.object(admission_mod, "ADMISSION_PATH", adm), \
                 mock.patch.object(admission_mod, "BOOTSTRAP_PATH", boot), \
                 mock.patch.object(base.os, "getenv", side_effect=AssertionError("key env read")):
                self.assertEqual(base.collect_keys(base.PROVIDERS[0]), [])

    def test_catalog_discovery_does_not_collect_keys_or_touch_network_when_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "UNKNOWN", False)
            boot = _bootstrap(root)
            with mock.patch.object(admission_mod, "ADMISSION_PATH", adm), \
                 mock.patch.object(admission_mod, "BOOTSTRAP_PATH", boot), \
                 mock.patch.dict(os.environ, {"CLAY_FREE_ONLY_ATTESTED": "1"}, clear=True), \
                 mock.patch.object(base, "collect_keys", side_effect=AssertionError("secret collection called")), \
                 mock.patch.object(entityos_driver, "fetch_catalog", side_effect=AssertionError("network catalog called")):
                report = entityos_driver.discover_and_export(0.1)
        self.assertTrue(report)
        self.assertTrue(all(v["source"] == "typed_admission_blocked" for v in report.values()))

    def test_supervisor_sources_only_through_admission_gated_entrypoint(self) -> None:
        text = (ROOT / "tools/run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        self.assertNotIn("load_all_secret_sources", text)
        self.assertIn("typed_admission_compat_flags\nload_admitted_secret_sources", text)
        self.assertIn("provider_admitted groq", text)
        self.assertIn("run_research_distillery_entry.py", text)
        self.assertIn("EXPIRED_WITHOUT_CANONICALLY_FREE_ADMITTED_PROVIDER", text)


if __name__ == "__main__":
    unittest.main()
