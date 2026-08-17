import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "deployment" / "collect_microvm_attestation.py"
SPEC = importlib.util.spec_from_file_location("collect_microvm_attestation", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

AttestationError = MODULE.AttestationError
attest_snapshot = MODULE.attest_snapshot

DIGEST = "sha256:" + "a" * 64


def _pod(*, image_digest=DIGEST, guest_ready=True):
    return {
        "metadata": {
            "namespace": "clayverse",
            "name": "clayverse-0",
            "uid": "pod-uid",
            "labels": {"app": "clayverse"},
        },
        "spec": {
            "runtimeClassName": "kata-qemu-runtime-rs",
            "hostNetwork": False,
            "hostPID": False,
            "hostIPC": False,
            "automountServiceAccountToken": False,
            "nodeName": "node-a",
            "containers": [
                {
                    "name": "clayverse",
                    "image": "registry.example/clayverse@" + image_digest,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "readOnlyRootFilesystem": True,
                        "allowPrivilegeEscalation": False,
                        "capabilities": {"drop": ["ALL"]},
                    },
                }
            ],
            "volumes": [
                {"name": "state", "persistentVolumeClaim": {"claimName": "state"}},
                {"name": "tmp", "emptyDir": {"medium": "Memory"}},
            ],
        },
        "status": {
            "containerStatuses": [
                {
                    "name": "clayverse",
                    "imageID": "containerd://registry.example/clayverse@" + image_digest,
                    "ready": guest_ready,
                }
            ]
        },
    }


def _runtime_class():
    return {
        "metadata": {"name": "kata-qemu-runtime-rs"},
        "handler": "kata-qemu-runtime-rs",
    }


def _node(kernel="6.8.0-host"):
    return {
        "metadata": {"name": "node-a"},
        "status": {
            "nodeInfo": {
                "kernelVersion": kernel,
                "containerRuntimeVersion": "containerd://2.0.0",
                "kubeletVersion": "v1.35.0",
                "architecture": "amd64",
                "osImage": "test",
            }
        },
    }


def _default_deny():
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {
            "name": "clayverse-default-deny",
            "uid": "deny-uid",
            "resourceVersion": "10",
        },
        "spec": {
            "podSelector": {"matchLabels": {"app": "clayverse"}},
            "policyTypes": ["Ingress", "Egress"],
            "ingress": [],
            "egress": [],
        },
    }


def _policies(*extra):
    return {"items": [_default_deny(), *extra]}


def _attest(**kwargs):
    values = {
        "pod": _pod(),
        "runtime_class": _runtime_class(),
        "node": _node(),
        "network_policies": _policies(),
        "guest_kernel": "6.1.0-kata",
        "expected_image_digest": DIGEST,
        "expected_runtime_class": "kata-qemu-runtime-rs",
    }
    values.update(kwargs)
    return attest_snapshot(**values)


def test_collector_attests_runtime_identity_without_claiming_network_or_whole_pass():
    result = _attest()
    assert result["scope_pass"] is True
    assert result["whole_product_pass"] is False
    assert result["image"]["expected_digest"] == DIGEST
    assert result["runtime"]["runtime_class"] == "kata-qemu-runtime-rs"
    assert result["runtime"]["host_kernel"] != result["runtime"]["guest_kernel"]
    assert result["network_policy"]["declarative_default_deny_present"] is True
    assert result["network_policy"]["enforcement_observed"] is False
    assert result["network_policy"]["active_probe_required"] is True
    assert result["network_policy"]["selecting_policy_names"] == ["clayverse-default-deny"]


def test_collector_rejects_runtime_image_digest_drift():
    pod = _pod(image_digest="sha256:" + "b" * 64)
    with pytest.raises(AttestationError, match="pod spec image digest drift"):
        _attest(pod=pod)


def test_collector_rejects_host_kernel_indistinguishable_from_guest_kernel():
    with pytest.raises(AttestationError, match="guest kernel is not distinguishable"):
        _attest(guest_kernel="6.8.0-host")


def test_collector_rejects_missing_default_deny_policy():
    with pytest.raises(AttestationError, match="clayverse-default-deny"):
        _attest(network_policies={"items": []})


def test_collector_rejects_obvious_allow_all_egress_even_when_default_deny_exists():
    broad = {
        "metadata": {"name": "bad-egress", "uid": "bad", "resourceVersion": "11"},
        "spec": {
            "podSelector": {"matchLabels": {"app": "clayverse"}},
            "policyTypes": ["Egress"],
            "egress": [{}],
        },
    }
    with pytest.raises(AttestationError, match="obvious broad NetworkPolicy allow"):
        _attest(network_policies=_policies(broad))


def test_collector_rejects_global_ipblock_allow():
    broad = {
        "metadata": {"name": "bad-world", "uid": "bad2", "resourceVersion": "12"},
        "spec": {
            "podSelector": {"matchLabels": {"app": "clayverse"}},
            "policyTypes": ["Egress"],
            "egress": [{"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}], "ports": [{"port": 443}]}],
        },
    }
    with pytest.raises(AttestationError, match="obvious broad NetworkPolicy allow"):
        _attest(network_policies=_policies(broad))


def test_nonselecting_broad_policy_does_not_pollute_clayverse_inventory():
    unrelated = {
        "metadata": {"name": "other-app", "uid": "other", "resourceVersion": "13"},
        "spec": {
            "podSelector": {"matchLabels": {"app": "other"}},
            "policyTypes": ["Ingress", "Egress"],
            "ingress": [{}],
            "egress": [{}],
        },
    }
    result = _attest(network_policies=_policies(unrelated))
    assert result["network_policy"]["selecting_policy_names"] == ["clayverse-default-deny"]


def test_collector_rejects_hostpath_and_nonready_container():
    pod = _pod(guest_ready=False)
    pod["spec"]["volumes"].append({"name": "bad", "hostPath": {"path": "/"}})
    with pytest.raises(AttestationError, match="hostPath"):
        _attest(pod=pod)

    pod = _pod(guest_ready=False)
    with pytest.raises(AttestationError, match="not ready"):
        _attest(pod=pod)
