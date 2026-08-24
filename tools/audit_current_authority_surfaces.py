#!/usr/bin/env python3
"""Successor-dynamic audit for current-facing Clay authority surfaces.

The expected authority epoch is resolved from SUPERVISOR_INBOX -> steering, not from
constants in the validator or from the surfaces being checked. This makes stale,
self-consistent islands visible without granting this diagnostic any authority of its own.

The tool is read-only. By default it emits a JSON report and exits 0 even when drift is
present. Pass --strict to exit non-zero when any current-facing surface is stale or
malformed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

INBOX_REL = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
BOOTSTRAP_REL = Path("research_entity/continuity/BOOTSTRAP_MINIMAL.json")
PROGRAM_REL = Path("research_entity/rooms/PROGRAM_STATE.json")
MANIFEST_REL = Path("the artefact/manifest.json")
README_REL = Path("the artefact/README.md")


class AuthorityAuditError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuthorityAuditError(f"MISSING_FILE:{path}") from exc
    except json.JSONDecodeError as exc:
        raise AuthorityAuditError(f"MALFORMED_JSON:{path}:{exc.msg}") from exc
    if not isinstance(value, dict):
        raise AuthorityAuditError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _epoch_suffix(epoch: str) -> str:
    return epoch.replace(".", "_")


def resolve_current_authority(root: Path) -> dict[str, str]:
    inbox = _load_json(root / INBOX_REL)
    steering_rel_raw = inbox.get("steering")
    if not isinstance(steering_rel_raw, str) or not steering_rel_raw.strip():
        raise AuthorityAuditError("SUPERVISOR_INBOX_STEERING_POINTER_REQUIRED")
    steering_rel = Path(steering_rel_raw)
    steering = _load_json(root / steering_rel)
    epoch_raw = steering.get("schema_version")
    if not isinstance(epoch_raw, (str, int, float)):
        raise AuthorityAuditError("SUPERVISOR_STEERING_SCHEMA_VERSION_REQUIRED")
    epoch = str(epoch_raw)

    owner = ""
    execution = inbox.get("execution_authority")
    if isinstance(execution, dict):
        candidate = execution.get("active_owner_authority")
        if isinstance(candidate, str):
            owner = candidate
    if not owner:
        candidate = steering.get("active_owner_authority")
        if isinstance(candidate, str):
            owner = candidate

    return {
        "epoch": epoch,
        "steering": steering_rel.as_posix(),
        "directive": (
            "research_entity/claycode/"
            f"CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_{_epoch_suffix(epoch)}.md"
        ),
        "owner_authority": owner,
    }


def _add_mismatch(
    mismatches: list[dict[str, Any]],
    *,
    surface: str,
    field: str,
    expected: Any,
    observed: Any,
) -> None:
    if observed != expected:
        mismatches.append(
            {
                "surface": surface,
                "field": field,
                "expected": expected,
                "observed": observed,
            }
        )


def audit(root: Path) -> dict[str, Any]:
    expected = resolve_current_authority(root)
    mismatches: list[dict[str, Any]] = []
    errors: list[str] = []

    def json_surface(name: str, rel: Path) -> dict[str, Any] | None:
        try:
            return _load_json(root / rel)
        except AuthorityAuditError as exc:
            errors.append(f"{name}:{exc}")
            return None

    bootstrap = json_surface("BOOTSTRAP_MINIMAL", BOOTSTRAP_REL)
    if bootstrap is not None:
        _add_mismatch(
            mismatches,
            surface="BOOTSTRAP_MINIMAL",
            field="schema_version",
            expected=expected["epoch"],
            observed=str(bootstrap.get("schema_version")),
        )
        _add_mismatch(
            mismatches,
            surface="BOOTSTRAP_MINIMAL",
            field="authority_correction",
            expected=expected["steering"],
            observed=bootstrap.get("authority_correction"),
        )
        _add_mismatch(
            mismatches,
            surface="BOOTSTRAP_MINIMAL",
            field="all_worker_protocol",
            expected=expected["directive"],
            observed=bootstrap.get("all_worker_protocol"),
        )
        if expected["owner_authority"]:
            _add_mismatch(
                mismatches,
                surface="BOOTSTRAP_MINIMAL",
                field="active_owner_authority",
                expected=expected["owner_authority"],
                observed=bootstrap.get("active_owner_authority"),
            )

    program = json_surface("PROGRAM_STATE", PROGRAM_REL)
    if program is not None:
        _add_mismatch(
            mismatches,
            surface="PROGRAM_STATE",
            field="schema_version",
            expected=expected["epoch"],
            observed=str(program.get("schema_version")),
        )
        _add_mismatch(
            mismatches,
            surface="PROGRAM_STATE",
            field="authority_correction",
            expected=expected["steering"],
            observed=program.get("authority_correction"),
        )
        _add_mismatch(
            mismatches,
            surface="PROGRAM_STATE",
            field="all_worker_protocol",
            expected=expected["directive"],
            observed=program.get("all_worker_protocol"),
        )
        if expected["owner_authority"]:
            _add_mismatch(
                mismatches,
                surface="PROGRAM_STATE",
                field="active_owner_authority",
                expected=expected["owner_authority"],
                observed=program.get("active_owner_authority"),
            )

    manifest = json_surface("ARTIFACT_MANIFEST", MANIFEST_REL)
    if manifest is not None:
        _add_mismatch(
            mismatches,
            surface="ARTIFACT_MANIFEST",
            field="authority_correction",
            expected=expected["steering"],
            observed=manifest.get("authority_correction"),
        )
        execution_policy = manifest.get("execution_policy")
        if isinstance(execution_policy, dict):
            _add_mismatch(
                mismatches,
                surface="ARTIFACT_MANIFEST",
                field="execution_policy.active_supervisor_epoch",
                expected=expected["epoch"],
                observed=str(execution_policy.get("active_supervisor_epoch")),
            )
        else:
            errors.append("ARTIFACT_MANIFEST:execution_policy:OBJECT_REQUIRED")
        coordination = manifest.get("coordination_authority")
        if isinstance(coordination, dict) and "supervisor" in coordination:
            _add_mismatch(
                mismatches,
                surface="ARTIFACT_MANIFEST",
                field="coordination_authority.supervisor",
                expected=expected["epoch"],
                observed=str(coordination.get("supervisor")),
            )

    try:
        readme = (root / README_REL).read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"ARTIFACT_README:MISSING_FILE:{README_REL}")
    else:
        required_fragments = {
            "steering_pointer": expected["steering"].split("/")[-1],
            "worker_directive": expected["directive"].split("/")[-1],
            "epoch_statement": f"Current supervisor epoch: **{expected['epoch']}**",
        }
        for field, fragment in required_fragments.items():
            if fragment not in readme:
                mismatches.append(
                    {
                        "surface": "ARTIFACT_README",
                        "field": field,
                        "expected": fragment,
                        "observed": "MISSING",
                    }
                )
        if expected["owner_authority"] and expected["owner_authority"] not in readme:
            mismatches.append(
                {
                    "surface": "ARTIFACT_README",
                    "field": "owner_authority",
                    "expected": expected["owner_authority"],
                    "observed": "MISSING",
                }
            )

    return {
        "schema": "CLAY_CURRENT_AUTHORITY_SURFACE_AUDIT/v1",
        "authority_source": "SUPERVISOR_INBOX_TO_STEERING",
        "expected": expected,
        "status": "PASS" if not mismatches and not errors else "DRIFT",
        "mismatch_count": len(mismatches),
        "error_count": len(errors),
        "mismatches": mismatches,
        "errors": errors,
        "epistemic_scope": "READ_ONLY_CURRENT_FACING_ALIGNMENT_DIAGNOSTIC_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when drift/errors are found",
    )
    args = parser.parse_args()
    try:
        report = audit(args.root.resolve())
    except AuthorityAuditError as exc:
        report = {
            "schema": "CLAY_CURRENT_AUTHORITY_SURFACE_AUDIT/v1",
            "status": "ERROR",
            "errors": [str(exc)],
            "epistemic_scope": "READ_ONLY_CURRENT_FACING_ALIGNMENT_DIAGNOSTIC_ONLY",
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.strict and report.get("status") != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
