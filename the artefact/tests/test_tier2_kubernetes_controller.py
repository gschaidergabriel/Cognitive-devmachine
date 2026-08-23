from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = ROOT / "deployment" / "tier2_kubernetes_controller.py"


def _load_controller():
    spec = importlib.util.spec_from_file_location("tier2_kubernetes_controller_test", CONTROLLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


controller = _load_controller()
DIGEST = "sha256:" + "a" * 64


def _pod(*, uid="pod-old", exit_code=86, runtime_class="kata-qemu-runtime-rs", image_digest=DIGEST):
    return {
        "metadata": {
            "namespace": "clayverse",
            "name": "clayverse-0",
            "uid": uid,
            "labels": {"app": "clayverse"},
            "ownerReferences": [
                {
                    "apiVersion": "apps/v1",
                    "kind": "StatefulSet",
                    "name": "clayverse",
                    "uid": "statefulset-uid",
                    "controller": True,
                }
            ],
        },
        "spec": {
            "runtimeClassName": runtime_class,
            "automountServiceAccountToken": False,
            "containers": [
                {"name": "clayverse", "image": "registry.example.invalid/clayverse@" + image_digest}
            ],
        },
        "status": {
            "containerStatuses": [
                {
                    "name": "clayverse",
                    "imageID": "docker-pullable://registry.example.invalid/clayverse@" + image_digest,
                    "state": {"running": {"startedAt": "2026-08-17T00:00:00Z"}},
                    "lastState": {"terminated": {"exitCode": exit_code, "reason": "Error"}},
                }
            ]
        },
    }


def test_reserved_exit_86_produces_exact_uid_preconditioned_delete():
    request = controller.replacement_request(
        _pod(),
        namespace="clayverse",
        pod_name="clayverse-0",
        expected_image_digest=DIGEST,
        runtime_class="kata-qemu-runtime-rs",
    )
    assert request == {
        "pod_uid": "pod-old",
        "delete_options": {
            "apiVersion": "v1",
            "kind": "DeleteOptions",
            "gracePeriodSeconds": 30,
            "propagationPolicy": "Foreground",
            "preconditions": {"uid": "pod-old"},
        },
    }


def test_non_tier2_exit_and_not_yet_started_pod_do_not_delete():
    assert controller.replacement_request(
        _pod(exit_code=1),
        namespace="clayverse",
        pod_name="clayverse-0",
        expected_image_digest=DIGEST,
        runtime_class="kata-qemu-runtime-rs",
    ) is None

    pod = _pod()
    pod["status"].pop("containerStatuses")
    assert controller.replacement_request(
        pod,
        namespace="clayverse",
        pod_name="clayverse-0",
        expected_image_digest=DIGEST,
        runtime_class="kata-qemu-runtime-rs",
    ) is None


def test_runtime_image_owner_and_app_credential_drift_fail_closed():
    cases = []

    pod = _pod(runtime_class="runc")
    cases.append(pod)

    pod = _pod()
    pod["status"]["containerStatuses"][0]["imageID"] = "sha256:" + "b" * 64
    cases.append(pod)

    pod = _pod()
    pod["metadata"]["ownerReferences"][0]["name"] = "other"
    cases.append(pod)

    pod = _pod()
    pod["spec"]["automountServiceAccountToken"] = True
    cases.append(pod)

    for candidate in cases:
        with pytest.raises(controller.ControllerError):
            controller.replacement_request(
                candidate,
                namespace="clayverse",
                pod_name="clayverse-0",
                expected_image_digest=DIGEST,
                runtime_class="kata-qemu-runtime-rs",
            )


def test_successor_name_reuse_is_never_broadened_past_uid_precondition():
    class ConflictAPI:
        def get_pod(self, namespace, pod_name):
            return _pod(uid="pod-old")

        def delete_pod(self, namespace, pod_name, options):
            assert options["preconditions"] == {"uid": "pod-old"}
            return False

    assert controller.run_once(
        ConflictAPI(),
        namespace="clayverse",
        pod_name="clayverse-0",
        digest=DIGEST,
        runtime_class="kata-qemu-runtime-rs",
    ) is False


def test_missing_pod_during_statefulset_replacement_is_transient():
    class MissingAPI:
        def get_pod(self, namespace, pod_name):
            return None

        def delete_pod(self, namespace, pod_name, options):
            raise AssertionError("delete must not run without exact live Pod")

    assert controller.run_once(
        MissingAPI(),
        namespace="clayverse",
        pod_name="clayverse-0",
        digest=DIGEST,
        runtime_class="kata-qemu-runtime-rs",
    ) is False


def test_rbac_is_exact_named_pod_get_delete_only():
    text = (ROOT / "deployment" / "tier2-controller-rbac.template.yaml").read_text()
    role = next(doc for doc in text.split("\n---\n") if "kind: Role\n" in doc)
    assert 'resources: ["pods"]' in role
    assert 'resourceNames: ["clayverse-0"]' in role
    assert 'verbs: ["get", "delete"]' in role
    for forbidden in ("list", "watch", "create", "update", "patch"):
        assert f'"{forbidden}"' not in role


def test_controller_is_deployment_only_and_has_no_shell_or_clayverse_state_imports():
    text = CONTROLLER.read_text()
    assert "subprocess" not in text
    assert "os.system" not in text
    assert "process.exec" not in text
    assert "UnifiedDB" not in text
    assert "clayverse.store" not in text
    assert "clayverse.effects" not in text
