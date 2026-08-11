import importlib.util
import json
import sys
import unittest
from pathlib import Path


PATH = Path(__file__).parents[1] / "research_entity/runtime/free_api_provider_runtime.py"
SPEC = importlib.util.spec_from_file_location("free_api_provider_runtime", PATH)
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, limit):
        return json.dumps(
            {"choices": [{"message": {"content": "mock-ok"}}]}
        ).encode()


class EndpointCapabilityIdentityTests(unittest.TestCase):
    def _execute(self, base_url, *, local=False, nonce="fixed-nonce"):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["selector"] = request.selector
            return Response()

        env = {
            "NVIDIA_API_KEY": "dummy-do-not-serialize",
            "FRANK_PROVIDER_BASE_URL": base_url,
        }
        if local:
            env["FRANK_ALLOW_LOCAL_TEST_ENDPOINT"] = "1"

        result = MOD.execute_chat(
            [{"role": "user", "content": "same"}],
            model="same-model",
            environ=env,
            opener=opener,
            now=iter((10.0, 10.01)).__next__,
            nonce_factory=lambda: nonce,
        )
        self.assertNotIn("dummy-do-not-serialize", repr(result))
        return result["receipt"], captured

    def test_exact_documented_nvidia_operation_is_admitted(self):
        receipt, captured = self._execute(
            "https://integrate.api.nvidia.com/v1"
        )
        self.assertEqual(captured["selector"], "/v1/chat/completions")
        self.assertEqual(receipt["endpoint_host"], "integrate.api.nvidia.com")
        self.assertEqual(receipt["endpoint_port"], 443)
        self.assertEqual(len(receipt["request_target_digest"]), 64)
        self.assertEqual(
            receipt["lifecycle"][-3:], ["EXECUTED", "VERIFIED", "DONE"]
        )

    def test_same_origin_path_aliases_are_blocked_before_network(self):
        aliases = (
            "https://integrate.api.nvidia.com/other",
            "https://integrate.api.nvidia.com/v1/.",
            "https://integrate.api.nvidia.com/v1/..",
            "https://integrate.api.nvidia.com/v1/%2e",
            "https://integrate.api.nvidia.com/v1/%2e%2e",
            "https://integrate.api.nvidia.com/v1//",
            "https://integrate.api.nvidia.com/v1/%2Fhidden",
        )
        for base_url in aliases:
            with self.subTest(base_url=base_url):
                called = False

                def opener(*args, **kwargs):
                    nonlocal called
                    called = True
                    raise AssertionError("network must not be reached")

                env = {
                    "NVIDIA_API_KEY": "dummy",
                    "FRANK_PROVIDER_BASE_URL": base_url,
                }
                with self.assertRaisesRegex(
                    RuntimeError,
                    "provider_endpoint_not_exact_selected_capability",
                ):
                    MOD.execute_chat(
                        [],
                        model="same-model",
                        environ=env,
                        opener=opener,
                    )
                self.assertFalse(called)

    def test_query_fragment_and_params_are_blocked_before_network(self):
        aliases = (
            "https://integrate.api.nvidia.com/v1?route=other",
            "https://integrate.api.nvidia.com/v1#cut",
            "https://integrate.api.nvidia.com/v1;shadow",
        )
        for base_url in aliases:
            with self.subTest(base_url=base_url):
                called = False

                def opener(*args, **kwargs):
                    nonlocal called
                    called = True
                    raise AssertionError("network must not be reached")

                env = {
                    "NVIDIA_API_KEY": "dummy",
                    "FRANK_PROVIDER_BASE_URL": base_url,
                }
                with self.assertRaisesRegex(
                    RuntimeError,
                    "provider_endpoint_not_exact_selected_capability",
                ):
                    MOD.execute_chat(
                        [],
                        model="same-model",
                        environ=env,
                        opener=opener,
                    )
                self.assertFalse(called)

    def test_request_identity_binds_complete_target_not_only_origin(self):
        first, first_capture = self._execute(
            "http://localhost:8765/v1", local=True
        )
        second, second_capture = self._execute(
            "http://localhost:8765/other", local=True
        )
        self.assertNotEqual(first_capture["selector"], second_capture["selector"])
        self.assertNotEqual(
            first["request_target_digest"], second["request_target_digest"]
        )
        self.assertNotEqual(first["request_id"], second["request_id"])

    def test_exact_retry_keeps_request_id_but_attempt_id_is_nonce_bound(self):
        first, _ = self._execute(
            "http://localhost:8765/v1",
            local=True,
            nonce="attempt-a",
        )
        second, _ = self._execute(
            "http://localhost:8765/v1",
            local=True,
            nonce="attempt-b",
        )
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertNotEqual(first["attempt_id"], second["attempt_id"])


if __name__ == "__main__":
    unittest.main()
