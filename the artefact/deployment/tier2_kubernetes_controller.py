#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

TIER2_EXIT_CODE = 86
TIER2_SCHEMA = "clayverse.tier2-replacement/v1"
TIER2_ACTION = "replace_pod_sandbox"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_REASON = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")


class ControllerError(RuntimeError):
    pass


def _required_text(value: object, name: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str):
        raise ControllerError(f"{name} must be text")
    value = value.strip()
    if not value or len(value) > max_len or any(ord(ch) < 0x20 for ch in value):
        raise ControllerError(f"{name} has invalid shape")
    return value


def _container(spec: dict, name: str) -> dict:
    matches = [item for item in spec.get("containers", []) if isinstance(item, dict) and item.get("name") == name]
    if len(matches) != 1:
        raise ControllerError(f"expected exactly one {name} container")
    return matches[0]


def _container_status(status: dict, name: str) -> dict:
    matches = [item for item in status.get("containerStatuses", []) if isinstance(item, dict) and item.get("name") == name]
    if len(matches) != 1:
        raise ControllerError(f"expected exactly one {name} container status")
    return matches[0]


def _termination(status: dict) -> dict | None:
    candidates = []
    state = status.get("state")
    last_state = status.get("lastState")
    if isinstance(state, dict) and isinstance(state.get("terminated"), dict):
        candidates.append(state["terminated"])
    if isinstance(last_state, dict) and isinstance(last_state.get("terminated"), dict):
        candidates.append(last_state["terminated"])
    for terminated in candidates:
        if terminated.get("exitCode") == TIER2_EXIT_CODE:
            return terminated
    return None


def _decode_receipt(raw: object, *, pod_uid: str) -> dict[str, object]:
    if not isinstance(raw, str) or not raw.strip() or len(raw.encode("utf-8")) > 4096:
        raise ControllerError("Tier-2 termination message is missing or oversized")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ControllerError("Tier-2 termination message is invalid JSON") from exc
    required = {
        "schema",
        "action",
        "request_id",
        "old_pod_uid",
        "generation",
        "reason",
        "requested_at",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ControllerError("Tier-2 termination receipt fields are invalid")
    if value["schema"] != TIER2_SCHEMA or value["action"] != TIER2_ACTION:
        raise ControllerError("Tier-2 termination receipt protocol is invalid")
    if value["old_pod_uid"] != pod_uid:
        raise ControllerError("Tier-2 receipt Pod UID does not match the live Pod")
    try:
        uuid.UUID(str(value["request_id"]))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ControllerError("Tier-2 request id is invalid") from exc
    generation = value["generation"]
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise ControllerError("Tier-2 generation is invalid")
    if not isinstance(value["reason"], str) or _REASON.fullmatch(value["reason"]) is None:
        raise ControllerError("Tier-2 reason is invalid")
    requested_at = value["requested_at"]
    if isinstance(requested_at, bool) or not isinstance(requested_at, (int, float)) or requested_at <= 0:
        raise ControllerError("Tier-2 timestamp is invalid")
    return value


def replacement_request(
    pod: dict,
    *,
    namespace: str,
    pod_name: str,
    expected_image_digest: str,
    runtime_class: str,
) -> dict[str, object] | None:
    """Return an exact UID-fenced replacement request or None when no trigger exists."""
    if _DIGEST.fullmatch(expected_image_digest) is None:
        raise ControllerError("expected image digest must be sha256:<64 lowercase hex>")
    metadata = pod.get("metadata")
    spec = pod.get("spec")
    status = pod.get("status")
    if not all(isinstance(item, dict) for item in (metadata, spec, status)):
        raise ControllerError("Pod object is missing metadata/spec/status")

    actual_namespace = _required_text(metadata.get("namespace"), "pod namespace")
    actual_name = _required_text(metadata.get("name"), "pod name")
    pod_uid = _required_text(metadata.get("uid"), "pod UID", max_len=160)
    if actual_namespace != namespace or actual_name != pod_name:
        raise ControllerError("Pod identity does not match configured Tier-2 target")
    labels = metadata.get("labels") or {}
    if not isinstance(labels, dict) or labels.get("app") != "clayverse":
        raise ControllerError("Tier-2 target is not the canonical ClayVerse Pod")

    controllers = [
        ref for ref in metadata.get("ownerReferences", [])
        if isinstance(ref, dict) and ref.get("controller") is True
    ]
    if len(controllers) != 1 or controllers[0].get("kind") != "StatefulSet" or controllers[0].get("name") != "clayverse":
        raise ControllerError("Tier-2 target must be controlled by StatefulSet/clayverse")
    if spec.get("runtimeClassName") != runtime_class:
        raise ControllerError("Tier-2 target runtimeClass drifted")
    if spec.get("automountServiceAccountToken") is not False:
        raise ControllerError("ClayVerse Pod unexpectedly has ServiceAccount token automount")

    container = _container(spec, "clayverse")
    image = _required_text(container.get("image"), "ClayVerse image")
    if not image.endswith("@" + expected_image_digest):
        raise ControllerError("ClayVerse Pod spec is not bound to the accepted image digest")
    cstatus = _container_status(status, "clayverse")
    image_id = _required_text(cstatus.get("imageID"), "ClayVerse runtime imageID")
    if not (image_id == expected_image_digest or image_id.endswith("@" + expected_image_digest)):
        raise ControllerError("ClayVerse runtime imageID does not match the accepted digest")

    terminated = _termination(cstatus)
    if terminated is None:
        return None
    receipt = _decode_receipt(terminated.get("message"), pod_uid=pod_uid)
    return {
        "pod_uid": pod_uid,
        "request_id": receipt["request_id"],
        "generation": receipt["generation"],
        "reason": receipt["reason"],
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
        self.base_url = _required_text(base_url, "Kubernetes API URL").rstrip("/")
        parsed = urllib.parse.urlsplit(self.base_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ControllerError("Kubernetes API URL must be credential-free HTTPS")
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

    def get_pod(self, namespace: str, pod_name: str) -> dict:
        ns = urllib.parse.quote(namespace, safe="")
        name = urllib.parse.quote(pod_name, safe="")
        return self._request("GET", f"/api/v1/namespaces/{ns}/pods/{name}")

    def delete_pod(self, namespace: str, pod_name: str, options: dict) -> dict:
        ns = urllib.parse.quote(namespace, safe="")
        name = urllib.parse.quote(pod_name, safe="")
        return self._request("DELETE", f"/api/v1/namespaces/{ns}/pods/{name}", options)


def run_once(api: KubernetesAPI, *, namespace: str, pod_name: str, digest: str, runtime_class: str) -> bool:
    pod = api.get_pod(namespace, pod_name)
    request = replacement_request(
        pod,
        namespace=namespace,
        pod_name=pod_name,
        expected_image_digest=digest,
        runtime_class=runtime_class,
    )
    if request is None:
        return False
    api.delete_pod(namespace, pod_name, request["delete_options"])
    print(json.dumps({
        "status": "tier2_pod_delete_requested",
        "pod_uid": request["pod_uid"],
        "request_id": request["request_id"],
        "generation": request["generation"],
        "reason": request["reason"],
    }, sort_keys=True), flush=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="ClayVerse external Kubernetes Tier-2 full-sandbox replacer")
    parser.add_argument("--once", action="store_true", help="perform one exact-pod check and exit")
    args = parser.parse_args()

    namespace = os.environ.get("CLAYVERSE_TIER2_NAMESPACE", "clayverse")
    pod_name = os.environ.get("CLAYVERSE_TIER2_POD_NAME", "clayverse-0")
    digest = os.environ.get("CLAYVERSE_TIER2_EXPECTED_IMAGE_DIGEST", "")
    runtime_class = os.environ.get("CLAYVERSE_TIER2_RUNTIME_CLASS", "kata-qemu-runtime-rs")
    api_url = os.environ.get("CLAYVERSE_TIER2_KUBE_API_URL", "")
    token_file = os.environ.get("CLAYVERSE_TIER2_KUBE_TOKEN_FILE", "")
    ca_file = os.environ.get("CLAYVERSE_TIER2_KUBE_CA_FILE", "")
    poll_seconds = float(os.environ.get("CLAYVERSE_TIER2_POLL_SECONDS", "2"))
    if not 0.5 <= poll_seconds <= 60:
        raise ControllerError("Tier-2 poll interval must be between 0.5 and 60 seconds")

    api = KubernetesAPI(api_url, token_file, ca_file)
    while True:
        run_once(api, namespace=namespace, pod_name=pod_name, digest=digest, runtime_class=runtime_class)
        if args.once:
            return 0
        time.sleep(poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
