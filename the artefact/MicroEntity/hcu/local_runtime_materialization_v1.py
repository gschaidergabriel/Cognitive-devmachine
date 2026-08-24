#!/usr/bin/env python3
"""Deterministic local runtime/model materialization gate for EntityOS/HCU.

Closes only the local byte-identity gap between pinned llama.cpp/Qwen source
candidates and later loader/executor evidence. It does not download, execute,
load or infer with a model, and grants no runtime, J-Space, training, truth or
effect credit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

SCHEMA = "HCU_LOCAL_RUNTIME_MATERIALIZATION/v1"
MODEL_CANDIDATE_SCHEMA = "HCU_LOCAL_APPROX_08B_MODEL_CANDIDATE/v1"
RUNTIME_CANDIDATE_SCHEMA = "HCU_LOCAL_RUNTIME_CANDIDATE/v1"
MODEL_CANDIDATE_STATUS = "CANDIDATE_ONLY_NO_RUNTIME_CREDIT"
RUNTIME_CANDIDATE_STATUS = "ATTESTED_DISTRIBUTION_CANDIDATE_ONLY_NO_RUNTIME_CREDIT"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class LocalRuntimeMaterializationError(ValueError):
    pass


@dataclass(frozen=True)
class LocalFileIdentity:
    relative_path: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class LocalRuntimeMaterializationReceipt:
    schema: str
    canonicalization_schema: str
    runtime_family: str
    runtime_build_tag: str
    runtime_source_commit: str
    runtime_platform: str
    runtime_acceleration: str
    runtime_archive_asset: str
    runtime_archive_sha256: str
    runtime_archive_byte_count: int
    runtime_binary: LocalFileIdentity
    dependency_set_sha256: str
    dependencies: tuple[LocalFileIdentity, ...]
    runtime_build_sha256: str
    model_repository: str
    model_artifact: str
    model_sha256: str
    model_byte_count: int
    materialization_sha256: str


@dataclass(frozen=True)
class MaterializedRuntime:
    receipt: LocalRuntimeMaterializationReceipt
    runtime_binary_path: Path
    dependency_paths: tuple[Path, ...]
    model_path: Path


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise LocalRuntimeMaterializationError(code)


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(normalized == value, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha256_text(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    _need(len(value) == 64 and value.lower() == value and all(ch in "0123456789abcdef" for ch in value)
          and value not in {"0" * 64, "f" * 64},
          f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED")
    return value


def _git_sha1(value: Any, field: str) -> str:
    value = _text(value, field, 40)
    _need(len(value) == 40 and value.lower() == value and all(ch in "0123456789abcdef" for ch in value)
          and value not in {"0" * 40, "f" * 40},
          f"{field}:LOWERCASE_NONPLACEHOLDER_GIT_SHA1_REQUIRED")
    return value


def _safe_nonnegative_int(value: Any, field: str) -> int:
    _need(type(value) is int and 0 <= value <= MAX_SAFE_INTEGER,
          f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    _need(isinstance(value, Mapping), f"{field}:OBJECT_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise LocalRuntimeMaterializationError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _read_candidate(path: Path, field: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalRuntimeMaterializationError(f"{field}:UNAVAILABLE_OR_INVALID:{exc.__class__.__name__}") from exc
    _need(isinstance(value, dict), f"{field}:OBJECT_REQUIRED")
    return value


def _candidate_contracts(model: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    _need(model.get("schema") == MODEL_CANDIDATE_SCHEMA, "MODEL_CANDIDATE_SCHEMA_UNSUPPORTED")
    _need(runtime.get("schema") == RUNTIME_CANDIDATE_SCHEMA, "RUNTIME_CANDIDATE_SCHEMA_UNSUPPORTED")
    _need(model.get("status") == MODEL_CANDIDATE_STATUS, "MODEL_CANDIDATE_MUST_REMAIN_NONPROMOTED")
    _need(runtime.get("status") == RUNTIME_CANDIDATE_STATUS, "RUNTIME_CANDIDATE_MUST_REMAIN_NONPROMOTED")

    upstream_model = _mapping(model.get("upstream_model_artifact"), "model.upstream_model_artifact")
    role_mapping = _mapping(model.get("single_file_role_mapping"), "model.single_file_role_mapping")
    runtime_family = _mapping(model.get("documented_local_runtime_family"), "model.documented_local_runtime_family")
    runtime_upstream = _mapping(runtime.get("upstream"), "runtime.upstream")
    distribution = _mapping(runtime.get("distribution_candidate"), "runtime.distribution_candidate")
    pairing = _mapping(runtime.get("model_pairing"), "runtime.model_pairing")

    model_sha = _sha256_text(upstream_model.get("sha256"), "model.upstream_model_artifact.sha256")
    checkpoint_sha = _sha256_text(role_mapping.get("checkpoint_expected_sha256"), "model.single_file_role_mapping.checkpoint_expected_sha256")
    tokenizer_sha = _sha256_text(role_mapping.get("tokenizer_container_expected_sha256"), "model.single_file_role_mapping.tokenizer_container_expected_sha256")
    _need(model_sha == checkpoint_sha == tokenizer_sha, "MODEL_SINGLE_FILE_ROLE_IDENTITY_MISMATCH")

    model_size = _safe_nonnegative_int(upstream_model.get("byte_count"), "model.upstream_model_artifact.byte_count")
    _need(model_size > 0, "MODEL_BYTE_COUNT_POSITIVE_REQUIRED")

    runtime_source = _git_sha1(runtime_upstream.get("source_repository_digest"), "runtime.upstream.source_repository_digest")
    model_runtime_source = _git_sha1(runtime_family.get("exact_runtime_source_commit"), "model.documented_local_runtime_family.exact_runtime_source_commit")
    _need(runtime_source == model_runtime_source, "RUNTIME_SOURCE_CANDIDATE_MISMATCH")

    pairing_sha = _sha256_text(pairing.get("model_sha256"), "runtime.model_pairing.model_sha256")
    pairing_size = _safe_nonnegative_int(pairing.get("model_byte_count"), "runtime.model_pairing.model_byte_count")
    _need(pairing_sha == model_sha and pairing_size == model_size, "RUNTIME_MODEL_PAIRING_MISMATCH")
    _need(_text(pairing.get("model_repository"), "runtime.model_pairing.model_repository") ==
          _text(upstream_model.get("repository"), "model.upstream_model_artifact.repository"),
          "RUNTIME_MODEL_REPOSITORY_MISMATCH")
    _need(_text(pairing.get("model_artifact"), "runtime.model_pairing.model_artifact") ==
          _text(upstream_model.get("artifact"), "model.upstream_model_artifact.artifact"),
          "RUNTIME_MODEL_ARTIFACT_MISMATCH")

    return {
        "runtime_family": _text(runtime.get("runtime_family"), "runtime.runtime_family"),
        "runtime_build_tag": _text(runtime_upstream.get("build_tag"), "runtime.upstream.build_tag"),
        "runtime_source_commit": runtime_source,
        "runtime_platform": _text(distribution.get("platform"), "runtime.distribution_candidate.platform"),
        "runtime_acceleration": _text(distribution.get("acceleration"), "runtime.distribution_candidate.acceleration"),
        "runtime_archive_asset": _text(distribution.get("asset"), "runtime.distribution_candidate.asset"),
        "runtime_archive_sha256": _sha256_text(distribution.get("archive_sha256"), "runtime.distribution_candidate.archive_sha256"),
        "model_repository": _text(upstream_model.get("repository"), "model.upstream_model_artifact.repository"),
        "model_artifact": _text(upstream_model.get("artifact"), "model.upstream_model_artifact.artifact"),
        "model_sha256": model_sha,
        "model_byte_count": model_size,
    }


def _regular_file(path: Path, field: str, *, executable: bool = False) -> Path:
    try:
        lst = path.lstat()
    except OSError as exc:
        raise LocalRuntimeMaterializationError(f"{field}:UNAVAILABLE:{exc.__class__.__name__}") from exc
    _need(not stat.S_ISLNK(lst.st_mode), f"{field}:SYMLINK_FORBIDDEN")
    _need(stat.S_ISREG(lst.st_mode), f"{field}:REGULAR_FILE_REQUIRED")
    if executable:
        _need(bool(lst.st_mode & 0o111), f"{field}:EXECUTABLE_BIT_REQUIRED")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise LocalRuntimeMaterializationError(f"{field}:RESOLVE_FAILED:{exc.__class__.__name__}") from exc


def _hash_file(path: Path, field: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                count += len(chunk)
                _need(count <= MAX_SAFE_INTEGER, f"{field}:BYTE_COUNT_EXCEEDS_IJSON_SAFE_INTEGER")
    except OSError as exc:
        raise LocalRuntimeMaterializationError(f"{field}:READ_FAILED:{exc.__class__.__name__}") from exc
    return digest.hexdigest(), count


def _relative_file(root: Path, relative: str, field: str, *, executable: bool = False) -> tuple[Path, LocalFileIdentity]:
    rel = Path(_text(relative, field, 4096))
    _need(not rel.is_absolute(), f"{field}:RELATIVE_PATH_REQUIRED")
    _need(".." not in rel.parts and "." not in rel.parts, f"{field}:PATH_TRAVERSAL_FORBIDDEN")
    target = _regular_file(root / rel, field, executable=executable)
    root_resolved = root.resolve(strict=True)
    try:
        actual_rel = target.relative_to(root_resolved)
    except ValueError as exc:
        raise LocalRuntimeMaterializationError(f"{field}:OUTSIDE_EXTRACTION_ROOT") from exc
    canonical_rel = actual_rel.as_posix()
    _need(canonical_rel == rel.as_posix(), f"{field}:RESOLVED_PATH_ALIAS_FORBIDDEN")
    sha, size = _hash_file(target, field)
    return target, LocalFileIdentity(relative_path=canonical_rel, sha256=sha, byte_count=size)


def _receipt_material(receipt: LocalRuntimeMaterializationReceipt) -> dict[str, Any]:
    material = asdict(receipt)
    material.pop("materialization_sha256", None)
    return material


def verify_local_runtime_materialization(*, model_candidate: Mapping[str, Any], runtime_candidate: Mapping[str, Any],
                                         runtime_archive_path: Path, extraction_root: Path,
                                         runtime_binary_relative_path: str, dependency_relative_paths: Sequence[str],
                                         model_path: Path) -> MaterializedRuntime:
    """Hash and bind exact local candidate bytes without executing them."""
    contract = _candidate_contracts(model_candidate, runtime_candidate)

    archive = _regular_file(Path(runtime_archive_path), "runtime_archive_path")
    archive_sha, archive_size = _hash_file(archive, "runtime_archive_path")
    _need(archive_sha == contract["runtime_archive_sha256"], "RUNTIME_ARCHIVE_SHA256_MISMATCH")

    model_file = _regular_file(Path(model_path), "model_path")
    model_sha, model_size = _hash_file(model_file, "model_path")
    _need(model_sha == contract["model_sha256"], "MODEL_SHA256_MISMATCH")
    _need(model_size == contract["model_byte_count"], "MODEL_BYTE_COUNT_MISMATCH")

    root = Path(extraction_root)
    try:
        root_stat = root.lstat()
    except OSError as exc:
        raise LocalRuntimeMaterializationError(f"extraction_root:UNAVAILABLE:{exc.__class__.__name__}") from exc
    _need(stat.S_ISDIR(root_stat.st_mode), "extraction_root:DIRECTORY_REQUIRED")
    _need(not stat.S_ISLNK(root_stat.st_mode), "extraction_root:SYMLINK_FORBIDDEN")
    root = root.resolve(strict=True)

    binary_path, binary_id = _relative_file(root, runtime_binary_relative_path,
                                             "runtime_binary_relative_path", executable=True)
    _need(isinstance(dependency_relative_paths, Sequence) and not isinstance(dependency_relative_paths, (str, bytes)),
          "dependency_relative_paths:SEQUENCE_REQUIRED")
    normalized = [_text(value, "dependency_relative_path", 4096) for value in dependency_relative_paths]
    _need(len(normalized) == len(set(normalized)), "DEPENDENCY_RELATIVE_PATH_DUPLICATE")
    _need(runtime_binary_relative_path not in set(normalized), "RUNTIME_BINARY_MUST_NOT_REPEAT_AS_DEPENDENCY")

    observed = [_relative_file(root, relative, "dependency_relative_path") for relative in normalized]
    observed.sort(key=lambda item: item[1].relative_path)
    dependency_ids = tuple(item[1] for item in observed)
    dependency_paths = tuple(item[0] for item in observed)

    dependency_set_sha = _canonical_sha256({
        "schema": "HCU_LOCAL_RUNTIME_DEPENDENCY_SET/v1",
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "dependencies": [asdict(item) for item in dependency_ids],
    }, "RUNTIME_DEPENDENCY_SET")
    runtime_build_sha = _canonical_sha256({
        "schema": "HCU_LOCAL_RUNTIME_BUILD_IDENTITY/v1",
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "runtime_family": contract["runtime_family"],
        "runtime_build_tag": contract["runtime_build_tag"],
        "runtime_source_commit": contract["runtime_source_commit"],
        "runtime_platform": contract["runtime_platform"],
        "runtime_acceleration": contract["runtime_acceleration"],
        "runtime_archive_sha256": archive_sha,
        "runtime_binary": asdict(binary_id),
        "dependency_set_sha256": dependency_set_sha,
    }, "RUNTIME_BUILD_IDENTITY")

    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "runtime_family": contract["runtime_family"],
        "runtime_build_tag": contract["runtime_build_tag"],
        "runtime_source_commit": contract["runtime_source_commit"],
        "runtime_platform": contract["runtime_platform"],
        "runtime_acceleration": contract["runtime_acceleration"],
        "runtime_archive_asset": contract["runtime_archive_asset"],
        "runtime_archive_sha256": archive_sha,
        "runtime_archive_byte_count": archive_size,
        "runtime_binary": binary_id,
        "dependency_set_sha256": dependency_set_sha,
        "dependencies": dependency_ids,
        "runtime_build_sha256": runtime_build_sha,
        "model_repository": contract["model_repository"],
        "model_artifact": contract["model_artifact"],
        "model_sha256": model_sha,
        "model_byte_count": model_size,
    }
    provisional = LocalRuntimeMaterializationReceipt(**material, materialization_sha256="1" * 64)
    receipt = LocalRuntimeMaterializationReceipt(
        **material,
        materialization_sha256=_canonical_sha256(_receipt_material(provisional), "LOCAL_RUNTIME_MATERIALIZATION"),
    )
    return MaterializedRuntime(receipt=receipt, runtime_binary_path=binary_path,
                               dependency_paths=dependency_paths, model_path=model_file)


def verify_local_runtime_materialization_from_candidate_files(*, model_candidate_path: Path,
                                                                runtime_candidate_path: Path,
                                                                runtime_archive_path: Path,
                                                                extraction_root: Path,
                                                                runtime_binary_relative_path: str,
                                                                dependency_relative_paths: Sequence[str],
                                                                model_path: Path) -> MaterializedRuntime:
    return verify_local_runtime_materialization(
        model_candidate=_read_candidate(Path(model_candidate_path), "model_candidate_path"),
        runtime_candidate=_read_candidate(Path(runtime_candidate_path), "runtime_candidate_path"),
        runtime_archive_path=runtime_archive_path,
        extraction_root=extraction_root,
        runtime_binary_relative_path=runtime_binary_relative_path,
        dependency_relative_paths=dependency_relative_paths,
        model_path=model_path,
    )
