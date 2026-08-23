#!/usr/bin/env python3
"""Fail-closed validator for JSPACE_GWT_BOOT_BINDING_RECEIPT/v1.

This is an identity/binding gate only. Passing it must never be interpreted as
J-Space, GWT, model-quality, Claude-adapter, BASE, or whole-product acceptance.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_BINDINGS = (
    "bundled_core_manifest_digest",
    "checkpoint_digest",
    "tokenizer_digest",
    "runtime_digest",
    "jspace_profile_digest",
    "workspace_policy_digest",
    "zero_identity_digest",
    "grf_projection_digest",
    "claude_adapter_digest",
    "claude_capability_profile_digest",
)

OPTIONAL_BINDINGS = (
    "lens_profile_digest",
    "steering_calibration_digest",
)

ALLOWED_ORIGINS = {
    "ZERO",
    "HOOK_TIMER",
    "CLAUDE_CODE",
    "PROXY_SANDBOX_CONTROLLER",
    "OTHER",
}

ZERO_CREDIT_FIELDS = (
    "bundled_08b_exact_runtime_credit",
    "jspace_runtime_credit",
    "whole_gwt_production_credit",
    "claude_code_adapter_runtime_credit",
    "canonical_semantics_credit",
)


def _fail(errors: list[str], code: str) -> None:
    errors.append(code)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _is_git_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(GIT_SHA_RE.fullmatch(value))


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(receipt: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ["RECEIPT_NOT_OBJECT"]

    if receipt.get("schema") != SCHEMA:
        _fail(errors, "SCHEMA_MISMATCH")

    source = receipt.get("source")
    if not isinstance(source, dict):
        _fail(errors, "SOURCE_MISSING")
    else:
        if not _is_git_sha(source.get("commit")):
            _fail(errors, "SOURCE_COMMIT_INVALID")
        if not _is_git_sha(source.get("tree")):
            _fail(errors, "SOURCE_TREE_INVALID")
        dirty = source.get("dirty")
        if not isinstance(dirty, bool):
            _fail(errors, "SOURCE_DIRTY_FLAG_INVALID")
        if dirty is True and not _is_sha256(source.get("dirty_diff_digest")):
            _fail(errors, "DIRTY_SOURCE_DIFF_DIGEST_REQUIRED")

    executor = receipt.get("executor")
    if not isinstance(executor, dict):
        _fail(errors, "EXECUTOR_MISSING")
    else:
        for key in ("os", "machine_id_digest", "runner_identity_digest"):
            value = executor.get(key)
            if key.endswith("_digest"):
                if not _is_sha256(value):
                    _fail(errors, f"EXECUTOR_{key.upper()}_INVALID")
            elif not isinstance(value, str) or not value.strip():
                _fail(errors, f"EXECUTOR_{key.upper()}_INVALID")

    pre = receipt.get("prestart_frozen_baseline")
    if not isinstance(pre, dict):
        _fail(errors, "PRESTART_BASELINE_MISSING")
    else:
        generation = pre.get("generation")
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
            _fail(errors, "PRESTART_GENERATION_INVALID")
        if not _is_git_sha(pre.get("agentzero_export_head")):
            _fail(errors, "PRESTART_EXPORT_HEAD_INVALID")
        if not isinstance(pre.get("receipt_source_short"), str) or not pre.get("receipt_source_short"):
            _fail(errors, "PRESTART_RECEIPT_SOURCE_SHORT_INVALID")

    expected = receipt.get("expected_binding")
    observed = receipt.get("observed_binding")
    if not isinstance(expected, dict):
        _fail(errors, "EXPECTED_BINDING_MISSING")
        expected = {}
    if not isinstance(observed, dict):
        _fail(errors, "OBSERVED_BINDING_MISSING")
        observed = {}

    for key in REQUIRED_BINDINGS:
        ev = expected.get(key)
        ov = observed.get(key)
        if not _is_sha256(ev):
            _fail(errors, f"EXPECTED_{key.upper()}_INVALID")
        if not _is_sha256(ov):
            _fail(errors, f"OBSERVED_{key.upper()}_INVALID")
        if _is_sha256(ev) and _is_sha256(ov) and ev != ov:
            _fail(errors, f"BINDING_MISMATCH:{key}")

    for key in OPTIONAL_BINDINGS:
        e_present = key in expected
        o_present = key in observed
        if e_present != o_present:
            _fail(errors, f"OPTIONAL_BINDING_PRESENCE_MISMATCH:{key}")
            continue
        if e_present:
            ev = expected.get(key)
            ov = observed.get(key)
            if not _is_sha256(ev):
                _fail(errors, f"EXPECTED_{key.upper()}_INVALID")
            if not _is_sha256(ov):
                _fail(errors, f"OBSERVED_{key.upper()}_INVALID")
            if _is_sha256(ev) and _is_sha256(ov) and ev != ov:
                _fail(errors, f"BINDING_MISMATCH:{key}")

    unexpected = sorted(set(observed) - set(expected))
    if unexpected:
        _fail(errors, "UNEXPECTED_OBSERVED_BINDINGS:" + ",".join(unexpected))

    post = receipt.get("poststart_observation")
    if not isinstance(post, dict):
        _fail(errors, "POSTSTART_OBSERVATION_MISSING")
    else:
        first_generation = post.get("first_generation")
        if not isinstance(first_generation, int) or isinstance(first_generation, bool) or first_generation < 0:
            _fail(errors, "POSTSTART_FIRST_GENERATION_INVALID")
        engine = post.get("first_inference_engine_choice")
        if not isinstance(engine, str) or not engine.strip():
            _fail(errors, "POSTSTART_ENGINE_CHOICE_INVALID")
        actions = post.get("first_actions")
        if not isinstance(actions, list) or not actions:
            _fail(errors, "POSTSTART_FIRST_ACTIONS_REQUIRED")
        else:
            seen: set[str] = set()
            for i, action in enumerate(actions):
                if not isinstance(action, dict):
                    _fail(errors, f"ACTION_{i}_NOT_OBJECT")
                    continue
                action_id = action.get("action_id")
                if not isinstance(action_id, str) or not action_id:
                    _fail(errors, f"ACTION_{i}_ID_INVALID")
                elif action_id in seen:
                    _fail(errors, f"ACTION_DUPLICATE_ID:{action_id}")
                else:
                    seen.add(action_id)
                origin = action.get("origin")
                if origin not in ALLOWED_ORIGINS:
                    _fail(errors, f"ACTION_{i}_ORIGIN_INVALID")
                if origin == "OTHER" and not isinstance(action.get("origin_detail"), str):
                    _fail(errors, f"ACTION_{i}_OTHER_DETAIL_REQUIRED")
                if not isinstance(action.get("effect_requested"), bool):
                    _fail(errors, f"ACTION_{i}_EFFECT_FLAG_INVALID")

    credits = receipt.get("credits")
    if not isinstance(credits, dict):
        _fail(errors, "CREDITS_MISSING")
    else:
        for key in ZERO_CREDIT_FIELDS:
            value = credits.get(key)
            if value != 0:
                _fail(errors, f"BOOT_BINDING_CANNOT_GRANT_CREDIT:{key}")
        if credits.get("binding_identity_credit") != "BOUND_OBSERVATION_ONLY":
            _fail(errors, "BINDING_IDENTITY_CREDIT_CLASS_INVALID")

    if receipt.get("claim_class") != "SOURCE_BOUND_BOOT_OBSERVATION_ONLY":
        _fail(errors, "CLAIM_CLASS_INVALID")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = _load_json(args.receipt)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"LOAD_ERROR:{type(exc).__name__}"]}, sort_keys=True))
        return 2

    errors = validate(receipt)
    print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
