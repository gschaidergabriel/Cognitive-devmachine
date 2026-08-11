import importlib.util
import json
import sys
import unittest
from pathlib import Path


PATH = Path(__file__).parents[1] / "research_entity/runtime/free_api_provider_runtime.py"
SPEC = importlib.util.spec_from_file_location("free_api_provider_runtime_endpoint_regression", PATH)
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
        return json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()


class EndpointCapabilityRegressionTests(unittest.TestCase):
    def _execute(self, base_url, *, local=False):
        captured = {}

        def opener(request, timeout):
            captured["full_url"] = request.full_url
            captured["selector"] = request.selector
            return Response()

        env = {
            "NVIDIA_API_KEY": "dummy-secret-never-serialize",
            "FRANK_PROVIDER_BASE_URL": base_url,
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "endpoint-regression-cut2",
        }
        if local:
            env["FRANK_ALLOW_LOCAL_TEST_ENDPOINT"] = "1"

        result = MOD.execute_chat(
            [{"role": "user", "content": "same"}],
            model="same-model",
            environ=env,
            opener=opener,
            now=iter((10.0, 10.01)).__next__,
            nonce_factory=lambda: "fixed-nonce",
            payment_latches=set(),
        )
        self.assertNotIn("dummy-secret-never-serialize", repr(result))
        return result["receipt"], captured

    def test_exact_documented_nvidia_operation_is_admitted(self):
        receipt, captured = self._execute("https://integrate.api.nvidia.com/v1")
        self.assertEqual(captured["selector"], "/v1/chat/completions")
        self.assertEqual(receipt["lifecycle"][-3:], ["EXECUTED", "VERIFIED", "DONE"])
        self.assertEqual(len(receipt["endpoint_capability_id"]), 16)
        self.assertEqual(len(receipt["cost_policy_principal_id"]), 16)
        self.assertEqual(len(receipt["request_id"]), 16)

    def test_same_origin_aliases_fail_before_opener(self):
        aliases = (
            "https://integrate.api.nvidia.com/other",
            "https://integrate.api.nvidia.com/v1/.",
            "https://integrate.api.nvidia.com/v1/..",
            "https://integrate.api.nvidia.com/v1/%2e",
            "https://integrate.api.nvidia.com/v1/%2e%2e",
            "https://integrate.api.nvidia.com/v1//",
            "https://integrate.api.nvidia.com/v1/%2Fhidden",
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
                    raise AssertionError("opener must not be reached")

                env = {
                    "NVIDIA_API_KEY": "dummy",
                    "FRANK_PROVIDER_BASE_URL": base_url,
                    "FRANK_FREE_ONLY_BUDGET_EPOCH": "endpoint-regression-cut2",
                }
                with self.assertRaisesRegex(RuntimeError, "not_bound_to_selected_provider"):
                    MOD.execute_chat(
                        [],
                        model="same-model",
                        environ=env,
                        opener=opener,
                        payment_latches=set(),
                    )
                self.assertFalse(called)

    def test_endpoint_capability_changes_request_identity(self):
        first, first_capture = self._execute("http://localhost:8765/v1", local=True)
        second, second_capture = self._execute("http://localhost:8765/other", local=True)
        self.assertNotEqual(first_capture["selector"], second_capture["selector"])
        self.assertNotEqual(first["endpoint_capability_id"], second["endpoint_capability_id"])
        self.assertEqual(first["cost_policy_principal_id"], second["cost_policy_principal_id"])
        self.assertNotEqual(first["request_id"], second["request_id"])


if __name__ == "__main__":
    unittest.main()
