from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_6000_free_swarm_supervisor.sh"
SCHEDULER = ROOT / "tools/free_swarm_backfill_scheduler.py"


def _control_loop(text: str) -> str:
    marker = "while (( $(date +%s) < DEADLINE )); do"
    start = text.index(marker)
    end = text.index("  NOW=$(date +%s); REMAINING=$((DEADLINE-NOW))", start)
    return text[start:end]


def test_conversion_pressure_never_kills_shared_extraction_fabric() -> None:
    text = SUPERVISOR.read_text(encoding="utf-8")
    loop = _control_loop(text)

    # raw_generation_allowed remains a credential-blind pressure/telemetry probe,
    # but the shared process must stay alive because it also carries historical
    # extraction. Process-level stop on pressure would deadlock pending extraction.
    assert "raw_generation_allowed || true" in loop
    assert "start_6000" in loop
    assert "else\n    stop_6000" not in loop


def test_slot_level_scheduler_owns_raw_suppression_during_backfill() -> None:
    text = SCHEDULER.read_text(encoding="utf-8")

    # Every reservable slot is conversion-first. Ordinary raw prompting is reached
    # only when no historical packet can be reserved.
    assert "packet = _reserve(serial)" in text
    assert "if packet is None:\n            return original" in text
    assert "if serial % 4 == 0" not in text
    assert "HISTORICAL FREE-SWARM BACKFILL OVERRIDE" in text
