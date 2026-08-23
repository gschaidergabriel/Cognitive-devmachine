#!/usr/bin/env python3
"""Cross-bind source-locked bundled cognition manifest to a J-Space/GWT boot receipt.

Additive validation layer only: canonical manifest and boot-receipt validators remain
independent authorities for their own schemas. This gate proves only identity coherence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA = "mini-entity-bundled-cognition-manifest/v1"
RECEIPT_SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CrossBindingError(ValueError):
    pass


def fail(code: str) -> None:
    raise CrossBindingError(code)


def obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if type(value) is not dict:
        fail(f"CROSS_BINDING_OBJECT_REQUIRED:{key}")
    return value


def text(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if type(value) is not str or not value.strip():
        fail(f"CROSS_BINDING_TEXT_REQUIRED:{key}")
    return value


def sha(parent: dict[str, Any], key: str) -> str:
    value = text(parent, key)
    if HEX64.fullmatch(value) is None:
        fail(f"CROSS_BINDING_SHA256_REQUIRED:{key}")
    return value


def eq(label: str, left: str, right: str) -> None:
    if left != right:
        fail(f"CROSS_BINDING_MISMATCH:{label}")


def cross_validate(
    manifest: Any,
    receipt: Any,
    *,
    manifest_raw_sha256: str,
    expected_manifest_raw_sha256: str,
) -> None:
    if type(manifest) is not dict:
        fail("MANIFEST_OBJECT_REQUIRED")
    if type(receipt) is not dict:
        fail("RECEIPT_OBJECT_REQUIRED")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        fail("MANIFEST_SCHEMA_MISMATCH")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        fail("RECEIPT_SCHEMA_MISMATCH")
    if HEX64.fullmatch(manifest_raw_sha256) is None:
        fail("MANIFEST_RAW_SHA256_INVALID")
    if HEX64.fullmatch(expected_manifest_raw_sha256) is None:
        fail("EXPECTED_MANIFEST_RAW_SHA256_INVALID")

    # External source/startup lock defeats a self-consistent manifest+receipt substitution.
    eq("source_locked_manifest_raw_sha256", manifest_raw_sha256, expected_manifest_raw_sha256)

    core = obj(receipt, "bundled_core")
    jspace = obj(receipt, "jspace")
    gwt = obj(receipt, "gwt")

    # Receipt must name the exact same manifest bytes observed by this gate.
    eq("manifest_raw_sha256", sha(core, "manifest_sha256"), manifest_raw_sha256)

    # Identity-bearing components must agree after independent schema validation.
    eq("engine_id", text(core, "engine_id"), text(manifest, "engine_id"))
    eq("model_family", text(core, "model_family"), text(manifest, "model_family"))
    eq("checkpoint_digest", sha(core, "checkpoint_sha256"), sha(manifest, "checkpoint_digest"))
    eq("tokenizer_digest", sha(core, "tokenizer_sha256"), sha(manifest, "tokenizer_digest"))

    runtime_digest = manifest.get("runtime_digest")
    if runtime_digest is None:
        fail("CROSS_BINDING_RUNTIME_DIGEST_REQUIRED")
    eq("runtime_digest", sha(core, "runtime_sha256"), sha(manifest, "runtime_digest"))

    runtime_identity = manifest.get("quantization_runtime_identity")
    if runtime_identity is None:
        fail("CROSS_BINDING_RUNTIME_IDENTITY_REQUIRED")
    eq("quantization_runtime_identity", text(core, "runtime_identity"), text(manifest, "quantization_runtime_identity"))

    eq("jspace_profile_digest", sha(jspace, "jspace_profile_sha256"), sha(manifest, "jspace_profile_digest"))
    eq("lens_profile_digest", sha(jspace, "lens_profile_sha256"), sha(manifest, "lens_profile_digest"))
    eq("workspace_calibration_digest", sha(gwt, "calibration_sha256"), sha(manifest, "workspace_calibration_digest"))

    steering = manifest.get("steering_calibration_digest")
    if steering is not None:
        if type(steering) is not str or HEX64.fullmatch(steering) is None:
            fail("CROSS_BINDING_SHA256_REQUIRED:steering_calibration_digest")
        eq("steering_calibration_digest", sha(jspace, "steering_calibration_sha256"), steering)
    elif jspace.get("steering_calibration_sha256") is not None:
        fail("CROSS_BINDING_UNEXPECTED_STEERING_CALIBRATION")


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"READ_OR_JSON_ERROR:{path.name}:{exc.__class__.__name__}")
    if type(data) is not dict:
        fail(f"TOP_LEVEL_OBJECT_REQUIRED:{path.name}")
    return data, raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expected-manifest-raw-sha256", required=True)
    args = parser.parse_args()
    try:
        manifest, manifest_raw = load_json(args.manifest)
        receipt, _ = load_json(args.receipt)
        cross_validate(
            manifest,
            receipt,
            manifest_raw_sha256=hashlib.sha256(manifest_raw).hexdigest(),
            expected_manifest_raw_sha256=args.expected_manifest_raw_sha256,
        )
    except CrossBindingError as exc:
        print(f"FAIL {exc}")
        return 1
    print("PASS JSPACE_GWT_MANIFEST_CROSS_BINDING/v1 SOURCE_LOCKED_RUNTIME_BOUND")
    print("EVIDENCE_CREDIT ZERO_RUNTIME_ZERO_MODEL_ZERO_WHOLE_GWT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
