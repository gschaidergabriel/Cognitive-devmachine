#!/usr/bin/env python3
import unittest

from frankenstein2_effect_dispatch_boundary_v1 import (
    EffectDispatchBoundaryError,
    EffectSubmittedOutcomeUnknown,
    ExecutionObservation,
    guarded_dispatch,
)


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


if __name__ == "__main__":
    unittest.main()
