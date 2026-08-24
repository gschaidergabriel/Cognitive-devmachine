#!/usr/bin/env python3
"""Streaming regular-file -> sealed-memfd loader-consumption witness for EntityOS/HCU.

This producer is intentionally narrow. It exists for large local model artifacts such as a
single-file GGUF where materializing the entire source as one Python ``bytes`` object before
creating a sealed memfd is unnecessary. It opens one regular source file fail-closed, streams
its exact bytes into an anonymous Linux memfd while hashing, seals the memfd against writes,
re-hashes the sealed object, and exposes only the sealed fd plus ``/proc/self/fd/<fd>`` path to
one synchronous bound loader callback.

Evidence scope is deliberately limited. Success proves that this producer copied one stable
regular-file snapshot matching the declared source digest/size into one sealed kernel object
and supplied that object to the callback. It does NOT prove an opaque loader read every byte,
that a model was actually constructed, that inference occurred, or that J-Space/model/training
credit is earned. Downstream canonical loader-consumption admission, physical-engine lease,
ModelExecution admission, inference receipt and J-Space binding remain separate gates.
"""
from __future__ import annotations

from dataclasses import dataclass
import errno
import fcntl
import hashlib
import os
from pathlib import Path
import stat
from typing import Callable, Generic, TypeVar

try:
    from .loader_consumption_witness_v1 import (
        LoaderConsumptionWitness,
        SealedMemfdHandle,
        WitnessedLoad,
        WITNESS_SCHEMA,
    )
except ImportError:
    from loader_consumption_witness_v1 import (
        LoaderConsumptionWitness,
        SealedMemfdHandle,
        WitnessedLoad,
        WITNESS_SCHEMA,
    )

STREAM_FILE_EVIDENCE_CLASS = "SEALED_MEMFD_STREAMED_REGULAR_FILE_FD_PATH_CALLBACK/v1"
_CHUNK = 1024 * 1024
T = TypeVar("T")


class LoaderConsumptionStreamError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceFileSnapshot:
    path: str
    sha256: str
    byte_count: int
    device: int
    inode: int
    mtime_ns: int
    ctime_ns: int


_REQUIRED_SEALS = (
    getattr(fcntl, "F_SEAL_WRITE", 0)
    | getattr(fcntl, "F_SEAL_GROW", 0)
    | getattr(fcntl, "F_SEAL_SHRINK", 0)
    | getattr(fcntl, "F_SEAL_SEAL", 0)
)


def _require_linux_primitives() -> None:
    if not hasattr(os, "memfd_create") or not hasattr(os, "MFD_ALLOW_SEALING"):
        raise LoaderConsumptionStreamError("SEALED_MEMFD_UNAVAILABLE")
    if not hasattr(os, "O_NOFOLLOW"):
        raise LoaderConsumptionStreamError("O_NOFOLLOW_UNAVAILABLE")
    required = (
        "F_ADD_SEALS",
        "F_GET_SEALS",
        "F_SEAL_WRITE",
        "F_SEAL_GROW",
        "F_SEAL_SHRINK",
        "F_SEAL_SEAL",
    )
    if any(not hasattr(fcntl, name) for name in required) or _REQUIRED_SEALS == 0:
        raise LoaderConsumptionStreamError("MEMFD_SEAL_CONSTANTS_UNAVAILABLE")
    if not os.path.isdir("/proc/self/fd"):
        raise LoaderConsumptionStreamError("PROC_SELF_FD_UNAVAILABLE")


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LoaderConsumptionStreamError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 4096:
        raise LoaderConsumptionStreamError(f"{field}:TOO_LONG")
    return value


def _sha256(value: str, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise LoaderConsumptionStreamError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _byte_count(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LoaderConsumptionStreamError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _stat_identity(st: os.stat_result) -> tuple[int, int, int, int, int]:
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        written = os.write(fd, view[offset:])
        if written <= 0:
            raise LoaderConsumptionStreamError("MEMFD_WRITE_STALLED")
        offset += written


def _hash_fd(fd: int, *, expected_size: int) -> str:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    observed = 0
    while observed < expected_size:
        chunk = os.read(fd, min(_CHUNK, expected_size - observed))
        if not chunk:
            raise LoaderConsumptionStreamError(
                f"FD_SHORT_READ:{observed}:{expected_size}"
            )
        digest.update(chunk)
        observed += len(chunk)
    if os.read(fd, 1):
        raise LoaderConsumptionStreamError("FD_LENGTH_DRIFT")
    return digest.hexdigest()


def _open_regular_source(path: Path) -> tuple[int, os.stat_result]:
    if not isinstance(path, Path):
        raise LoaderConsumptionStreamError("SOURCE_PATH_TYPE_REQUIRED")
    flags = os.O_RDONLY | int(getattr(os, "O_CLOEXEC", 0)) | int(os.O_NOFOLLOW)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise LoaderConsumptionStreamError(f"SOURCE_SYMLINK_FORBIDDEN:{path}") from exc
        raise LoaderConsumptionStreamError(
            f"SOURCE_OPEN_FAILED:{path}:{exc.errno}:{exc.strerror}"
        ) from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise LoaderConsumptionStreamError(f"SOURCE_REGULAR_FILE_REQUIRED:{path}")
        return fd, st
    except BaseException:
        os.close(fd)
        raise


def witnessed_load_regular_file_memfd(
    source_path: Path,
    *,
    expected_source_sha256: str,
    expected_source_byte_count: int,
    artifact_kind: str,
    loader_id: str,
    loader_binding_sha256: str,
    loader: Callable[[SealedMemfdHandle], T],
) -> WitnessedLoad[T]:
    """Stream one exact regular file into a sealed memfd and invoke a bound loader.

    The source is opened with ``O_NOFOLLOW`` and must remain identical by device, inode,
    size, mtime_ns and ctime_ns from pre-copy to post-copy. The streamed SHA-256 and byte
    count must exactly match the caller's independently pinned expectations. Only then is the
    memfd sealed and exposed synchronously to ``loader``.
    """
    _require_linux_primitives()
    expected_source_sha256 = _sha256(expected_source_sha256, "expected_source_sha256")
    expected_source_byte_count = _byte_count(
        expected_source_byte_count, "expected_source_byte_count"
    )
    artifact_kind = _text(artifact_kind, "artifact_kind")
    loader_id = _text(loader_id, "loader_id")
    loader_binding_sha256 = _sha256(loader_binding_sha256, "loader_binding_sha256")
    if not callable(loader):
        raise LoaderConsumptionStreamError("LOADER_CALLABLE_REQUIRED")

    source_fd = -1
    memfd = -1
    try:
        source_fd, before = _open_regular_source(source_path)
        if before.st_size != expected_source_byte_count:
            raise LoaderConsumptionStreamError(
                f"SOURCE_SIZE_MISMATCH:{before.st_size}:{expected_source_byte_count}"
            )

        memfd_flags = int(os.MFD_ALLOW_SEALING) | int(getattr(os, "MFD_CLOEXEC", 0))
        memfd = os.memfd_create("entityos-hcu-loader-consumption-stream", flags=memfd_flags)
        source_digest = hashlib.sha256()
        copied = 0
        while True:
            block = os.read(source_fd, _CHUNK)
            if not block:
                break
            _write_all(memfd, block)
            source_digest.update(block)
            copied += len(block)
            if copied > expected_source_byte_count:
                raise LoaderConsumptionStreamError("SOURCE_GREW_DURING_COPY")

        after = os.fstat(source_fd)
        if _stat_identity(before) != _stat_identity(after):
            raise LoaderConsumptionStreamError("SOURCE_CHANGED_DURING_COPY")
        if copied != expected_source_byte_count:
            raise LoaderConsumptionStreamError(
                f"SOURCE_COPY_SIZE_MISMATCH:{copied}:{expected_source_byte_count}"
            )
        observed_source_sha256 = source_digest.hexdigest()
        if observed_source_sha256 != expected_source_sha256:
            raise LoaderConsumptionStreamError(
                f"SOURCE_SHA256_MISMATCH:{observed_source_sha256}:{expected_source_sha256}"
            )

        os.fsync(memfd)
        fcntl.fcntl(memfd, fcntl.F_ADD_SEALS, _REQUIRED_SEALS)
        observed_seals = int(fcntl.fcntl(memfd, fcntl.F_GET_SEALS))
        if observed_seals & _REQUIRED_SEALS != _REQUIRED_SEALS:
            raise LoaderConsumptionStreamError(
                f"SEALED_MEMFD_REQUIRED_SEALS_MISSING:{observed_seals}"
            )

        sealed_sha256 = _hash_fd(memfd, expected_size=copied)
        if sealed_sha256 != observed_source_sha256:
            raise LoaderConsumptionStreamError("SEALED_MEMFD_SOURCE_DIGEST_DRIFT")
        proc_path = f"/proc/self/fd/{memfd}"
        proc_stat = os.stat(proc_path)
        if proc_stat.st_size != copied:
            raise LoaderConsumptionStreamError(
                f"SEALED_MEMFD_PROC_PATH_SIZE_MISMATCH:{proc_stat.st_size}:{copied}"
            )

        handle = SealedMemfdHandle(
            fd=memfd,
            proc_path=proc_path,
            sha256=sealed_sha256,
            byte_count=copied,
            observed_seals=observed_seals,
        )
        value = loader(handle)

        final_seals = int(fcntl.fcntl(memfd, fcntl.F_GET_SEALS))
        if final_seals & _REQUIRED_SEALS != _REQUIRED_SEALS:
            raise LoaderConsumptionStreamError(
                f"SEALED_MEMFD_POST_LOAD_SEALS_MISSING:{final_seals}"
            )
        if _hash_fd(memfd, expected_size=copied) != sealed_sha256:
            raise LoaderConsumptionStreamError("SEALED_MEMFD_POST_LOAD_DIGEST_DRIFT")

        return WitnessedLoad(
            value=value,
            witness=LoaderConsumptionWitness(
                schema=WITNESS_SCHEMA,
                evidence_class=STREAM_FILE_EVIDENCE_CLASS,
                artifact_kind=artifact_kind,
                sha256=sealed_sha256,
                byte_count=copied,
                loader_id=loader_id,
                loader_binding_sha256=loader_binding_sha256,
                observed_seals=final_seals,
            ),
        )
    except LoaderConsumptionStreamError:
        raise
    except OSError as exc:
        raise LoaderConsumptionStreamError(
            f"STREAM_WITNESS_OS_ERROR:{exc.errno}:{exc.strerror}"
        ) from exc
    finally:
        if source_fd >= 0:
            os.close(source_fd)
        if memfd >= 0:
            os.close(memfd)
