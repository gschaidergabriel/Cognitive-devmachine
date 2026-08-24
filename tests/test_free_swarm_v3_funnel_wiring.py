import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_6000_free_swarm_v3 as v3  # noqa: E402


def _proposal():
    return {
        "delta_id": "worker-1-jspace-control",
        "hypothesis": "matched controls separate steering from schema recurrence",
        "mechanism": "add a sham control trace",
        "target_files": ["tests/test_jspace_control.py"],
        "patch_unified_diff": "--- /dev/null\n+++ b/tests/test_jspace_control.py\n@@ -0,0 +1 @@\n+def test_control(): assert True\n",
        "test_commands": ["python -m pytest -q tests/test_jspace_control.py"],
        "benchmark_command": "",
        "metric": "control_family_complete",
        "expected_direction": "boolean",
        "baseline_needed": True,
        "falsifier": "target and sham remain indistinguishable",
        "risk": "source-only trace overclaim",
        "ready_for_forge": True,
    }


def test_accelerator_is_bound_before_fabric_prompt_capture():
    assert v3.ACCELERATOR_BINDING == "FREE_SWARM_ACCELERATOR_V2_PRE_FABRIC"
    prompt = v3.fabric.base.worker_prompt("PROTOCOL", "HCU_CAUSAL", "task", "state", 1)
    assert prompt.startswith("PROTOCOL")
    assert "ENTITYOS/HCU FREE-SWARM STATIC PRODUCTIVITY CONTRACT" in prompt
    assert "6000-WORKER FABRIC SHARD" in prompt
    assert "ARCHITECTURE_DELTA_JSON=" in prompt


def test_successful_worker_is_typed_and_materialized(tmp_path):
    sink = v3.fabric.base.JsonlSink(tmp_path)
    proposal = _proposal()
    text = (
        "DEUTSCHE_ZUSAMMENFASSUNG\n"
        "ARCHITECTURE_DELTA_JSON=" + json.dumps(proposal) + "\n"
        "OPEN_RESEARCH_QUESTIONS_JSON=[\"Does the sham preserve output identity?\"]"
    )
    row = {
        "schema": "CLAY_FREE_GO_SWARM_WORKER/v2",
        "ts": "2026-08-24T00:00:00+00:00",
        "provider": "test",
        "model": "test-model",
        "role": "HCU_CAUSAL",
        "worker_serial": 1,
        "logical_worker_slot": 0,
        "repo_head_at_prompt": "deadbeef",
        "http_status": 200,
        "text": text,
        "text_sha256": "worker-sha",
    }
    asyncio.run(sink.append(row))

    worker = json.loads((tmp_path / "workers.jsonl").read_text(encoding="utf-8").strip())
    assert worker["delta_ingress"]["status"] == "VALID_READY"
    assert worker["delta_ingress"]["ready_for_forge"] is True

    candidate = json.loads((tmp_path / "architecture_deltas.jsonl").read_text(encoding="utf-8").strip())
    assert candidate["schema"] == "CLAY_ARCHITECTURE_DELTA_CANDIDATE/v1"
    assert candidate["proposal"]["delta_id"] == proposal["delta_id"]
    assert candidate["ready_for_forge"] is True

    questions = json.loads((tmp_path / "open_research_questions.jsonl").read_text(encoding="utf-8").strip())
    assert questions["questions"] == ["Does the sham preserve output identity?"]
