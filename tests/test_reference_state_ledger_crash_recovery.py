from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from research_entity.harness.reference_state_ledger import Mutation, StateLedger


PROV = {
    "origin_actor": "chatgpt-secondary",
    "research_entity": "frank-project-global-research-entity",
    "target": "FRANK H1 reference harness",
    "source_ref": "H-WP-02-crash-probe",
}


def seeded(tmp_path: Path) -> tuple[StateLedger, dict]:
    l = StateLedger(tmp_path / "ledger.sqlite")
    receipt = l.commit(
        event_id="seed-e1",
        idempotency_key="seed-k1",
        base_epoch=0,
        event_type="SEED",
        mutations=[Mutation("world", "x", 1)],
        provenance=PROV,
        committed_at="2026-08-09T10:03:00Z",
        writer_node="seed",
    )
    return l, receipt


def abrupt_probe(db_path: Path, point: str, cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "research_entity.harness.reference_state_ledger_crash_probe",
            str(db_path),
            point,
        ],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("point", ["AFTER_STATE", "AFTER_EVENT", "AFTER_EPOCH"])
def test_abrupt_process_death_rolls_back_entire_uncommitted_transaction(tmp_path, point):
    root = Path(__file__).resolve().parents[1]
    ledger, seed = seeded(tmp_path)
    db_path = ledger.path
    ledger.close()

    result = abrupt_probe(db_path, point, root)
    assert result.returncode != 0

    reopened = StateLedger(db_path)
    assert reopened.head()["epoch"] == seed["epoch"] == 1
    assert reopened.head()["root_hash"] == seed["root_hash"]
    assert reopened.read("world", "x")["value"] == 1
    assert reopened.read("world", "x")["epistemic_state"] == "KNOWN"
    assert reopened.db.execute("SELECT COUNT(*) FROM ledger_events WHERE event_id='crash-event'").fetchone()[0] == 0
    assert reopened.db.execute("SELECT COUNT(*) FROM ledger_epochs WHERE epoch=2").fetchone()[0] == 0
    assert reopened.verify()["status"] == "PASS"


def test_retry_after_crash_commits_exactly_once(tmp_path):
    root = Path(__file__).resolve().parents[1]
    ledger, seed = seeded(tmp_path)
    db_path = ledger.path
    ledger.close()

    result = abrupt_probe(db_path, "AFTER_EVENT", root)
    assert result.returncode != 0

    reopened = StateLedger(db_path)
    committed = reopened.commit(
        event_id="post-crash-e2",
        idempotency_key="post-crash-k2",
        base_epoch=seed["epoch"],
        event_type="RECOVERY_RETRY",
        mutations=[Mutation("world", "x", 2)],
        provenance=PROV,
        committed_at="2026-08-09T10:03:01Z",
        writer_node="recovery",
    )
    replay = reopened.commit(
        event_id="post-crash-e2",
        idempotency_key="post-crash-k2",
        base_epoch=seed["epoch"],
        event_type="RECOVERY_RETRY",
        mutations=[Mutation("world", "x", 2)],
        provenance=PROV,
        committed_at="2026-08-09T10:03:01Z",
        writer_node="recovery",
    )
    assert committed["epoch"] == 2
    assert replay["status"] == "IDEMPOTENT_REPLAY"
    assert reopened.head()["epoch"] == 2
    assert reopened.read("world", "x")["value"] == 2
    assert reopened.verify()["status"] == "PASS"
