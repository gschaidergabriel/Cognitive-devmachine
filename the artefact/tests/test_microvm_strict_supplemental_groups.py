from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def _statefulset(text: str) -> str:
    return next(doc for doc in text.split("\n---\n") if "kind: StatefulSet" in doc)


def test_kata_profile_fails_closed_on_implicit_image_groups():
    text = TEMPLATE.read_text()
    stateful = _statefulset(text)
    assert "fsGroup: 10001" in stateful
    assert 'fsGroupChangePolicy: "OnRootMismatch"' in stateful
    assert "supplementalGroupsPolicy: Strict" in stateful
    assert "supplementalGroupsPolicy: Merge" not in stateful
    assert "runAsNonRoot: true" in stateful
    assert "runAsUser: 10001" in stateful
    assert "runAsGroup: 10001" in stateful
    assert "type: RuntimeDefault" in stateful
    assert 'drop: ["ALL"]' in stateful
    assert "mountPath: /var/lib/clayverse" in stateful
    assert "mountPath: /workspace" in stateful
    assert 'accessModes: ["ReadWriteOncePod"]' in stateful
    assert "initContainers:" not in stateful
    assert "privileged: true" not in stateful
    assert text.count('accessModes: ["ReadWriteOncePod"]') == 2


def test_strict_group_fence_preserves_adjacent_microvm_contracts():
    text = CONTRACT.read_text()
    assert "VOLUME_MOUNT_GROUP" in text
    assert "ReadWriteOncePod" in text
    assert "TIER2_REPLACEMENT_BLOCKED" in text
    assert "RestartAllContainers" in text
    assert "PodRestartInPlace" in text
    assert "io.katacontainers.*" in text
    assert "NetworkPolicy" in text
