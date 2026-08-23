#!/usr/bin/env python3
"""Fail-closed binding for the bundled ~0.8B J-Space/GWT cognition manifest.

This module is intentionally dependency-free. It validates a structurally complete,
exactly identified candidate separately from boot admission; SOURCE_ONLY candidates
must never receive boot/runtime credit until all required identities/calibrations are
measured and the manifest is explicitly promoted to MEASURED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "BundledCognitionManifest/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDERS = {"", "unknown", "unmeasured", "tbd", "todo", "unset", "none", "null"}

TOP_KEYS = {
    "schema_version",
    "status",
    "engine_id",
    "model_family",
    "checkpoint_digest",
    "tokenizer_digest",
    "runtime_binding",
    "jspace_profile_digest",
    "lens_profile_digest",
    "lens_semantics",
    "workspace_calibration_digest",
    "steering_calibration_digest",
    "claycode_contract_version",
    "grf_contract_version",
    "hyperposition_contract_version",
    "compatible_entityos_range",
    "provenance",
}

REQUIRED_TOP_KEYS = TOP_KEYS - {"steering_calibration_digest"}
RUNTIME_KEYS = {"runtime_id", "quantization", "artifact_digest"}
LENS_KEYS = {"d_model", "source_layers", "n_prompts"}
PROVENANCE_KEYS = {"source_commit", "source_tree", "lens_source", "calibration_receipt"}


class ManifestError(ValueError):
    pass


def _require_exact_keys(obj: dict[str, Any], required: set[str], allowed: set[str], where: str) -> None:
    missing = sorted(required - set(obj))
    extra = sorted(set(obj) - allowed)
    if missing or extra:
        raise ManifestError(f"{where}:KEYSET_MISMATCH:missing={missing}:extra={extra}")


def _require_text(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise ManifestError(f"{where}:STRING_REQUIRED")
    if value.strip().lower() in PLACEHOLDERS:
        raise ManifestError(f"{where}:PLACEHOLDER_FORBIDDEN")
    return value


def _require_sha256(value: Any, where: str) -> str:
    value = _require_text(value, where)
    if not SHA256_RE.fullmatch(value):
        raise ManifestError(f"{where}:SHA256_REQUIRED")
    return value


def _require_git_sha(value: Any, where: str) -> str:
    value = _require_text(value, where)
    if not GIT_SHA_RE.fullmatch(value):
        raise ManifestError(f"{where}:GIT_SHA40_REQUIRED")
    return value


def _require_pos_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ManifestError(f"{where}:POSITIVE_INT_REQUIRED")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"NONCANONICAL_JSON:{exc}") from exc
    return text.encode("utf-8")


def bundle_identity(manifest: dict[str, Any]) -> str:
    """Digest the whole admitted manifest, excluding no semantic field."""
    return hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()


def validate_structure(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ManifestError("MANIFEST_OBJECT_REQUIRED")
    _require_exact_keys(manifest, REQUIRED_TOP_KEYS, TOP_KEYS, "manifest")

    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestError("schema_version:UNSUPPORTED")
    if manifest["status"] not in {"SOURCE_ONLY", "MEASURED"}:
        raise ManifestError("status:SOURCE_ONLY_OR_MEASURED_REQUIRED")

    _require_text(manifest["engine_id"], "engine_id")
    _require_text(manifest["model_family"], "model_family")
    _require_sha256(manifest["checkpoint_digest"], "checkpoint_digest")
    _require_sha256(manifest["tokenizer_digest"], "tokenizer_digest")
    _require_sha256(manifest["jspace_profile_digest"], "jspace_profile_digest")
    _require_sha256(manifest["lens_profile_digest"], "lens_profile_digest")
    _require_sha256(manifest["workspace_calibration_digest"], "workspace_calibration_digest")
    if "steering_calibration_digest" in manifest and manifest["steering_calibration_digest"] is not None:
        _require_sha256(manifest["steering_calibration_digest"], "steering_calibration_digest")

    for key in ("claycode_contract_version", "grf_contract_version", "hyperposition_contract_version", "compatible_entityos_range"):
        _require_text(manifest[key], key)

    runtime = manifest["runtime_binding"]
    if not isinstance(runtime, dict):
        raise ManifestError("runtime_binding:OBJECT_REQUIRED")
    _require_exact_keys(runtime, RUNTIME_KEYS, RUNTIME_KEYS, "runtime_binding")
    _require_text(runtime["runtime_id"], "runtime_binding.runtime_id")
    _require_text(runtime["quantization"], "runtime_binding.quantization")
    _require_sha256(runtime["artifact_digest"], "runtime_binding.artifact_digest")

    lens = manifest["lens_semantics"]
    if not isinstance(lens, dict):
        raise ManifestError("lens_semantics:OBJECT_REQUIRED")
    _require_exact_keys(lens, LENS_KEYS, LENS_KEYS, "lens_semantics")
    _require_pos_int(lens["d_model"], "lens_semantics.d_model")
    _require_pos_int(lens["n_prompts"], "lens_semantics.n_prompts")
    layers = lens["source_layers"]
    if not isinstance(layers, list) or not layers:
        raise ManifestError("lens_semantics.source_layers:NONEMPTY_LIST_REQUIRED")
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in layers):
        raise ManifestError("lens_semantics.source_layers:NONNEGATIVE_INT_REQUIRED")
    if layers != sorted(set(layers)):
        raise ManifestError("lens_semantics.source_layers:SORTED_UNIQUE_REQUIRED")

    provenance = manifest["provenance"]
    if not isinstance(provenance, dict):
        raise ManifestError("provenance:OBJECT_REQUIRED")
    _require_exact_keys(provenance, PROVENANCE_KEYS, PROVENANCE_KEYS, "provenance")
    _require_git_sha(provenance["source_commit"], "provenance.source_commit")
    _require_git_sha(provenance["source_tree"], "provenance.source_tree")
    _require_text(provenance["lens_source"], "provenance.lens_source")
    _require_text(provenance["calibration_receipt"], "provenance.calibration_receipt")

    canonical_json_bytes(manifest)
    return manifest


def admit_boot(manifest: Any, *, expected_identity: str | None = None) -> str:
    manifest = validate_structure(manifest)
    if manifest["status"] != "MEASURED":
        raise ManifestError("BOOT_ADMISSION_REQUIRES_MEASURED_STATUS")
    ident = bundle_identity(manifest)
    if expected_identity is not None:
        _require_sha256(expected_identity, "expected_identity")
        if ident != expected_identity:
            raise ManifestError("STALE_OR_SUBSTITUTED_BUNDLE_IDENTITY")
    return ident


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--boot", action="store_true")
    parser.add_argument("--expected-identity")
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        ident = admit_boot(data, expected_identity=args.expected_identity) if args.boot else bundle_identity(validate_structure(data))
    except (OSError, json.JSONDecodeError, ManifestError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps({"ok": True, "schema_version": SCHEMA_VERSION, "bundle_identity": ident, "boot_admitted": bool(args.boot)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
