from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def test_kubernetes_inplace_pod_restart_is_never_tier2():
    text = CONTRACT.read_text()
    assert "RestartAllContainers" in text
    assert "PodRestartInPlace" in text
    assert "preserving the Pod UID" in text
    assert "old Kata sandbox/VM identity is intentionally retained" in text
    assert "Tier-1/component recovery only" in text
    assert "MUST NOT be credited as Tier-2" in text


def test_tier2_still_requires_new_pod_and_sandbox_identity():
    text = CONTRACT.read_text()
    assert "old Pod UID and old Kata sandbox/VM identity are terminal" in text
    assert "new Pod UID and new sandbox/VM identity are observed" in text
    assert "TIER2_REPLACEMENT_BLOCKED" in text
