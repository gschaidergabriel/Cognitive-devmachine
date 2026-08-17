import contextlib
import json
import sqlite3
import time

import pytest

from clayverse.method_memory import MethodMemoryManager, MethodMemoryValidationError


class PromotionDB:
    def __init__(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE durable_memory(
                memory_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                subject TEXT NOT NULL,
                value TEXT NOT NULL,
                source_turn_id TEXT,
                user_id TEXT,
                ts REAL NOT NULL,
                provenance TEXT NOT NULL
            );
            CREATE TABLE workspace_episodes(
                episode_id TEXT PRIMARY KEY
            );
            """
        )
        self._next = 0

    @contextlib.contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    def add_memory(self, kind, subject, value, source_turn_id, user_id, provenance):
        self._next += 1
        memory_id = f"db:m{self._next}"
        self.db.execute(
            "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
            (
                memory_id,
                kind,
                subject,
                value,
                source_turn_id,
                user_id,
                time.time(),
                json.dumps(provenance, sort_keys=True),
            ),
        )
        return memory_id


def candidate_record(**overrides):
    value = {
        "problem_signature": {
            "goal": ["identify causal fault"],
            "constraint_shape": ["partial observability"],
            "evidence_shape": ["competing explanations"],
        },
        "preconditions": ["at least two plausible mechanisms remain"],
        "goal_shape": "separate competing causal mechanisms",
        "method_steps": ["generate alternatives", "derive discriminating predictions", "run cheapest falsifier"],
        "invariants": ["unknown facts remain unknown"],
        "expected_observations": ["one intervention separates predictions"],
        "falsifiers": ["candidate predictions remain indistinguishable"],
        "failure_modes": ["proxy metric is not causally diagnostic"],
        "scope_limits": ["not for settled factual lookup"],
        "source_episode_ids": ["episode:a", "episode:b"],
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "1",
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 0.75,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }
    value.update(overrides)
    return value


def test_promotion_transaction_binds_candidate_episodes_evidence_and_receipt():
    db = PromotionDB()
    db.db.executemany(
        "INSERT INTO workspace_episodes(episode_id) VALUES(?)",
        [("episode:a",), ("episode:b",)],
    )
    evidence_a = db.add_memory("fact", "evidence", "A", None, "gabriel", {"source": "test"})
    evidence_b = db.add_memory("fact", "evidence", "B", None, "gabriel", {"source": "test"})
    manager = MethodMemoryManager(db)
    candidate_id = manager.admit(
        "framework_candidate",
        "causal discrimination",
        candidate_record(supporting_memory_ids=[evidence_a, evidence_b]),
        "turn:promotion",
        "gabriel",
        {"source": "episode_abstraction", "extractor": "test"},
    )

    result = manager.promote(
        candidate_id,
        evaluation="held-out transfer succeeded on a second source episode",
        provenance={"source": "held_out_eval", "evaluator": "test"},
    )
    receipt = manager.decode_row(
        db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=?",
            (result["receipt_memory_id"],),
        ).fetchone()
    )
    promoted = manager.decode_row(
        db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=?",
            (result["promoted_memory_id"],),
        ).fetchone()
    )
    assert receipt["value"]["action"] == "PROMOTE"
    assert receipt["value"]["method_memory_id"] == candidate_id
    assert promoted["kind"] == "framework"
    assert promoted["value"]["status"] == "PROMOTED"
    assert promoted["provenance"]["promotion_source_memory_id"] == candidate_id
    assert promoted["provenance"]["promotion_receipt_id"] == result["receipt_memory_id"]

    row_count = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
    with pytest.raises(MethodMemoryValidationError, match="already has a promotion receipt"):
        manager.promote(
            candidate_id,
            evaluation="duplicate promotion attempt",
            provenance={"source": "held_out_eval", "evaluator": "test"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == row_count


def test_promotion_missing_episode_rolls_back_without_receipt_or_framework():
    db = PromotionDB()
    db.db.execute("INSERT INTO workspace_episodes(episode_id) VALUES('episode:a')")
    evidence = db.add_memory("fact", "evidence", "A", None, "gabriel", {"source": "test"})
    manager = MethodMemoryManager(db)
    candidate_id = manager.admit(
        "framework_candidate",
        "causal discrimination",
        candidate_record(
            source_episode_ids=["episode:a", "episode:missing"],
            supporting_memory_ids=[evidence],
        ),
        "turn:promotion",
        "gabriel",
        {"source": "episode_abstraction", "extractor": "test"},
    )
    before = db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
    with pytest.raises(MethodMemoryValidationError, match="episode evidence is incomplete"):
        manager.promote(
            candidate_id,
            evaluation="must not promote with a missing source episode",
            provenance={"source": "held_out_eval", "evaluator": "test"},
        )
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == before
    assert db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind IN ('method_receipt','framework','heuristic')"
    ).fetchone()[0] == 0
