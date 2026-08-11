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


class FreeApiProviderRuntimeTests(unittest.TestCase):
    def test_nvidia_is_preferred_and_secret_is_not_exposed(self):
        env = {"NVIDIA_API_KEY": "do-not-leak", "GROQ_API_KEY": "also-secret"}
        rows = MOD.inventory(env)
        self.assertEqual(MOD.route(env)["selected"], "nvidia")
        self.assertNotIn("do-not-leak", repr(rows))
        self.assertTrue(all(row["secret_exposed"] is False for row in rows))

    def test_together_is_hard_denied_even_if_key_exists(self):
        env = {"TOGETHER_API_KEY": "must-not-be-touched"}
        self.assertIn("together", MOD.DENIED_PROVIDERS)
        self.assertTrue(all(row["provider_id"] != "together" for row in MOD.inventory(env)))
        self.assertIsNone(MOD.route(env)["selected"])

    def test_no_key_means_no_route(self):
        self.assertIsNone(MOD.route({})["selected"])
        self.assertTrue(MOD.route({})["zero_cost_only"])

    def test_key_without_zero_cost_evidence_fails_closed(self):
        env = {"GROQ_API_KEY": "configured-but-billing-unknown"}
        groq = next(row for row in MOD.inventory(env) if row["provider_id"] == "groq")
        self.assertTrue(groq["configured"])
        self.assertFalse(groq["zero_cost_assured"])
        self.assertFalse(groq["eligible"])
        self.assertIsNone(MOD.route(env)["selected"])

    def test_explicit_zero_cost_attestation_enables_non_denied_provider(self):
        env = {
            "GROQ_API_KEY": "secret",
            "FRANK_ZERO_COST_ATTESTED_PROVIDERS": "groq,together",
        }
        self.assertEqual(MOD.route(env)["selected"], "groq")
        self.assertNotIn("together", MOD.route(env)["candidates"])

    def test_local_mock_executes_full_verified_lifecycle_without_secret_leak(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({"choices": [{"message": {"content": "mock-ok"}}]}).encode()

        captured = {}
        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["authorization"] = request.headers["Authorization"]
            return Response()

        env = {
            "NVIDIA_API_KEY": "never-serialize-this",
            "FRANK_PROVIDER_BASE_URL": "http://127.0.0.1:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            [{"role": "user", "content": "ping"}], model="mock-model",
            environ=env, opener=opener, now=iter((10.0, 10.125)).__next__,
        )
        self.assertEqual(result["content"], "mock-ok")
        self.assertEqual(result["receipt"]["lifecycle"][-3:], ["EXECUTED", "VERIFIED", "DONE"])
        self.assertEqual(result["receipt"]["duration_ms"], 125)
        self.assertNotIn("never-serialize-this", repr(result))
        self.assertNotIn("together", captured["url"])

    def test_unallowlisted_remote_endpoint_is_blocked_before_network(self):
        env = {"NVIDIA_API_KEY": "secret", "FRANK_PROVIDER_BASE_URL": "https://evil.example/v1"}
        with self.assertRaisesRegex(RuntimeError, "not_bound_to_selected_provider"):
            MOD.execute_chat([], model="x", environ=env)

    def test_key_cannot_be_sent_to_another_allowlisted_provider_host(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {
            "NVIDIA_API_KEY": "nvidia-secret",
            "FRANK_PROVIDER_BASE_URL": "https://api.groq.com/openai/v1",
        }
        with self.assertRaisesRegex(RuntimeError, "not_bound_to_selected_provider"):
            MOD.execute_chat([], model="x", environ=env, opener=opener)
        self.assertFalse(called)

    def test_default_transport_rejects_redirects_before_auth_can_be_forwarded(self):
        request = MOD.urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": "Bearer secret"}, method="POST", data=b"{}",
        )
        redirected = MOD._NoRedirectHandler().redirect_request(
            request, None, 302, "Found", {},
            "https://api.groq.com/openai/v1/chat/completions",
        )
        self.assertIsNone(redirected)

    def test_retry_keeps_request_identity_but_gets_unique_attempt_identity(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"choices":[{"message":{"content":"ok"}}]}'

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        def execute(started):
            return MOD.execute_chat(
                [{"role": "user", "content": "same operation"}], model="mock",
                environ=env, opener=lambda *args, **kwargs: Response(),
                now=iter((started, started + 0.01)).__next__,
            )["receipt"]

        first, retry = execute(40.0), execute(41.0)
        self.assertEqual(first["request_id"], retry["request_id"])
        self.assertNotEqual(first["attempt_id"], retry["attempt_id"])

    def test_equal_time_concurrent_attempts_do_not_alias(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"choices":[{"message":{"content":"ok"}}]}'

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        def execute(nonce):
            return MOD.execute_chat(
                [{"role": "user", "content": "same operation"}], model="mock",
                environ=env, opener=lambda *args, **kwargs: Response(),
                now=iter((80.0, 80.01)).__next__,
                nonce_factory=lambda: nonce,
            )["receipt"]

        first, concurrent = execute("attempt-a"), execute("attempt-b")
        self.assertEqual(first["request_id"], concurrent["request_id"])
        self.assertNotEqual(first["attempt_id"], concurrent["attempt_id"])
        self.assertEqual(len(first["attempt_id"]), 32)
        self.assertEqual(len(concurrent["attempt_id"]), 32)
        self.assertNotIn("attempt-a", repr(first))
        self.assertNotIn("attempt-b", repr(concurrent))

    def test_different_equal_length_payloads_have_distinct_request_ids(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"choices":[{"message":{"content":"ok"}}]}'

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        def request_id(content):
            return MOD.execute_chat(
                [{"role": "user", "content": content}], model="mock",
                environ=env, opener=lambda *args, **kwargs: Response(),
                now=iter((30.0, 30.01)).__next__,
            )["receipt"]["request_id"]

        self.assertNotEqual(request_id("AA"), request_id("BB"))

    def test_invalid_response_is_executed_but_never_verified(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b"not-json"

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            [], model="mock", environ=env, opener=lambda *args, **kwargs: Response(),
            now=iter((20.0, 20.01)).__next__,
        )
        self.assertEqual(result["receipt"]["status"], 200)
        self.assertEqual(result["receipt"]["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", result["receipt"]["lifecycle"])
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])

    def test_structurally_invalid_json_responses_fail_closed_with_receipt(self):
        class Response:
            status = 200
            def __init__(self, body): self.body = body
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return self.body

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        malformed = (
            b"[]", b'{"choices":[]}',
            b'{"choices":[{"message":{"content":null}}]}',
            b'{"choices":[{"message":"not-an-object"}]}',
        )
        for body in malformed:
            with self.subTest(body=body):
                result = MOD.execute_chat(
                    [], model="mock", environ=env,
                    opener=lambda *args, body=body, **kwargs: Response(body),
                    now=iter((50.0, 50.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], 200)
                self.assertEqual(receipt["outcome"], "invalid_provider_response")
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
                self.assertIsNone(result["content"])

    def test_http_error_is_executed_but_never_verified(self):
        def opener(request, timeout):
            raise MOD.urllib.error.HTTPError(
                request.full_url, 429, "Too Many Requests", {}, None,
            )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            [], model="mock", environ=env, opener=opener,
            now=iter((60.0, 60.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 429)
        self.assertEqual(receipt["outcome"], "rate_limited")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])

    def test_unreachable_provider_has_no_http_status_or_executed_state(self):
        def opener(request, timeout):
            raise MOD.urllib.error.URLError("connection refused")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            [], model="mock", environ=env, opener=opener,
            now=iter((70.0, 70.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertIsNone(receipt["status"])
        self.assertEqual(receipt["outcome"], "unreachable_provider")
        self.assertNotIn("EXECUTED", receipt["lifecycle"])

    def test_body_read_timeout_preserves_received_status_and_executed_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): raise TimeoutError("body stalled")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            [], model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((90.0, 90.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "incomplete_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])


if __name__ == "__main__":
    unittest.main()
