#!/usr/bin/env python3
"""Assess the existing local J-Space raw probe against a predeclared policy.

This is a second-stage evaluator for ``ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v2``.
It deliberately reuses the canonical raw-probe validator rather than creating a competing
probe or receipt authority.

The acceptance policy is valid only when its exact bytes existed in a Git commit that is
an ancestor of (or equal to) the raw probe's ``source_git_head``. This makes target/off-target
metric identity, intervention locus, token family, placebo family and numerical thresholds
predeclared evidence instead of post-hoc choices.

Even when every policy gate passes, the current raw probe still lacks verified exact
loader-consumption attestation and canonical ModelExecution/InferenceReceipt admission.
Therefore this evaluator can only report a predeclared *effect-pattern* result. It always
keeps J-Space causal-control, model-runtime, HCU, training, canonical-truth and real-effect
credit at zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping

try:
    from tools.validate_hcu_jspace_local_activation_probe_v2 import (
        ProbeReceiptError,
        validate as validate_raw_probe,
    )
except ModuleNotFoundError:
    from validate_hcu_jspace_local_activation_probe_v2 import (  # type: ignore
        ProbeReceiptError,
        validate as validate_raw_probe,
    )

RAW_SCHEMA = "ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v2"
POLICY_SCHEMA = "HCU_JSPACE_LOCAL_INTERVENTION_ACCEPTANCE_POLICY/v1"
ASSESSMENT_SCHEMA = "HCU_JSPACE_LOCAL_INTERVENTION_ASSESSMENT/v1"
INTERVENTION_FAMILY = "ACTIVATION_REPLACEMENT_CLEAN_TO_CORRUPTED/v1"
SHAM_POLICY = "SAME_SITE_CORRUPTED_REFERENCE_NOOP/v1"
OFF_TARGET_POLICY = "DISTINCT_POSITION_CLEAN_REFERENCE_PATCH/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ZERO_CREDITS = {
    "entityos_hcu_whole_runtime": 0,
    "hcu_full_runtime": 0,
    "jspace_model_runtime": 0,
    "training": 0,
    "jspace_causal_control": 0,
    "canonical_truth": 0,
    "real_effect": 0,
}


class AssessmentRejected(ValueError):
    pass


def _obj(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AssessmentRejected(f"{field}:OBJECT_REQUIRED")
    return value


def _text(value: Any, field: str, *, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AssessmentRejected(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise AssessmentRejected(f"{field}:TOO_LONG")
    return value


def _hex(value: Any, field: str, pattern: re.Pattern[str]) -> str:
    value = _text(value, field, max_len=64)
    if pattern.fullmatch(value) is None or value in {"0" * len(value), "f" * len(value)}:
        raise AssessmentRejected(f"{field}:DIGEST_INVALID")
    return value


def _integer(value: Any, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AssessmentRejected(f"{field}:INTEGER_REQUIRED")
    return value


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssessmentRejected(f"{field}:FINITE_NUMBER_REQUIRED")
    value = float(value)
    if not math.isfinite(value):
        raise AssessmentRejected(f"{field}:FINITE_NUMBER_REQUIRED")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], field: str) -> None:
    actual = set(value)
    if actual != expected:
        raise AssessmentRejected(
            f"{field}:KEYSET_MISMATCH:missing={sorted(expected-actual)}:extra={sorted(actual-expected)}"
        )


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            stderr=subprocess.DEVNULL,
            text=text,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AssessmentRejected(f"GIT_PROOF_FAILED:{':'.join(args[:2])}") from exc


def git_root(start: Path) -> Path:
    start = start.resolve()
    root = Path(str(_git(start if start.is_dir() else start.parent, "rev-parse", "--show-toplevel")).strip())
    if not root.is_dir():
        raise AssessmentRejected("GIT_ROOT_REQUIRED")
    return root.resolve()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def verify_predeclared_policy(
    policy_path: Path,
    *,
    policy_commit: str,
    probe_source_git_head: str,
) -> dict[str, Any]:
    policy_commit = _hex(policy_commit, "policy_commit", HEX40)
    probe_source_git_head = _hex(probe_source_git_head, "probe_source_git_head", HEX40)
    root = git_root(policy_path)
    policy_path = policy_path.resolve()
    try:
        rel = policy_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise AssessmentRejected("POLICY_MUST_BE_INSIDE_CANONICAL_GIT_ROOT") from exc
    actual = policy_path.read_bytes()
    committed = _git(root, "show", f"{policy_commit}:{rel}", text=False)
    assert isinstance(committed, bytes)
    if actual != committed:
        raise AssessmentRejected("POLICY_BYTES_DO_NOT_MATCH_PREDECLARED_COMMIT")
    ancestor = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", policy_commit, probe_source_git_head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if ancestor.returncode != 0:
        raise AssessmentRejected("POLICY_COMMIT_NOT_ANCESTOR_OF_PROBE_SOURCE_HEAD")
    return {
        "policy_path": rel,
        "policy_commit": policy_commit,
        "policy_sha256": hashlib.sha256(actual).hexdigest(),
        "policy_git_blob_sha1": git_blob_sha1(actual),
        "predeclared_ancestor_of_probe_source_head": True,
    }


POLICY_KEYS = {
    "schema",
    "authority_epoch",
    "probe_schema",
    "probe_source_sha256",
    "intervention_family",
    "sham_policy",
    "off_target_policy",
    "scope",
    "thresholds",
}
SCOPE_KEYS = {
    "layer",
    "target_position",
    "off_target_position",
    "clean_token_ids_sha256",
    "corrupted_token_ids_sha256",
    "target_token_id",
    "off_target_token_id",
}
THRESHOLD_KEYS = {
    "min_corruption_effect_on_target_logit",
    "min_target_patch_effect_on_target_logit",
    "min_target_advantage_vs_sham",
    "min_target_advantage_vs_off_target_patch",
    "max_abs_sham_effect_on_target_logit",
    "max_abs_off_target_patch_effect_on_target_logit",
    "max_abs_target_patch_effect_on_off_target_logit",
}


def normalize_policy(policy: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    policy = _obj(policy, "policy")
    _exact_keys(policy, POLICY_KEYS, "policy")
    if _text(policy["schema"], "policy.schema") != POLICY_SCHEMA:
        raise AssessmentRejected("POLICY_SCHEMA_MISMATCH")
    if _text(policy["probe_schema"], "policy.probe_schema") != RAW_SCHEMA:
        raise AssessmentRejected("POLICY_PROBE_SCHEMA_MISMATCH")
    receipt_authority = _obj(receipt.get("authority"), "receipt.authority")
    if _text(policy["authority_epoch"], "policy.authority_epoch", max_len=64) != _text(
        receipt_authority.get("epoch"), "receipt.authority.epoch", max_len=64
    ):
        raise AssessmentRejected("POLICY_AUTHORITY_EPOCH_MISMATCH")
    probe_source = _hex(receipt.get("probe_source_sha256"), "receipt.probe_source_sha256", HEX64)
    if _hex(policy["probe_source_sha256"], "policy.probe_source_sha256", HEX64) != probe_source:
        raise AssessmentRejected("POLICY_PROBE_SOURCE_MISMATCH")
    if _text(policy["intervention_family"], "policy.intervention_family") != INTERVENTION_FAMILY:
        raise AssessmentRejected("POLICY_INTERVENTION_FAMILY_UNSUPPORTED")
    if _text(policy["sham_policy"], "policy.sham_policy") != SHAM_POLICY:
        raise AssessmentRejected("POLICY_SHAM_FAMILY_UNSUPPORTED")
    if _text(policy["off_target_policy"], "policy.off_target_policy") != OFF_TARGET_POLICY:
        raise AssessmentRejected("POLICY_OFF_TARGET_FAMILY_UNSUPPORTED")

    scope = _obj(policy["scope"], "policy.scope")
    _exact_keys(scope, SCOPE_KEYS, "policy.scope")
    normalized_scope = {
        "layer": _integer(scope["layer"], "policy.scope.layer"),
        "target_position": _integer(scope["target_position"], "policy.scope.target_position"),
        "off_target_position": _integer(scope["off_target_position"], "policy.scope.off_target_position"),
        "clean_token_ids_sha256": _hex(scope["clean_token_ids_sha256"], "policy.scope.clean_token_ids_sha256", HEX64),
        "corrupted_token_ids_sha256": _hex(
            scope["corrupted_token_ids_sha256"], "policy.scope.corrupted_token_ids_sha256", HEX64
        ),
        "target_token_id": _integer(scope["target_token_id"], "policy.scope.target_token_id"),
        "off_target_token_id": _integer(scope["off_target_token_id"], "policy.scope.off_target_token_id"),
    }
    if normalized_scope["target_position"] == normalized_scope["off_target_position"]:
        raise AssessmentRejected("POLICY_SCOPE_DISTINCT_POSITIONS_REQUIRED")
    if normalized_scope["target_token_id"] == normalized_scope["off_target_token_id"]:
        raise AssessmentRejected("POLICY_SCOPE_DISTINCT_METRIC_TOKENS_REQUIRED")

    thresholds = _obj(policy["thresholds"], "policy.thresholds")
    _exact_keys(thresholds, THRESHOLD_KEYS, "policy.thresholds")
    normalized_thresholds = {
        key: _number(thresholds[key], f"policy.thresholds.{key}") for key in sorted(THRESHOLD_KEYS)
    }
    if any(value < 0.0 for value in normalized_thresholds.values()):
        raise AssessmentRejected("POLICY_THRESHOLDS_MUST_BE_NONNEGATIVE")

    return {
        "schema": POLICY_SCHEMA,
        "authority_epoch": _text(policy["authority_epoch"], "policy.authority_epoch", max_len=64),
        "probe_schema": RAW_SCHEMA,
        "probe_source_sha256": probe_source,
        "intervention_family": INTERVENTION_FAMILY,
        "sham_policy": SHAM_POLICY,
        "off_target_policy": OFF_TARGET_POLICY,
        "scope": normalized_scope,
        "thresholds": normalized_thresholds,
    }


def _conditions(receipt: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    probe = _obj(receipt.get("probe"), "receipt.probe")
    rows = probe.get("conditions")
    if not isinstance(rows, list):
        raise AssessmentRejected("receipt.probe.conditions:LIST_REQUIRED")
    result: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        row = _obj(row, f"receipt.probe.conditions[{index}]")
        name = _text(row.get("condition"), f"receipt.probe.conditions[{index}].condition")
        if name in result:
            raise AssessmentRejected(f"CONDITION_DUPLICATE:{name}")
        result[name] = row
    return result


def _condition_number(row: Mapping[str, Any], field: str, condition: str) -> float:
    return _number(row.get(field), f"{condition}.{field}")


def _condition_int(row: Mapping[str, Any], field: str, condition: str) -> int:
    return _integer(row.get(field), f"{condition}.{field}")


def assess(
    receipt: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    policy_identity: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        raw_result = validate_raw_probe(dict(receipt))
    except ProbeReceiptError as exc:
        raise AssessmentRejected(f"RAW_PROBE_REJECTED:{exc}") from exc
    if raw_result.get("ok") is not True or raw_result.get("probe_mode") != "intervention":
        raise AssessmentRejected("RAW_PROBE_INTERVENTION_PASS_REQUIRED")
    if receipt.get("schema") != RAW_SCHEMA:
        raise AssessmentRejected("RAW_PROBE_SCHEMA_MISMATCH")

    policy_n = normalize_policy(policy, receipt)
    policy_identity = _obj(policy_identity, "policy_identity")
    if policy_identity.get("predeclared_ancestor_of_probe_source_head") is not True:
        raise AssessmentRejected("PREDECLARED_POLICY_GIT_PROOF_REQUIRED")
    for key in ("policy_path", "policy_commit", "policy_sha256", "policy_git_blob_sha1"):
        _text(policy_identity.get(key), f"policy_identity.{key}")

    probe = _obj(receipt.get("probe"), "receipt.probe")
    scope = policy_n["scope"]
    comparisons = {
        "layer": _integer(probe.get("layer"), "receipt.probe.layer") == scope["layer"],
        "target_position": _integer(probe.get("target_position"), "receipt.probe.target_position")
        == scope["target_position"],
        "off_target_position": _integer(probe.get("off_target_position"), "receipt.probe.off_target_position")
        == scope["off_target_position"],
        "clean_token_ids_sha256": _hex(
            probe.get("clean_token_ids_sha256"), "receipt.probe.clean_token_ids_sha256", HEX64
        )
        == scope["clean_token_ids_sha256"],
        "corrupted_token_ids_sha256": _hex(
            probe.get("corrupted_token_ids_sha256"), "receipt.probe.corrupted_token_ids_sha256", HEX64
        )
        == scope["corrupted_token_ids_sha256"],
    }
    if not all(comparisons.values()):
        raise AssessmentRejected(
            "PREDECLARED_SCOPE_MISMATCH:" + ",".join(sorted(key for key, ok in comparisons.items() if not ok))
        )

    conditions = _conditions(receipt)
    required = {
        "BASELINE_CLEAN",
        "BASELINE_CORRUPTED",
        "INTERVENTION_TARGET",
        "SHAM_CONTROL",
        "OFF_TARGET_CONTROL",
        "BASELINE_CLEAN_OFF_TARGET_REFERENCE",
    }
    if set(conditions) != required:
        raise AssessmentRejected("RAW_PROBE_CONDITION_SET_CHANGED_AFTER_VALIDATION")

    for name, row in conditions.items():
        if _condition_int(row, "target_token_id", name) != scope["target_token_id"]:
            raise AssessmentRejected(f"PREDECLARED_TARGET_TOKEN_MISMATCH:{name}")
        if _condition_int(row, "off_target_token_id", name) != scope["off_target_token_id"]:
            raise AssessmentRejected(f"PREDECLARED_OFF_TARGET_TOKEN_MISMATCH:{name}")

    clean = conditions["BASELINE_CLEAN"]
    corrupted = conditions["BASELINE_CORRUPTED"]
    target = conditions["INTERVENTION_TARGET"]
    sham = conditions["SHAM_CONTROL"]
    off_target = conditions["OFF_TARGET_CONTROL"]

    metrics = {
        "corruption_effect_on_target_logit": (
            _condition_number(clean, "target_logit", "BASELINE_CLEAN")
            - _condition_number(corrupted, "target_logit", "BASELINE_CORRUPTED")
        ),
        "target_patch_effect_on_target_logit": (
            _condition_number(target, "target_logit", "INTERVENTION_TARGET")
            - _condition_number(corrupted, "target_logit", "BASELINE_CORRUPTED")
        ),
        "sham_effect_on_target_logit": (
            _condition_number(sham, "target_logit", "SHAM_CONTROL")
            - _condition_number(corrupted, "target_logit", "BASELINE_CORRUPTED")
        ),
        "off_target_patch_effect_on_target_logit": (
            _condition_number(off_target, "target_logit", "OFF_TARGET_CONTROL")
            - _condition_number(corrupted, "target_logit", "BASELINE_CORRUPTED")
        ),
        "target_patch_effect_on_off_target_logit": (
            _condition_number(target, "off_target_logit", "INTERVENTION_TARGET")
            - _condition_number(corrupted, "off_target_logit", "BASELINE_CORRUPTED")
        ),
    }
    metrics["target_advantage_vs_sham"] = (
        metrics["target_patch_effect_on_target_logit"] - metrics["sham_effect_on_target_logit"]
    )
    metrics["target_advantage_vs_off_target_patch"] = (
        metrics["target_patch_effect_on_target_logit"]
        - metrics["off_target_patch_effect_on_target_logit"]
    )

    derived = _obj(probe.get("derived_metrics"), "receipt.probe.derived_metrics")
    for key in (
        "target_patch_effect_on_target_logit",
        "sham_effect_on_target_logit",
        "off_target_patch_effect_on_target_logit",
        "target_patch_effect_on_off_target_logit",
    ):
        observed = _number(derived.get(key), f"receipt.probe.derived_metrics.{key}")
        if not math.isclose(observed, metrics[key], rel_tol=0.0, abs_tol=1e-12):
            raise AssessmentRejected(f"RAW_PROBE_DERIVED_METRIC_MISMATCH:{key}")

    t = policy_n["thresholds"]
    gates = {
        "corruption_effect": metrics["corruption_effect_on_target_logit"]
        >= t["min_corruption_effect_on_target_logit"],
        "target_effect": metrics["target_patch_effect_on_target_logit"]
        >= t["min_target_patch_effect_on_target_logit"],
        "target_advantage_vs_sham": metrics["target_advantage_vs_sham"]
        >= t["min_target_advantage_vs_sham"],
        "target_advantage_vs_off_target_patch": metrics["target_advantage_vs_off_target_patch"]
        >= t["min_target_advantage_vs_off_target_patch"],
        "sham_specificity": abs(metrics["sham_effect_on_target_logit"])
        <= t["max_abs_sham_effect_on_target_logit"],
        "off_target_patch_specificity": abs(metrics["off_target_patch_effect_on_target_logit"])
        <= t["max_abs_off_target_patch_effect_on_target_logit"],
        "target_off_target_regression": abs(metrics["target_patch_effect_on_off_target_logit"])
        <= t["max_abs_target_patch_effect_on_off_target_logit"],
    }
    effect_pattern_pass = all(gates.values())
    post_load = _obj(receipt.get("post_load_identity"), "receipt.post_load_identity")
    if post_load.get("loader_consumption_attestation") is not False:
        raise AssessmentRejected("RAW_PROBE_LOADER_BOUNDARY_CHANGED_UNEXPECTEDLY")

    return {
        "schema": ASSESSMENT_SCHEMA,
        "raw_probe_schema": RAW_SCHEMA,
        "raw_probe_source_git_head": _hex(receipt.get("source_git_head"), "receipt.source_git_head", HEX40),
        "policy": policy_n,
        "policy_identity": dict(policy_identity),
        "effect_pattern_pass": effect_pattern_pass,
        "evidence_class": (
            "PREDECLARED_LOCAL_INTERVENTION_EFFECT_PATTERN_PASS_RAW_PROBE_ONLY"
            if effect_pattern_pass
            else "PREDECLARED_LOCAL_INTERVENTION_EFFECT_PATTERN_REJECTED"
        ),
        "metrics": metrics,
        "gates": gates,
        "loader_consumption_verified": False,
        "canonical_inference_binding_verified": False,
        "jspace_causal_control_candidate": False,
        "runtime_promotion_allowed": False,
        "credits": dict(ZERO_CREDITS),
        "next_gate": (
            "VERIFIED_LOADER_CONSUMPTION_PLUS_CANONICAL_MODEL_EXECUTION_INFERENCE_RECEIPT_BINDING"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("--policy-commit", required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    try:
        raw_result = validate_raw_probe(receipt)
        if raw_result.get("ok") is not True:
            raise AssessmentRejected("RAW_PROBE_VALIDATOR_DID_NOT_PASS")
        identity = verify_predeclared_policy(
            args.policy,
            policy_commit=args.policy_commit,
            probe_source_git_head=_text(receipt.get("source_git_head"), "receipt.source_git_head", max_len=40),
        )
        result = assess(receipt, policy, policy_identity=identity)
    except (json.JSONDecodeError, OSError, ProbeReceiptError, AssessmentRejected) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "assessment": result}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
