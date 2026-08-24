import sqlite3
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path

from model_execution_admission_store_v1 import (
    ModelExecutionAdmissionStoreError,
    admit_and_verify_model_execution,
)
from model_execution_receipt_v1 import model_execution_observation_sha256
from test_model_execution_receipt_v1 import digest, grid_plan, observation, verified_load


def open_db(path: Path, generation: int = 7) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=5.0, check_same_thread=False)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute(
        "CREATE TABLE IF NOT EXISTS entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
    )
    row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    if row is None:
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    db.commit()
    return db


class ModelExecutionAdmissionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "miniunified.db"

    def tearDown(self):
        self.tempdir.cleanup()

    def test_exact_invocation_is_persisted_before_verified_execution_returns(self):
        db = open_db(self.db_path)
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)
        verified = admit_and_verify_model_execution(
            db, plan, load, obs, current_generation=plan.entity_generation
        )
        self.assertEqual(verified.invocation_id, obs.invocation_id)
        self.assertEqual(verified.output_sha256, obs.output_sha256)
        self.assertEqual(
            db.execute("SELECT COUNT(*) FROM hcu_model_execution_observations").fetchone()[0],
            1,
        )
        self.assertEqual(
            db.execute("SELECT COUNT(*) FROM hcu_model_execution_invocations").fetchone()[0],
            1,
        )
        db.close()

    def test_exact_replay_is_idempotent(self):
        db = open_db(self.db_path)
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)
        first = admit_and_verify_model_execution(
            db, plan, load, obs, current_generation=plan.entity_generation
        )
        second = admit_and_verify_model_execution(
            db, plan, load, obs, current_generation=plan.entity_generation
        )
        self.assertEqual(first.receipt_sha256, second.receipt_sha256)
        self.assertEqual(
            db.execute("SELECT COUNT(*) FROM hcu_model_execution_observations").fetchone()[0],
            1,
        )
        self.assertEqual(
            db.execute("SELECT COUNT(*) FROM hcu_model_execution_invocations").fetchone()[0],
            1,
        )
        db.close()

    def test_exact_replay_after_connection_reopen_is_idempotent(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)

        db = open_db(self.db_path)
        first = admit_and_verify_model_execution(
            db, plan, load, obs, current_generation=plan.entity_generation
        )
        db.close()

        reopened = open_db(self.db_path)
        second = admit_and_verify_model_execution(
            reopened, plan, load, obs, current_generation=plan.entity_generation
        )
        self.assertEqual(first.receipt_sha256, second.receipt_sha256)
        self.assertEqual(
            reopened.execute("SELECT COUNT(*) FROM hcu_model_execution_observations").fetchone()[0],
            1,
        )
        self.assertEqual(
            reopened.execute("SELECT COUNT(*) FROM hcu_model_execution_invocations").fetchone()[0],
            1,
        )
        reopened.close()

    def test_same_invocation_with_different_output_rolls_back_without_rebinding(self):
        db = open_db(self.db_path)
        plan = grid_plan()
        load = verified_load(plan)
        original = observation(plan, load)
        divergent = replace(original, output_sha256=digest("divergent-output"))
        admit_and_verify_model_execution(
            db, plan, load, original, current_generation=plan.entity_generation
        )
        with self.assertRaisesRegex(
            ModelExecutionAdmissionStoreError,
            "MODEL_EXECUTION_INVOCATION_REPLAY_DIVERGENCE",
        ):
            admit_and_verify_model_execution(
                db, plan, load, divergent, current_generation=plan.entity_generation
            )
        row = db.execute(
            "SELECT observation_sha256 FROM hcu_model_execution_invocations"
        ).fetchone()
        self.assertEqual(row[0], model_execution_observation_sha256(original))
        self.assertEqual(
            db.execute("SELECT COUNT(*) FROM hcu_model_execution_observations").fetchone()[0],
            1,
        )
        db.close()

    def test_stale_generation_fails_before_observation_or_invocation_write(self):
        db = open_db(self.db_path, generation=8)
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)
        with self.assertRaisesRegex(
            ModelExecutionAdmissionStoreError,
            "STALE_MODEL_EXECUTION_ADMISSION_GENERATION",
        ):
            admit_and_verify_model_execution(
                db, plan, load, obs, current_generation=plan.entity_generation
            )
        tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        self.assertNotIn("hcu_model_execution_observations", tables)
        self.assertNotIn("hcu_model_execution_invocations", tables)
        db.close()

    def test_concurrent_divergent_same_invocation_has_exactly_one_winner(self):
        bootstrap = open_db(self.db_path)
        bootstrap.close()
        plan = grid_plan()
        load = verified_load(plan)
        original = observation(plan, load)
        divergent = replace(original, output_sha256=digest("concurrent-divergent-output"))
        barrier = threading.Barrier(2)
        outcomes = []
        lock = threading.Lock()

        def worker(obs):
            db = open_db(self.db_path)
            barrier.wait()
            try:
                verified = admit_and_verify_model_execution(
                    db, plan, load, obs, current_generation=plan.entity_generation
                )
                result = ("PASS", verified.output_sha256)
            except ModelExecutionAdmissionStoreError as exc:
                result = ("REJECT", str(exc))
            finally:
                db.close()
            with lock:
                outcomes.append(result)

        threads = [
            threading.Thread(target=worker, args=(original,)),
            threading.Thread(target=worker, args=(divergent,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(sum(1 for status, _ in outcomes if status == "PASS"), 1)
        self.assertEqual(sum(1 for status, _ in outcomes if status == "REJECT"), 1)
        self.assertTrue(
            any(
                "MODEL_EXECUTION_INVOCATION_REPLAY_DIVERGENCE" in detail
                for status, detail in outcomes
                if status == "REJECT"
            )
        )


if __name__ == "__main__":
    unittest.main()
