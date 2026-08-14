#!/usr/bin/env python3
"""Executable WP03 discriminator for the owner-fixed Frank single-spawn lease contract.

This probe does four bounded things:
1. derives a V18 declarative fixture from the current owner-fixed lease contract;
2. reproduces the current TypedIR semantic-identity blind spot for `type`/`class` declarations;
3. checks the isolated candidate that preserves those declarations and their identity;
4. separates that WP03 fix from the later atomic runtime/effect gap, while exercising SQLite
   BEGIN IMMEDIATE as a host reference control for exactly-one acquisition + epoch fencing.

A PASS means the discriminator behaved as expected. It does NOT promote CC-WP-03, CC-WP-09,
F-V01-02, effect authority, or finished Frank v0.1.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import threading
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as base
import claycode_structured_backend as structured
import claycode_wp03_type_decl_candidate as candidate

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR_PATH = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
OWNER_DIRECTIVE = ROOT / "research_entity/global/FRANK_V0_1_SINGLE_SPAWN_GLOBAL_BUSY_LEASE_DIRECTIVE.clay"

FIXTURE = """\
module clay.wp03.frank_single_spawn_fixture
type LeaseState = IDLE | ACTIVE | RELEASING | RECOVERING
type TaskState = RUNNING | WAITING_USER | DONE | FAILED | CANCELLED
class CredentialClass = TOKEN_AUTHENTICATED_SCOPED_CALLER
record FrankExecutionLease {
  state:LeaseState;
  lease_epoch:Int;
  execution_id:Option<ExecutionId>;
  holder_session_id:Option<SessionId>;
  holder_client_id:Option<ClientId>;
  holder_credential_fingerprint:Option<CredentialFingerprint>;
  current_task_id:Option<TaskId>;
  current_task_state:Option<TaskState>
}
record DirectTokenMessage {
  credential_class:CredentialClass;
  client_id:ClientId;
  session_id:SessionId;
  request_id:RequestId;
  credential_fingerprint:CredentialFingerprint;
  scope:Set<Constraint>
}
record SpawnDecision {
  semantic_code:Symbol;
  execution_id:Option<ExecutionId>;
  lease_epoch:Int
}
"""

ATOMIC_STRUCTURED_FIXTURE = """\
module clay.wp03.frank_single_spawn_atomic_gap
fn acquire(authenticated:Bool, state:LeaseState) -> Symbol {
  require authenticated
  return atomic_compare_and_set(state)
}
"""


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _class_map(ir: dict[str, Any]) -> dict[str, str]:
    return {row["name"]: row["class"] for row in ir["types"]}


def _decl_keys(ir: dict[str, Any]) -> set[tuple[str, str]]:
    return {(row["kind"], row["name"]) for row in ir["declarations"]}


def _build(source: str, logical_name: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    grammar = GRAMMAR_PATH.read_text(encoding="utf-8")
    artifact = front.compile_frontend(source, grammar, strict=True)
    unit = base.SourceUnit(Path(logical_name), artifact)
    baseline = base.build_typed_ir([unit])
    improved = candidate.build_typed_ir_candidate([unit])
    return artifact, baseline, improved


def _sqlite_reference_control(rounds: int = 32) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    lock = threading.Lock()

    with tempfile.TemporaryDirectory(prefix="claycode-single-spawn-") as td:
        db = Path(td) / "lease.sqlite3"
        con = sqlite3.connect(db, isolation_level=None)
        con.execute(
            "CREATE TABLE lease (lease_key TEXT PRIMARY KEY, state TEXT NOT NULL, lease_epoch INTEGER NOT NULL, holder TEXT)"
        )
        con.execute(
            "INSERT INTO lease(lease_key,state,lease_epoch,holder) VALUES('self.root/global-execution','IDLE',0,NULL)"
        )
        con.close()

        for round_index in range(rounds):
            setup = sqlite3.connect(db, isolation_level=None)
            current_epoch = setup.execute(
                "SELECT lease_epoch FROM lease WHERE lease_key='self.root/global-execution'"
            ).fetchone()[0]
            setup.execute(
                "UPDATE lease SET state='IDLE', holder=NULL WHERE lease_key='self.root/global-execution'"
            )
            setup.close()

            barrier = threading.Barrier(2)
            round_rows: list[tuple[str, str, int]] = []

            def acquire(holder: str) -> None:
                conn = sqlite3.connect(db, timeout=5.0, isolation_level=None)
                conn.execute("PRAGMA busy_timeout=5000")
                try:
                    barrier.wait(timeout=5.0)
                    conn.execute("BEGIN IMMEDIATE")
                    state, epoch = conn.execute(
                        "SELECT state,lease_epoch FROM lease WHERE lease_key='self.root/global-execution'"
                    ).fetchone()
                    if state == "IDLE":
                        new_epoch = int(epoch) + 1
                        changed = conn.execute(
                            "UPDATE lease SET state='ACTIVE', lease_epoch=?, holder=? "
                            "WHERE lease_key='self.root/global-execution' AND state='IDLE' AND lease_epoch=?",
                            (new_epoch, holder, epoch),
                        ).rowcount
                        if changed != 1:
                            conn.execute("ROLLBACK")
                            decision = "CAS_LOST"
                            observed_epoch = int(epoch)
                        else:
                            conn.execute("COMMIT")
                            decision = "ACQUIRED"
                            observed_epoch = new_epoch
                    else:
                        conn.execute("ROLLBACK")
                        decision = "FRANK_BUSY"
                        observed_epoch = int(epoch)
                    with lock:
                        round_rows.append((holder, decision, observed_epoch))
                except Exception as exc:  # preserve runtime failures as evidence
                    try:
                        conn.execute("ROLLBACK")
                    except Exception:
                        pass
                    with lock:
                        errors.append(f"round={round_index} holder={holder}: {type(exc).__name__}:{exc}")
                finally:
                    conn.close()

            a = threading.Thread(target=acquire, args=("client-A",), daemon=True)
            b = threading.Thread(target=acquire, args=("client-B",), daemon=True)
            a.start(); b.start(); a.join(timeout=10.0); b.join(timeout=10.0)
            if a.is_alive() or b.is_alive():
                errors.append(f"round={round_index}: thread timeout")
                break

            acquired = [x for x in round_rows if x[1] == "ACQUIRED"]
            busy = [x for x in round_rows if x[1] == "FRANK_BUSY"]
            if len(acquired) != 1 or len(busy) != 1:
                errors.append(f"round={round_index}: expected one ACQUIRED/one FRANK_BUSY, got {round_rows!r}")
                break

            admitted_epoch = acquired[0][2]
            if admitted_epoch != current_epoch + 1:
                errors.append(
                    f"round={round_index}: epoch did not increment exactly once: {current_epoch}->{admitted_epoch}"
                )
                break

            fence = sqlite3.connect(db, isolation_level=None)
            fence.execute("BEGIN IMMEDIATE")
            stale_changed = fence.execute(
                "UPDATE lease SET holder='zombie' WHERE lease_key='self.root/global-execution' AND lease_epoch=?",
                (current_epoch,),
            ).rowcount
            fence.execute("COMMIT")
            final_state, final_epoch, final_holder = fence.execute(
                "SELECT state,lease_epoch,holder FROM lease WHERE lease_key='self.root/global-execution'"
            ).fetchone()
            fence.close()
            if stale_changed != 0 or final_epoch != admitted_epoch or final_holder == "zombie":
                errors.append(
                    f"round={round_index}: stale epoch fencing failed changed={stale_changed} final={(final_state,final_epoch,final_holder)!r}"
                )
                break

            results.append(
                {
                    "round": round_index,
                    "decisions": sorted(x[1] for x in round_rows),
                    "admitted_epoch": admitted_epoch,
                    "stale_epoch_write_rows": stale_changed,
                }
            )

    return {
        "rounds_requested": rounds,
        "rounds_completed": len(results),
        "errors": errors,
        "exactly_one_acquire_each_round": len(results) == rounds and not errors,
        "stale_epoch_fencing_each_round": len(results) == rounds and not errors,
        "pass": len(results) == rounds and not errors,
    }


def main() -> int:
    owner_text = OWNER_DIRECTIVE.read_text(encoding="utf-8")
    owner_anchors = {
        "single_active": "ACTIVE_EXECUTION_COUNT <= 1" in owner_text,
        "busy_semantic": "FRANK_BUSY" in owner_text,
        "epoch_fencing": "presented_lease_epoch == current_lease_epoch" in owner_text,
        "short_sqlite_cas": "BEGIN_IMMEDIATE + compare_and_set + COMMIT" in owner_text,
    }

    artifact_a, baseline_a, candidate_a = _build(FIXTURE, "FRANK_SINGLE_SPAWN_FIXTURE_A.clay")
    mutated = FIXTURE.replace("RECOVERING", "RECOVERING_MUTATION", 1)
    artifact_b, baseline_b, candidate_b = _build(mutated, "FRANK_SINGLE_SPAWN_FIXTURE_B.clay")

    baseline_classes = _class_map(baseline_a)
    candidate_classes = _class_map(candidate_a)
    baseline_decls = _decl_keys(baseline_a)
    candidate_decls = _decl_keys(candidate_a)

    baseline_gap = {
        "type_declarations_missing": ("type", "LeaseState") not in baseline_decls and ("type", "TaskState") not in baseline_decls,
        "class_declaration_missing": ("class", "CredentialClass") not in baseline_decls,
        "lease_state_misclassified_external": baseline_classes.get("LeaseState") == "EXTERNAL_NOMINAL",
        "credential_class_misclassified_external": baseline_classes.get("CredentialClass") == "EXTERNAL_NOMINAL",
        "type_rhs_mutation_semantic_hash_blind": baseline_a["typed_ir_sha256"] == baseline_b["typed_ir_sha256"],
    }
    baseline_gap["reproduced"] = all(baseline_gap.values())

    candidate_fix = {
        "lease_type_preserved": ("type", "LeaseState") in candidate_decls,
        "task_type_preserved": ("type", "TaskState") in candidate_decls,
        "credential_class_preserved": ("class", "CredentialClass") in candidate_decls,
        "lease_state_declared_nominal": candidate_classes.get("LeaseState") == "DECLARED_NOMINAL",
        "credential_class_declared_nominal": candidate_classes.get("CredentialClass") == "DECLARED_NOMINAL",
        "type_rhs_mutation_changes_semantic_hash": candidate_a["typed_ir_sha256"] != candidate_b["typed_ir_sha256"],
        "any_not_introduced": "Any" not in candidate_classes,
        "declarations_mint_no_authority": all(d.get("authority") == "NONE" for d in candidate_a["declarations"]),
    }
    candidate_fix["pass"] = all(candidate_fix.values())

    atomic_program = structured.parse(ATOMIC_STRUCTURED_FIXTURE)
    atomic_validation = structured.validate(atomic_program)
    atomic_gap = {
        "structured_backend_version": structured.VERSION,
        "validation_pass": atomic_validation["pass"],
        "errors": atomic_validation["errors"],
        "expected_unknown_atomic_call_observed": "UNKNOWN_CALL:atomic_compare_and_set" in atomic_validation["errors"],
        "effect_authority_surface": atomic_validation["effect_authority_surface"],
    }
    atomic_gap["gap_reproduced"] = (
        not atomic_gap["validation_pass"]
        and atomic_gap["expected_unknown_atomic_call_observed"]
        and atomic_gap["effect_authority_surface"] == []
    )

    sqlite_control = _sqlite_reference_control()

    pass_value = (
        all(owner_anchors.values())
        and baseline_gap["reproduced"]
        and candidate_fix["pass"]
        and atomic_gap["gap_reproduced"]
        and sqlite_control["pass"]
    )
    output = {
        "schema_version": "1.0",
        "experiment": "CC_WP03_FRANK_SINGLE_SPAWN_TYPE_IDENTITY_AND_ATOMIC_BOUNDARY",
        "owner_directive": str(OWNER_DIRECTIVE.relative_to(ROOT)),
        "owner_directive_sha256": _sha256_text(owner_text),
        "owner_anchors": owner_anchors,
        "grammar_sha256": _sha256_text(GRAMMAR_PATH.read_text(encoding="utf-8")),
        "frontend_fixture_semantic_hash": artifact_a["semantic_hash"],
        "baseline_current_typed_ir": baseline_gap,
        "candidate_type_decl_ir": {
            **candidate_fix,
            "candidate_version": candidate.VERSION,
            "candidate_ir_schema": candidate.IR_SCHEMA,
            "semantic_id": candidate_a["program_semantic_id"],
        },
        "structured_atomic_boundary": atomic_gap,
        "sqlite_host_reference_control": sqlite_control,
        "result": "SUPPORTED_WP03_TYPE_DECL_IMPLEMENTATION_GAP_AND_SEPARATE_WP09_ATOMIC_RUNTIME_GAP",
        "architecture_decision": "NO_SURFACE_SEMANTIC_CHANGE; IMPLEMENT_ALREADY_ADMITTED_TYPE_CLASS_DECLARATIONS; KEEP_ATOMIC_CAS_AS_SEPARATE_RUNTIME_EFFECT_BOUNDARY",
        "scope_guard": "Experiment PASS is not CC-WP-03/WP-09/F-V01-02 or Frank-v0.1 promotion. Candidate is isolated until exact target-VPS receipt and production integration tests exist.",
        "pass": pass_value,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if pass_value else 1


if __name__ == "__main__":
    raise SystemExit(main())
