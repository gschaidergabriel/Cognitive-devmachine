#!/usr/bin/env python3
"""Kernel-sealed loader-consumption witness for HCU engine-load evidence.

This module is a producer-side evidence primitive, not authority. It closes one
specific gap in engine_load_lease_v1: a string label cannot prove that a loader
received the exact admitted bytes. The witness constructs an anonymous Linux
memfd, writes one artifact payload, applies irreversible write/grow/shrink/seal
seals, and exposes either the exact read-back bytes or the still-sealed memfd to
one bound loader callback.

The fd/path callback exists for real loaders that require a file descriptor or
filesystem path (for example mmap/file based model loaders) and avoids copying
verified bytes into an uncontrolled temporary file. The /proc/self/fd path is
valid only for the synchronous callback lifetime; deferred/lazy work after the
callback returns is not witnessed by this primitive.

A successful witness proves only this adapter supplied the exact sealed bytes or
sealed fd-backed object to that callable and observed unchanged kernel seals. It
does not by itself prove that opaque loader code read every byte, establish model
behavior, full checkpoint coverage, inference correctness, canonical truth, or
training benefit. Positive runtime credit still requires a separately bound
loader implementation plus downstream canonical loader-consumption admission and
model-execution evidence. Unsupported platforms fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import errno
import fcntl
import hashlib
import os
from typing import Any, Callable, Generic, TypeVar

WITNESS_SCHEMA = "HCU_LOADER_CONSUMPTION_WITNESS/v1"
BYTES_CALLBACK_EVIDENCE_CLASS = "SEALED_MEMFD_EXACT_BYTES_CALLBACK/v1"
FD_PATH_EVIDENCE_CLASS = "SEALED_MEMFD_EXACT_FD_PATH_CALLBACK/v1"
# Compatibility alias retained for existing callers/tests.
EVIDENCE_CLASS = BYTES_CALLBACK_EVIDENCE_CLASS
_REQUIRED_SEALS = (
    fcntl.F_SEAL_WRITE
    | fcntl.F_SEAL_GROW
    | fcntl.F_SEAL_SHRINK
    | fcntl.F_SEAL_SEAL
)
T = TypeVar("T")


class LoaderConsumptionWitnessError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoaderConsumptionWitness:
    schema: str
    evidence_class: str
    artifact_kind: str
    sha256: str
    byte_count: int
    loader_id: str
    loader_binding_sha256: str
    observed_seals: int

    def engine_load_registry_material(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "evidence_class": self.evidence_class,
            "artifact_kind": self.artifact_kind,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "loader_id": self.loader_id,
            "loader_binding_sha256": self.loader_binding_sha256,
            "observed_seals": self.observed_seals,
        }


@dataclass(frozen=True)
class SealedMemfdHandle:
    """Ephemeral read-only loader handle valid only during its callback."""

    fd: int
    proc_path: str
    sha256: str
    byte_count: int
    observed_seals: int


@dataclass(frozen=True)
class WitnessedLoad(Generic[T]):
    value: T
    witness: LoaderConsumptionWitness


def _nonempty_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LoaderConsumptionWitnessError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 1024:
        raise LoaderConsumptionWitnessError(f"{field}:TOO_LONG")
    return value


def _sha256_text(value: str, field: str) -> str:
    value = _nonempty_text(value, field)
    if len(value) != 64 or value.lower() != value or any(c not in "0123456789abcdef" for c in value):
        raise LoaderConsumptionWitnessError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _require_linux_memfd_sealing() -> None:
    if not hasattr(os, "memfd_create") or not hasattr(os, "MFD_ALLOW_SEALING"):
        raise LoaderConsumptionWitnessError("SEALED_MEMFD_UNAVAILABLE")
    required = (
        "F_ADD_SEALS", "F_GET_SEALS", "F_SEAL_WRITE", "F_SEAL_GROW",
        "F_SEAL_SHRINK", "F_SEAL_SEAL",
    )
    if any(not hasattr(fcntl, name) for name in required):
        raise LoaderConsumptionWitnessError("MEMFD_SEAL_CONSTANTS_UNAVAILABLE")


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        written = os.write(fd, view[offset:])
        if written <= 0:
            raise LoaderConsumptionWitnessError("MEMFD_WRITE_STALLED")
        offset += written


def _read_exact(fd: int, byte_count: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = byte_count
    while remaining:
        chunk = os.read(fd, min(1024 * 1024, remaining))
        if not chunk:
            raise LoaderConsumptionWitnessError(
                f"SEALED_MEMFD_SHORT_READ:{byte_count - remaining}:{byte_count}"
            )
        chunks.append(chunk)
        remaining -= len(chunk)
    extra = os.read(fd, 1)
    if extra:
        raise LoaderConsumptionWitnessError("SEALED_MEMFD_LENGTH_DRIFT")
    return b"".join(chunks)


def _prepare_sealed_memfd(payload: bytes | bytearray | memoryview) -> tuple[int, str, int, int]:
    """Create and attest one sealed memfd; caller owns and must close the fd."""
    _require_linux_memfd_sealing()
    exact_payload = bytes(payload)
    expected_sha256 = hashlib.sha256(exact_payload).hexdigest()
    flags = int(os.MFD_ALLOW_SEALING) | int(getattr(os, "MFD_CLOEXEC", 0))
    fd = os.memfd_create("entityos-hcu-loader-consumption", flags=flags)
    try:
        _write_all(fd, exact_payload)
        os.fsync(fd)
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, _REQUIRED_SEALS)
        observed_seals = int(fcntl.fcntl(fd, fcntl.F_GET_SEALS))
        if observed_seals & _REQUIRED_SEALS != _REQUIRED_SEALS:
            raise LoaderConsumptionWitnessError(
                f"SEALED_MEMFD_REQUIRED_SEALS_MISSING:{observed_seals}"
            )
        consumed = _read_exact(fd, len(exact_payload))
        observed_sha256 = hashlib.sha256(consumed).hexdigest()
        if observed_sha256 != expected_sha256:
            raise LoaderConsumptionWitnessError("SEALED_MEMFD_DIGEST_DRIFT")
        return fd, observed_sha256, len(consumed), observed_seals
    except BaseException:
        os.close(fd)
        raise


def _verify_sealed_memfd_after_callback(fd: int, *, byte_count: int, sha256: str) -> int:
    final_seals = int(fcntl.fcntl(fd, fcntl.F_GET_SEALS))
    if final_seals & _REQUIRED_SEALS != _REQUIRED_SEALS:
        raise LoaderConsumptionWitnessError(
            f"SEALED_MEMFD_POST_LOAD_SEALS_MISSING:{final_seals}"
        )
    post = _read_exact(fd, byte_count)
    if hashlib.sha256(post).hexdigest() != sha256:
        raise LoaderConsumptionWitnessError("SEALED_MEMFD_POST_LOAD_DIGEST_DRIFT")
    return final_seals


def witnessed_load_bytes(
    payload: bytes | bytearray | memoryview,
    *,
    artifact_kind: str,
    loader_id: str,
    loader_binding_sha256: str,
    loader: Callable[[bytes], T],
) -> WitnessedLoad[T]:
    """Load from exact bytes supplied by a kernel-sealed memfd witness.

    The callable receives immutable bytes read from the sealed kernel object.
    Positive use still requires a separately bound loader implementation whose
    contract consumes that argument, plus external canonical registry admission
    of the resulting observation.
    """
    artifact_kind = _nonempty_text(artifact_kind, "artifact_kind")
    loader_id = _nonempty_text(loader_id, "loader_id")
    loader_binding_sha256 = _sha256_text(loader_binding_sha256, "loader_binding_sha256")
    if not callable(loader):
        raise LoaderConsumptionWitnessError("LOADER_CALLABLE_REQUIRED")

    fd = -1
    try:
        fd, observed_sha256, byte_count, observed_seals = _prepare_sealed_memfd(payload)
        consumed = _read_exact(fd, byte_count)
        value = loader(consumed)
        final_seals = _verify_sealed_memfd_after_callback(
            fd, byte_count=byte_count, sha256=observed_sha256
        )
        return WitnessedLoad(
            value=value,
            witness=LoaderConsumptionWitness(
                schema=WITNESS_SCHEMA,
                evidence_class=BYTES_CALLBACK_EVIDENCE_CLASS,
                artifact_kind=artifact_kind,
                sha256=observed_sha256,
                byte_count=byte_count,
                loader_id=loader_id,
                loader_binding_sha256=loader_binding_sha256,
                observed_seals=final_seals,
            ),
        )
    except OSError as exc:
        raise LoaderConsumptionWitnessError(
            f"SEALED_MEMFD_OS_ERROR:{exc.errno}:{exc.strerror}"
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)


def witnessed_load_memfd(
    payload: bytes | bytearray | memoryview,
    *,
    artifact_kind: str,
    loader_id: str,
    loader_binding_sha256: str,
    loader: Callable[[SealedMemfdHandle], T],
) -> WitnessedLoad[T]:
    """Supply a real loader with one exact sealed fd/path-backed artifact.

    ``handle.proc_path`` names the same anonymous sealed kernel object as
    ``handle.fd`` (``/proc/self/fd/<fd>``) and is valid only while ``loader`` is
    executing. This avoids an uncontrolled temp-file copy for APIs that require
    a pathname. The callback must complete any load that is intended to receive
    credit before returning; lazy/deferred reads after return are outside this
    witness and must fail closed at downstream admission.
    """
    artifact_kind = _nonempty_text(artifact_kind, "artifact_kind")
    loader_id = _nonempty_text(loader_id, "loader_id")
    loader_binding_sha256 = _sha256_text(loader_binding_sha256, "loader_binding_sha256")
    if not callable(loader):
        raise LoaderConsumptionWitnessError("LOADER_CALLABLE_REQUIRED")

    fd = -1
    try:
        fd, observed_sha256, byte_count, observed_seals = _prepare_sealed_memfd(payload)
        proc_path = f"/proc/self/fd/{fd}"
        try:
            stat = os.stat(proc_path)
        except OSError as exc:
            raise LoaderConsumptionWitnessError(
                f"SEALED_MEMFD_PROC_PATH_UNAVAILABLE:{exc.errno}:{exc.strerror}"
            ) from exc
        if stat.st_size != byte_count:
            raise LoaderConsumptionWitnessError(
                f"SEALED_MEMFD_PROC_PATH_SIZE_MISMATCH:{stat.st_size}:{byte_count}"
            )

        handle = SealedMemfdHandle(
            fd=fd,
            proc_path=proc_path,
            sha256=observed_sha256,
            byte_count=byte_count,
            observed_seals=observed_seals,
        )
        value = loader(handle)
        final_seals = _verify_sealed_memfd_after_callback(
            fd, byte_count=byte_count, sha256=observed_sha256
        )
        return WitnessedLoad(
            value=value,
            witness=LoaderConsumptionWitness(
                schema=WITNESS_SCHEMA,
                evidence_class=FD_PATH_EVIDENCE_CLASS,
                artifact_kind=artifact_kind,
                sha256=observed_sha256,
                byte_count=byte_count,
                loader_id=loader_id,
                loader_binding_sha256=loader_binding_sha256,
                observed_seals=final_seals,
            ),
        )
    except OSError as exc:
        raise LoaderConsumptionWitnessError(
            f"SEALED_MEMFD_OS_ERROR:{exc.errno}:{exc.strerror}"
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)


def assert_memfd_write_is_sealed(payload: bytes = b"seal-probe") -> bool:
    """Deterministic regression helper; not runtime/model credit."""
    _require_linux_memfd_sealing()
    fd = os.memfd_create(
        "entityos-hcu-seal-probe",
        flags=int(os.MFD_ALLOW_SEALING) | int(getattr(os, "MFD_CLOEXEC", 0)),
    )
    try:
        _write_all(fd, bytes(payload))
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, _REQUIRED_SEALS)
        try:
            os.pwrite(fd, b"X", 0)
        except OSError as exc:
            return exc.errno in (errno.EPERM, errno.EBUSY)
        return False
    finally:
        os.close(fd)
