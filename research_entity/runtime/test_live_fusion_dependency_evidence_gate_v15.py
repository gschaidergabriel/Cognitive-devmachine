import unittest

from live_fusion_dependency_evidence_gate_v15 import (
    DependencyEvidenceGateV15,
    DependencyWitness,
    ParentRouteObservation,
    INDEX_ONLY,
    NEXT_CHECKPOINT,
    INTERRUPT_NEXT_SAFE_POINT,
)


class DependencyEvidenceGateV15Tests(unittest.TestCase):
    def setUp(self):
        self.gate = DependencyEvidenceGateV15()

    def obs(self, **kw):
        data = dict(
            event_id="evt",
            worker_id="harness",
            base_class=INDEX_ONLY,
            proposed_class=INTERRUPT_NEXT_SAFE_POINT,
            direct_overlap=False,
            dependency_only=True,
            conflict=True,
            impact=0.95,
            urgency=0.90,
            projection_current=True,
            projection_worker_match=True,
            projection_epoch="graph-7",
            projection_state_hash="state-7",
        )
        data.update(kw)
        return ParentRouteObservation(**data)

    def wit(self, witness_class, *, current=True, worker_id="harness"):
        return DependencyWitness(
            worker_id=worker_id,
            scope_id="WP-HIDDEN",
            witness_class=witness_class,
            current=current,
            provenance_refs=("receipt:test",),
        )

    def test_soft_associative_dependency_cannot_mint_interrupt(self):
        row = self.gate.adjudicate(self.obs(), [self.wit("ASSOCIATIVE_ONLY")])
        self.assertEqual(row.gated_class, NEXT_CHECKPOINT)
        self.assertTrue(row.verification_required)
        self.assertEqual(row.change, "BLOCKING_DOWNGRADED_PENDING_EVIDENCE")

    def test_verified_causal_dependency_can_retain_interrupt(self):
        row = self.gate.adjudicate(self.obs(), [self.wit("VERIFIED_CAUSAL")])
        self.assertEqual(row.gated_class, INTERRUPT_NEXT_SAFE_POINT)
        self.assertFalse(row.verification_required)

    def test_declared_work_dependency_can_retain_interrupt(self):
        row = self.gate.adjudicate(self.obs(), [self.wit("DECLARED_WORK_DEPENDENCY")])
        self.assertEqual(row.gated_class, INTERRUPT_NEXT_SAFE_POINT)

    def test_stale_hard_witness_does_not_retain_interrupt(self):
        row = self.gate.adjudicate(self.obs(), [self.wit("VERIFIED_CAUSAL", current=False)])
        self.assertEqual(row.gated_class, NEXT_CHECKPOINT)
        self.assertTrue(row.verification_required)
        self.assertEqual(row.stale_witness_count, 1)

    def test_stale_projection_rejects_dependency_upgrade(self):
        row = self.gate.adjudicate(
            self.obs(projection_current=False), [self.wit("VERIFIED_CAUSAL")]
        )
        self.assertEqual(row.gated_class, INDEX_ONLY)
        self.assertTrue(row.verification_required)
        self.assertFalse(row.projection_accepted)

    def test_direct_parent_interrupt_is_not_weakened(self):
        row = self.gate.adjudicate(
            self.obs(
                base_class=INTERRUPT_NEXT_SAFE_POINT,
                proposed_class=INTERRUPT_NEXT_SAFE_POINT,
                direct_overlap=True,
                dependency_only=False,
            ),
            [],
        )
        self.assertEqual(row.gated_class, INTERRUPT_NEXT_SAFE_POINT)
        self.assertFalse(row.verification_required)

    def test_worker_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "worker mismatch"):
            self.gate.adjudicate(self.obs(), [self.wit("VERIFIED_CAUSAL", worker_id="other")])

    def test_dependency_checkpoint_stays_nonblocking_and_requests_verification(self):
        row = self.gate.adjudicate(
            self.obs(proposed_class=NEXT_CHECKPOINT, conflict=False, impact=0.4, urgency=0.3),
            [self.wit("HEURISTIC")],
        )
        self.assertEqual(row.gated_class, NEXT_CHECKPOINT)
        self.assertTrue(row.verification_required)

    def test_out_of_box_false_edge_lesion_rescue(self):
        # Deliberately unusual experiment: inject a plausible but false associative edge,
        # then rescue only by adding an independently verified causal witness.
        poisoned = self.gate.adjudicate(self.obs(event_id="oob"), [self.wit("ASSOCIATIVE_ONLY")])
        rescued = self.gate.adjudicate(
            self.obs(event_id="oob"),
            [self.wit("ASSOCIATIVE_ONLY"), self.wit("REPLAY_CONFIRMED")],
        )
        self.assertEqual(poisoned.gated_class, NEXT_CHECKPOINT)
        self.assertEqual(rescued.gated_class, INTERRUPT_NEXT_SAFE_POINT)
        self.assertTrue(poisoned.verification_required)
        self.assertFalse(rescued.verification_required)

    def test_summary_observability(self):
        rows = [
            self.gate.adjudicate(self.obs(event_id="a"), [self.wit("ASSOCIATIVE_ONLY")]),
            self.gate.adjudicate(self.obs(event_id="b"), [self.wit("VERIFIED_CAUSAL")]),
        ]
        s = self.gate.summarize(rows)
        self.assertEqual(s["rows"], 2)
        self.assertEqual(s["blocking_downgrades"], 1)
        self.assertEqual(s["verification_required"], 1)
        self.assertEqual(s["interrupts_after_gate"], 1)


if __name__ == "__main__":
    unittest.main()
