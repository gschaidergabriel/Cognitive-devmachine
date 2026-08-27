#!/usr/bin/env python3
"""Trigger-2 V68 physical-cohort witness capability.

Source-only candidate primitive. It does not execute providers/models and does not mint
physical GRID10/HCU/EntityOS/training credit. Its purpose is to make physical-cohort
admission require a non-serializable OS-handle-bearing capability rather than a caller-
supplied JSON/dict of booleans.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from types import MappingProxyType
from typing import Any, Mapping, Sequence

SCHEMA = "TRIGGER2_PHYSICAL_COHORT_WITNESS/v1"
SOURCE = "spawn_held_cohort_barrier_observer"
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


def mint_barrier_witness(
    *,
    ready_by_node: Mapping[str, Mapping[str, Any]],
    readonly_s1_fd_binding: Mapping[str, Sequence[Mapping[str, int]]],
    s1_file_identity: Mapping[str, int],
    required_physical_predicates: Mapping[str, Any],
    source: str = SOURCE,
) -> PhysicalCohortWitness:
    """Mint only while the exact process handles can be opened at the barrier.

    Each readonly binding carries fd, flags, mnt_id and inode from /proc/<pid>/fdinfo.
    The integration path must populate these from the retained barrier observer and the
    actual S1 file, never from model narration or deterministic source fixtures.
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
