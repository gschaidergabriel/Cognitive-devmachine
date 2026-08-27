#!/usr/bin/env python3
"""Joint-case-universe successor promotion gate for Trigger-1 J-Space claims.

v9 composes v8 and then closes a composition gap: v7 semantic-factorial evidence and
v8 preregistration/runtime binding must refer to the SAME executed cases and the SAME
per-case control receipt maps. It is insufficient for two independently valid evidence
universes to make two independent predecessor gates green.

The common case identity is reconstructed from split, case_id, seed, prompt_sha256,
semantic_target, output_code_identity and split_family_id. The preregistration-facing
attestation must additionally echo the exact six-control runtime receipt map used by the
factorial evidence row. Any missing/extra/mismatched case or receipt fails closed.

This adjudicator is source-only, fail-closed and non-minting. It never runs a model and
cannot mint canonical semantics, J-Space model runtime, HCU, EntityOS, training, BASE,
or real-effect credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v8 as v8
import trigger1_semantic_factorial_evidence_gate_v1 as factorial

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v9"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v9"
JOINT_BINDING_SCHEMA = "CLAY_TRIGGER1_JOINT_CASE_UNIVERSE_BINDING/v1"
SPLITS = ("CALIBRATION", "HOLDOUT")
COMMON_FIELDS = (
    "case_id",
    "seed",
    "prompt_sha256",
    "semantic_target",
    "output_code_identity",
    "split_family_id",
)


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _normalized_receipts(value: Any, prefix: str, failures: list[str]) -> dict[str, str] | None:
    if not isinstance(value, dict):
        failures.append(f"{prefix}_CONTROL_RUNTIME_RECEIPTS_REQUIRED")
        return None
    keys = set(value)
    expected = set(factorial.REQUIRED_CONTROLS)
    if keys != expected:
        failures.append(f"{prefix}_CONTROL_RUNTIME_RECEIPT_SET_MISMATCH")
        return None
    out: dict[str, str] = {}
    for control in factorial.REQUIRED_CONTROLS:
        digest = value.get(control)
        if not _sha256(digest):
            failures.append(f"{prefix}_CONTROL_RUNTIME_RECEIPT_INVALID:{control}")
        else:
            out[control] = digest
    return out if len(out) == len(expected) else None


def _factorial_rows(candidate: dict[str, Any], failures: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for split in SPLITS:
        section = candidate.get(split.lower())
        if not isinstance(section, dict):
            failures.append(f"JOINT_{split}_SECTION_REQUIRED")
            continue
        rows = section.get("case_rows")
        if not isinstance(rows, list) or not rows:
            failures.append(f"JOINT_{split}_FACTORIAL_CASE_ROWS_REQUIRED")
            continue
        for index, raw in enumerate(rows):
            prefix = f"JOINT_{split}_FACTORIAL_ROW_{index}"
            if not isinstance(raw, dict):
                failures.append(f"{prefix}_OBJECT_REQUIRED")
                continue
            case_id = raw.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                failures.append(f"{prefix}_CASE_ID_REQUIRED")
                continue
            key = (split, case_id)
            if key in out:
                failures.append(f"{prefix}_DUPLICATE_CASE_ID")
                continue
            normalized = {field: raw.get(field) for field in COMMON_FIELDS}
            if normalized["split_family_id"] != section.get("family_id"):
                failures.append(f"{prefix}_SPLIT_FAMILY_ID_MISMATCH")
            receipts = _normalized_receipts(raw.get("control_runtime_receipts"), prefix, failures)
            normalized["control_runtime_receipts"] = receipts
            out[key] = normalized
    return out


def _attestation_rows(candidate: dict[str, Any], failures: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    att = candidate.get("semantic_factorial_attestation")
    if not isinstance(att, dict):
        failures.append("JOINT_SEMANTIC_FACTORIAL_ATTESTATION_REQUIRED")
        return {}
    rows = att.get("rows")
    if not isinstance(rows, list) or not rows:
        failures.append("JOINT_SEMANTIC_FACTORIAL_ATTESTATION_ROWS_REQUIRED")
        return {}

    out: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw in enumerate(rows):
        prefix = f"JOINT_PREREG_ROW_{index}"
        if not isinstance(raw, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        split = str(raw.get("split") or "").strip().upper()
        case_id = raw.get("case_id")
        if split not in SPLITS:
            failures.append(f"{prefix}_SPLIT_INVALID")
            continue
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{prefix}_CASE_ID_REQUIRED")
            continue
        key = (split, case_id)
        if key in out:
            failures.append(f"{prefix}_DUPLICATE_CASE_ID")
            continue
        normalized = {field: raw.get(field) for field in COMMON_FIELDS}
        receipts = _normalized_receipts(raw.get("control_runtime_receipts"), prefix, failures)
        normalized["control_runtime_receipts"] = receipts
        out[key] = normalized
    return out


def bind_joint_case_universe(candidate: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    factorial_rows = _factorial_rows(candidate, failures)
    prereg_rows = _attestation_rows(candidate, failures)

    factorial_keys = set(factorial_rows)
    prereg_keys = set(prereg_rows)
    if factorial_keys != prereg_keys:
        missing_from_prereg = sorted(factorial_keys - prereg_keys)
        missing_from_factorial = sorted(prereg_keys - factorial_keys)
        if missing_from_prereg:
            failures.append("JOINT_CASES_MISSING_FROM_PREREG_ATTESTATION")
        if missing_from_factorial:
            failures.append("JOINT_CASES_MISSING_FROM_FACTORIAL_EVIDENCE")

    joint_rows: list[dict[str, Any]] = []
    for key in sorted(factorial_keys & prereg_keys):
        frow = factorial_rows[key]
        prow = prereg_rows[key]
        split, case_id = key
        for field in COMMON_FIELDS:
            if frow.get(field) != prow.get(field):
                failures.append(f"JOINT_CASE_FIELD_MISMATCH:{split}:{case_id}:{field}")
        if frow.get("control_runtime_receipts") != prow.get("control_runtime_receipts"):
            failures.append(f"JOINT_CONTROL_RUNTIME_RECEIPTS_MISMATCH:{split}:{case_id}")
        joint_rows.append(
            {
                "split": split,
                **{field: frow.get(field) for field in COMMON_FIELDS},
                "control_runtime_receipts": frow.get("control_runtime_receipts"),
            }
        )

    for split in SPLITS:
        split_rows = [row for row in joint_rows if row["split"] == split]
        if len(split_rows) != 9:
            failures.append(f"JOINT_{split}_EXACTLY_NINE_CASES_REQUIRED")
        observed = {
            (str(row.get("semantic_target")), str(row.get("output_code_identity")))
            for row in split_rows
        }
        expected = {
            (target, code)
            for target in factorial.TARGETS
            for code in factorial.CODES
        }
        if observed != expected:
            failures.append(f"JOINT_{split}_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED")

    material = {
        "schema": JOINT_BINDING_SCHEMA,
        "common_fields": list(COMMON_FIELDS),
        "required_controls": list(factorial.REQUIRED_CONTROLS),
        "rows": sorted(
            joint_rows,
            key=lambda row: (row["split"], row["case_id"]),
        ),
    }
    return {
        "schema": JOINT_BINDING_SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "joint_case_count": len(joint_rows),
        "joint_case_universe_sha256": _canonical_sha(material),
        "binding_material": material,
        "runtime_credit_minted": False,
        "canonical_semantics_promotion": False,
    }


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v8.adjudicate(candidate)
    joint = bind_joint_case_universe(candidate)
    joint_ok = joint.get("pass") is True

    scientific = bool(
        base.get("scientifically_independent_vector_candidate") is True and joint_ok
    )
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and joint_ok)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and joint_ok)
    failures = sorted(
        set(list(base.get("v8_failures", [])) + list(joint.get("failures", [])))
    )

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "joint_case_universe_binding_pass": joint_ok,
        "joint_case_universe_sha256": joint.get("joint_case_universe_sha256"),
        "joint_case_universe_failures": list(joint.get("failures", [])),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "v9_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v9 composes v8 and additionally proves that the preregistration-facing case "
            "attestation and the v7 factorial runtime evidence are the same case/control "
            "universe. Independent green universes cannot be combined. This adjudicator "
            "is non-minting and does not authenticate external runtime receipt bytes by itself."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "joint_case_universe_binding_pass": False,
            "canonical_credit_minted": False,
            "v9_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "joint_case_universe_binding_pass": False,
            "canonical_credit_minted": False,
            "v9_failures": ["CANDIDATE_OBJECT_REQUIRED"],
        }
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    positive = [
        row for row in verdicts
        if row.get("owner_trigger1_goal_credit_candidate") is True
        and row.get("modular_hcu_jspace_control_candidate") is True
        and row.get("joint_case_universe_binding_pass") is True
    ]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "fully_joint_positive_candidate_files": len(positive),
        "owner_trigger1_goal_credit_candidate": bool(positive),
        "modular_hcu_jspace_control_candidate": bool(positive),
        "joint_case_universe_binding_pass": bool(positive),
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = parser.parse_args()
    result = (
        adjudicate_file(Path(args.candidate))
        if args.candidate
        else scan_batch(Path(args.batch_dir))
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
