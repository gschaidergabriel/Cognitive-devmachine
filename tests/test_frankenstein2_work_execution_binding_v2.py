from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "frankenstein2_work_execution_binding_v2.py"
SPEC = importlib.util.spec_from_file_location("frankenstein2_work_execution_binding_v2", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

WorkExecutionLedger = mod.WorkExecutionLedger
LegacyLedger = mod.v1.WorkExecutionLedger


def _row(db_path: Path, sql: str, args: tuple[object, ...] = ()) -> sqlite3.Row:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(sql, args).fetchone()
        assert row is not None
        return row
    finally:
        con.close()


def _count(db_path: Path, table: str, where: str = "1=1", args: tuple[object, ...] = ()) -> int:
    return int(_row(db_path, f"SELECT COUNT(*) AS n FROM {table} WHERE {where}", args)["n"])


def _bind(ledger, binding: str = "b1") -> None:
    ledger.bind_child(
        binding_id=binding,
        workpackage_id="wp1",
        work_generation="g1",
        child_runtime_kind="TEST_NATIVE_CHILD",
        child_execution_id="child-1",
        identity_provenance="deterministic-test-fixture",
    )


def _invoke(ledger, invocation: str, binding: str = "b1") -> None:
    ledger.record_invocation(
        binding_id=binding,
        invocation_id=invocation,
        invocation_kind="TEST_CALL",
        request={"binding": binding, "invocation": invocation},
    )


def _result(ledger, invocation: str, result: str, outcome: str = "SUCCESS", binding: str = "b1") -> None:
    ledger.record_result(
        result_id=result,
        binding_id=binding,
        invocation_id=invocation,
        outcome=outcome,
        result={"result_id": result, "outcome": outcome},
        result_provenance="deterministic-test-fixture",
    )


def _complete(ledger, invocation: str, result: str, completion: str = "c1", binding: str = "b1") -> str:
    return ledger.verify_completion(
        completion_id=completion,
        binding_id=binding,
        invocation_id=invocation,
        result_id=result,
        expected_work_generation="g1",
        evidence_kind="DETERMINISTIC_TEST_RECEIPT",
        evidence_ref=f"fixture://{completion}",
        evidence_payload={"verified": True, "binding": binding, "result": result},
    )


def test_completion_fails_closed_while_any_invocation_is_unresolved(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)
    _bind(ledger)
    _invoke(ledger, "inv-1")
    _invoke(ledger, "inv-2")
    _result(ledger, "inv-1", "r1")

    with pytest.raises(ValueError, match="UNRESOLVED_INVOCATIONS:1"):
        _complete(ledger, "inv-1", "r1")

    assert _count(db, "fr2_completion_evidence") == 0
    assert _row(
        db,
        "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'",
    )["status"] == "RESULT_OBSERVED"


def test_completion_succeeds_after_all_invocations_are_resolved(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)
    _bind(ledger)
    _invoke(ledger, "inv-1")
    _invoke(ledger, "inv-2")
    _result(ledger, "inv-1", "r1")
    _result(ledger, "inv-2", "r2")

    digest = _complete(ledger, "inv-2", "r2")

    assert len(digest) == 64
    assert _row(
        db,
        "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'",
    )["status"] == "COMPLETED"
    assert _count(db, "fr2_completion_evidence", "binding_id=?", ("b1",)) == 1


def test_unknown_prior_invocation_blocks_later_success_completion(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)
    _bind(ledger)
    _invoke(ledger, "inv-1")
    _invoke(ledger, "inv-2")
    _result(ledger, "inv-1", "r1", outcome="UNKNOWN")
    _result(ledger, "inv-2", "r2", outcome="SUCCESS")

    with pytest.raises(ValueError, match="UNKNOWN_INVOCATION_OUTCOME:1"):
        _complete(ledger, "inv-2", "r2")

    assert _count(db, "fr2_completion_evidence") == 0


def test_late_result_cannot_regress_a_legacy_terminal_binding(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)
    _bind(ledger)
    _invoke(ledger, "inv-1")
    _invoke(ledger, "inv-2")
    _result(ledger, "inv-1", "r1")

    # Simulate the exact legacy/racy terminal shape v2 is designed to hard-off:
    # a binding was marked complete while a second invocation remained in flight.
    con = sqlite3.connect(str(db))
    try:
        con.execute("UPDATE fr2_work_execution_bindings SET status='COMPLETED' WHERE binding_id='b1'")
        con.commit()
    finally:
        con.close()

    with pytest.raises(ValueError, match="binding is terminal: COMPLETED"):
        _result(ledger, "inv-2", "r2")

    assert _count(db, "fr2_work_results", "result_id=?", ("r2",)) == 0
    assert _row(
        db,
        "SELECT status FROM fr2_work_execution_bindings WHERE binding_id='b1'",
    )["status"] == "COMPLETED"


def test_second_completion_of_same_binding_is_forbidden(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)
    _bind(ledger)
    _invoke(ledger, "inv-1")
    _result(ledger, "inv-1", "r1")
    _complete(ledger, "inv-1", "r1", completion="c1")

    with pytest.raises(ValueError, match="binding is terminal: COMPLETED"):
        _complete(ledger, "inv-1", "r1", completion="c2")

    assert _count(db, "fr2_completion_evidence", "binding_id=?", ("b1",)) == 1


def test_v2_refuses_legacy_database_with_multiple_completions(tmp_path: Path) -> None:
    db = tmp_path / "legacy.sqlite3"
    legacy = LegacyLedger(db)
    _bind(legacy)
    _invoke(legacy, "inv-1")
    _invoke(legacy, "inv-2")
    _result(legacy, "inv-1", "r1")
    _complete(legacy, "inv-1", "r1", completion="c1")

    # v1 permits the terminal regression: a late result reopens the binding, then a
    # second completion can be minted. Preserve this as a migration falsifier.
    _result(legacy, "inv-2", "r2")
    _complete(legacy, "inv-2", "r2", completion="c2")
    assert _count(db, "fr2_completion_evidence", "binding_id=?", ("b1",)) == 2

    with pytest.raises(
        ValueError,
        match="LEGACY_MULTIPLE_COMPLETIONS_REQUIRE_RECONCILIATION:b1:2",
    ):
        WorkExecutionLedger(db)
