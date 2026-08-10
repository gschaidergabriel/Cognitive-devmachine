from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class ClayGraphV4SemanticAccessHeadTests(unittest.TestCase):
    def make_db(self):
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        for name in (
            'RAE_CLAYGRAPH_SCHEMA.sql',
            'RAE_CLAYGRAPH_V3_SEMANTIC_ACCESS_PATHS.sql',
            'RAE_CLAYGRAPH_V4_SEMANTIC_ACCESS_HEADS.sql',
        ):
            conn.executescript((HERE / name).read_text(encoding='utf-8'))
        conn.execute(
            "INSERT INTO graph_epochs(graph_epoch,source_epoch,reason,created_at,status) VALUES(1,1,'seed','2026-08-10T00:00:00Z','SUPERSEDED')"
        )
        conn.execute(
            "INSERT INTO graph_epochs(graph_epoch,source_epoch,reason,created_at,status) VALUES(2,2,'update','2026-08-10T00:01:00Z','CURRENT')"
        )
        return conn

    @staticmethod
    def insert_path(conn, *, version, seed, target, epoch, status, rank=1, weight=1.0):
        conn.execute(
            """
            INSERT INTO graph_semantic_access_paths(
              access_path_version_id,seed_id,seed_logical_id,target_logical_id,
              graph_epoch,source_epoch,path_rank,hop_count,path_weight,relation_signature,
              provenance_clay,admissibility_clay,derivation_hash,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                version,seed,seed,target,epoch,epoch,rank,1,weight,'rel','{}','{}',
                f'h-{version}',status,'2026-08-10T00:00:00Z'
            ),
        )

    def test_newer_quarantine_cannot_resurrect_old_current_path(self):
        c = self.make_db()
        self.insert_path(c, version='v1', seed='s', target='t', epoch=1, status='CURRENT')
        self.insert_path(c, version='v2', seed='s', target='t', epoch=2, status='QUARANTINED')

        # Documents the V3 bug: status is filtered before MAX(epoch), reviving epoch 1.
        buggy = c.execute(
            "SELECT graph_epoch FROM v_current_graph_semantic_access_paths WHERE seed_id='s' AND target_logical_id='t'"
        ).fetchall()
        self.assertEqual([int(r[0]) for r in buggy], [1])

        strict = c.execute(
            "SELECT graph_epoch FROM v_current_graph_semantic_access_paths_strict WHERE seed_id='s' AND target_logical_id='t'"
        ).fetchall()
        fast = c.execute(
            "SELECT graph_epoch FROM v_current_graph_semantic_access_paths_fast WHERE seed_id='s' AND target_logical_id='t'"
        ).fetchall()
        self.assertEqual(strict, [])
        self.assertEqual(fast, [])
        c.close()

    def test_fast_projection_matches_strict_latest_version_semantics(self):
        c = self.make_db()
        self.insert_path(c, version='a1', seed='s', target='a', epoch=1, status='CURRENT', rank=2, weight=.4)
        self.insert_path(c, version='b1', seed='s', target='b', epoch=1, status='CURRENT', rank=3, weight=.3)
        self.insert_path(c, version='a2', seed='s', target='a', epoch=2, status='CURRENT', rank=1, weight=.9)
        self.insert_path(c, version='b2', seed='s', target='b', epoch=2, status='SUPERSEDED', rank=3, weight=.3)

        columns = 'seed_id,target_logical_id,graph_epoch,path_rank,path_weight,derivation_hash'
        strict = [tuple(r) for r in c.execute(
            f"SELECT {columns} FROM v_current_graph_semantic_access_paths_strict ORDER BY seed_id,path_rank,target_logical_id"
        )]
        fast = [tuple(r) for r in c.execute(
            "SELECT seed_id,target_logical_id,graph_epoch,path_rank,path_weight,derivation_hash "
            "FROM v_current_graph_semantic_access_paths_fast ORDER BY seed_id,path_rank,target_logical_id"
        )]
        self.assertEqual(strict, fast)
        self.assertEqual(strict, [('s', 'a', 2, 1, .9, 'h-a2')])
        c.close()

    def test_same_epoch_multiple_versions_block_promotion(self):
        c = self.make_db()
        self.insert_path(c, version='a', seed='s', target='t', epoch=2, status='CURRENT')
        self.insert_path(c, version='b', seed='s', target='t', epoch=2, status='QUARANTINED')
        rows = c.execute(
            "SELECT seed_id,target_logical_id,graph_epoch,version_count FROM v_graph_semantic_access_ambiguous_epochs"
        ).fetchall()
        self.assertEqual([tuple(r) for r in rows], [('s', 't', 2, 2)])
        c.close()


if __name__ == '__main__':
    unittest.main()
