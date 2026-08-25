#!/usr/bin/env python3
"""Fail-closed GO878 repair for the 6000 extraction-transport liveness gate.

The same 6000 fabric carries historical extraction. Pending extraction therefore
must keep that fabric alive, but it must not be mislabeled as permission to scale
ordinary raw generation. This patch changes only the local supervisor policy block
and its focused regression; provider admission/economic guards remain untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SUPERVISOR_REL = "tools/run_6000_free_swarm_supervisor.sh"
TEST_REL = "tests/test_go_878_raw_generation_backpressure.py"

OLD_GATE = """   pressure=ready+implementation+pending
   allowed=pressure < threshold
   status.update({
    'state':'OBSERVED',
    'ready_backlog':ready,
    'implementation_backlog':implementation,
    'pending_extraction':pending,
    'conversion_pressure':pressure,
    'action':'ALLOW_RAW_GENERATION' if allowed else 'PAUSE_RAW_GENERATION_BACKPRESSURE',
   })"""

NEW_GATE = """   raw_backlog_pressure=ready+implementation
   pressure=raw_backlog_pressure+pending
   extraction_transport_required=pending > 0
   allowed=extraction_transport_required or raw_backlog_pressure < threshold
   action=(
    'ALLOW_EXTRACTION_TRANSPORT' if extraction_transport_required
    else ('ALLOW_RAW_GENERATION' if allowed else 'PAUSE_RAW_GENERATION_BACKPRESSURE')
   )
   status.update({
    'state':'OBSERVED',
    'ready_backlog':ready,
    'implementation_backlog':implementation,
    'pending_extraction':pending,
    'raw_backlog_pressure':raw_backlog_pressure,
    'conversion_pressure':pressure,
    'extraction_transport_required':extraction_transport_required,
    'action':action,
   })"""

OLD_TEST_BELOW = """def test_pressure_below_threshold_allows_raw_generation(tmp_path: Path):
    candidates = [(1, \"NEW\")] * 2 + [(0, \"NEEDS_IMPLEMENTATION\")]
    proc, status = _run_gate(tmp_path, candidates=candidates, pending=1)
    assert proc.returncode == 0
    assert status[\"conversion_pressure\"] == 4
    assert status[\"action\"] == \"ALLOW_RAW_GENERATION\"
"""

NEW_TEST_BELOW = """def test_pressure_below_threshold_allows_raw_generation(tmp_path: Path):
    candidates = [(1, \"NEW\")] * 2 + [(0, \"NEEDS_IMPLEMENTATION\")]
    proc, status = _run_gate(tmp_path, candidates=candidates, pending=0)
    assert proc.returncode == 0
    assert status[\"raw_backlog_pressure\"] == 3
    assert status[\"conversion_pressure\"] == 3
    assert status[\"extraction_transport_required\"] is False
    assert status[\"action\"] == \"ALLOW_RAW_GENERATION\"
"""

OLD_PENDING_TEST = """@pytest.mark.xfail(
    strict=True,
    reason=(
        \"Supervisor 8.78 successor gate: pending historical extraction is carried by the \"
        \"6000 fabric, so pending-only pressure must not stop that extraction transport.\"
    ),
)
def test_pending_extraction_only_pressure_preserves_extraction_transport(tmp_path: Path):
    proc, status = _run_gate(tmp_path, candidates=[], pending=64)
    assert status[\"pending_extraction\"] == 64
    assert proc.returncode == 0
    assert status[\"action\"] == \"ALLOW_RAW_GENERATION\"
"""

NEW_PENDING_TEST = """def test_pending_extraction_only_pressure_preserves_extraction_transport(tmp_path: Path):
    proc, status = _run_gate(tmp_path, candidates=[], pending=64)
    assert status[\"pending_extraction\"] == 64
    assert status[\"raw_backlog_pressure\"] == 0
    assert status[\"extraction_transport_required\"] is True
    assert proc.returncode == 0
    assert status[\"action\"] == \"ALLOW_EXTRACTION_TRANSPORT\"


def test_pending_extraction_preserves_transport_even_with_ready_backpressure(tmp_path: Path):
    candidates = [(1, \"NEW\")] * 64
    proc, status = _run_gate(tmp_path, candidates=candidates, pending=1)
    assert status[\"raw_backlog_pressure\"] == 64
    assert status[\"pending_extraction\"] == 1
    assert status[\"extraction_transport_required\"] is True
    assert proc.returncode == 0
    assert status[\"action\"] == \"ALLOW_EXTRACTION_TRANSPORT\"
"""


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}_PREDECESSOR_MISMATCH:{count}")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    supervisor = repo / SUPERVISOR_REL
    tests = repo / TEST_REL
    s = supervisor.read_text(encoding="utf-8")
    t = tests.read_text(encoding="utf-8")
    s2 = replace_exact(s, OLD_GATE, NEW_GATE, "SUPERVISOR_GATE")
    t2 = replace_exact(t, OLD_TEST_BELOW, NEW_TEST_BELOW, "BELOW_THRESHOLD_TEST")
    t2 = replace_exact(t2, OLD_PENDING_TEST, NEW_PENDING_TEST, "PENDING_LIVENESS_TEST")
    supervisor.write_text(s2, encoding="utf-8")
    tests.write_text(t2, encoding="utf-8")
    print("GO878_EXTRACTION_TRANSPORT_LIVENESS_PATCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
