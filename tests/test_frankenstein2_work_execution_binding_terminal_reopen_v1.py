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


def test_late_result_cannot_reopen_completed_binding(tmp_path: Path) -> None:
    db = tmp_path / "binding.sqlite3"
    ledger = WorkExecutionLedger(db)

    ledger.bind_child(
        binding_id="b1",
        workpackage_id="wp1",
        work_generation="g1",
        child_runtime_kind="TEST_NATIVE_CHILD",
        child_execution_id="child-1",
        identity_provenance="deterministic-test-fixture",
    )
    ledger.record_invocation(
        binding_id="b1",
        invocation_id="inv-winner",
        invocation_kind="TEST_CALL",
        request={"lane": "winner"},
    )
    ledger.record_invocation(
        binding_id="b1",
        invocation_id="inv-late",
        invocation_kind="TEST_CALL",
        request={"lane": "late"},
    )
    ledger.record_result(
        result_id="result-winner",
        binding_id="b1",
        invocation_id="inv-winner",
        outcome="SUCCESS",
        result={"ok": True},
        result_provenance="deterministic-test-fixture",
    )
    ledger.verify_completion(
        completion_id="completion-winner",
        binding_id="b1",
        invocation_id="inv-winner",
        result_id="result-winner",
        expected_work_generation="g1",
        evidence_kind="DETERMINISTIC_TEST_RECEIPT",
        evidence_ref="fixture://winner",
        evidence_payload={"verified": True},
    )
    assert _status(db, "b1") == "COMPLETED"

    with pytest.raises(ValueError, match="binding is terminal: COMPLETED"):
        ledger.record_result(
            result_id="result-late",
            binding_id="b1",
            invocation_id="inv-late",
            outcome="SUCCESS",
            result={"ok": True, "late": True},
            result_provenance="deterministic-test-fixture",
        )

    assert _status(db, "b1") == "COMPLETED"

    con = sqlite3.connect(str(db))
    try:
        late_count = con.execute(
            "SELECT COUNT(*) FROM fr2_work_results WHERE result_id='result-late'"
        ).fetchone()[0]
    finally:
        con.close()
    assert late_count == 0
