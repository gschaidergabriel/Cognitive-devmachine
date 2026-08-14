from __future__ import annotations

import unittest
import semantic_pulse_effectivizer_s2 as m
from semantic_access_pulse_v12 import AccessPath, PulsePlan, SegmentedPulseProjection


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

    def test_effectivizes_chain_but_preserves_net_zero_identity_touch(self):
        events = (
            self.event("e1", 1, 2, "A", "a0", "a1", ("s1", "s2")),
            self.event("e2", 2, 3, "A", "a1", "a0", ("s1", "s2")),
            self.event("e3", 3, 4, "B", "b0", "b1", ("s2", "s3")),
        )
        plan = m.effectivize_pulse_batch("batch-1", events)
        self.assertEqual(plan.changed_logical_ids, ("A", "B"))
        self.assertEqual(plan.cancelled_logical_ids, ("A",))
        self.assertEqual(plan.impact_seed_ids, ("s1", "s2", "s3"))
        self.assertEqual(plan.raw_event_count, 3)
        self.assertEqual(plan.effective_change_count, 1)
        self.assertFalse(plan.metadata_only_epoch_advance_required)
        self.assertEqual(plan.authority, m.AUTHORITY)

    def test_fully_content_cancelled_batch_remains_publishable_identity_touch(self):
        plan = m.effectivize_pulse_batch(
            "batch-cancel",
            (
                self.event("e1", 1, 2, "A", "a0", "a1"),
                self.event("e2", 2, 3, "A", "a1", "a0"),
            ),
        )
        self.assertFalse(plan.metadata_only_epoch_advance_required)
        self.assertEqual(plan.changed_logical_ids, ("A",))
        self.assertEqual(plan.cancelled_logical_ids, ("A",))
        self.assertEqual(plan.impact_seed_ids, ("s1",))
        adapted = m.to_spm_s1_plan(plan)
        self.assertEqual(adapted.changed_logical_ids, ("A",))
        self.assertEqual(adapted.impact_seed_ids, ("s1",))
        self.assertEqual(adapted.to_source_epoch, 3)

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

    def test_content_aba_matches_sequential_spm_versioned_record_identity(self):
        """A->B->A content is not a no-op when SPM target_record_id versions advance."""
        seeds = ("seed:A", "seed:B")

        def make_projection(versions):
            projection = SegmentedPulseProjection()

            def paths_for(seed):
                logical = f"logical:{seed}"
                v = versions[seed]
                return [
                    AccessPath(
                        target_record_id=f"rec:{seed}:v{v}",
                        target_logical_id=logical,
                        path_rank=1,
                        hop_count=0,
                        path_weight=1.0 + v / 1000,
                        dependencies=(seed, logical),
                    )
                ]

            projection.bootstrap(
                event_id="boot",
                source_epoch=1,
                graph_epoch=1,
                seeds=seeds,
                recompute_seed=paths_for,
            )
            return projection, paths_for

        # Exact sequential baseline: A changes version twice and returns to the same
        # content fingerprint; B then changes once.
        seq_versions = {"seed:A": 0, "seed:B": 0}
        sequential, seq_paths = make_projection(seq_versions)
        seq_versions["seed:A"] = 1
        sequential.apply_pulse(
            PulsePlan("e1", "VALUE_UPDATE", ("logical:seed:A",), ("seed:A",), True, 2, 1),
            recompute_seed=seq_paths,
            recompute_all_seeds=lambda: seeds,
        )
        seq_versions["seed:A"] = 2
        sequential.apply_pulse(
            PulsePlan("e2", "VALUE_UPDATE", ("logical:seed:A",), ("seed:A",), True, 3, 1),
            recompute_seed=seq_paths,
            recompute_all_seeds=lambda: seeds,
        )
        seq_versions["seed:B"] = 1
        sequential.apply_pulse(
            PulsePlan("e3", "VALUE_UPDATE", ("logical:seed:B",), ("seed:B",), True, 4, 1),
            recompute_seed=seq_paths,
            recompute_all_seeds=lambda: seeds,
        )

        # One read-free batched publication from the same initial state. The content
        # fingerprint of A is net-zero, but final target_record_id is rec:seed:A:v2.
        batch_versions = {"seed:A": 0, "seed:B": 0}
        batched, batch_paths = make_projection(batch_versions)
        batch_versions.update({"seed:A": 2, "seed:B": 1})
        plan = m.effectivize_pulse_batch(
            "batch",
            (
                self.event("e1", 1, 2, "logical:seed:A", "a0", "a1", ("seed:A",)),
                self.event("e2", 2, 3, "logical:seed:A", "a1", "a0", ("seed:A",)),
                self.event("e3", 3, 4, "logical:seed:B", "b0", "b1", ("seed:B",)),
            ),
        )
        batched.apply_pulse(
            m.to_spm_s1_plan(plan),
            recompute_seed=batch_paths,
            recompute_all_seeds=lambda: seeds,
        )

        self.assertEqual(sequential.snapshot(), batched.snapshot())
        self.assertIn("rec:seed:A:v2", batched.query("seed:A"))
        self.assertIn("rec:seed:B:v1", batched.query("seed:B"))
        sequential.close()
        batched.close()

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
