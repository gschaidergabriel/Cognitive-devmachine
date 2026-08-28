#!/usr/bin/env python3
"""Focused falsifiers for the native Frankenstein2 execution-bundle writer.

These tests deliberately target EffectLifecycleStore.record_execution_bundle(), i.e. the
production writer reached by guarded_dispatch after a successful callback.  They do not
invoke an external effect.  The injected SQLite trigger aborts the second logical insert
so rollback of the first insert and both event rows can be observed directly.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from frankenstein2_effect_lifecycle_v1 import (
    AdmissionDecision,
    EffectLifecycleError,
    EffectLifecycleStore,
)


SOURCE_DIGEST = "s" * 64


def prepare_submitted_store(db: Path) -> tuple[EffectLifecycleStore, object]:
    store = EffectLifecycleStore(db)
    req = store.build_request(
        invocation_id="inv-native-atomic",
        session_id="session-native-atomic",
        agent_id="frankenstein-2",
        task_id="task-native-atomic",
        turn_id="turn-native-atomic",
        causal_id="cause-native-atomic",
        generation=19,
        tool_name="bounded-tool",
        normalized_arguments={"probe": "native-atomicity"},
        effect_scope="TEST_ONLY",
    )
    store.create_request(req, now_ts=1.0)
    store.bind_completion_source(
        req.invocation_id,
        source_digest=SOURCE_DIGEST,
        now_ts=2.0,
    )
    store.decide(
        req.invocation_id,
        AdmissionDecision.ALLOW,
        reason="native atomicity regression",
        now_ts=3.0,
    )
    store.record_enforcement(
        req.invocation_id,
        boundary_id="native-atomicity-boundary",
        dispatch_permitted=True,
        now_ts=4.0,
    )
    store.mark_submitted(req.invocation_id, now_ts=5.0)
    return store, req


def record_bundle(store: EffectLifecycleStore, *, source_digest: str = SOURCE_DIGEST) -> None:
    store.record_execution_bundle(
        "inv-native-atomic",
        executable_id="tool:fixture",
        command_digest="c" * 64,
        environment_id="env:test",
        exit_code=0,
        result_digest="r" * 64,
        source_digest=source_digest,
        duplicate_state="UNIQUE",
        status="SUCCEEDED",
        now_ts=6.0,
    )


class NativeExecutionReceiptAtomicityTests(unittest.TestCase):
    def test_second_insert_abort_rolls_back_base_metadata_and_execution_events(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, _ = prepare_submitted_store(Path(td) / "effects.sqlite")
            con = store._con()
            try:
                con.executescript(
                    """
                    CREATE TRIGGER inject_execution_v2_metadata_failure
                    BEFORE INSERT ON execution_v2_metadata
                    BEGIN
                      SELECT RAISE(ABORT, 'INJECTED_EXECUTION_V2_METADATA_FAILURE');
                    END;
                    """
                )
            finally:
                con.close()

            with self.assertRaisesRegex(
                EffectLifecycleError,
                "EXECUTION_BUNDLE_PERSISTENCE_CONFLICT",
            ):
                record_bundle(store)

            snapshot = store.snapshot("inv-native-atomic")
            self.assertIsNone(snapshot["execution"])
            self.assertIsNone(snapshot["execution_v2"])

            con = store._con()
            try:
                event_types = {
                    row[0]
                    for row in con.execute(
                        "SELECT event_type FROM effect_lifecycle_events WHERE invocation_id=?",
                        ("inv-native-atomic",),
                    )
                }
            finally:
                con.close()
            self.assertNotIn("EXECUTION_RECORDED", event_types)
            self.assertNotIn("EXECUTION_V2_METADATA_RECORDED", event_types)

    def test_success_commits_both_rows_with_same_invocation_request_and_source_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, req = prepare_submitted_store(Path(td) / "effects.sqlite")
            record_bundle(store)
            snapshot = store.snapshot("inv-native-atomic")

            self.assertEqual(snapshot["execution"]["invocation_id"], req.invocation_id)
            self.assertEqual(snapshot["execution_v2"]["invocation_id"], req.invocation_id)
            self.assertEqual(snapshot["execution"]["request_digest"], req.request_digest)
            self.assertEqual(snapshot["execution_v2"]["source_digest"], SOURCE_DIGEST)
            self.assertEqual(snapshot["execution_v2"]["status"], "SUCCEEDED")
            self.assertEqual(req.generation, 19)

    def test_source_drift_fails_before_either_execution_row_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, _ = prepare_submitted_store(Path(td) / "effects.sqlite")
            with self.assertRaisesRegex(
                EffectLifecycleError,
                "EXECUTION_SOURCE_DIGEST_MISMATCH",
            ):
                record_bundle(store, source_digest="x" * 64)

            snapshot = store.snapshot("inv-native-atomic")
            self.assertIsNone(snapshot["execution"])
            self.assertIsNone(snapshot["execution_v2"])

    def test_legacy_half_bundle_is_not_silently_completed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store, _ = prepare_submitted_store(Path(td) / "effects.sqlite")
            # Reproduce the old crash window: base row exists while v2 metadata is absent.
            store.record_execution(
                "inv-native-atomic",
                executable_id="tool:fixture",
                command_digest="c" * 64,
                environment_id="env:test",
                exit_code=0,
                result_digest="r" * 64,
                now_ts=6.0,
            )
            self.assertIsNotNone(store.snapshot("inv-native-atomic")["execution"])
            self.assertIsNone(store.snapshot("inv-native-atomic")["execution_v2"])

            with self.assertRaisesRegex(
                EffectLifecycleError,
                "EXECUTION_RECEIPT_ALREADY_FINAL",
            ):
                record_bundle(store)
            self.assertIsNone(store.snapshot("inv-native-atomic")["execution_v2"])


if __name__ == "__main__":
    unittest.main()
