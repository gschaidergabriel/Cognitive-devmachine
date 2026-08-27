from __future__ import annotations

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "run_24h_entityos_swarm.py"
SPEC = importlib.util.spec_from_file_location("adaptive_24h_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ADAPTIVE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTIVE)


@contextmanager
def open_slot(*args, **kwargs):
    del args, kwargs
    yield


class Adaptive24hFreeLaneBinding871Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = ADAPTIVE.base.ProviderSpec(
            name="nvidia",
            endpoint="https://integrate.api.nvidia.com/v1/chat/completions",
            key_envs=("NVIDIA_API_KEY",),
            keys_list_env="NVIDIA_API_KEYS",
            models_env="NVIDIA_SWARM_MODELS",
            default_models=("nvidia/test-model",),
            attestation_env="CLAY_NVIDIA_FREE_ATTESTED",
            default_max_concurrency=1,
        )
        self.saved = {
            "provider_is_admitted_free": ADAPTIVE.base.provider_is_admitted_free,
            "original_request": ADAPTIVE._ORIGINAL_REQUEST_CHAT,
            "current_lane_binding": ADAPTIVE.current_lane_binding,
            "binding_still_current": ADAPTIVE.binding_still_current,
            "quota_slot": ADAPTIVE.quota_slot,
            "quota_observe": ADAPTIVE.quota_observe,
            "emit_execution_receipt": ADAPTIVE.emit_execution_receipt,
            "lane_cached": ADAPTIVE._lane_evidence_cached,
            "urlopen": ADAPTIVE.urllib.request.urlopen,
        }
        ADAPTIVE.base.provider_is_admitted_free = lambda provider: True
        ADAPTIVE.quota_slot = open_slot
        ADAPTIVE.quota_observe = lambda *args, **kwargs: None

    def tearDown(self) -> None:
        ADAPTIVE.base.provider_is_admitted_free = self.saved["provider_is_admitted_free"]
        ADAPTIVE._ORIGINAL_REQUEST_CHAT = self.saved["original_request"]
        ADAPTIVE.current_lane_binding = self.saved["current_lane_binding"]
        ADAPTIVE.binding_still_current = self.saved["binding_still_current"]
        ADAPTIVE.quota_slot = self.saved["quota_slot"]
        ADAPTIVE.quota_observe = self.saved["quota_observe"]
        ADAPTIVE.emit_execution_receipt = self.saved["emit_execution_receipt"]
        ADAPTIVE._lane_evidence_cached = self.saved["lane_cached"]
        ADAPTIVE.urllib.request.urlopen = self.saved["urlopen"]

    def test_unbound_lane_never_reaches_provider_request(self) -> None:
        calls = []
        ADAPTIVE._ORIGINAL_REQUEST_CHAT = lambda *args, **kwargs: calls.append((args, kwargs))
        ADAPTIVE.current_lane_binding = lambda *args, **kwargs: {
            "ok": False,
            "reason": "NVIDIA_CREDENTIAL_DEVELOPER_FREE_ENTITLEMENT_NOT_BOUND",
        }

        status, _, payload = ADAPTIVE.provider_bounded_request_chat(
            self.spec, "secret-key", "nvidia/test-model", "prompt", 100, 5.0
        )

        self.assertEqual(status, 460)
        self.assertEqual(calls, [])
        self.assertEqual(payload["error"]["type"], "free_lane_binding")

    def test_authority_drift_inside_quota_gate_blocks_network(self) -> None:
        calls = []
        ADAPTIVE._ORIGINAL_REQUEST_CHAT = lambda *args, **kwargs: calls.append((args, kwargs))
        ADAPTIVE.current_lane_binding = lambda *args, **kwargs: {"ok": True, "admission_digest": "a"}
        states = iter((True, False))
        ADAPTIVE.binding_still_current = lambda binding: next(states)

        status, _, payload = ADAPTIVE.provider_bounded_request_chat(
            self.spec, "secret-key", "nvidia/test-model", "prompt", 100, 5.0
        )

        self.assertEqual(status, 460)
        self.assertEqual(calls, [])
        self.assertEqual(payload["error"]["type"], "free_lane_binding_drift")

    def test_bound_mocked_call_emits_exact_execution_receipt(self) -> None:
        receipts = []
        binding = {
            "ok": True,
            "observed_at": "2026-08-24T00:00:00+00:00",
            "admission_epoch": "8.71",
            "admission_digest": "admission",
            "economic_provenance_digest": "economic",
            "evidence": {"assertion": "BOUND"},
        }
        ADAPTIVE.current_lane_binding = lambda *args, **kwargs: binding
        ADAPTIVE.binding_still_current = lambda current: True
        ADAPTIVE._ORIGINAL_REQUEST_CHAT = lambda *args, **kwargs: (
            200,
            {"x-request-id": "req-123"},
            {
                "id": "provider-payload-id",
                "usage": {"prompt_tokens": 7, "completion_tokens": 3},
                "choices": [{"message": {"content": "ok"}}],
            },
        )
        ADAPTIVE.emit_execution_receipt = lambda **kwargs: receipts.append(kwargs)

        status, headers, payload = ADAPTIVE.provider_bounded_request_chat(
            self.spec, "secret-key", "nvidia/test-model", "prompt", 100, 5.0
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers["x-request-id"], "req-123")
        self.assertEqual(payload["id"], "provider-payload-id")
        self.assertEqual(len(receipts), 1)
        receipt = receipts[0]
        self.assertEqual(receipt["provider"], "nvidia")
        self.assertEqual(receipt["credential_fingerprint"], ADAPTIVE.base.key_fingerprint("secret-key"))
        self.assertEqual(receipt["model_or_route"], "nvidia/test-model")
        self.assertEqual(receipt["endpoint"], self.spec.endpoint)
        self.assertEqual(receipt["request_id"], "req-123")
        self.assertEqual(receipt["input_output_usage"]["prompt_tokens"], 7)
        self.assertTrue(receipt["binding_stable_after_call"])
        self.assertEqual(set(receipt["source_commit_and_tree"]), {"commit", "tree"})
        self.assertEqual(len(receipt["result_digest"]), 64)

    def test_reservation_filter_returns_none_when_no_lane_is_bound(self) -> None:
        runtime = ADAPTIVE.base.ProviderRuntime(
            self.spec, ["secret-key"], ["nvidia/test-model"], 1
        )
        ADAPTIVE._lane_evidence_cached = lambda spec, key, model: {
            "ok": False,
            "reason": "UNBOUND",
        }
        self.assertIsNone(ADAPTIVE.lane_bounded_next_key_model(runtime))

    def test_catalog_discovery_cannot_reach_network(self) -> None:
        calls = []

        def forbidden_urlopen(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("credentialed catalog network must not be reached")

        ADAPTIVE.urllib.request.urlopen = forbidden_urlopen
        rows = ADAPTIVE.fetch_catalog(
            "nvidia", "https://integrate.api.nvidia.com/v1/models", "secret-key", 5.0
        )
        self.assertEqual(rows, [])
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
