from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "frankenstein2_work_execution_binding_v2.py"
SPEC = importlib.util.spec_from_file_location(
    "frankenstein2_work_execution_binding_v2_unknown_replay_test",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

WorkExecutionLedger = mod.WorkExecutionLedger


def _status(db_path: Path, binding_id: str) -> str:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
            (binding_id,),
        ).fetchone()
        assert row is not None
        return str(row[0])
    finally:
        con.close()


def _invocation_count(db_path: Path, binding_id: str) -> int:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT COUNT(*) FROM fr2_work_invocations WHERE binding_id=?",
            (binding_id,),
        ).fetchone()
        assert row is not None
        return int(row[0])
    finally:
        con.close()


def _bind(ledger: WorkExecutionLedger, binding_id: str, child_id: str) -> None:
    ledger.bind_child(
        binding_id=binding_id,
        workpackage_id=f"wp-{binding_id}",
        work_generation="g1",
        child_runtime_kind="TEST_NATIVE_CHILD",
        child_execution_id=child_id,
        identity_provenance="deterministic-test-fixture",
    )


def _invoke(ledger: WorkExecutionLedger, binding_id: str, invocation_id: str) -> None:
    ledger.record_invocation(
        binding_id=binding_id,
        invocation_id=invocation_id,
        invocation_kind="TEST_CALL",
        request={"binding": binding_id, "invocation": invocation_id},
    )


def test_unknown_outcome_blocks_new_invocation_on_same_binding_generation(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)
    _bind(ledger, "b1", "child-1")
    _invoke(ledger, "b1", "inv-1")
    ledger.record_result(
        result_id="r1",
        binding_id="b1",
        invocation_id="inv-1",
        outcome="UNKNOWN",
        result={"transport": "lost-after-submit"},
        result_provenance="deterministic-test-fixture",
    )

    assert _status(db, "b1") == "UNKNOWN_OUTCOME"
    assert _invocation_count(db, "b1") == 1

    with pytest.raises(ValueError, match="UNKNOWN_OUTCOME_REQUIRES_RECONCILIATION"):
        _invoke(ledger, "b1", "inv-2")

    assert _status(db, "b1") == "UNKNOWN_OUTCOME"
    assert _invocation_count(db, "b1") == 1


def test_unknown_outcome_fence_is_binding_scoped_not_global(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)
    _bind(ledger, "b1", "child-1")
    _invoke(ledger, "b1", "inv-1")
    ledger.record_result(
        result_id="r1",
        binding_id="b1",
        invocation_id="inv-1",
        outcome="UNKNOWN",
        result={"transport": "lost-after-submit"},
        result_provenance="deterministic-test-fixture",
    )

    _bind(ledger, "b2", "child-2")
    _invoke(ledger, "b2", "inv-2")

    assert _status(db, "b1") == "UNKNOWN_OUTCOME"
    assert _status(db, "b2") == "RUNNING"
    assert _invocation_count(db, "b1") == 1
    assert _invocation_count(db, "b2") == 1
