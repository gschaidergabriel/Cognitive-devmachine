#!/usr/bin/env python3
"""Cross-bind the canonical bundled-cognition manifest to a J-Space/GWT boot receipt.

This module is deliberately *not* a replacement for either canonical standalone
validator. It checks only that two independently validated records describe the
same exact bundle/calibration identities. A cross-binding PASS grants no runtime,
model-quality, semantic, or Whole-GWT credit.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
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
    if not isinstance(value, dict):
        fail(f"CROSS_BINDING_OBJECT_REQUIRED:{key}")
    return value


def text(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
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
) -> None:
    if not isinstance(manifest, dict):
        fail("MANIFEST_OBJECT_REQUIRED")
    if not isinstance(receipt, dict):
        fail("RECEIPT_OBJECT_REQUIRED")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        fail("MANIFEST_SCHEMA_MISMATCH")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        fail("RECEIPT_SCHEMA_MISMATCH")
    if HEX64.fullmatch(manifest_raw_sha256) is None:
        fail("MANIFEST_RAW_SHA256_INVALID")

    core = obj(receipt, "bundled_core")
    jspace = obj(receipt, "jspace")
    gwt = obj(receipt, "gwt")

    # Bind the receipt to the exact manifest file bytes, not only its semantic fields.
    eq("manifest_raw_sha256", sha(core, "manifest_sha256"), manifest_raw_sha256)

    # Then bind the independently surfaced runtime identities back to the manifest.
    # This prevents a re-hashed/substituted manifest from shadowing stale receipt fields.
    eq("engine_id", text(core, "engine_id"), text(manifest, "engine_id"))
    eq("model_family", text(core, "model_family"), text(manifest, "model_family"))
    eq("checkpoint_digest", sha(core, "checkpoint_sha256"), sha(manifest, "checkpoint_digest"))
    eq("tokenizer_digest", sha(core, "tokenizer_sha256"), sha(manifest, "tokenizer_digest"))
    eq(
        "jspace_profile_digest",
        sha(jspace, "jspace_profile_sha256"),
        sha(manifest, "jspace_profile_digest"),
    )
    eq(
        "lens_profile_digest",
        sha(jspace, "lens_profile_sha256"),
        sha(manifest, "lens_profile_digest"),
    )
    eq(
        "workspace_calibration_digest",
        sha(gwt, "calibration_sha256"),
        sha(manifest, "workspace_calibration_digest"),
    )

    steering = manifest.get("steering_calibration_digest")
    if steering is not None:
        if not isinstance(steering, str) or HEX64.fullmatch(steering) is None:
            fail("CROSS_BINDING_SHA256_REQUIRED:steering_calibration_digest")
        eq(
            "steering_calibration_digest",
            sha(jspace, "steering_calibration_sha256"),
            steering,
        )


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"READ_OR_JSON_ERROR:{path.name}:{exc.__class__.__name__}")
    if not isinstance(data, dict):
        fail(f"TOP_LEVEL_OBJECT_REQUIRED:{path.name}")
    return data, raw


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: validate_jspace_gwt_manifest_cross_binding_v1.py MANIFEST.json RECEIPT.json",
            file=sys.stderr,
        )
        return 2
    try:
        manifest, manifest_raw = load_json(Path(sys.argv[1]))
        receipt, _ = load_json(Path(sys.argv[2]))
        cross_validate(
            manifest,
            receipt,
            manifest_raw_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        )
    except CrossBindingError as exc:
        print(f"FAIL {exc}")
        return 1
    print("PASS JSPACE_GWT_MANIFEST_CROSS_BINDING/v1")
    print("EVIDENCE_CREDIT ZERO_RUNTIME_ZERO_MODEL_ZERO_WHOLE_GWT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
