import builtins
import hashlib
import hmac
import importlib.util
import http.client
import json
import os
import ssl
import sys
import threading
import unittest
from pathlib import Path


PATH = Path(__file__).parents[1] / "research_entity/runtime/free_api_provider_runtime.py"
SPEC = importlib.util.spec_from_file_location("free_api_provider_runtime", PATH)
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)
# Synthetic success fixtures use created=1. Pin their default receipt wall
# clock so temporal-provenance tests remain deterministic across real dates.
MOD.execute_chat.__kwdefaults__["wall_time"] = lambda: 1.0

VALID_MESSAGES = [{"role": "user", "content": "test"}]


class FreeApiProviderRuntimeTests(unittest.TestCase):
    def test_nvidia_is_preferred_and_secret_is_not_exposed(self):
        env = {"NVIDIA_API_KEY": "do-not-leak", "GROQ_API_KEY": "also-secret"}
        rows = MOD.inventory(env)
        self.assertEqual(MOD.route(env)["selected"], "nvidia")
        self.assertNotIn("do-not-leak", repr(rows))
        self.assertTrue(all(row["secret_exposed"] is False for row in rows))

    def test_invalid_bearer_credential_is_blocked_before_network(self):
        invalid_credentials = (
            " secret",
            "secret ",
            "secret\r\nX-Injected: value",
            "secrét",
            "secret:colon",
        )

        for credential in invalid_credentials:
            with self.subTest(credential=repr(credential)):
                called = False

                def opener(*args, **kwargs):
                    nonlocal called
                    called = True
                    raise AssertionError("network must not be reached")

                env = {
                    "NVIDIA_API_KEY": credential,
                    "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
                    "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
                }
                self.assertIsNone(MOD.route(env)["selected"])
                with self.assertRaisesRegex(
                    RuntimeError, "no_configured_zero_cost_provider"
                ):
                    MOD.execute_chat(
                        VALID_MESSAGES, model="mock", environ=env,
                        opener=opener,
                    )
                self.assertFalse(called)

        self.assertEqual(
            MOD.route({"NVIDIA_API_KEY": "nvapi-valid_key~+/=="})["selected"],
            "nvidia",
        )

    def test_oversized_bearer_credential_is_blocked_before_header_and_network(self):
        opener_calls = []

        def opener(*args, **kwargs):
            opener_calls.append("open")
            raise AssertionError("oversized credential reached opener")

        env = {
            "NVIDIA_API_KEY": "A" * 8_193,
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        self.assertIsNone(MOD.route(env)["selected"])
        with self.assertRaisesRegex(
            RuntimeError, "no_configured_zero_cost_provider"
        ):
            MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env, opener=opener,
            )
        self.assertEqual(opener_calls, [])
        self.assertEqual(
            MOD.route({"NVIDIA_API_KEY": "A" * 8_192})["selected"],
            "nvidia",
        )

    def test_environment_snapshot_failure_is_redacted_and_fail_closed(self):
        leaked_text = "credential-value-must-not-escape"

        class FailingEnvironment(dict):
            def get(self, name, default=None):
                raise LookupError(leaked_text)

        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        with self.assertRaisesRegex(
            ValueError, "runtime_environment_could_not_be_snapshotted"
        ) as caught:
            MOD.execute_chat(
                VALID_MESSAGES, model="mock",
                environ=FailingEnvironment(), opener=opener,
            )
        self.assertNotIn(leaked_text, repr(caught.exception))
        self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(caught.exception.__cause__)
        self.assertFalse(called)

    def test_environment_snapshot_rejects_active_string_subclasses(self):
        leaked_text = "credential-subclass-method-must-not-run"

        class ActiveString(str):
            def split(self, *args, **kwargs):
                raise LookupError(leaked_text)

        called = False

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

        env = {
            "NVIDIA_API_KEY": "nvapi-valid_key",
            "FRANK_ZERO_COST_ATTESTED_PROVIDERS": ActiveString("nvidia"),
        }
        with self.assertRaisesRegex(
            ValueError, "runtime_environment_could_not_be_snapshotted"
        ) as caught:
            MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env, opener=opener,
            )
        self.assertNotIn(leaked_text, repr(caught.exception))
        self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(caught.exception.__cause__)
        self.assertFalse(called)

    def test_oversized_zero_cost_attestation_is_rejected_before_parsing(self):
        parser_calls = []
        original_parser = MOD._attested_zero_cost_providers

        def tracking_parser(environ):
            parser_calls.append("parse")
            return original_parser(environ)

        MOD._attested_zero_cost_providers = tracking_parser
        try:
            with self.assertRaisesRegex(
                ValueError, "runtime_environment_could_not_be_snapshotted"
            ):
                MOD.route(
                    {
                        "FRANK_ZERO_COST_ATTESTED_PROVIDERS":
                            "nvidia," * 200,
                    }
                )
            self.assertEqual(parser_calls, [])

            self.assertIsNone(
                MOD.route(
                    {"FRANK_ZERO_COST_ATTESTED_PROVIDERS": "x" * 1_024}
                )["selected"]
            )
            self.assertEqual(parser_calls, ["parse"])
        finally:
            MOD._attested_zero_cost_providers = original_parser

    def test_capability_receipt_uses_one_environment_snapshot(self):
        environment_reads = []
        original_environment = MOD.os.environ

        class ChangingEnvironment(dict):
            def get(self, name, default=None):
                if name == "NVIDIA_API_KEY":
                    environment_reads.append(name)
                    return "first-snapshot-key" if len(environment_reads) == 1 else None
                return None

        MOD.os.environ = ChangingEnvironment()
        try:
            capability_receipt = MOD.receipt()
        finally:
            MOD.os.environ = original_environment

        configured = [
            row["provider_id"]
            for row in capability_receipt["inventory"]
            if row["configured"]
        ]
        self.assertEqual(configured, ["nvidia"])
        self.assertEqual(capability_receipt["route"]["selected"], "nvidia")
        self.assertEqual(environment_reads, ["NVIDIA_API_KEY"])

    def test_capability_receipt_advertises_execution_schema_provenance(self):
        capability_receipt = MOD.receipt()

        self.assertEqual(
            capability_receipt["execution_receipt_schema_version"], "1.10"
        )
        self.assertEqual(
            capability_receipt["unicode_database_version"],
            MOD.unicodedata.unidata_version,
        )
        self.assertEqual(
            capability_receipt["execution_cost_policy_principal_scope"],
            "process_local_credential_binding",
        )
        self.assertFalse(
            capability_receipt[
                "execution_cost_policy_principal_restart_stable"
            ]
        )
        self.assertTrue(capability_receipt[
            "execution_cost_policy_principal_fork_isolated"
        ])
        self.assertTrue(capability_receipt["execution_lock_fork_isolated"])
        self.assertEqual(capability_receipt["schema_version"], "1.12")
        self.assertFalse(capability_receipt["invariants"][
            "semantic_request_identity_authorizes_replay"
        ])
        self.assertFalse(capability_receipt["invariants"][
            "cost_policy_principal_restart_stable"
        ])

    def test_capability_receipt_does_not_infer_model_availability(self):
        capability_receipt = MOD.receipt()

        self.assertFalse(capability_receipt["invariants"][
            "model_availability_inferred_without_probe"
        ])
        for provider in capability_receipt["inventory"]:
            self.assertFalse(provider["model_availability_verified"])

    def test_route_selection_is_scoped_to_provider_endpoint(self):
        route = MOD.route({"NVIDIA_API_KEY": "secret"})

        self.assertEqual(route["selected"], "nvidia")
        self.assertEqual(route["selection_scope"], "provider_endpoint")
        self.assertFalse(route["model_availability_verified"])

    def test_receipts_disclose_process_local_payment_latch_scope(self):
        capability_receipt = MOD.receipt()

        self.assertEqual(
            capability_receipt["route"]["payment_latch_scope"],
            "process_local",
        )
        self.assertTrue(all(
            row["payment_latch_scope"] == "process_local"
            for row in capability_receipt["inventory"]
        ))

        class PaymentResponse:
            status = 402
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                raise AssertionError("HTTP 402 body must not be read")

        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ={
                "NVIDIA_API_KEY": "secret",
                "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
                "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
                "FRANK_FREE_ONLY_BUDGET_EPOCH": "scope-regression",
            },
            opener=lambda *args, **kwargs: PaymentResponse(),
            now=iter((1.0, 1.01)).__next__,
            payment_latches=set(),
        )

        self.assertTrue(result["receipt"]["payment_latch_active"])
        self.assertEqual(
            result["receipt"]["payment_latch_scope"],
            "process_local",
        )

    def test_credential_rotation_changes_cost_principal_lineage_without_exposure(self):
        class SuccessResponse:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"ok"}}]}'
                )

        credentials = (
            "credential-alpha-high-entropy",
            "credential-beta-high-entropy",
        )
        receipts = []
        for index, credential in enumerate(credentials):
            result = MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ={
                    "NVIDIA_API_KEY": credential,
                    "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
                    "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
                    "FRANK_FREE_ONLY_BUDGET_EPOCH": "rotation-regression",
                },
                opener=lambda *args, **kwargs: SuccessResponse(),
                now=iter((2.0 + index, 2.01 + index)).__next__,
            )
            receipts.append(result["receipt"])

        self.assertNotEqual(
            receipts[0]["cost_policy_principal_id"],
            receipts[1]["cost_policy_principal_id"],
        )
        self.assertNotEqual(receipts[0]["request_id"], receipts[1]["request_id"])
        self.assertEqual(
            receipts[0]["semantic_request_id"],
            receipts[1]["semantic_request_id"],
        )
        public_context = b"frank-cost-principal-v1:nvidia:NVIDIA_API_KEY"
        guessed_binding = hmac.new(
            credentials[0].encode("ascii"),
            public_context,
            hashlib.sha256,
        ).hexdigest()[:16]
        public_guess = (
            "nvidia:NVIDIA_API_KEY:"
            f"{guessed_binding}:"
            "nvidia_developer_program_free_prototype_endpoint:"
            "rotation-regression"
        )
        guessed_principal_id = hashlib.sha256(
            public_guess.encode("utf-8")
        ).hexdigest()[:16]
        self.assertNotEqual(
            guessed_principal_id,
            receipts[0]["cost_policy_principal_id"],
        )
        restart_spec = importlib.util.spec_from_file_location(
            "free_api_provider_runtime_restart_probe",
            PATH,
        )
        restarted = importlib.util.module_from_spec(restart_spec)
        sys.modules[restart_spec.name] = restarted
        try:
            restart_spec.loader.exec_module(restarted)
            restarted_principal_id = restarted._cost_policy_principal_id(
                restarted.PROVIDERS[0],
                "NVIDIA_API_KEY",
                {
                    "NVIDIA_API_KEY": credentials[0],
                    "FRANK_FREE_ONLY_BUDGET_EPOCH": "rotation-regression",
                },
            )
        finally:
            sys.modules.pop(restart_spec.name, None)
        self.assertNotEqual(
            receipts[0]["cost_policy_principal_id"],
            restarted_principal_id,
        )
        self.assertTrue(all(
            receipt["cost_policy_principal_scope"]
            == "process_local_credential_binding"
            for receipt in receipts
        ))
        for credential in credentials:
            self.assertNotIn(credential, repr(receipts))

    @unittest.skipUnless(hasattr(os, "fork"), "requires POSIX fork")
    def test_cost_principal_process_key_is_reseeded_after_fork(self):
        env = {
            "NVIDIA_API_KEY": "fork-isolation-credential",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "fork-regression",
        }
        parent_principal_id = MOD._cost_policy_principal_id(
            MOD.PROVIDERS[0],
            "NVIDIA_API_KEY",
            env,
        )
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(read_fd)
                child_principal_id = MOD._cost_policy_principal_id(
                    MOD.PROVIDERS[0],
                    "NVIDIA_API_KEY",
                    env,
                )
                os.write(write_fd, child_principal_id.encode("ascii"))
            finally:
                os._exit(0)

        os.close(write_fd)
        try:
            child_principal_id = os.read(read_fd, 128).decode("ascii")
        finally:
            os.close(read_fd)
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertNotEqual(parent_principal_id, child_principal_id)

    @unittest.skipUnless(hasattr(os, "fork"), "requires POSIX fork")
    def test_execution_lock_is_reinitialized_after_fork(self):
        read_fd, write_fd = os.pipe()
        MOD.PROCESS_EXECUTION_LOCK.acquire()
        try:
            pid = os.fork()
            if pid == 0:
                try:
                    os.close(read_fd)
                    acquired = MOD.PROCESS_EXECUTION_LOCK.acquire(timeout=0.1)
                    if acquired:
                        MOD.PROCESS_EXECUTION_LOCK.release()
                    os.write(write_fd, b"1" if acquired else b"0")
                finally:
                    os._exit(0)
        finally:
            MOD.PROCESS_EXECUTION_LOCK.release()

        os.close(write_fd)
        try:
            child_acquired = os.read(read_fd, 1)
        finally:
            os.close(read_fd)
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertEqual(child_acquired, b"1")

    @unittest.skipUnless(hasattr(os, "fork"), "requires POSIX fork")
    def test_cost_principal_fork_isolation_survives_entropy_failure(self):
        env = {
            "NVIDIA_API_KEY": "fork-entropy-failure-credential",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "fork-entropy-failure",
        }
        parent_principal_id = MOD._cost_policy_principal_id(
            MOD.PROVIDERS[0],
            "NVIDIA_API_KEY",
            env,
        )

        class FailingSecrets:
            @staticmethod
            def token_bytes(size):
                raise OSError("simulated entropy failure")

        read_fd, write_fd = os.pipe()
        original_secrets = MOD.secrets
        MOD.secrets = FailingSecrets()
        try:
            pid = os.fork()
        finally:
            MOD.secrets = original_secrets
        if pid == 0:
            try:
                os.close(read_fd)
                child_principal_id = MOD._cost_policy_principal_id(
                    MOD.PROVIDERS[0],
                    "NVIDIA_API_KEY",
                    env,
                )
                os.write(write_fd, child_principal_id.encode("ascii"))
            finally:
                os._exit(0)

        os.close(write_fd)
        try:
            child_principal_id = os.read(read_fd, 128).decode("ascii")
        finally:
            os.close(read_fd)
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertNotEqual(parent_principal_id, child_principal_id)

    @unittest.skipUnless(hasattr(os, "fork"), "requires POSIX fork")
    def test_reused_child_pid_does_not_reuse_cost_principal(self):
        env = {
            "NVIDIA_API_KEY": "fork-pid-reuse-credential",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "fork-pid-reuse",
        }

        class FixedPidOS:
            @staticmethod
            def getpid():
                return 4242

        def forked_principal_id():
            read_fd, write_fd = os.pipe()
            pid = os.fork()
            if pid == 0:
                try:
                    os.close(read_fd)
                    principal_id = MOD._cost_policy_principal_id(
                        MOD.PROVIDERS[0],
                        "NVIDIA_API_KEY",
                        env,
                    )
                    os.write(write_fd, principal_id.encode("ascii"))
                finally:
                    os._exit(0)
            os.close(write_fd)
            try:
                principal_id = os.read(read_fd, 128).decode("ascii")
            finally:
                os.close(read_fd)
            _, status = os.waitpid(pid, 0)
            self.assertEqual(os.waitstatus_to_exitcode(status), 0)
            return principal_id

        original_os = MOD.os
        MOD.os = FixedPidOS()
        try:
            first_principal_id = forked_principal_id()
            second_principal_id = forked_principal_id()
        finally:
            MOD.os = original_os
        self.assertNotEqual(first_principal_id, second_principal_id)

    def test_execution_receipt_pins_unicode_database_version(self):
        class Response:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"ok"}}]}'
                )

        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ={
                "NVIDIA_API_KEY": "secret",
                "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
                "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            },
            opener=lambda *args, **kwargs: Response(),
            now=iter((1.0, 1.01)).__next__,
        )

        self.assertEqual(result["receipt"]["schema_version"], "1.10")
        self.assertTrue(result["receipt"]["execution_lock_fork_isolated"])
        self.assertEqual(
            result["receipt"]["unicode_database_version"],
            MOD.unicodedata.unidata_version,
        )

    def test_execution_receipt_scopes_model_availability_to_verified_success(self):
        class Response:
            headers = {}

            def __init__(self, status):
                self.status = status

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        success = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(200),
            now=iter((1.0, 1.01)).__next__,
        )
        failure = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(500),
            now=iter((2.0, 2.01)).__next__,
        )

        self.assertTrue(success["receipt"]["model_availability_verified"])
        self.assertFalse(failure["receipt"]["model_availability_verified"])

    def test_text_request_rejects_active_string_subclasses(self):
        leaked_text = "request-string-method-must-not-run"

        for field, expected_error in (
            ("model", "model_must_be_nonempty_string"),
            ("role", "message_role_must_be_nonempty_string"),
            ("content", "message_content_must_be_string"),
        ):
            with self.subTest(field=field):
                method_calls = []

                class ActiveString(str):
                    def strip(self, *args, **kwargs):
                        method_calls.append("strip")
                        raise LookupError(leaked_text)

                model = ActiveString("mock") if field == "model" else "mock"
                messages = [{"role": "user", "content": "hello"}]
                if field != "model":
                    messages[0][field] = ActiveString(messages[0][field])

                with self.assertRaisesRegex(ValueError, expected_error) as caught:
                    MOD.execute_chat(messages, model=model, environ={})
                self.assertEqual(method_calls, [])
                self.assertNotIn(leaked_text, repr(caught.exception))

    def test_text_request_rejects_active_list_subclass_before_iteration(self):
        leaked_text = "request-list-iterator-must-not-run"
        iterator_calls = []

        class ActiveMessages(list):
            def __iter__(self):
                iterator_calls.append("iter")
                raise LookupError(leaked_text)

        messages = ActiveMessages([{"role": "user", "content": "hello"}])
        with self.assertRaisesRegex(ValueError, "messages_must_be_list") as caught:
            MOD.execute_chat(messages, model="mock", environ={})
        self.assertEqual(iterator_calls, [])
        self.assertNotIn(leaked_text, repr(caught.exception))
        self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(caught.exception.__cause__)

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
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": "mock-model",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "choices": [{
                        "index": 0,
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

    def test_oversized_serialized_request_is_blocked_before_environment(self):
        environment_reads = []
        opener_calls = []

        class TrackingEnvironment(dict):
            def get(self, name, default=None):
                environment_reads.append(name)
                return super().get(name, default)

        def opener(*args, **kwargs):
            opener_calls.append("open")
            raise AssertionError("network must not be reached")

        env = TrackingEnvironment({
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        })
        oversized_messages = [{
            "role": "user",
            "content": "x" * 2_000_000,
        }]
        with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
            MOD.execute_chat(
                oversized_messages, model="mock", environ=env, opener=opener,
            )
        self.assertEqual(environment_reads, [])
        self.assertEqual(opener_calls, [])

        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock","usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},"choices":[{"index":0,"finish_reason":"stop","message":{"role":"assistant","content":"ok"}}]}'

        empty_body_size = len(json.dumps({
            "model": "mock",
            "messages": [{"role": "user", "content": ""}],
            "stream": False,
            "n": 1,
            "max_tokens": MOD.MAX_PROVIDER_OUTPUT_TOKENS,
        }).encode())
        captured_sizes = []

        def accepted_opener(request, timeout):
            captured_sizes.append(len(request.data))
            return Response()

        at_limit = [{
            "role": "user",
            "content": "x" * (MOD.MAX_PROVIDER_REQUEST_BYTES - empty_body_size),
        }]
        result = MOD.execute_chat(
            at_limit, model="mock", environ=dict(env),
            opener=accepted_opener, now=iter((1.0, 1.01)).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(captured_sizes, [MOD.MAX_PROVIDER_REQUEST_BYTES])

    def test_oversized_request_is_rejected_before_json_materialization(self):
        serialization_calls = []
        original_dumps = MOD.json.dumps

        def tracking_dumps(*args, **kwargs):
            serialization_calls.append("serialize")
            return original_dumps(*args, **kwargs)

        MOD.json.dumps = tracking_dumps
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
                MOD.execute_chat(
                    [{
                        "role": "user",
                        "content": "x" * MOD.MAX_PROVIDER_REQUEST_BYTES,
                    }],
                    model="mock",
                    environ={},
                )
        finally:
            MOD.json.dumps = original_dumps

        self.assertEqual(serialization_calls, [])

    def test_oversized_text_lower_bound_is_rejected_before_execution_lock(self):
        lock_calls = []
        original_lock = MOD.PROCESS_EXECUTION_LOCK

        class TrackingLock:
            def acquire(self, timeout):
                lock_calls.append("acquire")
                return True

            def release(self):
                lock_calls.append("release")

        MOD.PROCESS_EXECUTION_LOCK = TrackingLock()
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
                MOD.execute_chat(
                    [{
                        "role": "user",
                        "content": "x" * MOD.MAX_PROVIDER_REQUEST_BYTES,
                    }],
                    model="mock",
                    environ={},
                )
        finally:
            MOD.PROCESS_EXECUTION_LOCK = original_lock

        self.assertEqual(lock_calls, [])

    def test_escaped_unicode_overflow_is_rejected_before_json_materialization(self):
        serialization_calls = []
        original_dumps = MOD.json.dumps

        def tracking_dumps(*args, **kwargs):
            serialization_calls.append("serialize")
            return original_dumps(*args, **kwargs)

        # With ensure_ascii=True, each non-BMP scalar becomes a pair of
        # six-byte \uXXXX escapes. Character count alone therefore
        # underestimates the serialized request by a factor of twelve.
        escaped_overflow = "😀" * (MOD.MAX_PROVIDER_REQUEST_BYTES // 12 + 1)
        MOD.json.dumps = tracking_dumps
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
                MOD.execute_chat(
                    [{"role": "user", "content": escaped_overflow}],
                    model="mock",
                    environ={},
                )
        finally:
            MOD.json.dumps = original_dumps

        self.assertEqual(serialization_calls, [])

    def test_del_escape_overflow_is_rejected_before_json_materialization(self):
        serialization_calls = []
        original_dumps = MOD.json.dumps

        def tracking_dumps(*args, **kwargs):
            serialization_calls.append("serialize")
            return original_dumps(*args, **kwargs)

        # CPython's default encoder escapes ASCII DEL as six-byte \\u007f.
        # Counting it as one byte lets an oversized document reach dumps.
        escaped_overflow = "x" + "\x7f" * (
            MOD.MAX_PROVIDER_REQUEST_BYTES // 6 + 1
        )
        MOD.json.dumps = tracking_dumps
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
                MOD.execute_chat(
                    [{"role": "user", "content": escaped_overflow}],
                    model="mock",
                    environ={},
                )
        finally:
            MOD.json.dumps = original_dumps

        self.assertEqual(serialization_calls, [])

    def test_structurally_oversized_request_is_rejected_before_snapshot(self):
        snapshot_calls = []
        original_snapshot = MOD._snapshot_text_chat_request

        def tracking_snapshot(*args, **kwargs):
            snapshot_calls.append("snapshot")
            return original_snapshot(*args, **kwargs)

        user = {"role": "user", "content": "x"}
        assistant = {"role": "assistant", "content": "x"}
        max_messages = MOD.MAX_PROVIDER_REQUEST_BYTES // 32
        messages = [user, assistant] * (max_messages // 2)
        messages.append(user)

        MOD._snapshot_text_chat_request = tracking_snapshot
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
                MOD.execute_chat(messages, model="mock", environ={})
        finally:
            MOD._snapshot_text_chat_request = original_snapshot

        self.assertEqual(snapshot_calls, [])

    def test_dense_alternating_overflow_is_rejected_before_execution_lock(self):
        lock_calls = []
        original_lock = MOD.PROCESS_EXECUTION_LOCK
        user = {"role": "user", "content": "x"}
        assistant = {"role": "assistant", "content": "x"}
        # 54,793 is the first odd, system-free alternating conversation whose
        # smallest closed-schema JSON representation exceeds 2,000,000 bytes.
        messages = [user, assistant] * 27_396 + [user]

        class TrackingLock:
            def acquire(self, timeout):
                lock_calls.append("acquire")
                return True

            def release(self):
                lock_calls.append("release")

        MOD.PROCESS_EXECUTION_LOCK = TrackingLock()
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
                MOD.execute_chat(messages, model="x", environ={})
        finally:
            MOD.PROCESS_EXECUTION_LOCK = original_lock

        self.assertEqual(lock_calls, [])

    def test_wide_message_object_is_rejected_before_execution_lock(self):
        lock_calls = []
        original_lock = MOD.PROCESS_EXECUTION_LOCK
        message = {"role": "user", "content": "x"}
        message.update({f"extra_{index}": "x" for index in range(10_000)})

        class TrackingLock:
            def acquire(self, timeout):
                lock_calls.append("acquire")
                return True

            def release(self):
                lock_calls.append("release")

        MOD.PROCESS_EXECUTION_LOCK = TrackingLock()
        try:
            with self.assertRaisesRegex(
                ValueError, "message_fields_not_supported_by_text_adapter"
            ):
                MOD.execute_chat([message], model="x", environ={})
        finally:
            MOD.PROCESS_EXECUTION_LOCK = original_lock

        self.assertEqual(lock_calls, [])

    def test_message_count_mutation_is_rechecked_before_snapshot(self):
        snapshot_completed = []
        original_lock = MOD.PROCESS_EXECUTION_LOCK
        original_snapshot = MOD._snapshot_text_chat_request

        user = {"role": "user", "content": "x"}
        assistant = {"role": "assistant", "content": "x"}
        messages = [user]
        growth = [assistant, user] * (
            MOD.MAX_PROVIDER_REQUEST_BYTES // 32 // 2
        )

        class MutatingLock:
            def acquire(self, timeout):
                messages.extend(growth)
                return True

            def release(self):
                pass

        def tracking_snapshot(*args, **kwargs):
            snapshot = original_snapshot(*args, **kwargs)
            snapshot_completed.append("snapshot")
            return snapshot

        MOD.PROCESS_EXECUTION_LOCK = MutatingLock()
        MOD._snapshot_text_chat_request = tracking_snapshot
        try:
            with self.assertRaisesRegex(ValueError, "provider_request_too_large"):
                MOD.execute_chat(messages, model="mock", environ={})
        finally:
            MOD.PROCESS_EXECUTION_LOCK = original_lock
            MOD._snapshot_text_chat_request = original_snapshot

        self.assertEqual(len(messages), 62_501)
        self.assertEqual(snapshot_completed, [])

    def test_active_monotonic_values_cannot_suppress_execution_receipt(self):
        method_calls = []

        class ActiveTime(float):
            def __format__(self, spec):
                method_calls.append("format")
                raise LookupError("clock-format-must-not-run")

            def __sub__(self, other):
                method_calls.append("sub")
                raise LookupError("clock-subtraction-must-not-run")

        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": "mock",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant", "content": "mock-ok"
                        },
                    }]
                }).encode()

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        opener_calls = []

        def opener(*args, **kwargs):
            opener_calls.append("open")
            return Response()

        with self.assertRaisesRegex(
            RuntimeError, "monotonic_clock_unavailable"
        ):
            MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env,
                opener=opener,
                now=iter((ActiveTime(100.0), 100.01)).__next__,
            )
        self.assertEqual(opener_calls, [])

        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=opener,
            now=iter((100.0, ActiveTime(100.01))).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(result["receipt"]["duration_ms"], 0)
        self.assertEqual(opener_calls, ["open"])
        self.assertEqual(method_calls, [])

    def test_extreme_monotonic_values_cannot_suppress_or_bloat_receipt(self):
        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": "mock",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant", "content": "mock-ok"
                        },
                    }]
                }).encode()

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        for readings in (
            (-1e308, 1e308),
            (-10**1000, 1.0),
            (0, 10**100),
        ):
            with self.subTest(readings=readings):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=lambda *args, **kwargs: Response(),
                    now=iter(readings).__next__,
                )
                self.assertEqual(result["receipt"]["outcome"], "success")
                self.assertEqual(result["receipt"]["duration_ms"], 86_400_000)

    def test_extreme_integer_clock_cannot_suppress_attempt_receipt(self):
        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": "mock",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant", "content": "mock-ok"
                        },
                    }]
                }).encode()

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        started = 1 << 20_000
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((started, started + 1)).__next__,
            nonce_factory=lambda: "fixed-passive-nonce",
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(result["receipt"]["duration_ms"], 1000)
        self.assertEqual(len(result["receipt"]["attempt_id"]), 32)

    def test_credential_cannot_change_between_authorization_and_request(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": "mock",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "ok"},
                    }]
                }).encode()

        captured = {}
        env = {
            "NVIDIA_API_KEY": "authorized-secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        def mutate_after_authorization():
            env["NVIDIA_API_KEY"] = "swapped-secret"
            return "fixed-attempt-nonce"

        def opener(request, timeout):
            captured["authorization"] = request.headers["Authorization"]
            return Response()

        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env, opener=opener,
            nonce_factory=mutate_after_authorization,
            now=iter((15.0, 15.01)).__next__,
        )

        self.assertEqual(result["content"], "ok")
        self.assertEqual(
            captured["authorization"], "Bearer authorized-secret"
        )

    def test_nonce_callback_latch_change_is_rechecked_before_network(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "nonce-latch-epoch",
        }
        latches = set()
        opener_calls = []

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        def mutate_latch_after_authorization():
            latches.add(MOD._payment_latch_key("nvidia", env))
            return "fixed-attempt-nonce"

        with self.assertRaisesRegex(
            RuntimeError, "payment_required_hard_stop_active"
        ):
            MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ=env,
                opener=lambda *args, **kwargs: (
                    opener_calls.append("open") or Response()
                ),
                nonce_factory=mutate_latch_after_authorization,
                payment_latches=latches,
            )
        self.assertEqual(opener_calls, [])

    def test_clock_callback_latch_change_is_rechecked_before_network(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "clock-latch-epoch",
        }
        latches = set()
        opener_calls = []

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        def mutate_latch_during_clock_read():
            latches.add(MOD._payment_latch_key("nvidia", env))
            return 16.0

        with self.assertRaisesRegex(
            RuntimeError, "payment_required_hard_stop_active"
        ):
            MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ=env,
                opener=lambda *args, **kwargs: (
                    opener_calls.append("open") or Response()
                ),
                now=mutate_latch_during_clock_read,
                nonce_factory=lambda: "fixed-attempt-nonce",
                payment_latches=latches,
            )
        self.assertEqual(opener_calls, [])

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

    def test_request_messages_are_snapshotted_before_routing_side_effects(self):
        messages = [{"role": "user", "content": "validated-text"}]

        class MutatingEnvironment(dict):
            mutated = False

            def get(self, key, default=None):
                if not self.mutated:
                    self.mutated = True
                    messages[0]["content"] = ""
                    messages[0]["tool_calls"] = [{"id": "unvalidated"}]
                return super().get(key, default)

        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": "mock",
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "ok"},
                    }]
                }).encode()

        captured = {}

        def opener(request, timeout):
            captured["body"] = json.loads(request.data)
            return Response()

        env = MutatingEnvironment({
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        })
        result = MOD.execute_chat(
            messages, model="mock", environ=env, opener=opener,
            now=iter((20.0, 20.01)).__next__,
        )

        self.assertEqual(result["content"], "ok")
        self.assertEqual(
            captured["body"]["messages"],
            [{"role": "user", "content": "validated-text"}],
        )

    def test_provider_request_has_explicit_output_token_budget(self):
        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock","usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},"choices":[{"index":0,"finish_reason":"stop","message":{"role":"assistant","content":"ok"}}]}'

        captured = {}

        def opener(request, timeout):
            captured.update(json.loads(request.data))
            return Response()

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env, opener=opener,
            now=iter((22.0, 22.01)).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(captured["max_tokens"], 4096)
        self.assertEqual(captured["max_tokens"], MOD.MAX_PROVIDER_OUTPUT_TOKENS)

    def test_model_name_with_surrounding_whitespace_is_blocked_before_network(self):
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
        for model in (" mock-model", "mock-model ", "mock-model\n"):
            with self.subTest(model=repr(model)):
                with self.assertRaisesRegex(
                    ValueError, "model_must_match_served_identifier_exactly"
                ):
                    MOD.execute_chat(
                        VALID_MESSAGES, model=model, environ=env, opener=opener,
                    )
        self.assertFalse(called)

    def test_model_name_with_internal_control_character_is_blocked_before_network(self):
        called = False

        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": "mock\nforged",
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "ok"},
                    }],
                }).encode("utf-8")

        def opener(*args, **kwargs):
            nonlocal called
            called = True
            return Response()

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        with self.assertRaisesRegex(
            ValueError, "model_must_not_contain_control_characters"
        ):
            MOD.execute_chat(
                VALID_MESSAGES,
                model="mock\nforged",
                environ=env,
                opener=opener,
            )
        self.assertFalse(called)

    def test_nonsemantic_model_identifier_is_blocked_before_network(self):
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
        for model in ("\u200b", "\ue000"):
            with self.subTest(model=repr(model)):
                with self.assertRaisesRegex(
                    ValueError, "model_must_be_nonempty_string"
                ):
                    MOD.execute_chat(
                        VALID_MESSAGES, model=model, environ=env, opener=opener,
                    )
        self.assertFalse(called)

    def test_documented_nvidia_style_model_identifier_remains_compatible(self):
        model = "meta/llama-3.1-8b-instruct"

        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({
                    "object": "chat.completion",
                    "id": "chatcmpl-test",
                    "created": 1,
                    "model": model,
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "ok"},
                    }],
                }).encode("utf-8")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model=model,
            environ=env,
            opener=lambda *args, **kwargs: Response(),
        )

        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(result["receipt"]["model"], model)

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

    def test_blank_text_message_is_blocked_before_network(self):
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
        for content in ("", " \n\t"):
            with self.subTest(content=repr(content)):
                with self.assertRaisesRegex(
                    ValueError, "message_content_must_be_nonempty_string"
                ):
                    MOD.execute_chat(
                        [{"role": "user", "content": content}], model="mock",
                        environ=env, opener=opener,
                    )
        self.assertFalse(called)

    def test_control_only_text_cannot_cross_semantic_text_boundaries(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        class Response:
            status = 200

            def __init__(self, message):
                self.message = message

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    + self.message
                    + b'}]}'
                )

        with self.subTest(boundary="request_content"):
            called = False

            def opener(*args, **kwargs):
                nonlocal called
                called = True
                return Response(
                    b'{"role":"assistant","content":"ok",'
                    b'"reasoning":"thought"}'
                )

            with self.assertRaisesRegex(
                ValueError, "message_content_must_be_nonempty_string"
            ):
                MOD.execute_chat(
                    [{"role": "user", "content": "\x00"}],
                    model="mock",
                    environ=env,
                    opener=opener,
                    now=iter((50.31, 50.32)).__next__,
                )
            self.assertFalse(called)

        responses = (
            (
                "response_content",
                b'{"role":"assistant","content":"\\u0000"}',
            ),
            (
                "response_reasoning",
                b'{"role":"assistant","content":"visible-ok",'
                b'"reasoning":"\\u0000"}',
            ),
        )
        for boundary, message in responses:
            with self.subTest(boundary=boundary):
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, message=message, **kwargs: Response(
                        message
                    ),
                    now=iter((50.33, 50.34)).__next__,
                )
                self.assertEqual(
                    result["receipt"]["outcome"],
                    "invalid_provider_response",
                )
                self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
                self.assertNotIn("DONE", result["receipt"]["lifecycle"])
                self.assertIsNone(result["content"])

    def test_format_only_text_cannot_cross_semantic_text_boundaries(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        class Response:
            status = 200

            def __init__(self, message):
                self.message = message

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    + self.message
                    + b'}]}'
                )

        with self.subTest(boundary="request_content"):
            called = False

            def opener(*args, **kwargs):
                nonlocal called
                called = True
                return Response(
                    b'{"role":"assistant","content":"ok",'
                    b'"reasoning":"thought"}'
                )

            with self.assertRaisesRegex(
                ValueError, "message_content_must_be_nonempty_string"
            ):
                MOD.execute_chat(
                    [{"role": "user", "content": "\u200b"}],
                    model="mock",
                    environ=env,
                    opener=opener,
                    now=iter((50.31, 50.32)).__next__,
                )
            self.assertFalse(called)

        responses = (
            (
                "response_content",
                b'{"role":"assistant","content":"\\u200b"}',
            ),
            (
                "response_reasoning",
                b'{"role":"assistant","content":"visible-ok",'
                b'"reasoning":"\\u200b"}',
            ),
        )
        for boundary, message in responses:
            with self.subTest(boundary=boundary):
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, message=message, **kwargs: Response(
                        message
                    ),
                    now=iter((50.33, 50.34)).__next__,
                )
                self.assertEqual(
                    result["receipt"]["outcome"],
                    "invalid_provider_response",
                )
                self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
                self.assertNotIn("DONE", result["receipt"]["lifecycle"])
                self.assertIsNone(result["content"])

        compatible = MOD.execute_chat(
            [{"role": "user", "content": "visible\u200bprompt"}],
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(
                b'{"role":"assistant","content":"visible\\u200banswer",'
                b'"reasoning":"reasoned\\u200btrace"}'
            ),
            now=iter((50.35, 50.36)).__next__,
        )
        self.assertEqual(compatible["receipt"]["outcome"], "success")
        self.assertIn("VERIFIED", compatible["receipt"]["lifecycle"])
        self.assertIn("DONE", compatible["receipt"]["lifecycle"])

    def test_combining_mark_only_text_cannot_cross_semantic_boundaries(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        class Response:
            status = 200

            def __init__(self, message):
                self.message = message

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    + self.message
                    + b'}]}'
                )

        with self.subTest(boundary="request_content"):
            called = False

            def opener(*args, **kwargs):
                nonlocal called
                called = True
                return Response(
                    b'{"role":"assistant","content":"ok",'
                    b'"reasoning":"thought"}'
                )

            with self.assertRaisesRegex(
                ValueError, "message_content_must_be_nonempty_string"
            ):
                MOD.execute_chat(
                    [{"role": "user", "content": "\u0301"}],
                    model="mock",
                    environ=env,
                    opener=opener,
                    now=iter((50.41, 50.42)).__next__,
                )
            self.assertFalse(called)

        responses = (
            (
                "response_content",
                b'{"role":"assistant","content":"\\u0301"}',
            ),
            (
                "response_reasoning",
                b'{"role":"assistant","content":"visible-ok",'
                b'"reasoning":"\\u0301"}',
            ),
        )
        for boundary, message in responses:
            with self.subTest(boundary=boundary):
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, message=message, **kwargs: Response(
                        message
                    ),
                    now=iter((50.43, 50.44)).__next__,
                )
                self.assertEqual(
                    result["receipt"]["outcome"],
                    "invalid_provider_response",
                )
                self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
                self.assertNotIn("DONE", result["receipt"]["lifecycle"])
                self.assertIsNone(result["content"])

        compatible = MOD.execute_chat(
            [{"role": "user", "content": "e\u0301"}],
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(
                b'{"role":"assistant","content":"e\\u0301",'
                b'"reasoning":"trace\\u0301"}'
            ),
            now=iter((50.45, 50.46)).__next__,
        )
        self.assertEqual(compatible["receipt"]["outcome"], "success")
        self.assertIn("VERIFIED", compatible["receipt"]["lifecycle"])
        self.assertIn("DONE", compatible["receipt"]["lifecycle"])

    def test_noncharacter_only_text_cannot_cross_semantic_boundaries(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        class Response:
            status = 200

            def __init__(self, message):
                self.message = message

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    + self.message
                    + b'}]}'
                )

        with self.subTest(boundary="request_content"):
            called = False

            def opener(*args, **kwargs):
                nonlocal called
                called = True
                return Response(
                    b'{"role":"assistant","content":"ok",'
                    b'"reasoning":"thought"}'
                )

            with self.assertRaisesRegex(
                ValueError, "message_content_must_be_nonempty_string"
            ):
                MOD.execute_chat(
                    [{"role": "user", "content": "\ufdd0"}],
                    model="mock",
                    environ=env,
                    opener=opener,
                    now=iter((50.51, 50.52)).__next__,
                )
            self.assertFalse(called)

        responses = (
            (
                "response_content",
                b'{"role":"assistant","content":"\\ufdd0"}',
            ),
            (
                "response_reasoning",
                b'{"role":"assistant","content":"visible-ok",'
                b'"reasoning":"\\udbff\\udfff"}',
            ),
        )
        for boundary, message in responses:
            with self.subTest(boundary=boundary):
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, message=message, **kwargs: Response(
                        message
                    ),
                    now=iter((50.53, 50.54)).__next__,
                )
                self.assertEqual(
                    result["receipt"]["outcome"],
                    "invalid_provider_response",
                )
                self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
                self.assertNotIn("DONE", result["receipt"]["lifecycle"])
                self.assertIsNone(result["content"])

        compatible = MOD.execute_chat(
            [{"role": "user", "content": "prompt\ufdd0"}],
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(
                b'{"role":"assistant","content":"answer\\ufdd0",'
                b'"reasoning":"trace\\udbff\\udfff"}'
            ),
            now=iter((50.55, 50.56)).__next__,
        )
        self.assertEqual(compatible["receipt"]["outcome"], "success")
        self.assertIn("VERIFIED", compatible["receipt"]["lifecycle"])
        self.assertIn("DONE", compatible["receipt"]["lifecycle"])

    def test_private_use_only_text_cannot_cross_semantic_boundaries(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        class Response:
            status = 200

            def __init__(self, message):
                self.message = message

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    + self.message
                    + b'}]}'
                )

        with self.subTest(boundary="request_content"):
            called = False

            def opener(*args, **kwargs):
                nonlocal called
                called = True
                return Response(
                    b'{"role":"assistant","content":"ok",'
                    b'"reasoning":"thought"}'
                )

            with self.assertRaisesRegex(
                ValueError, "message_content_must_be_nonempty_string"
            ):
                MOD.execute_chat(
                    [{"role": "user", "content": "\ue000"}],
                    model="mock",
                    environ=env,
                    opener=opener,
                    now=iter((50.61, 50.62)).__next__,
                )
            self.assertFalse(called)

        responses = (
            (
                "response_content",
                b'{"role":"assistant","content":"\\ue000"}',
            ),
            (
                "response_reasoning",
                b'{"role":"assistant","content":"visible-ok",'
                b'"reasoning":"\\udbff\\udffd"}',
            ),
        )
        for boundary, message in responses:
            with self.subTest(boundary=boundary):
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, message=message, **kwargs: Response(
                        message
                    ),
                    now=iter((50.63, 50.64)).__next__,
                )
                self.assertEqual(
                    result["receipt"]["outcome"],
                    "invalid_provider_response",
                )
                self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
                self.assertNotIn("DONE", result["receipt"]["lifecycle"])
                self.assertIsNone(result["content"])

        compatible = MOD.execute_chat(
            [{"role": "user", "content": "prompt\ue000"}],
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(
                b'{"role":"assistant","content":"answer\\ue000",'
                b'"reasoning":"trace\\udbff\\udffd"}'
            ),
            now=iter((50.65, 50.66)).__next__,
        )
        self.assertEqual(compatible["receipt"]["outcome"], "success")
        self.assertIn("VERIFIED", compatible["receipt"]["lifecycle"])
        self.assertIn("DONE", compatible["receipt"]["lifecycle"])

    def test_unassigned_only_text_cannot_cross_semantic_boundaries(self):
        self.assertEqual(MOD.unicodedata.category("\u0378"), "Cn")
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        class Response:
            status = 200

            def __init__(self, message):
                self.message = message

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    + self.message
                    + b'}]}'
                )

        with self.subTest(boundary="request_content"):
            called = False

            def opener(*args, **kwargs):
                nonlocal called
                called = True
                return Response(
                    b'{"role":"assistant","content":"ok",'
                    b'"reasoning":"thought"}'
                )

            with self.assertRaisesRegex(
                ValueError, "message_content_must_be_nonempty_string"
            ):
                MOD.execute_chat(
                    [{"role": "user", "content": "\u0378"}],
                    model="mock",
                    environ=env,
                    opener=opener,
                    now=iter((50.71, 50.72)).__next__,
                )
            self.assertFalse(called)

        responses = (
            (
                "response_content",
                b'{"role":"assistant","content":"\\u0378"}',
            ),
            (
                "response_reasoning",
                b'{"role":"assistant","content":"visible-ok",'
                b'"reasoning":"\\u0378"}',
            ),
        )
        for boundary, message in responses:
            with self.subTest(boundary=boundary):
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, message=message, **kwargs: Response(
                        message
                    ),
                    now=iter((50.73, 50.74)).__next__,
                )
                self.assertEqual(
                    result["receipt"]["outcome"],
                    "invalid_provider_response",
                )
                self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
                self.assertNotIn("DONE", result["receipt"]["lifecycle"])
                self.assertIsNone(result["content"])

        compatible = MOD.execute_chat(
            [{"role": "user", "content": "prompt\u0378"}],
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(
                b'{"role":"assistant","content":"answer\\u0378",'
                b'"reasoning":"trace\\u0378"}'
            ),
            now=iter((50.75, 50.76)).__next__,
        )
        self.assertEqual(compatible["receipt"]["outcome"], "success")
        self.assertIn("VERIFIED", compatible["receipt"]["lifecycle"])
        self.assertIn("DONE", compatible["receipt"]["lifecycle"])

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

    def test_active_attempt_nonce_is_rejected_before_network(self):
        leaked_text = "attempt-nonce-format-must-not-run"
        network_calls = []
        format_calls = []

        class ActiveNonce(str):
            def __format__(self, format_spec):
                format_calls.append(format_spec)
                raise LookupError(leaked_text)

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

        def opener(*args, **kwargs):
            network_calls.append("open")
            return Response()

        with self.assertRaisesRegex(
            ValueError, "attempt_nonce_must_be_nonempty_string"
        ) as caught:
            MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env, opener=opener,
                nonce_factory=lambda: ActiveNonce("active-nonce"),
            )
        self.assertEqual(network_calls, [])
        self.assertEqual(format_calls, [])
        self.assertNotIn(leaked_text, repr(caught.exception))

    def test_surrogate_attempt_nonce_is_rejected_before_network(self):
        network_calls = []

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

        def opener(*args, **kwargs):
            network_calls.append("open")
            return Response()

        with self.assertRaises(ValueError) as caught:
            MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env, opener=opener,
                nonce_factory=lambda: "\ud800",
            )
        self.assertEqual(network_calls, [])
        self.assertEqual(
            str(caught.exception),
            "attempt_nonce_must_be_unicode_scalar_string",
        )

    def test_oversized_attempt_nonce_is_rejected_before_network(self):
        network_calls = []

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

        def opener(*args, **kwargs):
            network_calls.append("open")
            return Response()

        with self.assertRaisesRegex(ValueError, "attempt_nonce_too_large"):
            MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env, opener=opener,
                nonce_factory=lambda: "n" * 129,
            )
        self.assertEqual(network_calls, [])

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

        def request_ids(content):
            return MOD.execute_chat(
                [{"role": "user", "content": content}], model="mock",
                environ=env, opener=lambda *args, **kwargs: Response(),
                now=iter((30.0, 30.01)).__next__,
            )["receipt"]

        first = request_ids("AA")
        second = request_ids("BB")
        self.assertNotEqual(first["request_id"], second["request_id"])
        self.assertNotEqual(
            first["semantic_request_id"],
            second["semantic_request_id"],
        )

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
                    b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"finish_reason":"length",'
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

    def test_whitespace_only_stopped_response_cannot_reach_verified_state(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":" \\n\\t"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((27.1, 27.11)).__next__,
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

    def test_response_choice_extensions_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"choices":[{"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"},'
                    b'"unrecognized_extension":{"accepted":true}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.1, 50.11)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_unknown_top_level_response_extension_cannot_be_verified(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"ok"}}],'
                    b'"unverified_extension":{"active":true}}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.15, 50.16)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_documented_nvidia_choice_metadata_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"message":{"role":"assistant",'
                    b'"content":"ok"},"logprobs":null,"finish_reason":"stop",'
                    b'"stop_reason":null}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.2, 50.21)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "success")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertIn("VERIFIED", receipt["lifecycle"])
        self.assertIn("DONE", receipt["lifecycle"])
        self.assertEqual(
            receipt["provider_response_id_sha256"],
            "a561165cb4bb29b35a07f18118186a6e"
            "a6a0ecac2bda09c348e11837427a42cc",
        )
        self.assertEqual(receipt["provider_created_unix_seconds"], 1)
        self.assertEqual(
            receipt["provider_usage"],
            {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )
        self.assertEqual(result["content"], "ok")

    def test_documented_nvidia_reasoning_usage_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":4,"completion_tokens":5,'
                    b'"total_tokens":9,"prompt_tokens_details":{'
                    b'"cached_tokens":2},"completion_tokens_details":{'
                    b'"reasoning_tokens":3}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.22, 50.23)).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(
            result["receipt"]["provider_usage"]["completion_tokens_details"],
            {"reasoning_tokens": 3},
        )
        self.assertEqual(
            result["receipt"]["provider_usage"]["prompt_tokens_details"],
            {"cached_tokens": 2},
        )
        self.assertEqual(result["content"], "ok")

    def test_documented_nvidia_reasoning_message_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"visible-ok",'
                    b'"reasoning":"private-thought"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.235, 50.236)).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(result["content"], "visible-ok")
        self.assertEqual(result["receipt"]["provider_reasoning_characters"], 15)
        self.assertEqual(
            result["receipt"]["provider_reasoning_sha256"],
            "6df946a1e9278127ca397078b16d6f5c"
            "4d250e1a4740e378407e6a51df862ff6",
        )
        self.assertNotIn("private-thought", repr(result))

        class UnsupportedReasoningResponse(Response):
            def read(self, limit):
                return super().read(limit).replace(
                    b'"reasoning":"private-thought"',
                    b'"reasoning":{"active":true}',
                )

        rejected = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: UnsupportedReasoningResponse(),
            now=iter((50.237, 50.238)).__next__,
        )
        self.assertEqual(
            rejected["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", rejected["receipt"]["lifecycle"])
        self.assertIsNone(rejected["content"])

    def test_reasoning_message_requires_reasoning_token_provenance(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"visible-ok",'
                    b'"reasoning":"unaccounted-reasoning"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.239, 50.24)).__next__,
        )
        self.assertEqual(
            result["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])
        self.assertIsNone(result["content"])

    def test_blank_reasoning_cannot_enter_verified_receipt(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":2,'
                    b'"total_tokens":3,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"visible-ok",'
                    b'"reasoning":"   "}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.2401, 50.2402)).__next__,
        )
        self.assertEqual(
            result["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])
        self.assertIsNone(result["receipt"]["provider_reasoning_sha256"])
        self.assertIsNone(result["receipt"]["provider_reasoning_characters"])
        self.assertIsNone(result["content"])

    def test_visible_content_requires_non_reasoning_completion_token(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2,"completion_tokens_details":{'
                    b'"reasoning_tokens":1}},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"visible-ok",'
                    b'"reasoning":"private-thought"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.241, 50.242)).__next__,
        )
        self.assertEqual(
            result["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])
        self.assertIsNone(result["content"])

    def test_visible_content_requires_positive_completion_tokens(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":0,'
                    b'"total_tokens":1},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"visible-ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.243, 50.244)).__next__,
        )
        self.assertEqual(
            result["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])
        self.assertIsNone(result["content"])

    def test_nonempty_text_request_requires_positive_prompt_tokens(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":0,"completion_tokens":1,'
                    b'"total_tokens":1},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"visible-ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.245, 50.246)).__next__,
        )
        self.assertEqual(
            result["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])
        self.assertIsNone(result["content"])

    def test_completion_usage_cannot_exceed_requested_output_limit(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":4097,'
                    b'"total_tokens":4098},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"visible-ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.247, 50.248)).__next__,
        )
        self.assertEqual(
            result["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
        self.assertNotIn("DONE", result["receipt"]["lifecycle"])
        self.assertIsNone(result["content"])

    def test_documented_nvidia_passive_message_metadata_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock",'
                    b'"prompt_routed_experts":null,"service_tier":null,'
                    b'"system_fingerprint":"vllm-test",'
                    b'"prompt_logprobs":null,"prompt_token_ids":null,'
                    b'"prompt_text":null,"kv_transfer_params":null,"usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"ok","refusal":null,'
                    b'"annotations":null,"audio":null,"function_call":null,'
                    b'"tool_calls":[],"reasoning":null},'
                    b'"routed_experts":null}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.24, 50.25)).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(
            result["receipt"]["provider_system_fingerprint_sha256"],
            "e2781078d590a3596c9c00c003f5e15"
            "e11bb0112dcf8ac52dfdfe8a18cb9897f",
        )
        self.assertEqual(result["content"], "ok")

    def test_noncanonical_system_fingerprint_cannot_enter_verified_receipt(self):
        class Response:
            status = 200

            def __init__(self, fingerprint):
                self.fingerprint = fingerprint

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","system_fingerprint":'
                    + self.fingerprint
                    + b',"usage":{"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for fingerprint in (
            b'"   "',
            b'"vllm\\u000aforged"',
            b'"\\u200b"',
            b'"\\ue000"',
        ):
            with self.subTest(fingerprint=fingerprint):
                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, **kwargs: Response(fingerprint),
                    now=iter((50.251, 50.252)).__next__,
                )
                self.assertEqual(
                    result["receipt"]["outcome"],
                    "invalid_provider_response",
                )
                self.assertNotIn("VERIFIED", result["receipt"]["lifecycle"])
                self.assertNotIn("DONE", result["receipt"]["lifecycle"])
                self.assertIsNone(
                    result["receipt"]["provider_system_fingerprint_sha256"]
                )
                self.assertIsNone(result["content"])

    def test_documented_vllm_service_tier_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","service_tier":"default",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":{'
                    b'"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.26, 50.27)).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(result["receipt"]["provider_service_tier"], "default")
        self.assertEqual(result["content"], "ok")

        class UnsupportedTierResponse(Response):
            def read(self, limit):
                return super().read(limit).replace(
                    b'"service_tier":"default"',
                    b'"service_tier":"paid-unverified"',
                )

        rejected = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: UnsupportedTierResponse(),
            now=iter((50.28, 50.29)).__next__,
        )
        self.assertEqual(
            rejected["receipt"]["outcome"], "invalid_provider_response"
        )
        self.assertNotIn("VERIFIED", rejected["receipt"]["lifecycle"])
        self.assertIsNone(rejected["content"])

    def test_multiple_response_choices_cannot_be_partially_verified(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"choices":['
                    b'{"index":0,"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"first"}},'
                    b'{"index":1,"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"unverified second"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        captured_request = {}

        def opener(request, timeout):
            captured_request.update(json.loads(request.data))
            return Response()

        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=opener,
            now=iter((50.3, 50.31)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])
        self.assertEqual(captured_request["n"], 1)

    def test_missing_response_choice_index_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.35, 50.36)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_missing_response_id_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","created":1,"model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.37, 50.38)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_noncanonical_response_id_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"   ",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.381, 50.382)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_control_character_response_id_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion",'
                    b'"id":"chatcmpl-safe\\nforged",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.383, 50.384)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_canonical_ascii_response_id_suffix_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion",'
                    b'"id":"chatcmpl-Az09._-",'
                    b'"created":1,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.385, 50.386)).__next__,
        )
        self.assertEqual(result["receipt"]["outcome"], "success")
        self.assertEqual(
            result["receipt"]["lifecycle"][-2:], ["VERIFIED", "DONE"]
        )
        self.assertEqual(result["content"], "ok")

    def test_missing_response_created_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"model":"mock","usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.39, 50.40)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_zero_response_created_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":0,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.401, 50.402)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_future_response_created_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1301,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.403, 50.404)).__next__,
            wall_time=lambda: 1000.0,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_response_created_at_future_skew_boundary_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1300,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.405, 50.406)).__next__,
            wall_time=lambda: 1000.0,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["outcome"], "success")
        self.assertEqual(receipt["lifecycle"][-2:], ["VERIFIED", "DONE"])
        self.assertEqual(receipt["response_received_unix_seconds"], 1000.0)
        self.assertEqual(
            receipt["provider_created_max_future_skew_seconds"], 300
        )
        self.assertEqual(result["content"], "ok")

    def test_stale_response_created_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":699,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.407, 50.408)).__next__,
            wall_time=lambda: 1000.0,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_response_created_at_past_skew_boundary_remains_compatible(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":700,"model":"mock","usage":{'
                    b'"prompt_tokens":1,"completion_tokens":1,'
                    b'"total_tokens":2},"choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.409, 50.410)).__next__,
            wall_time=lambda: 1000.0,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["outcome"], "success")
        self.assertEqual(receipt["lifecycle"][-2:], ["VERIFIED", "DONE"])
        self.assertEqual(receipt["provider_created_max_past_skew_seconds"], 300)
        self.assertEqual(result["content"], "ok")

    def test_missing_response_usage_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"model":"mock","choices":[{"index":0,'
                    b'"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.41, 50.42)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_http_200_provider_error_envelope_is_classified_as_error(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"error","message":"BadRequest",'
                    b'"type":"BadRequestError","param":null,"code":400}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.4, 50.41)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "provider_error")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_response_model_mismatch_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"other-model",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.5, 50.51)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_missing_response_model_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test",'
                    b'"created":1,"choices":[{"index":0,"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.55, 50.56)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_non_chat_response_object_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"text_completion","model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.6, 50.61)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_missing_response_object_cannot_reach_verified_state(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"finish_reason":"stop",'
                    b'"message":{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES,
            model="mock",
            environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((50.65, 50.66)).__next__,
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

    def test_active_bytes_response_body_cannot_execute_methods(self):
        method_calls = []

        class ActiveBytes(bytes):
            def __len__(self):
                method_calls.append("len")
                raise LookupError("response-body-len-must-not-run")

            def decode(self, *args, **kwargs):
                method_calls.append("decode")
                raise LookupError("response-body-decode-must-not-run")

        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return ActiveBytes(b'{"choices":[]}')

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((55.0, 55.01)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertFalse(receipt["retryable"])
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])
        self.assertEqual(method_calls, [])

    def test_non_utf8_network_json_cannot_reach_verified_state(self):
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
        document = json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "must-not-pass"},
            }]
        })
        for encoding in ("utf-16", "utf-32"):
            body = document.encode(encoding)
            with self.subTest(encoding=encoding):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=lambda *args, body=body, **kwargs: Response(body),
                    now=iter((56.0, 56.01)).__next__,
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
                b'{"choices":[{"finish_reason":"stop","message":{'
                b'"role":"assistant","content":"must-not-pass"}}],'
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

    def test_overflowing_json_exponents_cannot_reach_verified_state(self):
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
        for token in (b"1e400", b"-1e400"):
            body = (
                b'{"choices":[{"finish_reason":"stop","message":{'
                b'"role":"assistant","content":"must-not-pass"}}],'
                b'"usage":{"total_tokens":' + token + b"}}"
            )
            with self.subTest(token=token):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=lambda *args, body=body, **kwargs: Response(body),
                    now=iter((57.5, 57.51)).__next__,
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

        finite_body = (
            b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock",'
            b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
            b'"choices":[{"index":0,"finish_reason":"stop","message":{'
            b'"role":"assistant","content":"finite-ok"}}],'
            b'"telemetry":{"ratio":1e300}}'
        )
        finite_result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(finite_body),
            now=iter((57.6, 57.61)).__next__,
        )
        self.assertEqual(
            finite_result["receipt"]["outcome"],
            "invalid_provider_response",
        )
        self.assertIsNone(finite_result["content"])

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

    def test_rate_limit_retry_after_controls_cooldown_without_post_replay(self):
        class Response:
            status = 429
            def __init__(self, retry_after):
                self.headers = {"Retry-After": retry_after}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b"{}"

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        cases = (
            ("response", "137", 100.0, 137),
            ("http_error", "137", 100.0, 137),
            ("response", "Thu, 01 Jan 1970 00:04:00 GMT", 100.0, 140),
            ("http_error", "Thu, 01 Jan 1970 00:04:00 GMT", 100.0, 140),
        )
        for transport, retry_after, started, expected in cases:
            with self.subTest(transport=transport, retry_after=retry_after):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response(retry_after)
                else:
                    def opener(request, timeout, retry_after=retry_after):
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 429, "Too Many Requests",
                            {"Retry-After": retry_after}, None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((started, started + 0.01)).__next__,
                    wall_time=lambda: started,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["outcome"], "rate_limited")
                self.assertFalse(receipt["retryable"])
                self.assertEqual(receipt["cooldown_seconds"], expected)

    def test_http_date_retry_after_is_relative_to_response_receipt_time(self):
        class Response:
            status = 429
            headers = {
                "Retry-After": "Thu, 01 Jan 1970 00:04:00 GMT"
            }
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("non-200 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((100.0, 200.0)).__next__,
            wall_time=lambda: 200.0,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["outcome"], "rate_limited")
        self.assertEqual(receipt["duration_ms"], 100_000)
        self.assertEqual(receipt["cooldown_seconds"], 40)

    def test_duration_and_http_date_retry_after_use_distinct_clocks(self):
        class Response:
            status = 429
            headers = {
                "Retry-After": "Thu, 01 Jan 1970 00:04:00 GMT"
            }
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("non-200 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: Response(),
            now=iter((10.0, 10.25)).__next__,
            wall_time=lambda: 200.0,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["outcome"], "rate_limited")
        self.assertEqual(receipt["duration_ms"], 250)
        self.assertEqual(receipt["cooldown_seconds"], 40)

    def test_active_wall_clock_preserves_rate_limit_receipt(self):
        arithmetic_calls = []

        class ActiveWallTime(float):
            def __rsub__(self, other):
                arithmetic_calls.append("rsub")
                raise LookupError("wall-clock-arithmetic-must-not-run")

        class Response:
            status = 429
            headers = {
                "Retry-After": "Thu, 01 Jan 1970 00:04:00 GMT"
            }
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("non-200 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response()
                else:
                    def opener(request, timeout):
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 429, "Too Many Requests",
                            Response.headers, None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((100.0, 100.01)).__next__,
                    wall_time=lambda: ActiveWallTime(200.0),
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], 429)
                self.assertEqual(receipt["outcome"], "rate_limited")
                self.assertEqual(receipt["cooldown_seconds"], 60)
                self.assertFalse(receipt["retryable"])
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertEqual(arithmetic_calls, [])

    def test_oversized_retry_after_emits_receipt_with_safe_fallback(self):
        class Response:
            status = 429
            headers = {"Retry-After": "9" * 5000}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b"{}"

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response()
                else:
                    def opener(request, timeout):
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 429, "Too Many Requests",
                            Response.headers, None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((100.0, 100.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["outcome"], "rate_limited")
                self.assertEqual(receipt["cooldown_seconds"], 60)
                self.assertFalse(receipt["retryable"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])

    def test_impossible_retry_after_skips_parser_and_preserves_429_receipt(self):
        class Response:
            status = 429
            headers = {"Retry-After": "x" * 129}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b"{}"

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        parser_calls = []
        original_parser = MOD.parsedate_to_datetime

        def parser_must_not_run(value):
            parser_calls.append(value)
            raise AssertionError("impossible Retry-After reached date parser")

        MOD.parsedate_to_datetime = parser_must_not_run
        try:
            result = MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env,
                opener=lambda *args, **kwargs: Response(),
                now=iter((100.0, 100.01)).__next__,
            )
        finally:
            MOD.parsedate_to_datetime = original_parser

        receipt = result["receipt"]
        self.assertEqual(parser_calls, [])
        self.assertEqual(receipt["status"], 429)
        self.assertEqual(receipt["outcome"], "rate_limited")
        self.assertEqual(receipt["cooldown_seconds"], 60)
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])

    def test_retry_after_header_access_failure_preserves_rate_limit_receipt(self):
        class BrokenHeaders:
            def get(self, name, default=None):
                raise ValueError("malformed header adapter")

        class Response:
            status = 429
            headers = BrokenHeaders()
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("non-200 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response()
                else:
                    def opener(request, timeout):
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 429, "Too Many Requests",
                            BrokenHeaders(), None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((100.0, 100.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], 429)
                self.assertEqual(receipt["outcome"], "rate_limited")
                self.assertEqual(receipt["cooldown_seconds"], 60)
                self.assertFalse(receipt["retryable"])
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])

    def test_active_retry_after_value_preserves_rate_limit_receipt(self):
        method_calls = []

        class ActiveRetryAfter(str):
            def strip(self):
                method_calls.append("strip")
                raise LookupError("retry-after-value-method-must-not-run")

        class Headers:
            def get(self, name, default=None):
                return ActiveRetryAfter("137")

        class Response:
            status = 429
            headers = Headers()
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("non-200 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response()
                else:
                    def opener(request, timeout):
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 429, "Too Many Requests",
                            Headers(), None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((100.0, 100.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], 429)
                self.assertEqual(receipt["outcome"], "rate_limited")
                self.assertEqual(receipt["cooldown_seconds"], 60)
                self.assertFalse(receipt["retryable"])
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertEqual(method_calls, [])

    def test_header_property_failure_preserves_received_429_receipt(self):
        class Response:
            status = 429
            @property
            def headers(self):
                raise ValueError("broken headers property")
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("non-200 body must not be read")

        class BrokenHeaderHTTPError(MOD.urllib.error.HTTPError):
            @property
            def headers(self):
                raise ValueError("broken headers property")
            @headers.setter
            def headers(self, value):
                self.hdrs = value

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response()
                else:
                    def opener(request, timeout):
                        raise BrokenHeaderHTTPError(
                            request.full_url, 429, "Too Many Requests", {}, None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((101.0, 101.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], 429)
                self.assertEqual(receipt["outcome"], "rate_limited")
                self.assertEqual(receipt["cooldown_seconds"], 60)
                self.assertIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])

    def test_status_property_failure_emits_fail_closed_receipt(self):
        class Response:
            @property
            def status(self):
                raise RuntimeError("broken status property")
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("body must not be read without status")

        class BrokenStatusHTTPError(MOD.urllib.error.HTTPError):
            @property
            def code(self):
                raise RuntimeError("broken status property")
            @code.setter
            def code(self, value):
                self._stored_code = value
            def __str__(self):
                return "HTTP error with unreadable status"

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response()
                else:
                    def opener(request, timeout):
                        raise BrokenStatusHTTPError(
                            request.full_url, 429, "Too Many Requests", {}, None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((102.0, 102.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertIsNone(receipt["status"])
                self.assertEqual(
                    receipt["outcome"], "invalid_provider_response"
                )
                self.assertNotIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])

    def test_active_http_status_value_emits_fail_closed_receipt(self):
        comparison_calls = []

        class ActiveStatus(int):
            def __ge__(self, other):
                comparison_calls.append("ge")
                raise LookupError("status-comparison-must-not-run")

            def __le__(self, other):
                comparison_calls.append("le")
                raise LookupError("status-comparison-must-not-run")

            def __eq__(self, other):
                comparison_calls.append("eq")
                raise LookupError("status-comparison-must-not-run")

        class Response:
            status = ActiveStatus(429)
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("body must not be read without passive status")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                if transport == "response":
                    opener = lambda *args, **kwargs: Response()
                else:
                    def opener(request, timeout):
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, ActiveStatus(429),
                            "Too Many Requests", {}, None,
                        )

                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((102.0, 102.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertIsNone(receipt["status"])
                self.assertEqual(
                    receipt["outcome"], "invalid_provider_response"
                )
                self.assertNotIn("EXECUTED", receipt["lifecycle"])
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertEqual(comparison_calls, [])

    def test_unexpected_transport_adapter_failures_emit_receipts(self):
        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise RuntimeError("custom adapter body failure")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        cases = (
            (
                "before_response",
                lambda *args, **kwargs: (_ for _ in ()).throw(
                    RuntimeError("custom adapter open failure")
                ),
                None,
                "unreachable_provider",
                False,
            ),
            (
                "during_body",
                lambda *args, **kwargs: Response(),
                200,
                "incomplete_provider_response",
                True,
            ),
        )
        for name, opener, expected_status, expected_outcome, executed in cases:
            with self.subTest(name=name):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env,
                    opener=opener,
                    now=iter((103.0, 103.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertEqual(receipt["status"], expected_status)
                self.assertEqual(receipt["outcome"], expected_outcome)
                self.assertEqual("EXECUTED" in receipt["lifecycle"], executed)
                self.assertNotIn("VERIFIED", receipt["lifecycle"])
                self.assertNotIn("DONE", receipt["lifecycle"])

    def test_retry_after_cooldown_is_bounded_in_receipts(self):
        class Response:
            status = 429
            def __init__(self, retry_after):
                self.headers = {"Retry-After": retry_after}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b"{}"

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            for retry_after in ("9" * 100, "Fri, 31 Dec 9999 23:59:59 GMT"):
                with self.subTest(transport=transport, retry_after=retry_after):
                    if transport == "response":
                        opener = (
                            lambda *args, retry_after=retry_after, **kwargs:
                            Response(retry_after)
                        )
                    else:
                        def opener(request, timeout, retry_after=retry_after):
                            raise MOD.urllib.error.HTTPError(
                                request.full_url, 429, "Too Many Requests",
                                {"Retry-After": retry_after}, None,
                            )

                    result = MOD.execute_chat(
                        VALID_MESSAGES, model="mock", environ=env,
                        opener=opener,
                        now=iter((100.0, 100.01)).__next__,
                    )
                    receipt = result["receipt"]
                    self.assertEqual(receipt["outcome"], "rate_limited")
                    self.assertEqual(
                        receipt["cooldown_seconds"],
                        86_400,
                    )
                    self.assertFalse(receipt["retryable"])

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

    def test_generic_provider_errors_cannot_trigger_automatic_post_replay(self):
        class Response:
            def __init__(self, status):
                self.status = status
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b"{}"

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }

        for transport in ("response", "http_error"):
            for status in (400, 401, 403, 422, 500, 503):
                with self.subTest(transport=transport, status=status):
                    if transport == "response":
                        opener = (
                            lambda *args, status=status, **kwargs:
                            Response(status)
                        )
                    else:
                        def opener(request, timeout, status=status):
                            raise MOD.urllib.error.HTTPError(
                                request.full_url, status, "provider error", {}, None,
                            )

                    result = MOD.execute_chat(
                        VALID_MESSAGES, model="mock", environ=env,
                        opener=opener,
                        now=iter((65.02, 65.03)).__next__,
                    )
                    receipt = result["receipt"]
                    self.assertEqual(receipt["status"], status)
                    self.assertEqual(receipt["outcome"], "provider_error")
                    self.assertFalse(receipt["retryable"])
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

    def test_active_payment_latch_container_is_rejected_before_execution(self):
        leaked_text = "payment-latch-add-must-not-run"

        class ActiveLatches(set):
            def add(self, value):
                raise LookupError(leaked_text)

        class Response:
            status = 402
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("HTTP 402 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                opener_calls = []

                def opener(request, timeout):
                    opener_calls.append(transport)
                    if transport == "http_error":
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 402, "Payment Required", {}, None,
                        )
                    return Response()

                with self.assertRaisesRegex(
                    ValueError, "payment_latches_must_be_set"
                ) as caught:
                    MOD.execute_chat(
                        VALID_MESSAGES,
                        model="mock",
                        environ=env,
                        opener=opener,
                        now=iter((68.1, 68.11)).__next__,
                        payment_latches=ActiveLatches(),
                    )
                self.assertEqual(opener_calls, [])
                self.assertNotIn(leaked_text, repr(caught.exception))

    def test_process_payment_latch_storage_is_validated_before_membership(self):
        membership_calls = []
        original_latches = MOD.PROCESS_PAYMENT_LATCHES

        class ActiveProcessLatches(set):
            def __contains__(self, value):
                membership_calls.append(value)
                raise LookupError("process-latch-membership-must-not-run")

        MOD.PROCESS_PAYMENT_LATCHES = ActiveProcessLatches()
        try:
            with self.assertRaisesRegex(
                ValueError, "payment_latches_must_be_set"
            ) as caught:
                MOD.route({"NVIDIA_API_KEY": "secret"})
        finally:
            MOD.PROCESS_PAYMENT_LATCHES = original_latches

        self.assertEqual(membership_calls, [])
        self.assertNotIn(
            "process-latch-membership-must-not-run", repr(caught.exception)
        )

    def test_payment_latch_cardinality_is_bounded_before_network(self):
        class Response:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        accepted = {f"historical-latch-{index}" for index in range(1_023)}
        self.assertEqual(
            MOD.route(env, payment_latches=accepted)["selected"], "nvidia"
        )

        full = accepted | {"historical-latch-capacity"}
        full_rows = MOD.inventory(env, payment_latches=full)
        nvidia_row = next(
            row for row in full_rows if row["provider_id"] == "nvidia"
        )
        self.assertFalse(
            nvidia_row["payment_blocked_current_budget_epoch"]
        )
        self.assertTrue(nvidia_row["payment_latch_capacity_exhausted"])
        full_route = MOD.route(env, payment_latches=full)
        self.assertIsNone(full_route["selected"])
        self.assertEqual(
            full_route["reason"], "payment_latch_capacity_exhausted"
        )
        self.assertEqual(full_route["payment_blocked_providers"], [])
        self.assertTrue(full_route["payment_latch_capacity_exhausted"])

        opener_calls = []

        def opener(*args, **kwargs):
            opener_calls.append("open")
            return Response()

        oversized = full | {"historical-latch-overflow"}
        with self.assertRaisesRegex(
            ValueError, "payment_latches_too_large"
        ):
            MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ=env,
                opener=opener,
                now=iter((68.15, 68.16)).__next__,
                payment_latches=oversized,
            )
        self.assertEqual(opener_calls, [])

    def test_inventory_snapshots_payment_latches_before_membership(self):
        env = {"NVIDIA_API_KEY": "secret"}
        latches = set()
        target_key = MOD._payment_latch_key("nvidia", env)
        membership_reached = threading.Event()
        mutation_finished = threading.Event()
        original_key = MOD._payment_latch_key
        gate_used = False

        def gated_key(provider_id, snapshot):
            nonlocal gate_used
            key = original_key(provider_id, snapshot)
            if provider_id == "nvidia" and not gate_used:
                gate_used = True
                membership_reached.set()
                self.assertTrue(mutation_finished.wait(2))
            return key

        def mutate_latches():
            if membership_reached.wait(2):
                latches.add(target_key)
                mutation_finished.set()

        mutator = threading.Thread(target=mutate_latches)
        mutator.start()
        MOD._payment_latch_key = gated_key
        try:
            rows = MOD.inventory(env, payment_latches=latches)
        finally:
            MOD._payment_latch_key = original_key
            mutation_finished.set()
            mutator.join(2)

        self.assertFalse(mutator.is_alive())
        nvidia_row = next(
            row for row in rows if row["provider_id"] == "nvidia"
        )
        self.assertFalse(
            nvidia_row["payment_blocked_current_budget_epoch"]
        )
        self.assertTrue(nvidia_row["eligible"])
        self.assertIn(target_key, latches)

    def test_inventory_snapshots_latches_before_element_validation(self):
        env = {"NVIDIA_API_KEY": "secret"}
        latches = {"historical-a", "historical-b"}
        mutation_count = 0

        def mutate_during_any(iterable):
            nonlocal mutation_count
            iterator = iter(iterable)
            first = next(iterator, False)
            if mutation_count == 0:
                mutation_count += 1
                latches.add("published-during-validation")
            return bool(first) or builtins.any(iterator)

        MOD.any = mutate_during_any
        try:
            rows = MOD.inventory(env, payment_latches=latches)
        finally:
            del MOD.any

        nvidia_row = next(
            row for row in rows if row["provider_id"] == "nvidia"
        )
        self.assertEqual(mutation_count, 1)
        self.assertTrue(nvidia_row["eligible"])
        self.assertFalse(
            nvidia_row["payment_blocked_current_budget_epoch"]
        )
        self.assertIn("published-during-validation", latches)

    def test_execute_snapshots_latches_before_element_validation(self):
        class SuccessResponse:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return (
                    b'{"object":"chat.completion","id":"chatcmpl-test","created":1,"model":"mock",'
                    b'"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2},'
                    b'"choices":[{"index":0,"finish_reason":"stop","message":'
                    b'{"role":"assistant","content":"ok"}}]}'
                )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        latches = {"historical-a", "historical-b"}
        mutation_count = 0

        def mutate_during_any(iterable):
            nonlocal mutation_count
            iterator = iter(iterable)
            first = next(iterator, False)
            frame = getattr(iterator, "gi_frame", None)
            if (
                mutation_count == 0
                and frame is not None
                and "latch" in frame.f_locals
            ):
                mutation_count += 1
                latches.add("published-during-execution-validation")
            return bool(first) or builtins.any(iterator)

        MOD.any = mutate_during_any
        try:
            result = MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ=env,
                opener=lambda *args, **kwargs: SuccessResponse(),
                now=iter((68.25, 68.26)).__next__,
                payment_latches=latches,
            )
        finally:
            del MOD.any

        self.assertEqual(result["content"], "ok")
        self.assertEqual(mutation_count, 1)
        self.assertIn("published-during-execution-validation", latches)

    def test_active_payment_latch_element_is_rejected_before_execution(self):
        leaked_text = "payment-latch-element-equality-must-not-run"

        class ActiveLatchKey(str):
            __hash__ = str.__hash__

            def __new__(cls, value):
                instance = super().__new__(cls, value)
                instance.comparisons = 0
                return instance

            def __eq__(self, other):
                self.comparisons += 1
                if self.comparisons <= 2:
                    return False
                raise LookupError(leaked_text)

        class Response:
            status = 402
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                raise AssertionError("HTTP 402 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        latch_key = MOD._payment_latch_key("nvidia", env)
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                opener_calls = []
                active_key = ActiveLatchKey(latch_key)

                def opener(request, timeout):
                    opener_calls.append(transport)
                    if transport == "http_error":
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 402, "Payment Required", {}, None,
                        )
                    return Response()

                with self.assertRaisesRegex(
                    ValueError, "payment_latches_must_contain_strings"
                ) as caught:
                    MOD.execute_chat(
                        VALID_MESSAGES,
                        model="mock",
                        environ=env,
                        opener=opener,
                        now=iter((68.2, 68.21)).__next__,
                        payment_latches={active_key},
                    )
                self.assertEqual(opener_calls, [])
                self.assertEqual(active_key.comparisons, 0)
                self.assertNotIn(leaked_text, repr(caught.exception))

    def test_post_network_latch_corruption_cannot_suppress_402_receipt(self):
        leaked_text = "post-network-latch-equality-must-not-run"

        class ActiveLatchKey(str):
            __hash__ = str.__hash__

            def __eq__(self, other):
                raise LookupError(leaked_text)

        class Response:
            status = 402
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                raise AssertionError("HTTP 402 body must not be read")

        base_env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        for transport in ("response", "http_error"):
            with self.subTest(transport=transport):
                env = {
                    **base_env,
                    "FRANK_FREE_ONLY_BUDGET_EPOCH": (
                        f"post-network-corruption-{transport}"
                    ),
                }
                latch_key = MOD._payment_latch_key("nvidia", env)
                latches = set()

                def opener(request, timeout):
                    latches.add(ActiveLatchKey(latch_key))
                    if transport == "http_error":
                        raise MOD.urllib.error.HTTPError(
                            request.full_url, 402, "Payment Required", {}, None,
                        )
                    return Response()

                result = MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=opener,
                    now=iter((68.3, 68.31)).__next__,
                    payment_latches=latches,
                )
                receipt = result["receipt"]
                self.assertEqual(
                    receipt["outcome"], "payment_required_hard_stop"
                )
                self.assertEqual(receipt["status"], 402)
                self.assertTrue(receipt["payment_latch_active"])
                self.assertTrue(receipt["payment_latch_publication_failed"])
                self.assertNotIn(leaked_text, repr(result))

                with self.assertRaisesRegex(
                    ValueError, "payment_latches_must_contain_strings"
                ):
                    MOD.route(env, payment_latches=latches)

    def test_failed_latch_publication_uses_process_fallback(self):
        class ActiveLatchKey(str):
            __hash__ = str.__hash__

            def __eq__(self, other):
                raise LookupError("external-latch-corrupted")

        class PaymentResponse:
            status = 402
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                raise AssertionError("HTTP 402 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "fallback-hard-stop-epoch",
        }
        latches = set()
        latch_key = MOD._payment_latch_key("nvidia", env)
        original_process_latches = set(MOD.PROCESS_PAYMENT_LATCHES)
        MOD.PROCESS_PAYMENT_LATCHES.clear()
        try:
            def corrupting_opener(*args, **kwargs):
                latches.add(ActiveLatchKey(latch_key))
                return PaymentResponse()

            first = MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ=env,
                opener=corrupting_opener,
                now=iter((68.4, 68.41)).__next__,
                payment_latches=latches,
            )
            self.assertTrue(
                first["receipt"]["payment_latch_publication_failed"]
            )

            latches.clear()
            second_opener_calls = []
            with self.assertRaisesRegex(
                RuntimeError, "payment_required_hard_stop_active"
            ):
                MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, **kwargs: (
                        second_opener_calls.append("open") or PaymentResponse()
                    ),
                    payment_latches=latches,
                )
            self.assertEqual(second_opener_calls, [])
        finally:
            MOD.PROCESS_PAYMENT_LATCHES.clear()
            MOD.PROCESS_PAYMENT_LATCHES.update(original_process_latches)

    def test_successful_external_latch_cannot_be_cleared_for_replay(self):
        class PaymentResponse:
            status = 402
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                raise AssertionError("HTTP 402 body must not be read")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "successful-mirror-epoch",
        }
        latches = set()
        original_process_latches = set(MOD.PROCESS_PAYMENT_LATCHES)
        MOD.PROCESS_PAYMENT_LATCHES.clear()
        try:
            first = MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ=env,
                opener=lambda *args, **kwargs: PaymentResponse(),
                now=iter((68.5, 68.51)).__next__,
                payment_latches=latches,
            )
            self.assertTrue(first["receipt"]["payment_latch_active"])
            self.assertFalse(
                first["receipt"]["payment_latch_publication_failed"]
            )

            latches.clear()
            second_opener_calls = []
            with self.assertRaisesRegex(
                RuntimeError, "payment_required_hard_stop_active"
            ):
                MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, **kwargs: (
                        second_opener_calls.append("open") or PaymentResponse()
                    ),
                    payment_latches=latches,
                )
            self.assertEqual(second_opener_calls, [])
        finally:
            MOD.PROCESS_PAYMENT_LATCHES.clear()
            MOD.PROCESS_PAYMENT_LATCHES.update(original_process_latches)

    def test_response_cleanup_cannot_erase_payment_hard_stop(self):
        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
            "FRANK_FREE_ONLY_BUDGET_EPOCH": "cleanup-erasure-epoch",
        }
        latches = set()
        original_process_latches = set(MOD.PROCESS_PAYMENT_LATCHES)
        MOD.PROCESS_PAYMENT_LATCHES.clear()

        class ErasingPaymentResponse:
            status = 402
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                latches.clear()
                MOD.PROCESS_PAYMENT_LATCHES.clear()
                return False

            def read(self, limit):
                raise AssertionError("HTTP 402 body must not be read")

        try:
            first = MOD.execute_chat(
                VALID_MESSAGES,
                model="mock",
                environ=env,
                opener=lambda *args, **kwargs: ErasingPaymentResponse(),
                now=iter((68.6, 68.61)).__next__,
                payment_latches=latches,
            )
            self.assertTrue(first["receipt"]["payment_latch_active"])
            self.assertFalse(
                first["receipt"]["payment_latch_publication_failed"]
            )

            second_opener_calls = []
            with self.assertRaisesRegex(
                RuntimeError, "payment_required_hard_stop_active"
            ):
                MOD.execute_chat(
                    VALID_MESSAGES,
                    model="mock",
                    environ=env,
                    opener=lambda *args, **kwargs: (
                        second_opener_calls.append("open")
                        or ErasingPaymentResponse()
                    ),
                    payment_latches=latches,
                )
            self.assertEqual(second_opener_calls, [])
        finally:
            MOD.PROCESS_PAYMENT_LATCHES.clear()
            MOD.PROCESS_PAYMENT_LATCHES.update(original_process_latches)

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

    def test_transport_ambiguity_cannot_trigger_automatic_post_replay(self):
        class BodyTimeoutResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): raise TimeoutError("body stalled")

        def remote_disconnect(request, timeout):
            raise http.client.RemoteDisconnected(
                "remote end closed connection without response"
            )

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        openers = (
            remote_disconnect,
            lambda *args, **kwargs: BodyTimeoutResponse(),
        )
        for opener in openers:
            with self.subTest(opener=opener.__name__):
                result = MOD.execute_chat(
                    VALID_MESSAGES, model="mock", environ=env, opener=opener,
                    now=iter((80.0, 80.01)).__next__,
                )
                receipt = result["receipt"]
                self.assertFalse(receipt["retryable"])
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

    def test_context_exit_cannot_suppress_oversized_response_rejection(self):
        def encoded_payload(content):
            return json.dumps({
                "choices": [{
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }]
            }).encode()

        empty_payload = encoded_payload("")
        body = encoded_payload(
            "x" * (MOD.MAX_PROVIDER_RESPONSE_BYTES + 1 - len(empty_payload))
        )
        self.assertEqual(len(body), MOD.MAX_PROVIDER_RESPONSE_BYTES + 1)

        class SuppressingResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return True
            def read(self, limit): return body[:limit]

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: SuppressingResponse(),
            now=iter((95.1, 95.11)).__next__,
        )
        receipt = result["receipt"]
        self.assertEqual(receipt["status"], 200)
        self.assertEqual(receipt["outcome"], "provider_response_too_large")
        self.assertIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_context_exit_cannot_suppress_invalid_status_receipt(self):
        class SuppressingResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return True
            def read(self, limit):
                raise AssertionError("body must not be read without status")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        result = MOD.execute_chat(
            VALID_MESSAGES, model="mock", environ=env,
            opener=lambda *args, **kwargs: SuppressingResponse(),
            now=iter((95.2, 95.21)).__next__,
        )
        receipt = result["receipt"]
        self.assertIsNone(receipt["status"])
        self.assertEqual(receipt["outcome"], "invalid_provider_response")
        self.assertNotIn("EXECUTED", receipt["lifecycle"])
        self.assertNotIn("VERIFIED", receipt["lifecycle"])
        self.assertNotIn("DONE", receipt["lifecycle"])
        self.assertIsNone(result["content"])

    def test_context_exit_cannot_suppress_process_control_signal(self):
        class SuppressingResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return True
            def read(self, limit): raise SystemExit("operator stop")

        env = {
            "NVIDIA_API_KEY": "secret",
            "FRANK_PROVIDER_BASE_URL": "http://localhost:8765/v1",
            "FRANK_ALLOW_LOCAL_TEST_ENDPOINT": "1",
        }
        with self.assertRaisesRegex(SystemExit, "operator stop"):
            MOD.execute_chat(
                VALID_MESSAGES, model="mock", environ=env,
                opener=lambda *args, **kwargs: SuppressingResponse(),
                now=iter((95.3, 95.31)).__next__,
            )

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
