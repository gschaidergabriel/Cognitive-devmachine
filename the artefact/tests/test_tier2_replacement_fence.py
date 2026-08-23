from pathlib import Path

import pytest

from clayverse import tier2

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
SERVICE = ROOT / "clayverse" / "service.py"
CONTRACT = ROOT / "deployment" / "TIER2_REPLACEMENT_SIGNAL_CONTRACT.md"


def test_no_fence_allows_normal_non_kubernetes_probe(tmp_path: Path):
    assert tier2.assert_tier2_boot_allowed(tmp_path, current_pod_uid="") is None


def test_same_pod_is_fenced_until_new_uid_and_generation(tmp_path: Path):
    first = tier2.request_tier2_replacement(
        tmp_path,
        current_pod_uid="pod-old-uid",
        reason="recovery_integrity_failure",
        entity_generation=7,
    )
    assert first.old_pod_uid == "pod-old-uid"
    with pytest.raises(tier2.Tier2ReplacementBlocked, match="same Pod UID"):
        tier2.assert_tier2_boot_allowed(tmp_path, current_pod_uid="pod-old-uid")

    admitted = tier2.assert_tier2_boot_allowed(tmp_path, current_pod_uid="pod-new-uid")
    assert admitted == first
    with pytest.raises(tier2.Tier2ReplacementBlocked, match="did not advance"):
        tier2.clear_tier2_fence_after_boot(
            tmp_path,
            current_pod_uid="pod-new-uid",
            live_entity_generation=7,
        )
    assert tier2.load_tier2_fence(tmp_path) == first

    assert tier2.clear_tier2_fence_after_boot(
        tmp_path,
        current_pod_uid="pod-new-uid",
        live_entity_generation=8,
    ) == first
    assert tier2.load_tier2_fence(tmp_path) is None


def test_same_pod_repeat_is_idempotent_and_preserves_first_fence(tmp_path: Path):
    first = tier2.request_tier2_replacement(
        tmp_path,
        current_pod_uid="pod-a",
        reason="recovery_integrity_failure",
        entity_generation=3,
    )
    repeated = tier2.request_tier2_replacement(
        tmp_path,
        current_pod_uid="pod-a",
        reason="later_reason",
        entity_generation=4,
    )
    assert repeated == first
    assert tier2.load_tier2_fence(tmp_path) == first


def test_new_pod_can_refence_if_integrity_fails_again(tmp_path: Path):
    tier2.request_tier2_replacement(
        tmp_path,
        current_pod_uid="pod-a",
        reason="recovery_integrity_failure",
        entity_generation=3,
    )
    replacement = tier2.request_tier2_replacement(
        tmp_path,
        current_pod_uid="pod-b",
        reason="recovery_integrity_failure",
        entity_generation=4,
    )
    assert replacement.old_pod_uid == "pod-b"
    with pytest.raises(tier2.Tier2ReplacementBlocked, match="same Pod UID"):
        tier2.assert_tier2_boot_allowed(tmp_path, current_pod_uid="pod-b")


def test_partial_os_write_is_completed_before_fsync(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    real_write = tier2.os.write

    def partial_write(fd: int, payload) -> int:
        data = bytes(payload)
        return real_write(fd, data[: max(1, len(data) // 2)])

    monkeypatch.setattr(tier2.os, "write", partial_write)
    expected = tier2.request_tier2_replacement(
        tmp_path,
        current_pod_uid="pod-partial",
        reason="recovery_integrity_failure",
        entity_generation=5,
    )
    assert tier2.load_tier2_fence(tmp_path) == expected


def test_symlinked_malformed_and_oversized_fences_fail_closed(tmp_path: Path):
    target = tmp_path / "outside.json"
    target.write_text(
        '{"schema":"clayverse.tier2-replacement/v1","old_pod_uid":"pod-a",'
        '"reason":"recovery_integrity_failure","entity_generation":1}\n'
    )
    tier2.fence_path(tmp_path).symlink_to(target)
    with pytest.raises(tier2.Tier2ReplacementBlocked):
        tier2.load_tier2_fence(tmp_path)

    tier2.fence_path(tmp_path).unlink()
    tier2.fence_path(tmp_path).write_text("not-json")
    with pytest.raises(tier2.Tier2ReplacementBlocked):
        tier2.assert_tier2_boot_allowed(tmp_path, current_pod_uid="pod-b")

    tier2.fence_path(tmp_path).write_bytes(b"x" * 4097)
    with pytest.raises(tier2.Tier2ReplacementBlocked, match="exceeds bound"):
        tier2.load_tier2_fence(tmp_path)


def test_kata_template_injects_pod_uid_without_service_account():
    text = TEMPLATE.read_text()
    assert "name: CLAYVERSE_POD_UID" in text
    assert "fieldPath: metadata.uid" in text
    assert "automountServiceAccountToken: false" in text
    assert "ReadWriteOncePod" in text
    assert "clayverse-default-deny" in text
    assert "external-full-sandbox-required" in text


def test_service_wires_recovery_integrity_failure_to_tier2_fence():
    text = SERVICE.read_text()
    assert "except RecoveryIntegrityError" in text
    assert "request_tier2_replacement(" in text
    assert 'reason="recovery_integrity_failure"' in text
    assert "assert_tier2_boot_allowed(" in text
    assert "clear_tier2_fence_after_boot(" in text
    assert "TIER2_EXIT_CODE" in text


def test_contract_keeps_external_full_sandbox_gate_open():
    text = CONTRACT.read_text()
    assert "SOURCE CANDIDATE / NOT FINAL TIER-2 ACCEPTANCE" in text
    assert "new Pod UID" in text
    assert "new Kata sandbox/VM identity" in text
    assert "deletion precondition" in text
    assert "RestartAllContainers" in text
    assert "TIER2_REPLACEMENT_BLOCKED" in text
