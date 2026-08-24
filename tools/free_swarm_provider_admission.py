#!/usr/bin/env python3
"""Typed FREE_ONLY provider admission gate for the EntityOS/HCU free swarm.

This module is deliberately evaluated before provider credential lookup and before
provider network I/O. Environment attestation flags are compatibility metadata only;
they never create provider admission.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, TypeVar

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ENTITYOS_HCU_PROVIDER_ADMISSION/v1"
MODE = "FREE_ONLY"
SOURCE = "ENTITYOS_HCU_CONTROL_PLANE"
COST_CLASSES = frozenset({"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"})
DEFAULT_ADMISSION_PATH = Path("/artifacts/clay-entityos-control/FREE_SWARM_PROVIDER_ADMISSION.json")
DEFAULT_SUPERVISOR_PATH = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
RUNTIME_ADMISSION_ROOTS = (
    Path("/artifacts/clay-entityos-control"),
    ROOT / "research_entity/runtime/admissions",
)
MAX_ADMISSION_BYTES = 64 * 1024
MAX_SUPERVISOR_BYTES = 512 * 1024
_PROVIDER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
T = TypeVar("T")


class AdmissionError(RuntimeError):
    """Fail-closed provider-admission rejection."""


@dataclasses.dataclass(frozen=True)
class ProviderAdmission:
    provider: str
    cost_class: str
    admitted: bool
    evidence_ref: str


@dataclasses.dataclass(frozen=True)
class AdmissionSnapshot:
    admission_id: str
    authority_epoch: str
    issued_at: dt.datetime
    valid_until: dt.datetime
    source_path: str
    source_sha256: str
    supervisor_sha256: str
    providers: dict[str, ProviderAdmission]

    def provider(self, name: str) -> ProviderAdmission:
        row = self.providers.get(name)
        if row is None:
            raise AdmissionError(f"provider_not_admitted:{name}")
        return row


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_utc(value: Any, field: str) -> dt.datetime:
    if type(value) is not str or not value or len(value) > 64:
        raise AdmissionError(f"invalid_{field}")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdmissionError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise AdmissionError(f"invalid_{field}_timezone")
    return parsed.astimezone(dt.timezone.utc)


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise AdmissionError(f"duplicate_json_name:{key}")
        out[key] = value
    return out


def _read_bytes(path: Path, limit: int, label: str) -> bytes:
    try:
        with path.open("rb") as fh:
            data = fh.read(limit + 1)
    except OSError as exc:
        raise AdmissionError(f"{label}_unavailable") from exc
    if len(data) > limit:
        raise AdmissionError(f"{label}_too_large")
    return data


def _load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdmissionError(f"{label}_invalid_json") from exc
    if type(value) is not dict:
        raise AdmissionError(f"{label}_not_object")
    return value


def load_supervisor_epoch(path: Path = DEFAULT_SUPERVISOR_PATH) -> tuple[str, str]:
    data = _read_bytes(path, MAX_SUPERVISOR_BYTES, "supervisor")
    obj = _load_json_bytes(data, "supervisor")
    epoch = obj.get("schema_version")
    if type(epoch) is not str or not epoch:
        raise AdmissionError("supervisor_epoch_missing")
    free_only = obj.get("free_only")
    if type(free_only) is not dict or free_only.get("enabled") is not True:
        raise AdmissionError("supervisor_free_only_not_enabled")
    if free_only.get("provider_execution_requires_typed_explicit_free_classification") is not True:
        raise AdmissionError("supervisor_typed_free_admission_not_required")
    if free_only.get("admission_boundary") != "BEFORE_SECRET_OR_KEY_LOOKUP_AND_BEFORE_NETWORK_IO":
        raise AdmissionError("supervisor_admission_boundary_mismatch")
    return epoch, hashlib.sha256(data).hexdigest()


def _validate_closed_keys(obj: dict[str, Any], expected: set[str], label: str) -> None:
    if set(obj) != expected:
        raise AdmissionError(f"{label}_schema_keys_mismatch")


def load_admission(
    path: Path,
    *,
    supervisor_path: Path = DEFAULT_SUPERVISOR_PATH,
    now: dt.datetime | None = None,
) -> AdmissionSnapshot:
    current_epoch, supervisor_sha256 = load_supervisor_epoch(supervisor_path)
    data = _read_bytes(path, MAX_ADMISSION_BYTES, "admission")
    obj = _load_json_bytes(data, "admission")
    _validate_closed_keys(
        obj,
        {"schema", "admission_id", "authority_epoch", "mode", "source", "issued_at", "valid_until", "providers"},
        "admission",
    )
    if obj.get("schema") != SCHEMA:
        raise AdmissionError("admission_schema_mismatch")
    if obj.get("mode") != MODE:
        raise AdmissionError("admission_mode_mismatch")
    if obj.get("source") != SOURCE:
        raise AdmissionError("admission_source_mismatch")
    admission_id = obj.get("admission_id")
    if type(admission_id) is not str or not (1 <= len(admission_id) <= 160):
        raise AdmissionError("admission_id_invalid")
    authority_epoch = obj.get("authority_epoch")
    if type(authority_epoch) is not str or authority_epoch != current_epoch:
        raise AdmissionError("admission_authority_epoch_stale_or_mismatched")
    issued_at = _parse_utc(obj.get("issued_at"), "issued_at")
    valid_until = _parse_utc(obj.get("valid_until"), "valid_until")
    if valid_until <= issued_at:
        raise AdmissionError("admission_invalid_validity_window")
    instant = (now or _utc_now()).astimezone(dt.timezone.utc)
    if instant < issued_at:
        raise AdmissionError("admission_not_yet_valid")
    if instant >= valid_until:
        raise AdmissionError("admission_expired")
    providers_obj = obj.get("providers")
    if type(providers_obj) is not dict:
        raise AdmissionError("admission_providers_not_object")
    providers: dict[str, ProviderAdmission] = {}
    for provider, raw in providers_obj.items():
        if type(provider) is not str or not _PROVIDER_RE.fullmatch(provider):
            raise AdmissionError("provider_name_invalid")
        if type(raw) is not dict:
            raise AdmissionError(f"provider_row_not_object:{provider}")
        _validate_closed_keys(raw, {"cost_class", "admitted", "evidence_ref"}, f"provider:{provider}")
        cost_class = raw.get("cost_class")
        admitted = raw.get("admitted")
        evidence_ref = raw.get("evidence_ref")
        if type(cost_class) is not str or cost_class not in COST_CLASSES:
            raise AdmissionError(f"provider_cost_class_invalid:{provider}")
        if type(admitted) is not bool:
            raise AdmissionError(f"provider_admitted_not_boolean:{provider}")
        if type(evidence_ref) is not str or not (1 <= len(evidence_ref) <= 512):
            raise AdmissionError(f"provider_evidence_ref_invalid:{provider}")
        if cost_class != "FREE" and admitted:
            raise AdmissionError(f"nonfree_provider_cannot_be_admitted:{provider}")
        providers[provider] = ProviderAdmission(provider, cost_class, admitted, evidence_ref)
    return AdmissionSnapshot(
        admission_id=admission_id,
        authority_epoch=authority_epoch,
        issued_at=issued_at,
        valid_until=valid_until,
        source_path=str(path),
        source_sha256=hashlib.sha256(data).hexdigest(),
        supervisor_sha256=supervisor_sha256,
        providers=providers,
    )


def resolve_runtime_admission_path() -> Path:
    raw = os.getenv("CLAY_PROVIDER_ADMISSION_FILE", "").strip()
    candidate = Path(raw) if raw else DEFAULT_ADMISSION_PATH
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        raise AdmissionError("admission_path_invalid") from exc
    for root in RUNTIME_ADMISSION_ROOTS:
        root_resolved = root.resolve(strict=False)
        if resolved == root_resolved or root_resolved in resolved.parents:
            return resolved
    raise AdmissionError("admission_path_outside_control_plane_roots")


def load_runtime_admission(*, supervisor_path: Path = DEFAULT_SUPERVISOR_PATH) -> AdmissionSnapshot:
    return load_admission(resolve_runtime_admission_path(), supervisor_path=supervisor_path)


def require_free_provider(
    snapshot: AdmissionSnapshot,
    provider: str,
    *,
    supervisor_path: Path = DEFAULT_SUPERVISOR_PATH,
    now: dt.datetime | None = None,
) -> ProviderAdmission:
    current_epoch, current_supervisor_sha256 = load_supervisor_epoch(supervisor_path)
    if current_epoch != snapshot.authority_epoch or current_supervisor_sha256 != snapshot.supervisor_sha256:
        raise AdmissionError("provider_admission_supervisor_changed")
    instant = (now or _utc_now()).astimezone(dt.timezone.utc)
    if instant < snapshot.issued_at or instant >= snapshot.valid_until:
        raise AdmissionError("provider_admission_not_current")
    row = snapshot.provider(provider)
    if row.cost_class != "FREE" or row.admitted is not True:
        raise AdmissionError(f"provider_not_explicit_free:{provider}:{row.cost_class}")
    return row


def with_provider_permit(
    snapshot: AdmissionSnapshot,
    provider: str,
    operation: Callable[[ProviderAdmission], T],
    *,
    supervisor_path: Path = DEFAULT_SUPERVISOR_PATH,
) -> T:
    permit = require_free_provider(snapshot, provider, supervisor_path=supervisor_path)
    return operation(permit)


def admitted_provider_names(
    snapshot: AdmissionSnapshot,
    *,
    supervisor_path: Path = DEFAULT_SUPERVISOR_PATH,
) -> list[str]:
    names: list[str] = []
    for provider in sorted(snapshot.providers):
        try:
            require_free_provider(snapshot, provider, supervisor_path=supervisor_path)
        except AdmissionError:
            continue
        names.append(provider)
    return names


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate typed EntityOS/HCU FREE_ONLY provider admission")
    sub = parser.add_subparsers(dest="command", required=True)
    runtime = sub.add_parser("runtime-admitted-providers")
    runtime.add_argument("--json", action="store_true")
    check = sub.add_parser("check")
    check.add_argument("--admission-file", required=True)
    check.add_argument("--supervisor-file", required=True)
    check.add_argument("--provider", default="")
    args = parser.parse_args(argv)
    try:
        if args.command == "runtime-admitted-providers":
            snapshot = load_runtime_admission()
            names = admitted_provider_names(snapshot)
            if not names:
                return 4
            if args.json:
                print(json.dumps({
                    "schema": SCHEMA,
                    "admission_id": snapshot.admission_id,
                    "authority_epoch": snapshot.authority_epoch,
                    "admitted_providers": names,
                    "source_sha256": snapshot.source_sha256,
                }, sort_keys=True))
            else:
                print("\n".join(names))
            return 0
        snapshot = load_admission(Path(args.admission_file), supervisor_path=Path(args.supervisor_file))
        if args.provider:
            require_free_provider(snapshot, args.provider, supervisor_path=Path(args.supervisor_file))
        print(json.dumps({"status": "PASS", "admission_id": snapshot.admission_id}, sort_keys=True))
        return 0
    except AdmissionError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 5


if __name__ == "__main__":
    raise SystemExit(_cli())
