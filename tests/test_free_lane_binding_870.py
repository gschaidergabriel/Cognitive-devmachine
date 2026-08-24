from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_lane_provenance as provenance


class FreeLaneBinding870Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.artifacts = root / "artifacts"
        self.admission = root / "FREE_PROVIDER_ADMISSION.json"
        self.economic = root / "FREE_LANE_ECONOMIC_PROVENANCE.json"
        self.supervisor_dir = root / "research_entity/claycode/autonomous"
        self.supervisor_dir.mkdir(parents=True)
        self.inbox = self.supervisor_dir / "SUPERVISOR_INBOX.json"
        self.steering = self.supervisor_dir / "SUPERVISOR_STEERING_8_70.json"
        self.admission.write_text(
            json.dumps(
                {
                    "schema": provenance.ADMISSION_SCHEMA,
                    "authority_epoch": "8.70",
                    "mode": "FREE_ONLY",
                    "providers": {
                        "openrouter": {"admitted": True, "cost_class": "FREE"}
                    },
                }
            ),
            encoding="utf-8",
        )
        self.economic.write_text(
            json.dumps(
                {
                    "schema": provenance.PROVENANCE_SCHEMA,
                    "authority_epoch": "8.70",
                    "mode": "FREE_ONLY",
                    "providers": {
                        "openrouter": {
                            "allowed_endpoint_host": "openrouter.ai",
                            "allowed_routes": ["openrouter/free"],
                            "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                            "source": "fixture",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.inbox.write_text(
            json.dumps(
                {
                    "schema_version": "8.70",
                    "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_70.json",
                }
            ),
            encoding="utf-8",
        )
        self._write_steering()
        self.old_root = provenance.ROOT
        self.old_admission_path = provenance.ADMISSION_PATH
        self.old_provenance_path = provenance.PROVENANCE_PATH
        self.old_inbox_path = provenance.SUPERVISOR_INBOX_PATH
        provenance.ROOT = root
        provenance.ADMISSION_PATH = self.admission
        provenance.PROVENANCE_PATH = self.economic
        provenance.SUPERVISOR_INBOX_PATH = self.inbox

    def tearDown(self) -> None:
        provenance.ROOT = self.old_root
        provenance.ADMISSION_PATH = self.old_admission_path
        provenance.PROVENANCE_PATH = self.old_provenance_path
        provenance.SUPERVISOR_INBOX_PATH = self.old_inbox_path
        sys.modules.pop("run_6000_free_swarm_v3_870_test", None)
        sys.modules.pop("run_6000_free_swarm", None)
        self.tmp.cleanup()

    def _write_steering(
        self,
        *,
        epoch: str = "8.70",
        execution_state: str = "FREE_CONTINGENTS_AUTHORIZED_PENDING_PER_LANE_COST_PROVENANCE",
        contingents: list[str] | None = None,
    ) -> None:
        self.steering.write_text(
            json.dumps(
                {
                    "schema_version": epoch,
                    "active_program": "ENTITYOS_HCU",
                    "product": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "free_only": {
                        "enabled": True,
                        "no_paid_fallback": True,
                        "execution_state": execution_state,
                        "owner_authorized_free_contingents": contingents
                        if contingents is not None
                        else ["openrouter"],
                    },
                }
            ),
            encoding="utf-8",
        )

    def _endpoint(self) -> str:
        return "https://openrouter.ai/api/v1/chat/completions"

    def _binding(self) -> dict:
        return provenance.current_lane_binding(
            "openrouter",
            "fp",
            "openrouter/free",
            self._endpoint(),
            artifacts=self.artifacts,
        )

    def _revoke_openrouter(self) -> None:
        obj = json.loads(self.admission.read_text(encoding="utf-8"))
        obj["providers"]["openrouter"]["admitted"] = False
        self.admission.write_text(json.dumps(obj), encoding="utf-8")

    def _load_v3(self, request_impl):
        class Spec:
            name = "openrouter"
            endpoint = "https://openrouter.ai/api/v1/chat/completions"

        class Runtime:
            def __init__(self) -> None:
                self.spec = Spec()
                self.keys = ["secret"]
                self.models = ["openrouter/free"]

            def next_key_model(self):
                return "secret", "openrouter/free"

        base = types.SimpleNamespace(
            request_chat=request_impl,
            key_fingerprint=lambda _key: "fp",
            git_text=lambda *_args: "deadbeef",
            usage_from=lambda payload: payload.get("usage", {})
            if isinstance(payload, dict)
            else {},
            ProviderSpec=Spec,
        )
        fabric = types.ModuleType("run_6000_free_swarm")
        fabric.base = base
        fabric.FastProviderRuntime = Runtime
        fabric.ARTIFACT_ROOT = self.artifacts
        fabric.run = lambda *_args: None
        fabric.parse_args = lambda: None
        sys.modules["run_6000_free_swarm"] = fabric

        spec = importlib.util.spec_from_file_location(
            "run_6000_free_swarm_v3_870_test", TOOLS / "run_6000_free_swarm_v3.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module, Spec

    def test_current_binding_rejects_revoked_provider(self) -> None:
        self.assertTrue(self._binding()["ok"])
        self._revoke_openrouter()
        binding = self._binding()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "PROVIDER_NOT_CURRENTLY_ADMITTED")

    def test_current_binding_rejects_supervisor_epoch_advance_with_stale_lane_files(self) -> None:
        self.assertTrue(self._binding()["ok"])
        newer = self.supervisor_dir / "SUPERVISOR_STEERING_8_71.json"
        newer.write_text(
            json.dumps(
                {
                    "schema_version": "8.71",
                    "active_program": "ENTITYOS_HCU",
                    "product": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "free_only": {
                        "enabled": True,
                        "no_paid_fallback": True,
                        "execution_state": "AUTHORIZED",
                        "owner_authorized_free_contingents": ["openrouter"],
                    },
                }
            ),
            encoding="utf-8",
        )
        self.inbox.write_text(
            json.dumps(
                {
                    "schema_version": "8.71",
                    "steering": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_71.json",
                }
            ),
            encoding="utf-8",
        )
        binding = self._binding()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "FREE_LANE_SUPERVISOR_EPOCH_MISMATCH")

    def test_current_binding_rejects_supervisor_runtime_quarantine(self) -> None:
        self.assertTrue(self._binding()["ok"])
        self._write_steering(execution_state="RUNTIME_QUARANTINED")
        binding = self._binding()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "FREE_LANE_AUTHORITY_SNAPSHOT_INVALID")
        self.assertIn("SUPERVISOR_EXTERNAL_PROVIDER_EXECUTION_NOT_AUTHORIZED", binding["detail"])

    def test_current_binding_rejects_provider_removed_from_supervisor_contingents(self) -> None:
        self.assertTrue(self._binding()["ok"])
        self._write_steering(contingents=["groq"])
        binding = self._binding()
        self.assertFalse(binding["ok"])
        self.assertEqual(binding["reason"], "PROVIDER_NOT_AUTHORIZED_BY_CURRENT_SUPERVISOR")

    def test_binding_still_current_rejects_supervisor_mutation(self) -> None:
        binding = self._binding()
        self.assertTrue(binding["ok"])
        self._write_steering(contingents=["openrouter", "groq"])
        self.assertFalse(provenance.binding_still_current(binding))

    def test_receipt_keeps_exact_pre_call_authority_digests(self) -> None:
        binding = self._binding()
        self.assertTrue(binding["ok"])
        expected_admission = binding["admission_digest"]
        expected_inbox = binding["supervisor_inbox_digest"]
        expected_steering = binding["supervisor_steering_digest"]
        self._revoke_openrouter()
        receipt = provenance.emit_execution_receipt(
            provider="openrouter",
            credential_fingerprint="fp",
            model_or_route="openrouter/free",
            endpoint=self._endpoint(),
            binding=binding,
            request_id="request-1",
            usage={},
            http_status=200,
            result_digest="result",
            source_commit_and_tree={"commit": "c", "tree": "t"},
            binding_stable_after_call=False,
            artifacts=self.artifacts,
        )
        self.assertEqual(receipt["typed_admission_digest"], expected_admission)
        self.assertEqual(receipt["supervisor_inbox_digest"], expected_inbox)
        self.assertEqual(receipt["supervisor_steering_digest"], expected_steering)
        self.assertEqual(receipt["supervisor_epoch"], "8.70")
        self.assertFalse(receipt["binding_stable_after_call"])

    def test_cached_reservation_cannot_survive_revocation(self) -> None:
        called = []

        def request(*_args):
            called.append(True)
            return 200, {}, {}

        module, spec_type = self._load_v3(request)
        self.assertTrue(module._evidence(spec_type(), "secret", "openrouter/free")["ok"])
        self._revoke_openrouter()
        status, _, payload = module.gated_request_chat(
            spec_type(), "secret", "openrouter/free", "prompt", 32, 1.0
        )
        self.assertEqual(status, 460)
        self.assertEqual(called, [])
        self.assertEqual(payload["reason"], "PROVIDER_NOT_CURRENTLY_ADMITTED")

    def test_cached_reservation_cannot_survive_supervisor_quarantine(self) -> None:
        called = []

        def request(*_args):
            called.append(True)
            return 200, {}, {}

        module, spec_type = self._load_v3(request)
        self.assertTrue(module._evidence(spec_type(), "secret", "openrouter/free")["ok"])
        self._write_steering(execution_state="RUNTIME_QUARANTINED")
        status, _, payload = module.gated_request_chat(
            spec_type(), "secret", "openrouter/free", "prompt", 32, 1.0
        )
        self.assertEqual(status, 460)
        self.assertEqual(called, [])
        self.assertEqual(payload["reason"], "FREE_LANE_AUTHORITY_SNAPSHOT_INVALID")

    def test_mid_call_authority_change_is_visible_in_receipt(self) -> None:
        def request(*_args):
            self._revoke_openrouter()
            return 200, {"x-request-id": "request-2"}, {
                "id": "request-2",
                "usage": {"total_tokens": 2},
                "choices": [],
            }

        module, spec_type = self._load_v3(request)
        status, _, _ = module.gated_request_chat(
            spec_type(), "secret", "openrouter/free", "prompt", 32, 1.0
        )
        self.assertEqual(status, 200)
        rows = (self.artifacts / "free_lane_execution_receipts.jsonl").read_text(
            encoding="utf-8"
        ).strip().splitlines()
        receipt = json.loads(rows[-1])
        self.assertEqual(receipt["typed_admission_epoch"], "8.70")
        self.assertEqual(receipt["supervisor_epoch"], "8.70")
        self.assertFalse(receipt["binding_stable_after_call"])


if __name__ == "__main__":
    unittest.main()
