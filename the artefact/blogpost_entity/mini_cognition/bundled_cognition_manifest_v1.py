#!/usr/bin/env python3
"""Fail-closed validator for the Mini Entity bundled cognition integration manifest.

This validator binds model bytes and J-Space/GWT calibration bytes into one stable
integration identity. It intentionally does not claim that any referenced artifact exists
or has been runtime-verified; runtime admission must separately hash the actual bytes.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "mini-entity-bundled-cognition-manifest/v1"
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_FIELDS = {
    "schema",
    "engine_id",
    "model_family",
    "checkpoint_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "lens_profile_digest",
    "workspace_calibration_digest",
    "claycode_contract_version",
    "grf_contract_version",
    "hyperposition_contract_version",
    "compatible_entityos_range",
    "provenance",
}
OPTIONAL_FIELDS = {
    "quantization_runtime_identity",
    "steering_calibration_digest",
}
DIGEST_FIELDS = {
    "checkpoint_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "lens_profile_digest",
    "workspace_calibration_digest",
    "steering_calibration_digest",
}
IDENTITY_FIELDS = (
    "schema",
    "engine_id",
    "model_family",
    "checkpoint_digest",
    "tokenizer_digest",
    "quantization_runtime_identity",
    "jspace_profile_digest",
    "lens_profile_digest",
    "workspace_calibration_digest",
    "steering_calibration_digest",
    "claycode_contract_version",
    "grf_contract_version",
    "hyperposition_contract_version",
    "compatible_entityos_range",
)


class ManifestError(ValueError):
    """Typed fail-closed manifest error."""


@dataclass(frozen=True)
class ValidatedManifest:
    manifest: dict[str, Any]
    integration_identity_sha256: str
    manifest_identity_sha256: str


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value


def _sha256(value: Any, field: str) -> str:
    text = _nonempty_string(value, field)
    if not DIGEST_RE.fullmatch(text):
        raise ManifestError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if text in {"0" * 64, "f" * 64}:
        raise ManifestError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return text


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"MANIFEST_NOT_CANONICAL_JSON:{exc.__class__.__name__}") from exc


def _canonical_identity_payload(manifest: Mapping[str, Any]) -> bytes:
    payload = {name: manifest.get(name) for name in IDENTITY_FIELDS}
    return _canonical_json_bytes(payload)


def validate_manifest(data: Any) -> ValidatedManifest:
    if not isinstance(data, dict):
        raise ManifestError("MANIFEST_OBJECT_REQUIRED")

    keys = set(data)
    missing = sorted(REQUIRED_FIELDS - keys)
    if missing:
        raise ManifestError("MISSING_REQUIRED_FIELDS:" + ",".join(missing))
    unknown = sorted(keys - REQUIRED_FIELDS - OPTIONAL_FIELDS)
    if unknown:
        raise ManifestError("UNKNOWN_FIELDS:" + ",".join(unknown))

    manifest = dict(data)
    if manifest["schema"] != SCHEMA:
        raise ManifestError("SCHEMA_UNSUPPORTED")

    for field in (
        "engine_id",
        "model_family",
        "claycode_contract_version",
        "grf_contract_version",
        "hyperposition_contract_version",
        "compatible_entityos_range",
    ):
        _nonempty_string(manifest[field], field)

    for field in DIGEST_FIELDS:
        if field in manifest:
            _sha256(manifest[field], field)

    if "quantization_runtime_identity" in manifest:
        _nonempty_string(manifest["quantization_runtime_identity"], "quantization_runtime_identity")

    provenance = manifest["provenance"]
    if not isinstance(provenance, dict) or not provenance:
        raise ManifestError("provenance:NONEMPTY_OBJECT_REQUIRED")
    for key, value in provenance.items():
        if not isinstance(key, str) or not key.strip():
            raise ManifestError("provenance:NONEMPTY_STRING_KEYS_REQUIRED")
        if isinstance(value, float) and not (value == value and abs(value) != float("inf")):
            raise ManifestError("provenance:NONFINITE_VALUE_FORBIDDEN")

    integration_identity = hashlib.sha256(_canonical_identity_payload(manifest)).hexdigest()
    manifest_identity = hashlib.sha256(_canonical_json_bytes(manifest)).hexdigest()
    return ValidatedManifest(
        manifest=manifest,
        integration_identity_sha256=integration_identity,
        manifest_identity_sha256=manifest_identity,
    )


def load_and_validate(path: Path) -> ValidatedManifest:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"MANIFEST_READ_OR_JSON_ERROR:{exc.__class__.__name__}") from exc
    return validate_manifest(data)
