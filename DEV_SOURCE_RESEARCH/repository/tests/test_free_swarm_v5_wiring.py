from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_fast_launcher_preserves_model_health_then_selects_v5():
    src = text("tools/run_6000_free_swarm_fast.py")
    assert "model_health.install_scheduler(fabric_v2)" in src
    assert "import run_6000_free_swarm_v5 as fabric" in src
    assert "model_health.bind_request_observer(fabric)" in src
    assert src.index("model_health.install_scheduler(fabric_v2)") < src.index(
        "import run_6000_free_swarm_v5 as fabric"
    )


def test_v5_preserves_v3_network_authority_and_replaces_only_execute_call():
    src = text("tools/run_6000_free_swarm_v5.py")
    assert "import run_6000_free_swarm_v3 as gated" in src
    assert "fabric = gated.fabric" in src
    assert "fabric.execute_call = execute_call" in src
    assert "base.request_chat" in src
    assert "git apply --check" in src


def test_activation_compiles_entire_v5_conversion_stack():
    src = text("tools/activate_6000_free_swarm.sh")
    for required in (
        "tools/free_swarm_model_health_v1.py",
        "tools/forge_source_rehydration.py",
        "tools/free_swarm_patch_pipeline.py",
        "tools/run_6000_free_swarm_v5.py",
        "tools/run_6000_free_swarm_fast.py",
    ):
        assert required in src
