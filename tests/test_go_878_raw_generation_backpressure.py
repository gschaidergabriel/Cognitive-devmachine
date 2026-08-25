from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

SUPERVISOR = Path(__file__).resolve().parents[1] / "tools" / "run_6000_free_swarm_supervisor.sh"


def _embedded_gate(tmp_path: Path) -> str:
    text = SUPERVISOR.read_text(encoding="utf-8")
    assert "fabric_generation_allowed(){" in text
    tail = text.split("fabric_generation_allowed(){", 1)[1]
    block = tail.split("python3 - <<'PY'\n", 1)[1].split("\nPY\n}", 1)[0]
    needle = "state_root=Path('/artifacts/clay-entityos-swarm')"
    assert block.count(needle) == 1
    return block.replace(needle, f"state_root=Path({str(tmp_path)!r})", 1)


def _run_gate(tmp_path: Path, *, candidates: list[tuple[int, str]] | None, pending: int = 0):
    forge = tmp_path / "forge"
    forge.mkdir(parents=True, exist_ok=True)
    if candidates is not None:
        db = forge / "forge.sqlite3"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE candidates(ready INTEGER NOT NULL, state TEXT NOT NULL)")
        con.executemany("INSERT INTO candidates(ready,state) VALUES(?,?)", candidates)
        if pending:
            con.execute("CREATE TABLE historical_chunks(state TEXT NOT NULL)")
            con.executemany(
                "INSERT INTO historical_chunks(state) VALUES(?)",
                [("PENDING_EXTRACTION",)] * pending,
            )
        con.commit()
        con.close()
    code = _embedded_gate(tmp_path)
    proc = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True)
    status = json.loads((tmp_path / "RAW_GENERATION_BACKPRESSURE.json").read_text(encoding="utf-8"))
    return proc, status


def test_control_loop_is_gated_and_credential_blind():
    text = SUPERVISOR.read_text(encoding="utf-8")
    assert "fabric_generation_allowed(){" in text
    assert "if fabric_generation_allowed; then" in text
    assert "'external_provider_calls':0" in text
    assert "'credentials_read':False" in text
    assert "CLAY_SWARM_RAW_GENERATION_BACKPRESSURE/v2" in text
    assert "PENDING_EXTRACTION_NEVER_SELF_STOPS_EXTRACTION_TRANSPORT" in text


def test_missing_forge_db_pauses_fail_closed(tmp_path: Path):
    proc, status = _run_gate(tmp_path, candidates=None)
    assert proc.returncode == 1
    assert status["state"] == "UNKNOWN_FORGE_DB"
    assert status["action"] == "PAUSE_FABRIC_FAIL_CLOSED"


def test_ready_plus_implementation_pressure_at_threshold_pauses_when_no_extraction_remains(tmp_path: Path):
    candidates = [(1, "NEW")] * 40 + [(0, "NEEDS_IMPLEMENTATION")] * 24
    proc, status = _run_gate(tmp_path, candidates=candidates, pending=0)
    assert proc.returncode == 1
    assert status["conversion_pressure"] == 64
    assert status["pending_extraction"] == 0
    assert status["extraction_transport_required"] is False
    assert status["action"] == "PAUSE_RAW_GENERATION_BACKPRESSURE"


def test_pressure_below_threshold_allows_raw_generation_when_no_extraction_remains(tmp_path: Path):
    candidates = [(1, "NEW")] * 2 + [(0, "NEEDS_IMPLEMENTATION")]
    proc, status = _run_gate(tmp_path, candidates=candidates, pending=0)
    assert proc.returncode == 0
    assert status["conversion_pressure"] == 3
    assert status["pending_extraction"] == 0
    assert status["action"] == "ALLOW_RAW_GENERATION"


def test_pending_extraction_only_pressure_preserves_extraction_transport(tmp_path: Path):
    proc, status = _run_gate(tmp_path, candidates=[], pending=64)
    assert status["pending_extraction"] == 64
    assert status["conversion_pressure"] == 0
    assert status["total_backlog_observed"] == 64
    assert status["extraction_transport_required"] is True
    assert proc.returncode == 0
    assert status["action"] == "KEEP_EXTRACTION_TRANSPORT_ALIVE"


def test_pending_extraction_overrides_candidate_stop_pressure_only_for_transport_liveness(tmp_path: Path):
    candidates = [(1, "NEW")] * 40 + [(0, "NEEDS_IMPLEMENTATION")] * 24
    proc, status = _run_gate(tmp_path, candidates=candidates, pending=1)
    assert status["conversion_pressure"] == 64
    assert status["pending_extraction"] == 1
    assert status["total_backlog_observed"] == 65
    assert status["extraction_transport_required"] is True
    assert proc.returncode == 0
    assert status["action"] == "KEEP_EXTRACTION_TRANSPORT_ALIVE"
