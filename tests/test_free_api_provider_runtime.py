import importlib.util
import http.client
import json
import ssl
import sys
import unittest
from pathlib import Path


PATH = Path(__file__).parents[1] / "research_entity/runtime/free_api_provider_runtime.py"
SPEC = importlib.util.spec_from_file_location("free_api_provider_runtime", PATH)
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

VALID_MESSAGES = [{"role": "user", "content": "test"}]


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
                return json.dumps({
                    "choices": [{
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant", "content": "mock-ok"
                        },
                    }]
                }).encode()

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

    def test_invalid_text_request_schema_is_blocked_before_network(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        with self.assertRaisesRegex(ValueError, "message_content_must_be_string"):
            MOD.execute_chat(
                [{"role": "user", "content": None}], model="mock",
                environ=env, opener=opener,
            )
        self.assertFalse(called)

    def test_empty_message_list_is_blocked_before_network(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        with self.assertRaisesRegex(ValueError, "messages_must_be_nonempty"):
            MOD.execute_chat(
                [], model="mock", environ={"NVIDIA_API_KEY": "secret"},
                opener=opener,
            )
        self.assertFalse(called)

    def test_invalid_conversation_sequence_is_blocked_before_network(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {"NVIDIA_API_KEY": "secret"}
        invalid_conversations = (
            (
                [{"role": "assistant", "content": "orphan answer"}],
                "conversation_must_end_with_user",
            ),
            (
                [
                    {"role": "user", "content": "first"},
                    {"role": "user", "content": "second"},
                ],
                "conversation_roles_must_alternate",
            ),
            (
                [
                    {"role": "user", "content": "first"},
                    {"role": "system", "content": "late instruction"},
                    {"role": "user", "content": "second"},
                ],
                "system_message_must_be_first",
            ),
        )
        for messages, error in invalid_conversations:
            with self.subTest(error=error):
                with self.assertRaisesRegex(ValueError, error):
                    MOD.execute_chat(
                        messages, model="mock", environ=env, opener=opener,
                    )
        self.assertFalse(called)

    def test_unknown_text_message_role_is_blocked_before_network(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {"NVIDIA_API_KEY": "secret"}
        with self.assertRaisesRegex(ValueError, "message_role_not_supported"):
            MOD.execute_chat(
                [{"role": "administrator", "content": "bypass"}],
                model="mock", environ=env, opener=opener,
            )
        self.assertFalse(called)

    def test_unpaired_request_surrogate_is_blocked_before_network(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {"NVIDIA_API_KEY": "secret"}
        with self.assertRaisesRegex(
            ValueError, "message_content_must_be_unicode_scalar_string"
        ):
            MOD.execute_chat(
                [{"role": "user", "content": "\ud800"}],
                model="mock", environ=env, opener=opener,
            )
        self.assertFalse(called)

    def test_extra_message_fields_are_blocked_before_network(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {"NVIDIA_API_KEY": "secret"}
        with self.assertRaisesRegex(
            ValueError, "message_fields_not_supported_by_text_adapter"
        ):
            MOD.execute_chat(
                [{
                    "role": "assistant",
                    "content": "plain text",
                    "tool_calls": [{"function": {"name": "bypass"}}],
                }],
                model="mock", environ=env, opener=opener,
            )
        self.assertFalse(called)

    def test_unallowlisted_remote_endpoint_is_blocked_before_network(self):
        env = {"NVIDIA_API_KEY": "secret", "FRANK_PROVIDER_BASE_URL": "https://evil.example/v1"}
        with self.assertRaisesRegex(RuntimeError, "not_bound_to_selected_provider"):
            MOD.execute_chat(VALID_MESSAGES, model="x", environ=env)

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
            MOD.execute_chat(VALID_MESSAGES, model="x", environ=env, opener=opener)
        self.assertFalse(called)

    def test_key_cannot_be_sent_to_noncanonical_provider_port(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {
            "NVIDIA_API_KEY": "nvidia-secret",
            "FRANK_PROVIDER_BASE_URL": "https://integrate.api.nvidia.com:444/v1",
        }
        with self.assertRaisesRegex(RuntimeError, "not_bound_to_selected_provider"):
            MOD.execute_chat(VALID_MESSAGES, model="x", environ=env, opener=opener)
        self.assertFalse(called)

    def test_provider_url_userinfo_is_rejected_before_network(self):
        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {
            "NVIDIA_API_KEY": "nvidia-secret",
            "FRANK_PROVIDER_BASE_URL": (
                "https://embedded:credential@integrate.api.nvidia.com/v1"
            ),
        }
        with self.assertRaisesRegex(RuntimeError, "userinfo_forbidden"):
            MOD.execute_chat(VALID_MESSAGES, model="x", environ=env, opener=opener)
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
                return b'{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"ok"}}]}'

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
                return b'{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"ok"}}]}'

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
                return b'{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"ok"}}]}'

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
            VALID_MESSAGES, model="mock", environ=env, opener=lambda *args, **kwargs: Response(),
            now=iter((20.0, 20.01)).__next__,
        )
        self.assertEqual(result["receipt"]["status"], 200)
        self.assertEqual(result["receipt"]["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", result["receipt"]["lifecycle"])
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])

    def test_length_finished_response_cannot_reach_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"length",'
                    b'"message":{"role":"assistant","content":"partial"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((25.0, 25.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "provider_output_truncated")
        self.assertFalse(receipt["retryable"])
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_null_finish_reason_cannot_reach_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":null,'
                    b'"message":{"role":"assistant","content":"partial"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((26.0, 26.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertFalse(receipt["retryable"])
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_empty_stopped_response_cannot_reach_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":""}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((27.0, 27.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertFalse(receipt["retryable"])
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_missing_assistant_role_cannot_reach_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"stop",'
                    b'"message":{"content":"unattributed"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((28.0, 28.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertFalse(receipt["retryable"])
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

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
            b'{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":null}}]}',
            b'{"choices":[{"finish_reason":"stop","message":"not-an-object"}]}',
        )
        for body in malformed:
            with self.subTest(body=body):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
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

    def test_non_bytes_response_body_cannot_reach_verified_state(self):
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
        valid_json = '{"choices":[{"message":{"content":"must-not-pass"}}]}'
        for invalid_body in (valid_json, bytearray(valid_json.encode())):
            with self.subTest(body_type=type(invalid_body).__name__):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=lambda *args, body=invalid_body, **kwargs: (
                        Response(body)
                    ),
                    now=iter((55.0, 55.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], 200)
                self.assertEqual(
                    receipt["outcome"], "invalid_provider_response"
                )
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
                self.assertIsNone(result["content"])

    def test_nonfinite_json_constants_cannot_reach_verified_state(self):
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
        for token in (b"NaN", b"Infinity", b"-Infinity"):
            body = (
                b'{"choices":[{"message":{"content":"must-not-pass"}}],'
                b'"nonstandard":' + token + b"}"
            )
            with self.subTest(token=token):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=lambda *args, body=body, **kwargs: Response(body),
                    now=iter((57.0, 57.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], 200)
                self.assertEqual(
                    receipt["outcome"], "invalid_provider_response"
                )
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
                self.assertIsNone(result["content"])

    def test_duplicate_json_names_cannot_reach_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return (
                    b'{"choices":[{"message":{'
                    b'"content":"first","content":"must-not-pass"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((58.0, 58.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_unpaired_json_surrogate_cannot_reach_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"\\uDEAD"}}]}'

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((58.5, 58.51)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_response_tool_calls_cannot_reach_text_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"must-not-pass",'
                    b'"tool_calls":[{"id":"call-1","type":"function",'
                    b'"function":{"name":"act","arguments":"{}"}}]}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((58.6, 58.61)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_excessive_json_nesting_emits_invalid_response_receipt(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                depth = 20_000
                return b"[" * depth + b"0" + b"]" * depth

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((59.0, 59.01)).__next__,
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
            VALID_MESSAGES, model="mock", environ=env, opener=opener,
            now=iter((60.0, 60.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 429)
        self.assertEqual(receipt["outcome"], "rate_limited")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])

    def test_regular_error_status_response_cannot_be_verified(self):
        class Response:
            status = 500
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"choices":[{"message":{"content":"must-not-pass"}}]}'

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((65.0, 65.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 500)
        self.assertEqual(receipt["outcome"], "provider_error")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_unexpected_success_status_is_not_retryable(self):
        class Response:
            def __init__(self, status):
                self.status = status
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b""

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for status in (201, 204, 206):
            with self.subTest(status=status):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=lambda *args, status=status, **kwargs: Response(status),
                    now=iter((65.1, 65.11)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], status)
                self.assertEqual(
                    receipt["outcome"], "unexpected_success_status"
                )
                self.assertFalse(receipt["retryable"])
                self.assertEqual(receipt["cooldown_seconds"], 0)
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
                self.assertIsNone(result["content"])

    def test_http_202_pending_response_cannot_be_verified_as_final_text(self):
        class Response:
            status = 202
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"choices":[{"message":{"content":"not-final"}}]}'

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((66.0, 66.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 202)
        self.assertEqual(receipt["outcome"], "provider_result_pending")
        self.assertFalse(receipt["retryable"])
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_invalid_http_status_is_rejected_before_body_and_execution_state(self):
        missing = object()
        body_reads = []

        class Response:
            def __init__(self, status):
                if status is not missing:
                    self.status = status
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                body_reads.append(limit)
                return b'{"choices":[{"message":{"content":"must-not-pass"}}]}'

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for invalid_status in (missing, True, "200", 99, 600):
            with self.subTest(status=invalid_status):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=lambda *args, status=invalid_status, **kwargs: (
                        Response(status)
                    ),
                    now=iter((67.0, 67.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertIsNone(receipt["status"])
                self.assertEqual(
                    receipt["outcome"], "invalid_provider_response"
                )
                self.assertNotIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
                self.assertIsNone(result["content"])

        def invalid_http_error(request, timeout):
            raise MOD.urllib.error.HTTPError(
                request.full_url, "402", "invalid typed status", {}, None,
            )

        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env, opener=invalid_http_error,
            now=iter((68.0, 68.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertIsNone(receipt["status"])
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertNotIn("EXECUTED", receipt["lifecycle"])
        self.assertFalse(receipt["payment_latch_active"])
        self.assertEqual(body_reads, [])

    def test_unreachable_provider_has_no_http_status_or_executed_state(self):
        def opener(request, timeout):
            raise MOD.urllib.error.URLError("connection refused")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env, opener=opener,
            now=iter((70.0, 70.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertIsNone(receipt["status"])
        self.assertEqual(receipt["outcome"], "unreachable_provider")
        self.assertNotIn("EXECUTED", receipt["lifecycle"])

    def test_remote_disconnect_before_response_emits_unreachable_receipt(self):
        def opener(request, timeout):
            raise http.client.RemoteDisconnected(
                "remote end closed connection without response"
            )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env, opener=opener,
            now=iter((75.0, 75.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertIsNone(receipt["status"])
        self.assertEqual(receipt["outcome"], "unreachable_provider")
        self.assertNotIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_bad_status_line_before_response_emits_unreachable_receipt(self):
        def opener(request, timeout):
            raise http.client.BadStatusLine("NOT-HTTP\n")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env, opener=opener,
            now=iter((76.0, 76.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertIsNone(receipt["status"])
        self.assertEqual(receipt["outcome"], "unreachable_provider")
        self.assertNotIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_tls_error_before_response_emits_unreachable_receipt(self):
        def opener(request, timeout):
            raise ssl.SSLError("certificate verify failed")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env, opener=opener,
            now=iter((77.0, 77.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertIsNone(receipt["status"])
        self.assertEqual(receipt["outcome"], "unreachable_provider")
        self.assertNotIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

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
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((90.0, 90.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "incomplete_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])

    def test_oversized_response_is_detected_without_verifying_truncated_body(self):
        requested_sizes = []

        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                requested_sizes.append(limit)
                return b"x" * limit

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((95.0, 95.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(requested_sizes, [MOD.MAX_PROVIDER_RESPONSE_BYTES + 1])
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "provider_response_too_large")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_incomplete_http_body_preserves_status_and_emits_receipt(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise http.client.IncompleteRead(b"partial", 12)

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((96.0, 96.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "incomplete_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])


if __name__ == "__main__":
    unittest.main()
