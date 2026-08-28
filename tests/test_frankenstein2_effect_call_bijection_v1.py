import tempfile
from pathlib import Path
import unittest

from tools.frankenstein2_effect_call_bijection_v1 import (
    EffectCallBijectionError,
    EffectCallBijectionStore,
    reenter_bijected_result,
)


class _FakeLifecycleStore:
    def __init__(self):
        self.reentries = []

    def reenter_result(self, invocation_id, *, result_digest, now_ts=None):
        self.reentries.append((invocation_id, result_digest, now_ts))


class EffectCallBijectionTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.bindings = EffectCallBijectionStore(Path(self.td.name) / "call_effect.sqlite")
        self.lifecycle = _FakeLifecycleStore()

    def tearDown(self):
        self.td.cleanup()

    def _bind(self, call_id, effect_id, *, task_id, turn_id, causal_id):
        return self.bindings.bind_once(
            immutable_call_id=call_id,
            canonical_effect_id=effect_id,
            session_id="shared-session",
            agent_id="agent-1",
            task_id=task_id,
            turn_id=turn_id,
            causal_id=causal_id,
            generation=7,
            now_ts=100.0,
        )

    def test_overlapping_a_b_wrong_target_is_rejected_before_lifecycle_mutation(self):
        self._bind("call-A", "effect-A", task_id="task-A", turn_id="turn-A", causal_id="cause-A")
        self._bind("call-B", "effect-B", task_id="task-B", turn_id="turn-B", causal_id="cause-B")

        # Interleaving or a mutable session pointer may select effect-A after call-B returns.
        # The immutable external call id must make that cross-attachment impossible even
        # when both calls return the same result digest.
        with self.assertRaisesRegex(EffectCallBijectionError, "CALL_EFFECT_BIJECTION_MISMATCH"):
            reenter_bijected_result(
                self.bindings,
                self.lifecycle,
                immutable_call_id="call-B",
                target_canonical_effect_id="effect-A",
                result_digest="same-result-digest",
            )
        self.assertEqual(self.lifecycle.reentries, [])

        reenter_bijected_result(
            self.bindings,
            self.lifecycle,
            immutable_call_id="call-B",
            target_canonical_effect_id="effect-B",
            result_digest="same-result-digest",
        )
        reenter_bijected_result(
            self.bindings,
            self.lifecycle,
            immutable_call_id="call-A",
            target_canonical_effect_id="effect-A",
            result_digest="same-result-digest",
        )
        self.assertEqual(
            [row[:2] for row in self.lifecycle.reentries],
            [
                ("effect-B", "same-result-digest"),
                ("effect-A", "same-result-digest"),
            ],
        )

    def test_call_id_cannot_be_reassigned_to_second_effect(self):
        self._bind("call-A", "effect-A", task_id="task-A", turn_id="turn-A", causal_id="cause-A")
        with self.assertRaisesRegex(EffectCallBijectionError, "IMMUTABLE_CALL_ID_ALREADY_BOUND"):
            self._bind("call-A", "effect-B", task_id="task-B", turn_id="turn-B", causal_id="cause-B")
        self.assertEqual(self.bindings.resolve_call("call-A").canonical_effect_id, "effect-A")

    def test_effect_id_cannot_be_reassigned_to_second_call(self):
        self._bind("call-A", "effect-A", task_id="task-A", turn_id="turn-A", causal_id="cause-A")
        with self.assertRaisesRegex(EffectCallBijectionError, "CANONICAL_EFFECT_ID_ALREADY_BOUND"):
            self._bind("call-B", "effect-A", task_id="task-B", turn_id="turn-B", causal_id="cause-B")
        self.assertEqual(self.bindings.resolve_effect("effect-A").immutable_call_id, "call-A")

    def test_same_pair_cannot_be_rebound_and_lineage_stays_create_once(self):
        first = self._bind("call-A", "effect-A", task_id="task-A", turn_id="turn-A", causal_id="cause-A")
        with self.assertRaisesRegex(EffectCallBijectionError, "IMMUTABLE_CALL_ID_ALREADY_BOUND"):
            self._bind("call-A", "effect-A", task_id="task-other", turn_id="turn-other", causal_id="cause-other")
        current = self.bindings.resolve_call("call-A")
        self.assertEqual(current, first)
        self.assertEqual(current.task_id, "task-A")
        self.assertEqual(current.turn_id, "turn-A")
        self.assertEqual(current.causal_id, "cause-A")

    def test_unknown_call_and_missing_result_fail_closed(self):
        with self.assertRaisesRegex(EffectCallBijectionError, "UNKNOWN_IMMUTABLE_CALL_ID"):
            self.bindings.resolve_call("missing")
        self._bind("call-A", "effect-A", task_id="task-A", turn_id="turn-A", causal_id="cause-A")
        with self.assertRaisesRegex(EffectCallBijectionError, "MISSING_RESULT_DIGEST"):
            reenter_bijected_result(
                self.bindings,
                self.lifecycle,
                immutable_call_id="call-A",
                target_canonical_effect_id="effect-A",
                result_digest="",
            )
        self.assertEqual(self.lifecycle.reentries, [])


if __name__ == "__main__":
    unittest.main()
