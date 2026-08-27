from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUP = ROOT / "tools" / "run_6000_free_swarm_supervisor.sh"


def _text() -> str:
    return SUP.read_text(encoding="utf-8")


def test_raw_generation_pressure_is_observed_fail_closed() -> None:
    text = _text()
    assert "raw_generation_allowed(){" in text
    assert "CLAY_SWARM_RAW_GENERATION_BACKPRESSURE/v1" in text
    assert "PAUSE_RAW_GENERATION_FAIL_CLOSED" in text
    assert "PAUSE_RAW_GENERATION_BACKPRESSURE" in text
    # Do not lock a specific process-stop policy here. The 6000 fabric also carries
    # historical extraction, so transport liveness must remain independently testable.


def test_backlog_first_forge_remains_single_active_entrypoint() -> None:
    text = _text()
    block = text.split("start_forge(){", 1)[1].split("refresh_root_results(){", 1)[0]
    assert 'local x="$ROOT/tools/run_free_evidence_forge_backfill.py"' in block
    assert 'local x="$ROOT/tools/run_free_evidence_forge_safe.py"' not in block
    assert "pgrep -f '[r]un_free_evidence_forge_backfill.py'" in block
