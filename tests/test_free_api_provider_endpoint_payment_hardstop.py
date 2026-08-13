import importlib.util
import sys
import unittest
import urllib.error
from pathlib import Path


PATH = Path(__file__).parents[1] / "research_entity/runtime/free_api_provider_runtime.py"
SPEC = importlib.util.spec_from_file_location("free_api_provider_runtime_hardstop", PATH)
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

VALID_MESSAGES = [{"role": "user", "content": "test"}]


class Response:
    def __init__(
        self,
        status=200,
        body=(
            b'{"choices":[{"finish_reason":"stop",'
            b'"message":{"content":"ok"}}]}'
        ),
    ):
        self.status = status
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, limit):
        return self.body


class EndpointIdentityAndPaymentHardStopTests(unittest.TestCase):
    def test_remote_endpoint_aliases_are_rejected_before_network(self):
        variants = (
            "https://integrate.api.nvidia.com/other",
            "https://integrate.api.nvidia.com/v1?route=other",
            "https://integrate.api.nvidia.com/v1#cut",
            "https://integrate.api.nvidia.com/v1///",
            "https://integrate.api.nvidia.com/v1/../v1",
            "https://integrate.api.nvidia.com/%76%31",
            "https://integrate.api.nvidia.com//v1",
        )
        for endpoint in variants:
            with self.subTest(endpoint=endpoint):
                called = False

                def opener(*args, **kwargs):
                    nonlocal called
                    called = True
                    raise AssertionError("network must not be reached")

                with self.assertRaisesRegex(
                    RuntimeError, "not_bound_to_selected_provider"
                ):
                    MOD.execute_chat(
                        VALID_MESSAGES,
                        model="x",
                        environ={
                            "NVIDIA_API_KEY": "secret",
                            "FRANK_PROVIDER_BASE_URL": endpoint,
                        },
                        opener=opener,
                    )
                self.assertFalse(called)

    def test_semantically_equivalent_origin_forms_use_canonical_request_target(self):
        captured = []
        for endpoint in (
            "https://INTEGRATE.API.NVIDIA.COM/v1",
            "https://integrate.api.nvidia.com:443/v1",
        ):
            result = MOD.execute_chat(
                VALID_MESSAGES,
                model="x",
                environ={
                    "NVIDIA_API_KEY": "secret",
                    "FRANK_PROVIDER_BASE_URL": endpoint,
                },
                opener=lambda request, timeout: (
                    captured.append(request.full_url) or Response()
                ),
                now=iter((1.0, 1.01)).__next__,
            )
            self.assertEqual(result["content"], "ok")
        self.assertEqual(
            captured,
            ["https://integrate.api.nvidia.com/v1/chat/completions"] * 2,
        )

    def test_http_402_regular_and_exception_paths_latch_current_budget_epoch(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "test-epoch-a",
        }
        openers = (
            lambda *args, **kwargs: Response(status=402, body=b"{}"),
            lambda request, timeout: (_ for _ in ()).throw(
                urllib.error.HTTPError(
                    request.full_url, 402, "Payment Required", {}, None
                )
            ),
        )
        for opener in openers:
            with self.subTest(opener=repr(opener)):
                latches = set()
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="x",
                    environ=env,
                    opener=opener,
                    now=iter((2.0, 2.01)).__next__,
                    payment_latches=latches,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["outcome"], "payment_required_hard_stop")
                self.assertFalse(receipt["retryable"])
                self.assertEqual(receipt["cooldown_seconds"], 0)
                self.assertTrue(receipt["payment_latch_active"])
                route = MOD.route(env, payment_latches=latches)
                self.assertIsNone(route["selected"])
                self.assertEqual(route["reason"], "payment_required_hard_stop_active")
                with self.assertRaisesRegex(
                    RuntimeError, "payment_required_hard_stop_active"
                ):
                    MOD.execute_chat(
                        VALID_MESSAGES,
                        model="x",
                        environ=env,
                        opener=lambda *args, **kwargs: Response(),
                        payment_latches=latches,
                    )

    def test_new_budget_epoch_does_not_inherit_old_epoch_payment_latch(self):
        latches = set()
        env_a = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "epoch-a",
        }
        env_b = {**env_a, "FRANK_FREE_ONLY_BUDGET_EPOCH": "epoch-b"}
        MOD.execute_chat(
            VALID_MESSAGES,
            model="x",
            environ=env_a,
            opener=lambda *args, **kwargs: Response(status=402, body=b"{}"),
            now=iter((3.0, 3.01)).__next__,
            payment_latches=latches,
        )
        self.assertIsNone(MOD.route(env_a, payment_latches=latches)["selected"])
        self.assertEqual(MOD.route(env_b, payment_latches=latches)["selected"], "nvidia")


if __name__ == "__main__":
    unittest.main()
