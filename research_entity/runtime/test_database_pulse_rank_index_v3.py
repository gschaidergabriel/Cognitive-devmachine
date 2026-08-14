from __future__ import annotations

import sqlite3
import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.database_pulse_rank_index_v3 import AuthoritativeRankIndexV3, INDEX_NAME


def seed_many(n: int = 180) -> StateLedger:
    ledger = StateLedger()
    ops = []
    for i in range(n):
        ops.append({
            "op":"SET","domain":"memory","key":f"k{i:04d}",
            "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN","status":"CURRENT",
        })
    ops.extend([
        {"op":"SET","domain":"memory","key":"zzzz-critical",
         "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
         "epistemic":"KNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"unknown","value":{"priority":1.0},
         "epistemic":"UNKNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"conflict","value":{"priority":1.0},
         "epistemic":"CONFLICT","status":"CURRENT"},
    ])
    ledger.append_event(
        event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="RANK_INDEX_TEST_SEED",
        writer="test",ops=ops,committed_at="2026-08-10T01:10:00Z",
    )
    return ledger


class AuthoritativeRankIndexV3Tests(unittest.TestCase):
    def test_repairs_lexicographic_prelimit_without_second_projection_table(self):
        ledger=seed_many()
        try:
            legacy=UnifiedDBQueryPlane(ledger).query(QuerySpec(
                query_id="legacy",domains=("memory",),statuses=("CURRENT",),
                epistemic=("KNOWN","UNKNOWN","CONFLICT"),limit=64,basis_epoch=ledger.epoch,purpose="FALSIFIER",
            ))
            self.assertNotIn("zzzz-critical",[r["key"] for r in legacy.rows])
            root_before=(ledger.epoch,ledger.semantic_state_hash,ledger.trace_root_hash)
            rank=AuthoritativeRankIndexV3(ledger)
            got=rank.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=64,max_focus=1)
            self.assertEqual(got.focus_refs,("memory:zzzz-critical",))
            self.assertTrue(got.query_truncated)
            self.assertEqual(got.candidate_universe_count,181)
            self.assertEqual(got.unknown_present,1)
            self.assertEqual(got.conflicts_present,1)
            self.assertTrue(any(INDEX_NAME in p for p in got.query_plan),got.query_plan)
            self.assertEqual(root_before,(ledger.epoch,ledger.semantic_state_hash,ledger.trace_root_hash))
            tables={r[0] for r in ledger.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertNotIn("pulse_active_field",tables)
            self.assertTrue(rank.verify_index_semantics(domains=("memory",))["pass"])
        finally:
            ledger.close()

    def test_index_implements_python_signal_type_and_clamp_semantics(self):
        ledger=StateLedger()
        try:
            ledger.append_event(
                event_id="types",idem="types",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"numeric",
                     "value":{"priority":2.0,"urgency":-2.0,"salience":0.5,"novelty":0.25},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"bools",
                     "value":{"priority":True,"urgency":False},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"strings",
                     "value":{"priority":"1.0"},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"scalar","value":5,"epistemic":"KNOWN","status":"CURRENT"},
                ],committed_at="2026-08-10T01:10:00Z",
            )
            rank=AuthoritativeRankIndexV3(ledger)
            got=rank.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=4,max_focus=4)
            scores=dict(zip(got.candidate_refs,got.candidate_scores))
            self.assertAlmostEqual(scores["memory:numeric"],1.4+0.2*0.5+0.15*0.25,7)
            self.assertEqual(scores["memory:bools"],1.0)
            self.assertEqual(scores["memory:strings"],1.0)
            self.assertEqual(scores["memory:scalar"],1.0)
            self.assertTrue(rank.verify_index_semantics(domains=("memory",))["pass"])
        finally:
            ledger.close()

    def test_state_update_automatically_updates_rank_inside_authoritative_transaction(self):
        ledger=seed_many(8)
        try:
            rank=AuthoritativeRankIndexV3(ledger)
            before=rank.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=8,max_focus=2)
            self.assertEqual(before.focus_refs[0],"memory:zzzz-critical")
            ledger.append_event(
                event_id="promote",idem="promote",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[{"op":"SET","domain":"memory","key":"000-new-critical",
                      "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                      "epistemic":"KNOWN","status":"CURRENT"}],
                committed_at="2026-08-10T01:10:01Z",
            )
            after=rank.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=8,max_focus=2)
            self.assertEqual(after.focus_refs[:2],("memory:000-new-critical","memory:zzzz-critical"))
            self.assertTrue(rank.verify_index_semantics(domains=("memory",))["pass"])
        finally:
            ledger.close()

    def test_retraction_automatically_removes_candidate(self):
        ledger=seed_many(8)
        try:
            rank=AuthoritativeRankIndexV3(ledger)
            rank.ensure_index()
            ledger.append_event(
                event_id="retract",idem="retract",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[{"op":"RETRACT","domain":"memory","key":"zzzz-critical","value":None,
                      "epistemic":"KNOWN","status":"CURRENT"}],committed_at="2026-08-10T01:10:01Z",
            )
            after=rank.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=8,max_focus=1)
            self.assertNotIn("memory:zzzz-critical",after.candidate_refs)
        finally:
            ledger.close()

    def test_truthful_reentry_reserves_previous_candidate_before_final_budget(self):
        ledger=StateLedger()
        try:
            ledger.append_event(
                event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"challenger","value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT"},
                ],committed_at="2026-08-10T01:10:00Z",
            )
            rank=AuthoritativeRankIndexV3(ledger)
            no=rank.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=1,max_focus=1)
            truthful=rank.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=1,max_focus=1,
                                 reentry_mode="TRUTHFUL",previous_focus_refs=("memory:previous",))
            self.assertEqual(no.focus_refs,("memory:challenger",))
            self.assertEqual(truthful.focus_refs,("memory:previous",))
        finally:
            ledger.close()

    def test_direct_malformed_json_tamper_fails_closed(self):
        ledger=seed_many(3)
        try:
            rank=AuthoritativeRankIndexV3(ledger)
            rank.ensure_index()
            with self.assertRaises(sqlite3.DatabaseError):
                ledger.conn.execute("UPDATE state SET value_json='{' WHERE domain='memory' AND k='k0000'")
        finally:
            ledger.close()


if __name__=='__main__':
    unittest.main(verbosity=2)
