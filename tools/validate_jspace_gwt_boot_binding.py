#!/usr/bin/env python3
"""Fail-closed validator for JSPACE_GWT_BOOT_BINDING_RECEIPT/v1.

This validates receipt structure and exact identity binding only. It deliberately does
not infer model quality, semantic truth, consciousness, or whole-product acceptance.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_SECRET_KEY_RE = re.compile(r"(?:^|_)(?:api_?key|token|secret|authorization|password)(?:$|_)", re.I)
ALLOWED_PROFILE_STATES = {"PRESENT", "ABSENT_UNCALIBRATED"}
ALLOWED_ACTION_ORIGINS = {"ZERO", "HOOK", "TIMER", "CLAUDE_CODE", "PROXY", "SANDBOX_CONTROLLER", "OTHER"}
FREE_ONLY_COST_CLASSES = {"FREE_LOCAL", "FREE_REMOTE"}
FORBIDDEN_CREDIT_KEYS = {
    "whole_gwt_production_credit",
    "model_quality_credit",
    "semantic_truth_credit",
    "consciousness_credit",
    "frank_v01_acceptance_credit",
}


class ReceiptFault(ValueError):
    pass


def _require_map(value: Any, path: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ReceiptFault(f"{path}:EXPECTED_OBJECT")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if type(value) is not list:
        raise ReceiptFault(f"{path}:EXPECTED_ARRAY")
    return value


def _require_str(value: Any, path: str) -> str:
    if type(value) is not str or not value.strip():
        raise ReceiptFault(f"{path}:EXPECTED_NONEMPTY_STRING")
    return value


def _require_bool(value: Any, path: str) -> bool:
    if type(value) is not bool:
        raise ReceiptFault(f"{path}:EXPECTED_BOOL")
    return value


def _require_int(value: Any, path: str) -> int:
    if type(value) is not int:
        raise ReceiptFault(f"{path}:EXPECTED_INT")
    return value


def _require_sha256(value: Any, path: str) -> str:
    text = _require_str(value, path)
    if not SHA256_RE.fullmatch(text):
        raise ReceiptFault(f"{path}:BAD_SHA256")
    return text


def _require_git_sha(value: Any, path: str) -> str:
    text = _require_str(value, path)
    if not GIT_SHA_RE.fullmatch(text):
        raise ReceiptFault(f"{path}:BAD_GIT_SHA")
    return text


def _walk_no_secrets(value: Any, path: str = "$") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ReceiptFault(f"{path}:NON_STRING_KEY")
            if FORBIDDEN_SECRET_KEY_RE.search(key):
                raise ReceiptFault(f"{path}.{key}:SECRET_FIELD_FORBIDDEN")
            _walk_no_secrets(child, f"{path}.{key}")
    elif type(value) is list:
        for index, child in enumerate(value):
            _walk_no_secrets(child, f"{path}[{index}]")


def _validate_profile_binding(value: Any, path: str) -> None:
    item = _require_map(value, path)
    state = _require_str(item.get("state"), f"{path}.state")
    if state not in ALLOWED_PROFILE_STATES:
        raise ReceiptFault(f"{path}.state:UNKNOWN_STATE")
    digest = item.get("sha256")
    if state == "PRESENT":
        _require_sha256(digest, f"{path}.sha256")
    elif digest is not None:
        raise ReceiptFault(f"{path}.sha256:MUST_BE_NULL_WHEN_UNCALIBRATED")


def validate_receipt(receipt: Any) -> dict[str, Any]:
    root = _require_map(receipt, "$")
    _walk_no_secrets(root)
    if root.get("schema") != "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1":
        raise ReceiptFault("$.schema:BAD_SCHEMA")

    required = (
        "source", "executor", "control", "prestart", "poststart",
        "bundled_cognition", "cognitive_fabric", "identity_projection",
        "claude_adapter", "first_inference", "first_actions", "credit_boundary",
    )
    for name in required:
        if name not in root:
            raise ReceiptFault(f"$.{name}:MISSING")

    source = _require_map(root["source"], "$.source")
    _require_str(source.get("repository"), "$.source.repository")
    _require_git_sha(source.get("commit_sha"), "$.source.commit_sha")
    _require_git_sha(source.get("tree_sha"), "$.source.tree_sha")
    _require_bool(source.get("dirty"), "$.source.dirty")
    if source["dirty"]:
        _require_sha256(source.get("dirty_state_sha256"), "$.source.dirty_state_sha256")
    elif source.get("dirty_state_sha256") is not None:
        raise ReceiptFault("$.source.dirty_state_sha256:MUST_BE_NULL_WHEN_CLEAN")

    executor = _require_map(root["executor"], "$.executor")
    for field in ("os_name", "os_release", "machine", "executor_id"):
        _require_str(executor.get(field), f"$.executor.{field}")

    control = _require_map(root["control"], "$.control")
    free_only = _require_bool(control.get("free_only"), "$.control.free_only")
    _require_str(control.get("control_version"), "$.control.control_version")

    prestart = _require_map(root["prestart"], "$.prestart")
    pre_generation = _require_int(prestart.get("generation"), "$.prestart.generation")
    if pre_generation < 0:
        raise ReceiptFault("$.prestart.generation:NEGATIVE")
    _require_str(prestart.get("baseline_id"), "$.prestart.baseline_id")

    poststart = _require_map(root["poststart"], "$.poststart")
    post_generation = _require_int(poststart.get("generation"), "$.poststart.generation")
    if post_generation < pre_generation:
        raise ReceiptFault("$.poststart.generation:REGRESSION")
    _require_str(poststart.get("checkpoint_id"), "$.poststart.checkpoint_id")
    _require_bool(poststart.get("observation_boundary_complete"), "$.poststart.observation_boundary_complete")
    if not poststart["observation_boundary_complete"]:
        raise ReceiptFault("$.poststart.observation_boundary_complete:REQUIRED_TRUE")

    core = _require_map(root["bundled_cognition"], "$.bundled_cognition")
    for field in ("engine_id", "model_family", "runtime_identity", "claycode_contract_version", "grf_contract_version", "hyperposition_contract_version", "compatible_entityos_range"):
        _require_str(core.get(field), f"$.bundled_cognition.{field}")
    for field in ("manifest_sha256", "checkpoint_sha256", "tokenizer_sha256", "runtime_sha256"):
        _require_sha256(core.get(field), f"$.bundled_cognition.{field}")
    _validate_profile_binding(core.get("jspace_profile"), "$.bundled_cognition.jspace_profile")
    _validate_profile_binding(core.get("lens_profile"), "$.bundled_cognition.lens_profile")
    _validate_profile_binding(core.get("steering_calibration"), "$.bundled_cognition.steering_calibration")
    _require_sha256(core.get("workspace_calibration_sha256"), "$.bundled_cognition.workspace_calibration_sha256")
    _require_sha256(core.get("provenance_sha256"), "$.bundled_cognition.provenance_sha256")

    fabric = _require_map(root["cognitive_fabric"], "$.cognitive_fabric")
    for field in ("gwt_policy_sha256", "thalamus_policy_sha256", "epq_profile_sha256", "workspace_policy_sha256"):
        _require_sha256(fabric.get(field), f"$.cognitive_fabric.{field}")
    mode = _require_str(fabric.get("jspace_mode"), "$.cognitive_fabric.jspace_mode")
    if mode not in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}:
        raise ReceiptFault("$.cognitive_fabric.jspace_mode:BAD_MODE")

    identity = _require_map(root["identity_projection"], "$.identity_projection")
    _require_sha256(identity.get("zero_identity_sha256"), "$.identity_projection.zero_identity_sha256")
    _require_sha256(identity.get("grf_projection_sha256"), "$.identity_projection.grf_projection_sha256")

    claude = _require_map(root["claude_adapter"], "$.claude_adapter")
    _require_str(claude.get("adapter_version"), "$.claude_adapter.adapter_version")
    _require_sha256(claude.get("capability_profile_sha256"), "$.claude_adapter.capability_profile_sha256")
    _require_bool(claude.get("enabled"), "$.claude_adapter.enabled")

    first = _require_map(root["first_inference"], "$.first_inference")
    engine_class = _require_str(first.get("engine_class"), "$.first_inference.engine_class")
    if engine_class not in {"BUNDLED_LOCAL", "CLAUDE_CODE", "OTHER_LOCAL", "REMOTE", "NONE"}:
        raise ReceiptFault("$.first_inference.engine_class:BAD_ENGINE_CLASS")
    _require_str(first.get("engine_id"), "$.first_inference.engine_id")
    cost_class = _require_str(first.get("cost_class"), "$.first_inference.cost_class")
    if free_only and cost_class not in FREE_ONLY_COST_CLASSES:
        raise ReceiptFault("$.first_inference.cost_class:FREE_ONLY_DENIED")
    if first.get("capability_receipt_sha256") is not None:
        _require_sha256(first.get("capability_receipt_sha256"), "$.first_inference.capability_receipt_sha256")

    actions = _require_list(root["first_actions"], "$.first_actions")
    seen_action_ids: set[str] = set()
    for index, value in enumerate(actions):
        path = f"$.first_actions[{index}]"
        action = _require_map(value, path)
        action_id = _require_str(action.get("action_id"), f"{path}.action_id")
        if action_id in seen_action_ids:
            raise ReceiptFault(f"{path}.action_id:DUPLICATE")
        seen_action_ids.add(action_id)
        origin = _require_str(action.get("origin"), f"{path}.origin")
        if origin not in ALLOWED_ACTION_ORIGINS:
            raise ReceiptFault(f"{path}.origin:BAD_ORIGIN")
        _require_str(action.get("kind"), f"{path}.kind")
        _require_sha256(action.get("receipt_sha256"), f"{path}.receipt_sha256")
    _require_bool(root.get("first_action_observation_complete"), "$.first_action_observation_complete")
    if not root["first_action_observation_complete"]:
        raise ReceiptFault("$.first_action_observation_complete:REQUIRED_TRUE")

    credit = _require_map(root["credit_boundary"], "$.credit_boundary")
    for key in FORBIDDEN_CREDIT_KEYS:
        if _require_bool(credit.get(key), f"$.credit_boundary.{key}"):
            raise ReceiptFault(f"$.credit_boundary.{key}:FORBIDDEN_TRUE")
    _require_bool(credit.get("boot_binding_credit"), "$.credit_boundary.boot_binding_credit")

    return {
        "ok": True,
        "status": "VALID_BOOT_BINDING_RECEIPT",
        "source_commit": source["commit_sha"],
        "source_tree": source["tree_sha"],
        "pre_generation": pre_generation,
        "post_generation": post_generation,
        "bundled_engine_id": core["engine_id"],
        "jspace_mode": mode,
        "first_inference_engine_class": engine_class,
        "first_action_count": len(actions),
        "credit_scope": "BOOT_BINDING_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        result = validate_receipt(receipt)
    except (OSError, json.JSONDecodeError, ReceiptFault) as exc:
        print(json.dumps({"ok": False, "status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
