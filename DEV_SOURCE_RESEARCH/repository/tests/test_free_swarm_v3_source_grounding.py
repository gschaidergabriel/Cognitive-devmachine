import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_6000_free_swarm_v3 as v3  # noqa: E402


def _digest(capsule: str) -> str:
    match = re.search(r"full_file_sha256=([0-9a-f]{64})", capsule)
    assert match is not None
    return match.group(1)


def test_accelerator_is_installed_before_fabric_capture():
    assert v3.ACCELERATOR_BINDING == "FREE_SWARM_ACCELERATOR_V2_PRE_FABRIC"
    assert v3.fabric.base.worker_prompt is v3.source_grounded_worker_prompt
    prompt = v3._ORIGINAL_WORKER_PROMPT("PROTOCOL", "TESTER", "task", "state", 1)
    assert "ENTITYOS/HCU FREE-SWARM STATIC PRODUCTIVITY CONTRACT" in prompt
    assert "ready_for_forge=true" in prompt


def test_forge_shard_gets_exact_hash_bound_source_excerpt():
    capsule = v3._source_capsule_for_prompt("focus=forge candidate conversion")
    assert "status=BOUND_EXCERPT_ONLY" in capsule
    assert "path=tools/run_free_evidence_forge.py" in capsule
    assert "def validate_candidate" in capsule
    assert len(_digest(capsule)) == 64
    assert "ready_for_forge=true only if every modified hunk is grounded" in capsule


def test_jspace_shard_gets_current_intervention_probe_source():
    capsule = v3._source_capsule_for_prompt("focus=J-Space intervention controls")
    assert "path=tools/hcu_jspace_local_activation_probe.py" in capsule
    assert "def validate_atomic_claim" in capsule
    assert len(_digest(capsule)) == 64


def test_unmapped_shard_fails_closed_to_design_only():
    capsule = v3._source_capsule_for_prompt("focus=unmapped future shard")
    assert "status=NOT_SELECTED_FOR_THIS_SHARD" in capsule
    assert "ready_for_forge MUST remain false" in capsule


def test_v3_keeps_catalog_discovery_network_free():
    assert v3.fabric.opt.discover_and_export is v3.route_safe_discover_and_export
