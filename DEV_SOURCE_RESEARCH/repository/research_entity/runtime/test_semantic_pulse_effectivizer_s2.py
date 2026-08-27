from __future__ import annotations

import unittest
import semantic_pulse_effectivizer_s2 as m


class PulseEffectivizerS2Tests(unittest.TestCase):
    def event(self, eid, fs, ts, logical, before, after, seeds=("s1",), **kw):
        return m.PulseDeltaEvent(
            event_id=eid,
            change_class=kw.pop("change_class", "VALUE_UPDATE"),
            from_source_epoch=fs,
            to_source_epoch=ts,
            from_graph_epoch=kw.pop("from_graph_epoch", 1),
            to_graph_epoch=kw.pop("to_graph_epoch", 1),
            changed_logical_id=logical,
            before_fingerprint=before,
            after_fingerprint=after,
            impact_seed_ids=tuple(seeds),
            **kw,
        )

    def test_effectivizes_chain_and_cancels_net_zero_entity(self):
        events = (
            self.event("e1", 1, 2, "A", "a0", "a1", ("s1", "s2")),
            self.event("e2", 2, 3, "A", "a1", "a0", ("s1", "s2")),
            self.event("e3", 3, 4, "B", "b0", "b1", ("s2", "s3")),
        )
        plan = m.effectivize_pulse_batch("batch-1", events)
        self.assertEqual(plan.changed_logical_ids, ("B",))
        self.assertEqual(plan.cancelled_logical_ids, ("A",))
        self.assertEqual(plan.impact_seed_ids, ("s2", "s3"))
        self.assertEqual(plan.raw_event_count, 3)
        self.assertEqual(plan.effective_change_count, 1)
        self.assertFalse(plan.metadata_only_epoch_advance_required)
        self.assertEqual(plan.authority, m.AUTHORITY)

    def test_fully_cancelled_batch_surfaces_metadata_only_epoch_gap(self):
        plan = m.effectivize_pulse_batch(
            "batch-cancel",
            (
                self.event("e1", 1, 2, "A", "a0", "a1"),
                self.event("e2", 2, 3, "A", "a1", "a0"),
            ),
        )
        self.assertTrue(plan.metadata_only_epoch_advance_required)
        self.assertEqual(plan.changed_logical_ids, ())
        with self.assertRaisesRegex(m.PulseEffectivizationError, "metadata-only epoch advance"):
            m.to_spm_s1_plan(plan)

    def test_adapter_emits_safe_local_rewrite_plan(self):
        plan = m.effectivize_pulse_batch(
            "batch-live",
            (self.event("e1", 1, 2, "A", "a0", "a1", ("s1", "s2")),),
        )
        adapted = m.to_spm_s1_plan(plan)
        self.assertEqual(adapted.event_id, "batch-live")
        self.assertEqual(adapted.change_class, "LOCAL_REWRITE")
        self.assertEqual(adapted.changed_logical_ids, ("A",))
        self.assertEqual(adapted.impact_seed_ids, ("s1", "s2"))
        self.assertEqual(adapted.to_source_epoch, 2)

    def test_rejects_fingerprint_discontinuity(self):
        with self.assertRaisesRegex(m.PulseEffectivizationError, "fingerprint lineage"):
            m.effectivize_pulse_batch(
                "bad",
                (
                    self.event("e1", 1, 2, "A", "a0", "a1"),
                    self.event("e2", 2, 3, "A", "WRONG", "a2"),
                ),
            )

    def test_rejects_noncontiguous_epochs(self):
        with self.assertRaisesRegex(m.PulseEffectivizationError, "source epochs"):
            m.effectivize_pulse_batch(
                "bad",
                (
                    self.event("e1", 1, 2, "A", "a0", "a1"),
                    self.event("e2", 3, 4, "B", "b0", "b1"),
                ),
            )

    def test_rejects_observation_boundary(self):
        with self.assertRaisesRegex(m.PulseEffectivizationError, "sequential publication"):
            m.effectivize_pulse_batch(
                "bad",
                (self.event("e1", 1, 2, "A", "a0", "a1", intermediate_observation_required=True),),
            )

    def test_rejects_unsafe_change_class(self):
        with self.assertRaisesRegex(m.PulseEffectivizationError, "change class"):
            m.effectivize_pulse_batch(
                "bad",
                (self.event("e1", 1, 2, "A", "a0", "a1", change_class="DELETE_WORLD"),),
            )

    def test_duplicate_event_id_rejected(self):
        with self.assertRaisesRegex(m.PulseEffectivizationError, "unique"):
            m.effectivize_pulse_batch(
                "bad",
                (
                    self.event("e1", 1, 2, "A", "a0", "a1"),
                    self.event("e1", 2, 3, "B", "b0", "b1"),
                ),
            )


if __name__ == "__main__":
    unittest.main()
