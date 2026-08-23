from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from miniunifieddb_cognition_store_v1 import (  # noqa: E402
    CognitionStoreFault,
    bind_object,
    install_schema,
    put_object,
    read_binding,
)

HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64


class CognitionStoreV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute(
            "CREATE TABLE entity_state("
            "id INTEGER PRIMARY KEY CHECK(id=1),"
            "generation INTEGER NOT NULL,"
            "active_profile TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)"
        )
        self.db.execute(
            "INSERT INTO entity_state(id,generation,active_profile,created_at,updated_at) "
            "VALUES(1,7,NULL,'t0','t0')"
        )
        self.db.commit()
        install_schema(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def _put(self, *, generation: int = 7) -> str:
        return put_object(
            self.db,
            object_kind="ZERO_IDENTITY",
            schema_version="ZERO_IDENTITY/v1",
            payload={"identity": "zero", "mode": "runtime_configuration"},
            provenance={"source": "MiniUnifiedDB", "source_digest": HEX_A},
            generation=generation,
            causal_id="causal-7",
            created_at="2026-08-23T08:11:00Z",
        )

    def _bind(self, digest: str, *, generation: int = 7) -> None:
        bind_object(
            self.db,
            binding_name="zero.identity.current",
            object_digest=digest,
            generation=generation,
            semantic_class="RUNTIME_CONFIGURATION",
            causal_id=f"causal-{generation}",
            receipt_digest=HEX_B,
            status="ACTIVE",
            bound_at="2026-08-23T08:11:01Z",
            workspace_digest=HEX_C,
        )

    def test_same_miniunifieddb_generation_round_trip(self) -> None:
        digest = self._put()
        self._bind(digest)
        row = read_binding(
            self.db,
            binding_name="zero.identity.current",
            expected_generation=7,
        )
        self.assertEqual(row["object_digest"], digest)
        self.assertEqual(row["entity_generation"], 7)
        self.assertEqual(row["binding_truth_authority"], 0)
        self.assertEqual(row["binding_effect_authority"], 0)
        self.assertEqual(row["object_truth_authority"], 0)
        self.assertEqual(row["object_effect_authority"], 0)

    def test_stale_generation_rebind_poison_fails_closed(self) -> None:
        """Unusual falsifier candidate: keep valid bytes but stale the generation."""
        digest = self._put()
        self.db.execute("UPDATE entity_state SET generation=8,updated_at='t1' WHERE id=1")
        self.db.commit()
        with self.assertRaisesRegex(CognitionStoreFault, "COGNITION_BINDING_STALE_GENERATION"):
            self._bind(digest, generation=7)
        count = self.db.execute("SELECT COUNT(*) FROM cognition_bindings").fetchone()[0]
        self.assertEqual(count, 0)

    def test_append_only_binding_allows_next_generation_not_mutation(self) -> None:
        digest = self._put()
        self._bind(digest)
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute(
                "UPDATE cognition_bindings SET status='RETIRED' "
                "WHERE binding_name='zero.identity.current' AND entity_generation=7"
            )
        self.db.rollback()

        self.db.execute("UPDATE entity_state SET generation=8,updated_at='t1' WHERE id=1")
        self.db.commit()
        self._bind(digest, generation=8)
        rows = self.db.execute(
            "SELECT entity_generation FROM cognition_bindings "
            "WHERE binding_name='zero.identity.current' ORDER BY entity_generation"
        ).fetchall()
        self.assertEqual(rows, [(7,), (8,)])

    def test_cognition_object_is_immutable(self) -> None:
        digest = self._put()
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute(
                "UPDATE cognition_objects SET object_kind='GRF' WHERE object_digest=?",
                (digest,),
            )
        self.db.rollback()
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute("DELETE FROM cognition_objects WHERE object_digest=?", (digest,))
        self.db.rollback()

    def test_nonfinite_payload_never_becomes_canonical_object(self) -> None:
        with self.assertRaisesRegex(CognitionStoreFault, "COGNITION_NON_CANONICAL_JSON"):
            put_object(
                self.db,
                object_kind="JSPACE_MEASUREMENT",
                schema_version="JSPACE_MEASUREMENT/v1",
                payload={"score": float("inf")},
                provenance={"source": "lens", "source_digest": HEX_A},
                generation=7,
                causal_id="causal-7",
                created_at="2026-08-23T08:11:00Z",
            )
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM cognition_objects").fetchone()[0],
            0,
        )

    def test_direct_authority_escalation_is_rejected_by_schema(self) -> None:
        digest = self._put()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                """
                INSERT INTO cognition_bindings(
                  binding_name,entity_generation,object_digest,semantic_class,causal_id,
                  receipt_digest,status,bound_at,truth_authority,effect_authority
                ) VALUES(?,?,?,?,?,?,?, ?,1,0)
                """,
                (
                    "poison.truth",
                    7,
                    digest,
                    "CANDIDATE",
                    "causal-7",
                    HEX_B,
                    "CANDIDATE",
                    "2026-08-23T08:11:02Z",
                ),
            )
        self.db.rollback()

    def test_profile_identity_is_all_or_nothing(self) -> None:
        digest = self._put()
        with self.assertRaisesRegex(CognitionStoreFault, "COGNITION_PROFILE_BINDING_INCOMPLETE"):
            bind_object(
                self.db,
                binding_name="ucf.profile.current",
                object_digest=digest,
                generation=7,
                semantic_class="RUNTIME_CONFIGURATION",
                causal_id="causal-7",
                receipt_digest=HEX_B,
                status="ACTIVE",
                bound_at="2026-08-23T08:11:01Z",
                profile_id="zero_blog",
                profile_sha256=None,
            )


if __name__ == "__main__":
    unittest.main()
