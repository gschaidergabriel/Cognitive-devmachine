#!/usr/bin/env python3
"""Fail-closed Kubernetes snapshot collector for ClayVerse MicroVM acceptance.

This is deployment evidence tooling, not a ClayVerse service. Kubernetes objects can
prove observed identity/declarative state, not Kata version/configuration, CNI
enforcement, host isolation, volume write semantics, Tier-2 replacement, or whole-product PASS.
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

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
KATA_PREFIX = "io.katacontainers."
UID_GID = 10001
PERSISTENT_MOUNTS = {
    "clayverse-state": "/var/lib/clayverse",
    "clayverse-workspace": "/workspace",
}


class AttestationError(RuntimeError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AttestationError(message)


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Kubectl:
    binary: str = "kubectl"
    timeout_seconds: int = 20

    def run(self, args: list[str]) -> str:
        try:
            proc = subprocess.run(
                [self.binary, *args], check=False, capture_output=True, text=True,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AttestationError(f"kubectl execution failed: {type(exc).__name__}") from exc
        require(proc.returncode == 0, f"kubectl failed rc={proc.returncode}: {proc.stderr.strip()[:400]}")
        return proc.stdout

    def json(self, args: list[str]) -> dict[str, Any]:
        try:
            value = json.loads(self.run([*args, "-o", "json"]))
        except json.JSONDecodeError as exc:
            raise AttestationError("kubectl returned non-JSON data") from exc
        require(isinstance(value, dict), "kubectl JSON root must be an object")
        return value

    def text(self, args: list[str]) -> str:
        value = self.run(args).strip()
        require(bool(value), "kubectl returned empty text")
        return value


def selector_matches(selector: dict[str, Any], labels: dict[str, str]) -> bool:
    match_labels = selector.get("matchLabels", {})
    require(isinstance(match_labels, dict), "matchLabels must be an object")
    for key, expected in match_labels.items():
        require(isinstance(key, str) and isinstance(expected, str), "matchLabels must be strings")
        if labels.get(key) != expected:
            return False
    expressions = selector.get("matchExpressions", [])
    require(isinstance(expressions, list), "matchExpressions must be a list")
    for expr in expressions:
        require(isinstance(expr, dict), "selector expression must be an object")
        key, op, values = expr.get("key"), expr.get("operator"), expr.get("values", [])
        require(isinstance(key, str) and key, "selector key invalid")
        require(op in {"In", "NotIn", "Exists", "DoesNotExist"}, "selector operator unsupported")
        require(isinstance(values, list) and all(isinstance(v, str) for v in values), "selector values invalid")
        if op in {"In", "NotIn"}:
            require(bool(values), f"selector {op} requires values")
        else:
            require(not values, f"selector {op} must not contain values")
        if op == "In" and (key not in labels or labels[key] not in values): return False
        if op == "NotIn" and key in labels and labels[key] in values: return False
        if op == "Exists" and key not in labels: return False
        if op == "DoesNotExist" and key in labels: return False
    return True


def selecting_policies(policies: dict[str, Any], labels: dict[str, str]) -> list[dict[str, Any]]:
    items = policies.get("items")
    require(isinstance(items, list), "NetworkPolicy list missing items")
    selected = []
    for policy in items:
        require(isinstance(policy, dict), "NetworkPolicy item must be an object")
        spec = policy.get("spec", {})
        require(isinstance(spec, dict), "NetworkPolicy spec must be an object")
        selector = spec.get("podSelector", {})
        require(isinstance(selector, dict), "NetworkPolicy podSelector must be an object")
        if selector_matches(selector, labels):
            selected.append(policy)
    return sorted(selected, key=lambda p: str(p.get("metadata", {}).get("name", "")))


def peer_obviously_broad(peer: dict[str, Any]) -> bool:
    if not peer:
        return True
    block = peer.get("ipBlock")
    if isinstance(block, dict) and block.get("cidr") in {"0.0.0.0/0", "::/0"}:
        return True
    ns, pod = peer.get("namespaceSelector"), peer.get("podSelector")
    return (ns == {} and pod in (None, {})) or (pod == {} and ns is None)


def policy_obviously_broad(policy: dict[str, Any]) -> bool:
    spec = policy.get("spec", {})
    for direction, peer_key in (("ingress", "from"), ("egress", "to")):
        rules = spec.get(direction, [])
        require(isinstance(rules, list), f"NetworkPolicy {direction} must be a list")
        for rule in rules:
            require(isinstance(rule, dict), f"NetworkPolicy {direction} rule must be an object")
            if not rule or peer_key not in rule:
                return True
            peers = rule[peer_key]
            require(isinstance(peers, list), f"NetworkPolicy {peer_key} must be a list")
            for peer in peers:
                require(isinstance(peer, dict), f"NetworkPolicy {peer_key} peer must be an object")
                if peer_obviously_broad(peer):
                    return True
    return False


def kata_annotations(pod: dict[str, Any]) -> dict[str, str]:
    annotations = pod.get("metadata", {}).get("annotations", {}) or {}
    require(isinstance(annotations, dict), "pod annotations must be an object")
    result = {}
    for key, value in annotations.items():
        require(isinstance(key, str) and isinstance(value, str), "pod annotations must be strings")
        if key.startswith(KATA_PREFIX):
            result[key] = value
    return dict(sorted(result.items()))


def probe_path(probe: Any) -> str | None:
    if not isinstance(probe, dict) or not isinstance(probe.get("httpGet"), dict):
        return None
    path = probe["httpGet"].get("path")
    return path if isinstance(path, str) else None


def validate_storage(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    require(isinstance(items, list), "storage inventory must be a list")
    by_name = {}
    identity = ("claim_name", "pvc_uid", "pv_name", "pv_uid", "storage_class", "storage_class_uid", "csi_driver", "csi_driver_uid")
    for item in items:
        require(isinstance(item, dict), "storage inventory item must be an object")
        name = item.get("volume_name")
        require(name in PERSISTENT_MOUNTS, "unexpected persistent volume identity")
        require(name not in by_name, "duplicate storage inventory volume")
        for key in identity:
            require(isinstance(item.get(key), str) and item[key], f"storage inventory missing {key}")
        require(item.get("mount_path") == PERSISTENT_MOUNTS[name], "storage inventory mount_path drift")
        by_name[name] = item
    require(set(by_name) == set(PERSISTENT_MOUNTS), "storage inventory must cover both persistent mounts")
    return [by_name[name] for name in sorted(by_name)]


def attest_snapshot(*, pod: dict[str, Any], runtime_class: dict[str, Any], node: dict[str, Any],
                    network_policies: dict[str, Any], storage_inventory: list[dict[str, Any]],
                    guest_kernel: str, expected_image_digest: str, expected_runtime_class: str,
                    allowed_kata_annotations: dict[str, str] | None = None) -> dict[str, Any]:
    require(DIGEST_RE.fullmatch(expected_image_digest) is not None, "invalid expected image digest")
    require(bool(guest_kernel.strip()), "guest kernel identity is empty")
    expected_annotations = dict(sorted((allowed_kata_annotations or {}).items()))
    for key, value in expected_annotations.items():
        require(key.startswith(KATA_PREFIX) and isinstance(value, str), "invalid expected Kata annotation")

    metadata, spec, status = pod.get("metadata", {}), pod.get("spec", {}), pod.get("status", {})
    require(all(isinstance(v, dict) for v in (metadata, spec, status)), "pod object malformed")
    labels = metadata.get("labels", {})
    require(isinstance(labels, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in labels.items()), "pod labels invalid")
    effective_annotations = kata_annotations(pod)
    require(effective_annotations == expected_annotations, "effective io.katacontainers.* annotations differ from declared expected allowset")

    require(spec.get("runtimeClassName") == expected_runtime_class, "pod RuntimeClass drift")
    require(runtime_class.get("metadata", {}).get("name") == expected_runtime_class, "RuntimeClass object drift")
    handler = runtime_class.get("handler")
    require(isinstance(handler, str) and handler, "RuntimeClass handler missing")
    for key in ("hostNetwork", "hostPID", "hostIPC"):
        require(spec.get(key) is False, f"{key} must be false")
    require(spec.get("automountServiceAccountToken") is False, "ServiceAccount token automount must be false")

    pod_sec = spec.get("securityContext", {})
    require(isinstance(pod_sec, dict), "pod securityContext missing")
    require(pod_sec.get("fsGroup") == UID_GID, "pod fsGroup must be 10001")
    require(pod_sec.get("fsGroupChangePolicy") == "OnRootMismatch", "fsGroupChangePolicy drift")
    require(pod_sec.get("seccompProfile", {}).get("type") == "RuntimeDefault", "seccompProfile drift")

    containers = spec.get("containers")
    require(isinstance(containers, list) and len(containers) == 1, "expected one application container")
    container = containers[0]
    require(isinstance(container, dict) and container.get("name") == "clayverse", "ClayVerse container identity drift")
    image = container.get("image")
    require(isinstance(image, str) and image.endswith("@" + expected_image_digest), "pod spec image digest drift")
    csec = container.get("securityContext", {})
    require(csec.get("runAsNonRoot") is True, "runAsNonRoot must be true")
    require(csec.get("runAsUser") == UID_GID and csec.get("runAsGroup") == UID_GID, "runtime uid/gid drift")
    require(csec.get("readOnlyRootFilesystem") is True, "readOnlyRootFilesystem must be true")
    require(csec.get("allowPrivilegeEscalation") is False, "allowPrivilegeEscalation must be false")
    require(set(csec.get("capabilities", {}).get("drop", [])) == {"ALL"}, "capability drop drift")
    require(probe_path(container.get("readinessProbe")) == "/readyz", "readiness probe must use /readyz")
    require(probe_path(container.get("livenessProbe")) == "/healthz", "liveness probe must use /healthz")

    mounts = {m.get("name"): m.get("mountPath") for m in container.get("volumeMounts", []) if isinstance(m, dict)}
    for name, path in PERSISTENT_MOUNTS.items():
        require(mounts.get(name) == path, f"persistent mount drift: {name}")
    volumes = spec.get("volumes", [])
    require(isinstance(volumes, list), "pod volumes must be a list")
    for volume in volumes:
        require(isinstance(volume, dict), "pod volume must be an object")
        require("hostPath" not in volume, "hostPath volume is forbidden")
    pvc_names = {v.get("name") for v in volumes if isinstance(v.get("persistentVolumeClaim"), dict)}
    require(set(PERSISTENT_MOUNTS).issubset(pvc_names), "persistent PVC volumes are missing")
    storage = validate_storage(storage_inventory)

    statuses = status.get("containerStatuses")
    require(isinstance(statuses, list), "containerStatuses missing")
    matches = [x for x in statuses if isinstance(x, dict) and x.get("name") == "clayverse"]
    require(len(matches) == 1, "ClayVerse container status identity drift")
    image_id = matches[0].get("imageID")
    require(isinstance(image_id, str) and expected_image_digest in image_id, "runtime imageID digest drift")
    require(matches[0].get("ready") is True, "ClayVerse container is not ready")

    node_name = spec.get("nodeName")
    require(isinstance(node_name, str) and node_name, "pod nodeName missing")
    require(node.get("metadata", {}).get("name") == node_name, "node object identity drift")
    node_info = node.get("status", {}).get("nodeInfo", {})
    host_kernel = node_info.get("kernelVersion") if isinstance(node_info, dict) else None
    require(isinstance(host_kernel, str) and host_kernel, "host kernel identity missing")
    require(guest_kernel.strip() != host_kernel.strip(), "guest kernel is not distinguishable from host kernel")

    selected = selecting_policies(network_policies, labels)
    require(selected, "no NetworkPolicy selects the ClayVerse pod")
    deny = [p for p in selected if p.get("metadata", {}).get("name") == "clayverse-default-deny"]
    require(len(deny) == 1, "exact clayverse-default-deny policy is required")
    deny_spec = deny[0].get("spec", {})
    require(set(deny_spec.get("policyTypes", [])) == {"Ingress", "Egress"}, "default deny policyTypes drift")
    require(deny_spec.get("ingress", []) == [] and deny_spec.get("egress", []) == [], "default deny rules must be empty")
    broad = [str(p.get("metadata", {}).get("name", "<unnamed>")) for p in selected if policy_obviously_broad(p)]
    require(not broad, "obvious broad NetworkPolicy allow detected: " + ",".join(broad))
    policy_projection = [{
        "apiVersion": p.get("apiVersion"), "kind": p.get("kind"),
        "namespace": p.get("metadata", {}).get("namespace"), "name": p.get("metadata", {}).get("name"),
        "uid": p.get("metadata", {}).get("uid"), "resourceVersion": p.get("metadata", {}).get("resourceVersion"),
        "spec": p.get("spec"),
    } for p in selected]

    pod_uid = metadata.get("uid")
    require(isinstance(pod_uid, str) and pod_uid, "pod UID missing")
    return {
        "schema": "clayverse-microvm-attestation/v3",
        "scope_pass": True,
        "whole_product_pass": False,
        "classification": "KUBERNETES_SNAPSHOT_ATTESTED_EXTERNAL_ACCEPTANCE_GATES_OPEN",
        "expectations": {
            "image_digest": expected_image_digest,
            "runtime_class": expected_runtime_class,
            "kata_annotations": expected_annotations,
            "source": "caller_supplied",
            "external_review_binding_observed": False,
        },
        "pod": {
            "namespace": metadata.get("namespace"), "name": metadata.get("name"), "uid": pod_uid, "node": node_name,
            "effective_kata_annotations": effective_annotations,
            "kata_annotation_inventory_sha256": canonical_hash(effective_annotations),
        },
        "image": {"spec": image, "runtime_image_id": image_id, "runtime_image_id_observed": True},
        "runtime": {
            "runtime_class": expected_runtime_class, "handler": handler,
            "host_kernel": host_kernel, "guest_kernel": guest_kernel.strip(),
            "guest_kernel_distinguishable_from_host": True,
            "independent_guest_kernel_proven_by_this_collector": False,
            "kata_runtime_version_observed": False, "kata_runtime_configuration_observed": False,
            "container_runtime_version": node_info.get("containerRuntimeVersion"),
            "kubelet_version": node_info.get("kubeletVersion"), "architecture": node_info.get("architecture"),
        },
        "network_policy": {
            "selecting_policy_names": [p.get("metadata", {}).get("name") for p in selected],
            "inventory_sha256": canonical_hash(policy_projection), "declarative_default_deny_present": True,
            "obvious_broad_allow_present": False, "selecting_policy_review_observed": False,
            "cni_identity_observed": False, "enforcement_observed": False, "active_probe_required": True,
        },
        "storage": {
            "inventory": storage, "inventory_sha256": canonical_hash(storage),
            "nonroot_rw_semantics_observed": False, "post_replacement_rw_semantics_observed": False,
            "active_probe_required": True,
        },
        "security": {
            "declarative_profile_attested": True, "runtime_enforcement_observed": False,
            "read_only_root_declared": True, "host_namespaces_disabled_declared": True,
            "service_account_token_automount_disabled_declared": True, "host_path_absent_from_pod_spec": True,
            "runtime_default_seccomp_declared": True, "readiness_liveness_separated_declared": True,
            "active_enforcement_probe_required": True,
        },
        "tier2": {"pod_uid_observed": pod_uid, "sandbox_vm_identity_observed": False, "full_replacement_observed": False},
        "missing_acceptance_evidence": [
            "external reviewed binding for caller-supplied image digest, RuntimeClass and Kata annotation expectation set",
            "fresh supported Kata runtime version plus exact effective runtime/hypervisor/shared-filesystem configuration",
            "independent sandbox/VM identity proving the guest boundary and later Tier-2 replacement",
            "external review of the complete selecting NetworkPolicy inventory plus CNI identity and active enforcement probes",
            "active read-only-root/host-isolation enforcement probes",
            "non-root persistent-volume create/write/fsync/read/rename/delete before and after replacement",
            "Tier-2 new Pod UID plus new sandbox/VM identity and new canonical generation",
            "remaining ClayVerse OCI/auth/PTY/Claude/effect/recovery/concurrency acceptance matrix",
        ],
    }


def collect_storage(k: Kubectl, pod: dict[str, Any], namespace: str) -> list[dict[str, Any]]:
    inventory = []
    for volume in pod.get("spec", {}).get("volumes", []):
        require(isinstance(volume, dict), "pod volume must be an object")
        name = volume.get("name")
        if name not in PERSISTENT_MOUNTS:
            continue
        pvc_ref = volume.get("persistentVolumeClaim")
        require(isinstance(pvc_ref, dict), f"{name} must be a persistentVolumeClaim")
        claim = pvc_ref.get("claimName")
        require(isinstance(claim, str) and claim, f"{name} claimName missing")
        pvc = k.json(["get", "pvc", claim, "-n", namespace]); pvc_spec = pvc.get("spec", {})
        pv_name = pvc_spec.get("volumeName") if isinstance(pvc_spec, dict) else None
        require(isinstance(pv_name, str) and pv_name, "PVC is not bound to a PV")
        pv = k.json(["get", "pv", pv_name]); pv_spec = pv.get("spec", {})
        sc_name = pvc_spec.get("storageClassName") or (pv_spec.get("storageClassName") if isinstance(pv_spec, dict) else None)
        csi = pv_spec.get("csi") if isinstance(pv_spec, dict) else None
        driver = csi.get("driver") if isinstance(csi, dict) else None
        require(isinstance(sc_name, str) and sc_name, "storageClass identity missing")
        require(isinstance(driver, str) and driver, "CSI driver identity missing")
        sc, csi_obj = k.json(["get", "storageclass", sc_name]), k.json(["get", "csidriver", driver])
        inventory.append({
            "volume_name": name, "mount_path": PERSISTENT_MOUNTS[name], "claim_name": claim,
            "pvc_uid": pvc.get("metadata", {}).get("uid"), "pv_name": pv_name, "pv_uid": pv.get("metadata", {}).get("uid"),
            "storage_class": sc_name, "storage_class_uid": sc.get("metadata", {}).get("uid"),
            "volume_binding_mode": sc.get("volumeBindingMode"), "allow_volume_expansion": sc.get("allowVolumeExpansion"),
            "csi_driver": driver, "csi_driver_uid": csi_obj.get("metadata", {}).get("uid"),
            "csi_fs_group_policy": csi_obj.get("spec", {}).get("fsGroupPolicy"),
        })
    return inventory


def parse_expected_annotations(items: list[str]) -> dict[str, str]:
    result = {}
    for item in items:
        require("=" in item, "--expect-kata-annotation requires KEY=VALUE")
        key, value = item.split("=", 1)
        require(key.startswith(KATA_PREFIX), "expected Kata annotation must use io.katacontainers.*")
        require(key not in result, "duplicate expected Kata annotation")
        result[key] = value
    return result


def collect(args: argparse.Namespace) -> dict[str, Any]:
    k = Kubectl(args.kubectl, args.timeout_seconds)
    pod = k.json(["get", "pod", args.pod, "-n", args.namespace])
    node_name = pod.get("spec", {}).get("nodeName")
    require(isinstance(node_name, str) and node_name, "pod nodeName missing")
    return attest_snapshot(
        pod=pod,
        runtime_class=k.json(["get", "runtimeclass", args.expected_runtime_class]),
        node=k.json(["get", "node", node_name]),
        network_policies=k.json(["get", "networkpolicy", "-n", args.namespace]),
        storage_inventory=collect_storage(k, pod, args.namespace),
        guest_kernel=k.text(["exec", "-n", args.namespace, args.pod, "-c", "clayverse", "--", "uname", "-r"]),
        expected_image_digest=args.expected_image_digest,
        expected_runtime_class=args.expected_runtime_class,
        allowed_kata_annotations=parse_expected_annotations(args.expect_kata_annotation),
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--namespace", required=True); p.add_argument("--pod", required=True)
    p.add_argument("--expected-image-digest", required=True)
    p.add_argument("--expected-runtime-class", default="kata-qemu-runtime-rs")
    p.add_argument("--expect-kata-annotation", action="append", default=[])
    p.add_argument("--kubectl", default="kubectl"); p.add_argument("--timeout-seconds", type=int, default=20)
    p.add_argument("--output")
    args = p.parse_args(argv)
    if not 1 <= args.timeout_seconds <= 120: p.error("--timeout-seconds must be in 1..120")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = collect(args)
        rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.output:
            with open(args.output, "x", encoding="utf-8") as f: f.write(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except (AttestationError, OSError) as exc:
        print(json.dumps({
            "schema": "clayverse-microvm-attestation/v3", "scope_pass": False,
            "whole_product_pass": False, "classification": "FAIL_CLOSED",
            "error": f"{type(exc).__name__}: {exc}",
        }, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
