#!/usr/bin/env python3
"""Fail-closed EntityOS/HCU engine-admission producer from exact local artifact bytes.

This module is deterministic control-plane plumbing, not cognition or authority storage.
It verifies checkpoint/tokenizer/runtime/build artifact bytes against an immutable lock and
only then constructs the separate ``EngineAdmission`` consumed by the retained HCU router.

Scope limit: hashing bytes immediately before routing does not by itself prove that a
later model loader consumed the same bytes. Runtime acceptance must additionally bind the
loader/inference receipt (or an immutable read-only artifact boundary) to this receipt.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

from reactive_event_router_v1 import (
    ADMITTED_INTERNAL_ENGINES,
    ADMITTED_INTERNAL_PROVIDER_ALIASES,
    EngineAdmission,
)

LOCK_SCHEMA = "HCU_ENGINE_ARTIFACT_LOCK/v1"
BUNDLE_SCHEMA = "HCU_ENGINE_ARTIFACT_BUNDLE/v1"
TREE_SCHEMA = b"HCU_ARTIFACT_TREE_SHA256/v1\x00"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CHUNK = 1024 * 1024


class EngineAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactDigest:
    kind: str
    sha256: str
    file_count: int
    byte_count: int


@dataclass(frozen=True)
class EngineArtifactLock:
    schema: str
    provider_alias: str
    engine_identity: str
    engine_class: str
    checkpoint_sha256: str
    tokenizer_sha256: str
    runtime_sha256: str
    build_sha256: str
    engine_artifact_sha256: str


@dataclass(frozen=True)
class EngineArtifactPaths:
    checkpoint: Path
    tokenizer: Path
    runtime: Path
    build: Path


@dataclass(frozen=True)
class VerifiedEngineAdmission:
    entity_generation: int
    admission: EngineAdmission
    checkpoint: ArtifactDigest
    tokenizer: ArtifactDigest
    runtime: ArtifactDigest
    build: ArtifactDigest
    engine_artifact_sha256: str
    receipt_sha256: str

    def admitted_engine_artifacts(self) -> dict[str, str]:
        return {self.admission.engine_identity: self.engine_artifact_sha256}

    def receipt(self) -> dict[str, Any]:
        return {
            "schema": "HCU_VERIFIED_ENGINE_ADMISSION_RECEIPT/v1",
            "entity_generation": self.entity_generation,
            "provider_alias": self.admission.provider_alias,
            "engine_identity": self.admission.engine_identity,
            "engine_class": self.admission.engine_class,
            "checkpoint": self.checkpoint.__dict__,
            "tokenizer": self.tokenizer.__dict__,
            "runtime": self.runtime.__dict__,
            "build": self.build.__dict__,
            "engine_artifact_sha256": self.engine_artifact_sha256,
            "receipt_sha256": self.receipt_sha256,
        }


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EngineAdmissionError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha256_text(value: Any, field: str) -> str:
    value = _text(value, field)
    if not SHA256_RE.fullmatch(value):
        raise EngineAdmissionError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EngineAdmissionError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _hash_regular_file(path: Path) -> tuple[bytes, int]:
    if path.is_symlink():
        raise EngineAdmissionError(f"ARTIFACT_SYMLINK_FORBIDDEN:{path}")
    try:
        before = path.stat()
    except OSError as exc:
        raise EngineAdmissionError(f"ARTIFACT_STAT_FAILED:{path}:{exc.__class__.__name__}") from exc
    if not path.is_file():
        raise EngineAdmissionError(f"ARTIFACT_REGULAR_FILE_REQUIRED:{path}")

    h = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while True:
                block = handle.read(_CHUNK)
                if not block:
                    break
                h.update(block)
        after = path.stat()
    except OSError as exc:
        raise EngineAdmissionError(f"ARTIFACT_READ_FAILED:{path}:{exc.__class__.__name__}") from exc

    stable = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) == (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if not stable:
        raise EngineAdmissionError(f"ARTIFACT_CHANGED_DURING_HASH:{path}")
    return h.digest(), before.st_size


def digest_artifact_path(path: Path) -> ArtifactDigest:
    """Hash a regular file directly or a directory as a deterministic file-name tree.

    Directory identity commits to every relative UTF-8 path, file size and raw file
    SHA-256 in lexicographic POSIX-path order. Symlinks and non-regular members fail closed.
    """
    if not isinstance(path, Path):
        raise EngineAdmissionError("ARTIFACT_PATH_TYPE_REQUIRED")
    if path.is_symlink():
        raise EngineAdmissionError(f"ARTIFACT_SYMLINK_FORBIDDEN:{path}")
    if path.is_file():
        digest, size = _hash_regular_file(path)
        return ArtifactDigest("FILE_SHA256", digest.hex(), 1, size)
    if not path.is_dir():
        raise EngineAdmissionError(f"ARTIFACT_PATH_NOT_FOUND_OR_UNSUPPORTED:{path}")

    members: list[tuple[str, Path]] = []
    for root, dirs, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        for name in dirs:
            candidate = root_path / name
            if candidate.is_symlink():
                raise EngineAdmissionError(f"ARTIFACT_SYMLINK_FORBIDDEN:{candidate}")
        for name in files:
            candidate = root_path / name
            if candidate.is_symlink():
                raise EngineAdmissionError(f"ARTIFACT_SYMLINK_FORBIDDEN:{candidate}")
            if not candidate.is_file():
                raise EngineAdmissionError(f"ARTIFACT_REGULAR_FILE_REQUIRED:{candidate}")
            rel = candidate.relative_to(path).as_posix()
            members.append((rel, candidate))
    members.sort(key=lambda row: row[0])
    if not members:
        raise EngineAdmissionError(f"ARTIFACT_TREE_EMPTY:{path}")

    tree = hashlib.sha256()
    tree.update(TREE_SCHEMA)
    total = 0
    for rel, candidate in members:
        try:
            rel_bytes = rel.encode("utf-8", "strict")
        except UnicodeEncodeError as exc:
            raise EngineAdmissionError("ARTIFACT_RELATIVE_PATH_UTF8_REQUIRED") from exc
        if len(rel_bytes) > 65535:
            raise EngineAdmissionError("ARTIFACT_RELATIVE_PATH_TOO_LONG")
        file_digest, size = _hash_regular_file(candidate)
        tree.update(len(rel_bytes).to_bytes(2, "big"))
        tree.update(rel_bytes)
        tree.update(size.to_bytes(8, "big"))
        tree.update(file_digest)
        total += size
    return ArtifactDigest("TREE_SHA256_V1", tree.hexdigest(), len(members), total)


def derive_engine_artifact_sha256(lock: EngineArtifactLock) -> str:
    material = {
        "schema": BUNDLE_SCHEMA,
        "provider_alias": lock.provider_alias,
        "engine_identity": lock.engine_identity,
        "engine_class": lock.engine_class,
        "checkpoint_sha256": lock.checkpoint_sha256,
        "tokenizer_sha256": lock.tokenizer_sha256,
        "runtime_sha256": lock.runtime_sha256,
        "build_sha256": lock.build_sha256,
    }
    return hashlib.sha256(_canonical(material)).hexdigest()


def _validate_lock(lock: EngineArtifactLock) -> EngineArtifactLock:
    if not isinstance(lock, EngineArtifactLock):
        raise EngineAdmissionError("ENGINE_ARTIFACT_LOCK_TYPE_REQUIRED")
    if lock.schema != LOCK_SCHEMA:
        raise EngineAdmissionError("ENGINE_ARTIFACT_LOCK_SCHEMA_UNSUPPORTED")
    provider = _text(lock.provider_alias, "provider_alias").lower()
    if provider not in ADMITTED_INTERNAL_PROVIDER_ALIASES:
        raise EngineAdmissionError("ENGINE_PROVIDER_NOT_ADMITTED")
    identity = _text(lock.engine_identity, "engine_identity").lower()
    engine_class = _text(lock.engine_class, "engine_class").upper()
    admitted_class = ADMITTED_INTERNAL_ENGINES.get(identity)
    if admitted_class is None:
        raise EngineAdmissionError("ENGINE_IDENTITY_NOT_ADMITTED")
    if engine_class != admitted_class:
        raise EngineAdmissionError("ENGINE_CLASS_MISMATCH")

    validated = EngineArtifactLock(
        schema=LOCK_SCHEMA,
        provider_alias=provider,
        engine_identity=identity,
        engine_class=engine_class,
        checkpoint_sha256=_sha256_text(lock.checkpoint_sha256, "checkpoint_sha256"),
        tokenizer_sha256=_sha256_text(lock.tokenizer_sha256, "tokenizer_sha256"),
        runtime_sha256=_sha256_text(lock.runtime_sha256, "runtime_sha256"),
        build_sha256=_sha256_text(lock.build_sha256, "build_sha256"),
        engine_artifact_sha256=_sha256_text(lock.engine_artifact_sha256, "engine_artifact_sha256"),
    )
    if derive_engine_artifact_sha256(validated) != validated.engine_artifact_sha256:
        raise EngineAdmissionError("ENGINE_ARTIFACT_BUNDLE_DIGEST_MISMATCH")
    return validated


def verify_and_construct_engine_admission(
    lock: EngineArtifactLock,
    paths: EngineArtifactPaths,
    *,
    entity_generation: int,
    current_generation: int,
) -> VerifiedEngineAdmission:
    """Verify exact local bytes and construct the router's separate EngineAdmission.

    No network, secret lookup, model inference, durable state write or real effect occurs.
    """
    generation = _generation(entity_generation, "entity_generation")
    current = _generation(current_generation, "current_generation")
    if generation != current:
        raise EngineAdmissionError("STALE_ENTITY_GENERATION")
    if not isinstance(paths, EngineArtifactPaths):
        raise EngineAdmissionError("ENGINE_ARTIFACT_PATHS_TYPE_REQUIRED")
    lock = _validate_lock(lock)

    checkpoint = digest_artifact_path(paths.checkpoint)
    tokenizer = digest_artifact_path(paths.tokenizer)
    runtime = digest_artifact_path(paths.runtime)
    build = digest_artifact_path(paths.build)
    observed = {
        "checkpoint_sha256": checkpoint.sha256,
        "tokenizer_sha256": tokenizer.sha256,
        "runtime_sha256": runtime.sha256,
        "build_sha256": build.sha256,
    }
    expected = {
        "checkpoint_sha256": lock.checkpoint_sha256,
        "tokenizer_sha256": lock.tokenizer_sha256,
        "runtime_sha256": lock.runtime_sha256,
        "build_sha256": lock.build_sha256,
    }
    for field in sorted(expected):
        if observed[field] != expected[field]:
            raise EngineAdmissionError(f"{field}:LOADED_BYTES_MISMATCH")

    admission = EngineAdmission(
        provider_alias=lock.provider_alias,
        engine_identity=lock.engine_identity,
        engine_class=lock.engine_class,
        engine_artifact_sha256=lock.engine_artifact_sha256,
    )
    receipt_material = {
        "schema": "HCU_VERIFIED_ENGINE_ADMISSION_RECEIPT/v1",
        "entity_generation": generation,
        "provider_alias": admission.provider_alias,
        "engine_identity": admission.engine_identity,
        "engine_class": admission.engine_class,
        "checkpoint": checkpoint.__dict__,
        "tokenizer": tokenizer.__dict__,
        "runtime": runtime.__dict__,
        "build": build.__dict__,
        "engine_artifact_sha256": lock.engine_artifact_sha256,
    }
    receipt_sha256 = hashlib.sha256(_canonical(receipt_material)).hexdigest()
    return VerifiedEngineAdmission(
        entity_generation=generation,
        admission=admission,
        checkpoint=checkpoint,
        tokenizer=tokenizer,
        runtime=runtime,
        build=build,
        engine_artifact_sha256=lock.engine_artifact_sha256,
        receipt_sha256=receipt_sha256,
    )
