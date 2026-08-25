#!/usr/bin/env python3
"""Deterministic reference fixture for COGNITIVE_PROCESS_ABI/v1.

This is a control-plane/component fixture, not a trained cognitive grid and not a
Claude Code runtime. It exists to falsify ABI shape errors before model execution.

Credit boundary:
- variable-grid control fixture: executable component evidence only
- small-model cognition: 0
- Claude Code bridge runtime: 0 (bridge is stubbed)
- Global J-Space causal runtime: 0
- whole EntityOS/HCU runtime: 0
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Iterable

CENSUS_SCHEMA = "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1"
ABI_SCHEMA = "COGNITIVE_PROCESS_ABI/v1"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RuntimeConfig:
    requested_n: int
    available_n: int
    grid_instance_id: str = "fixture-grid-v1"

    def __post_init__(self):
        if self.requested_n < 1 or self.available_n < 1:
            raise ValueError("N must be >= 1")


class VariableGridFixture:
    def __init__(self, census: dict, abi: dict, config: RuntimeConfig):
        if census.get("schema") != CENSUS_SCHEMA:
            raise ValueError("wrong census schema")
        if abi.get("schema") != ABI_SCHEMA:
            raise ValueError("wrong ABI schema")
        self.census = census
        self.abi = abi
        self.config = config
        self.processes = {p["id"]: p for p in census["processes"]}
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        self._schema()

    def _schema(self) -> None:
        self.con.executescript("""
        CREATE TABLE canonical_state(
          object_key TEXT PRIMARY KEY,
          value_json TEXT NOT NULL,
          epoch INTEGER NOT NULL,
          digest TEXT NOT NULL
        );
        CREATE TABLE task_admission(
          causal_event_id TEXT PRIMARY KEY,
          admission_id TEXT NOT NULL UNIQUE,
          generation INTEGER NOT NULL,
          payload_digest TEXT NOT NULL
        );
        CREATE TABLE work_queue(
          work_id TEXT PRIMARY KEY,
          causal_event_id TEXT NOT NULL,
          admission_id TEXT NOT NULL,
          generation INTEGER NOT NULL,
          process_id TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          payload_digest TEXT NOT NULL,
          workspace_epoch INTEGER NOT NULL,
          status TEXT NOT NULL
        );
        CREATE TABLE result_log(
          result_id TEXT PRIMARY KEY,
          work_id TEXT NOT NULL,
          process_id TEXT NOT NULL,
          executor_id TEXT NOT NULL,
          result_class TEXT NOT NULL,
          result_json TEXT NOT NULL,
          semantic_digest TEXT NOT NULL
        );
        CREATE TABLE db_write_proposals(
          proposal_id TEXT PRIMARY KEY,
          work_id TEXT NOT NULL,
          object_key TEXT NOT NULL,
          value_json TEXT NOT NULL,
          status TEXT NOT NULL
        );
        CREATE TABLE effect_request_candidates(
          effect_candidate_id TEXT PRIMARY KEY,
          work_id TEXT NOT NULL,
          request_json TEXT NOT NULL,
          status TEXT NOT NULL
        );
        CREATE TABLE effect_journal(
          effect_id TEXT PRIMARY KEY,
          work_id TEXT NOT NULL,
          outcome TEXT NOT NULL
        );
        CREATE TABLE workspace_reentry(
          reentry_id TEXT PRIMARY KEY,
          source_result_id TEXT NOT NULL,
          source_process_id TEXT NOT NULL,
          causal_event_id TEXT NOT NULL,
          from_workspace_epoch INTEGER NOT NULL,
          to_workspace_epoch INTEGER NOT NULL,
          payload_digest TEXT NOT NULL,
          observed_downstream_change TEXT NOT NULL
        );
        """)

    def close(self) -> None:
        self.con.close()

    def seed_canonical_state(self, object_key: str, value: Any, epoch: int = 1) -> None:
        """Deterministic test-only state seeding; never called from a cognitive result."""
        text = canonical_json(value)
        self.con.execute(
            "INSERT INTO canonical_state(object_key,value_json,epoch,digest) VALUES(?,?,?,?)",
            (object_key, text, epoch, hashlib.sha256(text.encode()).hexdigest()),
        )
        self.con.commit()

    def canonical_state(self, object_key: str) -> Any | None:
        row = self.con.execute(
            "SELECT value_json FROM canonical_state WHERE object_key=?", (object_key,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def admit_task(self, payload: Any, generation: int = 1) -> dict:
        p_digest = digest(payload)
        causal_event_id = "ce-" + digest({"generation": generation, "payload_digest": p_digest})[:20]
        admission_id = "adm-" + digest({"causal_event_id": causal_event_id, "transport": "fixture"})[:20]
        self.con.execute(
            "INSERT OR IGNORE INTO task_admission(causal_event_id,admission_id,generation,payload_digest) VALUES(?,?,?,?)",
            (causal_event_id, admission_id, generation, p_digest),
        )
        self.con.commit()
        return {
            "causal_event_id": causal_event_id,
            "admission_id": admission_id,
            "generation": generation,
            "payload_digest": p_digest,
        }

    def enqueue(self, admission: dict, process_id: str, payload: Any, workspace_epoch: int = 1) -> dict:
        if process_id not in self.processes:
            raise ValueError("unknown process_id")
        payload_digest = digest(payload)
        work_id = "work-" + digest({
            "causal_event_id": admission["causal_event_id"],
            "generation": admission["generation"],
            "process_id": process_id,
            "payload_digest": payload_digest,
            "workspace_epoch": workspace_epoch,
        })[:24]
        self.con.execute(
            """INSERT OR IGNORE INTO work_queue
               (work_id,causal_event_id,admission_id,generation,process_id,payload_json,payload_digest,workspace_epoch,status)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                work_id,
                admission["causal_event_id"],
                admission["admission_id"],
                admission["generation"],
                process_id,
                canonical_json(payload),
                payload_digest,
                workspace_epoch,
                "READY",
            ),
        )
        self.con.commit()
        return {"work_id": work_id, "process_id": process_id}

    def _executor_for(self, work_id: str) -> str:
        n = min(self.config.requested_n, self.config.available_n)
        slot = int(hashlib.sha256(work_id.encode()).hexdigest(), 16) % n
        return f"fixture-executor-{slot:04d}"

    def execute_ready(self) -> list[dict]:
        rows = self.con.execute(
            "SELECT * FROM work_queue WHERE status='READY' ORDER BY work_id"
        ).fetchall()
        results = []
        for row in rows:
            process_id = row["process_id"]
            executor_id = self._executor_for(row["work_id"])
            semantic_result = {
                "causal_event_id": row["causal_event_id"],
                "admission_id": row["admission_id"],
                "generation": row["generation"],
                "work_id": row["work_id"],
                "process_id": process_id,
                "result_class": "CANDIDATE"
                    if self.processes[process_id]["implementation_class"] in {
                        "SIMULATE_ON_GRID", "EXTERNAL_STRONG_MODEL_BRIDGE", "OPTIONAL_CAUSAL_RESEARCH"
                    }
                    else "DETERMINISTIC_CONTROL_RESULT",
                "payload_digest": row["payload_digest"],
                "workspace_epoch": row["workspace_epoch"],
                "credit_scope": "REFERENCE_FIXTURE_COMPONENT_ONLY",
            }
            semantic_digest = digest(semantic_result)
            result_id = "res-" + digest({"semantic_digest": semantic_digest, "executor_id": executor_id})[:24]
            self.con.execute(
                """INSERT INTO result_log
                   (result_id,work_id,process_id,executor_id,result_class,result_json,semantic_digest)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    result_id, row["work_id"], process_id, executor_id,
                    semantic_result["result_class"], canonical_json(semantic_result), semantic_digest,
                ),
            )
            self.con.execute("UPDATE work_queue SET status='DONE' WHERE work_id=?", (row["work_id"],))
            results.append({
                "result_id": result_id,
                "executor_id": executor_id,
                "semantic": semantic_result,
                "semantic_digest": semantic_digest,
            })
        self.con.commit()
        return results

    def propose_db_write(self, work_id: str, object_key: str, value: Any) -> str:
        proposal_id = "dbp-" + digest({"work_id": work_id, "object_key": object_key, "value": value})[:24]
        self.con.execute(
            "INSERT INTO db_write_proposals(proposal_id,work_id,object_key,value_json,status) VALUES(?,?,?,?,?)",
            (proposal_id, work_id, object_key, canonical_json(value), "PROPOSED_NOT_COMMITTED"),
        )
        self.con.commit()
        return proposal_id

    def propose_effect(self, work_id: str, request: Any) -> str:
        candidate_id = "efp-" + digest({"work_id": work_id, "request": request})[:24]
        self.con.execute(
            "INSERT INTO effect_request_candidates(effect_candidate_id,work_id,request_json,status) VALUES(?,?,?,?)",
            (candidate_id, work_id, canonical_json(request), "PROPOSED_NOT_EXECUTED"),
        )
        self.con.commit()
        return candidate_id

    def stub_claude_roundtrip(self, admission: dict, work_id: str, workspace_epoch: int, state_refs: Iterable[str]) -> dict:
        """Deterministic bridge fixture. This is explicitly NOT a Claude Code invocation."""
        bridge_request = {
            "schema": "CLAUDE_CODE_BRIDGE_PACKET/v1",
            "bridge_id": "bridge-" + digest({"work_id": work_id, "direction": "GRID_TO_CLAUDE"})[:20],
            "direction": "GRID_TO_CLAUDE",
            "causal_event_id": admission["causal_event_id"],
            "work_id": work_id,
            "workspace_epoch": workspace_epoch,
            "interface_class": "STRUCTURED_TEXT",
            "payload_ref": "fixture://handoff/" + work_id,
            "payload_digest": digest({"work_id": work_id, "kind": "handoff"}),
            "state_refs": sorted(state_refs),
            "tool_scope_ref": "fixture://no-tools",
            "request_or_result_identity": "fixture-request-" + work_id,
        }
        bridge_result = {
            **bridge_request,
            "bridge_id": "bridge-" + digest({"work_id": work_id, "direction": "CLAUDE_TO_GRID"})[:20],
            "direction": "CLAUDE_TO_GRID",
            "payload_ref": "fixture://return/" + work_id,
            "payload_digest": digest({"work_id": work_id, "kind": "return"}),
            "request_or_result_identity": "fixture-result-" + work_id,
            "runtime_credit": 0,
            "stubbed": True,
        }
        source_result_id = "stub-claude-" + bridge_result["payload_digest"][:18]
        reentry = {
            "schema": "WORKSPACE_REENTRY/v1",
            "source_result_id": source_result_id,
            "source_process_id": "ZECP14",
            "causal_event_id": admission["causal_event_id"],
            "from_workspace_epoch": workspace_epoch,
            "to_workspace_epoch": workspace_epoch + 1,
            "reentry_payload_ref": bridge_result["payload_ref"],
            "reentry_digest": bridge_result["payload_digest"],
            "observed_downstream_change": "TRUE",
        }
        reentry_id = "re-" + digest(reentry)[:24]
        self.con.execute(
            """INSERT INTO workspace_reentry
               (reentry_id,source_result_id,source_process_id,causal_event_id,from_workspace_epoch,to_workspace_epoch,payload_digest,observed_downstream_change)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                reentry_id, source_result_id, "ZECP14", admission["causal_event_id"],
                workspace_epoch, workspace_epoch + 1, bridge_result["payload_digest"], "TRUE",
            ),
        )
        self.con.commit()
        return {"request": bridge_request, "result": bridge_result, "reentry": reentry}

    def semantic_fingerprint(self) -> str:
        rows = self.con.execute(
            "SELECT result_json FROM result_log ORDER BY work_id"
        ).fetchall()
        return digest([json.loads(r[0]) for r in rows])

    def count(self, table: str) -> int:
        if table not in {
            "canonical_state", "task_admission", "work_queue", "result_log",
            "db_write_proposals", "effect_request_candidates", "effect_journal", "workspace_reentry"
        }:
            raise ValueError("table not allowed")
        return int(self.con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
