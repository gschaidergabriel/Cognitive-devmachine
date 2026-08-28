from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "frankenstein2_work_execution_binding_v1.py"
SPEC = importlib.util.spec_from_file_location("frankenstein2_work_execution_binding_v1", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

WorkExecutionLedger = mod.WorkExecutionLedger


def _row(db_path: Path, sql: str, args: tuple[object, ...] = ()) -> sqlite3.Row:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(sql, args).fetchone()
        assert row is not None
        return row
    finally:
        con.close()


def _bind(ledger: WorkExecutionLedger, *, binding: str, package: str, generation: str, child: str) -> None:
    ledger.bind_child(
        binding_id=binding,
        workpackage_id=package,
        work_generation=generation,
        child_runtime_kind="TEST_NATIVE_CHILD",
        child_execution_id=child,
        identity_provenance="deterministic-test-fixture",
    )


def _invoke(ledger: WorkExecutionLedger, *, binding: str, invocation: str) -> None:
    ledger.record_invocation(
        binding_id=binding,
        invocation_id=invocation,
        invocation_kind="TEST_CALL",
        request={"binding": binding, "invocation": invocation},
    )


def _result(
    ledger: WorkExecutionLedger,
    *,
    binding: str,
    invocation: str,
    result: str,
    outcome: str,
) -> None:
    ledger.record_result(
        result_id=result,
        binding_id=binding,
        invocation_id=invocation,
        outcome=outcome,
        result={"result_id": result, "outcome": outcome},
        result_provenance="deterministic-test-fixture",
    )


def test_nullable_native_ids_are_not_invented(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    _bind(ledger, binding="b1", package="wp1", generation="g1", child="child-exec-1")

    row = _row(
        db,
        "SELECT native_agent_id,native_task_id,status FROM fr2_work_execution_bindings WHERE binding_id=?",
        ("b1",),
    )
    assert row["native_agent_id"] is None
    assert row["native_task_id"] is None
    assert row["status"] == "BOUND"


def test_task_and_agent_identity_namespaces_remain_distinct(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    ledger.bind_child(
        binding_id="b1",
        workpackage_id="wp1",
        work_generation="g1",
        child_runtime_kind="TEST_NATIVE_CHILD",
        child_execution_id="child-exec-1",
        identity_provenance="observed-fixture",
        native_agent_id="agent-17",
        native_task_id="task-17",
    )

    row = _row(
        db,
        "SELECT native_agent_id,native_task_id FROM fr2_work_execution_bindings WHERE binding_id=?",
        ("b1",),
    )
    assert row["native_agent_id"] == "agent-17"
    assert row["native_task_id"] == "task-17"
    assert row["native_agent_id"] != row["native_task_id"]


def test_result_cross_talk_between_bindings_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    _bind(ledger, binding="b1", package="wp1", generation="g1", child="child-1")
    _bind(ledger, binding="b2", package="wp2", generation="g1", child="child-2")
    _invoke(ledger, binding="b1", invocation="inv-1")
    _invoke(ledger, binding="b2", invocation="inv-2")

    with pytest.raises(ValueError, match="result does not bind"):
        _result(
            ledger,
            binding="b1",
            invocation="inv-2",
            result="result-cross-talk",
            outcome="SUCCESS",
        )

    assert _row(
        db,
        "SELECT COUNT(*) AS n FROM fr2_work_results WHERE result_id=?",
        ("result-cross-talk",),
    )["n"] == 0


def test_unknown_outcome_never_becomes_completion(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    _bind(ledger, binding="b1", package="wp1", generation="g1", child="child-1")
    _invoke(ledger, binding="b1", invocation="inv-1")
    _result(ledger, binding="b1", invocation="inv-1", result="r1", outcome="UNKNOWN")

    assert _row(
        db,
        "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
        ("b1",),
    )["status"] == "UNKNOWN_OUTCOME"

    with pytest.raises(ValueError, match="completion forbidden for outcome=UNKNOWN"):
        ledger.verify_completion(
            completion_id="c1",
            binding_id="b1",
            invocation_id="inv-1",
            result_id="r1",
            expected_work_generation="g1",
            evidence_kind="DETERMINISTIC_TEST_RECEIPT",
            evidence_ref="fixture://unknown-must-not-complete",
            evidence_payload={"verified": False},
        )


def test_stale_generation_cannot_close_success(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    _bind(ledger, binding="b1", package="wp1", generation="g2", child="child-1")
    _invoke(ledger, binding="b1", invocation="inv-1")
    _result(ledger, binding="b1", invocation="inv-1", result="r1", outcome="SUCCESS")

    with pytest.raises(ValueError, match="STALE_WORK_GENERATION"):
        ledger.verify_completion(
            completion_id="c1",
            binding_id="b1",
            invocation_id="inv-1",
            result_id="r1",
            expected_work_generation="g1",
            evidence_kind="DETERMINISTIC_TEST_RECEIPT",
            evidence_ref="fixture://stale",
            evidence_payload={"generation": "g1"},
        )

    assert _row(
        db,
        "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
        ("b1",),
    )["status"] == "RESULT_OBSERVED"


def test_textual_claim_is_not_mechanistic_completion_evidence(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    _bind(ledger, binding="b1", package="wp1", generation="g1", child="child-1")
    _invoke(ledger, binding="b1", invocation="inv-1")
    _result(ledger, binding="b1", invocation="inv-1", result="r1", outcome="SUCCESS")

    with pytest.raises(ValueError, match="mechanistic evidence"):
        ledger.verify_completion(
            completion_id="c1",
            binding_id="b1",
            invocation_id="inv-1",
            result_id="r1",
            expected_work_generation="g1",
            evidence_kind="MODEL_TEXT_CLAIM",
            evidence_ref="fixture://text-only",
            evidence_payload={"text": "done"},
        )


def test_exact_success_plus_mechanistic_evidence_can_close_binding(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    _bind(ledger, binding="b1", package="wp1", generation="g1", child="child-1")
    _invoke(ledger, binding="b1", invocation="inv-1")
    _result(ledger, binding="b1", invocation="inv-1", result="r1", outcome="SUCCESS")

    digest = ledger.verify_completion(
        completion_id="c1",
        binding_id="b1",
        invocation_id="inv-1",
        result_id="r1",
        expected_work_generation="g1",
        evidence_kind="DETERMINISTIC_TEST_RECEIPT",
        evidence_ref="fixture://verified",
        evidence_payload={"test": "pass", "identity": "b1/inv-1/r1/g1"},
    )

    assert len(digest) == 64
    assert _row(
        db,
        "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
        ("b1",),
    )["status"] == "COMPLETED"
    completion = _row(
        db,
        "SELECT binding_id,invocation_id,result_id,evidence_kind FROM fr2_completion_evidence WHERE completion_id=?",
        ("c1",),
    )
    assert dict(completion) == {
        "binding_id": "b1",
        "invocation_id": "inv-1",
        "result_id": "r1",
        "evidence_kind": "DETERMINISTIC_TEST_RECEIPT",
    }
