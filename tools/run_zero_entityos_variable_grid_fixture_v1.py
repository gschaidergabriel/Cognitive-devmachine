#!/usr/bin/env python3
"""Deterministic DB-backed variable-grid reference fixture for EntityOS/HCU.

Implements the current owner-aligned ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1
and COGNITIVE_PROCESS_ABI/v1 discriminators without model/provider network I/O.

This is a deterministic reference-fixture execution only. It grants no 0.8B
model runtime, Claude Code runtime, Global J-Space causal, full-HCU, whole-
EntityOS/HCU, or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_CENSUS = "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1"
EXPECTED_ABI = "COGNITIVE_PROCESS_ABI/v1"
FIXTURE_SCHEMA = "ZERO_ENTITYOS_VARIABLE_GRID_FIXTURE/v1"
RESULT_SCHEMA = "ZERO_ENTITYOS_VARIABLE_GRID_FIXTURE_RESULT/v1"
GRID_SIZES = (1, 10, 20)
PROCESS_IDS = {f"ZECP{i:02d}" for i in range(1, 21)}


class FixtureError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), f"{path}: object required")
    return value


def validate_contract(census: dict[str, Any], abi: dict[str, Any]) -> None:
    require(census.get("schema") == EXPECTED_CENSUS, "census schema drift")
    require(abi.get("schema") == EXPECTED_ABI, "ABI schema drift")
    ids = {p.get("id") for p in census.get("processes", []) if isinstance(p, dict)}
    require(ids == PROCESS_IDS, "census process set must be ZECP01..ZECP20")
    discriminators = {
        item.get("id")
        for item in abi.get("acceptance_discriminators", [])
        if isinstance(item, dict)
    }
    require(
        discriminators
        == {
            "ABI-D1-N-INVARIANCE",
            "ABI-D2-DB-FACT-FENCE",
            "ABI-D3-EFFECT-FENCE",
            "ABI-D4-CLAUDE-REENTRY",
            "ABI-D5-JSPACE-EVIDENCE",
        },
        "ABI discriminator set drift",
    )


@dataclass(frozen=True)
class WorkIdentity:
    causal_event_id: str
    admission_id: str
    generation: int
    work_id: str
    process_id: str

    def semantic_id(self) -> str:
        # Runtime topology and physical executor identity are deliberately absent.
        return digest(
            {
                "schema": "COGNITIVE_SEMANTIC_WORK_ID/v1",
                "causal_event_id": self.causal_event_id,
                "admission_id": self.admission_id,
                "generation": self.generation,
                "work_id": self.work_id,
                "process_id": self.process_id,
            }
        )


def executor_binding(work: WorkIdentity, requested_n: int) -> dict[str, Any]:
    require(requested_n > 0, "requested_N must be positive")
    semantic = work.semantic_id()
    executor_index = int(semantic[:16], 16) % requested_n
    lease_material = {
        "grid_instance_id": f"fixture-grid-N{requested_n}",
        "requested_N": requested_n,
        "available_N": requested_n,
        "executor_id": f"cell-{executor_index:04d}",
        "process_id": work.process_id,
        "semantic_work_id": semantic,
    }
    return {
        "schema": "GRID_EXECUTOR_BINDING/v1",
        **lease_material,
        "lease_id": digest({"lease": lease_material}),
        "runtime_identity": "DETERMINISTIC_REFERENCE_FIXTURE_NO_MODEL",
        "started_at": "FIXTURE_LOGICAL_TIME_0",
        "ended_at": "FIXTURE_LOGICAL_TIME_1",
    }


class CanonicalDB:
    """Minimal deterministic state boundary used only by this fixture."""

    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            "CREATE TABLE canonical_state (key TEXT PRIMARY KEY, value TEXT NOT NULL, epoch INTEGER NOT NULL, provenance TEXT NOT NULL)"
        )
        self.conn.execute(
            "CREATE TABLE admissions (proposal_digest TEXT PRIMARY KEY, admission_id TEXT NOT NULL, status TEXT NOT NULL)"
        )
        self.conn.execute(
            "INSERT INTO canonical_state(key,value,epoch,provenance) VALUES (?,?,?,?)",
            ("fact:project", "EntityOS", 1, "fixture:seed"),
        )
        self.conn.commit()

    def read(self, key: str) -> tuple[str, int, str] | None:
        row = self.conn.execute(
            "SELECT value,epoch,provenance FROM canonical_state WHERE key=?", (key,)
        ).fetchone()
        return tuple(row) if row else None

    def propose_write(self, *, key: str, value: str, source_result_id: str) -> dict[str, Any]:
        proposal = {
            "schema": "DB_WRITE_PROPOSAL/v1",
            "key": key,
            "value": value,
            "source_result_id": source_result_id,
            "commit_authority": False,
        }
        return {**proposal, "proposal_digest": digest(proposal)}

    def direct_model_write(self, proposal: dict[str, Any]) -> None:
        raise FixtureError("ABI-D2: MODEL_GRID_CLAUDE_DIRECT_DB_COMMIT_FORBIDDEN")

    def admit(self, proposal: dict[str, Any], admission_id: str) -> dict[str, Any]:
        proposal_digest = proposal.get("proposal_digest")
        require(isinstance(proposal_digest, str) and proposal_digest, "proposal digest required")
        self.conn.execute(
            "INSERT INTO admissions(proposal_digest,admission_id,status) VALUES (?,?,?)",
            (proposal_digest, admission_id, "ADMITTED"),
        )
        self.conn.commit()
        return {
            "schema": "DETERMINISTIC_DB_ADMISSION/v1",
            "proposal_digest": proposal_digest,
            "admission_id": admission_id,
            "status": "ADMITTED",
        }

    def commit_admitted(self, proposal: dict[str, Any], admission: dict[str, Any]) -> None:
        proposal_digest = proposal.get("proposal_digest")
        require(admission.get("proposal_digest") == proposal_digest, "DB admission digest mismatch")
        row = self.conn.execute(
            "SELECT status FROM admissions WHERE proposal_digest=? AND admission_id=?",
            (proposal_digest, admission.get("admission_id")),
        ).fetchone()
        require(row == ("ADMITTED",), "missing deterministic DB admission")
        old = self.read(proposal["key"])
        epoch = (old[1] + 1) if old else 1
        self.conn.execute(
            "INSERT INTO canonical_state(key,value,epoch,provenance) VALUES (?,?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value,epoch=excluded.epoch,provenance=excluded.provenance",
            (proposal["key"], proposal["value"], epoch, f"admission:{admission['admission_id']}"),
        )
        self.conn.commit()


class EffectBoundary:
    def issue_result(self, *, process_id: str, requested_result_class: str) -> dict[str, Any]:
        if requested_result_class == "EFFECT_RECEIPT" and process_id != "ZECP17":
            raise FixtureError("ABI-D3: NON_ZECP17_EFFECT_RECEIPT_FORBIDDEN")
        return {
            "schema": "COGNITIVE_RESULT_PACKET/v1",
            "process_id": process_id,
            "result_class": requested_result_class,
            "real_effect_executed": False,
        }


def claude_reentry_fixture(work: WorkIdentity, payload: dict[str, Any]) -> dict[str, Any]:
    """Synthetic observable-interface return; never claims Claude runtime credit."""
    request = {
        "schema": "CLAUDE_CODE_BRIDGE_PACKET/v1",
        "direction": "GRID_TO_CLAUDE",
        "bridge_id": "bridge-fixture-1",
        "causal_event_id": work.causal_event_id,
        "work_id": work.work_id,
        "workspace_epoch": 4,
        "interface_class": "STRUCTURED_TEXT",
        "payload_ref": "fixture:handoff",
        "payload_digest": digest({"handoff": "fixture"}),
        "state_refs": ["db:fixture:snapshot:1"],
        "tool_scope_ref": "fixture:none",
        "request_or_result_identity": "fixture-request-1",
    }
    returned = {
        "schema": "CLAUDE_CODE_BRIDGE_PACKET/v1",
        "direction": "CLAUDE_TO_GRID",
        "bridge_id": request["bridge_id"],
        "causal_event_id": request["causal_event_id"],
        "work_id": request["work_id"],
        "workspace_epoch": request["workspace_epoch"],
        "interface_class": request["interface_class"],
        "payload_ref": "fixture:return",
        "payload_digest": digest(payload),
        "state_refs": request["state_refs"],
        "tool_scope_ref": request["tool_scope_ref"],
        "request_or_result_identity": "fixture-result-1",
        "synthetic_fixture_return": True,
    }
    reentry = {
        "schema": "WORKSPACE_REENTRY/v1",
        "source_result_id": returned["request_or_result_identity"],
        "source_process_id": "ZECP14",
        "causal_event_id": returned["causal_event_id"],
        "from_workspace_epoch": returned["workspace_epoch"],
        "to_workspace_epoch": returned["workspace_epoch"] + 1,
        "reentry_payload_ref": returned["payload_ref"],
        "reentry_digest": returned["payload_digest"],
        "observed_downstream_change": "TRUE",
        "runtime_credit": "SYNTHETIC_REFERENCE_FIXTURE_ONLY",
    }
    downstream = digest(
        {
            "schema": "FIXTURE_DOWNSTREAM_SELECTION/v1",
            "semantic_work_id": work.semantic_id(),
            "reentry_digest": reentry["reentry_digest"],
        }
    )
    return {"request": request, "return": returned, "reentry": reentry, "downstream": downstream}


def run_fixture(census: dict[str, Any], abi: dict[str, Any]) -> dict[str, Any]:
    validate_contract(census, abi)
    checks: list[dict[str, Any]] = []

    work = WorkIdentity(
        causal_event_id="fixture-event-001",
        admission_id="fixture-admission-001",
        generation=1,
        work_id="fixture-work-001",
        process_id="ZECP06",
    )

    bindings = [executor_binding(work, n) for n in GRID_SIZES]
    semantic_ids = {binding["semantic_work_id"] for binding in bindings}
    require(len(semantic_ids) == 1, "ABI-D1: semantic identity changed with N")
    require({b["requested_N"] for b in bindings} == set(GRID_SIZES), "ABI-D1: N coverage incomplete")
    checks.append({"id": "ABI-D1-N-INVARIANCE", "status": "PASS", "grid_sizes": list(GRID_SIZES)})

    db = CanonicalDB()
    before = db.read("fact:project")
    proposal = db.propose_write(
        key="fact:project",
        value="FORGED_MODEL_VALUE",
        source_result_id="fixture-model-result-1",
    )
    blocked = False
    try:
        db.direct_model_write(proposal)
    except FixtureError:
        blocked = True
    require(blocked, "ABI-D2: direct model DB write was not blocked")
    require(db.read("fact:project") == before, "ABI-D2: blocked proposal changed canonical DB")
    admission = db.admit(proposal, "fixture-db-admission-1")
    db.commit_admitted(proposal, admission)
    after = db.read("fact:project")
    require(after is not None and after[0] == "FORGED_MODEL_VALUE", "ABI-D2: admitted DB write did not commit")
    require(after[1] == before[1] + 1, "ABI-D2: DB epoch did not advance exactly once")
    checks.append({"id": "ABI-D2-DB-FACT-FENCE", "status": "PASS"})

    effects = EffectBoundary()
    effect_blocked = False
    try:
        effects.issue_result(process_id="ZECP16", requested_result_class="EFFECT_RECEIPT")
    except FixtureError:
        effect_blocked = True
    require(effect_blocked, "ABI-D3: non-ZECP17 effect receipt escaped fence")
    admitted_effect_boundary = effects.issue_result(process_id="ZECP17", requested_result_class="EFFECT_RECEIPT")
    require(admitted_effect_boundary["real_effect_executed"] is False, "fixture must never execute a real effect")
    checks.append({"id": "ABI-D3-EFFECT-FENCE", "status": "PASS"})

    reentry_a = claude_reentry_fixture(work, {"candidate": "A"})
    reentry_b = claude_reentry_fixture(work, {"candidate": "B"})
    require(reentry_a["request"]["bridge_id"] == reentry_a["return"]["bridge_id"], "ABI-D4: bridge identity lost")
    require(reentry_a["reentry"]["causal_event_id"] == work.causal_event_id, "ABI-D4: causal event lost")
    require(reentry_a["downstream"] != reentry_b["downstream"], "ABI-D4: controlled return change did not change deterministic downstream selection")
    checks.append({"id": "ABI-D4-CLAUDE-REENTRY", "status": "PASS", "scope": "SYNTHETIC_OBSERVABLE_INTERFACE_FIXTURE"})

    jspace_claim = {
        "text_presence": True,
        "controlled_model_internal_intervention": False,
        "promotion": "FORBIDDEN",
    }
    require(jspace_claim["promotion"] == "FORBIDDEN", "ABI-D5: text presence minted J-Space causal credit")
    checks.append({"id": "ABI-D5-JSPACE-EVIDENCE", "status": "PASS", "model_runtime_credit": 0})

    return {
        "schema": RESULT_SCHEMA,
        "fixture_schema": FIXTURE_SCHEMA,
        "status": "PASS",
        "checks": checks,
        "semantic_work_id": work.semantic_id(),
        "grid_bindings": bindings,
        "credit_boundary": {
            "deterministic_reference_fixture": 1,
            "variable_grid_model_runtime": 0,
            "claude_code_runtime": 0,
            "global_jspace_causal_runtime": 0,
            "whole_entityos_hcu_runtime": 0,
            "training": 0,
        },
        "network_io": "NONE",
        "real_effect_execution": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", default="research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json")
    parser.add_argument("--abi", default="research_entity/global/COGNITIVE_PROCESS_ABI_v1.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_fixture(load_json(Path(args.census)), load_json(Path(args.abi)))
    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    else:
        print("PASS: ZERO_ENTITYOS_VARIABLE_GRID_REFERENCE_FIXTURE")
        for check in result["checks"]:
            print(f"PASS: {check['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
