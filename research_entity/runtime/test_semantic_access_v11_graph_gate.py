#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from semantic_access_generation_builder_v11 import Path as AccessPath
from semantic_access_generation_builder_v11 import publish_generation, stage_generation, verify_generation

HERE = Path(__file__).resolve().parent


class U11ClayGraphVerificationGateTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(':memory:')
        for name in (
            'RAE_CLAYGRAPH_SCHEMA.sql',
            'RAE_CLAYGRAPH_V4_VERIFIED_ACCESS_PLANS.sql',
            'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql',
            'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql',
            'RAE_UNIFIEDDB_V11B_GRAPH_PLAN_BINDINGS.sql',
        ):
            self.con.executescript((HERE / name).read_text(encoding='utf-8'))
        self.con.execute(
            "INSERT INTO graph_epochs(graph_epoch,source_epoch,reason,created_at,status) VALUES(9,7,'test','t','CURRENT')"
        )
        self.con.execute(
            "INSERT INTO semantic_query_seeds VALUES('sv','s','shared semantic state','seed-logical','ALIAS',1.0,'{}',7,9,'CURRENT','t','t')"
        )
        self.con.commit()

    def tearDown(self):
        self.con.close()

    def add_plan(
        self,
        *,
        plan_id='p1',
        target='target-a',
        status='VERIFIED',
        passed=1,
        invalid=0,
        stale=0,
        missing_counter=0,
        topology='topo-1',
    ):
        self.con.execute(
            """INSERT INTO graph_semantic_access_plans(
                 plan_id,seed_id,source_epoch,graph_epoch,planner_id,planner_hash,topology_hash,max_hops,
                 candidate_path_count,selected_path_count,counterevidence_path_count,verification_clay,
                 status,created_at,verified_at
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (plan_id,'s',7,9,'planner','planner-h',topology,2,1,1,0,'{}',status,'t','t'),
        )
        self.con.execute(
            """INSERT INTO graph_semantic_access_plan_paths(
                 plan_id,path_id,target_logical_id,path_rank,hop_count,relation_signature,path_weight,
                 admissibility_clay,provenance_clay,counterevidence
               ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (plan_id,f'path-{plan_id}',target,1,1,'REL',1.0,'{}','{}',0),
        )
        self.con.execute(
            """INSERT INTO graph_access_plan_verification_receipts(
                 receipt_id,plan_id,graph_epoch,topology_hash,checked_path_count,invalid_path_count,
                 stale_reference_count,missing_counterevidence_count,verification_clay,passed,created_at
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (f'receipt-{plan_id}',plan_id,9,topology,1,invalid,stale,missing_counter,'{}',passed,'t'),
        )
        self.con.commit()

    @staticmethod
    def path(record='record-a', target='target-a'):
        return AccessPath('s', record, target, 1, 1, 1.0, 0.0, '{}')

    def stage(self, generation='g1', *, paths=None, plan_ids=('p1',)):
        return stage_generation(
            self.con,
            generation_id=generation,
            source_epoch=7,
            graph_epoch=9,
            derivation_id='derivation',
            derivation_hash=f'h-{generation}',
            paths=list(paths or [self.path()]),
            created_at='t',
            verified_plan_ids=plan_ids,
        )

    def test_integrated_graph_requires_explicit_verified_plan_ids(self):
        self.add_plan()
        with self.assertRaisesRegex(ValueError, 'verified_plan_ids required'):
            self.stage(plan_ids=())
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)

    def test_clean_verified_plan_is_bound_verified_and_published(self):
        self.add_plan()
        staged = self.stage()
        self.assertTrue(staged['graph_plan_gate_enforced'])
        self.assertEqual(staged['bound_plan_count'], 1)
        binding = self.con.execute(
            "SELECT plan_id,verification_receipt_id,seed_id,source_epoch,graph_epoch,topology_hash "
            "FROM semantic_access_generation_plan_bindings WHERE generation_id='g1'"
        ).fetchone()
        self.assertEqual(tuple(binding), ('p1','receipt-p1','s',7,9,'topo-1'))
        verify_generation(self.con, 'g1', verification_clay='{}', verified_at='t')
        published = publish_generation(self.con, 'g1', published_at='t2')
        self.assertTrue(published['published'])
        self.assertEqual(self.con.execute("SELECT generation_id FROM semantic_access_head").fetchone()[0], 'g1')

    def test_generation_path_not_covered_by_verified_plan_is_rejected(self):
        self.add_plan(target='target-a')
        with self.assertRaisesRegex(ValueError, 'not covered'):
            self.stage(paths=[self.path(target='target-injected')])
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)

    def test_unclean_verification_receipt_is_rejected(self):
        self.add_plan(stale=1)
        with self.assertRaisesRegex(ValueError, 'lacks a clean passed verification receipt'):
            self.stage()
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)

    def test_plan_drift_after_stage_quarantines_at_verify(self):
        self.add_plan()
        self.stage()
        self.con.execute("UPDATE graph_semantic_access_plans SET status='SUPERSEDED' WHERE plan_id='p1'")
        self.con.commit()
        with self.assertRaisesRegex(ValueError, 'stale or no longer VERIFIED'):
            verify_generation(self.con, 'g1', verification_clay='{}', verified_at='t')
        self.assertEqual(
            self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g1'").fetchone()[0],
            'QUARANTINED',
        )

    def test_graph_epoch_drift_after_verify_blocks_publish_and_preserves_lkg(self):
        self.add_plan(plan_id='p1')
        self.stage('g1', plan_ids=('p1',))
        verify_generation(self.con, 'g1', verification_clay='{}', verified_at='t')
        publish_generation(self.con, 'g1', published_at='t1')

        self.add_plan(plan_id='p2')
        self.stage('g2', paths=[self.path(record='record-b')], plan_ids=('p2',))
        verify_generation(self.con, 'g2', verification_clay='{}', verified_at='t')

        self.con.execute("UPDATE graph_epochs SET status='SUPERSEDED' WHERE graph_epoch=9")
        self.con.commit()
        with self.assertRaisesRegex(ValueError, 'graph epoch became stale'):
            publish_generation(self.con, 'g2', published_at='t2')

        self.assertEqual(self.con.execute("SELECT generation_id FROM semantic_access_head").fetchone()[0], 'g1')
        self.assertEqual(
            self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g2'").fetchone()[0],
            'QUARANTINED',
        )
        self.assertEqual(
            self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g1'").fetchone()[0],
            'CURRENT',
        )

    def test_open_foreign_transaction_fails_closed(self):
        self.add_plan()
        self.con.execute("UPDATE semantic_query_seeds SET confidence=0.9 WHERE seed_id='s'")
        with self.assertRaisesRegex(ValueError, 'clean transaction boundary'):
            self.stage()
        self.con.rollback()
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
