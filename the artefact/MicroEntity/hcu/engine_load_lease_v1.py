#!/usr/bin/env python3
"""Physical HCU engine-load lease over verified engine artifacts.

This module closes one specific gap between pre-load EngineAdmission and actual loader
inputs: source paths are copied into a content-addressed staged snapshot, re-digested with
the existing EngineAdmission digest function, and exposed to the loader only through the
lease object. Mutation of the original source paths after lease creation cannot change the
staged bytes.

This is not full loader attestation. Runtime acceptance must additionally enforce that the
real loader consumes only these lease paths (or an equivalent read-only boundary) and must
echo ``lease_id_sha256`` into the downstream inference receipt. A same-user-writable lease
root or a loader that ignores the lease remains untrusted and receives zero runtime credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from engine_admission_v1 import VerifiedEngineAdmission, digest_artifact_path

LEASE_SCHEMA = "HCU_PHYSICAL_ENGINE_LOAD_LEASE/v1"
LEASE_RECEIPT_SCHEMA = "HCU_PHYSICAL_ENGINE_LOAD_LEASE_RECEIPT/v1"
_ARTIFACT_KINDS = ("checkpoint", "tokenizer", "runtime", "build")


class EngineLoadLeaseError(ValueError):
    pass


@dataclass(frozen=True)
class PhysicalEngineLoadLease:
    entity_generation: int
    engine_identity: str
    engine_artifact_sha256: str
    engine_admission_receipt_sha256: str
    lease_id_sha256: str
    lease_root: Path
    checkpoint: Path
    tokenizer: Path
    runtime: Path
    build: Path
    checkpoint_sha256: str
    tokenizer_sha256: str
    runtime_sha256: str
    build_sha256: str

    def loader_paths(self) -> dict[str, Path]:
        return {kind: getattr(self, kind) for kind in _ARTIFACT_KINDS}

    def receipt(self) -> dict[str, Any]:
        return {
            "schema": LEASE_RECEIPT_SCHEMA,
            "entity_generation": self.entity_generation,
            "engine_identity": self.engine_identity,
            "engine_artifact_sha256": self.engine_artifact_sha256,
            "engine_admission_receipt_sha256": self.engine_admission_receipt_sha256,
            "lease_id_sha256": self.lease_id_sha256,
            "lease_subdir": self.lease_id_sha256,
            "artifacts": {
                kind: {
                    "relative_path": kind,
                    "sha256": getattr(self, f"{kind}_sha256"),
                }
                for kind in _ARTIFACT_KINDS
            },
            "runtime_credit": "ZERO_UNTIL_REAL_LOADER_CONSUMPTION_ECHO",
        }


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EngineLoadLeaseError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _sha(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise EngineLoadLeaseError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _assert_source_shape(path: Path) -> None:
    if not isinstance(path, Path):
        raise EngineLoadLeaseError("ARTIFACT_PATH_TYPE_REQUIRED")
    if path.is_symlink():
        raise EngineLoadLeaseError(f"ARTIFACT_SYMLINK_FORBIDDEN:{path}")
    if path.is_file():
        return
    if not path.is_dir():
        raise EngineLoadLeaseError(f"ARTIFACT_PATH_NOT_FOUND_OR_UNSUPPORTED:{path}")
    saw_file = False
    for root, dirs, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        for name in dirs:
            candidate = root_path / name
            if candidate.is_symlink():
                raise EngineLoadLeaseError(f"ARTIFACT_SYMLINK_FORBIDDEN:{candidate}")
        for name in files:
            candidate = root_path / name
            if candidate.is_symlink():
                raise EngineLoadLeaseError(f"ARTIFACT_SYMLINK_FORBIDDEN:{candidate}")
            if not candidate.is_file():
                raise EngineLoadLeaseError(f"ARTIFACT_REGULAR_FILE_REQUIRED:{candidate}")
            saw_file = True
    if not saw_file:
        raise EngineLoadLeaseError(f"ARTIFACT_TREE_EMPTY:{path}")


def _copy_artifact(source: Path, destination: Path) -> None:
    _assert_source_shape(source)
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
        return
    destination.mkdir(parents=True, exist_ok=False)
    for root, dirs, files in os.walk(source, followlinks=False):
        root_path = Path(root)
        rel_root = root_path.relative_to(source)
        dest_root = destination / rel_root
        for name in sorted(dirs):
            src_dir = root_path / name
            if src_dir.is_symlink():
                raise EngineLoadLeaseError(f"ARTIFACT_SYMLINK_FORBIDDEN:{src_dir}")
            (dest_root / name).mkdir(exist_ok=False)
        for name in sorted(files):
            src_file = root_path / name
            if src_file.is_symlink() or not src_file.is_file():
                raise EngineLoadLeaseError(f"ARTIFACT_REGULAR_FILE_REQUIRED:{src_file}")
            shutil.copyfile(src_file, dest_root / name, follow_symlinks=False)


def _make_read_only(path: Path) -> None:
    if path.is_file():
        path.chmod(0o444)
        return
    for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
        root_path = Path(root)
        for name in files:
            (root_path / name).chmod(0o444)
        for name in dirs:
            (root_path / name).chmod(0o555)
        root_path.chmod(0o555)


def _cleanup_temp_root(path: Path) -> None:
    if not path.exists():
        return
    for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
        root_path = Path(root)
        for name in files:
            try:
                (root_path / name).chmod(0o600)
            except OSError:
                pass
        for name in dirs:
            try:
                (root_path / name).chmod(0o700)
            except OSError:
                pass
        try:
            root_path.chmod(0o700)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


def _expected_digests(verified: VerifiedEngineAdmission) -> dict[str, str]:
    try:
        values = {
            kind: _sha(getattr(verified, kind).sha256, f"{kind}_sha256")
            for kind in _ARTIFACT_KINDS
        }
    except AttributeError as exc:
        raise EngineLoadLeaseError("VERIFIED_ENGINE_ADMISSION_SHAPE_REQUIRED") from exc
    return values


def _lease_material(
    verified: VerifiedEngineAdmission,
    digests: dict[str, str],
) -> dict[str, Any]:
    try:
        engine_identity = verified.admission.engine_identity
        artifact_sha = _sha(verified.engine_artifact_sha256, "engine_artifact_sha256")
        receipt_sha = _sha(
            verified.receipt_sha256,
            "engine_admission_receipt_sha256",
        )
    except AttributeError as exc:
        raise EngineLoadLeaseError("VERIFIED_ENGINE_ADMISSION_SHAPE_REQUIRED") from exc
    if not isinstance(engine_identity, str) or not engine_identity.strip():
        raise EngineLoadLeaseError("engine_identity:NONEMPTY_STRING_REQUIRED")
    return {
        "schema": LEASE_SCHEMA,
        "entity_generation": _generation(verified.entity_generation, "entity_generation"),
        "engine_identity": engine_identity.strip().lower(),
        "engine_artifact_sha256": artifact_sha,
        "engine_admission_receipt_sha256": receipt_sha,
        "artifacts": {kind: digests[kind] for kind in _ARTIFACT_KINDS},
    }


def _validate_snapshot(root: Path, expected: dict[str, str]) -> None:
    if root.is_symlink() or not root.is_dir():
        raise EngineLoadLeaseError("LEASE_ROOT_DIRECTORY_REQUIRED")
    for kind in _ARTIFACT_KINDS:
        observed = digest_artifact_path(root / kind).sha256
        if observed != expected[kind]:
            raise EngineLoadLeaseError(f"LEASE_{kind.upper()}_DIGEST_MISMATCH")


def stage_verified_engine_load_lease(
    verified: VerifiedEngineAdmission,
    source_paths: dict[str, Path],
    *,
    lease_root: Path,
    current_generation: int,
) -> PhysicalEngineLoadLease:
    current = _generation(current_generation, "current_generation")
    generation = _generation(
        getattr(verified, "entity_generation", None),
        "entity_generation",
    )
    if generation != current:
        raise EngineLoadLeaseError("STALE_ENTITY_GENERATION")
    if not isinstance(source_paths, dict) or set(source_paths) != set(_ARTIFACT_KINDS):
        raise EngineLoadLeaseError("EXACT_ENGINE_ARTIFACT_PATH_SET_REQUIRED")
    if not isinstance(lease_root, Path):
        raise EngineLoadLeaseError("LEASE_ROOT_PATH_TYPE_REQUIRED")
    if lease_root.is_symlink():
        raise EngineLoadLeaseError("LEASE_ROOT_SYMLINK_FORBIDDEN")
    lease_root.mkdir(parents=True, exist_ok=True)
    if not lease_root.is_dir():
        raise EngineLoadLeaseError("LEASE_ROOT_DIRECTORY_REQUIRED")

    expected = _expected_digests(verified)
    for kind in _ARTIFACT_KINDS:
        source = source_paths[kind]
        _assert_source_shape(source)
        observed = digest_artifact_path(source).sha256
        if observed != expected[kind]:
            raise EngineLoadLeaseError(f"SOURCE_{kind.upper()}_DIGEST_MISMATCH")

    material = _lease_material(verified, expected)
    lease_id = hashlib.sha256(_canonical(material)).hexdigest()
    final_root = lease_root / lease_id
    if final_root.exists():
        _validate_snapshot(final_root, expected)
    else:
        temp_root = Path(
            tempfile.mkdtemp(prefix=f".{lease_id}.tmp-", dir=lease_root)
        )
        try:
            for kind in _ARTIFACT_KINDS:
                _copy_artifact(source_paths[kind], temp_root / kind)
            _validate_snapshot(temp_root, expected)
            for kind in _ARTIFACT_KINDS:
                _make_read_only(temp_root / kind)
            try:
                temp_root.rename(final_root)
            except OSError:
                if final_root.exists():
                    _validate_snapshot(final_root, expected)
                else:
                    raise
            if temp_root.exists():
                _cleanup_temp_root(temp_root)
        except Exception:
            _cleanup_temp_root(temp_root)
            raise

    _validate_snapshot(final_root, expected)
    return PhysicalEngineLoadLease(
        entity_generation=generation,
        engine_identity=material["engine_identity"],
        engine_artifact_sha256=material["engine_artifact_sha256"],
        engine_admission_receipt_sha256=material["engine_admission_receipt_sha256"],
        lease_id_sha256=lease_id,
        lease_root=final_root,
        checkpoint=final_root / "checkpoint",
        tokenizer=final_root / "tokenizer",
        runtime=final_root / "runtime",
        build=final_root / "build",
        checkpoint_sha256=expected["checkpoint"],
        tokenizer_sha256=expected["tokenizer"],
        runtime_sha256=expected["runtime"],
        build_sha256=expected["build"],
    )


def assert_engine_load_lease_unchanged(
    lease: PhysicalEngineLoadLease,
    *,
    current_generation: int,
) -> None:
    if not isinstance(lease, PhysicalEngineLoadLease):
        raise EngineLoadLeaseError("PHYSICAL_ENGINE_LOAD_LEASE_TYPE_REQUIRED")
    current = _generation(current_generation, "current_generation")
    if lease.entity_generation != current:
        raise EngineLoadLeaseError("STALE_ENTITY_GENERATION")
    expected = {
        kind: getattr(lease, f"{kind}_sha256")
        for kind in _ARTIFACT_KINDS
    }
    _validate_snapshot(lease.lease_root, expected)
