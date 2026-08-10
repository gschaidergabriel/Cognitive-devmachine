from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from semantic_retrieval_runtime_v10 import SemanticRetrievalFabric

ROOT = Path(__file__).resolve().parents[2]
U10 = ROOT / "research_entity" / "runtime" / "RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql"
U11 = ROOT / "research_entity" / "runtime" / "RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql"


class SemanticRetrievalV11Tests(unittest.TestCase):
    def make(self) -> sqlite3.Connection:
        con = sqlite3.connect(":memory:")
        con.executescript(U10.read_text(encoding="utf-8"))
        con.executescript(U11.read_text(encoding="utf-8"))
        con.execute(
            "INSERT INTO semantic_query_seeds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "sv1",
                "seed:gwt",
                "gwt causal receipts",
                "topic:gwt-causal-receipts",
                "CANONICAL",
                1.0,
                '{"source":"test"}',
                7,
                11,
                "CURRENT",
                "2026-08-10T00:00:00Z",
                "2026-08-10T00:00:00Z",
            ),
        )
        return con

    @staticmethod
    def stage_generation(con: sqlite3.Connection, generation: str, *, status: str, refs: list[str]) -> None:
        con.execute(
            "INSERT INTO semantic_access_generations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                generation,
                7,
                11,
                "possibility-field-v1",
                f"hash:{generation}",
                1,
                len(refs),
                '{"complete":true,"tests":"passed"}',
                status,
                "2026-08-10T00:00:00Z",
                "2026-08-10T00:00:01Z" if status in {"VERIFIED", "CURRENT"} else None,
                "2026-08-10T00:00:02Z" if status == "CURRENT" else None,
            ),
        )
        for rank, ref in enumerate(refs, 1):
            con.execute(
                "INSERT INTO semantic_access_projection_v11 VALUES(?,?,?,?,?,?,?,?,?)",
                (generation, "seed:gwt", ref, ref, rank, 0, 1.0, 1.0, '{"proof":"test"}'),
            )

    @staticmethod
    def publish(con: sqlite3.Connection, generation: str) -> None:
        row = con.execute(
            "SELECT derivation_hash FROM semantic_access_generations WHERE generation_id=?",
            (generation,),
        ).fetchone()
        assert row is not None
        derivation_hash = row[0]
        with con:
            con.execute(
                "UPDATE semantic_access_generations SET status='SUPERSEDED' WHERE status='CURRENT' AND generation_id<>?",
                (generation,),
            )
            con.execute(
                "UPDATE semantic_access_generations SET status='CURRENT',published_at='2026-08-10T00:00:03Z' WHERE generation_id=?",
                (generation,),
            )
            con.execute(
                """INSERT INTO semantic_access_head VALUES('CURRENT',?,?,?,?,?)
                   ON CONFLICT(head_key) DO UPDATE SET
                     generation_id=excluded.generation_id,
                     source_epoch=excluded.source_epoch,
                     graph_epoch=excluded.graph_epoch,
                     derivation_hash=excluded.derivation_hash,
                     published_at=excluded.published_at""",
                (generation, 7, 11, derivation_hash, "2026-08-10T00:00:03Z"),
            )

    def test_verified_current_generation_is_sufficient_and_not_padded(self):
        con = self.make()
        self.stage_generation(con, "g1", status="CURRENT", refs=["claim:current", "claim:refuted"])
        self.publish(con, "g1")
        fabric = SemanticRetrievalFabric(con)
        result = fabric.query_seed(
            "assemble evidence for gwt causal receipts",
            source_epoch=7,
            graph_epoch=11,
            limit=5,
            lexical_ranking=["noise:1", "noise:2", "noise:3"],
        )
        self.assertEqual(result.mode, "SEMANTIC_GENERATION_SUFFICIENT")
        self.assertTrue(result.sufficient)
        self.assertEqual(result.refs, ("claim:current", "claim:refuted"))
        self.assertEqual(result.generation_id, "g1")
        con.close()

    def test_staging_generation_is_invisible_until_atomic_head_publish(self):
        con = self.make()
        self.stage_generation(con, "g1", status="CURRENT", refs=["claim:old"])
        self.publish(con, "g1")
        self.stage_generation(con, "g2", status="STAGING", refs=["claim:new"])
        fabric = SemanticRetrievalFabric(con)
        before = fabric.query_seed("gwt causal receipts", source_epoch=7, graph_epoch=11, limit=5)
        self.assertEqual(before.refs, ("claim:old",))
        self.assertEqual(before.generation_id, "g1")
        self.publish(con, "g2")
        after = fabric.query_seed("gwt causal receipts", source_epoch=7, graph_epoch=11, limit=5)
        self.assertEqual(after.refs, ("claim:new",))
        self.assertEqual(after.generation_id, "g2")
        con.close()

    def test_stale_epoch_cannot_use_compiled_generation(self):
        con = self.make()
        self.stage_generation(con, "g1", status="CURRENT", refs=["claim:compiled"])
        self.publish(con, "g1")
        fabric = SemanticRetrievalFabric(con)
        result = fabric.query_seed(
            "gwt causal receipts",
            source_epoch=8,
            graph_epoch=11,
            limit=5,
            lexical_ranking=["claim:fallback"],
        )
        self.assertEqual(result.mode, "LEXICAL_FALLBACK")
        self.assertFalse(result.sufficient)
        self.assertEqual(result.refs, ("claim:fallback",))
        con.close()


if __name__ == "__main__":
    unittest.main()
