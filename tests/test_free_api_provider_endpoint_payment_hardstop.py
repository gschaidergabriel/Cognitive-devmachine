import importlib.util
import sys
import threading
import unittest
import urllib.error
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
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
            b'"message":{"role":"assistant","content":"ok"}}]}'
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

    def test_http_402_latches_before_response_body_is_read(self):
        body_reads = []

        class StalledPaymentResponse:
            status = 402
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self, limit):
                body_reads.append(limit)
                raise TimeoutError("payment response body stalled")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "stalled-402-epoch",
        }
        latches = set()
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="x",
            environ=env,
            opener=lambda *args, **kwargs: StalledPaymentResponse(),
            now=iter((2.1, 2.11)).__next__,
            payment_latches=latches,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 402)
        self.assertEqual(receipt["outcome"], "payment_required_hard_stop")
        self.assertFalse(receipt["retryable"])
        self.assertTrue(receipt["payment_latch_active"])
        self.assertEqual(body_reads, [])
        self.assertIsNone(MOD.route(env, payment_latches=latches)["selected"])

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

    def test_concurrent_attempt_waits_for_payment_hard_stop_result(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "concurrent-402-epoch",
        }
        latches = set()
        first_opened = threading.Event()
        release_first = threading.Event()
        second_opened = threading.Event()
        opener_lock = threading.Lock()
        opener_calls = 0

        def opener(*args, **kwargs):
            nonlocal opener_calls
            with opener_lock:
                opener_calls += 1
                call_number = opener_calls
            if call_number == 1:
                first_opened.set()
                self.assertTrue(release_first.wait(2))
                return Response(status=402, body=b"{}")
            second_opened.set()
            return Response()

        def attempt(clock_start, nonce):
            try:
                return MOD.execute_chat(
                    VALID_MESSAGES,
                    model="x",
                    environ=env,
                    opener=opener,
                    now=iter((clock_start, clock_start + 0.01)).__next__,
                    nonce_factory=lambda: nonce,
                    payment_latches=latches,
                )
            except Exception as exc:
                return exc

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(attempt, 4.0, "first")
            self.assertTrue(first_opened.wait(2))
            second = pool.submit(attempt, 5.0, "second")
            second_reached_network_while_first_pending = second_opened.wait(0.5)
            release_first.set()
            first_result = first.result(timeout=2)
            second_result = second.result(timeout=2)

        self.assertFalse(second_reached_network_while_first_pending)
        self.assertEqual(
            first_result["receipt"]["outcome"],
            "payment_required_hard_stop",
        )
        self.assertIsInstance(second_result, RuntimeError)
        self.assertEqual(str(second_result), "payment_required_hard_stop_active")
        self.assertEqual(opener_calls, 1)

    def test_busy_execution_lock_times_out_before_network(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        opener_called = False

        def opener(*args, **kwargs):
            nonlocal opener_called
            opener_called = True
            return Response()

        def attempt():
            try:
                return MOD.execute_chat(
                    VALID_MESSAGES,
                    model="x",
                    environ=env,
                    opener=opener,
                )
            except Exception as exc:
                return exc

        MOD.PROCESS_EXECUTION_LOCK.acquire()
        original_timeout = getattr(MOD, "EXECUTION_LOCK_TIMEOUT_SECONDS", None)
        MOD.EXECUTION_LOCK_TIMEOUT_SECONDS = 0.05
        completed_while_busy = True
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(attempt)
                try:
                    result = future.result(timeout=0.2)
                except FutureTimeout:
                    completed_while_busy = False
                    MOD.PROCESS_EXECUTION_LOCK.release()
                    result = future.result(timeout=2)
                else:
                    MOD.PROCESS_EXECUTION_LOCK.release()
        finally:
            if MOD.PROCESS_EXECUTION_LOCK.locked():
                MOD.PROCESS_EXECUTION_LOCK.release()
            if original_timeout is None:
                del MOD.EXECUTION_LOCK_TIMEOUT_SECONDS
            else:
                MOD.EXECUTION_LOCK_TIMEOUT_SECONDS = original_timeout

        self.assertTrue(completed_while_busy)
        self.assertIsInstance(result, RuntimeError)
        self.assertEqual(str(result), "execution_busy")
        self.assertFalse(opener_called)


if __name__ == "__main__":
    unittest.main()
