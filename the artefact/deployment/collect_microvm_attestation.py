#!/usr/bin/env python3
"""Collect bounded fail-closed ClayVerse MicroVM deployment evidence.

The collector is deployment tooling, not a ClayVerse application service. It records
only evidence directly observable through the Kubernetes API and an in-guest command.
It deliberately leaves runtime-version/configuration, CNI enforcement, persistent-volume
write semantics, Tier-2 sandbox replacement and whole-product acceptance open unless a
separate accepted evidence path proves them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_KATA_ANNOTATION_PREFIX = "io.katacontainers."
_REQUIRED_UID_GID = 10001
_REQUIRED_PERSISTENT_MOUNTS = {
    "clayverse-state": "/var/lib/clayverse",
    "clayverse-workspace": "/workspace",
}


class AttestationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Kubectl:
    binary: str = "kubectl"
    timeout_seconds: int = 20

    def _run(self, args: list[str]) -> str:
        command = [self.binary, *args]
        try:
            proc = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AttestationError(f"kubectl execution failed: {type(exc).__name__}") from exc
        if proc.returncode != 0:
            raise AttestationError(
                f"kubectl command failed rc={proc.returncode}: {proc.stderr.strip()[:400]}"
            )
        return proc.stdout

    def json(self, args: list[str]) -> dict[str, Any]:
        raw = self._run([*args, "-o", "json"])
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AttestationError("kubectl returned non-JSON data") from exc
        if not isinstance(value, dict):
            raise AttestationError("kubectl JSON root must be an object")
        return value

    def text(self, args: list[str]) -> str:
        value = self._run(args).strip()
        if not value:
            raise AttestationError("kubectl returned empty text")
        return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AttestationError(message)


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _selector_matches(selector: dict[str, Any], labels: dict[str, str]) -> bool:
    match_labels = selector.get("matchLabels", {})
    _require(isinstance(match_labels, dict), "podSelector.matchLabels must be an object")
    for key, expected in match_labels.items():
        _require(isinstance(key, str) and isinstance(expected, str), "matchLabels must be strings")
        if labels.get(key) != expected:
            return False

    expressions = selector.get("matchExpressions", [])
    _require(isinstance(expressions, list), "podSelector.matchExpressions must be a list")
    for expr in expressions:
        _require(isinstance(expr, dict), "podSelector expression must be an object")
        key = expr.get("key")
        operator = expr.get("operator")
        values = expr.get("values", [])
        _require(isinstance(key, str) and key, "selector expression key is invalid")
        _require(operator in {"In", "NotIn", "Exists", "DoesNotExist"}, "selector operator unsupported")
        _require(isinstance(values, list) and all(isinstance(v, str) for v in values), "selector values must be strings")
        if operator in {"In", "NotIn"}:
            _require(bool(values), f"selector {operator} requires values")
        elif values:
            raise AttestationError(f"selector {operator} must not contain values")

        if operator == "In" and (key not in labels or labels[key] not in values):
            return False
        if operator == "NotIn" and key in labels and labels[key] in values:
            return False
        if operator == "Exists" and key not in labels:
            return False
        if operator == "DoesNotExist" and key in labels:
            return False
    return True


def _peer_is_obviously_broad(peer: dict[str, Any]) -> bool:
    if not peer:
        return True
    ip_block = peer.get("ipBlock")
    if isinstance(ip_block, dict) and ip_block.get("cidr") in {"0.0.0.0/0", "::/0"}:
        return True
    namespace_selector = peer.get("namespaceSelector")
    pod_selector = peer.get("podSelector")
    if namespace_selector == {} and pod_selector in (None, {}):
        return True
    if pod_selector == {} and namespace_selector is None:
        return True
    return False


def _policy_has_obvious_broad_allow(policy: dict[str, Any]) -> bool:
    spec = policy.get("spec", {})
    _require(isinstance(spec, dict), "NetworkPolicy spec must be an object")
    for direction, peer_key in (("ingress", "from"), ("egress", "to")):
        rules = spec.get(direction, [])
        _require(isinstance(rules, list), f"NetworkPolicy {direction} must be a list")
        for rule in rules:
            _require(isinstance(rule, dict), f"NetworkPolicy {direction} rule must be an object")
            if not rule or peer_key not in rule:
                return True
            peers = rule.get(peer_key)
            _require(isinstance(peers, list), f"NetworkPolicy {peer_key} must be a list")
            for peer in peers:
                _require(isinstance(peer, dict), f"NetworkPolicy {peer_key} peer must be an object")
                if _peer_is_obviously_broad(peer):
                    return True
    return False


def _selecting_policies(policies: dict[str, Any], labels: dict[str, str]) -> list[dict[str, Any]]:
    items = policies.get("items")
    _require(isinstance(items, list), "NetworkPolicy list must contain items")
    selected: list[dict[str, Any]] = []
    for policy in items:
        _require(isinstance(policy, dict), "NetworkPolicy item must be an object")
        spec = policy.get("spec", {})
        _require(isinstance(spec, dict), "NetworkPolicy spec must be an object")
        selector = spec.get("podSelector", {})
        _require(isinstance(selector, dict), "NetworkPolicy podSelector must be an object")
        if _selector_matches(selector, labels):
            selected.append(policy)
    selected.sort(key=lambda p: str(p.get("metadata", {}).get("name", "")))
    return selected


def _effective_kata_annotations(pod: dict[str, Any]) -> dict[str, str]:
    annotations = pod.get("metadata", {}).get("annotations", {}) or {}
    _require(isinstance(annotations, dict), "pod annotations must be an object")
    result: dict[str, str] = {}
    for key, value in annotations.items():
        _require(isinstance(key, str) and isinstance(value, str), "pod annotation keys/values must be strings")
        if key.startswith(_KATA_ANNOTATION_PREFIX):
            result[key] = value
    return dict(sorted(result.items()))


def _validate_storage_inventory(storage_inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _require(isinstance(storage_inventory, list), "storage inventory must be a list")
    by_volume: dict[str, dict[str, Any]] = {}
    for item in storage_inventory:
        _require(isinstance(item, dict), "storage inventory item must be an object")
        volume_name = item.get("volume_name")
        _require(volume_name in _REQUIRED_PERSISTENT_MOUNTS, "unexpected persistent volume identity")
        _require(volume_name not in by_volume, "duplicate storage inventory volume")
        for key in ("claim_name", "pvc_uid", "pv_name", "storage_class", "csi_driver"):
            _require(isinstance(item.get(key), str) and item[key], f"storage inventory missing {key}")
        by_volume[volume_name] = item
    _require(set(by_volume) == set(_REQUIRED_PERSISTENT_MOUNTS), "storage inventory must cover both persistent mounts")
    return [by_volume[name] for name in sorted(by_volume)]


def _probe_path(probe: Any) -> str | None:
    if not isinstance(probe, dict):
        return None
    http_get = probe.get("httpGet")
    if not isinstance(http_get, dict):
        return None
    path = http_get.get("path")
    return path if isinstance(path, str) else None


def attest_snapshot(
    *,
    pod: dict[str, Any],
    runtime_class: dict[str, Any],
    node: dict[str, Any],
    network_policies: dict[str, Any],
    storage_inventory: list[dict[str, Any]],
    guest_kernel: str,
    expected_image_digest: str,
    expected_runtime_class: str,
    allowed_kata_annotations: dict[str, str] | None = None,
) -> dict[str, Any]:
    _require(_DIGEST_RE.fullmatch(expected_image_digest) is not None, "invalid expected image digest")
    _require(bool(guest_kernel.strip()), "guest kernel identity is empty")
    allowed_kata_annotations = dict(sorted((allowed_kata_annotations or {}).items()))
    for key, value in allowed_kata_annotations.items():
        _require(key.startswith(_KATA_ANNOTATION_PREFIX), "allowed Kata annotation must use io.katacontainers.*")
        _require(isinstance(value, str), "allowed Kata annotation value must be a string")

    metadata = pod.get("metadata", {})
    spec = pod.get("spec", {})
    status = pod.get("status", {})
    _require(isinstance(metadata, dict) and isinstance(spec, dict) and isinstance(status, dict), "pod object is malformed")
    labels = metadata.get("labels", {})
    _require(isinstance(labels, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in labels.items()), "pod labels must be strings")

    effective_kata_annotations = _effective_kata_annotations(pod)
    _require(
        effective_kata_annotations == allowed_kata_annotations,
        "effective io.katacontainers.* annotations differ from exact reviewed allowset",
    )

    _require(spec.get("runtimeClassName") == expected_runtime_class, "pod RuntimeClass drift")
    _require(runtime_class.get("metadata", {}).get("name") == expected_runtime_class, "RuntimeClass object name drift")
    runtime_handler = runtime_class.get("handler")
    _require(isinstance(runtime_handler, str) and runtime_handler, "RuntimeClass handler is missing")

    _require(spec.get("hostNetwork") is False, "hostNetwork must be false")
    _require(spec.get("hostPID") is False, "hostPID must be false")
    _require(spec.get("hostIPC") is False, "hostIPC must be false")
    _require(spec.get("automountServiceAccountToken") is False, "ServiceAccount token automount must be false")

    pod_security = spec.get("securityContext", {})
    _require(isinstance(pod_security, dict), "pod securityContext must be an object")
    _require(pod_security.get("fsGroup") == _REQUIRED_UID_GID, "pod fsGroup must be 10001")
    _require(pod_security.get("fsGroupChangePolicy") == "OnRootMismatch", "fsGroupChangePolicy drift")
    _require(pod_security.get("seccompProfile", {}).get("type") == "RuntimeDefault", "pod seccompProfile must be RuntimeDefault")

    containers = spec.get("containers")
    _require(isinstance(containers, list) and len(containers) == 1, "expected exactly one application container")
    container = containers[0]
    _require(isinstance(container, dict) and container.get("name") == "clayverse", "application container must be named clayverse")
    image = container.get("image")
    _require(isinstance(image, str) and image.endswith("@" + expected_image_digest), "pod spec image digest drift")

    security = container.get("securityContext", {})
    _require(isinstance(security, dict), "container securityContext must be an object")
    _require(security.get("runAsNonRoot") is True, "runAsNonRoot must be true")
    _require(security.get("runAsUser") == _REQUIRED_UID_GID, "runAsUser must be 10001")
    _require(security.get("runAsGroup") == _REQUIRED_UID_GID, "runAsGroup must be 10001")
    _require(security.get("readOnlyRootFilesystem") is True, "readOnlyRootFilesystem must be true")
    _require(security.get("allowPrivilegeEscalation") is False, "allowPrivilegeEscalation must be false")
    drops = security.get("capabilities", {}).get("drop", [])
    _require(isinstance(drops, list) and set(drops) == {"ALL"}, "all Linux capabilities must be dropped exactly")

    _require(_probe_path(container.get("readinessProbe")) == "/readyz", "readiness probe must use /readyz")
    _require(_probe_path(container.get("livenessProbe")) == "/healthz", "liveness probe must use /healthz")

    volume_mounts = container.get("volumeMounts", [])
    _require(isinstance(volume_mounts, list), "volumeMounts must be a list")
    mount_map = {
        item.get("name"): item.get("mountPath")
        for item in volume_mounts
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    for name, path in _REQUIRED_PERSISTENT_MOUNTS.items():
        _require(mount_map.get(name) == path, f"persistent mount drift: {name}")

    pod_volumes = spec.get("volumes", [])
    _require(isinstance(pod_volumes, list), "pod volumes must be a list")
    for volume in pod_volumes:
        _require(isinstance(volume, dict), "pod volume must be an object")
        _require("hostPath" not in volume, "hostPath volume is forbidden")
    persistent_volume_names = {
        volume.get("name")
        for volume in pod_volumes
        if isinstance(volume.get("persistentVolumeClaim"), dict)
    }
    _require(set(_REQUIRED_PERSISTENT_MOUNTS).issubset(persistent_volume_names), "persistent PVC volumes are missing")

    storage_projection = _validate_storage_inventory(storage_inventory)

    statuses = status.get("containerStatuses")
    _require(isinstance(statuses, list), "pod containerStatuses are missing")
    clay_statuses = [item for item in statuses if isinstance(item, dict) and item.get("name") == "clayverse"]
    _require(len(clay_statuses) == 1, "expected exactly one ClayVerse container status")
    clay_status = clay_statuses[0]
    image_id = clay_status.get("imageID")
    _require(isinstance(image_id, str) and expected_image_digest in image_id, "runtime imageID digest drift")
    _require(clay_status.get("ready") is True, "ClayVerse container is not ready")

    node_name = spec.get("nodeName")
    _require(isinstance(node_name, str) and node_name, "pod nodeName is missing")
    _require(node.get("metadata", {}).get("name") == node_name, "node object identity drift")
    node_info = node.get("status", {}).get("nodeInfo", {})
    _require(isinstance(node_info, dict), "nodeInfo is missing")
    host_kernel = node_info.get("kernelVersion")
    _require(isinstance(host_kernel, str) and host_kernel, "host kernel identity is missing")
    _require(guest_kernel.strip() != host_kernel.strip(), "guest kernel is not distinguishable from host kernel")

    selecting = _selecting_policies(network_policies, labels)
    _require(selecting, "no NetworkPolicy selects the ClayVerse pod")
    default_deny = [p for p in selecting if p.get("metadata", {}).get("name") == "clayverse-default-deny"]
    _require(len(default_deny) == 1, "exact clayverse-default-deny policy is required")
    deny_spec = default_deny[0].get("spec", {})
    policy_types = deny_spec.get("policyTypes", [])
    _require(isinstance(policy_types, list) and set(policy_types) == {"Ingress", "Egress"}, "default deny must cover ingress and egress")
    _require(deny_spec.get("ingress", []) == [], "default deny ingress must be empty")
    _require(deny_spec.get("egress", []) == [], "default deny egress must be empty")

    broad = [
        str(p.get("metadata", {}).get("name", "<unnamed>"))
        for p in selecting
        if _policy_has_obvious_broad_allow(p)
    ]
    _require(not broad, "obvious broad NetworkPolicy allow detected: " + ",".join(broad))

    policy_projection = [
        {
            "apiVersion": p.get("apiVersion"),
            "kind": p.get("kind"),
            "namespace": p.get("metadata", {}).get("namespace"),
            "name": p.get("metadata", {}).get("name"),
            "uid": p.get("metadata", {}).get("uid"),
            "resourceVersion": p.get("metadata", {}).get("resourceVersion"),
            "spec": p.get("spec"),
        }
        for p in selecting
    ]

    pod_uid = metadata.get("uid")
    _require(isinstance(pod_uid, str) and pod_uid, "pod UID is missing")

    return {
        "schema": "clayverse-microvm-attestation/v2",
        "scope_pass": True,
        "whole_product_pass": False,
        "classification": "MICROVM_DEPLOYMENT_SNAPSHOT_ATTESTED_EXTERNAL_RUNTIME_GATES_OPEN",
        "pod": {
            "namespace": metadata.get("namespace"),
            "name": metadata.get("name"),
            "uid": pod_uid,
            "node": node_name,
            "effective_kata_annotations": effective_kata_annotations,
            "kata_annotation_inventory_sha256": _canonical_hash(effective_kata_annotations),
        },
        "image": {
            "expected_digest": expected_image_digest,
            "spec": image,
            "runtime_image_id": image_id,
        },
        "runtime": {
            "runtime_class": expected_runtime_class,
            "handler": runtime_handler,
            "host_kernel": host_kernel,
            "guest_kernel": guest_kernel.strip(),
            "guest_kernel_distinguishable_from_host": True,
            "independent_guest_kernel_proven_by_this_collector": False,
            "kata_runtime_version_observed": False,
            "kata_runtime_configuration_observed": False,
            "container_runtime_version": node_info.get("containerRuntimeVersion"),
            "kubelet_version": node_info.get("kubeletVersion"),
            "architecture": node_info.get("architecture"),
            "os_image": node_info.get("osImage"),
        },
        "network_policy": {
            "selecting_policy_names": [p.get("metadata", {}).get("name") for p in selecting],
            "inventory_sha256": _canonical_hash(policy_projection),
            "declarative_default_deny_present": True,
            "obvious_broad_allow_present": False,
            "cni_identity_observed": False,
            "enforcement_observed": False,
            "active_probe_required": True,
        },
        "storage": {
            "inventory": storage_projection,
            "inventory_sha256": _canonical_hash(storage_projection),
            "nonroot_rw_semantics_observed": False,
            "post_replacement_rw_semantics_observed": False,
            "active_probe_required": True,
        },
        "security": {
            "read_only_root": True,
            "run_as_non_root_uid_gid": _REQUIRED_UID_GID,
            "pod_fs_group": _REQUIRED_UID_GID,
            "no_privilege_escalation": True,
            "all_capabilities_dropped": True,
            "runtime_default_seccomp": True,
            "host_namespaces_disabled": True,
            "service_account_token_automount_disabled": True,
            "host_path_absent": True,
            "readiness_liveness_separated": True,
        },
        "tier2": {
            "pod_uid_observed": pod_uid,
            "sandbox_vm_identity_observed": False,
            "full_replacement_observed": False,
        },
        "missing_acceptance_evidence": [
            "fresh supported Kata runtime version plus exact effective runtime/hypervisor/shared-filesystem configuration",
            "independent sandbox/VM identity proving the guest boundary and later Tier-2 replacement",
            "CNI identity plus active default-deny and reviewed-allow enforcement probes",
            "non-root persistent-volume create/write/fsync/read/rename/delete before and after replacement",
            "Tier-2 new Pod UID plus new sandbox/VM identity and new canonical generation",
            "remaining ClayVerse OCI/auth/PTY/Claude/effect/recovery/concurrency acceptance matrix",
        ],
    }


def _collect_storage_inventory(kubectl: Kubectl, pod: dict[str, Any], namespace: str) -> list[dict[str, Any]]:
    spec = pod.get("spec", {})
    volumes = spec.get("volumes", [])
    _require(isinstance(volumes, list), "pod volumes must be a list")
    inventory: list[dict[str, Any]] = []
    for volume in volumes:
        if not isinstance(volume, dict):
            raise AttestationError("pod volume must be an object")
        name = volume.get("name")
        if name not in _REQUIRED_PERSISTENT_MOUNTS:
            continue
        pvc_ref = volume.get("persistentVolumeClaim")
        _require(isinstance(pvc_ref, dict), f"{name} must be a persistentVolumeClaim")
        claim_name = pvc_ref.get("claimName")
        _require(isinstance(claim_name, str) and claim_name, f"{name} claimName missing")
        pvc = kubectl.json(["get", "pvc", claim_name, "-n", namespace])
        pvc_spec = pvc.get("spec", {})
        _require(isinstance(pvc_spec, dict), "PVC spec must be an object")
        pv_name = pvc_spec.get("volumeName")
        _require(isinstance(pv_name, str) and pv_name, "PVC is not bound to a PV")
        pv = kubectl.json(["get", "pv", pv_name])
        pv_spec = pv.get("spec", {})
        _require(isinstance(pv_spec, dict), "PV spec must be an object")
        storage_class = pvc_spec.get("storageClassName") or pv_spec.get("storageClassName")
        _require(isinstance(storage_class, str) and storage_class, "storageClass identity missing")
        csi = pv_spec.get("csi")
        _require(isinstance(csi, dict), "persistent volume has no CSI driver identity")
        csi_driver = csi.get("driver")
        _require(isinstance(csi_driver, str) and csi_driver, "CSI driver identity missing")
        sc = kubectl.json(["get", "storageclass", storage_class])
        csi_obj = kubectl.json(["get", "csidriver", csi_driver])
        inventory.append(
            {
                "volume_name": name,
                "mount_path": _REQUIRED_PERSISTENT_MOUNTS[name],
                "claim_name": claim_name,
                "pvc_uid": pvc.get("metadata", {}).get("uid"),
                "pv_name": pv_name,
                "pv_uid": pv.get("metadata", {}).get("uid"),
                "storage_class": storage_class,
                "storage_class_uid": sc.get("metadata", {}).get("uid"),
                "volume_binding_mode": sc.get("volumeBindingMode"),
                "allow_volume_expansion": sc.get("allowVolumeExpansion"),
                "csi_driver": csi_driver,
                "csi_driver_uid": csi_obj.get("metadata", {}).get("uid"),
                "csi_fs_group_policy": csi_obj.get("spec", {}).get("fsGroupPolicy"),
                "csi_requires_republish": csi_obj.get("spec", {}).get("requiresRepublish"),
                "csi_se_linux_mount": csi_obj.get("spec", {}).get("seLinuxMount"),
            }
        )
    return inventory


def _parse_allowed_annotations(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        _require("=" in item, "--allow-kata-annotation requires KEY=VALUE")
        key, value = item.split("=", 1)
        _require(key.startswith(_KATA_ANNOTATION_PREFIX), "allowed Kata annotation must use io.katacontainers.*")
        _require(key not in result, "duplicate allowed Kata annotation")
        result[key] = value
    return result


def collect(args: argparse.Namespace) -> dict[str, Any]:
    kubectl = Kubectl(binary=args.kubectl, timeout_seconds=args.timeout_seconds)
    pod = kubectl.json(["get", "pod", args.pod, "-n", args.namespace])
    _require(pod.get("spec", {}).get("runtimeClassName") == args.expected_runtime_class, "pod RuntimeClass differs before lookup")
    runtime_class = kubectl.json(["get", "runtimeclass", args.expected_runtime_class])
    node_name = pod.get("spec", {}).get("nodeName")
    _require(isinstance(node_name, str) and node_name, "pod nodeName is missing")
    node = kubectl.json(["get", "node", node_name])
    policies = kubectl.json(["get", "networkpolicy", "-n", args.namespace])
    storage_inventory = _collect_storage_inventory(kubectl, pod, args.namespace)
    guest_kernel = kubectl.text(["exec", "-n", args.namespace, args.pod, "-c", "clayverse", "--", "uname", "-r"])
    return attest_snapshot(
        pod=pod,
        runtime_class=runtime_class,
        node=node,
        network_policies=policies,
        storage_inventory=storage_inventory,
        guest_kernel=guest_kernel,
        expected_image_digest=args.expected_image_digest,
        expected_runtime_class=args.expected_runtime_class,
        allowed_kata_annotations=_parse_allowed_annotations(args.allow_kata_annotation),
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--pod", required=True)
    parser.add_argument("--expected-image-digest", required=True)
    parser.add_argument("--expected-runtime-class", default="kata-qemu-runtime-rs")
    parser.add_argument("--allow-kata-annotation", action="append", default=[])
    parser.add_argument("--kubectl", default="kubectl")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if args.timeout_seconds <= 0 or args.timeout_seconds > 120:
        parser.error("--timeout-seconds must be in 1..120")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = collect(args)
    except AttestationError as exc:
        failure = {
            "schema": "clayverse-microvm-attestation/v2",
            "scope_pass": False,
            "whole_product_pass": False,
            "classification": "FAIL_CLOSED",
            "error": str(exc),
        }
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        return 2
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        try:
            with open(args.output, "x", encoding="utf-8") as handle:
                handle.write(rendered)
        except OSError as exc:
            print(json.dumps({"schema": "clayverse-microvm-attestation/v2", "scope_pass": False, "whole_product_pass": False, "classification": "FAIL_CLOSED", "error": f"output write failed: {type(exc).__name__}"}, sort_keys=True), file=sys.stderr)
            return 2
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
