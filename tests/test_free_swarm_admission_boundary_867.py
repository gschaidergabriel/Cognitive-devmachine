from __future__ import annotations

import argparse
import asyncio
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
import free_lane_provenance as lane_prov
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


def _canonical_admission_path(root: Path) -> Path:
    target = root / CANONICAL_ADMISSION_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


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
    inbox.write_text(json.dumps({
        "schema_version": epoch,
        "steering": rel.as_posix(),
    }), encoding="utf-8")
    return inbox


def _admission(root: Path, cost_class: str, admitted: bool, epoch: str = "8.68") -> Path:
    target = _canonical_admission_path(root)
    providers = {
        name: {
            "admitted": admitted,
            "cost_class": cost_class,
            "evidence_ref": f"test:{name}:{cost_class}",
        }
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


def _mixed_admission(root: Path, epoch: str = "8.68") -> Path:
    target = _canonical_admission_path(root)
    target.write_text(json.dumps({
        "schema": admission_mod.SCHEMA,
        "authority_epoch": epoch,
        "mode": "FREE_ONLY",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "source": "ENTITYOS_HCU_CONTROL_PLANE",
        "providers": {
            "groq": {"admitted": True, "cost_class": "FREE", "evidence_ref": "test:groq:free"},
            "mistral": {"admitted": False, "cost_class": "UNKNOWN", "evidence_ref": "test:mistral:unknown"},
            "nvidia": {"admitted": False, "cost_class": "UNKNOWN", "evidence_ref": "test:nvidia:unknown"},
            "openrouter": {"admitted": False, "cost_class": "UNKNOWN", "evidence_ref": "test:openrouter:unknown"},
        },
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


class TrapEnv(dict[str, str]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.secret_reads: list[str] = []

    def _touch(self, key: object) -> None:
        name = str(key)
        if name in SECRET_ENV_NAMES or any(name.startswith(prefix + "_") for prefix in SECRET_ENV_NAMES):
            self.secret_reads.append(name)

    def get(self, key, default=None):  # type: ignore[override]
        self._touch(key)
        return super().get(key, default)

    def __getitem__(self, key):  # type: ignore[override]
        self._touch(key)
        return super().__getitem__(key)

    def items(self):  # type: ignore[override]
        for key, value in super().items():
            self._touch(key)
            yield key, value


class FreeProviderAdmissionBoundaryTests(unittest.TestCase):
    def _patch_authority(self, root: Path, admission_path: Path, inbox_path: Path):
        return (
            mock.patch.object(admission_mod, "ROOT", root),
            mock.patch.object(admission_mod, "ADMISSION_PATH", admission_path),
            mock.patch.object(admission_mod, "SUPERVISOR_INBOX_PATH", inbox_path),
        )

    def _run_with_tripwires(self, admission_path: Path, root: Path, inbox_path: Path, *, global_attested: bool) -> tuple[int, int, int]:
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
        p_root, p_adm, p_inbox = self._patch_authority(root, admission_path, inbox_path)
        with tempfile.TemporaryDirectory() as out, p_root, p_adm, p_inbox, \
             mock.patch.object(base, "load_protocol", return_value=base.PROTOCOL_BEGIN + "\n" + base.PROTOCOL_END), \
             mock.patch.object(base.os, "getenv", side_effect=guarded_getenv), \
             mock.patch.object(base.urllib.request, "urlopen", side_effect=network_tripwire), \
             mock.patch.dict(os.environ, env, clear=True):
            code = asyncio.run(base.run(_args(out)))
        return code, secret_reads, network_attempts

    def test_fixture_uses_same_canonical_path_as_production_loader(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "UNKNOWN", False)
        self.assertEqual(adm.relative_to(root), CANONICAL_ADMISSION_REL)

    def test_global_attestation_missing_has_zero_secret_and_network_access(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "FREE", True)
            inbox = _authority(root)
            code, secret_reads, network = self._run_with_tripwires(adm, root, inbox, global_attested=False)
        self.assertEqual(code, 3)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_unknown_paid_subscription_all_fail_before_secret_or_network(self) -> None:
        for cost_class in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost_class=cost_class), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                adm = _admission(root, cost_class, False)
                inbox = _authority(root)
                code, secret_reads, network = self._run_with_tripwires(adm, root, inbox, global_attested=True)
                self.assertEqual(code, 4)
                self.assertEqual(secret_reads, 0)
                self.assertEqual(network, 0)

    def test_missing_provider_admission_file_fails_before_secret_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = _canonical_admission_path(root)
            inbox = _authority(root)
            code, secret_reads, network = self._run_with_tripwires(missing, root, inbox, global_attested=True)
        self.assertEqual(code, 5)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_malformed_provider_admission_fails_before_secret_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            malformed = _canonical_admission_path(root)
            malformed.write_text("{not-json", encoding="utf-8")
            inbox = _authority(root)
            code, secret_reads, network = self._run_with_tripwires(malformed, root, inbox, global_attested=True)
        self.assertEqual(code, 5)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_nonfree_record_cannot_self_admit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "PAID", True)
            inbox = _authority(root)
            with self.assertRaises(admission_mod.ProviderAdmissionError):
                admission_mod.load_provider_admission(adm, supervisor_inbox_path=inbox, root=root)

    def test_authority_epoch_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "FREE", True, epoch="8.67")
            inbox = _authority(root, epoch="8.68")
            with self.assertRaisesRegex(admission_mod.ProviderAdmissionError, "AUTHORITY_EPOCH_MISMATCH"):
                admission_mod.load_provider_admission(adm, supervisor_inbox_path=inbox, root=root)

    def test_authority_epoch_mismatch_has_zero_secret_and_network_access(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "FREE", True, epoch="8.67")
            inbox = _authority(root, epoch="8.68")
            code, secret_reads, network = self._run_with_tripwires(adm, root, inbox, global_attested=True)
        self.assertEqual(code, 5)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_unlisted_provider_fails_closed(self) -> None:
        self.assertFalse(admission_mod.provider_is_admitted_free("unlisted-provider"))

    def test_unlisted_provider_record_has_zero_secret_and_network_access(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "FREE", True)
            payload = json.loads(adm.read_text(encoding="utf-8"))
            payload["providers"]["unlisted-provider"] = {
                "admitted": True,
                "cost_class": "FREE",
                "evidence_ref": "test:unlisted:must-reject",
            }
            adm.write_text(json.dumps(payload), encoding="utf-8")
            inbox = _authority(root)
            code, secret_reads, network = self._run_with_tripwires(adm, root, inbox, global_attested=True)
        self.assertEqual(code, 5)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_openrouter_provider_admission_does_not_self_admit_unknown_route(self) -> None:
        self.assertIn("openrouter", admission_mod.ALLOWED_PROVIDERS)
        self.assertTrue(admission_mod.provider_is_admitted_free("openrouter"))
        evidence = lane_prov.lane_evidence(
            "openrouter",
            "TEST_CREDENTIAL_FINGERPRINT",
            "not-an-admitted-free-route",
            "https://openrouter.ai/api/v1",
        )
        self.assertFalse(evidence.get("ok"))
        self.assertEqual(evidence.get("reason"), "OPENROUTER_ROUTE_NOT_EXPLICIT_ZERO_PRICE")

    def test_collect_keys_ignores_caller_forged_admission(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "UNKNOWN", False)
            inbox = _authority(root)
            forged = {"providers": {"groq": {"admitted": True, "cost_class": "FREE"}}}
            env = TrapEnv({
                "CLAY_FREE_ONLY_ATTESTED": "1",
                "CLAY_GROQ_FREE_ATTESTED": "1",
                "GROQ_API_KEY": "SECRET_TRIPWIRE",
            })
            p_root, p_adm, p_inbox = self._patch_authority(root, adm, inbox)
            with p_root, p_adm, p_inbox, mock.patch.object(base.os, "environ", env):
                self.assertEqual(base.collect_keys(base.PROVIDERS[0], forged), [])
            self.assertNotIn("GROQ_API_KEY", env.secret_reads)

    def test_admitted_provider_does_not_materialize_blocked_provider_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _mixed_admission(root)
            inbox = _authority(root)
            env = TrapEnv({
                "CLAY_FREE_ONLY_ATTESTED": "1",
                "CLAY_GROQ_FREE_ATTESTED": "1",
                "GROQ_API_KEY": "g_fake",
                "NVIDIA_API_KEY": "n_blocked_secret",
                "OPENROUTER_API_KEY": "or_blocked_secret",
            })
            p_root, p_adm, p_inbox = self._patch_authority(root, adm, inbox)
            with p_root, p_adm, p_inbox, mock.patch.object(base.os, "environ", env):
                keys = base.collect_keys(base.PROVIDERS[0])
            self.assertEqual(keys, ["g_fake"])
            self.assertNotIn("NVIDIA_API_KEY", env.secret_reads)
            self.assertNotIn("OPENROUTER_API_KEY", env.secret_reads)

    def test_direct_request_chat_is_network_blind_without_canonical_free_admission(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "UNKNOWN", False)
            inbox = _authority(root)
            env = {"CLAY_FREE_ONLY_ATTESTED": "1", "CLAY_GROQ_FREE_ATTESTED": "1"}
            network_attempts = 0

            def network_tripwire(*args, **kwargs):
                nonlocal network_attempts
                network_attempts += 1
                raise AssertionError("provider socket reached")

            p_root, p_adm, p_inbox = self._patch_authority(root, adm, inbox)
            with p_root, p_adm, p_inbox, mock.patch.dict(os.environ, env, clear=True), \
                 mock.patch.object(base.urllib.request, "urlopen", side_effect=network_tripwire):
                with self.assertRaises(admission_mod.ProviderAdmissionError):
                    base.request_chat(base.PROVIDERS[0], "fake-key", "fake-model", "probe", 1, 0.01)
            self.assertEqual(network_attempts, 0)

    def test_catalog_discovery_does_not_collect_keys_or_touch_network_when_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adm = _admission(root, "UNKNOWN", False)
            inbox = _authority(root)
            p_root, p_adm, p_inbox = self._patch_authority(root, adm, inbox)
            with p_root, p_adm, p_inbox, \
                 mock.patch.dict(os.environ, {"CLAY_FREE_ONLY_ATTESTED": "1"}, clear=True), \
                 mock.patch.object(base, "collect_keys", side_effect=AssertionError("secret collection called")), \
                 mock.patch.object(entityos_driver, "fetch_catalog", side_effect=AssertionError("network catalog called")):
                report = entityos_driver.discover_and_export(0.1)
        self.assertTrue(report)
        self.assertTrue(all(v["source"] == "typed_admission_blocked" for v in report.values()))

    def test_distillery_openrouter_secret_and_network_are_blind_when_unadmitted(self) -> None:
        secret_reads = 0
        network_attempts = 0

        def secret_tripwire(name: str) -> str:
            nonlocal secret_reads
            secret_reads += 1
            raise AssertionError(f"distillery secret reached: {name}")

        def network_tripwire(*args, **kwargs):
            nonlocal network_attempts
            network_attempts += 1
            raise AssertionError("distillery provider network reached")

        with mock.patch.object(distillery_entry, "_ORIGINAL_SECRET", side_effect=secret_tripwire), \
             mock.patch.object(distillery_entry, "_ORIGINAL_REQUEST_JSON", side_effect=network_tripwire), \
             mock.patch.object(distillery_entry, "provider_is_admitted_free", return_value=False):
            self.assertEqual(distillery_entry.admitted_secret("OPENROUTER_API_KEY"), "")
            status, headers, body = distillery_entry.admitted_request_json("openrouter", "test", "https://invalid.example")
        self.assertEqual(status, 412)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network_attempts, 0)
        self.assertEqual(body.get("error"), "PROVIDER_NOT_TYPED_FREE_ADMITTED")

    def test_supervisor_sources_only_through_admission_gated_entrypoint(self) -> None:
        text = (ROOT / "tools/run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        self.assertNotIn("load_all_secret_sources", text)
        loop = text[text.index("while (( $(date +%s) < DEADLINE )); do"):]
        self.assertIn("typed_admission_compat_flags", loop)
        self.assertIn("load_admitted_secret_sources", loop)
        self.assertLess(loop.index("typed_admission_compat_flags"), loop.index("load_admitted_secret_sources"))
        self.assertIn("provider_admitted groq", text)
        self.assertIn("run_research_distillery_", text)
        self.assertIn("start_local_model", text)
        self.assertIn("start_forge", text)
        self.assertIn("stop_unadmitted_go_swarm", text)
        self.assertIn("start_go_swarm_if_admitted", text)
        self.assertIn("EXTERNAL_LLM_SWARM_ONLY_WHEN_TYPED_FREE_ADMITTED", text)
        self.assertIn("LOOPBACK_4B+PUBLIC_FORGE_CONTINUE_DURING_QUARANTINE", text)
        self.assertNotIn("EXPIRED_WITHOUT_CANONICALLY_FREE_ADMITTED_PROVIDER", text)
        self.assertIn('"state":"EXPIRED"', text)


if __name__ == "__main__":
    unittest.main()
