#!/usr/bin/env python3
"""Trigger-2 physical-cohort witness capability.

Source-only candidate primitive. It does not execute providers/models and does not mint
physical GRID10/HCU/EntityOS/training credit. Its purpose is to make physical-cohort
admission require a non-serializable OS-handle-bearing capability rather than a caller-
supplied JSON/dict of booleans.

The strict path additionally binds a held child process incarnation to the actual S1 file
descriptor by duplicating that descriptor through pidfd_getfd before barrier release.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
import fcntl
from hashlib import sha256
import json
import os
import platform
import sys
from types import MappingProxyType
from typing import Any, Mapping, Sequence

SCHEMA = "TRIGGER2_PHYSICAL_COHORT_WITNESS/v1"
SOURCE = "spawn_held_cohort_barrier_observer"
STRICT_BINDING_CLASS = "PIDFD_GETFD_OBSERVER_BOUND_PRE_RELEASE"
N = 10


class PhysicalWitnessError(RuntimeError):
    pass


def _cj(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _dg(value: Any) -> str:
    return sha256(_cj(value).encode("utf-8")).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PhysicalWitnessError(code)


_MINT = object()


@dataclass(frozen=True, slots=True)
class PhysicalCohortWitness:
    """Process-local capability carrying pidfds plus sealed physical evidence.

    This is a source/API authority boundary, not a cryptographic sandbox against hostile
    code in the same Python interpreter. The invariant is that JSON/mapping data alone is
    structurally insufficient for a future physical commit path.
    """

    _evidence: Mapping[str, Any]
    _pidfds: tuple[int, ...]
    witness_sha256: str
    _mint: object

    def __post_init__(self) -> None:
        _require(self._mint is _MINT, "PHYSICAL_WITNESS_CONSTRUCTOR_FORBIDDEN")

    @property
    def evidence(self) -> Mapping[str, Any]:
        return self._evidence

    @property
    def pidfds(self) -> tuple[int, ...]:
        return self._pidfds

    def __reduce__(self):
        raise TypeError("PHYSICAL_COHORT_WITNESS_NOT_SERIALIZABLE")

    def close(self) -> None:
        for fd in self._pidfds:
            try:
                os.close(fd)
            except OSError:
                pass


def _pidfd_supported() -> bool:
    return hasattr(os, "pidfd_open")


def _pidfd_getfd(pidfd: int, targetfd: int, flags: int = 0) -> int:
    """Duplicate targetfd from the pidfd-referenced task or fail closed.

    Python versions without os.pidfd_getfd use the Linux syscall directly only on the two
    Ubuntu architectures explicitly admitted here. Unknown platforms/architectures are not
    guessed and therefore cannot silently degrade to caller-supplied fd metadata.
    """
    high_level = getattr(os, "pidfd_getfd", None)
    if high_level is not None:
        return int(high_level(pidfd, targetfd, flags))
    if sys.platform != "linux":
        raise PhysicalWitnessError("PIDFD_GETFD_UNSUPPORTED_PLATFORM")
    machine = platform.machine().lower()
    syscall_number = {
        "x86_64": 438,
        "amd64": 438,
        "aarch64": 438,
        "arm64": 438,
    }.get(machine)
    if syscall_number is None:
        raise PhysicalWitnessError(f"PIDFD_GETFD_UNSUPPORTED_ARCH:{machine}")
    libc = ctypes.CDLL(None, use_errno=True)
    syscall = libc.syscall
    syscall.restype = ctypes.c_long
    rc = syscall(
        ctypes.c_long(syscall_number),
        ctypes.c_int(pidfd),
        ctypes.c_int(targetfd),
        ctypes.c_uint(flags),
    )
    if rc < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return int(rc)


def _require_pre_release_predicates(required_physical_predicates: Mapping[str, Any]) -> None:
    for key in (
        "all_alive_at_barrier",
        "parent_child_pid_binding",
        "same_snapshot_identity",
        "all_transactions_open_at_barrier",
        "all_hold_readonly_s1_fd_at_barrier",
        "writer_free_identity_stable",
    ):
        _require(
            required_physical_predicates.get(key) is True,
            f"PHYSICAL_PREDICATE_FALSE:{key}",
        )
    _require(required_physical_predicates.get("distinct_os_pids") == N, "PHYSICAL_PID_COUNT_INVALID")
    _require(
        required_physical_predicates.get("synthetic_source_fixture_only") is not True,
        "SYNTHETIC_PROOF_CANNOT_MINT_PHYSICAL_WITNESS",
    )


def mint_pidfd_getfd_barrier_witness(
    *,
    ready_by_node: Mapping[str, Mapping[str, Any]],
    parent_pid_by_node: Mapping[str, int],
    target_s1_fd_by_node: Mapping[str, int],
    s1_path: os.PathLike[str] | str,
    required_physical_predicates: Mapping[str, Any],
    source: str = SOURCE,
) -> PhysicalCohortWitness:
    """Mint strict physical evidence while the exact held cohort is still alive.

    The caller may identify the numeric target fd, but cannot mint the S1 binding from fdinfo
    rows. This boundary opens a pidfd for the exact parent-owned child PID, duplicates the
    child's target fd with pidfd_getfd, then independently checks the duplicate's device,
    inode and access mode against an observer-opened canonical S1 descriptor. Every temporary
    duplicate is closed before return; pidfds remain owned by the witness through release.
    """
    _require(source == SOURCE, "PHYSICAL_WITNESS_SOURCE_INVALID")
    _require(_pidfd_supported(), "PIDFD_UNAVAILABLE")
    _require(len(ready_by_node) == N, "PHYSICAL_WITNESS_NODE_COUNT_INVALID")
    _require_pre_release_predicates(required_physical_predicates)

    nodes = sorted(ready_by_node)
    _require(set(nodes) == set(parent_pid_by_node), "PARENT_PID_NODE_SET_MISMATCH")
    _require(set(nodes) == set(target_s1_fd_by_node), "TARGET_FD_NODE_SET_MISMATCH")

    pids: list[int] = []
    for node in nodes:
        marker_pid = int(ready_by_node[node]["pid"])
        parent_pid = int(parent_pid_by_node[node])
        _require(marker_pid == parent_pid, f"PARENT_CHILD_PID_BINDING_MISMATCH:{node}")
        pids.append(parent_pid)
    _require(len(set(pids)) == N, "PHYSICAL_WITNESS_DUPLICATE_PID")

    canonical_fd = -1
    pidfds: list[int] = []
    bindings: dict[str, dict[str, int]] = {}
    try:
        canonical_fd = os.open(os.fspath(s1_path), os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        canonical_stat = os.fstat(canonical_fd)
        canonical_dev = int(canonical_stat.st_dev)
        canonical_ino = int(canonical_stat.st_ino)

        for node, pid in zip(nodes, pids, strict=True):
            target_fd = int(target_s1_fd_by_node[node])
            _require(target_fd >= 0, f"S1_TARGET_FD_INVALID:{node}")
            try:
                pidfd = os.pidfd_open(pid, 0)
            except OSError as exc:
                raise PhysicalWitnessError(
                    f"PIDFD_OPEN_FAILED:{node}:errno={exc.errno}"
                ) from exc
            pidfds.append(pidfd)

            duplicate_fd = -1
            try:
                try:
                    duplicate_fd = _pidfd_getfd(pidfd, target_fd, 0)
                except PhysicalWitnessError:
                    raise
                except OSError as exc:
                    raise PhysicalWitnessError(
                        f"PIDFD_GETFD_FAILED:{node}:errno={exc.errno}"
                    ) from exc
                duplicate_stat = os.fstat(duplicate_fd)
                flags = int(fcntl.fcntl(duplicate_fd, fcntl.F_GETFL))
                _require(
                    int(duplicate_stat.st_dev) == canonical_dev
                    and int(duplicate_stat.st_ino) == canonical_ino,
                    f"PIDFD_GETFD_S1_IDENTITY_MISMATCH:{node}",
                )
                _require(
                    (flags & os.O_ACCMODE) == os.O_RDONLY,
                    f"PIDFD_GETFD_S1_NOT_READONLY:{node}",
                )
                bindings[node] = {
                    "pid": pid,
                    "target_fd": target_fd,
                    "dev": int(duplicate_stat.st_dev),
                    "ino": int(duplicate_stat.st_ino),
                    "flags": flags,
                }
            finally:
                if duplicate_fd >= 0:
                    try:
                        os.close(duplicate_fd)
                    except OSError:
                        pass

        evidence = {
            "schema": SCHEMA,
            "source": source,
            "physical_binding_class": STRICT_BINDING_CLASS,
            "pre_release": True,
            "nodes": nodes,
            "pids": pids,
            "ready_by_node": {node: dict(ready_by_node[node]) for node in nodes},
            "pidfd_getfd_s1_binding": bindings,
            "s1_file_identity": {"dev": canonical_dev, "ino": canonical_ino},
            "required_physical_predicates": {
                key: required_physical_predicates[key]
                for key in sorted(required_physical_predicates)
            },
            "nonserializable_pidfd_capability_count": len(pidfds),
        }
        digest = _dg(evidence)
        return PhysicalCohortWitness(
            MappingProxyType(evidence),
            tuple(pidfds),
            digest,
            _MINT,
        )
    except Exception:
        for fd in pidfds:
            try:
                os.close(fd)
            except OSError:
                pass
        raise
    finally:
        if canonical_fd >= 0:
            try:
                os.close(canonical_fd)
            except OSError:
                pass


def mint_barrier_witness(
    *,
    ready_by_node: Mapping[str, Mapping[str, Any]],
    readonly_s1_fd_binding: Mapping[str, Sequence[Mapping[str, int]]],
    s1_file_identity: Mapping[str, int],
    required_physical_predicates: Mapping[str, Any],
    source: str = SOURCE,
) -> PhysicalCohortWitness:
    """Compatibility mint for existing caller-observed fdinfo evidence.

    This remains intentionally weaker than mint_pidfd_getfd_barrier_witness and must not be
    accepted by a future strict physical commit path merely because it carries pidfds.
    """
    _require(source == SOURCE, "PHYSICAL_WITNESS_SOURCE_INVALID")
    _require(_pidfd_supported(), "PIDFD_UNAVAILABLE")
    _require(len(ready_by_node) == N, "PHYSICAL_WITNESS_NODE_COUNT_INVALID")

    required_true = (
        "all_alive_at_barrier",
        "parent_child_pid_binding",
        "same_snapshot_identity",
        "all_transactions_open_at_barrier",
        "all_hold_readonly_s1_fd_at_barrier",
        "writer_free_identity_stable",
        "process_intervals_overlap_release",
    )
    for key in required_true:
        _require(required_physical_predicates.get(key) is True, f"PHYSICAL_PREDICATE_FALSE:{key}")
    _require(required_physical_predicates.get("distinct_os_pids") == N, "PHYSICAL_PID_COUNT_INVALID")
    _require(
        required_physical_predicates.get("synthetic_source_fixture_only") is not True,
        "SYNTHETIC_PROOF_CANNOT_MINT_PHYSICAL_WITNESS",
    )

    nodes = sorted(ready_by_node)
    pids = [int(ready_by_node[node]["pid"]) for node in nodes]
    _require(len(set(pids)) == N, "PHYSICAL_WITNESS_DUPLICATE_PID")

    s1_ino = int(s1_file_identity.get("ino", -1))
    _require(s1_ino >= 0, "S1_FILE_INODE_REQUIRED")
    _require(int(s1_file_identity.get("dev", -1)) >= 0, "S1_FILE_DEVICE_REQUIRED")

    normalized_fd_binding: dict[str, list[dict[str, int]]] = {}
    pidfds: list[int] = []
    try:
        for node, pid in zip(nodes, pids, strict=True):
            rows = list(readonly_s1_fd_binding.get(node, ()))
            _require(bool(rows), f"S1_FD_BINDING_MISSING:{node}")
            normalized_rows: list[dict[str, int]] = []
            for row in rows:
                flags = int(row["flags"])
                _require((flags & os.O_ACCMODE) == os.O_RDONLY, f"S1_FD_NOT_READONLY:{node}")
                _require(int(row["ino"]) == s1_ino, f"S1_FD_INODE_MISMATCH:{node}")
                normalized_rows.append(
                    {
                        "fd": int(row["fd"]),
                        "flags": flags,
                        "mnt_id": int(row["mnt_id"]),
                        "ino": int(row["ino"]),
                    }
                )
            normalized_fd_binding[node] = sorted(normalized_rows, key=lambda item: item["fd"])
            pidfds.append(os.pidfd_open(pid, 0))

        evidence = {
            "schema": SCHEMA,
            "source": source,
            "physical_binding_class": "CALLER_FDINFO_COMPAT_ONLY",
            "nodes": nodes,
            "pids": pids,
            "ready_by_node": {node: dict(ready_by_node[node]) for node in nodes},
            "readonly_s1_fd_binding": normalized_fd_binding,
            "s1_file_identity": {"dev": int(s1_file_identity["dev"]), "ino": s1_ino},
            "required_physical_predicates": {
                key: required_physical_predicates[key]
                for key in sorted(required_physical_predicates)
            },
            "nonserializable_pidfd_capability_count": len(pidfds),
        }
        digest = _dg(evidence)
        return PhysicalCohortWitness(
            MappingProxyType(evidence),
            tuple(pidfds),
            digest,
            _MINT,
        )
    except Exception:
        for fd in pidfds:
            try:
                os.close(fd)
            except OSError:
                pass
        raise


def require_physical_witness(value: Any) -> PhysicalCohortWitness:
    """Fail closed before physical-cohort mutation on raw/synthetic mappings."""
    _require(isinstance(value, PhysicalCohortWitness), "PHYSICAL_WITNESS_CAPABILITY_REQUIRED")
    expected = _dg(dict(value.evidence))
    _require(value.witness_sha256 == expected, "PHYSICAL_WITNESS_DIGEST_MISMATCH")
    _require(len(value.pidfds) == N, "PHYSICAL_WITNESS_PIDFD_COUNT_INVALID")
    for fd in value.pidfds:
        try:
            os.fstat(fd)
        except OSError as exc:
            raise PhysicalWitnessError("PHYSICAL_WITNESS_PIDFD_INVALID") from exc
    return value


def require_pidfd_getfd_witness(value: Any) -> PhysicalCohortWitness:
    """Require the strict pre-release observer-bound physical evidence class."""
    witness = require_physical_witness(value)
    _require(
        witness.evidence.get("physical_binding_class") == STRICT_BINDING_CLASS,
        "STRICT_PIDFD_GETFD_WITNESS_REQUIRED",
    )
    _require(witness.evidence.get("pre_release") is True, "STRICT_WITNESS_NOT_PRE_RELEASE")
    _require(
        len(witness.evidence.get("pidfd_getfd_s1_binding", {})) == N,
        "STRICT_WITNESS_BINDING_COUNT_INVALID",
    )
    return witness


def source_fixture_receipt(*, state_delta: int, cohort_id: str) -> dict[str, Any]:
    """Receipt shape for deterministic source-fixture persistence tests only."""
    _require(state_delta in (0, 1), "SOURCE_FIXTURE_STATE_DELTA_INVALID")
    return {
        "schema": "TRIGGER2_SOURCE_FIXTURE_COMMIT_RECEIPT/v1",
        "cohort_id": cohort_id,
        "state_delta": state_delta,
        "evidence_class": "SOURCE_FIXTURE_ONLY",
        "physical_grid10_runtime_credit": 0,
        "model_runtime_credit": 0,
        "training_credit": 0,
        "canonical_truth": False,
        "effect_authority": False,
    }
