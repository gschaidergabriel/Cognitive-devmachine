#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIER2_EXIT_CODE = 86
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class ControllerError(RuntimeError):
    pass


class KubernetesObjectNotFound(ControllerError):
    pass


class KubernetesConflict(ControllerError):
    pass


def _required_text(value: object, name: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str):
        raise ControllerError(f"{name} must be text")
    value = value.strip()
    if not value or len(value) > max_len or any(ord(ch) < 0x21 or ord(ch) > 0x7E for ch in value):
        raise ControllerError(f"{name} has invalid shape")
    return value


def _container(spec: dict, name: str) -> dict:
    containers = spec.get("containers")
    if not isinstance(containers, list):
        raise ControllerError("Pod spec containers are missing")
    matches = [item for item in containers if isinstance(item, dict) and item.get("name") == name]
    if len(matches) != 1:
        raise ControllerError(f"expected exactly one {name} container")
    return matches[0]


def _container_status(status: dict, name: str) -> dict | None:
    statuses = status.get("containerStatuses")
    if statuses is None:
        return None
    if not isinstance(statuses, list):
        raise ControllerError("Pod containerStatuses has invalid shape")
    matches = [item for item in statuses if isinstance(item, dict) and item.get("name") == name]
    if not matches:
        return None
    if len(matches) != 1:
        raise ControllerError(f"expected at most one {name} container status")
    return matches[0]


def _tier2_termination(status: dict) -> dict | None:
    for key in ("state", "lastState"):
        state = status.get(key)
        if not isinstance(state, dict):
            continue
        terminated = state.get("terminated")
        if not isinstance(terminated, dict):
            continue
        exit_code = terminated.get("exitCode")
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            raise ControllerError("terminated exitCode has invalid shape")
        if exit_code == TIER2_EXIT_CODE:
            return terminated
    return None


def replacement_request(
    pod: dict,
    *,
    namespace: str,
    pod_name: str,
    expected_image_digest: str,
    runtime_class: str,
) -> dict[str, object] | None:
    """Return one exact-UID delete request only for the reserved Tier-2 exit signal."""
    if not isinstance(pod, dict):
        raise ControllerError("Pod response must be an object")
    if _DIGEST.fullmatch(expected_image_digest) is None:
        raise ControllerError("expected image digest must be sha256:<64 lowercase hex>")
    namespace = _required_text(namespace, "configured namespace", max_len=253)
    pod_name = _required_text(pod_name, "configured pod name", max_len=253)
    runtime_class = _required_text(runtime_class, "configured runtimeClass", max_len=253)

    metadata = pod.get("metadata")
    spec = pod.get("spec")
    status = pod.get("status")
    if not all(isinstance(item, dict) for item in (metadata, spec, status)):
        raise ControllerError("Pod object is missing metadata/spec/status")

    actual_namespace = _required_text(metadata.get("namespace"), "Pod namespace", max_len=253)
    actual_name = _required_text(metadata.get("name"), "Pod name", max_len=253)
    pod_uid = _required_text(metadata.get("uid"), "Pod UID", max_len=160)
    if actual_namespace != namespace or actual_name != pod_name:
        raise ControllerError("Pod identity does not match configured Tier-2 target")

    labels = metadata.get("labels") or {}
    if not isinstance(labels, dict) or labels.get("app") != "clayverse":
        raise ControllerError("Tier-2 target is not the canonical ClayVerse Pod")

    owners = metadata.get("ownerReferences")
    if not isinstance(owners, list):
        raise ControllerError("Tier-2 target is missing ownerReferences")
    controllers = [ref for ref in owners if isinstance(ref, dict) and ref.get("controller") is True]
    if len(controllers) != 1:
        raise ControllerError("Tier-2 target must have exactly one controller owner")
    owner = controllers[0]
    if owner.get("kind") != "StatefulSet" or owner.get("name") != "clayverse":
        raise ControllerError("Tier-2 target must be controlled by StatefulSet/clayverse")
    _required_text(owner.get("uid"), "StatefulSet owner UID", max_len=160)

    if spec.get("runtimeClassName") != runtime_class:
        raise ControllerError("Tier-2 target runtimeClass drifted")
    if spec.get("automountServiceAccountToken") is not False:
        raise ControllerError("ClayVerse Pod unexpectedly has ServiceAccount token automount")

    container = _container(spec, "clayverse")
    image = _required_text(container.get("image"), "ClayVerse image", max_len=1024)
    if not image.endswith("@" + expected_image_digest):
        raise ControllerError("ClayVerse Pod spec is not bound to the accepted image digest")

    cstatus = _container_status(status, "clayverse")
    if cstatus is None:
        return None
    image_id = _required_text(cstatus.get("imageID"), "ClayVerse runtime imageID", max_len=2048)
    if not (image_id == expected_image_digest or image_id.endswith("@" + expected_image_digest)):
        raise ControllerError("ClayVerse runtime imageID does not match the accepted digest")
    if _tier2_termination(cstatus) is None:
        return None

    return {
        "pod_uid": pod_uid,
        "delete_options": {
            "apiVersion": "v1",
            "kind": "DeleteOptions",
            "gracePeriodSeconds": 30,
            "propagationPolicy": "Foreground",
            "preconditions": {"uid": pod_uid},
        },
    }


class KubernetesAPI:
    def __init__(self, base_url: str, token_file: str, ca_file: str):
        self.base_url = _required_text(base_url, "Kubernetes API URL", max_len=2048).rstrip("/")
        parsed = urllib.parse.urlsplit(self.base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ControllerError("Kubernetes API URL must be a credential-free HTTPS origin")
        token = Path(token_file).read_text(encoding="utf-8").strip()
        if not token or len(token) > 16384 or any(ch.isspace() for ch in token):
            raise ControllerError("Kubernetes bearer token has invalid shape")
        self._token = token
        self._ssl = ssl.create_default_context(cafile=ca_file)

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer " + self._token,
                **({"Content-Type": "application/json"} if data is not None else {}),
            },
        )
        try:
            with urllib.request.urlopen(request, context=self._ssl, timeout=10) as response:
                raw = response.read(1_000_001)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise KubernetesObjectNotFound("Kubernetes object not found") from exc
            if exc.code == 409:
                raise KubernetesConflict("Kubernetes UID/resource precondition conflict") from exc
            raise ControllerError(f"Kubernetes API {method} failed with HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ControllerError(f"Kubernetes API {method} transport failure") from exc
        if len(raw) > 1_000_000:
            raise ControllerError("Kubernetes API response exceeded bound")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ControllerError("Kubernetes API returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise ControllerError("Kubernetes API returned non-object JSON")
        return value

    def get_pod(self, namespace: str, pod_name: str) -> dict | None:
        ns = urllib.parse.quote(namespace, safe="")
        name = urllib.parse.quote(pod_name, safe="")
        try:
            return self._request("GET", f"/api/v1/namespaces/{ns}/pods/{name}")
        except KubernetesObjectNotFound:
            return None

    def delete_pod(self, namespace: str, pod_name: str, options: dict) -> bool:
        ns = urllib.parse.quote(namespace, safe="")
        name = urllib.parse.quote(pod_name, safe="")
        try:
            self._request("DELETE", f"/api/v1/namespaces/{ns}/pods/{name}", options)
            return True
        except (KubernetesObjectNotFound, KubernetesConflict):
            # 404 means the exact old Pod is already gone. 409 means the UID
            # precondition no longer matches. Both are safe: never broaden the
            # deletion to a successor that reused clayverse-0.
            return False


def run_once(api: KubernetesAPI, *, namespace: str, pod_name: str, digest: str, runtime_class: str) -> bool:
    pod = api.get_pod(namespace, pod_name)
    if pod is None:
        return False
    request = replacement_request(
        pod,
        namespace=namespace,
        pod_name=pod_name,
        expected_image_digest=digest,
        runtime_class=runtime_class,
    )
    if request is None:
        return False
    deleted = api.delete_pod(namespace, pod_name, request["delete_options"])
    print(json.dumps({
        "status": "tier2_old_pod_delete_requested" if deleted else "tier2_old_pod_already_replaced_or_conflicted",
        "pod_uid": request["pod_uid"],
    }, sort_keys=True), flush=True)
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser(description="ClayVerse external Kubernetes Tier-2 full-sandbox replacer")
    parser.add_argument("--once", action="store_true", help="perform one exact-Pod check and exit")
    args = parser.parse_args()

    namespace = os.environ.get("CLAYVERSE_TIER2_NAMESPACE", "clayverse")
    pod_name = os.environ.get("CLAYVERSE_TIER2_POD_NAME", "clayverse-0")
    digest = os.environ.get("CLAYVERSE_TIER2_EXPECTED_IMAGE_DIGEST", "")
    runtime_class = os.environ.get("CLAYVERSE_TIER2_RUNTIME_CLASS", "kata-qemu-runtime-rs")
    api_url = os.environ.get("CLAYVERSE_TIER2_KUBE_API_URL", "")
    token_file = os.environ.get("CLAYVERSE_TIER2_KUBE_TOKEN_FILE", "")
    ca_file = os.environ.get("CLAYVERSE_TIER2_KUBE_CA_FILE", "")
    try:
        poll_seconds = float(os.environ.get("CLAYVERSE_TIER2_POLL_SECONDS", "2"))
    except ValueError as exc:
        raise ControllerError("Tier-2 poll interval must be numeric") from exc
    if not math.isfinite(poll_seconds) or not 0.5 <= poll_seconds <= 60:
        raise ControllerError("Tier-2 poll interval must be between 0.5 and 60 seconds")

    api = KubernetesAPI(api_url, token_file, ca_file)
    while True:
        run_once(api, namespace=namespace, pod_name=pod_name, digest=digest, runtime_class=runtime_class)
        if args.once:
            return 0
        time.sleep(poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
