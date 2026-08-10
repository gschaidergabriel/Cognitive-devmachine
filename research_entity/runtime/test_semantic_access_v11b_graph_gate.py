#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from semantic_access_generation_builder_v11 import Path as AccessPath
from semantic_access_generation_builder_v11 import SemanticAccessBusyError
from semantic_access_generation_builder_v11 import publish_generation, stage_generation, verify_generation

HERE = Path(__file__).resolve().parent
SCHEMAS = (
    'RAE_CLAYGRAPH_SCHEMA.sql',
    'RAE_CLAYGRAPH_V4_VERIFIED_ACCESS_PLANS.sql',
    'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql',
    'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql',
    'RAE_UNIFIEDDB_V11B_GRAPH_PLAN_BINDINGS.sql',
)


class U11BClayGraphGateTests(unittest.TestCase):
    @staticmethod
    def install(con: sqlite3.Connection) -> None:
        for name in SCHEMAS:
            con.executescript((HERE / name).read_text(encoding='utf-8'))
        con.execute(
            "INSERT INTO graph_epochs(graph_epoch,source_epoch,reason,created_at,status) VALUES(9,7,'test','t','CURRENT')"
        )
        con.execute(
            "INSERT INTO semantic_query_seeds VALUES('sv','s','shared semantic state','seed-logical','ALIAS',1.0,'{}',7,9,'CURRENT','t','t')"
        )
        con.commit()

    def setUp(self):
        self.con = sqlite3.connect(':memory:')
        self.install(self.con)

    def tearDown(self):
        self.con.close()

    @staticmethod
    def add_plan_to(con: sqlite3.Connection, *, plan_id='p1', target='target-a', topology='topo-1') -> None:
        con.execute(
            """INSERT INTO graph_semantic_access_plans(
                 plan_id,seed_id,source_epoch,graph_epoch,planner_id,planner_hash,topology_hash,max_hops,
                 candidate_path_count,selected_path_count,counterevidence_path_count,verification_clay,
                 status,created_at,verified_at
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (plan_id,'s',7,9,'planner','planner-h',topology,2,1,1,0,'{}','VERIFIED','t','t'),
        )
        con.execute(
            """INSERT INTO graph_semantic_access_plan_paths(
                 plan_id,path_id,target_logical_id,path_rank,hop_count,relation_signature,path_weight,
                 admissibility_clay,provenance_clay,counterevidence
               ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (plan_id,f'path-{plan_id}',target,1,1,'REL',1.0,'{}','{}',0),
        )
        con.execute(
            """INSERT INTO graph_access_plan_verification_receipts(
                 receipt_id,plan_id,graph_epoch,topology_hash,checked_path_count,invalid_path_count,
                 stale_reference_count,missing_counterevidence_count,verification_clay,passed,created_at
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (f'receipt-{plan_id}-1',plan_id,9,topology,1,0,0,0,'{}',1,'t1'),
        )
        con.commit()

    def add_plan(self, **kwargs) -> None:
        self.add_plan_to(self.con, **kwargs)

    @staticmethod
    def path(record='record-a', target='target-a') -> AccessPath:
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

    def test_explicit_verified_plan_ids_are_required(self):
        self.add_plan()
        with self.assertRaisesRegex(ValueError, 'verified_plan_ids required'):
            self.stage(plan_ids=())
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)

    def test_clean_latest_receipt_binds_verifies_and_publishes(self):
        self.add_plan()
        staged = self.stage()
        self.assertTrue(staged['graph_plan_gate_enforced'])
        binding = self.con.execute(
            "SELECT plan_id,verification_receipt_id,length(plan_paths_hash) "
            "FROM semantic_access_generation_plan_bindings WHERE generation_id='g1'"
        ).fetchone()
        self.assertEqual(tuple(binding), ('p1','receipt-p1-1',64))
        verify_generation(self.con, 'g1', verification_clay='{}', verified_at='t')
        publish_generation(self.con, 'g1', published_at='t2')
        self.assertEqual(self.con.execute("SELECT generation_id FROM semantic_access_head").fetchone()[0], 'g1')

    def test_injected_target_not_covered_by_plan_is_rejected(self):
        self.add_plan()
        with self.assertRaisesRegex(ValueError, 'not covered'):
            self.stage(paths=[self.path(target='target-injected')])
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)

    def test_newest_failed_receipt_invalidates_older_good_receipt(self):
        self.add_plan()
        self.con.execute(
            """INSERT INTO graph_access_plan_verification_receipts VALUES(
               'receipt-p1-2','p1',9,'topo-1',1,1,0,0,'{}',0,'t2')"""
        )
        self.con.commit()
        with self.assertRaisesRegex(ValueError, 'latest receipt.*not clean'):
            self.stage()
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)

    def test_plan_path_mutation_after_stage_quarantines_at_verify(self):
        self.add_plan()
        self.stage()
        self.con.execute(
            "UPDATE graph_semantic_access_plan_paths SET relation_signature='MUTATED' WHERE plan_id='p1'"
        )
        self.con.commit()
        with self.assertRaisesRegex(ValueError, 'path content changed'):
            verify_generation(self.con, 'g1', verification_clay='{}', verified_at='t')
        self.assertEqual(
            self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g1'").fetchone()[0],
            'QUARANTINED',
        )

    def test_newer_clean_receipt_after_stage_requires_restage(self):
        self.add_plan()
        self.stage()
        self.con.execute(
            """INSERT INTO graph_access_plan_verification_receipts VALUES(
               'receipt-p1-2','p1',9,'topo-1',1,0,0,0,'{}',1,'t2')"""
        )
        self.con.commit()
        with self.assertRaisesRegex(ValueError, 'newer verification receipt; restage required'):
            verify_generation(self.con, 'g1', verification_clay='{}', verified_at='t')
        self.assertEqual(
            self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g1'").fetchone()[0],
            'QUARANTINED',
        )

    def test_plan_status_drift_after_stage_quarantines(self):
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
        self.assertEqual(self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g2'").fetchone()[0], 'QUARANTINED')
        self.assertEqual(self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g1'").fetchone()[0], 'CURRENT')

    def test_foreign_open_transaction_fails_closed_only_in_integrated_mode(self):
        self.add_plan()
        self.con.execute("UPDATE semantic_query_seeds SET confidence=0.9 WHERE seed_id='s'")
        with self.assertRaisesRegex(ValueError, 'clean transaction boundary'):
            self.stage()
        self.con.rollback()
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)

    def test_competing_writer_returns_busy_before_semantic_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / 'gate.sqlite')
            reader = sqlite3.connect(db, timeout=0.0)
            writer = sqlite3.connect(db, timeout=0.0)
            try:
                self.install(reader)
                self.add_plan_to(reader)
                writer.execute('BEGIN IMMEDIATE')
                writer.execute("UPDATE semantic_query_seeds SET confidence=0.8 WHERE seed_id='s'")
                with self.assertRaisesRegex(SemanticAccessBusyError, 'safe to retry from fresh state'):
                    stage_generation(
                        reader,
                        generation_id='g-busy',
                        source_epoch=7,
                        graph_epoch=9,
                        derivation_id='d',
                        derivation_hash='h-busy',
                        paths=[self.path()],
                        created_at='t',
                        verified_plan_ids=('p1',),
                    )
                writer.rollback()
                self.assertEqual(reader.execute("SELECT COUNT(*) FROM semantic_access_generations").fetchone()[0], 0)
            finally:
                if writer.in_transaction:
                    writer.rollback()
                writer.close()
                reader.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
