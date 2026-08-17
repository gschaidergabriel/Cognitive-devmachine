from __future__ import annotations

import contextlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tier2 = _load("tier2_replacement_test", ROOT / "clayverse" / "tier2_replacement.py")
controller = _load("tier2_kubernetes_controller_test", ROOT / "deployment" / "tier2_kubernetes_controller.py")


class FakeDB:
    def __init__(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        self.checkpoints = []

    @contextlib.contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    def entity_generation(self):
        return 7

    def checkpoint(self, note):
        self.checkpoints.append(note)
        return "checkpoint", "0" * 64


def _pod(uid: str, message: str, *, digest: str = "sha256:" + "a" * 64) -> dict:
    return {
        "metadata": {
            "namespace": "clayverse",
            "name": "clayverse-0",
            "uid": uid,
            "labels": {"app": "clayverse"},
            "ownerReferences": [
                {"kind": "StatefulSet", "name": "clayverse", "controller": True, "uid": "owner-uid"}
            ],
        },
        "spec": {
            "runtimeClassName": "kata-qemu-runtime-rs",
            "automountServiceAccountToken": False,
            "containers": [
                {"name": "clayverse", "image": "registry.example.invalid/clayverse@" + digest}
            ],
        },
        "status": {
            "containerStatuses": [
                {
                    "name": "clayverse",
                    "imageID": "docker-pullable://registry.example.invalid/clayverse@" + digest,
                    "state": {"running": {"startedAt": "2026-08-17T00:00:00Z"}},
                    "lastState": {"terminated": {"exitCode": tier2.TIER2_EXIT_CODE, "message": message}},
                }
            ]
        },
    }


def test_tier2_request_is_canonical_idempotent_and_same_pod_stays_blocked(tmp_path):
    db = FakeDB()
    term = tmp_path / "termination.log"

    receipt = tier2.request_tier2_replacement(
        db,
        "recovery_integrity_error",
        pod_uid="pod-old",
        termination_path=term,
        now=1000.0,
    )
    second = tier2.request_tier2_replacement(
        db,
        "recovery_integrity_error",
        pod_uid="pod-old",
        termination_path=term,
        now=2000.0,
    )
    assert second == receipt
    assert json.loads(term.read_text()) == receipt
    assert len([n for n in db.checkpoints if n.startswith("tier2-request:")]) == 1

    with pytest.raises(tier2.Tier2ReplacementPending) as exc:
        tier2.reconcile_tier2_replacement(db, pod_uid="pod-old", termination_path=term, now=3000.0)
    assert exc.value.receipt == receipt
    assert json.loads(term.read_text()) == receipt
    assert db.db.execute("SELECT value FROM meta WHERE key='tier2_replacement_pending'").fetchone()


def test_new_pod_uid_consumes_pending_fence_before_normal_recovery(tmp_path):
    db = FakeDB()
    term = tmp_path / "termination.log"
    receipt = tier2.request_tier2_replacement(
        db,
        "recovery_integrity_error",
        pod_uid="pod-old",
        termination_path=term,
        now=1000.0,
    )
    result = tier2.reconcile_tier2_replacement(db, pod_uid="pod-new", termination_path=term, now=2000.0)
    assert result == {
        "status": "replacement_observed",
        "request_id": receipt["request_id"],
        "old_pod_uid": "pod-old",
        "new_pod_uid": "pod-new",
    }
    assert db.db.execute("SELECT value FROM meta WHERE key='tier2_replacement_pending'").fetchone() is None
    raw = db.db.execute("SELECT value FROM meta WHERE key='tier2_replacement_last'").fetchone()[0]
    resolved = json.loads(raw)
    assert resolved["old_pod_uid"] == "pod-old"
    assert resolved["new_pod_uid"] == "pod-new"
    assert any(n.startswith("tier2-replaced:") for n in db.checkpoints)


def test_malformed_pending_state_fails_closed(tmp_path):
    db = FakeDB()
    db.db.execute("INSERT INTO meta(key,value) VALUES('tier2_replacement_pending','{}')")
    with pytest.raises(tier2.Tier2ReplacementIntegrityError):
        tier2.reconcile_tier2_replacement(db, pod_uid="pod-new", termination_path=tmp_path / "term")


def test_controller_requires_exact_runtime_image_and_uid_bound_receipt(tmp_path):
    db = FakeDB()
    term = tmp_path / "termination.log"
    receipt = tier2.request_tier2_replacement(
        db,
        "recovery_integrity_error",
        pod_uid="pod-old",
        termination_path=term,
        now=1000.0,
    )
    message = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    digest = "sha256:" + "a" * 64
    request = controller.replacement_request(
        _pod("pod-old", message, digest=digest),
        namespace="clayverse",
        pod_name="clayverse-0",
        expected_image_digest=digest,
        runtime_class="kata-qemu-runtime-rs",
    )
    assert request is not None
    assert request["pod_uid"] == "pod-old"
    assert request["delete_options"]["preconditions"] == {"uid": "pod-old"}
    assert request["delete_options"]["propagationPolicy"] == "Foreground"

    bad = json.loads(message)
    bad["old_pod_uid"] = "other-pod"
    with pytest.raises(controller.ControllerError):
        controller.replacement_request(
            _pod("pod-old", json.dumps(bad), digest=digest),
            namespace="clayverse",
            pod_name="clayverse-0",
            expected_image_digest=digest,
            runtime_class="kata-qemu-runtime-rs",
        )


def test_controller_rejects_non_trigger_and_identity_drift(tmp_path):
    db = FakeDB()
    term = tmp_path / "termination.log"
    receipt = tier2.request_tier2_replacement(
        db,
        "recovery_integrity_error",
        pod_uid="pod-old",
        termination_path=term,
        now=1000.0,
    )
    message = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    digest = "sha256:" + "a" * 64
    pod = _pod("pod-old", message, digest=digest)
    pod["status"]["containerStatuses"][0]["lastState"]["terminated"]["exitCode"] = 1
    assert controller.replacement_request(
        pod,
        namespace="clayverse",
        pod_name="clayverse-0",
        expected_image_digest=digest,
        runtime_class="kata-qemu-runtime-rs",
    ) is None

    drift = _pod("pod-old", message, digest=digest)
    drift["spec"]["runtimeClassName"] = "runc"
    with pytest.raises(controller.ControllerError):
        controller.replacement_request(
            drift,
            namespace="clayverse",
            pod_name="clayverse-0",
            expected_image_digest=digest,
            runtime_class="kata-qemu-runtime-rs",
        )


def test_kata_template_exposes_pod_uid_without_granting_clayverse_api_credentials():
    text = (ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml").read_text()
    assert "name: CLAYVERSE_POD_UID" in text
    assert "fieldPath: metadata.uid" in text
    assert "terminationMessagePath: /dev/termination-log" in text
    assert "terminationMessagePolicy: File" in text
    assert "automountServiceAccountToken: false" in text


def test_service_promotes_recovery_integrity_failure_to_tier2_request():
    text = (ROOT / "clayverse" / "service.py").read_text()
    assert "RecoveryIntegrityError" in text
    assert "reconcile_tier2_replacement" in text
    assert 'request_tier2_replacement(db, "recovery_integrity_error")' in text
    assert "return TIER2_EXIT_CODE" in text
