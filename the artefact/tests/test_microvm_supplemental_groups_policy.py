from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"


def _statefulset(text: str) -> str:
    return next(doc for doc in text.split("\n---\n") if "kind: StatefulSet" in doc)


def test_microvm_pod_identity_is_manifest_bounded_for_persistent_volumes():
    stateful = _statefulset(TEMPLATE.read_text())

    assert "fsGroup: 10001" in stateful
    assert 'fsGroupChangePolicy: "OnRootMismatch"' in stateful
    assert "supplementalGroupsPolicy: Strict" in stateful
    assert "runAsNonRoot: true" in stateful
    assert "runAsUser: 10001" in stateful
    assert "runAsGroup: 10001" in stateful
    assert 'drop: ["ALL"]' in stateful
    assert "mountPath: /var/lib/clayverse" in stateful
    assert "mountPath: /workspace" in stateful
    assert 'accessModes: ["ReadWriteOncePod"]' in stateful
    assert "initContainers:" not in stateful
    assert "privileged: true" not in stateful
