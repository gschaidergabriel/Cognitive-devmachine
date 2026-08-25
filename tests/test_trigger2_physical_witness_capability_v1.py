from __future__ import annotations

import errno
import os
import pickle
from pathlib import Path
from types import SimpleNamespace

import pytest

import tools.trigger2_physical_witness_capability_v1 as mod
from tools.trigger2_physical_witness_capability_v1 import (
    N,
    PhysicalWitnessError,
    mint_barrier_witness,
    mint_pidfd_getfd_barrier_witness,
    require_physical_witness,
    require_pidfd_getfd_witness,
    source_fixture_receipt,
)


def _ready():
    pid = 10_000
    return {f"x{i:02d}": {"pid": pid + i} for i in range(1, N + 1)}


def _predicates():
    return {
        "all_alive_at_barrier": True,
        "distinct_os_pids": N,
        "parent_child_pid_binding": True,
        "same_snapshot_identity": True,
        "all_transactions_open_at_barrier": True,
        "all_hold_readonly_s1_fd_at_barrier": True,
        "writer_free_identity_stable": True,
    }


def test_raw_all_true_mapping_is_rejected_before_physical_use():
    raw = {**_predicates(), "process_intervals_overlap_release": True}
    with pytest.raises(PhysicalWitnessError, match="^PHYSICAL_WITNESS_CAPABILITY_REQUIRED$"):
        require_physical_witness(raw)


def test_source_fixture_receipt_is_structurally_nonpromoting():
    receipt = source_fixture_receipt(state_delta=1, cohort_id="fixture")
    assert receipt["evidence_class"] == "SOURCE_FIXTURE_ONLY"
    assert receipt["physical_grid10_runtime_credit"] == 0
    assert receipt["model_runtime_credit"] == 0
    assert receipt["training_credit"] == 0
    assert receipt["canonical_truth"] is False
    assert receipt["effect_authority"] is False


def test_synthetic_flag_cannot_mint_even_before_pidfd_open():
    predicates = {
        **_predicates(),
        "process_intervals_overlap_release": True,
        "synthetic_source_fixture_only": True,
    }
    ready = _ready()
    with pytest.raises(
        PhysicalWitnessError,
        match="^SYNTHETIC_PROOF_CANNOT_MINT_PHYSICAL_WITNESS$",
    ):
        mint_barrier_witness(
            ready_by_node=ready,
            readonly_s1_fd_binding={
                node: [{"fd": 3, "flags": os.O_RDONLY, "mnt_id": 1, "ino": 7}]
                for node in ready
            },
            s1_file_identity={"dev": 1, "ino": 7},
            required_physical_predicates=predicates,
        )


def test_constructor_is_not_a_plain_serializable_data_contract():
    with pytest.raises(
        PhysicalWitnessError,
        match="^PHYSICAL_WITNESS_CONSTRUCTOR_FORBIDDEN$",
    ):
        mod.PhysicalCohortWitness({}, tuple(), "0" * 64, object())


def test_pickle_is_forbidden_for_a_minted_compat_shape(monkeypatch):
    fake_fds = iter(range(100, 100 + N))
    monkeypatch.setattr(mod, "_pidfd_supported", lambda: True)
    monkeypatch.setattr(mod.os, "pidfd_open", lambda pid, flags=0: next(fake_fds))
    monkeypatch.setattr(mod.os, "fstat", lambda fd: object())
    monkeypatch.setattr(mod.os, "close", lambda fd: None)

    predicates = {**_predicates(), "process_intervals_overlap_release": True}
    ready = _ready()
    witness = mint_barrier_witness(
        ready_by_node=ready,
        readonly_s1_fd_binding={
            node: [{"fd": 3, "flags": os.O_RDONLY, "mnt_id": 1, "ino": 7}]
            for node in ready
        },
        s1_file_identity={"dev": 1, "ino": 7},
        required_physical_predicates=predicates,
    )
    assert require_physical_witness(witness) is witness
    with pytest.raises(TypeError, match="PHYSICAL_COHORT_WITNESS_NOT_SERIALIZABLE"):
        pickle.dumps(witness)
    with pytest.raises(
        PhysicalWitnessError,
        match="^STRICT_PIDFD_GETFD_WITNESS_REQUIRED$",
    ):
        require_pidfd_getfd_witness(witness)


def _install_strict_fakes(monkeypatch, *, duplicate_ino=7, getfd_error=None):
    ready = _ready()
    parent = {node: row["pid"] for node, row in ready.items()}
    targets = {node: 40 + i for i, node in enumerate(sorted(ready))}
    pidfds = {pid: 1000 + i for i, pid in enumerate(parent.values())}
    duplicate_fds = {target: 2000 + i for i, target in enumerate(targets.values())}
    closed = []

    monkeypatch.setattr(mod, "_pidfd_supported", lambda: True)
    monkeypatch.setattr(mod.os, "open", lambda path, flags: 900)
    monkeypatch.setattr(mod.os, "pidfd_open", lambda pid, flags=0: pidfds[pid])

    def fake_getfd(pidfd, targetfd, flags=0):
        if getfd_error is not None:
            raise OSError(getfd_error, os.strerror(getfd_error))
        return duplicate_fds[targetfd]

    monkeypatch.setattr(mod, "_pidfd_getfd", fake_getfd)

    def fake_fstat(fd):
        if fd == 900:
            return SimpleNamespace(st_dev=1, st_ino=7)
        if fd in duplicate_fds.values():
            return SimpleNamespace(st_dev=1, st_ino=duplicate_ino)
        if fd in pidfds.values():
            return SimpleNamespace(st_dev=0, st_ino=0)
        raise OSError(errno.EBADF, "bad fd")

    monkeypatch.setattr(mod.os, "fstat", fake_fstat)
    monkeypatch.setattr(mod.fcntl, "fcntl", lambda fd, cmd: os.O_RDONLY)
    monkeypatch.setattr(mod.os, "close", lambda fd: closed.append(fd))
    return ready, parent, targets, pidfds, duplicate_fds, closed


def test_strict_mint_binds_parent_pid_and_actual_duplicated_s1(monkeypatch):
    ready, parent, targets, pidfds, duplicate_fds, closed = _install_strict_fakes(monkeypatch)
    witness = mint_pidfd_getfd_barrier_witness(
        ready_by_node=ready,
        parent_pid_by_node=parent,
        target_s1_fd_by_node=targets,
        s1_path=Path("/isolated/S1.sqlite"),
        required_physical_predicates=_predicates(),
    )
    assert require_pidfd_getfd_witness(witness) is witness
    assert witness.evidence["physical_binding_class"] == mod.STRICT_BINDING_CLASS
    assert witness.evidence["pre_release"] is True
    assert len(witness.evidence["pidfd_getfd_s1_binding"]) == N
    assert 900 in closed
    assert set(duplicate_fds.values()).issubset(closed)
    assert not set(pidfds.values()).intersection(closed)
    witness.close()
    assert set(pidfds.values()).issubset(closed)


def test_strict_mint_rejects_marker_parent_pid_mismatch_before_open(monkeypatch):
    ready = _ready()
    parent = {node: row["pid"] for node, row in ready.items()}
    parent[sorted(parent)[0]] += 99
    targets = {node: 3 for node in ready}
    calls = []
    monkeypatch.setattr(mod, "_pidfd_supported", lambda: True)
    monkeypatch.setattr(mod.os, "pidfd_open", lambda pid, flags=0: calls.append(pid))
    with pytest.raises(PhysicalWitnessError, match="^PARENT_CHILD_PID_BINDING_MISMATCH"):
        mint_pidfd_getfd_barrier_witness(
            ready_by_node=ready,
            parent_pid_by_node=parent,
            target_s1_fd_by_node=targets,
            s1_path="S1.sqlite",
            required_physical_predicates=_predicates(),
        )
    assert calls == []


def test_strict_mint_pidfd_getfd_eperm_fails_closed_without_fdinfo_fallback(monkeypatch):
    ready, parent, targets, pidfds, _, closed = _install_strict_fakes(
        monkeypatch,
        getfd_error=errno.EPERM,
    )
    with pytest.raises(PhysicalWitnessError, match="^PIDFD_GETFD_FAILED:.*:errno=1$"):
        mint_pidfd_getfd_barrier_witness(
            ready_by_node=ready,
            parent_pid_by_node=parent,
            target_s1_fd_by_node=targets,
            s1_path="S1.sqlite",
            required_physical_predicates=_predicates(),
        )
    assert 900 in closed
    assert next(iter(pidfds.values())) in closed


def test_strict_mint_rejects_wrong_s1_inode_and_closes_temporary_fds(monkeypatch):
    ready, parent, targets, pidfds, duplicate_fds, closed = _install_strict_fakes(
        monkeypatch,
        duplicate_ino=999,
    )
    with pytest.raises(PhysicalWitnessError, match="^PIDFD_GETFD_S1_IDENTITY_MISMATCH"):
        mint_pidfd_getfd_barrier_witness(
            ready_by_node=ready,
            parent_pid_by_node=parent,
            target_s1_fd_by_node=targets,
            s1_path="S1.sqlite",
            required_physical_predicates=_predicates(),
        )
    assert 900 in closed
    assert next(iter(duplicate_fds.values())) in closed
    assert next(iter(pidfds.values())) in closed
