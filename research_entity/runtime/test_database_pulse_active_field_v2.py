from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.database_pulse_active_field_v2 import PulseActiveFieldV2


class PulseActiveFieldV2Tests(unittest.TestCase):
    def seed_many(self, n: int = 180):
        ledger = StateLedger()
        ops = []
        for i in range(n):
            ops.append({
                "op":"SET", "domain":"memory", "key":f"k{i:04d}",
                "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
                "epistemic":"KNOWN", "status":"CURRENT",
            })
        ops.extend([
            {
                "op":"SET", "domain":"memory", "key":"zzzz-critical",
                "value":{"fact":"critical","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                "epistemic":"KNOWN", "status":"CURRENT",
            },
            {
                "op":"SET", "domain":"memory", "key":"unknown",
                "value":{"fact":"u"}, "epistemic":"UNKNOWN", "status":"CURRENT",
            },
            {
                "op":"SET", "domain":"memory", "key":"conflict",
                "value":{"fact":"c"}, "epistemic":"CONFLICT", "status":"CURRENT",
            },
        ])
        ledger.append_event(
            event_id="seed-many", idem="seed-many", base_epoch=ledger.epoch,
            event_type="ACTIVE_FIELD_TEST_SEED", writer="test", ops=ops,
            committed_at="2026-08-10T00:30:00Z",
        )
        return ledger

    def test_reproduces_v1_lexicographic_truncation_and_repairs_it(self):
        ledger = self.seed_many()
        try:
            legacy = UnifiedDBQueryPlane(ledger).query(QuerySpec(
                query_id="lexical-census", domains=("memory",), statuses=("CURRENT",),
                epistemic=("KNOWN","UNKNOWN","CONFLICT"), limit=64,
                basis_epoch=ledger.epoch, purpose="FALSIFIER",
            ))
            self.assertNotIn("zzzz-critical", [r["key"] for r in legacy.rows])

            active = PulseActiveFieldV2(ledger)
            selected = active.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=64, max_focus=1, reentry_mode="NO_REENTRY", now="select",
            )
            self.assertEqual(selected.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(selected.conflicts_present, 1)
            self.assertEqual(selected.unknown_present, 1)
            self.assertEqual(selected.refresh_mode, "FULL_REBUILD")
            self.assertTrue(active.verify_projection()["pass"])
        finally:
            ledger.close()

    def test_second_refresh_touches_only_new_authoritative_refs(self):
        ledger = self.seed_many(20)
        try:
            active = PulseActiveFieldV2(ledger)
            first = active.refresh(now="initial")
            self.assertEqual(first["mode"], "FULL_REBUILD")
            ledger.append_event(
                event_id="one-change", idem="one-change", base_epoch=ledger.epoch,
                event_type="ACTIVE_FIELD_ONE_CHANGE", writer="test",
                ops=[{
                    "op":"SET", "domain":"memory", "key":"k0000",
                    "value":{"fact":0,"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                    "epistemic":"KNOWN", "status":"CURRENT",
                }], committed_at="2026-08-10T00:30:01Z",
            )
            second = active.refresh(now="delta")
            self.assertEqual(second["mode"], "DELTA_REFRESH")
            self.assertEqual(second["touched_refs"], 1)
            self.assertEqual(second["events_consumed"], 1)
            self.assertTrue(active.verify_projection()["pass"])
        finally:
            ledger.close()

    def test_truthful_reentry_reserve_preserves_candidate_outside_base_cut(self):
        ledger = StateLedger()
        try:
            ledger.append_event(
                event_id="seed", idem="seed", base_epoch=ledger.epoch,
                event_type="TEST", writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"previous",
                     "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"challenger",
                     "value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT"},
                ], committed_at="2026-08-10T00:30:00Z",
            )
            active = PulseActiveFieldV2(ledger)
            no_reentry = active.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=1, max_focus=1, reentry_mode="NO_REENTRY", now="a",
            )
            truthful = active.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=1, max_focus=1, reentry_mode="TRUTHFUL",
                previous_focus_refs=("memory:previous",), now="b",
            )
            self.assertEqual(no_reentry.focus_refs, ("memory:challenger",))
            self.assertEqual(truthful.focus_refs, ("memory:previous",))
            self.assertNotEqual(no_reentry.selection_hash, truthful.selection_hash)
        finally:
            ledger.close()

    def test_retracted_high_salience_ref_disappears_after_delta_refresh(self):
        ledger = self.seed_many(10)
        try:
            active = PulseActiveFieldV2(ledger)
            before = active.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=8, max_focus=1, now="before",
            )
            self.assertEqual(before.focus_refs, ("memory:zzzz-critical",))
            ledger.append_event(
                event_id="retract-critical", idem="retract-critical", base_epoch=ledger.epoch,
                event_type="TEST_RETRACT", writer="test",
                ops=[{
                    "op":"RETRACT", "domain":"memory", "key":"zzzz-critical",
                    "value":None, "epistemic":"KNOWN", "status":"CURRENT",
                }], committed_at="2026-08-10T00:30:02Z",
            )
            after = active.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=8, max_focus=1, now="after",
            )
            self.assertNotIn("memory:zzzz-critical", after.candidate_refs)
            self.assertTrue(active.verify_projection()["pass"])
        finally:
            ledger.close()

    def test_deterministic_replay_produces_same_selection_hash(self):
        ledger = self.seed_many(40)
        events = ledger.export_events()
        ledger.close()
        left = StateLedger.replay(events)
        right = StateLedger.replay(events)
        try:
            a = PulseActiveFieldV2(left).select(
                source_domains=("memory",), basis_epoch=left.epoch,
                max_candidates=16, max_focus=4, now="left",
            )
            b = PulseActiveFieldV2(right).select(
                source_domains=("memory",), basis_epoch=right.epoch,
                max_candidates=16, max_focus=4, now="right",
            )
            self.assertEqual(a.focus_refs, b.focus_refs)
            self.assertEqual(a.candidate_refs, b.candidate_refs)
            self.assertEqual(a.selection_hash, b.selection_hash)
        finally:
            left.close(); right.close()

    def test_projection_is_non_authoritative_and_does_not_change_ledger_root(self):
        ledger = self.seed_many(5)
        try:
            before = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            active = PulseActiveFieldV2(ledger)
            active.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=4, max_focus=2, now="projection",
            )
            after = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            self.assertEqual(before, after)
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
