import sqlite3
import unittest

from verified_claygraph_ranker import (
    AmbiguousGraphProjection,
    StaleGraphProjection,
    VerifiedClayGraphRanker,
)


class VerifiedClayGraphRankerTests(unittest.TestCase):
    def make(self, *, ambiguous=False, verified=True, current_graph_epoch=3, future_head=False):
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        db.executescript('''
          CREATE TABLE graph_epochs(graph_epoch INTEGER,source_epoch INTEGER,status TEXT);
          CREATE TABLE graph_head_edges(logical_edge_id TEXT,graph_epoch INTEGER);
          CREATE TABLE graph_current_projection_receipts(
            graph_epoch INTEGER,source_epoch INTEGER,verified_equal INTEGER,created_at TEXT
          );
          CREATE TABLE amb(logical_edge_id TEXT,graph_epoch INTEGER,version_count INTEGER);
          CREATE VIEW v_graph_projection_ambiguous_edge_epochs AS SELECT * FROM amb;
          CREATE TABLE heads(
            logical_edge_id TEXT,source_logical_id TEXT,target_logical_id TEXT,
            relation_type TEXT,weight REAL,confidence REAL,graph_epoch INTEGER
          );
          CREATE VIEW v_graph_current_edges_fast AS SELECT * FROM heads;
        ''')
        db.execute("INSERT INTO graph_epochs VALUES(?,?, 'CURRENT')", (current_graph_epoch, 7))
        if ambiguous:
            db.execute("INSERT INTO amb VALUES('amb',?,2)", (current_graph_epoch,))
        if verified:
            db.execute(
                "INSERT INTO graph_current_projection_receipts VALUES(?,?,1,'z')",
                (current_graph_epoch, 7),
            )
        if future_head:
            db.execute("INSERT INTO graph_head_edges VALUES('future',?)", (current_graph_epoch + 1,))
        return db

    @staticmethod
    def add_edge(db, edge, source, target, relation, weight=1.0, confidence=1.0, epoch=3):
        db.execute('INSERT INTO graph_head_edges VALUES(?,?)', (edge, epoch))
        db.execute(
            'INSERT INTO heads VALUES(?,?,?,?,?,?,?)',
            (edge, source, target, relation, weight, confidence, epoch),
        )

    @staticmethod
    def ranker(db, *, conflict=()):
        text = {
            'anchor': 'Needle chooses route but does not commit effects',
            'gateway': 'Effect gateway commits verified external effects with authority',
            'memory': 'Memory stores episodic context and retrieval state',
            'reverse': 'Backward alternative route',
        }
        blocked = set(conflict)
        return VerifiedClayGraphRanker(
            db,
            text_for_ref=lambda ref, epoch: text.get(ref, ''),
            admissible_ref=lambda ref, epoch: ref not in blocked,
        )

    def test_residual_query_terms_rank_correct_neighbor(self):
        db = self.make()
        self.add_edge(db, 'e1', 'anchor', 'memory', 'routes_to')
        self.add_edge(db, 'e2', 'anchor', 'gateway', 'routes_to')
        got = self.ranker(db).rank(
            'anchor', 'after route which component commits external effects', 7, 3, 5
        )
        self.assertEqual(got[0].ref, 'gateway')
        db.close()

    def test_path_receipt_is_explicit(self):
        db = self.make()
        self.add_edge(db, 'e1', 'anchor', 'gateway', 'routes_to')
        got = self.ranker(db).rank('anchor', 'which gateway commits effect', 7, 3, 5)[0]
        self.assertEqual(
            (got.anchor_ref, got.relation_type, got.ref, got.direction),
            ('anchor', 'routes_to', 'gateway', 'FORWARD'),
        )
        self.assertEqual(got.edge_ref, 'claygraph:e1@3')
        self.assertEqual(got.authority, 'ASSEMBLY_CONTEXT_ONLY')
        db.close()

    def test_admissibility_callback_blocks_conflict(self):
        db = self.make()
        self.add_edge(db, 'e1', 'anchor', 'gateway', 'routes_to')
        self.assertEqual(
            self.ranker(db, conflict=('gateway',)).refs(
                'anchor', 'gateway effect commit', 7, 3, 5
            ),
            (),
        )
        db.close()

    def test_same_epoch_ambiguity_fails_closed(self):
        db = self.make(ambiguous=True)
        with self.assertRaises(AmbiguousGraphProjection):
            self.ranker(db).refs('anchor', 'anything', 7, 3, 5)
        db.close()

    def test_missing_verified_projection_receipt_fails_closed(self):
        db = self.make(verified=False)
        with self.assertRaises(StaleGraphProjection):
            self.ranker(db).refs('anchor', 'anything', 7, 3, 5)
        db.close()

    def test_stale_graph_epoch_fails_closed(self):
        db = self.make(current_graph_epoch=4)
        with self.assertRaises(StaleGraphProjection):
            self.ranker(db).refs('anchor', 'anything', 7, 3, 5)
        db.close()

    def test_future_head_beyond_receipt_fails_closed(self):
        db = self.make(future_head=True)
        with self.assertRaises(StaleGraphProjection):
            self.ranker(db).refs('anchor', 'anything', 7, 3, 5)
        db.close()

    def test_reverse_edge_is_available_but_discounted(self):
        db = self.make()
        self.add_edge(db, 'e-forward', 'anchor', 'gateway', 'routes_to')
        self.add_edge(db, 'e-reverse', 'reverse', 'anchor', 'routes_to')
        got = self.ranker(db).rank('anchor', 'route target', 7, 3, 5)
        by_ref = {x.ref: x for x in got}
        self.assertEqual(by_ref['reverse'].direction, 'REVERSE')
        self.assertGreater(by_ref['gateway'].score, by_ref['reverse'].score)
        db.close()


if __name__ == '__main__':
    unittest.main()
