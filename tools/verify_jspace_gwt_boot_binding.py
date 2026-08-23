#!/usr/bin/env python3
"""Fail-closed verifier for JSPACE_GWT_BOOT_BINDING_RECEIPT/v1.

This instrument establishes only exact boot-binding/source-mechanism evidence.
It does not grant model-quality, semantic-truth, Whole-GWT, BASE, provider,
or Frank/AgentZero acceptance credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

RECEIPT_VERSION = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
REQUIRED_ARTIFACT_ROLES = {
    "bundled_core_manifest",
    "checkpoint",
    "tokenizer",
    "local_runtime",
    "jacobian_lens",
    "workspace_policy",
    "zero_identity",
    "grf_projection",
    "claude_adapter",
    "claude_capability_profile",
}
ENGINE_CLASSES = {"LOCAL_HOOKABLE", "CLAUDE_CODE", "DETERMINISTIC_TOOL", "NO_MODEL_REQUIRED"}
ORIGIN_CLASSES = ENGINE_CLASSES | {"HOOK", "TIMER", "PROXY_CONTROLLER", "SANDBOX_CONTROLLER", "OTHER"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fail(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def verify_receipt(receipt: dict[str, Any], root: Path, *, verify_files: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    root = root.resolve()

    if receipt.get("receipt_version") != RECEIPT_VERSION:
        _fail(errors, "BAD_RECEIPT_VERSION")
    if not isinstance(receipt.get("macrocycle_id"), str) or not receipt["macrocycle_id"].strip():
        _fail(errors, "MACROCYCLE_ID_REQUIRED")

    source = receipt.get("source", {})
    if not GIT_OID_RE.fullmatch(str(source.get("commit_sha", ""))):
        _fail(errors, "SOURCE_COMMIT_GIT_OID_REQUIRED")
    if not GIT_OID_RE.fullmatch(str(source.get("tree_sha", ""))):
        _fail(errors, "SOURCE_TREE_GIT_OID_REQUIRED")
    if source.get("dirty_state") not in {"CLEAN", "DIRTY"}:
        _fail(errors, "SOURCE_DIRTY_STATE_INVALID")

    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list):
        artifacts = []
        _fail(errors, "ARTIFACTS_LIST_REQUIRED")

    by_role: dict[str, dict[str, Any]] = {}
    for i, item in enumerate(artifacts):
        if not isinstance(item, dict):
            _fail(errors, f"ARTIFACT_{i}_NOT_OBJECT")
            continue
        role = item.get("role")
        if role in by_role:
            _fail(errors, f"DUPLICATE_ARTIFACT_ROLE:{role}")
            continue
        by_role[role] = item
        sha = str(item.get("sha256", ""))
        if not SHA256_RE.fullmatch(sha):
            _fail(errors, f"BAD_SHA256:{role}")
        if not isinstance(item.get("size_bytes"), int) or item["size_bytes"] < 0:
            _fail(errors, f"BAD_SIZE:{role}")
        rel = item.get("path")
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
            _fail(errors, f"BAD_PATH:{role}")
            continue
        if verify_files:
            try:
                resolved = (root / rel).resolve(strict=True)
                resolved.relative_to(root)
            except (FileNotFoundError, ValueError, OSError):
                _fail(errors, f"PATH_NOT_BOUND_INSIDE_ROOT:{role}")
                continue
            if not resolved.is_file():
                _fail(errors, f"NOT_FILE:{role}")
                continue
            if resolved.stat().st_size != item.get("size_bytes"):
                _fail(errors, f"SIZE_MISMATCH:{role}")
            if _sha256_file(resolved) != sha:
                _fail(errors, f"DIGEST_MISMATCH:{role}")

    for role in sorted(REQUIRED_ARTIFACT_ROLES - set(by_role)):
        _fail(errors, f"MISSING_ARTIFACT:{role}")

    core = receipt.get("core", {})
    lens = receipt.get("jspace_lens", {})
    try:
        layer_count = int(core.get("layer_count"))
        d_model = int(core.get("d_model"))
    except (TypeError, ValueError):
        layer_count = d_model = -1
        _fail(errors, "CORE_DIMENSIONS_INVALID")
    if layer_count <= 0 or d_model <= 0:
        _fail(errors, "CORE_DIMENSIONS_INVALID")

    if str(core.get("checkpoint_sha256", "")) != str(by_role.get("checkpoint", {}).get("sha256", "")):
        _fail(errors, "CORE_CHECKPOINT_ARTIFACT_MISMATCH")
    if str(core.get("tokenizer_sha256", "")) != str(by_role.get("tokenizer", {}).get("sha256", "")):
        _fail(errors, "CORE_TOKENIZER_ARTIFACT_MISMATCH")

    if str(lens.get("artifact_sha256", "")) != str(by_role.get("jacobian_lens", {}).get("sha256", "")):
        _fail(errors, "LENS_ARTIFACT_MISMATCH")
    if str(lens.get("source_checkpoint_sha256", "")) != str(core.get("checkpoint_sha256", "")):
        _fail(errors, "LENS_SOURCE_CHECKPOINT_MISMATCH")
    if str(lens.get("source_tokenizer_sha256", "")) != str(core.get("tokenizer_sha256", "")):
        _fail(errors, "LENS_SOURCE_TOKENIZER_MISMATCH")
    if lens.get("d_model") != core.get("d_model"):
        _fail(errors, "LENS_D_MODEL_MISMATCH")

    layers = lens.get("source_layers")
    if not isinstance(layers, list) or not layers:
        _fail(errors, "LENS_SOURCE_LAYERS_REQUIRED")
    else:
        if any(not isinstance(x, int) for x in layers):
            _fail(errors, "LENS_SOURCE_LAYERS_NONINTEGER")
        else:
            if layers != sorted(set(layers)):
                _fail(errors, "LENS_SOURCE_LAYERS_NOT_STRICT_SET")
            if layer_count > 0 and any(x < 0 or x >= layer_count for x in layers):
                _fail(errors, "LENS_SOURCE_LAYER_OUT_OF_RANGE")
    if not isinstance(lens.get("n_prompts"), int) or lens["n_prompts"] <= 0:
        _fail(errors, "LENS_N_PROMPTS_INVALID")

    workspace = receipt.get("workspace", {})
    if workspace.get("fabric_mode") != "UNIFIED_JSPACE_GWT":
        _fail(errors, "WORKSPACE_FABRIC_MODE_INVALID")
    for field, role in (
        ("workspace_policy_sha256", "workspace_policy"),
        ("zero_identity_sha256", "zero_identity"),
        ("grf_projection_sha256", "grf_projection"),
    ):
        if str(workspace.get(field, "")) != str(by_role.get(role, {}).get("sha256", "")):
            _fail(errors, f"WORKSPACE_BINDING_MISMATCH:{field}")

    claude = receipt.get("claude_adapter", {})
    if str(claude.get("adapter_sha256", "")) != str(by_role.get("claude_adapter", {}).get("sha256", "")):
        _fail(errors, "CLAUDE_ADAPTER_ARTIFACT_MISMATCH")
    if str(claude.get("capability_profile_sha256", "")) != str(by_role.get("claude_capability_profile", {}).get("sha256", "")):
        _fail(errors, "CLAUDE_CAPABILITY_PROFILE_ARTIFACT_MISMATCH")
    for flag in ("tool_less_expected", "ephemeral_expected", "structured_output_expected", "env_isolated_expected"):
        if claude.get(flag) is not True:
            _fail(errors, f"CLAUDE_BOUNDARY_FLAG_REQUIRED:{flag}")

    first = receipt.get("first_action", {})
    if first.get("engine_class") not in ENGINE_CLASSES:
        _fail(errors, "FIRST_ENGINE_CLASS_INVALID")
    if first.get("origin") not in ORIGIN_CLASSES:
        _fail(errors, "FIRST_ACTION_ORIGIN_INVALID")
    if not SHA256_RE.fullmatch(str(first.get("inference_packet_sha256", ""))):
        _fail(errors, "FIRST_PACKET_SHA256_REQUIRED")

    control = receipt.get("control", {})
    if control.get("free_only") is not True:
        _fail(errors, "FREE_ONLY_NOT_BOUND")
    if control.get("paid_or_unknown_provider_network_attempted") is not False:
        _fail(errors, "PAID_OR_UNKNOWN_NETWORK_ATTEMPT_NOT_ZERO")

    unusual = receipt.get("unusual_experiment", {})
    if unusual.get("count_for_this_macrocycle") not in {0, 1}:
        _fail(errors, "UNUSUAL_EXPERIMENT_COUNT_INVALID")

    return {
        "receipt_version": RECEIPT_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "credit": "BOOT_BINDING_ONLY" if not errors else "NONE",
        "whole_runtime_credit": 0,
        "semantic_truth_credit": 0,
        "model_quality_credit": 0,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("receipt", type=Path)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--no-file-check", action="store_true", help="Schema/cross-binding review only; never runtime evidence.")
    args = p.parse_args(argv)
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "errors": [f"RECEIPT_READ_ERROR:{type(exc).__name__}"]}, sort_keys=True))
        return 2
    result = verify_receipt(receipt, args.root, verify_files=not args.no_file_check)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
