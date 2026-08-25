#!/usr/bin/env python3
"""Deterministic executable smoke for DB-vs-simulation restart/resize semantics.

Component scope only. This is a zero-network SQLite reference discriminator; it grants
no whole-EntityOS/HCU, model-specific J-Space, Claude bridge runtime, or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any

PROPOSAL_SCHEMA = "DB_WRITE_PROPOSAL/v1"
BRIDGE_SCHEMA = "CLAUDE_CODE_BRIDGE_PACKET/v1"
RECEIPT_SCHEMA = "RESTART_RESIZE_DB_BOUNDARY_SMOKE/v1"
BOUNDARY_SCHEMA = "DB_VS_SIMULATION_BOUNDARY/v1"


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(obj: Any) -> str:
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()


class BoundaryViolation(RuntimeError):
    pass


class CanonicalS0:
    """Tiny deterministic S0 substrate with proposal/admission fences."""

    def __init__(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE TABLE meta (id INTEGER PRIMARY KEY CHECK(id=1), generation INTEGER NOT NULL, epoch INTEGER NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE state (key TEXT PRIMARY KEY, value_json TEXT NOT NULL, provenance TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE admissions (proposal_digest TEXT PRIMARY KEY, admitted_epoch INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO meta(id,generation,epoch) VALUES(1,1,0)")
        self.db.commit()

    def seed(self) -> None:
        rows = {
            "task_id": ("task:restart-resize-smoke", "DETERMINISTIC_SEED"),
            "durable_goal": ("preserve-boundary-semantics", "DETERMINISTIC_SEED"),
            "evidence_ref": ("evidence:seed:0001", "DETERMINISTIC_SEED"),
            "causal_event_id": ("event:smoke:0001", "DETERMINISTIC_SEED"),
        }
        for key, (value, provenance) in rows.items():
            self.db.execute(
                "INSERT INTO state(key,value_json,provenance) VALUES(?,?,?)",
                (key, _canon(value), provenance),
            )
        self.db.commit()

    @property
    def generation(self) -> int:
        return int(self.db.execute("SELECT generation FROM meta WHERE id=1").fetchone()[0])

    @property
    def epoch(self) -> int:
        return int(self.db.execute("SELECT epoch FROM meta WHERE id=1").fetchone()[0])

    def snapshot(self) -> dict[str, Any]:
        rows = [
            {"key": k, "value": json.loads(v), "provenance": p}
            for k, v, p in self.db.execute(
                "SELECT key,value_json,provenance FROM state ORDER BY key"
            ).fetchall()
        ]
        obj = {"generation": self.generation, "epoch": self.epoch, "rows": rows}
        return {**obj, "digest": _digest(obj)}

    def project(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "schema": "S1_REBUILD_PROJECTION/v1",
            "generation": snap["generation"],
            "source_epoch": snap["epoch"],
            "source_digest": snap["digest"],
            "state_refs": {row["key"]: row["value"] for row in snap["rows"]},
            "authority": "NONCANONICAL_REBUILDABLE_PROJECTION",
        }

    def make_write_proposal(
        self,
        *,
        key: str,
        value: Any,
        causal_event_id: str,
        origin: str = "S1_CANDIDATE",
        generation: int | None = None,
        base_epoch: int | None = None,
    ) -> dict[str, Any]:
        proposal = {
            "schema": PROPOSAL_SCHEMA,
            "causal_event_id": causal_event_id,
            "generation": self.generation if generation is None else generation,
            "base_epoch": self.epoch if base_epoch is None else base_epoch,
            "key": key,
            "value": value,
            "origin": origin,
            "authority": "PROPOSAL_ONLY",
        }
        return {**proposal, "proposal_digest": _digest(proposal)}

    def admit_write(self, proposal: dict[str, Any]) -> dict[str, Any]:
        before = self.snapshot()
        if proposal.get("schema") != PROPOSAL_SCHEMA:
            raise BoundaryViolation("WRONG_PROPOSAL_SCHEMA")
        if proposal.get("authority") != "PROPOSAL_ONLY" or proposal.get("origin") != "S1_CANDIDATE":
            raise BoundaryViolation("DIRECT_OR_UNTRUSTED_ORIGIN")
        if self.db.execute(
            "SELECT 1 FROM admissions WHERE proposal_digest=?",
            (proposal.get("proposal_digest"),),
        ).fetchone():
            raise BoundaryViolation("DUPLICATE_PROPOSAL")
        if proposal.get("generation") != self.generation:
            raise BoundaryViolation("STALE_GENERATION")
        if proposal.get("base_epoch") != self.epoch:
            raise BoundaryViolation("STALE_EPOCH")
        if not str(proposal.get("key", "")).startswith("durable_memory:"):
            raise BoundaryViolation("KEY_NOT_ADMITTED_FOR_SMOKE")
        body = {k: proposal[k] for k in (
            "schema", "causal_event_id", "generation", "base_epoch",
            "key", "value", "origin", "authority"
        )}
        if proposal.get("proposal_digest") != _digest(body):
            raise BoundaryViolation("PROPOSAL_DIGEST_MISMATCH")

        with self.db:
            next_epoch = self.epoch + 1
            self.db.execute(
                "INSERT OR REPLACE INTO state(key,value_json,provenance) VALUES(?,?,?)",
                (proposal["key"], _canon(proposal["value"]), "DETERMINISTIC_ADMISSION"),
            )
            self.db.execute("UPDATE meta SET epoch=? WHERE id=1", (next_epoch,))
            self.db.execute(
                "INSERT INTO admissions(proposal_digest,admitted_epoch) VALUES(?,?)",
                (proposal["proposal_digest"], next_epoch),
            )
        after = self.snapshot()
        return {
            "schema": "DB_WRITE_ADMISSION_RECEIPT/v1",
            "proposal_digest": proposal["proposal_digest"],
            "before_digest": before["digest"],
            "after_digest": after["digest"],
            "admitted_epoch": after["epoch"],
            "status": "ADMITTED",
        }

    def direct_model_write(self, *_: Any, **__: Any) -> None:
        raise BoundaryViolation("MODEL_OUTPUT_DIRECT_DB_WRITE")

    def recover_from_s1_cache(self, *_: Any, **__: Any) -> None:
        raise BoundaryViolation("S1_CACHE_USED_AS_RECOVERY_AUTHORITY")

    def direct_effect(self, *_: Any, **__: Any) -> None:
        raise BoundaryViolation("EFFECT_EXECUTION_REQUIRES_EFFECTGATE_JOURNAL")


@dataclass
class GridModule:
    module_id: str
    grid_n: int
    process_id: str
    s1: dict[str, Any] | None = None
    s2: dict[str, Any] | None = None

    def rebuild_from_s0(self, store: CanonicalS0) -> None:
        self.s1 = store.project()
        self.s2 = {}

    def simulate(self, label: str, value: Any) -> None:
        if self.s2 is None:
            raise BoundaryViolation("S2_NOT_INITIALIZED")
        self.s2[label] = value


def claude_code_roundtrip(
    *,
    store: CanonicalS0,
    module: GridModule,
    request_payload: dict[str, Any],
    result_payload: dict[str, Any],
) -> dict[str, Any]:
    """Observable bridge stub: result re-enters S1 only, never S0."""
    before = store.snapshot()["digest"]
    request = {
        "schema": BRIDGE_SCHEMA,
        "direction": "GRID_TO_CLAUDE",
        "module_id": module.module_id,
        "process_id": module.process_id,
        "grid_n": module.grid_n,
        "generation": store.generation,
        "source_epoch": store.epoch,
        "payload": request_payload,
        "payload_digest": _digest(request_payload),
        "interface_class": "STRUCTURED_TEXT",
    }
    result = {
        "schema": BRIDGE_SCHEMA,
        "direction": "CLAUDE_TO_GRID",
        "request_digest": _digest(request),
        "generation": store.generation,
        "source_epoch": store.epoch,
        "payload": result_payload,
        "payload_digest": _digest(result_payload),
        "authority": "CANDIDATE_OR_EVIDENCE_BOUND_RESULT",
    }
    if module.s1 is None:
        raise BoundaryViolation("S1_NOT_INITIALIZED")
    module.s1["claude_reentry_candidate"] = result
    if store.snapshot()["digest"] != before:
        raise BoundaryViolation("CLAUDE_CODE_DIRECT_CANONICAL_WRITE")
    return result


def _rejects(fn, expected: str) -> bool:
    try:
        fn()
    except BoundaryViolation as exc:
        return str(exc) == expected
    return False


def run_smoke() -> dict[str, Any]:
    store = CanonicalS0()
    store.seed()
    baseline = store.snapshot()

    first = GridModule("module:A:boot1", 1, "ZECP03")
    first.rebuild_from_s0(store)
    first.simulate("hypothesis", {"candidate": "ephemeral"})
    proposal = store.make_write_proposal(
        key="durable_memory:smoke:1",
        value={"memory": "admitted only through deterministic boundary"},
        causal_event_id="event:smoke:0001",
    )

    restarted = GridModule("module:A:boot2", 20, "ZECP06")
    restarted.rebuild_from_s0(store)
    after_restart = store.snapshot()

    checks: dict[str, bool] = {}
    checks["s0_stable_across_restart_and_resize"] = (
        baseline["digest"] == after_restart["digest"]
        and baseline["epoch"] == after_restart["epoch"]
        and baseline["generation"] == after_restart["generation"]
    )
    checks["s1_rebuilt_from_s0"] = (
        restarted.s1 is not None
        and restarted.s1["source_digest"] == after_restart["digest"]
        and restarted.s1["source_epoch"] == after_restart["epoch"]
    )
    checks["s2_loss_tolerated"] = restarted.s2 == {}

    negative_before = store.snapshot()["digest"]
    checks["direct_model_to_s0_rejected"] = _rejects(
        lambda: store.direct_model_write("x"), "MODEL_OUTPUT_DIRECT_DB_WRITE"
    )
    stale = store.make_write_proposal(
        key="durable_memory:stale",
        value={"x": 1},
        causal_event_id="event:smoke:0001",
        generation=store.generation - 1,
    )
    checks["stale_generation_write_rejected"] = _rejects(
        lambda: store.admit_write(stale), "STALE_GENERATION"
    )
    checks["s1_cache_recovery_authority_rejected"] = _rejects(
        lambda: store.recover_from_s1_cache(restarted.s1),
        "S1_CACHE_USED_AS_RECOVERY_AUTHORITY",
    )
    checks["direct_effect_rejected"] = _rejects(
        lambda: store.direct_effect("effect"),
        "EFFECT_EXECUTION_REQUIRES_EFFECTGATE_JOURNAL",
    )
    checks["negative_paths_do_not_mutate_s0"] = store.snapshot()["digest"] == negative_before

    bridge_before = store.snapshot()["digest"]
    bridge_result = claude_code_roundtrip(
        store=store,
        module=restarted,
        request_payload={"task": "inspect candidate"},
        result_payload={"candidate": "bridge-return"},
    )
    checks["claude_reentry_candidate_only"] = (
        bridge_result["authority"] == "CANDIDATE_OR_EVIDENCE_BOUND_RESULT"
        and store.snapshot()["digest"] == bridge_before
        and restarted.s1 is not None
        and "claude_reentry_candidate" in restarted.s1
    )

    before_admission = store.snapshot()
    admission = store.admit_write(proposal)
    after_admission = store.snapshot()
    checks["typed_durable_proposal_admitted_once"] = (
        admission["status"] == "ADMITTED"
        and after_admission["epoch"] == before_admission["epoch"] + 1
        and after_admission["digest"] != before_admission["digest"]
    )
    checks["duplicate_proposal_rejected"] = _rejects(
        lambda: store.admit_write(proposal), "DUPLICATE_PROPOSAL"
    )

    final_module = GridModule("module:B:boot1", 3, "ZECP12")
    final_module.rebuild_from_s0(store)
    final_snapshot = store.snapshot()
    checks["post_admission_s0_stable_across_second_resize"] = (
        final_snapshot["digest"] == after_admission["digest"]
        and final_snapshot["epoch"] == after_admission["epoch"]
        and final_module.s1 is not None
        and final_module.s1["source_digest"] == final_snapshot["digest"]
    )
    checks["process_identity_not_fixed_to_module_or_n"] = (
        first.process_id != restarted.process_id != final_module.process_id
        and {first.grid_n, restarted.grid_n, final_module.grid_n} == {1, 20, 3}
    )

    passed = all(checks.values())
    return {
        "schema": RECEIPT_SCHEMA,
        "declared_boundary_schema": BOUNDARY_SCHEMA,
        "status": "PASS_DB_SIMULATION_BOUNDARY_COMPONENT_ONLY" if passed else "FAIL",
        "checks": checks,
        "counts": {"passed": sum(checks.values()), "total": len(checks)},
        "baseline_s0_digest": baseline["digest"],
        "post_admission_s0_digest": after_admission["digest"],
        "final_epoch": final_snapshot["epoch"],
        "network_calls": 0,
        "provider_model_calls": 0,
        "real_effects": 0,
        "credit": {
            "db_simulation_boundary_component": 1 if passed else 0,
            "whole_entityos_hcu": 0,
            "full_hcu": 0,
            "jspace_model_runtime": 0,
            "claude_code_runtime": 0,
            "training": 0,
            "whole_product_pass": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    receipt = run_smoke()
    if args.json:
        print(json.dumps(receipt, sort_keys=True, indent=2))
    else:
        print(receipt["status"], f'{receipt["counts"]["passed"]}/{receipt["counts"]["total"]}')
    return 0 if receipt["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
