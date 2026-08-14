from __future__ import annotations

import sqlite3
import unittest

from research_entity.runtime.claygraph_relation_conditioned_access_v6 import (
    ClayGraphRelationConditionedAccessV6,
)


SCHEMA = """
CREATE TABLE graph_head_edges(
  logical_edge_id TEXT PRIMARY KEY,
  edge_version_id TEXT NOT NULL UNIQUE,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  source_logical_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  weight REAL NOT NULL,
  confidence REAL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  causal_class TEXT,
  source_status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_graph_head_edges_current_source_weight_v6
  ON graph_head_edges(source_logical_id,weight DESC,target_logical_id,logical_edge_id)
  WHERE source_status='CURRENT';
CREATE INDEX idx_graph_head_edges_current_source_relation_weight_v6
  ON graph_head_edges(source_logical_id,relation_type,weight DESC,target_logical_id,logical_edge_id)
  WHERE source_status='CURRENT';
"""


class RelationConditionedV6Tests(unittest.TestCase):
    def make(self):
        c = sqlite3.connect(":memory:")
        c.executescript(SCHEMA)
        rels = ["REQUIRES", "DEPENDS_ON", "SUPPORTS", "CONTRADICTS", "BLOCKS", "DERIVED_FROM", "SUPERSEDES", "ALTERNATIVE"]
        rows = []
        base = {rel: 1.0 - i * 0.04 for i, rel in enumerate(rels)}
        base["REQUIRES"] = 0.40
        for rel in rels:
            for j in range(32):
                edge_id = f"root:{rel}:{j:02d}"
                rows.append((
                    edge_id, edge_id + ":v1", 4, 7, "root", f"target:{rel}:{j:02d}", rel,
                    base[rel] - j * 0.001, 0.9, "{}", "{}", "ASSOCIATIVE", "CURRENT", "t",
                ))
        rows.append((
            "root:REQUIRES:tomb", "root:REQUIRES:tomb:v2", 5, 8, "root", "target:tomb", "REQUIRES",
            9.0, 1.0, "{}", "{}", "ASSOCIATIVE", "RETIRED", "t",
        ))
        c.executemany("INSERT INTO graph_head_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        c.commit()
        return c, ClayGraphRelationConditionedAccessV6(c)

    def test_typed_relation_retained_with_same_total_budget(self):
        c, access = self.make()
        try:
            global_edges, _ = access.query(source_logical_id="root", total_budget=32)
            self.assertEqual(len(global_edges), 32)
            self.assertFalse(any(e.relation_type == "REQUIRES" for e in global_edges))

            edges, receipt = access.query(
                source_logical_id="root",
                total_budget=32,
                typed_relation="requires",
                typed_relation_confidence=0.99,
                relation_reserve=8,
            )
            self.assertTrue(receipt.relation_admitted)
            self.assertEqual(receipt.typed_relation, "REQUIRES")
            self.assertEqual(len(edges), 32)
            self.assertEqual(receipt.requested_relation_count, 8)
            self.assertEqual(receipt.fallback_count, 24)
            self.assertEqual(sum(e.relation_type == "REQUIRES" for e in edges), 8)
            self.assertEqual(edges[0].target_logical_id, "target:REQUIRES:00")
            self.assertEqual(len(set(receipt.selected_edge_ids)), 32)
        finally:
            c.close()

    def test_low_confidence_relation_falls_back_exactly_to_global(self):
        c, access = self.make()
        try:
            global_edges, _ = access.query(source_logical_id="root", total_budget=32)
            low_edges, receipt = access.query(
                source_logical_id="root",
                total_budget=32,
                typed_relation="REQUIRES",
                typed_relation_confidence=0.30,
                min_relation_confidence=0.75,
                relation_reserve=8,
            )
            self.assertFalse(receipt.relation_admitted)
            self.assertIsNone(receipt.typed_relation)
            self.assertEqual(receipt.relation_reserve, 0)
            self.assertEqual(
                tuple(e.logical_edge_id for e in low_edges),
                tuple(e.logical_edge_id for e in global_edges),
            )
        finally:
            c.close()

    def test_non_current_head_never_reenters(self):
        c, access = self.make()
        try:
            edges, _ = access.query(
                source_logical_id="root", total_budget=32, typed_relation="REQUIRES",
                typed_relation_confidence=1.0, relation_reserve=8
            )
            self.assertNotIn("root:REQUIRES:tomb", {e.logical_edge_id for e in edges})
        finally:
            c.close()

    def test_missing_relation_fills_entire_budget_from_global(self):
        c, access = self.make()
        try:
            edges, receipt = access.query(
                source_logical_id="root", total_budget=32, typed_relation="NO_SUCH_RELATION",
                typed_relation_confidence=1.0, relation_reserve=8
            )
            self.assertEqual(len(edges), 32)
            self.assertTrue(receipt.relation_admitted)
            self.assertEqual(receipt.requested_relation_count, 0)
            self.assertEqual(receipt.fallback_count, 32)
        finally:
            c.close()

    def test_budget_and_confidence_guards(self):
        c, access = self.make()
        try:
            with self.assertRaises(ValueError):
                access.query(source_logical_id="root", total_budget=0)
            with self.assertRaises(ValueError):
                access.query(
                    source_logical_id="root", total_budget=32, typed_relation="REQUIRES",
                    typed_relation_confidence=1.0, relation_reserve=33
                )
            with self.assertRaises(ValueError):
                access.query(
                    source_logical_id="root", total_budget=32, typed_relation="REQUIRES",
                    typed_relation_confidence=1.1
                )
        finally:
            c.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
