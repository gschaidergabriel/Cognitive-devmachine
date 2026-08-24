#!/usr/bin/env python3
"""Typed FREE_ONLY provider admission resolved before secrets or provider network I/O.

This module intentionally reads only canonical repository control-plane files. It does
not inspect API-key environment variables, provider responses, billing endpoints, or
credential files. Those surfaces are downstream of admission.

Authority is successor-dynamic: the current checkout's newest committed
SUPERVISOR_STEERING_<major>_<minor>.json controls the admission epoch. A stale
bootstrap or inbox cannot keep provider traffic enabled after a newer supervisor lands.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADMISSION_PATH = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
SUPERVISOR_DIR = ROOT / "research_entity/claycode/autonomous"
SCHEMA = "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"
ALLOWED_PROVIDERS = frozenset({"groq", "mistral", "nvidia", "openrouter"})
SUPERVISOR_NAME_RE = re.compile(r"^SUPERVISOR_STEERING_(\d+)_(\d+)\.json$")
LOWER_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FREE_EVIDENCE_CLAIM = "ZERO_MONETARY_COST_NO_OVERAGE_FOR_BOUND_EXECUTION_CLASS"


class ProviderAdmissionError(RuntimeError):
    pass


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderAdmissionError(f"{label}_UNAVAILABLE_OR_INVALID:{exc.__class__.__name__}") from exc
    if not isinstance(payload, dict):
        raise ProviderAdmissionError(f"{label}_OBJECT_REQUIRED")
    return payload


def _steering_ref(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve())).replace("\\", "/")
    except ValueError:
        # Test fixtures may live outside the repository. This is deterministic test
        # identity only and is never used as production canonical provenance.
        return path.name


def resolve_current_supervisor(
    *,
    supervisor_dir: Path | None = None,
    root: Path | None = None,
) -> tuple[str, str]:
    """Resolve the newest supervisor file from the current checkout and verify it.

    Ordering comes from filenames before reading contents. A malformed newer steering
    file is therefore fail-closed rather than silently skipped in favor of an older one.
    """
    repo_root = (root or ROOT).resolve()
    directory = supervisor_dir or (repo_root / "research_entity/claycode/autonomous")
    try:
        paths = list(directory.iterdir())
    except OSError as exc:
        raise ProviderAdmissionError(f"SUPERVISOR_DIR_UNAVAILABLE:{exc.__class__.__name__}") from exc

    candidates: list[tuple[tuple[int, int], Path]] = []
    for path in paths:
        match = SUPERVISOR_NAME_RE.fullmatch(path.name)
        if match:
            candidates.append(((int(match.group(1)), int(match.group(2))), path))
    if not candidates:
        raise ProviderAdmissionError("SUPERVISOR_STEERING_NOT_FOUND")

    newest_version = max(version for version, _ in candidates)
    newest = [path for version, path in candidates if version == newest_version]
    if len(newest) != 1:
        raise ProviderAdmissionError("SUPERVISOR_STEERING_VERSION_AMBIGUOUS")

    path = newest[0]
    steering = _read_json(path, "SUPERVISOR_STEERING")
    epoch = f"{newest_version[0]}.{newest_version[1]}"
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise ProviderAdmissionError("SUPERVISOR_STEERING_FILENAME_EPOCH_MISMATCH")
    if steering.get("active_program") != "ENTITYOS_HCU":
        raise ProviderAdmissionError("SUPERVISOR_STEERING_PROGRAM_AUTHORITY_MISMATCH")
    if steering.get("product") != "EntityOS":
        raise ProviderAdmissionError("SUPERVISOR_STEERING_PRODUCT_AUTHORITY_MISMATCH")
    if steering.get("integrated_cognition_compute_architecture") != "HCU":
        raise ProviderAdmissionError("SUPERVISOR_STEERING_COMPUTE_AUTHORITY_MISMATCH")
    return epoch, _steering_ref(path, repo_root)


def _validate_free_evidence(provider: str, record: dict[str, Any]) -> None:
    evidence = record.get("free_evidence")
    if not isinstance(evidence, dict):
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_EVIDENCE_OBJECT_REQUIRED:{provider}")
    if evidence.get("claim") != FREE_EVIDENCE_CLAIM:
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_EVIDENCE_CLAIM_INVALID:{provider}")
    if evidence.get("provider") != provider:
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_EVIDENCE_PROVIDER_MISMATCH:{provider}")
    execution_class = evidence.get("execution_class")
    if not isinstance(execution_class, str) or not execution_class.strip():
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_EXECUTION_CLASS_REQUIRED:{provider}")
    checked_at = evidence.get("checked_at")
    if not isinstance(checked_at, str) or not checked_at.strip():
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_CHECKED_AT_REQUIRED:{provider}")
    evidence_ref = evidence.get("evidence_ref")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_EVIDENCE_REF_REQUIRED:{provider}")
    if evidence_ref != record.get("evidence_ref"):
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_EVIDENCE_REF_MISMATCH:{provider}")
    digest = evidence.get("evidence_sha256")
    if not isinstance(digest, str) or not LOWER_SHA256_RE.fullmatch(digest):
        raise ProviderAdmissionError(f"PROVIDER_ADMISSION_FREE_EVIDENCE_SHA256_REQUIRED:{provider}")


def validate_provider_admission(
    payload: dict[str, Any],
    *,
    supervisor_dir: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    epoch, steering_ref = resolve_current_supervisor(supervisor_dir=supervisor_dir, root=root)

    if payload.get("schema") != SCHEMA:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_SCHEMA_UNSUPPORTED")
    if payload.get("mode") != "FREE_ONLY":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_MODE_NOT_FREE_ONLY")
    if payload.get("product") != "EntityOS" or payload.get("compute_architecture") != "HCU":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_PRODUCT_AUTHORITY_MISMATCH")
    if payload.get("source") != "ENTITYOS_HCU_CONTROL_PLANE":
        raise ProviderAdmissionError("PROVIDER_ADMISSION_CONTROL_PLANE_SOURCE_REQUIRED")

    admission_epoch = str(payload.get("authority_epoch") or "").strip()
    if not admission_epoch or admission_epoch != epoch:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_AUTHORITY_EPOCH_MISMATCH")
    admission_steering = str(payload.get("supervisor_steering") or "").strip()
    if not admission_steering or admission_steering != steering_ref:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_SUPERVISOR_STEERING_MISMATCH")

    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ProviderAdmissionError("PROVIDER_ADMISSION_PROVIDERS_OBJECT_REQUIRED")
    unknown_names = set(providers) - ALLOWED_PROVIDERS
    if unknown_names:
        raise ProviderAdmissionError("PROVIDER_ADMISSION_UNKNOWN_PROVIDER")

    for name in ALLOWED_PROVIDERS:
        record = providers.get(name)
        if not isinstance(record, dict):
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_RECORD_REQUIRED:{name}")
        cost_class = record.get("cost_class")
        if cost_class not in {"FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}:
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_COST_CLASS_INVALID:{name}")
        if not isinstance(record.get("admitted"), bool):
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_BOOLEAN_REQUIRED:{name}")
        if record.get("admitted") is True and cost_class != "FREE":
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_NONFREE_CANNOT_BE_ADMITTED:{name}")
        evidence_ref = record.get("evidence_ref")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise ProviderAdmissionError(f"PROVIDER_ADMISSION_EVIDENCE_REQUIRED:{name}")
        if cost_class == "FREE":
            _validate_free_evidence(name, record)
    return payload


def load_provider_admission(
    path: Path | None = None,
    *,
    supervisor_dir: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Load canonical admission without touching any provider secret or network surface."""
    repo_root = (root or ROOT).resolve()
    target = path or (repo_root / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")
    payload = _read_json(target, "PROVIDER_ADMISSION")
    return validate_provider_admission(payload, supervisor_dir=supervisor_dir, root=repo_root)


def provider_is_admitted_free(
    provider: str,
    admission: dict[str, Any] | None = None,
    *,
    supervisor_dir: Path | None = None,
    root: Path | None = None,
) -> bool:
    provider = str(provider).strip().lower()
    if provider not in ALLOWED_PROVIDERS:
        return False
    try:
        payload = (
            load_provider_admission(supervisor_dir=supervisor_dir, root=root)
            if admission is None
            else validate_provider_admission(admission, supervisor_dir=supervisor_dir, root=root)
        )
        record = payload["providers"][provider]
    except (ProviderAdmissionError, KeyError, TypeError):
        return False
    return record.get("admitted") is True and record.get("cost_class") == "FREE"


def require_provider_admitted_free(
    provider: str,
    admission: dict[str, Any] | None = None,
    *,
    supervisor_dir: Path | None = None,
    root: Path | None = None,
) -> None:
    provider = str(provider).strip().lower()
    if not provider_is_admitted_free(
        provider, admission, supervisor_dir=supervisor_dir, root=root
    ):
        raise ProviderAdmissionError(f"PROVIDER_NOT_CANONICALLY_ADMITTED_FREE:{provider or 'EMPTY'}")


def admitted_provider_names(
    admission: dict[str, Any] | None = None,
    *,
    supervisor_dir: Path | None = None,
    root: Path | None = None,
) -> tuple[str, ...]:
    try:
        payload = (
            load_provider_admission(supervisor_dir=supervisor_dir, root=root)
            if admission is None
            else validate_provider_admission(admission, supervisor_dir=supervisor_dir, root=root)
        )
    except ProviderAdmissionError:
        return ()
    return tuple(
        sorted(
            name
            for name in ALLOWED_PROVIDERS
            if payload["providers"][name].get("admitted") is True
            and payload["providers"][name].get("cost_class") == "FREE"
        )
    )


def admission_snapshot() -> dict[str, Any]:
    try:
        epoch, steering_ref = resolve_current_supervisor()
        payload = load_provider_admission()
    except ProviderAdmissionError as exc:
        return {
            "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1",
            "ok": False,
            "admitted_free_providers": [],
            "status": str(exc),
        }
    return {
        "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1",
        "ok": True,
        "authority_epoch": epoch,
        "steering": steering_ref,
        "admitted_free_providers": list(admitted_provider_names(payload)),
        "providers": {
            name: {
                "admitted": bool(payload["providers"][name]["admitted"]),
                "cost_class": payload["providers"][name]["cost_class"],
                "evidence_ref": payload["providers"][name]["evidence_ref"],
            }
            for name in sorted(ALLOWED_PROVIDERS)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read canonical EntityOS/HCU FREE provider admission")
    parser.add_argument("--provider", choices=sorted(ALLOWED_PROVIDERS))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    snapshot = admission_snapshot()
    if args.json or not args.provider:
        print(json.dumps(snapshot, sort_keys=True, separators=(",", ":")))
    if args.provider:
        if not snapshot.get("ok"):
            return 4
        return 0 if args.provider in snapshot.get("admitted_free_providers", []) else 3
    return 0 if snapshot.get("ok") else 4


if __name__ == "__main__":
    raise SystemExit(main())
