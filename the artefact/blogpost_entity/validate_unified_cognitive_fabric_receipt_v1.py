#!/usr/bin/env python3
"""Fail-closed validator for UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.

Source-level contract only. Runtime credit requires this validator to run against a
receipt emitted by the exact admitted runtime/source identity.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

RECEIPT_TYPE = "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1"
PHASES = {"BOOT_BINDING", "INFERENCE_CYCLE"}
ENGINE_CLASSES = {"LOCAL_08B", "CLAUDE_CODE", "ADAPTIVE_BACKEND", "DETERMINISTIC_ONLY"}
DECISIONS = {"ACCEPTED_CANDIDATE", "REJECTED", "STALE", "BLOCKED", "ERROR", "NO_INFERENCE"}
EPISTEMIC_STATUSES = {"MEASURED_SUPPORTED", "UNKNOWN", "ERROR", "REFUTED", "NOT_APPLICABLE"}
TERMINAL_STATUSES = {"DONE", "REJECTED", "BLOCKED", "ABORTED", "ERROR", "UNKNOWN"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class ReceiptError(ValueError):
    pass


def _fail(code: str) -> None:
    raise ReceiptError(code)


def _exact_dict(value: Any, code: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail(code)
    return value


def _exact_list(value: Any, code: str) -> list[Any]:
    if type(value) is not list:
        _fail(code)
    return value


def _exact_str(value: Any, code: str, *, nonempty: bool = True) -> str:
    if type(value) is not str:
        _fail(code)
    if nonempty and not value:
        _fail(code)
    return value


def _exact_bool(value: Any, code: str) -> bool:
    if type(value) is not bool:
        _fail(code)
    return value


def _exact_int(value: Any, code: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail(code)
    return value


def _sha256(value: Any, code: str) -> str:
    text = _exact_str(value, code)
    if SHA256_RE.fullmatch(text) is None:
        _fail(code)
    return text


def _git_oid(value: Any, code: str) -> str:
    text = _exact_str(value, code)
    if GIT_OID_RE.fullmatch(text) is None:
        _fail(code)
    return text


def _finite_json(value: Any, path: str = "$") -> None:
    """Reject active subclasses and non-finite floats before canonical serialization."""
    t = type(value)
    if value is None or t in {str, bool, int}:
        return
    if t is float:
        if not math.isfinite(value):
            _fail(f"NONFINITE_JSON:{path}")
        return
    if t is list:
        for i, item in enumerate(value):
            _finite_json(item, f"{path}[{i}]")
        return
    if t is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail(f"NONSTRING_KEY:{path}")
            _finite_json(item, f"{path}.{key}")
        return
    _fail(f"UNSUPPORTED_JSON_TYPE:{path}:{t.__name__}")


def canonical_digest(receipt: dict[str, Any]) -> str:
    material = copy.deepcopy(receipt)
    terminal = _exact_dict(material.get("terminal"), "TERMINAL_REQUIRED")
    terminal.pop("terminal_digest", None)
    _finite_json(material)
    payload = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_receipt(
    receipt: Any,
    *,
    expected_source_commit: str | None = None,
    expected_source_tree: str | None = None,
    expected_generation: int | None = None,
    expected_zero_identity_digest: str | None = None,
    expected_grf_digest: str | None = None,
    expected_bundled_manifest_digest: str | None = None,
    expect_free_only: bool | None = None,
    verify_terminal_digest: bool = True,
) -> dict[str, Any]:
    r = _exact_dict(receipt, "RECEIPT_MUST_BE_OBJECT")
    _finite_json(r)

    if r.get("receipt_type") != RECEIPT_TYPE:
        _fail("RECEIPT_TYPE_MISMATCH")
    phase = _exact_str(r.get("phase"), "PHASE_REQUIRED")
    if phase not in PHASES:
        _fail("PHASE_UNSUPPORTED")

    source = _exact_dict(r.get("source"), "SOURCE_REQUIRED")
    source_commit = _git_oid(source.get("commit"), "SOURCE_COMMIT_INVALID")
    source_tree = _git_oid(source.get("tree"), "SOURCE_TREE_INVALID")
    _exact_bool(source.get("dirty"), "SOURCE_DIRTY_REQUIRED")
    _exact_str(source.get("executor"), "SOURCE_EXECUTOR_REQUIRED")
    _exact_str(source.get("runtime_identity"), "SOURCE_RUNTIME_IDENTITY_REQUIRED")
    _exact_str(source.get("started_at"), "SOURCE_STARTED_AT_REQUIRED")
    _exact_str(source.get("completed_at"), "SOURCE_COMPLETED_AT_REQUIRED")

    entity = _exact_dict(r.get("entity"), "ENTITY_REQUIRED")
    _exact_str(entity.get("mini_entity_version"), "MINI_ENTITY_VERSION_REQUIRED")
    _exact_str(entity.get("entityos_version"), "ENTITYOS_VERSION_REQUIRED")
    generation = _exact_int(entity.get("generation"), "GENERATION_INVALID")

    zero = _exact_dict(r.get("zero"), "ZERO_REQUIRED")
    zero_identity_digest = _sha256(zero.get("identity_digest"), "ZERO_IDENTITY_DIGEST_INVALID")
    grf_digest = _sha256(zero.get("grf_digest"), "GRF_DIGEST_INVALID")
    _sha256(zero.get("workspace_policy_digest"), "WORKSPACE_POLICY_DIGEST_INVALID")

    bundled = _exact_dict(r.get("bundled_cognition"), "BUNDLED_COGNITION_REQUIRED")
    bundled_manifest_digest = _sha256(bundled.get("manifest_digest"), "BUNDLED_MANIFEST_DIGEST_INVALID")
    _sha256(bundled.get("checkpoint_digest"), "CHECKPOINT_DIGEST_INVALID")
    _sha256(bundled.get("tokenizer_digest"), "TOKENIZER_DIGEST_INVALID")
    _sha256(bundled.get("jspace_profile_digest"), "JSPACE_PROFILE_DIGEST_INVALID")
    _sha256(bundled.get("lens_profile_digest"), "LENS_PROFILE_DIGEST_INVALID")
    _sha256(bundled.get("workspace_calibration_digest"), "WORKSPACE_CALIBRATION_DIGEST_INVALID")
    _exact_str(bundled.get("runtime_identity"), "BUNDLED_RUNTIME_IDENTITY_REQUIRED")

    workspace = _exact_dict(r.get("workspace"), "WORKSPACE_REQUIRED")
    _sha256(workspace.get("before_digest"), "WORKSPACE_BEFORE_DIGEST_INVALID")
    _sha256(workspace.get("after_digest"), "WORKSPACE_AFTER_DIGEST_INVALID")
    candidates = _exact_list(workspace.get("gwt_candidates"), "GWT_CANDIDATES_REQUIRED")
    if not candidates:
        _fail("GWT_CANDIDATES_EMPTY")
    winner_count = 0
    for index, candidate in enumerate(candidates):
        c = _exact_dict(candidate, f"GWT_CANDIDATE_INVALID:{index}")
        _exact_str(c.get("candidate_ref"), f"GWT_CANDIDATE_REF_INVALID:{index}")
        admitted = _exact_bool(c.get("admitted"), f"GWT_ADMITTED_INVALID:{index}")
        winner = _exact_bool(c.get("winner"), f"GWT_WINNER_INVALID:{index}")
        if winner and not admitted:
            _fail(f"GWT_WINNER_NOT_ADMITTED:{index}")
        winner_count += int(winner)
    if winner_count > 1:
        _fail("GWT_MULTIPLE_WINNERS")

    for key in (
        "jspace_observation_refs",
        "thalamus_decisions",
        "hyperposition_refs",
        "claycode_refs",
        "omega_refs",
    ):
        _exact_list(workspace.get(key), f"WORKSPACE_LIST_REQUIRED:{key}")
    _sha256(workspace.get("epq_digest"), "EPQ_DIGEST_INVALID")

    inference = _exact_dict(r.get("inference"), "INFERENCE_REQUIRED")
    engine_class = _exact_str(inference.get("engine_class"), "ENGINE_CLASS_REQUIRED")
    if engine_class not in ENGINE_CLASSES:
        _fail("ENGINE_CLASS_UNSUPPORTED")
    packet_digest = _sha256(inference.get("packet_digest"), "INFERENCE_PACKET_DIGEST_INVALID")
    candidate_only = _exact_bool(inference.get("candidate_only"), "CANDIDATE_ONLY_REQUIRED")
    if not candidate_only:
        _fail("MODEL_RESULT_NOT_CANDIDATE_ONLY")

    epistemic_status = _exact_str(inference.get("epistemic_status"), "EPISTEMIC_STATUS_REQUIRED")
    if epistemic_status not in EPISTEMIC_STATUSES:
        _fail("EPISTEMIC_STATUS_UNSUPPORTED")

    result_digest = inference.get("candidate_result_digest")
    if engine_class == "DETERMINISTIC_ONLY":
        if result_digest is not None:
            _fail("DETERMINISTIC_ONLY_RESULT_DIGEST_MUST_BE_NULL")
        if epistemic_status != "NOT_APPLICABLE":
            _fail("DETERMINISTIC_ONLY_EPISTEMIC_STATUS_MUST_BE_NOT_APPLICABLE")
    else:
        _sha256(result_digest, "CANDIDATE_RESULT_DIGEST_INVALID")
        if epistemic_status == "NOT_APPLICABLE":
            _fail("LEARNED_INFERENCE_EPISTEMIC_STATUS_REQUIRED")

    if engine_class == "CLAUDE_CODE":
        _exact_str(inference.get("adapter_version"), "CLAUDE_ADAPTER_VERSION_REQUIRED")
        _sha256(inference.get("capability_profile_digest"), "CLAUDE_CAPABILITY_PROFILE_DIGEST_INVALID")
    elif engine_class == "ADAPTIVE_BACKEND":
        _sha256(inference.get("capability_profile_digest"), "ADAPTIVE_CAPABILITY_PROFILE_DIGEST_INVALID")
        jspace_mode = _exact_str(inference.get("jspace_mode"), "ADAPTIVE_JSPACE_MODE_REQUIRED")
        if jspace_mode not in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}:
            _fail("ADAPTIVE_JSPACE_MODE_UNSUPPORTED")

    validation = _exact_dict(r.get("validation"), "VALIDATION_REQUIRED")
    decision = _exact_str(validation.get("decision"), "VALIDATION_DECISION_REQUIRED")
    if decision not in DECISIONS:
        _fail("VALIDATION_DECISION_UNSUPPORTED")
    _sha256(validation.get("reconciliation_digest"), "RECONCILIATION_DIGEST_INVALID")
    canonical_write = _exact_bool(validation.get("canonical_write"), "CANONICAL_WRITE_REQUIRED")
    effect_requested = _exact_bool(validation.get("effect_requested"), "EFFECT_REQUESTED_REQUIRED")
    effect_admitted = _exact_bool(validation.get("effect_admitted"), "EFFECT_ADMITTED_REQUIRED")
    if canonical_write and decision != "ACCEPTED_CANDIDATE":
        _fail("CANONICAL_WRITE_WITHOUT_ACCEPTED_CANDIDATE")
    if effect_admitted and not effect_requested:
        _fail("EFFECT_ADMITTED_WITHOUT_REQUEST")
    if (canonical_write or effect_admitted) and epistemic_status != "MEASURED_SUPPORTED":
        _fail("UNSUPPORTED_EPISTEMIC_AUTHORITY")

    authority = _exact_dict(r.get("authority"), "AUTHORITY_REQUIRED")
    for key in ("model_is_truth_authority", "model_is_effect_authority", "workspace_stability_is_factual_truth"):
        value = _exact_bool(authority.get(key), f"AUTHORITY_FLAG_REQUIRED:{key}")
        if value:
            _fail(f"AUTHORITY_VIOLATION:{key}")

    boundary = _exact_dict(r.get("boundary"), "BOUNDARY_REQUIRED")
    free_only = _exact_bool(boundary.get("free_only"), "FREE_ONLY_REQUIRED")
    secret_lookup_count = _exact_int(boundary.get("secret_lookup_count"), "SECRET_LOOKUP_COUNT_INVALID")
    network_attempt_count = _exact_int(boundary.get("network_attempt_count"), "NETWORK_ATTEMPT_COUNT_INVALID")
    _exact_str(boundary.get("first_action_origin"), "FIRST_ACTION_ORIGIN_REQUIRED")
    if free_only and (secret_lookup_count != 0 or network_attempt_count != 0):
        _fail("FREE_ONLY_EXTERNAL_TOUCH")

    terminal = _exact_dict(r.get("terminal"), "TERMINAL_REQUIRED")
    status = _exact_str(terminal.get("status"), "TERMINAL_STATUS_REQUIRED")
    if status not in TERMINAL_STATUSES:
        _fail("TERMINAL_STATUS_UNSUPPORTED")
    terminal_digest = _sha256(terminal.get("terminal_digest"), "TERMINAL_DIGEST_INVALID")

    if expected_source_commit is not None and source_commit != expected_source_commit:
        _fail("STALE_SOURCE_COMMIT")
    if expected_source_tree is not None and source_tree != expected_source_tree:
        _fail("STALE_SOURCE_TREE")
    if expected_generation is not None and generation != expected_generation:
        _fail("STALE_GENERATION")
    if expected_zero_identity_digest is not None and zero_identity_digest != expected_zero_identity_digest:
        _fail("STALE_ZERO_IDENTITY")
    if expected_grf_digest is not None and grf_digest != expected_grf_digest:
        _fail("STALE_GRF")
    if expected_bundled_manifest_digest is not None and bundled_manifest_digest != expected_bundled_manifest_digest:
        _fail("STALE_BUNDLED_MANIFEST")
    if expect_free_only is not None and free_only is not expect_free_only:
        _fail("FREE_ONLY_EXPECTATION_MISMATCH")

    if verify_terminal_digest and terminal_digest != canonical_digest(r):
        _fail("TERMINAL_DIGEST_MISMATCH")

    return {
        "ok": True,
        "receipt_type": RECEIPT_TYPE,
        "phase": phase,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "generation": generation,
        "engine_class": engine_class,
        "epistemic_status": epistemic_status,
        "packet_digest": packet_digest,
        "terminal_digest": terminal_digest,
    }


def _load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(
        text,
        parse_constant=lambda value: (_ for _ in ()).throw(ReceiptError(f"NONFINITE_JSON_CONSTANT:{value}")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expected-source-commit")
    parser.add_argument("--expected-source-tree")
    parser.add_argument("--expected-generation", type=int)
    parser.add_argument("--expected-zero-identity-digest")
    parser.add_argument("--expected-grf-digest")
    parser.add_argument("--expected-bundled-manifest-digest")
    parser.add_argument("--expect-free-only", choices=("true", "false"))
    args = parser.parse_args(argv)

    try:
        receipt = _load_json(args.receipt)
        result = validate_receipt(
            receipt,
            expected_source_commit=args.expected_source_commit,
            expected_source_tree=args.expected_source_tree,
            expected_generation=args.expected_generation,
            expected_zero_identity_digest=args.expected_zero_identity_digest,
            expected_grf_digest=args.expected_grf_digest,
            expected_bundled_manifest_digest=args.expected_bundled_manifest_digest,
            expect_free_only=None if args.expect_free_only is None else args.expect_free_only == "true",
        )
    except (OSError, json.JSONDecodeError, ReceiptError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
