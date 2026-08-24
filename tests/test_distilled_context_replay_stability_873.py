import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "run_24h_entityos_swarm.py"
spec = importlib.util.spec_from_file_location("entityos_swarm_context_873", MODULE_PATH)
swarm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(swarm)

FORGE_CLASS = "FORGE_EVIDENCE_QUALIFIED_EXECUTION"


def make_db(path: Path, rows: list[dict]) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute(
            """
            CREATE TABLE knowledge_packets(
              id TEXT PRIMARY KEY,
              question_id TEXT NOT NULL,
              packet_text TEXT NOT NULL,
              metadata_json TEXT NOT NULL,
              intrinsic_score REAL NOT NULL,
              grf_score REAL NOT NULL,
              project_fit REAL NOT NULL,
              novelty_score REAL NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        for row in rows:
            con.execute(
                """
                INSERT INTO knowledge_packets(
                  id,question_id,packet_text,metadata_json,
                  intrinsic_score,grf_score,project_fit,novelty_score,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    row["id"],
                    row.get("question_id", "forge-q"),
                    row["packet_text"],
                    json.dumps(row["metadata"], sort_keys=True, separators=(",", ":")),
                    float(row.get("intrinsic_score", 1.0)),
                    float(row.get("grf_score", 0.0)),
                    float(row.get("project_fit", 1.0)),
                    float(row.get("novelty_score", 0.0)),
                    row["created_at"],
                ),
            )
        con.commit()
    finally:
        con.close()


def forge_row(packet_id: str, created_at: str) -> dict:
    replay_sha = ("a" if packet_id.endswith("a") else "b") * 64
    return {
        "id": packet_id,
        "packet_text": json.dumps(
            {
                "schema": "CLAY_DISTILLERY_FORGE_EXECUTION_PACKET/v2",
                "evidence_class": FORGE_CLASS,
                "worker_sha": "c" * 64,
                "metric": "execution_admission_causal_regression_pass_rate",
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        "metadata": {
            "packet_class": FORGE_CLASS,
            "forge_execution_replay_identity_sha256": replay_sha,
            "canonical_truth": False,
            "training_credit": 0,
        },
        "created_at": created_at,
    }


def ordinary_row(packet_id: str, created_at: str) -> dict:
    return {
        "id": packet_id,
        "question_id": "ordinary-q",
        "packet_text": "ordinary research packet",
        "metadata": {"packet_class": "ORDINARY_RESEARCH_PACKET", "canonical_truth": False},
        "created_at": created_at,
    }


def render(db: Path) -> dict:
    old = swarm.DISTILLERY_DB
    try:
        swarm.DISTILLERY_DB = db
        return json.loads(swarm.distilled_context(100_000))
    finally:
        swarm.DISTILLERY_DB = old


class DistilledContextReplayStability873Tests(unittest.TestCase):
    def test_forge_prompt_projection_ignores_ingest_wall_clock_but_db_keeps_provenance(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            first = root_path / "first.sqlite3"
            replay = root_path / "replay.sqlite3"
            make_db(first, [forge_row("kf-forge-a", "2026-08-24T18:00:00+00:00")])
            make_db(replay, [forge_row("kf-forge-a", "2026-08-24T19:00:00+00:00")])

            first_context = render(first)
            replay_context = render(replay)

            self.assertEqual(first_context, replay_context)
            self.assertNotIn("created_at", first_context["packets"][0])

            con = sqlite3.connect(first)
            first_created = con.execute(
                "SELECT created_at FROM knowledge_packets WHERE id='kf-forge-a'"
            ).fetchone()[0]
            con.close()
            con = sqlite3.connect(replay)
            replay_created = con.execute(
                "SELECT created_at FROM knowledge_packets WHERE id='kf-forge-a'"
            ).fetchone()[0]
            con.close()
            self.assertNotEqual(first_created, replay_created)

    def test_equal_score_forge_order_is_stable_when_ingest_times_swap(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            first = root_path / "first.sqlite3"
            replay = root_path / "replay.sqlite3"
            make_db(
                first,
                [
                    forge_row("kf-forge-a", "2026-08-24T18:00:00+00:00"),
                    forge_row("kf-forge-b", "2026-08-24T19:00:00+00:00"),
                ],
            )
            make_db(
                replay,
                [
                    forge_row("kf-forge-a", "2026-08-24T19:00:00+00:00"),
                    forge_row("kf-forge-b", "2026-08-24T18:00:00+00:00"),
                ],
            )

            first_ids = [row["packet_id"] for row in render(first)["packets"]]
            replay_ids = [row["packet_id"] for row in render(replay)["packets"]]
            self.assertEqual(first_ids, replay_ids)
            self.assertEqual(first_ids, sorted(first_ids))

    def test_ordinary_research_packet_keeps_recency_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            db = Path(root) / "ordinary.sqlite3"
            created_at = "2026-08-24T20:00:00+00:00"
            make_db(db, [ordinary_row("kp-ordinary-1", created_at)])
            payload = render(db)
            self.assertEqual(payload["packets"][0]["created_at"], created_at)


if __name__ == "__main__":
    unittest.main()
