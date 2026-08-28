#!/usr/bin/env python3
from pathlib import Path
import tempfile
import unittest

from grid10_persistent_agency_v1 import (
    DeferredIntentState,
    GoalState,
    InvalidTransition,
    PersistentAgencyStore,
    StaleGeneration,
    WakeKind,
)


class PersistentAgencyTests(unittest.TestCase):
    def make_store(self, td: str) -> PersistentAgencyStore:
        return PersistentAgencyStore(Path(td) / "agency.sqlite")

    def seed_active(self, store: PersistentAgencyStore, *, now: float = 100.0):
        g = store.create_goal(
            goal_id="g1", origin="AUTHENTICATED_USER", semantic_goal="finish bounded task",
            state=GoalState.CANDIDATE, success_criteria=("verified receipt",),
            uncertainty=0.2, priority=10, event_id="e:create", now_ts=now,
        )
        return store.transition_goal(
            "g1", expected_generation=g.generation, new_state=GoalState.ACTIVE,
            event_id="e:activate", reason="admitted", now_ts=now + 1,
        )

    def test_restart_preserves_goal_checkpoint_and_scheduler(self):
        with tempfile.TemporaryDirectory() as td:
            store = self.make_store(td)
            active = self.seed_active(store)
            store.set_continuation_checkpoint(
                {"goal_id": active.goal_id, "deficits": ["receipt"]},
                event_id="e:checkpoint", now_ts=102,
            )
            store.schedule_next_tick(not_before=150, mode="NORMAL", event_id="e:schedule", now_ts=103)

            reopened = self.make_store(td)
            snap = reopened.snapshot()
            self.assertEqual(snap.goals[0].state, GoalState.ACTIVE)
            self.assertIn('"deficits":["receipt"]', snap.continuation_checkpoint)
            self.assertFalse(reopened.due_for_tick(now_ts=149.9))
            self.assertTrue(reopened.due_for_tick(now_ts=150.0))
            self.assertGreaterEqual(snap.state_epoch, 4)

    def test_stale_generation_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store = self.make_store(td)
            active = self.seed_active(store)
            with self.assertRaises(StaleGeneration):
                store.transition_goal(
                    "g1", expected_generation=active.generation - 1,
                    new_state=GoalState.COMPLETED, event_id="e:stale", reason="bad writer", now_ts=120,
                )
            self.assertEqual(store.get_goal("g1").state, GoalState.ACTIVE)

    def test_invalid_terminal_transition_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            store = self.make_store(td)
            active = self.seed_active(store)
            done = store.transition_goal(
                "g1", expected_generation=active.generation, new_state=GoalState.COMPLETED,
                event_id="e:done", reason="verified elsewhere", now_ts=130,
            )
            with self.assertRaises(InvalidTransition):
                store.transition_goal(
                    "g1", expected_generation=done.generation, new_state=GoalState.ACTIVE,
                    event_id="e:revive", reason="not allowed", now_ts=131,
                )

    def test_hold_wake_resume_across_restart(self):
        with tempfile.TemporaryDirectory() as td:
            store = self.make_store(td)
            active = self.seed_active(store)
            intent = store.defer_goal(
                "g1", expected_generation=active.generation, intent_id="i1",
                wake_kind=WakeKind.TIME_AT, wake_value="200", event_id="e:defer",
                reason="wait for bounded condition", now_ts=140,
            )
            self.assertEqual(store.get_goal("g1").state, GoalState.DORMANT)
            self.assertEqual(intent.state, DeferredIntentState.PENDING)

            reopened = self.make_store(td)
            self.assertEqual(reopened.wake_due(now_ts=199), ())
            self.assertEqual(reopened.get_goal("g1").state, GoalState.DORMANT)
            self.assertEqual(reopened.wake_due(now_ts=200), ("g1",))
            self.assertEqual(reopened.get_goal("g1").state, GoalState.ACTIVE)
            self.assertEqual(reopened.get_intent("i1").state, DeferredIntentState.FIRED)

    def test_stale_deferred_intent_cannot_revive_changed_goal(self):
        with tempfile.TemporaryDirectory() as td:
            store = self.make_store(td)
            active = self.seed_active(store)
            store.defer_goal(
                "g1", expected_generation=active.generation, intent_id="i1",
                wake_kind=WakeKind.EVENT, wake_value="new-evidence", event_id="e:defer",
                reason="need evidence", now_ts=140,
            )
            dormant = store.get_goal("g1")
            store.transition_goal(
                "g1", expected_generation=dormant.generation, new_state=GoalState.BLOCKED,
                event_id="e:block", reason="new policy block", now_ts=141,
            )
            self.assertEqual(store.wake_due(now_ts=142, observed_events=("new-evidence",)), ())
            self.assertEqual(store.get_goal("g1").state, GoalState.BLOCKED)
            self.assertEqual(store.get_intent("i1").state, DeferredIntentState.STALE)

    def test_event_wake_is_exact_not_any_event(self):
        with tempfile.TemporaryDirectory() as td:
            store = self.make_store(td)
            active = self.seed_active(store)
            store.defer_goal(
                "g1", expected_generation=active.generation, intent_id="i1",
                wake_kind=WakeKind.EVENT, wake_value="camera:person-entered", event_id="e:defer",
                reason="perception-driven continuation", now_ts=140,
            )
            self.assertEqual(store.wake_due(now_ts=150, observed_events=("camera:motion",)), ())
            self.assertEqual(store.wake_due(now_ts=151, observed_events=("camera:person-entered",)), ("g1",))


if __name__ == "__main__":
    unittest.main()
