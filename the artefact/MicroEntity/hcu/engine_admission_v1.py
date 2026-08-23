#!/usr/bin/env python3
"""Fail-closed EntityOS/HCU engine-admission producer from exact local artifact bytes.

This module is deterministic control-plane plumbing, not cognition or authority storage.
It verifies checkpoint/tokenizer/runtime/build artifact bytes against an immutable lock and
only then constructs the separate ``EngineAdmission`` consumed by the retained HCU router.

A pre-load hash is not a loader-consumption proof. Route-ready artifact registry material
therefore requires a separate post-load revalidation binding. This closes straightforward
hash-then-load path substitution. Exact runtime acceptance still requires either a loader
that attests the bytes it actually consumed or an immutable/read-only artifact boundary;
a malicious swap-and-restore entirely inside the loader window is not proven impossible by
pre/post path hashing alone.
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
POST_LOAD_BINDING_SCHEMA = "HCU_ENGINE_POST_LOAD_BINDING/v1"
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
class PostLoadArtifactBinding:
    schema: str
    entity_generation: int
    engine_identity: str
    engine_artifact_sha256: str
    engine_admission_receipt_sha256: str
    checkpoint: ArtifactDigest
    tokenizer: ArtifactDigest
    runtime: ArtifactDigest
    build: ArtifactDigest
    receipt_sha256: str


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

    def admitted_engine_artifacts(
        self,
        post_load_binding: PostLoadArtifactBinding | None = None,
    ) -> dict[str, str]:
        """Return route registry material only after post-load byte revalidation."""
        if not isinstance(post_load_binding, PostLoadArtifactBinding):
            raise EngineAdmissionError("POST_LOAD_ARTIFACT_BINDING_REQUIRED")
        if post_load_binding.schema != POST_LOAD_BINDING_SCHEMA:
            raise EngineAdmissionError("POST_LOAD_ARTIFACT_BINDING_SCHEMA_UNSUPPORTED")
        if post_load_binding.entity_generation != self.entity_generation:
            raise EngineAdmissionError("POST_LOAD_ENTITY_GENERATION_MISMATCH")
        if post_load_binding.engine_identity != self.admission.engine_identity:
            raise EngineAdmissionError("POST_LOAD_ENGINE_IDENTITY_MISMATCH")
        if post_load_binding.engine_artifact_sha256 != self.engine_artifact_sha256:
            raise EngineAdmissionError("POST_LOAD_ENGINE_ARTIFACT_MISMATCH")
        if post_load_binding.engine_admission_receipt_sha256 != self.receipt_sha256:
            raise EngineAdmissionError("POST_LOAD_ENGINE_ADMISSION_RECEIPT_MISMATCH")
        for field in ("checkpoint", "tokenizer", "runtime", "build"):
            if getattr(post_load_binding, field) != getattr(self, field):
                raise EngineAdmissionError(f"POST_LOAD_{field.upper()}_DIGEST_MISMATCH")
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


def _enumerate_regular_tree_members(path: Path) -> list[tuple[str, Path]]:
    """Enumerate the exact regular-file membership admitted into a tree digest."""
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
    return members


def digest_artifact_path(path: Path) -> ArtifactDigest:
    """Hash a regular file directly or a directory as a deterministic file-name tree.

    Directory identity commits to every relative UTF-8 path, file size and raw file
    SHA-256 in lexicographic POSIX-path order. Symlinks and non-regular members fail closed.
    The member set is enumerated again before return so files added, removed, or renamed
    while hashing cannot silently produce a digest for an already-changed directory tree.
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

    members = _enumerate_regular_tree_members(path)
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

    final_members = _enumerate_regular_tree_members(path)
    if tuple(rel for rel, _ in final_members) != tuple(rel for rel, _ in members):
        raise EngineAdmissionError(f"ARTIFACT_TREE_MEMBERSHIP_CHANGED_DURING_HASH:{path}")

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
    """Verify exact local bytes and construct a pre-load EngineAdmission candidate.

    This result is deliberately not sufficient to obtain route registry material. Call
    ``verify_post_load_artifact_binding`` after the loader returns, then pass that binding
    to ``VerifiedEngineAdmission.admitted_engine_artifacts``.

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


def verify_post_load_artifact_binding(
    verified: VerifiedEngineAdmission,
    paths: EngineArtifactPaths,
    *,
    current_generation: int,
) -> PostLoadArtifactBinding:
    """Revalidate all artifact paths after model load before exposing route registry data."""
    if not isinstance(verified, VerifiedEngineAdmission):
        raise EngineAdmissionError("VERIFIED_ENGINE_ADMISSION_REQUIRED")
    current = _generation(current_generation, "current_generation")
    if verified.entity_generation != current:
        raise EngineAdmissionError("STALE_POST_LOAD_ENTITY_GENERATION")
    if not isinstance(paths, EngineArtifactPaths):
        raise EngineAdmissionError("ENGINE_ARTIFACT_PATHS_TYPE_REQUIRED")

    observed = {
        "checkpoint": digest_artifact_path(paths.checkpoint),
        "tokenizer": digest_artifact_path(paths.tokenizer),
        "runtime": digest_artifact_path(paths.runtime),
        "build": digest_artifact_path(paths.build),
    }
    for field, digest in observed.items():
        if digest != getattr(verified, field):
            raise EngineAdmissionError(f"{field.upper()}:POST_LOAD_BYTES_MISMATCH")

    material = {
        "schema": POST_LOAD_BINDING_SCHEMA,
        "entity_generation": verified.entity_generation,
        "engine_identity": verified.admission.engine_identity,
        "engine_artifact_sha256": verified.engine_artifact_sha256,
        "engine_admission_receipt_sha256": verified.receipt_sha256,
        "checkpoint": observed["checkpoint"].__dict__,
        "tokenizer": observed["tokenizer"].__dict__,
        "runtime": observed["runtime"].__dict__,
        "build": observed["build"].__dict__,
    }
    receipt_sha256 = hashlib.sha256(_canonical(material)).hexdigest()
    return PostLoadArtifactBinding(
        schema=POST_LOAD_BINDING_SCHEMA,
        entity_generation=verified.entity_generation,
        engine_identity=verified.admission.engine_identity,
        engine_artifact_sha256=verified.engine_artifact_sha256,
        engine_admission_receipt_sha256=verified.receipt_sha256,
        checkpoint=observed["checkpoint"],
        tokenizer=observed["tokenizer"],
        runtime=observed["runtime"],
        build=observed["build"],
        receipt_sha256=receipt_sha256,
    )
