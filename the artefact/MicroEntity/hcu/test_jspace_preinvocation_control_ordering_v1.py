#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sqlite3
import unittest

from jspace_preinvocation_control_ordering_v1 import (
    JSpacePreInvocationControlOrderingError,
    admit_preinvocation_control_ordering,
    read_preinvocation_control_ordering,
    validate_preinvocation_control_ordering,
)


def _sha(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _db(generation: int = 7) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)")
    db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    db.execute(
        """CREATE TABLE hcu_model_execution_observations(
          observation_sha256 TEXT PRIMARY KEY,
          observation_jcs BLOB NOT NULL,
          entity_generation INTEGER NOT NULL,
          executor_id TEXT NOT NULL,
          invocation_id TEXT NOT NULL
        )"""
    )
    db.execute(
        """CREATE TABLE hcu_model_execution_invocations(
          invocation_binding_key TEXT PRIMARY KEY,
          executor_id TEXT NOT NULL,
          invocation_id TEXT NOT NULL,
          entity_generation INTEGER NOT NULL,
          observation_sha256 TEXT NOT NULL,
          FOREIGN KEY(observation_sha256)
            REFERENCES hcu_model_execution_observations(observation_sha256)
        )"""
    )
    db.commit()
    return db


def _admit_execution(
    db: sqlite3.Connection,
    *,
    executor_id: str,
    invocation_id: str,
    generation: int = 7,
) -> str:
    observation_sha = _sha(f"obs:{executor_id}:{invocation_id}:{generation}")
    invocation_key = _sha(f"invocation:{executor_id}:{invocation_id}")
    db.execute(
        "INSERT INTO hcu_model_execution_observations "
        "(observation_sha256,observation_jcs,entity_generation,executor_id,invocation_id) "
        "VALUES(?,?,?,?,?)",
        (
            observation_sha,
            f"observation:{executor_id}:{invocation_id}".encode("utf-8"),
            generation,
            executor_id,
            invocation_id,
        ),
    )
    db.execute(
        "INSERT INTO hcu_model_execution_invocations "
        "(invocation_binding_key,executor_id,invocation_id,entity_generation,observation_sha256) "
        "VALUES(?,?,?,?,?)",
        (invocation_key, executor_id, invocation_id, generation, observation_sha),
    )
    db.commit()
    return observation_sha


def _admit_ordering(db: sqlite3.Connection, **overrides):
    args = {
        "current_generation": 7,
        "predecessor_executor_id": "executor-A",
        "predecessor_invocation_id": "invocation-t",
        "predecessor_training_trace_sha256": _sha("trace-t"),
        "vector_control_packet_sha256": _sha("packet-t"),
        "controlled_executor_id": "executor-A",
        "controlled_invocation_id": "invocation-t-plus-1",
        "prepared_input_sha256": _sha("input-t-plus-1"),
        "prepared_input_size": 1024,
    }
    args.update(overrides)
    return admit_preinvocation_control_ordering(db, **args)


class PreInvocationControlOrderingTests(unittest.TestCase):
    def test_positive_predecessor_admitted_controlled_absent(self):
        db = _db()
        predecessor_observation = _admit_execution(
            db,
            executor_id="executor-A",
            invocation_id="invocation-t",
        )
        ordering = _admit_ordering(db)
        validate_preinvocation_control_ordering(ordering)
        self.assertEqual(
            ordering.predecessor_model_execution_observation_sha256,
            predecessor_observation,
        )
        self.assertEqual(
            read_preinvocation_control_ordering(
                db,
                controlled_executor_id="executor-A",
                controlled_invocation_id="invocation-t-plus-1",
            ),
            ordering,
        )

    def test_exact_replay_is_idempotent_only_before_controlled_execution(self):
        db = _db()
        _admit_execution(db, executor_id="executor-A", invocation_id="invocation-t")
        first = _admit_ordering(db)
        second = _admit_ordering(db)
        self.assertEqual(first, second)
        count = db.execute(
            "SELECT COUNT(*) FROM hcu_jspace_preinvocation_control_orderings"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_divergent_replay_for_same_controlled_invocation_fails_closed(self):
        db = _db()
        _admit_execution(db, executor_id="executor-A", invocation_id="invocation-t")
        _admit_ordering(db)
        with self.assertRaisesRegex(
            JSpacePreInvocationControlOrderingError,
            "PREINVOCATION_CONTROL_ORDERING_REPLAY_DIVERGENCE",
        ):
            _admit_ordering(db, vector_control_packet_sha256=_sha("different-packet"))
        count = db.execute(
            "SELECT COUNT(*) FROM hcu_jspace_preinvocation_control_orderings"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_same_step_posthoc_claim_is_rejected(self):
        db = _db()
        _admit_execution(db, executor_id="executor-A", invocation_id="invocation-t")
        _admit_execution(
            db,
            executor_id="executor-A",
            invocation_id="invocation-t-plus-1",
        )
        with self.assertRaisesRegex(
            JSpacePreInvocationControlOrderingError,
            "CONTROLLED_MODEL_EXECUTION_ALREADY_ADMITTED_PREINVOCATION_REQUIRED",
        ):
            _admit_ordering(db)
        table = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='hcu_jspace_preinvocation_control_orderings'"
        ).fetchone()
        self.assertIsNone(table)

    def test_replay_after_controlled_execution_cannot_rewrite_history(self):
        db = _db()
        _admit_execution(db, executor_id="executor-A", invocation_id="invocation-t")
        ordering = _admit_ordering(db)
        _admit_execution(
            db,
            executor_id="executor-A",
            invocation_id="invocation-t-plus-1",
        )
        with self.assertRaisesRegex(
            JSpacePreInvocationControlOrderingError,
            "CONTROLLED_MODEL_EXECUTION_ALREADY_ADMITTED_PREINVOCATION_REQUIRED",
        ):
            _admit_ordering(db)
        self.assertEqual(
            read_preinvocation_control_ordering(
                db,
                controlled_executor_id="executor-A",
                controlled_invocation_id="invocation-t-plus-1",
            ),
            ordering,
        )

    def test_missing_predecessor_fails_closed_without_write(self):
        db = _db()
        with self.assertRaisesRegex(
            JSpacePreInvocationControlOrderingError,
            "PREDECESSOR_MODEL_EXECUTION_NOT_ADMITTED",
        ):
            _admit_ordering(db)
        self.assertFalse(db.in_transaction)

    def test_stale_generation_rolls_back(self):
        db = _db(generation=8)
        _admit_execution(
            db,
            executor_id="executor-A",
            invocation_id="invocation-t",
            generation=8,
        )
        with self.assertRaisesRegex(
            JSpacePreInvocationControlOrderingError,
            "STALE_PREINVOCATION_CONTROL_ORDERING_GENERATION",
        ):
            _admit_ordering(db, current_generation=7)
        self.assertFalse(db.in_transaction)

    def test_predecessor_and_controlled_invocation_must_be_distinct(self):
        db = _db()
        _admit_execution(db, executor_id="executor-A", invocation_id="invocation-t")
        with self.assertRaisesRegex(
            JSpacePreInvocationControlOrderingError,
            "PREDECESSOR_AND_CONTROLLED_INVOCATION_MUST_BE_DISTINCT",
        ):
            _admit_ordering(
                db,
                controlled_executor_id="executor-A",
                controlled_invocation_id="invocation-t",
            )


if __name__ == "__main__":
    unittest.main()
