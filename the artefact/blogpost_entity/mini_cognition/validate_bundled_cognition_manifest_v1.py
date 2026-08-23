#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

SCHEMA = "bundled-cognition-manifest/v1"
FINGERPRINT_SCHEMA = "bundled-cognition-integration/v1"

DIGEST_FIELDS = (
    "checkpoint_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "lens_profile_digest",
    "workspace_calibration_digest",
)

REQUIRED_STRING_FIELDS = (
    "engine_id",
    "model_family",
    "claycode_contract_version",
    "grf_contract_version",
    "hyperposition_contract_version",
    "compatible_entityos_range",
    "provenance",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(ValueError):
    pass


def _require_nonempty_string(data: Mapping[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field}:REQUIRED_NONEMPTY_STRING")
    return value.strip()


def _require_sha256(data: Mapping[str, Any], field: str) -> str:
    value = _require_nonempty_string(data, field)
    if not _SHA256_RE.fullmatch(value):
        raise ManifestError(f"{field}:REQUIRED_LOWER_HEX_SHA256")
    if value == "0" * 64:
        raise ManifestError(f"{field}:PLACEHOLDER_DIGEST_FORBIDDEN")
    return value


def integration_identity_payload(manifest: Mapping[str, Any]) -> dict[str, str]:
    if manifest.get("schema") != SCHEMA:
        raise ManifestError(f"schema:EXPECTED:{SCHEMA}")

    payload: dict[str, str] = {
        "fingerprint_schema": FINGERPRINT_SCHEMA,
    }
    for field in REQUIRED_STRING_FIELDS:
        payload[field] = _require_nonempty_string(manifest, field)
    for field in DIGEST_FIELDS:
        payload[field] = _require_sha256(manifest, field)

    optional_digest = manifest.get("steering_calibration_digest")
    if optional_digest is not None:
        if not isinstance(optional_digest, str) or not _SHA256_RE.fullmatch(optional_digest):
            raise ManifestError("steering_calibration_digest:REQUIRED_LOWER_HEX_SHA256")
        if optional_digest == "0" * 64:
            raise ManifestError("steering_calibration_digest:PLACEHOLDER_DIGEST_FORBIDDEN")
        payload["steering_calibration_digest"] = optional_digest

    runtime_identity = manifest.get("quantization_runtime_identity")
    if runtime_identity is not None:
        if not isinstance(runtime_identity, str) or not runtime_identity.strip():
            raise ManifestError("quantization_runtime_identity:REQUIRED_NONEMPTY_STRING")
        payload["quantization_runtime_identity"] = runtime_identity.strip()

    return payload


def compute_integration_fingerprint(manifest: Mapping[str, Any]) -> str:
    payload = integration_identity_payload(manifest)
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_manifest(manifest: Mapping[str, Any]) -> str:
    computed = compute_integration_fingerprint(manifest)
    supplied = manifest.get("integration_fingerprint")
    if supplied is None:
        raise ManifestError("integration_fingerprint:REQUIRED")
    if not isinstance(supplied, str) or not _SHA256_RE.fullmatch(supplied):
        raise ManifestError("integration_fingerprint:REQUIRED_LOWER_HEX_SHA256")
    if supplied != computed:
        raise ManifestError("integration_fingerprint:MISMATCH")
    return computed


def validate_boot_binding(manifest: Mapping[str, Any], receipt: Mapping[str, Any]) -> str:
    fingerprint = validate_manifest(manifest)

    if receipt.get("schema") != "jspace-gwt-boot-binding-receipt/v1":
        raise ManifestError("receipt.schema:EXPECTED:jspace-gwt-boot-binding-receipt/v1")

    supplied_fp = receipt.get("bundled_cognition_integration_fingerprint")
    if supplied_fp != fingerprint:
        raise ManifestError("receipt.bundled_cognition_integration_fingerprint:MISMATCH")

    for field in DIGEST_FIELDS:
        if receipt.get(field) != manifest.get(field):
            raise ManifestError(f"receipt.{field}:MISMATCH")

    if receipt.get("engine_id") != manifest.get("engine_id"):
        raise ManifestError("receipt.engine_id:MISMATCH")

    return fingerprint
