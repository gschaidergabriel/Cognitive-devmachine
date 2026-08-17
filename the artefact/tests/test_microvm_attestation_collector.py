import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "deployment" / "collect_microvm_attestation.py"
SPEC = importlib.util.spec_from_file_location("collect_microvm_attestation_v2", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

AttestationError = MODULE.AttestationError
attest_snapshot = MODULE.attest_snapshot
parse_expected_annotations = MODULE.parse_expected_annotations

DIGEST = "sha256:" + "a" * 64


def _pod(*, image_digest=DIGEST, guest_ready=True, annotations=None):
    return {
        "metadata": {
            "namespace": "clayverse",
            "name": "clayverse-0",
            "uid": "pod-uid-new",
            "labels": {"app": "clayverse"},
            "annotations": annotations or {
                "clayverse.seimensch.net/tier2-replacement": "external-full-sandbox-required"
            },
        },
        "spec": {
            "runtimeClassName": "kata-qemu-runtime-rs",
            "hostNetwork": False,
            "hostPID": False,
            "hostIPC": False,
            "automountServiceAccountToken": False,
            "nodeName": "node-a",
            "securityContext": {
                "fsGroup": 10001,
                "fsGroupChangePolicy": "OnRootMismatch",
                "seccompProfile": {"type": "RuntimeDefault"},
            },
            "containers": [
                {
                    "name": "clayverse",
                    "image": "registry.example/clayverse@" + image_digest,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": 10001,
                        "runAsGroup": 10001,
                        "readOnlyRootFilesystem": True,
                        "allowPrivilegeEscalation": False,
                        "capabilities": {"drop": ["ALL"]},
                    },
                    "volumeMounts": [
                        {"name": "clayverse-state", "mountPath": "/var/lib/clayverse"},
                        {"name": "clayverse-workspace", "mountPath": "/workspace"},
                        {"name": "tmp", "mountPath": "/tmp"},
                        {"name": "run", "mountPath": "/run"},
                    ],
                    "readinessProbe": {"httpGet": {"path": "/readyz", "port": 3000}},
                    "livenessProbe": {"httpGet": {"path": "/healthz", "port": 3000}},
                }
            ],
            "volumes": [
                {"name": "clayverse-state", "persistentVolumeClaim": {"claimName": "state-claim"}},
                {"name": "clayverse-workspace", "persistentVolumeClaim": {"claimName": "workspace-claim"}},
                {"name": "tmp", "emptyDir": {"medium": "Memory"}},
                {"name": "run", "emptyDir": {"medium": "Memory"}},
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
    return {"metadata": {"name": "kata-qemu-runtime-rs"}, "handler": "kata-qemu-runtime-rs"}


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
            "namespace": "clayverse",
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


def _storage():
    return [
        {
            "volume_name": "clayverse-state",
            "mount_path": "/var/lib/clayverse",
            "claim_name": "state-claim",
            "pvc_uid": "pvc-state",
            "pv_name": "pv-state",
            "pv_uid": "pvuid-state",
            "storage_class": "encrypted-rwo",
            "storage_class_uid": "sc-uid",
            "volume_binding_mode": "WaitForFirstConsumer",
            "allow_volume_expansion": True,
            "csi_driver": "csi.example.invalid",
            "csi_driver_uid": "csi-uid",
            "csi_fs_group_policy": "ReadWriteOnceWithFSType",
            "csi_requires_republish": False,
            "csi_se_linux_mount": False,
        },
        {
            "volume_name": "clayverse-workspace",
            "mount_path": "/workspace",
            "claim_name": "workspace-claim",
            "pvc_uid": "pvc-workspace",
            "pv_name": "pv-workspace",
            "pv_uid": "pvuid-workspace",
            "storage_class": "encrypted-rwo",
            "storage_class_uid": "sc-uid",
            "volume_binding_mode": "WaitForFirstConsumer",
            "allow_volume_expansion": True,
            "csi_driver": "csi.example.invalid",
            "csi_driver_uid": "csi-uid",
            "csi_fs_group_policy": "ReadWriteOnceWithFSType",
            "csi_requires_republish": False,
            "csi_se_linux_mount": False,
        },
    ]


def _attest(**kwargs):
    values = {
        "pod": _pod(),
        "runtime_class": _runtime_class(),
        "node": _node(),
        "network_policies": _policies(),
        "storage_inventory": _storage(),
        "guest_kernel": "6.1.0-kata",
        "expected_image_digest": DIGEST,
        "expected_runtime_class": "kata-qemu-runtime-rs",
        "allowed_kata_annotations": {},
    }
    values.update(kwargs)
    return attest_snapshot(**values)


def test_snapshot_pass_is_bounded_and_lists_external_acceptance_gates():
    result = _attest()
    assert result["scope_pass"] is True
    assert result["whole_product_pass"] is False
    assert result["runtime"]["guest_kernel_distinguishable_from_host"] is True
    assert result["runtime"]["independent_guest_kernel_proven_by_this_collector"] is False
    assert result["runtime"]["kata_runtime_version_observed"] is False
    assert result["expectations"]["external_review_binding_observed"] is False
    assert result["network_policy"]["selecting_policy_review_observed"] is False
    assert result["network_policy"]["enforcement_observed"] is False
    assert result["storage"]["nonroot_rw_semantics_observed"] is False
    assert result["security"]["read_only_root_declared"] is True
    assert result["security"]["runtime_enforcement_observed"] is False
    assert result["security"]["active_enforcement_probe_required"] is True
    assert result["tier2"]["full_replacement_observed"] is False
    assert len(result["missing_acceptance_evidence"]) >= 5


def test_exact_digest_runtime_and_readiness_are_fenced():
    with pytest.raises(AttestationError, match="pod spec image digest drift"):
        _attest(pod=_pod(image_digest="sha256:" + "b" * 64))
    with pytest.raises(AttestationError, match="not ready"):
        _attest(pod=_pod(guest_ready=False))
    with pytest.raises(AttestationError, match="guest kernel is not distinguishable"):
        _attest(guest_kernel="6.8.0-host")


def test_current_security_context_and_probe_contracts_are_fenced():
    pod = _pod()
    pod["spec"]["securityContext"]["fsGroup"] = 0
    with pytest.raises(AttestationError, match="fsGroup"):
        _attest(pod=pod)

    pod = _pod()
    pod["spec"]["containers"][0]["livenessProbe"]["httpGet"]["path"] = "/readyz"
    with pytest.raises(AttestationError, match="liveness probe"):
        _attest(pod=pod)

    pod = _pod()
    pod["spec"]["volumes"].append({"name": "bad", "hostPath": {"path": "/"}})
    with pytest.raises(AttestationError, match="hostPath"):
        _attest(pod=pod)


def test_effective_kata_annotations_default_deny_and_exact_allowset():
    annotation = "io.katacontainers.config.hypervisor.path"
    pod = _pod(annotations={annotation: "/opt/kata/bin/qemu"})
    with pytest.raises(AttestationError, match="declared expected allowset"):
        _attest(pod=pod)

    result = _attest(
        pod=pod,
        allowed_kata_annotations={annotation: "/opt/kata/bin/qemu"},
    )
    assert result["pod"]["effective_kata_annotations"] == {annotation: "/opt/kata/bin/qemu"}
    assert result["expectations"]["kata_annotations"] == {annotation: "/opt/kata/bin/qemu"}

    with pytest.raises(AttestationError, match="declared expected allowset"):
        _attest(pod=pod, allowed_kata_annotations={annotation: "/other"})


def test_expected_annotation_parser_is_prefix_and_duplicate_fenced():
    key = "io.katacontainers.config.runtime.disable_guest_seccomp"
    assert parse_expected_annotations([f"{key}=false"]) == {key: "false"}
    with pytest.raises(AttestationError, match="KEY=VALUE"):
        parse_expected_annotations([key])
    with pytest.raises(AttestationError, match="io.katacontainers"):
        parse_expected_annotations(["example.invalid/key=value"])
    with pytest.raises(AttestationError, match="duplicate"):
        parse_expected_annotations([f"{key}=false", f"{key}=true"])


def test_network_policy_inventory_is_additive_and_broad_allows_fail_closed():
    selected_allow = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"namespace": "clayverse", "name": "bad-world", "uid": "bad", "resourceVersion": "11"},
        "spec": {
            "podSelector": {"matchExpressions": [{"key": "app", "operator": "In", "values": ["clayverse"]}]},
            "policyTypes": ["Egress"],
            "egress": [{"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}], "ports": [{"port": 443}]}],
        },
    }
    with pytest.raises(AttestationError, match="obvious broad"):
        _attest(network_policies=_policies(selected_allow))

    unrelated = {
        "metadata": {"name": "other"},
        "spec": {"podSelector": {"matchLabels": {"app": "other"}}, "policyTypes": ["Egress"], "egress": [{}]},
    }
    result = _attest(network_policies=_policies(unrelated))
    assert result["network_policy"]["selecting_policy_names"] == ["clayverse-default-deny"]


def test_missing_or_malformed_network_policy_fails_closed():
    with pytest.raises(AttestationError, match="no NetworkPolicy selects"):
        _attest(network_policies={"items": []})
    malformed = {
        "metadata": {"name": "malformed"},
        "spec": {
            "podSelector": {"matchLabels": {"app": "clayverse"}},
            "policyTypes": ["Egress"],
            "egress": [{"to": ["not-an-object"]}],
        },
    }
    with pytest.raises(AttestationError, match="peer must be an object"):
        _attest(network_policies=_policies(malformed))


def test_storage_identity_must_cover_both_persistent_mounts_with_csi_identity():
    one = [_storage()[0]]
    with pytest.raises(AttestationError, match="cover both"):
        _attest(storage_inventory=one)
    broken = _storage()
    broken[0] = dict(broken[0], csi_driver="")
    with pytest.raises(AttestationError, match="csi_driver"):
        _attest(storage_inventory=broken)
    broken = _storage()
    broken[0] = dict(broken[0], mount_path="/wrong")
    with pytest.raises(AttestationError, match="mount_path drift"):
        _attest(storage_inventory=broken)


def test_required_persistent_mount_and_pvc_volume_must_match():
    pod = _pod()
    pod["spec"]["containers"][0]["volumeMounts"][0]["mountPath"] = "/wrong"
    with pytest.raises(AttestationError, match="persistent mount drift"):
        _attest(pod=pod)

    pod = _pod()
    pod["spec"]["volumes"][0] = {"name": "clayverse-state", "emptyDir": {}}
    with pytest.raises(AttestationError, match="persistent PVC volumes"):
        _attest(pod=pod)


def test_policy_and_storage_inventory_hashes_are_deterministic():
    first = _attest()
    second = _attest(
        network_policies={"items": list(reversed(_policies()["items"]))},
        storage_inventory=list(reversed(_storage())),
    )
    assert first["network_policy"]["inventory_sha256"] == second["network_policy"]["inventory_sha256"]
    assert first["storage"]["inventory_sha256"] == second["storage"]["inventory_sha256"]


def test_absent_key_notin_broad_policy_still_selects_and_fails_closed():
    broad = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"namespace": "clayverse", "name": "absent-notin-broad", "uid": "notin-broad", "resourceVersion": "14"},
        "spec": {
            "podSelector": {"matchExpressions": [{"key": "tier", "operator": "NotIn", "values": ["blocked"]}]},
            "policyTypes": ["Egress"],
            "egress": [{}],
        },
    }
    with pytest.raises(AttestationError, match="obvious broad"):
        _attest(network_policies=_policies(broad))


def test_absent_key_notin_narrow_empty_policy_appears_in_inventory():
    selected = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"namespace": "clayverse", "name": "absent-notin-empty", "uid": "notin-empty", "resourceVersion": "15"},
        "spec": {
            "podSelector": {"matchExpressions": [{"key": "tier", "operator": "NotIn", "values": ["blocked"]}]},
            "policyTypes": ["Egress"],
            "egress": [],
        },
    }
    result = _attest(network_policies=_policies(selected))
    assert result["network_policy"]["selecting_policy_names"] == ["absent-notin-empty", "clayverse-default-deny"]
