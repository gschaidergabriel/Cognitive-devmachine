#!/usr/bin/env python3
"""Collect fail-closed ClayVerse MicroVM deployment evidence from Kubernetes.

This collector proves only the bounded runtime identity/policy-inventory facts it can
observe. It MUST NOT convert declarative NetworkPolicy objects into network-enforcement
or whole-product PASS. Active deny/allow probes and the rest of the ClayVerse acceptance
matrix remain separate required evidence.
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
            stderr = proc.stderr.strip()
            raise AttestationError(
                f"kubectl command failed rc={proc.returncode}: {stderr[:400]}"
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
        if labels.get(str(key)) != expected:
            return False

    expressions = selector.get("matchExpressions", [])
    _require(isinstance(expressions, list), "podSelector.matchExpressions must be a list")
    for expr in expressions:
        _require(isinstance(expr, dict), "podSelector expression must be an object")
        key = expr.get("key")
        operator = expr.get("operator")
        values = expr.get("values", [])
        _require(isinstance(key, str) and key, "selector expression key is invalid")
        _require(isinstance(operator, str), "selector expression operator is invalid")
        _require(isinstance(values, list), "selector expression values must be a list")
        if operator == "In":
            if key not in labels or labels[key] not in values:
                return False
        elif operator == "NotIn":
            if key not in labels or labels[key] in values:
                return False
        elif operator == "Exists":
            if key not in labels:
                return False
        elif operator == "DoesNotExist":
            if key in labels:
                return False
        else:
            raise AttestationError(f"unsupported label selector operator: {operator}")
    return True


def _peer_is_broad(peer: dict[str, Any]) -> bool:
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
            if not rule:
                return True
            if peer_key not in rule:
                return True
            peers = rule.get(peer_key)
            _require(isinstance(peers, list), f"NetworkPolicy {peer_key} must be a list")
            if any(_peer_is_broad(peer) for peer in peers if isinstance(peer, dict)):
                return True
    return False


def _selecting_policies(policies: dict[str, Any], labels: dict[str, str]) -> list[dict[str, Any]]:
    items = policies.get("items")
    _require(isinstance(items, list), "NetworkPolicy list must contain items")
    selected: list[dict[str, Any]] = []
    for policy in items:
        _require(isinstance(policy, dict), "NetworkPolicy item must be an object")
        selector = policy.get("spec", {}).get("podSelector", {})
        _require(isinstance(selector, dict), "NetworkPolicy podSelector must be an object")
        if _selector_matches(selector, labels):
            selected.append(policy)
    selected.sort(key=lambda p: str(p.get("metadata", {}).get("name", "")))
    return selected


def attest_snapshot(
    *,
    pod: dict[str, Any],
    runtime_class: dict[str, Any],
    node: dict[str, Any],
    network_policies: dict[str, Any],
    guest_kernel: str,
    expected_image_digest: str,
    expected_runtime_class: str,
) -> dict[str, Any]:
    _require(_DIGEST_RE.fullmatch(expected_image_digest) is not None, "invalid expected image digest")
    _require(bool(guest_kernel.strip()), "guest kernel identity is empty")

    metadata = pod.get("metadata", {})
    spec = pod.get("spec", {})
    status = pod.get("status", {})
    _require(isinstance(metadata, dict) and isinstance(spec, dict) and isinstance(status, dict), "pod object is malformed")
    labels = metadata.get("labels", {})
    _require(isinstance(labels, dict), "pod labels must be an object")

    _require(spec.get("runtimeClassName") == expected_runtime_class, "pod RuntimeClass drift")
    _require(runtime_class.get("metadata", {}).get("name") == expected_runtime_class, "RuntimeClass object name drift")
    runtime_handler = runtime_class.get("handler")
    _require(isinstance(runtime_handler, str) and runtime_handler, "RuntimeClass handler is missing")

    _require(spec.get("hostNetwork") is False, "hostNetwork must be false")
    _require(spec.get("hostPID") is False, "hostPID must be false")
    _require(spec.get("hostIPC") is False, "hostIPC must be false")
    _require(spec.get("automountServiceAccountToken") is False, "ServiceAccount token automount must be false")

    containers = spec.get("containers")
    _require(isinstance(containers, list) and len(containers) == 1, "expected exactly one application container")
    container = containers[0]
    _require(container.get("name") == "clayverse", "application container must be named clayverse")
    image = container.get("image")
    _require(isinstance(image, str) and image.endswith("@" + expected_image_digest), "pod spec image digest drift")
    security = container.get("securityContext", {})
    _require(security.get("runAsNonRoot") is True, "runAsNonRoot must be true")
    _require(security.get("readOnlyRootFilesystem") is True, "readOnlyRootFilesystem must be true")
    _require(security.get("allowPrivilegeEscalation") is False, "allowPrivilegeEscalation must be false")
    drops = security.get("capabilities", {}).get("drop", [])
    _require(isinstance(drops, list) and "ALL" in drops, "all Linux capabilities must be dropped")

    for volume in spec.get("volumes", []):
        _require(isinstance(volume, dict), "pod volume must be an object")
        _require("hostPath" not in volume, "hostPath volume is forbidden")

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
    default_deny = [
        p for p in selecting if p.get("metadata", {}).get("name") == "clayverse-default-deny"
    ]
    _require(len(default_deny) == 1, "exact clayverse-default-deny policy is required")
    deny_spec = default_deny[0].get("spec", {})
    policy_types = deny_spec.get("policyTypes", [])
    _require(isinstance(policy_types, list), "default-deny policyTypes are malformed")
    _require(set(policy_types) == {"Ingress", "Egress"}, "default deny must cover ingress and egress")
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
            "name": p.get("metadata", {}).get("name"),
            "uid": p.get("metadata", {}).get("uid"),
            "resourceVersion": p.get("metadata", {}).get("resourceVersion"),
            "spec": p.get("spec"),
        }
        for p in selecting
    ]

    return {
        "schema": "clayverse-microvm-attestation/v1",
        "scope_pass": True,
        "whole_product_pass": False,
        "classification": "MICROVM_RUNTIME_IDENTITY_AND_POLICY_INVENTORY_ATTESTED_NETWORK_ENFORCEMENT_UNOBSERVED",
        "pod": {
            "namespace": metadata.get("namespace"),
            "name": metadata.get("name"),
            "uid": metadata.get("uid"),
            "node": node_name,
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
            "enforcement_observed": False,
            "active_probe_required": True,
        },
        "security": {
            "read_only_root": True,
            "run_as_non_root": True,
            "no_privilege_escalation": True,
            "all_capabilities_dropped": True,
            "host_namespaces_disabled": True,
            "service_account_token_automount_disabled": True,
            "host_path_absent": True,
        },
    }


def collect(args: argparse.Namespace) -> dict[str, Any]:
    kubectl = Kubectl(binary=args.kubectl, timeout_seconds=args.timeout_seconds)
    pod = kubectl.json(["get", "pod", args.pod, "-n", args.namespace])
    runtime_name = pod.get("spec", {}).get("runtimeClassName")
    _require(runtime_name == args.expected_runtime_class, "pod RuntimeClass differs before lookup")
    runtime_class = kubectl.json(["get", "runtimeclass", args.expected_runtime_class])
    node_name = pod.get("spec", {}).get("nodeName")
    _require(isinstance(node_name, str) and node_name, "pod nodeName is missing")
    node = kubectl.json(["get", "node", node_name])
    policies = kubectl.json(["get", "networkpolicy", "-n", args.namespace])
    guest_kernel = kubectl.text(
        ["exec", "-n", args.namespace, args.pod, "-c", "clayverse", "--", "uname", "-r"]
    )
    return attest_snapshot(
        pod=pod,
        runtime_class=runtime_class,
        node=node,
        network_policies=policies,
        guest_kernel=guest_kernel,
        expected_image_digest=args.expected_image_digest,
        expected_runtime_class=args.expected_runtime_class,
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--pod", required=True)
    parser.add_argument("--expected-image-digest", required=True)
    parser.add_argument("--expected-runtime-class", default="kata-qemu-runtime-rs")
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
            "schema": "clayverse-microvm-attestation/v1",
            "scope_pass": False,
            "whole_product_pass": False,
            "classification": "FAIL_CLOSED",
            "error": str(exc),
        }
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        return 2
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        with open(args.output, "x", encoding="utf-8") as handle:
            handle.write(rendered)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
