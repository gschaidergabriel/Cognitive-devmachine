#!/usr/bin/env python3
import tempfile
from pathlib import Path
import unittest

from frankenstein2_effect_dispatch_boundary_v1 import (
    EffectDispatchBoundaryError,
    EffectSubmittedOutcomeUnknown,
    ExecutionObservation,
    guarded_dispatch,
)
from frankenstein2_effect_lifecycle_v1 import (
    AdmissionDecision,
    EffectLifecycleError,
    EffectLifecycleStore,
)
from frankenstein2_execution_receipt_atomicity_v1 import record_execution_bundle_atomic


class FakeStore:
    def __init__(self, stored_decision="ALLOW", fail_record_execution=False):
        self.stored_decision = stored_decision
        self.fail_record_execution = fail_record_execution
        self.events = []

    def record_enforcement(self, invocation_id, *, boundary_id, dispatch_permitted, now_ts=None):
        expected = self.stored_decision == "ALLOW"
        self.events.append(("enforcement", invocation_id, boundary_id, dispatch_permitted))
        if bool(dispatch_permitted) != expected:
            raise RuntimeError("ENFORCEMENT_CONTRADICTS_ADMISSION")

    def mark_submitted(self, invocation_id, *, now_ts=None):
        self.events.append(("submitted", invocation_id))

    def record_execution(self, invocation_id, **kwargs):
        self.events.append(("execution", invocation_id, kwargs["result_digest"]))
        if self.fail_record_execution:
            raise OSError("receipt write failed")

    def record_execution_v2_metadata(self, invocation_id, **kwargs):
        self.events.append(("execution_v2", invocation_id, kwargs["status"], kwargs["duplicate_state"]))

    # Logical atomic-bundle seam used only by this deterministic boundary fake. The real
    # EffectLifecycleStore path is exercised separately below and uses one SQLite txn.
    def record_execution_bundle_atomic(self, invocation_id, **kwargs):
        self.record_execution(
            invocation_id,
            executable_id=kwargs["executable_id"],
            command_digest=kwargs["command_digest"],
            environment_id=kwargs["environment_id"],
            exit_code=kwargs["exit_code"],
            result_digest=kwargs["result_digest"],
            now_ts=kwargs.get("now_ts"),
        )
        self.record_execution_v2_metadata(
            invocation_id,
            source_digest=kwargs["source_digest"],
            duplicate_state=kwargs["duplicate_state"],
            status=kwargs["status"],
            now_ts=kwargs.get("now_ts"),
        )
        return "fake-request-digest"


def obs(exit_code=0, status=None):
    return ExecutionObservation(
        executable_id="tool:fixture",
        command_digest="c" * 64,
        environment_id="env:test",
        exit_code=exit_code,
        result_digest="r" * 64,
        source_digest="s" * 64,
        status=status,
    )


def prepare_submitted_store(db: Path, invocation_id: str = "inv-atomic"):
    store = EffectLifecycleStore(db)
    req = store.build_request(
        invocation_id=invocation_id,
        session_id="session-atomic",
        agent_id="frankenstein-2",
        task_id="task-atomic",
        turn_id="turn-atomic",
        causal_id="cause-atomic",
        generation=17,
        tool_name="bounded-tool",
        normalized_arguments={"x": 1},
        effect_scope="TEST_ONLY",
    )
    store.create_request(req, now_ts=1.0)
    store.bind_completion_source(invocation_id, source_digest="s" * 64, now_ts=2.0)
    store.decide(invocation_id, AdmissionDecision.ALLOW, reason="atomic regression", now_ts=3.0)
    store.record_enforcement(
        invocation_id,
        boundary_id="atomic-regression-boundary",
        dispatch_permitted=True,
        now_ts=4.0,
    )
    store.mark_submitted(invocation_id, now_ts=5.0)
    return store, req


class EffectDispatchBoundaryTests(unittest.TestCase):
    def test_deny_never_calls_dispatch(self):
        store = FakeStore("DENY")
        calls = []
        out = guarded_dispatch(
            store,
            invocation_id="inv-a",
            admission_decision="DENY",
            boundary_id="host-boundary",
            dispatch=lambda: calls.append(1),
        )
        self.assertFalse(out.dispatched)
        self.assertEqual(out.terminal_class, "BLOCKED_PRE_DISPATCH")
        self.assertEqual(calls, [])
        self.assertEqual(store.events, [("enforcement", "inv-a", "host-boundary", False)])

    def test_unknown_never_calls_dispatch(self):
        store = FakeStore("UNKNOWN")
        calls = []
        out = guarded_dispatch(
            store,
            invocation_id="inv-u",
            admission_decision="UNKNOWN",
            boundary_id="host-boundary",
            dispatch=lambda: calls.append(1),
        )
        self.assertFalse(out.dispatched)
        self.assertEqual(calls, [])

    def test_allow_latches_submitted_before_dispatch_and_records_receipt(self):
        store = FakeStore("ALLOW")
        calls = []

        def dispatch():
            calls.append("called")
            store.events.append(("callback", "inv-a"))
            return obs()

        out = guarded_dispatch(
            store,
            invocation_id="inv-a",
            admission_decision="ALLOW",
            boundary_id="host-boundary",
            dispatch=dispatch,
        )
        self.assertTrue(out.dispatched)
        self.assertEqual(calls, ["called"])
        self.assertEqual([e[0] for e in store.events], [
            "enforcement", "submitted", "callback", "execution", "execution_v2"
        ])
        self.assertEqual(store.events[-1][2], "SUCCEEDED")

    def test_mismatched_allow_is_rejected_before_dispatch(self):
        store = FakeStore("DENY")
        calls = []
        with self.assertRaises(RuntimeError):
            guarded_dispatch(
                store,
                invocation_id="inv-x",
                admission_decision="ALLOW",
                boundary_id="host-boundary",
                dispatch=lambda: calls.append(1),
            )
        self.assertEqual(calls, [])
        self.assertEqual([e[0] for e in store.events], ["enforcement"])

    def test_callback_failure_after_submitted_is_unknown_not_retryable_success(self):
        store = FakeStore("ALLOW")

        def dispatch():
            store.events.append(("callback", "inv-e"))
            raise TimeoutError("transport lost")

        with self.assertRaises(EffectSubmittedOutcomeUnknown) as ctx:
            guarded_dispatch(
                store,
                invocation_id="inv-e",
                admission_decision="ALLOW",
                boundary_id="host-boundary",
                dispatch=dispatch,
            )
        self.assertIn("DISPATCH_CALLBACK_FAILED_AFTER_SUBMITTED", str(ctx.exception))
        self.assertEqual([e[0] for e in store.events], ["enforcement", "submitted", "callback"])

    def test_receipt_failure_after_callback_is_unknown(self):
        store = FakeStore("ALLOW", fail_record_execution=True)
        with self.assertRaises(EffectSubmittedOutcomeUnknown) as ctx:
            guarded_dispatch(
                store,
                invocation_id="inv-r",
                admission_decision="ALLOW",
                boundary_id="host-boundary",
                dispatch=lambda: obs(),
            )
        self.assertIn("RECEIPT_PERSISTENCE_FAILED_AFTER_SUBMITTED", str(ctx.exception))

    def test_nonzero_exit_maps_to_failed(self):
        store = FakeStore("ALLOW")
        guarded_dispatch(
            store,
            invocation_id="inv-f",
            admission_decision="ALLOW",
            boundary_id="host-boundary",
            dispatch=lambda: obs(exit_code=7),
        )
        self.assertEqual(store.events[-1][2], "FAILED")

    def test_invalid_inputs_fail_before_enforcement(self):
        store = FakeStore("ALLOW")
        with self.assertRaises(EffectDispatchBoundaryError):
            guarded_dispatch(
                store,
                invocation_id="",
                admission_decision="ALLOW",
                boundary_id="host-boundary",
                dispatch=lambda: obs(),
            )
        self.assertEqual(store.events, [])


class EffectReceiptAtomicityIntegrationTests(unittest.TestCase):
    def test_injected_failure_after_base_insert_rolls_back_both_logical_records(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "effects.sqlite"
            store, _ = prepare_submitted_store(db)

            with self.assertRaisesRegex(
                EffectLifecycleError,
                "INJECTED_FAILURE_AFTER_BASE_EXECUTION_RECEIPT",
            ):
                record_execution_bundle_atomic(
                    store,
                    "inv-atomic",
                    executable_id="tool:fixture",
                    command_digest="c" * 64,
                    environment_id="env:test",
                    exit_code=0,
                    result_digest="r" * 64,
                    source_digest="s" * 64,
                    duplicate_state="UNIQUE",
                    status="SUCCEEDED",
                    now_ts=6.0,
                    _inject_failure_after_base_insert=True,
                )

            snap = store.snapshot("inv-atomic")
            self.assertIsNone(snap["execution"])
            self.assertIsNone(snap["execution_v2"])

            con = store._con()
            try:
                event_types = {
                    row[0]
                    for row in con.execute(
                        "SELECT event_type FROM effect_lifecycle_events WHERE invocation_id=?",
                        ("inv-atomic",),
                    )
                }
            finally:
                con.close()
            self.assertNotIn("EXECUTION_RECORDED", event_types)
            self.assertNotIn("EXECUTION_V2_METADATA_RECORDED", event_types)

    def test_success_path_commits_base_and_v2_with_one_bound_lineage(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "effects.sqlite"
            store, req = prepare_submitted_store(db)
            record_execution_bundle_atomic(
                store,
                "inv-atomic",
                executable_id="tool:fixture",
                command_digest="c" * 64,
                environment_id="env:test",
                exit_code=0,
                result_digest="r" * 64,
                source_digest="s" * 64,
                duplicate_state="UNIQUE",
                status="SUCCEEDED",
                now_ts=6.0,
            )
            snap = store.snapshot("inv-atomic")
            self.assertIsNotNone(snap["execution"])
            self.assertIsNotNone(snap["execution_v2"])
            self.assertEqual(snap["execution"]["invocation_id"], "inv-atomic")
            self.assertEqual(snap["execution_v2"]["invocation_id"], "inv-atomic")
            self.assertEqual(snap["execution"]["request_digest"], req.request_digest)
            self.assertEqual(snap["execution_v2"]["source_digest"], "s" * 64)
            self.assertEqual(snap["execution_v2"]["status"], "SUCCEEDED")
            self.assertEqual(req.generation, 17)

    def test_legacy_partial_bundle_fails_closed_instead_of_silent_completion(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "effects.sqlite"
            store, _ = prepare_submitted_store(db)
            # Reproduce the historical partial state: base row exists, v2 metadata absent.
            store.record_execution(
                "inv-atomic",
                executable_id="tool:fixture",
                command_digest="c" * 64,
                environment_id="env:test",
                exit_code=0,
                result_digest="r" * 64,
                now_ts=6.0,
            )
            self.assertIsNotNone(store.snapshot("inv-atomic")["execution"])
            self.assertIsNone(store.snapshot("inv-atomic")["execution_v2"])

            with self.assertRaisesRegex(EffectLifecycleError, "PARTIAL_EXECUTION_BUNDLE_STATE"):
                record_execution_bundle_atomic(
                    store,
                    "inv-atomic",
                    executable_id="tool:fixture",
                    command_digest="c" * 64,
                    environment_id="env:test",
                    exit_code=0,
                    result_digest="r" * 64,
                    source_digest="s" * 64,
                    duplicate_state="UNIQUE",
                    status="SUCCEEDED",
                    now_ts=7.0,
                )
            self.assertIsNone(store.snapshot("inv-atomic")["execution_v2"])

    def test_guarded_dispatch_real_store_commits_the_atomic_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "effects.sqlite"
            store = EffectLifecycleStore(db)
            req = store.build_request(
                invocation_id="inv-dispatch",
                session_id="session-dispatch",
                agent_id="frankenstein-2",
                task_id="task-dispatch",
                turn_id="turn-dispatch",
                causal_id="cause-dispatch",
                generation=18,
                tool_name="bounded-tool",
                normalized_arguments={"x": 2},
                effect_scope="TEST_ONLY",
            )
            store.create_request(req, now_ts=1.0)
            store.bind_completion_source("inv-dispatch", source_digest="s" * 64, now_ts=2.0)
            store.decide(
                "inv-dispatch",
                AdmissionDecision.ALLOW,
                reason="guarded dispatch atomic regression",
                now_ts=3.0,
            )

            out = guarded_dispatch(
                store,
                invocation_id="inv-dispatch",
                admission_decision="ALLOW",
                boundary_id="host-boundary",
                dispatch=lambda: obs(),
                now_ts=4.0,
            )
            self.assertTrue(out.dispatched)
            snap = store.snapshot("inv-dispatch")
            self.assertEqual(snap["request"]["pending_state"], "SUBMITTED")
            self.assertEqual(snap["execution"]["request_digest"], req.request_digest)
            self.assertEqual(snap["execution_v2"]["source_digest"], "s" * 64)
            self.assertEqual(snap["execution_v2"]["duplicate_state"], "UNIQUE")
            self.assertEqual(snap["execution_v2"]["status"], "SUCCEEDED")


if __name__ == "__main__":
    unittest.main()
