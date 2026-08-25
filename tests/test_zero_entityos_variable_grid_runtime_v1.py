from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.zero_entityos_variable_grid_runtime_v1 import (
    CognitiveWork,
    EphemeralGridLease,
    GridRuntimeError,
    VariableGridNode,
    VariableGridRuntime,
    canonical_digest,
)


class SQLiteStateAuthorityFixture:
    """Test-only external state authority. Runtime production code does not own this DB."""

    def __init__(self, path: str) -> None:
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("create table if not exists meta(generation integer not null)")
            db.execute("create table if not exists kv(k text primary key, v text not null)")
            row = db.execute("select count(*) from meta").fetchone()[0]
            if row == 0:
                db.execute("insert into meta values (1)")
            db.commit()

    def put_fixture(self, key: str, value: str) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("insert or replace into kv(k,v) values (?,?)", (key, value))
            db.commit()

    def current_generation(self) -> int:
        with sqlite3.connect(self.path) as db:
            return int(db.execute("select generation from meta").fetchone()[0])

    def bump_generation(self) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("update meta set generation = generation + 1")
            db.commit()

    def read_slice(self, generation: int, keys: tuple[str, ...]):
        if generation != self.current_generation():
            raise RuntimeError("fixture stale")
        out = {}
        with sqlite3.connect(self.path) as db:
            for key in keys:
                row = db.execute("select v from kv where k=?", (key,)).fetchone()
                if row is not None:
                    out[key] = row[0]
        return out

    def snapshot_digest(self, generation: int) -> str:
        if generation != self.current_generation():
            raise RuntimeError("fixture stale")
        with sqlite3.connect(self.path) as db:
            rows = db.execute("select k,v from kv order by k").fetchall()
        return canonical_digest({"generation": generation, "rows": rows})


def handler_context(work, state):
    return "MEASUREMENT", "KNOWN", {"seen": state.get("project"), "process": work.process_id}


def handler_plan(work, state):
    return "CANDIDATE", "BOUNDED", {"next": work.payload.get("goal"), "memory": state.get("memory"), "process": work.process_id}


class VariableGridRuntimeV1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "state.sqlite")
        self.state = SQLiteStateAuthorityFixture(self.db_path)
        self.state.put_fixture("project", "EntityOS")
        self.state.put_fixture("memory", "persisted")
        self.handlers = {"AZP01": handler_context, "AZP04": handler_plan}
        self.node = VariableGridNode(
            executor_instance_id="node-A",
            model_artifact_digest="model-08b-test-artifact",
            state_authority=self.state,
            handlers=self.handlers,
        )
        self.lease = EphemeralGridLease(
            generation=1,
            lease_id="lease-A",
            executor_instance_id="node-A",
            eligible_process_ids=("AZP01", "AZP04"),
            budget_digest="budget-1",
            expires_at=100,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def work(self, process_id: str, work_id: str = "w1") -> CognitiveWork:
        payload = {"goal": "advance"}
        return CognitiveWork(
            causal_event_id="event-1",
            admission_id="admission-1",
            generation=1,
            work_id=work_id,
            process_id=process_id,
            parent_work_ids=(),
            db_snapshot_digest=self.state.snapshot_digest(1),
            workspace_digest="workspace-1",
            input_digest=canonical_digest(payload),
            capability_scope_digest="caps-read-propose",
            budget_digest="budget-1",
            provenance_digest="prov-1",
            state_keys=("project", "memory"),
            payload=payload,
        )

    def test_same_role_free_node_executes_two_distinct_processes(self):
        a = self.node.execute(self.work("AZP01", "w-context"), self.lease, logical_tick=1)
        b = self.node.execute(self.work("AZP04", "w-plan"), self.lease, logical_tick=2)
        self.assertEqual(a.executor_instance_id, b.executor_instance_id)
        self.assertEqual(a.result_kind, "MEASUREMENT")
        self.assertEqual(b.result_kind, "CANDIDATE")
        self.assertFalse(hasattr(self.node, "role"))
        self.assertFalse(hasattr(self.node, "personality"))

    def test_restart_rejoin_reads_same_external_durable_state_with_new_lease(self):
        before = self.node.execute(self.work("AZP01", "w-before"), self.lease, logical_tick=1)
        restarted_state = SQLiteStateAuthorityFixture(self.db_path)
        restarted = VariableGridNode(
            executor_instance_id="node-B",
            model_artifact_digest="model-08b-test-artifact",
            state_authority=restarted_state,
            handlers=self.handlers,
        )
        new_lease = EphemeralGridLease(
            generation=1,
            lease_id="lease-B",
            executor_instance_id="node-B",
            eligible_process_ids=("AZP01",),
            budget_digest="budget-1",
            expires_at=100,
        )
        after = restarted.execute(self.work("AZP01", "w-after"), new_lease, logical_tick=2)
        self.assertEqual(before.output["seen"], "EntityOS")
        self.assertEqual(after.output["seen"], "EntityOS")
        self.assertNotEqual(self.lease.lease_digest, new_lease.lease_digest)

    def test_stale_generation_fails_closed(self):
        work = self.work("AZP01")
        self.state.bump_generation()
        with self.assertRaisesRegex(GridRuntimeError, "STALE_GENERATION"):
            self.node.execute(work, self.lease, logical_tick=1)

    def test_wrong_db_snapshot_fails_closed(self):
        work = self.work("AZP01")
        bad = CognitiveWork(**{**work.__dict__, "db_snapshot_digest": "wrong"})
        with self.assertRaisesRegex(GridRuntimeError, "DB_SNAPSHOT_DIGEST_MISMATCH"):
            self.node.execute(bad, self.lease, logical_tick=1)

    def test_process_not_in_lease_fails_closed(self):
        lease = EphemeralGridLease(
            generation=1,
            lease_id="lease-limited",
            executor_instance_id="node-A",
            eligible_process_ids=("AZP01",),
            budget_digest="budget-1",
            expires_at=100,
        )
        with self.assertRaisesRegex(GridRuntimeError, "PROCESS_NOT_LEASED"):
            self.node.execute(self.work("AZP04"), lease, logical_tick=1)

    def test_db_and_effect_outputs_remain_proposals_only(self):
        work = self.work("AZP04")
        dbp = self.node.propose_db_write(work, work.db_snapshot_digest, {"goal": "new"})
        eff = self.node.propose_effect(work, {"tool": "example"})
        self.assertEqual(dbp["authority"], "PROPOSAL_ONLY")
        self.assertEqual(dbp["commit_rule"], "DETERMINISTIC_DB_GATE_AND_CAS_REQUIRED")
        self.assertEqual(eff["authority"], "PROPOSAL_ONLY")
        self.assertEqual(eff["execution_rule"], "EFFECTGATE_EFFECTJOURNAL_REQUIRED")
        self.assertFalse(hasattr(self.node, "commit_db_write"))
        self.assertFalse(hasattr(self.node, "execute_effect"))

    def test_grid_n_does_not_change_wire_semantics(self):
        one = VariableGridRuntime(1)
        twenty = VariableGridRuntime(20)
        self.assertNotEqual(one.n, twenty.n)
        self.assertEqual(one.wire_semantics_fingerprint(), twenty.wire_semantics_fingerprint())

    def test_noncandidate_result_kind_is_rejected(self):
        def bad_handler(work, state):
            return "CANONICAL", "KNOWN", {"bad": True}

        node = VariableGridNode(
            executor_instance_id="node-A",
            model_artifact_digest="model-08b-test-artifact",
            state_authority=self.state,
            handlers={"AZP01": bad_handler},
        )
        with self.assertRaisesRegex(GridRuntimeError, "CANONICAL_RESULT_KIND_FORBIDDEN"):
            node.execute(self.work("AZP01"), self.lease, logical_tick=1)


if __name__ == "__main__":
    unittest.main()
