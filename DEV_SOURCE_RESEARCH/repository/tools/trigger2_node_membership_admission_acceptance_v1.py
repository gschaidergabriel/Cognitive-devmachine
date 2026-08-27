#!/usr/bin/env python3
"""Trigger-2 deterministic acceptance for NODE_RESULT membership identity.

This fixture adds a monotonic runtime-membership identity beside S1 snapshot identity.
It is intentionally local/source evidence only. It does not mint physical GRID10,
whole-HCU, EntityOS, J-Space, training, canonical-truth, or effect-authority credit.

The property is orthogonal to S1 freshness:
- an ordinary result source must be currently registered;
- its membership admission id must be the active id for that node;
- the active membership must be healthy and generation-current;
- re-registering the same logical node invalidates the old membership id even if S1
  epoch/digest did not change.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

from xeno_physical_grid10_acceptance_v2 import ExactSnapshotFabric
from xeno_self_organizing_fabric_acceptance_v1 import (
    FabricError,
    RESULT_SCHEMA,
    Xeno,
    dg,
)

SCHEMA = "TRIGGER2_NODE_MEMBERSHIP_ADMISSION_ACCEPTANCE/v1"
MEMBERSHIP_SCHEMA = "GRID_NODE_MEMBERSHIP/v1"


class MembershipBoundFabric(ExactSnapshotFabric):
    """Exact-snapshot fabric plus deterministic monotonic node-membership admission."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.con.executescript(
            """
            CREATE TABLE node_memberships(
              membership_id TEXT PRIMARY KEY,
              node_id TEXT NOT NULL,
              capability TEXT NOT NULL,
              generation INTEGER NOT NULL,
              serial INTEGER NOT NULL,
              valid INTEGER NOT NULL,
              healthy INTEGER NOT NULL
            );
            CREATE INDEX node_memberships_active
              ON node_memberships(node_id, valid, serial);
            """
        )

    def runtime_register_node(self, node_id: str, capability: str) -> dict[str, Any]:
        # Membership is deterministic runtime/fabric authority, not model-originated S1.
        # Re-registration revokes the prior admission identity without pretending S1 changed.
        super().runtime_register_node(node_id, capability)
        prior = self.con.execute(
            "SELECT COALESCE(MAX(serial),0) AS n FROM node_memberships"
        ).fetchone()
        serial = int(prior["n"]) + 1
        generation = self._int("generation")
        membership_id = "member-" + dg(
            {
                "schema": MEMBERSHIP_SCHEMA,
                "node_id": node_id,
                "capability": capability,
                "generation": generation,
                "serial": serial,
            }
        )[:24]
        self.con.execute(
            "UPDATE node_memberships SET valid=0 WHERE node_id=? AND valid=1",
            (node_id,),
        )
        self.con.execute(
            "INSERT INTO node_memberships VALUES(?,?,?,?,?,1,1)",
            (membership_id, node_id, capability, generation, serial),
        )
        return {
            "schema": MEMBERSHIP_SCHEMA,
            "membership_id": membership_id,
            "node_id": node_id,
            "capability": capability,
            "generation": generation,
            "serial": serial,
        }

    def runtime_set_health(self, node_id: str, healthy: bool) -> None:
        super().runtime_set_health(node_id, healthy)
        self.con.execute(
            "UPDATE node_memberships SET healthy=? WHERE node_id=? AND valid=1",
            (1 if healthy else 0, node_id),
        )

    def active_membership(self, node_id: str) -> dict[str, Any]:
        row = self.con.execute(
            "SELECT * FROM node_memberships "
            "WHERE node_id=? AND valid=1 ORDER BY serial DESC LIMIT 1",
            (node_id,),
        ).fetchone()
        if row is None:
            raise FabricError("NODE_MEMBERSHIP_NOT_FOUND")
        return dict(row)

    def bind_result_membership(
        self, packet: dict[str, Any], membership_id: str
    ) -> dict[str, Any]:
        if packet.get("schema") != RESULT_SCHEMA:
            raise FabricError("MEMBERSHIP_BINDING_ONLY_FOR_NODE_RESULT")
        bound = dict(packet)
        bound["source_membership_id"] = membership_id
        core = {
            key: bound[key]
            for key in bound
            if key not in ("packet_digest", "s1_write_intent")
        }
        bound["packet_digest"] = dg(core)
        return bound

    def _verify_result_membership(self, packet: dict[str, Any]) -> None:
        node_id = packet.get("source_node_id")
        membership_id = packet.get("source_membership_id")
        if not isinstance(node_id, str) or not node_id:
            raise FabricError("RESULT_SOURCE_NODE_ID_INVALID")
        if not isinstance(membership_id, str) or not membership_id:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_REQUIRED")

        row = self.con.execute(
            "SELECT * FROM node_memberships WHERE membership_id=?",
            (membership_id,),
        ).fetchone()
        if row is None:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_UNKNOWN")
        if row["node_id"] != node_id or int(row["valid"]) != 1:
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_INVALID")
        if int(row["generation"]) != self._int("generation"):
            raise FabricError("RESULT_SOURCE_MEMBERSHIP_STALE_GENERATION")
        if int(row["healthy"]) != 1:
            raise FabricError("RESULT_SOURCE_UNHEALTHY")

        node = self.con.execute(
            "SELECT capability,healthy FROM nodes WHERE node_id=?",
            (node_id,),
        ).fetchone()
        if node is None:
            raise FabricError("RESULT_SOURCE_NOT_REGISTERED")
        if int(node["healthy"]) != 1:
            raise FabricError("RESULT_SOURCE_UNHEALTHY")
        if node["capability"] != row["capability"]:
            raise FabricError("RESULT_SOURCE_CAPABILITY_MEMBERSHIP_MISMATCH")

    def coordinator_commit(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packet: dict[str, Any],
        expected_epoch: int,
        expected_digest: str,
    ) -> dict[str, Any]:
        if packet.get("schema") == RESULT_SCHEMA:
            self._verify_result_membership(packet)
        return super().coordinator_commit(
            lease=lease,
            token=token,
            packet=packet,
            expected_epoch=expected_epoch,
            expected_digest=expected_digest,
        )


def expect_error(fn, expected: str) -> str:
    got = None
    try:
        fn()
    except FabricError as exc:
        got = str(exc)
    if got != expected:
        raise AssertionError(f"expected {expected}, got {got}")
    return got


def admitted_count(fabric: MembershipBoundFabric) -> int:
    return int(
        fabric.con.execute("SELECT COUNT(*) AS n FROM admitted_results").fetchone()["n"]
    )


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="trigger2-membership-") as td:
        db = Path(td) / "membership.sqlite"
        fabric = MembershipBoundFabric(db)
        try:
            m1 = fabric.runtime_register_node("x01", "reason")
            m2 = fabric.runtime_register_node("x02", "reason")
            fabric.seed_scope("branch:a")
            fabric.seed_task("t01", "branch:a", 100, "reason", {"q": 1})
            lease, token = fabric.elect_coordinator("branch:a")

            # Positive control: a current, healthy, registered membership is admissible.
            snap = fabric.snapshot()
            healthy_packet = fabric.bind_result_membership(
                Xeno("x01", "reason").result(
                    snap, "branch:a", {"probe": "healthy_current_membership"}
                ),
                m1["membership_id"],
            )
            healthy_receipt = fabric.coordinator_commit(
                lease=lease,
                token=token,
                packet=healthy_packet,
                expected_epoch=snap.epoch,
                expected_digest=snap.state_digest,
            )

            # Negative 1: an arbitrary unregistered logical source cannot self-assert membership.
            before = admitted_count(fabric)
            snap = fabric.snapshot()
            ghost = Xeno("ghost", "reason").result(
                snap, "branch:a", {"probe": "unregistered_source"}
            )
            ghost["source_membership_id"] = "member-" + "0" * 24
            ghost_core = {
                key: ghost[key]
                for key in ghost
                if key not in ("packet_digest", "s1_write_intent")
            }
            ghost["packet_digest"] = dg(ghost_core)
            unregistered_error = expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=ghost,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                ),
                "RESULT_SOURCE_MEMBERSHIP_UNKNOWN",
            )
            after_unregistered = admitted_count(fabric)

            # Negative 2: a registered but unhealthy membership is rejected at exact-current S1.
            fabric.runtime_set_health("x02", False)
            snap = fabric.snapshot()
            unhealthy = fabric.bind_result_membership(
                Xeno("x02", "reason").result(
                    snap, "branch:a", {"probe": "unhealthy_source"}
                ),
                m2["membership_id"],
            )
            before_unhealthy = admitted_count(fabric)
            unhealthy_error = expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=unhealthy,
                    expected_epoch=snap.epoch,
                    expected_digest=snap.state_digest,
                ),
                "RESULT_SOURCE_UNHEALTHY",
            )
            after_unhealthy = admitted_count(fabric)
            fabric.runtime_set_health("x02", True)

            # Negative 3: re-registration invalidates the prior membership even when S1
            # generation/epoch/digest are unchanged by the registration event itself.
            snap_before_reregister = fabric.snapshot()
            stale_membership_packet = fabric.bind_result_membership(
                Xeno("x01", "reason").result(
                    snap_before_reregister,
                    "branch:a",
                    {"probe": "stale_membership_after_reregister"},
                ),
                m1["membership_id"],
            )
            m1_successor = fabric.runtime_register_node("x01", "reason")
            snap_after_reregister = fabric.snapshot()
            s1_unchanged_by_reregister = (
                snap_before_reregister.generation == snap_after_reregister.generation
                and snap_before_reregister.epoch == snap_after_reregister.epoch
                and snap_before_reregister.state_digest == snap_after_reregister.state_digest
            )
            before_stale_membership = admitted_count(fabric)
            stale_membership_error = expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=stale_membership_packet,
                    expected_epoch=snap_after_reregister.epoch,
                    expected_digest=snap_after_reregister.state_digest,
                ),
                "RESULT_SOURCE_MEMBERSHIP_INVALID",
            )
            after_stale_membership = admitted_count(fabric)

            # Successor membership works on that same S1 snapshot.
            successor_packet = fabric.bind_result_membership(
                Xeno("x01", "reason").result(
                    snap_after_reregister,
                    "branch:a",
                    {"probe": "successor_membership"},
                ),
                m1_successor["membership_id"],
            )
            successor_receipt = fabric.coordinator_commit(
                lease=lease,
                token=token,
                packet=successor_packet,
                expected_epoch=snap_after_reregister.epoch,
                expected_digest=snap_after_reregister.state_digest,
            )

            passed = all(
                (
                    healthy_receipt["new_epoch"] == healthy_receipt["prior_epoch"] + 1,
                    unregistered_error == "RESULT_SOURCE_MEMBERSHIP_UNKNOWN",
                    before == after_unregistered,
                    unhealthy_error == "RESULT_SOURCE_UNHEALTHY",
                    before_unhealthy == after_unhealthy,
                    s1_unchanged_by_reregister,
                    m1_successor["membership_id"] != m1["membership_id"],
                    stale_membership_error == "RESULT_SOURCE_MEMBERSHIP_INVALID",
                    before_stale_membership == after_stale_membership,
                    successor_receipt["new_epoch"]
                    == successor_receipt["prior_epoch"] + 1,
                )
            )

            return {
                "schema": SCHEMA,
                "pass": passed,
                "claim_scope": "DETERMINISTIC_NODE_MEMBERSHIP_ADMISSION_COMPONENT_ONLY",
                "membership_contract": {
                    "identity": "MONOTONIC_RUNTIME_ADMISSION_ID",
                    "separate_from_s1_snapshot_identity": True,
                    "reregistration_invalidates_prior_id": True,
                    "health_checked_at_commit": True,
                    "generation_checked_at_commit": True,
                    "packet_digest_binds_source_membership_id": True,
                    "cryptographic_os_process_authentication_proven": False,
                },
                "observations": {
                    "healthy_receipt": healthy_receipt,
                    "unregistered_error": unregistered_error,
                    "unhealthy_error": unhealthy_error,
                    "s1_unchanged_by_reregister": s1_unchanged_by_reregister,
                    "stale_membership_error": stale_membership_error,
                    "successor_receipt": successor_receipt,
                    "membership_serials": [
                        m1["serial"],
                        m2["serial"],
                        m1_successor["serial"],
                    ],
                },
                "interpretation": (
                    "S1 epoch/digest freshness and source membership are independent authority "
                    "dimensions. A result can be exact-current in S1 yet still be rejected because "
                    "its source membership is unknown, unhealthy, or superseded."
                ),
                "remaining_gap": (
                    "This fixture proves deterministic monotonic membership admission semantics, "
                    "not cryptographic authentication that an arbitrary packet was emitted by the "
                    "claimed OS process. Physical GRID10 integration must bind this membership id "
                    "to the parent-spawn/process/packet provenance before runtime promotion."
                ),
                "credit_boundary": {
                    "local_source_component_only": True,
                    "physical_grid10_runtime_credit": 0,
                    "whole_hcu_runtime_credit": 0,
                    "whole_entityos_runtime_credit": 0,
                    "jspace_model_credit": 0,
                    "training_credit": 0,
                    "canonical_truth_credit": 0,
                    "effect_authority_credit": 0,
                },
            }
        finally:
            fabric.close()


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
