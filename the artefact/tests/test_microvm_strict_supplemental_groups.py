from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def test_kata_profile_fails_closed_on_implicit_image_groups():
    text = TEMPLATE.read_text()
    assert "fsGroup: 10001" in text
    assert 'fsGroupChangePolicy: "OnRootMismatch"' in text
    assert "supplementalGroupsPolicy: Strict" in text
    assert "supplementalGroupsPolicy: Merge" not in text
    assert "runAsUser: 10001" in text
    assert "runAsGroup: 10001" in text
    assert "type: RuntimeDefault" in text
    assert text.count('accessModes: ["ReadWriteOncePod"]') == 2


def test_microvm_contract_requires_effective_strict_identity_evidence():
    text = CONTRACT.read_text()
    assert "supplementalGroupsPolicy: Strict" in text
    assert "/etc/group" in text
    assert ".status.features.supplementalGroupsPolicy" in text
    assert ".status.containerStatuses[].user.linux" in text
    assert "no undeclared supplemental groups" in text
    assert "unsupported, silently widened or uncertain group identity is `BLOCKED`" in text
    assert "VOLUME_MOUNT_GROUP" in text
    assert "ReadWriteOncePod" in text
