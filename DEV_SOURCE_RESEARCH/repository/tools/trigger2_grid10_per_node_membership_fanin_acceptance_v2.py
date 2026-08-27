#!/usr/bin/env python3
"""Trigger-2 per-node membership-bound atomic cohort fan-in acceptance v2.

This successor replaces the over-broad/under-sensitive global membership clock in
trigger2_grid10_atomic_cohort_fanin_pilot_v1 with deterministic per-node admission
revisions. It is source/component evidence only: no physical GRID10, HCU, EntityOS,
J-Space, canonical-truth, effect, dataset, checkpoint, or training credit is minted.

Selected invariants:
- every runtime registration creates a successor admission revision even when the
  visible node tuple is unchanged;
- unrelated node registration does not stale an otherwise unchanged cohort;
- every NODE_RESULT is bound to one current per-node admission id/revision;
- optional process-instance witnesses are deterministic-fabric-owned and admission-bound;
- all source authority checks occur before admitted_results/S1 mutation and are
  rechecked under the writer lock;
- cohort identity is canonicalized by packet digest, not transport arrival order;
- one accepted cohort advances S1 exactly once while preserving packet digests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping

from xeno_self_organizing_fabric_acceptance_v1 import (
    Fabric,
    FabricError,
    RESULT_SCHEMA,
    cj,
    dg,
)

SCHEMA = "TRIGGER2_GRID10_PER_NODE_MEMBERSHIP_FANIN_ACCEPTANCE/v2"
MEMBERSHIP_SCHEMA = "GRID_NODE_MEMBERSHIP_ADMISSION/v2"
PROCESS_WITNESS_SCHEMA = "GRID_NODE_PROCESS_WITNESS/v1"
COHORT_RECEIPT_SCHEMA = "GRID_COHORT_FANIN_RECEIPT/v2"


class PerNodeMembershipCohortFabric(Fabric):
    """Atomic cohort fan-in with deterministic per-node membership authority."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.con.executescript(
            """
            CREATE TABLE node_membership_admissions(
              admission_id TEXT PRIMARY KEY,
              node_id TEXT NOT NULL,
              revision INTEGER NOT NULL,
              capability TEXT NOT NULL,
              generation INTEGER NOT NULL,
              valid INTEGER NOT NULL,
              healthy INTEGER NOT NULL,
              UNIQUE(node_id, revision)
            );
            CREATE INDEX node_membership_active
              ON node_membership_admissions(node_id, valid, revision);

            CREATE TABLE node_process_witnesses(
              witness_id TEXT PRIMARY KEY,
              admission_id TEXT NOT NULL,
              node_id TEXT NOT NULL,
              pid INTEGER NOT NULL,
              serial INTEGER NOT NULL,
              valid INTEGER NOT NULL,
              UNIQUE(admission_id, serial)
            );
            CREATE INDEX node_process_witness_active
              ON node_process_witnesses(admission_id, valid, serial);
            """
        )

    def runtime_register_node(self, node_id: str, capability: str) -> dict[str, Any]:
        # Deterministic runtime authority; every registration/rejoin creates a new
        # per-node revision, even when capability/health are byte-identical.
        prior = self.con.execute(
            "SELECT COALESCE(MAX(revision),0) AS n "
            "FROM node_membership_admissions WHERE node_id=?",
            (node_id,),
        ).fetchone()
        revision = int(prior["n"]) + 1
        generation = self._int("generation")

        super().runtime_register_node(node_id, capability)
        self.con.execute(
            "UPDATE node_membership_admissions SET valid=0 "
            "WHERE node_id=? AND valid=1",
            (node_id,),
        )
        self.con.execute(
            "UPDATE node_process_witnesses SET valid=0 "
            "WHERE node_id=? AND valid=1",
            (node_id,),
        )
        admission_id = "member-" + dg(
            {
                "schema": MEMBERSHIP_SCHEMA,
                "node_id": node_id,
                "revision": revision,
                "capability": capability,
                "generation": generation,
            }
        )[:32]
        self.con.execute(
            "INSERT INTO node_membership_admissions "
            "(admission_id,node_id,revision,capability,generation,valid,healthy) "
            "VALUES(?,?,?,?,?,1,1)",
            (admission_id, node_id, revision, capability, generation),
        )
        return {
            "schema": MEMBERSHIP_SCHEMA,
            "admission_id": admission_id,
            "node_id": node_id,
            "revision": revision,
            "capability": capability,
            "generation": generation,
            "healthy": True,
        }

    def runtime_set_health(self, node_id: str, healthy: bool) -> None:
        active = self._active_membership_row(node_id)
        super().runtime_set_health(node_id, healthy)
        self.con.execute(
            "UPDATE node_membership_admissions SET healthy=? "
            "WHERE admission_id=? AND valid=1",
            (1 if healthy else 0, active["admission_id"]),
        )

    def _active_membership_row(self, node_id: str) -> Mapping[str, Any]:
        row = self.con.execute(
            "SELECT * FROM node_membership_admissions "
            "WHERE node_id=? AND valid=1 ORDER BY revision DESC LIMIT 1",
            (node_id,),
        ).fetchone()
        if row is None:
            raise FabricError("NODE_MEMBERSHIP_NOT_FOUND")
        return row

    def active_membership(self, node_id: str) -> dict[str, Any]:
        row = self._active_membership_row(node_id)
        return {
            "schema": MEMBERSHIP_SCHEMA,
            "admission_id": row["admission_id"],
            "node_id": row["node_id"],
            "revision": int(row["revision"]),
            "capability": row["capability"],
            "generation": int(row["generation"]),
            "healthy": int(row["healthy"]) == 1,
        }

    def runtime_bind_process(
        self, *, node_id: str, admission_id: str, pid: int
    ) -> dict[str, Any]:
        membership = self._membership_row(admission_id)
        if membership["node_id"] != node_id or int(membership["valid"]) != 1:
            raise FabricError("PROCESS_WITNESS_MEMBERSHIP_INVALID")
        active = self._active_membership_row(node_id)
        if active["admission_id"] != admission_id:
            raise FabricError("PROCESS_WITNESS_MEMBERSHIP_SUPERSEDED")
        prior = self.con.execute(
            "SELECT COALESCE(MAX(serial),0) AS n FROM node_process_witnesses "
            "WHERE admission_id=?",
            (admission_id,),
        ).fetchone()
        serial = int(prior["n"]) + 1
        self.con.execute(
            "UPDATE node_process_witnesses SET valid=0 "
            "WHERE admission_id=? AND valid=1",
            (admission_id,),
        )
        witness_id = "proc-" + dg(
            {
                "schema": PROCESS_WITNESS_SCHEMA,
                "admission_id": admission_id,
                "node_id": node_id,
                "pid": int(pid),
                "serial": serial,
            }
        )[:32]
        self.con.execute(
            "INSERT INTO node_process_witnesses VALUES(?,?,?,?,?,1)",
            (witness_id, admission_id, node_id, int(pid), serial),
        )
        return {
            "schema": PROCESS_WITNESS_SCHEMA,
            "witness_id": witness_id,
            "admission_id": admission_id,
            "node_id": node_id,
            "pid": int(pid),
            "serial": serial,
        }

    def _membership_row(self, admission_id: str) -> Mapping[str, Any]:
        row = self.con.execute(
            "SELECT * FROM node_membership_admissions WHERE admission_id=?",
            (admission_id,),
        ).fetchone()
        if row is None:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_UNKNOWN")
        return row

    def result_packet(
        self,
        *,
        node_id: str,
        snapshot: Any,
        membership: Mapping[str, Any],
        scope: str,
        payload: Any,
        process_witness: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        # This wrapper is deterministic fabric work. A model does not mint authority ids.
        core = {
            "schema": RESULT_SCHEMA,
            "source_kind": "ORDINARY_NODE",
            "source_node_id": node_id,
            "source_node_admission_id": membership["admission_id"],
            "source_node_admission_revision": int(membership["revision"]),
            "source_process_witness_id": (
                None if process_witness is None else process_witness["witness_id"]
            ),
            "scope": scope,
            "generation": snapshot.generation,
            "state_epoch": snapshot.epoch,
            "state_digest": snapshot.state_digest,
            "payload": payload,
        }
        return {**core, "packet_digest": dg(core), "s1_write_intent": False}

    def _verify_membership_binding(
        self, packet: Mapping[str, Any], *, require_process_witness: bool
    ) -> None:
        node_id = packet.get("source_node_id")
        admission_id = packet.get("source_node_admission_id")
        revision = packet.get("source_node_admission_revision")
        if not isinstance(node_id, str) or not node_id:
            raise FabricError("RESULT_SOURCE_NODE_ID_INVALID")
        if not isinstance(admission_id, str) or not admission_id:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_REQUIRED")
        if not isinstance(revision, int):
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_REVISION_INVALID")

        membership = self._membership_row(admission_id)
        if membership["node_id"] != node_id:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_NODE_MISMATCH")
        if int(membership["revision"]) != revision:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_REVISION_MISMATCH")
        if int(membership["valid"]) != 1:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_SUPERSEDED")
        if int(membership["generation"]) != self._int("generation"):
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_STALE_GENERATION")
        if int(membership["healthy"]) != 1:
            raise FabricError("RESULT_SOURCE_NODE_UNHEALTHY")

        active = self._active_membership_row(node_id)
        if (
            active["admission_id"] != admission_id
            or int(active["revision"]) != revision
        ):
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_SUPERSEDED")

        node = self.con.execute(
            "SELECT capability,healthy FROM nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        if node is None:
            raise FabricError("RESULT_SOURCE_NODE_UNREGISTERED")
        if int(node["healthy"]) != 1:
            raise FabricError("RESULT_SOURCE_NODE_UNHEALTHY")
        if node["capability"] != membership["capability"]:
            raise FabricError("RESULT_SOURCE_CAPABILITY_MEMBERSHIP_MISMATCH")

        witness_id = packet.get("source_process_witness_id")
        if require_process_witness and (
            not isinstance(witness_id, str) or not witness_id
        ):
            raise FabricError("RESULT_SOURCE_PROCESS_WITNESS_REQUIRED")
        if witness_id is not None:
            witness = self.con.execute(
                "SELECT * FROM node_process_witnesses WHERE witness_id=?",
                (witness_id,),
            ).fetchone()
            if witness is None:
                raise FabricError("RESULT_SOURCE_PROCESS_WITNESS_UNKNOWN")
            if (
                witness["admission_id"] != admission_id
                or witness["node_id"] != node_id
                or int(witness["valid"]) != 1
            ):
                raise FabricError("RESULT_SOURCE_PROCESS_WITNESS_INVALID")

    def _validate_cohort_packet(
        self,
        packet: dict[str, Any],
        *,
        current: Any,
        scope: str,
        require_process_witness: bool,
    ) -> None:
        if packet.get("schema") != RESULT_SCHEMA:
            raise FabricError("COHORT_PACKET_SCHEMA_INVALID")
        if packet.get("source_kind") != "ORDINARY_NODE":
            raise FabricError("COHORT_SOURCE_KIND_INVALID")
        if packet.get("scope") != scope:
            raise FabricError("COHORT_SCOPE_MISMATCH")
        if packet.get("generation") != current.generation:
            raise FabricError("COHORT_STALE_GENERATION")
        if packet.get("state_epoch") != current.epoch:
            raise FabricError("COHORT_STALE_EPOCH")
        if packet.get("state_digest") != current.state_digest:
            raise FabricError("COHORT_STALE_DIGEST")
        if packet.get("s1_write_intent") is not False:
            raise FabricError("COHORT_SOURCE_PACKET_MUST_NOT_SELF_WRITE")
        core = {
            k: packet[k]
            for k in packet
            if k not in ("packet_digest", "s1_write_intent")
        }
        if packet.get("packet_digest") != dg(core):
            raise FabricError("COHORT_PACKET_DIGEST_MISMATCH")
        self._verify_membership_binding(
            packet, require_process_witness=require_process_witness
        )
        if self.con.execute(
            "SELECT 1 FROM admitted_results WHERE result_digest=?",
            (packet["packet_digest"],),
        ).fetchone():
            raise FabricError("DUPLICATE_RESULT_REJECTED")

    def _authority_vector(
        self, packets: list[Mapping[str, Any]]
    ) -> tuple[tuple[str, str, int, str | None], ...]:
        return tuple(
            sorted(
                (
                    str(p["source_node_id"]),
                    str(p["source_node_admission_id"]),
                    int(p["source_node_admission_revision"]),
                    (
                        None
                        if p.get("source_process_witness_id") is None
                        else str(p["source_process_witness_id"])
                    ),
                )
                for p in packets
            )
        )

    def coordinator_commit_cohort(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packets: list[dict[str, Any]],
        expected_epoch: int,
        expected_digest: str,
        expected_authority_vector: tuple[
            tuple[str, str, int, str | None], ...
        ],
        require_process_witness: bool = False,
    ) -> dict[str, Any]:
        if len(packets) < 2:
            raise FabricError("COHORT_REQUIRES_MULTIPLE_PACKETS")
        scopes = {str(p.get("scope")) for p in packets}
        if len(scopes) != 1:
            raise FabricError("COHORT_SCOPE_MISMATCH")
        scope = next(iter(scopes))

        self._lease_row(lease, token, scope)
        current = self.snapshot()
        if expected_epoch != current.epoch or expected_digest != current.state_digest:
            raise FabricError("S1_COMPARE_AND_SWAP_FAILED")

        actual_authority_vector = self._authority_vector(packets)
        if actual_authority_vector != expected_authority_vector:
            raise FabricError("COHORT_SOURCE_AUTHORITY_VECTOR_MISMATCH")

        packet_digests = [str(p.get("packet_digest")) for p in packets]
        if len(set(packet_digests)) != len(packet_digests):
            raise FabricError("COHORT_DUPLICATE_PACKET")
        source_ids = [str(p.get("source_node_id")) for p in packets]
        if len(set(source_ids)) != len(source_ids):
            raise FabricError("COHORT_DUPLICATE_SOURCE_NODE")

        for packet in packets:
            self._validate_cohort_packet(
                packet,
                current=current,
                scope=scope,
                require_process_witness=require_process_witness,
            )

        canonical_packets = sorted(packets, key=lambda p: str(p["packet_digest"]))
        canonical_digests = [str(p["packet_digest"]) for p in canonical_packets]
        authority_vector = self._authority_vector(canonical_packets)
        cohort_core = {
            "base_generation": current.generation,
            "base_epoch": current.epoch,
            "base_state_digest": current.state_digest,
            "scope": scope,
            "source_authority_vector": authority_vector,
            "packet_digests": canonical_digests,
        }
        cohort_digest = dg(cohort_core)

        self.con.execute("BEGIN IMMEDIATE")
        try:
            if self._int("epoch") != expected_epoch:
                raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
            locked = self.snapshot()
            if locked.state_digest != expected_digest:
                raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
            # Membership/process authority is rechecked under the write lock.
            for packet in canonical_packets:
                self._verify_membership_binding(
                    packet, require_process_witness=require_process_witness
                )

            row = self.con.execute(
                "SELECT * FROM scopes WHERE scope=?", (scope,)
            ).fetchone()
            if row is None:
                raise FabricError("UNKNOWN_SCOPE")
            merged = {
                "previous": json.loads(row["summary_json"]),
                "latest_cohort": {
                    "schema": COHORT_RECEIPT_SCHEMA,
                    "cohort_digest": cohort_digest,
                    "base_generation": current.generation,
                    "base_epoch": current.epoch,
                    "base_state_digest": current.state_digest,
                    "source_authority_vector": authority_vector,
                    "evidence_packet_digests": canonical_digests,
                    "payloads": [p["payload"] for p in canonical_packets],
                },
                "source_schema": RESULT_SCHEMA,
            }
            new_epoch = expected_epoch + 1
            self.con.execute(
                "UPDATE scopes SET summary_json=?,evidence_count=evidence_count+?,"
                "last_writer_lease_id=?,last_result_digest=?,state_epoch=? WHERE scope=?",
                (
                    cj(merged),
                    len(canonical_packets),
                    lease["lease_id"],
                    cohort_digest,
                    new_epoch,
                    scope,
                ),
            )
            for packet in canonical_packets:
                self.con.execute(
                    "INSERT INTO admitted_results VALUES(?,?,?,?,?)",
                    (
                        packet["packet_digest"],
                        packet["source_node_id"],
                        lease["lease_id"],
                        scope,
                        new_epoch,
                    ),
                )
            self._set("epoch", str(new_epoch))
            self.con.execute("COMMIT")
        except Exception:
            self.con.execute("ROLLBACK")
            raise

        return {
            "schema": COHORT_RECEIPT_SCHEMA,
            "cohort_digest": cohort_digest,
            "scope": scope,
            "packet_digests": canonical_digests,
            "source_authority_vector": authority_vector,
            "base_epoch": current.epoch,
            "new_epoch": new_epoch,
            "canonical_truth": False,
            "effect_authority": False,
        }


def expect_error(fn: Any, expected: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == expected
    return False


def _seed(
    f: PerNodeMembershipCohortFabric, node_ids: tuple[str, ...] = ("x01", "x02")
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], str]:
    memberships = {
        node: f.runtime_register_node(node, "reason") for node in node_ids
    }
    f.seed_scope("branch:a")
    f.seed_task("t01", "branch:a", 100, "reason", {"q": 1})
    f.seed_task("t02", "branch:a", 99, "reason", {"q": 2})
    lease, token = f.elect_coordinator("branch:a")
    return memberships, lease, token


def _make_packets(
    f: PerNodeMembershipCohortFabric,
    memberships: Mapping[str, Mapping[str, Any]],
    *,
    with_process_witness: bool = False,
) -> tuple[Any, list[dict[str, Any]]]:
    snap = f.snapshot()
    packets: list[dict[str, Any]] = []
    for i, node_id in enumerate(("x01", "x02"), start=1):
        witness = (
            f.runtime_bind_process(
                node_id=node_id,
                admission_id=str(memberships[node_id]["admission_id"]),
                pid=4000 + i,
            )
            if with_process_witness
            else None
        )
        packets.append(
            f.result_packet(
                node_id=node_id,
                snapshot=snap,
                membership=memberships[node_id],
                process_witness=witness,
                scope="branch:a",
                payload={"answer": node_id, "evidence": [f"e{i}"]},
            )
        )
    return snap, packets


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}

    # Positive control: exact per-node authority vector, one atomic S1 transition.
    with tempfile.TemporaryDirectory(prefix="t2-pernode-positive-") as td:
        f = PerNodeMembershipCohortFabric(Path(td) / "f.sqlite")
        try:
            memberships, lease, token = _seed(f)
            snap, packets = _make_packets(f, memberships)
            vector = f._authority_vector(packets)
            receipt = f.coordinator_commit_cohort(
                lease=lease,
                token=token,
                packets=packets,
                expected_epoch=snap.epoch,
                expected_digest=snap.state_digest,
                expected_authority_vector=vector,
            )
            tests["P1_PER_NODE_AUTHORITY_ATOMIC_FANIN"] = (
                receipt["new_epoch"] == snap.epoch + 1
                and set(receipt["packet_digests"])
                == {p["packet_digest"] for p in packets}
            )
        finally:
            f.close()

    # Negative A: same visible state re-registration must stale only x01's old admission.
    with tempfile.TemporaryDirectory(prefix="t2-pernode-reregister-") as td:
        f = PerNodeMembershipCohortFabric(Path(td) / "f.sqlite")
        try:
            memberships, lease, token = _seed(f)
            snap, packets = _make_packets(f, memberships)
            old_revision = memberships["x01"]["revision"]
            replacement = f.runtime_register_node("x01", "reason")
            tests["P2_SAME_STATE_REREGISTRATION_ADVANCES_PER_NODE_REVISION"] = (
                replacement["revision"] == old_revision + 1
            )
            tests["P2_OLD_ADMISSION_REJECTED_AFTER_SAME_STATE_REREGISTRATION"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=packets,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                    expected_authority_vector=f._authority_vector(packets),
                ),
                "RESULT_SOURCE_MEMBERSHIP_SUPERSEDED",
            )
        finally:
            f.close()

    # Negative/control B: unrelated x11 registration must NOT stale x01/x02.
    with tempfile.TemporaryDirectory(prefix="t2-pernode-unrelated-") as td:
        f = PerNodeMembershipCohortFabric(Path(td) / "f.sqlite")
        try:
            memberships, lease, token = _seed(f)
            snap, packets = _make_packets(f, memberships)
            f.runtime_register_node("x11", "reason")
            receipt = f.coordinator_commit_cohort(
                lease=lease,
                token=token,
                packets=packets,
                expected_epoch=snap.epoch,
                expected_digest=snap.state_digest,
                expected_authority_vector=f._authority_vector(packets),
            )
            tests["P3_UNRELATED_MEMBERSHIP_CHANGE_NO_FALSE_COHORT_STALENESS"] = (
                receipt["new_epoch"] == snap.epoch + 1
            )
        finally:
            f.close()

    # Negative C: transplant x01 semantics onto x02 authority identity must fail.
    with tempfile.TemporaryDirectory(prefix="t2-pernode-transplant-") as td:
        f = PerNodeMembershipCohortFabric(Path(td) / "f.sqlite")
        try:
            memberships, lease, token = _seed(f)
            snap, packets = _make_packets(f, memberships)
            forged = dict(packets[0])
            forged["source_node_admission_id"] = memberships["x02"]["admission_id"]
            forged["source_node_admission_revision"] = memberships["x02"]["revision"]
            core = {
                k: forged[k]
                for k in forged
                if k not in ("packet_digest", "s1_write_intent")
            }
            forged["packet_digest"] = dg(core)
            mixed = [forged, packets[1]]
            tests["P4_LOGICAL_NODE_ADMISSION_TRANSPLANT_REJECTED"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=mixed,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                    expected_authority_vector=f._authority_vector(mixed),
                ),
                "RESULT_SOURCE_MEMBERSHIP_NODE_MISMATCH",
            )
        finally:
            f.close()

    # Negative D: process witness is admission-bound and superseded by re-registration.
    with tempfile.TemporaryDirectory(prefix="t2-pernode-process-") as td:
        f = PerNodeMembershipCohortFabric(Path(td) / "f.sqlite")
        try:
            memberships, lease, token = _seed(f)
            snap, packets = _make_packets(
                f, memberships, with_process_witness=True
            )
            f.runtime_register_node("x01", "reason")
            tests["P5_PROCESS_WITNESS_SUPERSEDED_WITH_ADMISSION"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=packets,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                    expected_authority_vector=f._authority_vector(packets),
                    require_process_witness=True,
                ),
                "RESULT_SOURCE_MEMBERSHIP_SUPERSEDED",
            )
        finally:
            f.close()

    # Negative E: an unknown/ghost source cannot self-mint membership authority.
    with tempfile.TemporaryDirectory(prefix="t2-pernode-ghost-") as td:
        f = PerNodeMembershipCohortFabric(Path(td) / "f.sqlite")
        try:
            memberships, lease, token = _seed(f)
            snap, packets = _make_packets(f, memberships)
            ghost = dict(packets[0])
            ghost["source_node_id"] = "ghost"
            core = {
                k: ghost[k]
                for k in ghost
                if k not in ("packet_digest", "s1_write_intent")
            }
            ghost["packet_digest"] = dg(core)
            mixed = [ghost, packets[1]]
            tests["P6_GHOST_SOURCE_REJECTED"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=mixed,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                    expected_authority_vector=f._authority_vector(mixed),
                ),
                "RESULT_SOURCE_MEMBERSHIP_NODE_MISMATCH",
            )
        finally:
            f.close()

    # Negative F: health authority is checked immediately before mutation.
    with tempfile.TemporaryDirectory(prefix="t2-pernode-unhealthy-") as td:
        f = PerNodeMembershipCohortFabric(Path(td) / "f.sqlite")
        try:
            memberships, lease, token = _seed(f)
            snap, packets = _make_packets(f, memberships)
            f.runtime_set_health("x01", False)
            current = f.snapshot()
            # Rebind S1 fields only to isolate membership-health rejection.
            rebound: list[dict[str, Any]] = []
            for packet in packets:
                p = dict(packet)
                p["state_epoch"] = current.epoch
                p["state_digest"] = current.state_digest
                core = {
                    k: p[k]
                    for k in p
                    if k not in ("packet_digest", "s1_write_intent")
                }
                p["packet_digest"] = dg(core)
                rebound.append(p)
            tests["P7_UNHEALTHY_SOURCE_REJECTED"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=rebound,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                    expected_authority_vector=f._authority_vector(rebound),
                ),
                "RESULT_SOURCE_NODE_UNHEALTHY",
            )
        finally:
            f.close()

    return {
        "schema": SCHEMA,
        "pass": all(tests.values()),
        "tests": tests,
        "scope": "DETERMINISTIC_SOURCE_COMPONENT_ONLY",
        "physical_process_authentication_observed": False,
        "repository_bound_runtime_observed": False,
        "canonical_truth_minted": False,
        "effect_authority_minted": False,
        "accepted_dataset_tokens": 0,
        "training_credit": 0,
        "next_gate": (
            "Fuse this per-node admission/revision authority vector with the exact "
            "ten-Popen held-S1 cohort/consumed-snapshot physical proof and execute only "
            "on a separately authorized exact-source non-provider surface."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = run()
    if args.out:
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
