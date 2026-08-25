#!/usr/bin/env python3
"""Trigger-2 deterministic candidate contract for same-cohort GRID fan-in.

Research/source pilot only. It mints no physical GRID10, HCU, EntityOS, J-Space,
training, canonical-truth, or effect-authority credit.

Why this exists
---------------
Current EXACT_SNAPSHOT_ONLY per-packet coordinator commits are intentionally
fail-closed: every successful write advances S1, so a second untouched packet
from the same exact observation snapshot becomes stale. A proof that ten
processes were concurrently alive therefore cannot be composed with ten later
fresh sequential packets and called a same-cohort integrated path.

This pilot tests one explicit alternative contract instead of silently rebasing
old observations:

  immutable cohort observed at S_k
    + deterministic runtime membership identity M_j
    + one coordinator lease/CAS authority
    -> validate the complete evidence set against (S_k, M_j)
    -> canonicalize by packet digest (never transport arrival order)
    -> one atomic coordinator-authorized transaction
    -> record every original packet digest unchanged
    -> publish one derived cohort summary
    -> advance S1 exactly once.

Membership is deliberately a separate deterministic authority identity rather
than being smuggled into model cognition or treated as canonical truth. The
pilot adds a monotonic membership_generation and membership_digest and binds
both into every candidate result packet. This is a candidate for a reusable
runtime contract, not an admission of the contract into product authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any

from xeno_self_organizing_fabric_acceptance_v1 import (
    Fabric,
    FabricError,
    RESULT_SCHEMA,
    cj,
    dg,
)

SCHEMA = "TRIGGER2_GRID10_ATOMIC_COHORT_FANIN_PILOT/v1"
COHORT_RECEIPT_SCHEMA = "GRID_COHORT_FANIN_RECEIPT/v1"
MEMBERSHIP_SCHEMA = "GRID_MEMBERSHIP_IDENTITY/v1"


class CohortFaninFabric(Fabric):
    """Candidate deterministic fabric with a separate membership authority clock."""

    def __init__(self, path: Path):
        super().__init__(path)
        if self.con.execute("SELECT 1 FROM meta WHERE k='membership_generation'").fetchone() is None:
            self._set("membership_generation", "1")

    def _bump_membership(self) -> int:
        generation = self._int("membership_generation") + 1
        self._set("membership_generation", str(generation))
        return generation

    def runtime_register_node(self, node_id: str, capability: str) -> None:
        # Membership mutation is deterministic runtime authority, never model authority.
        before = self.con.execute(
            "SELECT capability,healthy FROM nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        super().runtime_register_node(node_id, capability)
        after = self.con.execute(
            "SELECT capability,healthy FROM nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        if before is None or tuple(before) != tuple(after):
            self._bump_membership()

    def runtime_set_health(self, node_id: str, healthy: bool) -> None:
        before = self.con.execute(
            "SELECT healthy FROM nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        if before is None:
            raise FabricError("MEMBERSHIP_NODE_UNKNOWN")
        super().runtime_set_health(node_id, healthy)
        after = self.con.execute(
            "SELECT healthy FROM nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        if int(before["healthy"]) != int(after["healthy"]):
            self._bump_membership()

    def membership_identity(self) -> dict[str, Any]:
        rows = tuple(
            dict(r)
            for r in self.con.execute(
                "SELECT node_id,capability,healthy FROM nodes ORDER BY node_id"
            )
        )
        generation = self._int("membership_generation")
        digest = dg({"generation": generation, "nodes": rows})
        return {
            "schema": MEMBERSHIP_SCHEMA,
            "generation": generation,
            "digest": digest,
            "nodes": rows,
        }

    def result_packet(
        self,
        *,
        node_id: str,
        snapshot: Any,
        membership: dict[str, Any],
        scope: str,
        payload: Any,
    ) -> dict[str, Any]:
        core = {
            "schema": RESULT_SCHEMA,
            "source_kind": "ORDINARY_NODE",
            "source_node_id": node_id,
            "scope": scope,
            "generation": snapshot.generation,
            "state_epoch": snapshot.epoch,
            "state_digest": snapshot.state_digest,
            "membership_generation": membership["generation"],
            "membership_digest": membership["digest"],
            "payload": payload,
        }
        return {**core, "packet_digest": dg(core), "s1_write_intent": False}

    def _validate_cohort_packet(
        self,
        packet: dict[str, Any],
        *,
        current: Any,
        membership: dict[str, Any],
        scope: str,
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
        if packet.get("membership_generation") != membership["generation"]:
            raise FabricError("COHORT_STALE_MEMBERSHIP_GENERATION")
        if packet.get("membership_digest") != membership["digest"]:
            raise FabricError("COHORT_STALE_MEMBERSHIP_DIGEST")
        if packet.get("s1_write_intent") is not False:
            raise FabricError("COHORT_SOURCE_PACKET_MUST_NOT_SELF_WRITE")

        core = {
            key: packet[key]
            for key in packet
            if key not in ("packet_digest", "s1_write_intent")
        }
        if packet.get("packet_digest") != dg(core):
            raise FabricError("COHORT_PACKET_DIGEST_MISMATCH")

        node_id = packet.get("source_node_id")
        row = self.con.execute(
            "SELECT node_id,capability,healthy FROM nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        if row is None:
            raise FabricError("RESULT_SOURCE_NODE_UNREGISTERED")
        if int(row["healthy"]) != 1:
            raise FabricError("RESULT_SOURCE_NODE_UNHEALTHY")

        if self.con.execute(
            "SELECT 1 FROM admitted_results WHERE result_digest=?",
            (packet["packet_digest"],),
        ).fetchone():
            raise FabricError("DUPLICATE_RESULT_REJECTED")

    def coordinator_commit_cohort(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packets: list[dict[str, Any]],
        expected_epoch: int,
        expected_digest: str,
        expected_membership_generation: int,
        expected_membership_digest: str,
    ) -> dict[str, Any]:
        if len(packets) < 2:
            raise FabricError("COHORT_REQUIRES_MULTIPLE_PACKETS")
        scope_values = {str(packet.get("scope")) for packet in packets}
        if len(scope_values) != 1:
            raise FabricError("COHORT_SCOPE_MISMATCH")
        scope = next(iter(scope_values))

        # Coordinator lease is deterministic runtime authority and is checked once
        # for the whole cohort transaction.
        self._lease_row(lease, token, scope)
        current = self.snapshot()
        membership = self.membership_identity()
        if expected_epoch != current.epoch or expected_digest != current.state_digest:
            raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
        if (
            expected_membership_generation != membership["generation"]
            or expected_membership_digest != membership["digest"]
        ):
            raise FabricError("MEMBERSHIP_COMPARE_AND_SWAP_FAILED")

        packet_digests = [str(packet.get("packet_digest")) for packet in packets]
        if len(set(packet_digests)) != len(packet_digests):
            raise FabricError("COHORT_DUPLICATE_PACKET")
        source_ids = [str(packet.get("source_node_id")) for packet in packets]
        if len(set(source_ids)) != len(source_ids):
            raise FabricError("COHORT_DUPLICATE_SOURCE_NODE")

        for packet in packets:
            self._validate_cohort_packet(
                packet, current=current, membership=membership, scope=scope
            )

        # Canonical order is a semantic firewall against transport-arrival shortcuts.
        canonical_packets = sorted(packets, key=lambda packet: packet["packet_digest"])
        canonical_digests = [packet["packet_digest"] for packet in canonical_packets]
        cohort_core = {
            "base_generation": current.generation,
            "base_epoch": current.epoch,
            "base_state_digest": current.state_digest,
            "membership_generation": membership["generation"],
            "membership_digest": membership["digest"],
            "scope": scope,
            "packet_digests": canonical_digests,
        }
        cohort_digest = dg(cohort_core)

        self.con.execute("BEGIN IMMEDIATE")
        try:
            # Re-check both deterministic authority domains after obtaining the
            # writer lock. No model packet can self-mint either identity.
            if self._int("epoch") != expected_epoch:
                raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
            current_locked = self.snapshot()
            if current_locked.state_digest != expected_digest:
                raise FabricError("S1_COMPARE_AND_SWAP_FAILED")
            membership_locked = self.membership_identity()
            if (
                membership_locked["generation"] != expected_membership_generation
                or membership_locked["digest"] != expected_membership_digest
            ):
                raise FabricError("MEMBERSHIP_COMPARE_AND_SWAP_FAILED")

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
                    "membership_generation": membership["generation"],
                    "membership_digest": membership["digest"],
                    "evidence_packet_digests": canonical_digests,
                    "payloads": [packet["payload"] for packet in canonical_packets],
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
            "scope": scope,
            "cohort_digest": cohort_digest,
            "packet_digests": canonical_digests,
            "source_node_ids": [
                packet["source_node_id"] for packet in canonical_packets
            ],
            "base_generation": current.generation,
            "base_epoch": current.epoch,
            "base_state_digest": current.state_digest,
            "membership_generation": membership["generation"],
            "membership_digest": membership["digest"],
            "new_epoch": new_epoch,
            "canonical_truth": False,
            "effect_authority": False,
        }


def expect_error(fn: Any, code: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == code
    return False


def seed(fabric: CohortFaninFabric) -> tuple[dict[str, Any], str]:
    for node_id in ("x01", "x02", "x03"):
        fabric.runtime_register_node(node_id, "reason")
    fabric.seed_scope("branch:a")
    fabric.seed_task("t01", "branch:a", 100, "reason", {"q": 1})
    fabric.seed_task("t02", "branch:a", 99, "reason", {"q": 2})
    return fabric.elect_coordinator("branch:a")


def make_two(
    fabric: CohortFaninFabric,
) -> tuple[Any, dict[str, Any], list[dict[str, Any]]]:
    snapshot = fabric.snapshot()
    membership = fabric.membership_identity()
    packets = [
        fabric.result_packet(
            node_id="x01",
            snapshot=snapshot,
            membership=membership,
            scope="branch:a",
            payload={"answer": "alpha", "evidence": ["e1"]},
        ),
        fabric.result_packet(
            node_id="x02",
            snapshot=snapshot,
            membership=membership,
            scope="branch:a",
            payload={"answer": "beta", "evidence": ["e2"]},
        ),
    ]
    return snapshot, membership, packets


def commit_two(
    fabric: CohortFaninFabric,
    lease: dict[str, Any],
    token: str,
    packets: list[dict[str, Any]],
) -> dict[str, Any]:
    snapshot = fabric.snapshot()
    membership = fabric.membership_identity()
    return fabric.coordinator_commit_cohort(
        lease=lease,
        token=token,
        packets=packets,
        expected_epoch=snapshot.epoch,
        expected_digest=snapshot.state_digest,
        expected_membership_generation=membership["generation"],
        expected_membership_digest=membership["digest"],
    )


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}

    # Positive: two untouched same-snapshot packets enter one atomic fan-in and
    # S1 advances once rather than once per packet.
    with tempfile.TemporaryDirectory(prefix="t2-cohort-positive-") as td:
        f = CohortFaninFabric(Path(td) / "f.sqlite")
        try:
            lease, token = seed(f)
            base, membership, packets = make_two(f)
            receipt = f.coordinator_commit_cohort(
                lease=lease,
                token=token,
                packets=packets,
                expected_epoch=base.epoch,
                expected_digest=base.state_digest,
                expected_membership_generation=membership["generation"],
                expected_membership_digest=membership["digest"],
            )
            after = f.snapshot()
            count = int(
                f.con.execute("SELECT COUNT(*) FROM admitted_results").fetchone()[0]
            )
            tests["P1_SAME_SNAPSHOT_COHORT_ONE_ATOMIC_EPOCH"] = (
                receipt["base_epoch"] == base.epoch
                and receipt["new_epoch"] == base.epoch + 1
                and after.epoch == base.epoch + 1
                and count == 2
            )
            tests["P2_ORIGINAL_PACKET_DIGESTS_PRESERVED"] = (
                set(receipt["packet_digests"])
                == {packet["packet_digest"] for packet in packets}
            )
        finally:
            f.close()

    # Transport arrival order must not alter cohort identity or final state.
    order_results: list[tuple[str, str]] = []
    for reverse in (False, True):
        with tempfile.TemporaryDirectory(prefix="t2-cohort-order-") as td:
            f = CohortFaninFabric(Path(td) / "f.sqlite")
            try:
                lease, token = seed(f)
                base, membership, packets = make_two(f)
                if reverse:
                    packets.reverse()
                receipt = f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=packets,
                    expected_epoch=base.epoch,
                    expected_digest=base.state_digest,
                    expected_membership_generation=membership["generation"],
                    expected_membership_digest=membership["digest"],
                )
                order_results.append((receipt["cohort_digest"], f.snapshot().state_digest))
            finally:
                f.close()
    tests["P3_TRANSPORT_ARRIVAL_PERMUTATION_INVARIANT"] = (
        len(set(order_results)) == 1
    )

    # Unregistered source must fail atomically before admitted_results mutation.
    with tempfile.TemporaryDirectory(prefix="t2-cohort-ghost-") as td:
        f = CohortFaninFabric(Path(td) / "f.sqlite")
        try:
            lease, token = seed(f)
            base = f.snapshot()
            membership = f.membership_identity()
            valid = f.result_packet(
                node_id="x01",
                snapshot=base,
                membership=membership,
                scope="branch:a",
                payload={"answer": "valid"},
            )
            ghost = f.result_packet(
                node_id="ghost",
                snapshot=base,
                membership=membership,
                scope="branch:a",
                payload={"answer": "ghost"},
            )
            before = f.snapshot()
            tests["N1_UNREGISTERED_SOURCE_REJECTED"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=[valid, ghost],
                    expected_epoch=base.epoch,
                    expected_digest=base.state_digest,
                    expected_membership_generation=membership["generation"],
                    expected_membership_digest=membership["digest"],
                ),
                "RESULT_SOURCE_NODE_UNREGISTERED",
            )
            after = f.snapshot()
            admitted = int(
                f.con.execute("SELECT COUNT(*) FROM admitted_results").fetchone()[0]
            )
            tests["N2_FAILED_COHORT_IS_ATOMIC_NO_MUTATION"] = (
                before == after and admitted == 0
            )
        finally:
            f.close()

    # Healthy membership is deterministic runtime authority, not source assertion.
    with tempfile.TemporaryDirectory(prefix="t2-cohort-unhealthy-") as td:
        f = CohortFaninFabric(Path(td) / "f.sqlite")
        try:
            lease, token = seed(f)
            f.runtime_set_health("x02", False)
            base = f.snapshot()
            membership = f.membership_identity()
            packets = [
                f.result_packet(
                    node_id=node_id,
                    snapshot=base,
                    membership=membership,
                    scope="branch:a",
                    payload={"node": node_id},
                )
                for node_id in ("x01", "x02")
            ]
            tests["N3_UNHEALTHY_SOURCE_REJECTED"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=packets,
                    expected_epoch=base.epoch,
                    expected_digest=base.state_digest,
                    expected_membership_generation=membership["generation"],
                    expected_membership_digest=membership["digest"],
                ),
                "RESULT_SOURCE_NODE_UNHEALTHY",
            )
        finally:
            f.close()

    # Registration can change while legacy S1 digest remains unchanged. The
    # separate membership identity must still make the old cohort stale.
    with tempfile.TemporaryDirectory(prefix="t2-cohort-membership-") as td:
        f = CohortFaninFabric(Path(td) / "f.sqlite")
        try:
            lease, token = seed(f)
            base, membership, packets = make_two(f)
            s1_before = f.snapshot()
            f.runtime_register_node("x99", "reason")
            s1_after = f.snapshot()
            membership_after = f.membership_identity()
            tests["N4_MEMBERSHIP_CAN_CHANGE_WITHOUT_LEGACY_S1_CHANGE"] = (
                s1_before == s1_after
                and membership_after["generation"] != membership["generation"]
                and membership_after["digest"] != membership["digest"]
            )
            tests["N5_STALE_MEMBERSHIP_COHORT_REJECTED"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=packets,
                    expected_epoch=base.epoch,
                    expected_digest=base.state_digest,
                    expected_membership_generation=membership["generation"],
                    expected_membership_digest=membership["digest"],
                ),
                "MEMBERSHIP_COMPARE_AND_SWAP_FAILED",
            )
        finally:
            f.close()

    # S1 advancement independently invalidates old observations.
    with tempfile.TemporaryDirectory(prefix="t2-cohort-stale-s1-") as td:
        f = CohortFaninFabric(Path(td) / "f.sqlite")
        try:
            lease, token = seed(f)
            base, membership, packets = make_two(f)
            f.seed_task("late", "branch:a", 1, "reason", {"late": True})
            current = f.snapshot()
            current_membership = f.membership_identity()
            tests["N6_STALE_S1_COHORT_REJECTED"] = expect_error(
                lambda: f.coordinator_commit_cohort(
                    lease=lease,
                    token=token,
                    packets=packets,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                    expected_membership_generation=current_membership["generation"],
                    expected_membership_digest=current_membership["digest"],
                ),
                "COHORT_STALE_EPOCH",
            )
        finally:
            f.close()

    passed = all(tests.values())
    return {
        "schema": SCHEMA,
        "pass": passed,
        "tests": tests,
        "candidate_contract": {
            "same_snapshot_evidence": "IMMUTABLE",
            "fanin": "ATOMIC_COHORT_BATCH",
            "ordering": "CANONICAL_PACKET_DIGEST_NOT_TRANSPORT_ARRIVAL",
            "membership_authority": "SEPARATE_MONOTONIC_GENERATION_AND_DIGEST",
            "s1_epoch_transitions_per_cohort": 1,
            "model_can_mint_membership": False,
            "model_can_mint_truth": False,
            "model_can_mint_effect_authority": False,
        },
        "credit_boundary": {
            "source_pilot_only": True,
            "physical_grid10_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "canonical_semantics_credit": 0,
        },
        "next_gate": (
            "Run source regressions first; if they pass, compare this atomic-cohort "
            "contract against immutable-evidence-to-current-summary under failure, "
            "replay, membership churn, mixed scopes, causal-order-sensitive packets, "
            "and recursive Hyperposition preservation before product promotion or runtime pin."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
