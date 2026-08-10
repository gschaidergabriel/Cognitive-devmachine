from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "research_entity" / "runtime" / "RAE_UNIFIEDDB_V16_LIVE_FUSION_RECEIPTS.sql"


class LiveFusionReceiptsV16Test(unittest.TestCase):
    def connect(self, path: str = ":memory:") -> sqlite3.Connection:
        db = sqlite3.connect(path)
        db.executescript(MIGRATION.read_text(encoding="utf-8"))
        return db

    @staticmethod
    def event(db: sqlite3.Connection, content_hash: str = "event-hash") -> None:
        db.execute(
            """INSERT OR IGNORE INTO clay_live_fusion_events
               (source,event_id,content_hash,semantic_epoch,work_spec_rev,kind,payload_ref,evidence_class,created_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            ("urn:clay:test", "evt-1", content_hash, 5, 2, "CONTRADICTS", "git:payload", "RESEARCH_EVIDENCE", "2026-08-10T07:30:00Z"),
        )

    @staticmethod
    def current_projection(db: sqlite3.Connection, branch: str = "harness") -> None:
        db.execute(
            "INSERT INTO clay_live_fusion_branch_projections VALUES(?,?,?,?,?,?)",
            (branch, 5, f"projection-{branch}-5", "CURRENT", 4, "2026-08-10T07:30:00Z"),
        )

    @staticmethod
    def plan(db: sqlite3.Connection, plan_id: str, mode: str, route_epoch: int = 5) -> None:
        db.execute(
            """INSERT INTO clay_live_fusion_route_plans
               (route_plan_id,source,event_id,mode,predicted_affected_fraction,predicted_targeted_cost,
                predicted_dense_cost,predicted_repair_cost,confidence,route_epoch,reason_clay,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (plan_id, "urn:clay:test", "evt-1", mode, 0.2, 1.0, 5.0, 0.5, 0.9, route_epoch, "{}", "2026-08-10T07:30:00Z"),
        )

    def test_event_identity_exact_replay_vs_conflict(self) -> None:
        db = self.connect()
        self.event(db)
        self.event(db)  # exact replay is idempotent with INSERT OR IGNORE
        self.assertEqual(db.execute("SELECT COUNT(*) FROM clay_live_fusion_events").fetchone()[0], 1)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "LIVE_FUSION_IDENTITY_CONFLICT"):
            self.event(db, "different-content-hash")

    def test_targeted_route_requires_exact_current_projection(self) -> None:
        db = self.connect()
        self.event(db)
        self.current_projection(db)
        self.plan(db, "targeted-good", "TARGETED_DELTA")
        db.execute(
            "INSERT INTO clay_live_fusion_route_decisions VALUES(?,?,?,?,?,?,?,?)",
            ("targeted-good", "harness", "CONFLICT_INTERRUPT", "FULL_REF", "NEXT_SAFE_POINT", 5, "projection-harness-5", "2026-08-10T07:30:00Z"),
        )

        self.plan(db, "targeted-stale", "TARGETED_DELTA", 6)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "LIVE_FUSION_STALE_OR_INCOMPLETE_PROJECTION"):
            db.execute(
                "INSERT INTO clay_live_fusion_route_decisions VALUES(?,?,?,?,?,?,?,?)",
                ("targeted-stale", "harness", "DIRECT_WORK", "FULL_REF", "NEXT_CHECKPOINT", 6, "wrong", "2026-08-10T07:30:01Z"),
            )

    def test_dense_fanout_remains_fail_broad_fallback(self) -> None:
        db = self.connect()
        self.event(db)
        self.plan(db, "dense", "DENSE_FANOUT", 6)
        db.execute(
            "INSERT INTO clay_live_fusion_route_decisions VALUES(?,?,?,?,?,?,?,?)",
            ("dense", "frank", "DENSE_FANOUT", "FULL_REF", "NEXT_SAFE_POINT", None, None, "2026-08-10T07:30:00Z"),
        )
        self.assertEqual(db.execute("SELECT COUNT(*) FROM clay_live_fusion_route_decisions").fetchone()[0], 1)

    def test_receipt_chain_rejects_gap_and_reaches_reentry(self) -> None:
        db = self.connect()
        self.event(db)
        self.current_projection(db)
        self.plan(db, "p1", "TARGETED_DELTA")
        db.execute(
            "INSERT INTO clay_live_fusion_route_decisions VALUES(?,?,?,?,?,?,?,?)",
            ("p1", "harness", "CONFLICT_INTERRUPT", "FULL_REF", "NEXT_SAFE_POINT", 5, "projection-harness-5", "2026-08-10T07:30:00Z"),
        )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "LIVE_FUSION_RECEIPT_STAGE_GAP_OR_REGRESSION"):
            db.execute(
                "INSERT INTO clay_live_fusion_receipt_events VALUES(?,?,?,?,?,?,?,?,?)",
                ("urn:clay:test", "evt-1", "harness", 2, "p1", "r2", None, "RESEARCH_EVIDENCE", "2026-08-10T07:30:00Z"),
            )
        for stage in range(1, 8):
            db.execute(
                "INSERT INTO clay_live_fusion_receipt_events VALUES(?,?,?,?,?,?,?,?,?)",
                ("urn:clay:test", "evt-1", "harness", stage, "p1", f"r{stage}", None, "RESEARCH_EVIDENCE", f"2026-08-10T07:30:0{stage}Z"),
            )
        self.assertEqual(
            db.execute("SELECT stage,stage_name FROM v_clay_live_fusion_current_receipt_stage").fetchone(),
            (7, "REENTRY"),
        )
        db.execute(
            "INSERT OR IGNORE INTO clay_live_fusion_receipt_events VALUES(?,?,?,?,?,?,?,?,?)",
            ("urn:clay:test", "evt-1", "harness", 3, "p1", "r3", None, "RESEARCH_EVIDENCE", "2026-08-10T07:31:00Z"),
        )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "LIVE_FUSION_RECEIPT_IDENTITY_CONFLICT"):
            db.execute(
                "INSERT OR IGNORE INTO clay_live_fusion_receipt_events VALUES(?,?,?,?,?,?,?,?,?)",
                ("urn:clay:test", "evt-1", "harness", 3, "p1", "changed-r3", None, "RESEARCH_EVIDENCE", "2026-08-10T07:31:01Z"),
            )

    def test_restart_continues_receipt_chain(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "live-fusion.sqlite")
            db = self.connect(path)
            self.event(db)
            self.current_projection(db)
            self.plan(db, "restart", "TARGETED_DELTA")
            db.execute(
                "INSERT INTO clay_live_fusion_route_decisions VALUES(?,?,?,?,?,?,?,?)",
                ("restart", "harness", "DIRECT_WORK", "FULL_REF", "NEXT_CHECKPOINT", 5, "projection-harness-5", "2026-08-10T07:30:00Z"),
            )
            for stage in range(1, 5):
                db.execute(
                    "INSERT INTO clay_live_fusion_receipt_events VALUES(?,?,?,?,?,?,?,?,?)",
                    ("urn:clay:test", "evt-1", "harness", stage, "restart", f"restart-r{stage}", None, "RESEARCH_EVIDENCE", f"2026-08-10T07:30:0{stage}Z"),
                )
            db.commit()
            db.close()

            db = self.connect(path)
            for stage in range(5, 8):
                db.execute(
                    "INSERT INTO clay_live_fusion_receipt_events VALUES(?,?,?,?,?,?,?,?,?)",
                    ("urn:clay:test", "evt-1", "harness", stage, "restart", f"restart-r{stage}", None, "RESEARCH_EVIDENCE", f"2026-08-10T07:30:0{stage}Z"),
                )
            db.commit()
            self.assertEqual(
                db.execute("SELECT stage_name FROM v_clay_live_fusion_current_receipt_stage").fetchone()[0],
                "REENTRY",
            )
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_anti_entropy_latest_state_is_observable(self) -> None:
        db = self.connect()
        db.execute(
            "INSERT INTO clay_live_fusion_anti_entropy_checkpoints VALUES(?,?,?,?,?,?,?,?)",
            ("claycode", 5, "local-4", "source-5", "d5", "GAP", '["delta-x"]', "2026-08-10T07:30:00Z"),
        )
        db.execute(
            "INSERT INTO clay_live_fusion_anti_entropy_checkpoints VALUES(?,?,?,?,?,?,?,?)",
            ("claycode", 6, "local-6", "source-6", "d6", "REPAIRED", '[]', "2026-08-10T07:31:00Z"),
        )
        self.assertEqual(
            db.execute("SELECT checkpoint_epoch,state FROM v_clay_live_fusion_latest_anti_entropy WHERE branch='claycode'").fetchone(),
            (6, "REPAIRED"),
        )


if __name__ == "__main__":
    unittest.main()
