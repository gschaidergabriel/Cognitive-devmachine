from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from global_workspace_fixture_v1 import (
    GlobalWorkspaceError,
    GlobalWorkspaceFixture,
    WorkspaceCandidate,
)


def candidate(
    result_id: str,
    result_digest: str,
    salience: int,
    *,
    event: str = "event-1",
    generation: int = 7,
    process: str = "ZECP08",
    uncertainty: str = "UNKNOWN",
) -> WorkspaceCandidate:
    return WorkspaceCandidate(
        causal_event_id=event,
        admission_id="admission-1",
        generation=generation,
        work_id="work-" + result_id,
        process_id=process,
        result_id=result_id,
        result_class="CANDIDATE",
        result_digest=result_digest,
        salience_score=salience,
        uncertainty=uncertainty,
        provenance_ref="prov://fixture",
    )


class GlobalWorkspaceFixtureV1Tests(unittest.TestCase):
    def test_d1_selection_is_invariant_to_input_order(self):
        values = [
            candidate("r1", "b" * 64, 4),
            candidate("r2", "a" * 64, 7),
            candidate("r3", "c" * 64, 1),
        ]
        a = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=1)
        b = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=20)
        sa = a.compete(values, workspace_epoch=3)
        sb = b.compete(list(reversed(values)), workspace_epoch=3)
        self.assertEqual(sa["selection_id"], sb["selection_id"])
        self.assertEqual("r2", sa["selected_result_id"])

    def test_d2_grid_n_changes_capacity_not_workspace_semantics(self):
        self.assertEqual(
            GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=1).semantic_fingerprint(),
            GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=64).semantic_fingerprint(),
        )

    def test_d3_ties_are_deterministic_and_alternatives_are_preserved(self):
        values = [
            candidate("r-b", "b" * 64, 9),
            candidate("r-a", "a" * 64, 9),
            candidate("r-low", "c" * 64, 1),
        ]
        ws = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=10)
        selection = ws.compete(values, workspace_epoch=5)
        self.assertEqual("r-a", selection["selected_result_id"])
        self.assertEqual(["r-a", "r-b"], selection["tied_alternative_result_ids"])
        self.assertEqual("ATTENTION_SELECTION_ONLY_NOT_CANONICAL_TRUTH", selection["authority"])

    def test_recurrence_does_not_create_vote_weight_or_truth(self):
        repeated = candidate("repeat-1", "d" * 64, 1)
        values = [
            repeated,
            candidate("repeat-2", "d" * 64, 1),
            candidate("repeat-3", "d" * 64, 1),
            candidate("strong", "a" * 64, 2),
        ]
        ws = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=10)
        selection = ws.compete(values, workspace_epoch=1)
        self.assertEqual("strong", selection["selected_result_id"])
        self.assertEqual(2, selection["deduplicated_recurrence_count"])

    def test_d4_cross_event_and_stale_generation_fail_closed(self):
        ws = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=10)
        with self.assertRaisesRegex(GlobalWorkspaceError, "CROSS_CAUSAL_EVENT"):
            ws.compete([candidate("r1", "a" * 64, 1, event="event-2")], workspace_epoch=1)
        with self.assertRaisesRegex(GlobalWorkspaceError, "STALE_GENERATION"):
            ws.compete([candidate("r1", "a" * 64, 1, generation=6)], workspace_epoch=1)

    def test_d5_broadcast_targets_process_ids_not_executor_ids(self):
        ws = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=10)
        selection = ws.compete([candidate("r1", "a" * 64, 1)], workspace_epoch=1)
        packet = ws.broadcast(selection, ["ZECP03", "ZECP14", "ZECP03"])
        self.assertEqual(["ZECP03", "ZECP14"], packet["target_process_ids"])
        self.assertEqual("NONCANONICAL_S1_DELIVERY_ONLY", packet["authority"])
        with self.assertRaisesRegex(GlobalWorkspaceError, "BROADCAST_TARGET_MUST_BE_PROCESS_ID"):
            ws.broadcast(selection, ["fixture-executor-0001"])

    def test_d6_reentry_presence_and_downstream_change_keep_jspace_credit_zero(self):
        ws = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=10)
        selection = ws.compete([candidate("r1", "a" * 64, 1)], workspace_epoch=4)
        broadcast = ws.broadcast(selection, ["ZECP14"])
        reentry = ws.reenter(broadcast, target_process_id="ZECP14", observed_downstream_change="TRUE")
        self.assertTrue(reentry["delivery_observed"])
        self.assertFalse(reentry["causal_use_proven"])
        self.assertEqual(0, reentry["global_jspace_causal_credit"])
        self.assertEqual(4, reentry["from_workspace_epoch"])
        self.assertEqual(5, reentry["to_workspace_epoch"])

    def test_d7_restart_discards_s1_and_rebuild_is_n_invariant(self):
        values = [candidate("r1", "b" * 64, 3), candidate("r2", "a" * 64, 3)]
        first = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=1)
        s1 = first.compete(values, workspace_epoch=8)
        b1 = first.broadcast(s1, ["ZECP03"])
        first.reenter(b1, target_process_id="ZECP03")
        self.assertEqual({"selections": 1, "broadcasts": 1, "reentries": 1}, first.s1_counts())
        first.discard_s1()
        self.assertEqual({"selections": 0, "broadcasts": 0, "reentries": 0}, first.s1_counts())

        restarted = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=20)
        s2 = restarted.compete(values, workspace_epoch=8)
        self.assertEqual(s1["selection_id"], s2["selection_id"])
        self.assertFalse(restarted.direct_s0_commit_allowed())
        self.assertFalse(restarted.direct_real_effect_allowed())
        self.assertFalse(restarted.capability_broadening_allowed())

    def test_d8_unknown_is_preserved_and_not_collapsed_to_false(self):
        ws = GlobalWorkspaceFixture(causal_event_id="event-1", generation=7, requested_n=10)
        selection = ws.compete([candidate("r1", "a" * 64, 1, uncertainty="UNKNOWN")], workspace_epoch=1)
        broadcast = ws.broadcast(selection, ["ZECP03"])
        reentry = ws.reenter(broadcast, target_process_id="ZECP03")
        self.assertEqual("UNKNOWN", reentry["observed_downstream_change"])
        self.assertNotEqual("FALSE", reentry["observed_downstream_change"])


if __name__ == "__main__":
    unittest.main()
