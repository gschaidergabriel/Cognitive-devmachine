import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_6000_free_swarm_v3 as v3  # noqa: E402


def test_accelerator_is_installed_before_fabric_capture():
    assert v3.ACCELERATOR_BINDING == "FREE_SWARM_ACCELERATOR_V2_PRE_FABRIC"
    prompt = v3.fabric.base.worker_prompt("PROTOCOL", "HCU_CAUSAL", "task", "state", 7)
    assert prompt.startswith("PROTOCOL")
    assert "ENTITYOS/HCU FREE-SWARM STATIC PRODUCTIVITY CONTRACT" in prompt
    assert "ready_for_forge=true is STRICT" in prompt
    assert "A proposal with an empty patch is DESIGN-ONLY" in prompt


def test_template_never_labels_empty_patch_as_forge_ready():
    prompt = v3.fabric.base.worker_prompt("P", "JSPACE_CAUSAL", "task", "state", 9)
    marker = "ARCHITECTURE_DELTA_JSON="
    line = next(x for x in prompt.splitlines() if x.startswith(marker))
    assert '"patch_unified_diff":""' in line
    assert '"target_files":[]' in line
    assert '"test_commands":[]' in line
    assert '"ready_for_forge":false' in line


def test_v3_keeps_catalog_discovery_network_free():
    report_fn = v3.fabric.opt.discover_and_export
    assert report_fn is v3.route_safe_discover_and_export
