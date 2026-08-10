from __future__ import annotations

import unittest

from live_fusion_reentry_v13 import (
    DELIVERY_CHECKPOINT,
    DELIVERY_INDEX,
    DELIVERY_INTERRUPT,
    LiveDelta,
    WorkerView,
)
from live_fusion_strong_mesh_v14 import DependencyProjection, StrongMeshShadowRouter


class StrongMeshV14Tests(unittest.TestCase):
    def setUp(self):
        self.router = StrongMeshShadowRouter()

    @staticmethod
    def delta(
        event_id: str,
        *,
        branches=(), keys=(), work=(), claims=(), impact=0.7, urgency=0.5,
        conflict=False, applicability="CURRENT_MATERIAL",
    ):
        return LiveDelta(
            event_id=event_id,
            source="fixture",
            source_seq=1,
            source_epoch="fixture-epoch",
            semantic_keys=tuple(keys),
            affected_branches=tuple(branches),
            novelty="CONTRADICTS" if conflict else "REFINES",
            impact=impact,
            urgency=urgency,
            conflict=conflict,
            payload={"event": event_id},
            applicability=applicability,
            affected_work=tuple(work),
            affected_claims=tuple(claims),
        )

    @staticmethod
    def worker(worker_id="harness", *, branches=("harness",), keys=(), work=(), claims=()):
        return WorkerView(
            worker_id=worker_id,
            branches=tuple(branches),
            active_keys=tuple(keys),
            active_work=tuple(work),
            active_claims=tuple(claims),
            subscription_revision="r14-shadow",
            plan_revision="p1",
        )

    def projection(self, worker_id="harness", *, keys=(), work=(), claims=(), current=True):
        return DependencyProjection(
            worker_id=worker_id,
            graph_epoch="graph-42",
            state_hash="state-42",
            semantic_keys=tuple(keys),
            work_ids=tuple(work),
            claim_ids=tuple(claims),
            provenance_refs=("claygraph:graph-42",),
            current=current,
        )

    def test_direct_work_route_remains_active(self):
        d = self.delta("direct-work", work=("WP-9",), impact=0.5, urgency=0.3)
        w = self.worker(work=("WP-9",))
        row = self.router.plan(d, w)
        self.assertNotEqual(row.base_class, DELIVERY_INDEX)
        self.assertEqual(row.candidate_class, DELIVERY_CHECKPOINT)

    def test_low_signal_branch_only_noise_is_shadow_demoted(self):
        d = self.delta("branch-noise", branches=("harness",), impact=0.1, urgency=0.1)
        w = self.worker()
        row = self.router.plan(d, w)
        self.assertEqual(row.base_class, DELIVERY_CHECKPOINT)
        self.assertEqual(row.candidate_class, DELIVERY_INDEX)
        self.assertEqual(row.change, "DEMOTED_LOW_SIGNAL")

    def test_high_impact_branch_only_signal_stays_active(self):
        d = self.delta("branch-important", branches=("harness",), impact=0.9, urgency=0.8)
        w = self.worker()
        row = self.router.plan(d, w)
        self.assertEqual(row.candidate_class, DELIVERY_CHECKPOINT)

    def test_dependency_claim_rescues_cross_branch_route(self):
        d = self.delta("hidden-claim", claims=("CLAIM-X",), impact=0.8, urgency=0.6)
        w = self.worker()
        p = self.projection(claims=("CLAIM-X",))
        row = self.router.plan(d, w, p)
        self.assertEqual(row.base_class, DELIVERY_INDEX)
        self.assertEqual(row.candidate_class, DELIVERY_CHECKPOINT)
        self.assertEqual(row.change, "UPGRADED_DEPENDENCY_REACH")

    def test_false_current_dependency_is_contained_to_shadow_plane(self):
        # Strongest counterhypothesis control: a current but wrong graph edge can create a
        # candidate false positive. V1.4 containment keeps V1.3 live routing unchanged.
        d = self.delta("false-edge", claims=("CLAIM-WRONG",), impact=0.9, urgency=0.8, conflict=True)
        w = self.worker()
        row = self.router.plan(d, w, self.projection(claims=("CLAIM-WRONG",)))
        self.assertEqual(row.base_class, DELIVERY_INDEX)
        self.assertEqual(row.candidate_class, DELIVERY_INTERRUPT)
        self.assertEqual(row.authority, "SHADOW_ROUTING_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY")

    def test_stale_projection_cannot_upgrade(self):
        d = self.delta("stale-hidden", work=("WP-X",), impact=0.9, urgency=0.8, conflict=True)
        w = self.worker()
        p = self.projection(work=("WP-X",), current=False)
        row = self.router.plan(d, w, p)
        self.assertEqual(row.base_class, DELIVERY_INDEX)
        self.assertEqual(row.candidate_class, DELIVERY_INDEX)
        self.assertFalse(row.projection_used)

    def test_projection_worker_mismatch_fails_closed(self):
        d = self.delta("mismatch", keys=("x",))
        w = self.worker()
        with self.assertRaisesRegex(ValueError, "worker mismatch"):
            self.router.plan(d, w, self.projection(worker_id="other", keys=("x",)))

    def test_historical_event_never_upgrades_live_plan(self):
        d = self.delta("history", work=("WP-X",), impact=1.0, urgency=1.0, conflict=True,
                       applicability="HISTORICALLY_VALID_ONLY")
        w = self.worker()
        row = self.router.plan(d, w, self.projection(work=("WP-X",)))
        self.assertEqual(row.candidate_class, DELIVERY_INDEX)

    def test_high_impact_hidden_dependency_can_shadow_interrupt(self):
        d = self.delta("hidden-blocker", keys=("pulse-aba",), impact=0.95, urgency=0.9, conflict=True)
        w = self.worker()
        row = self.router.plan(d, w, self.projection(keys=("pulse-aba",)))
        self.assertEqual(row.base_class, DELIVERY_INDEX)
        self.assertEqual(row.candidate_class, DELIVERY_INTERRUPT)

    def test_summary_is_observable(self):
        w = self.worker()
        rows = [
            self.router.plan(self.delta("noise", branches=("harness",), impact=0.1, urgency=0.1), w),
            self.router.plan(self.delta("hidden", work=("WP-Z",), impact=0.8, urgency=0.6), w,
                             self.projection(work=("WP-Z",))),
        ]
        summary = self.router.summarize(rows)
        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["demoted_low_signal"], 1)
        self.assertEqual(summary["upgraded_dependency_reach"], 1)

    def test_out_of_box_hidden_dependency_lesion_rescue(self):
        """GO OOB experiment: lesion all direct topology, then rescue only via a derived dependency edge."""
        d = self.delta("oob-lesion-rescue", work=("WP-HIDDEN",), impact=0.95, urgency=0.9, conflict=True)
        w = self.worker(branches=("harness",), keys=(), work=(), claims=())

        lesioned = self.router.plan(d, w, None)
        self.assertEqual(lesioned.base_class, DELIVERY_INDEX)
        self.assertEqual(lesioned.candidate_class, DELIVERY_INDEX)

        rescued = self.router.plan(d, w, self.projection(work=("WP-HIDDEN",)))
        self.assertEqual(rescued.base_class, DELIVERY_INDEX)
        self.assertEqual(rescued.candidate_class, DELIVERY_INTERRUPT)
        self.assertEqual(rescued.change, "UPGRADED_DEPENDENCY_REACH")


if __name__ == "__main__":
    unittest.main()
