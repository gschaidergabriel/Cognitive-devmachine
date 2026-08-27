#!/usr/bin/env python3
"""Trigger-2 test-only atomic same-cohort GRID10 fan-in successor.

Implements the noncanonical PHYSICAL_GRID10_SINGLE_SCOPE_ATOMIC_COHORT_BASE candidate:
- one GLOBAL coordinator is elected before the cohort snapshot;
- ten simultaneous ordinary OS processes observe one exact read-only S1 snapshot;
- the exact packet/process cohort is bound to one deterministic cohort_id;
- deterministic fabric validates the complete immutable cohort against the starting S1;
- one SQLite transaction records all ten members, writes one GLOBAL summary, and advances
  S1 exactly once;
- original NODE_RESULT observation identities remain unchanged;
- exact replay is idempotent with zero second state delta;
- tamper, substituted cohort, stale-start and duplicate identities fail closed.

This is an isolated deterministic acceptance candidate only. Source or local PASS does not
mint physical GRID10 runtime, whole-HCU, EntityOS, J-Space, training, canonical-truth, or
effect-authority credit. No provider/model/network execution is performed.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

from xeno_physical_grid10_acceptance_v2 import (
    ExactSnapshotFabric,
    N,
    concurrent_probe,
)
from xeno_self_organizing_fabric_acceptance_v1 import FabricError, cj, dg

SCHEMA = "TRIGGER2_GRID10_ATOMIC_COHORT_BATCH_ACCEPTANCE/v1"
COHORT_SCHEMA = "GRID10_ATOMIC_COHORT/v1"
SCOPE = "GLOBAL"


def identity_from_snapshot(snapshot: Any) -> tuple[int, int, str]:
    return (int(snapshot.generation), int(snapshot.epoch), str(snapshot.state_digest))


def identity_from_packet(packet: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(packet["generation"]),
        int(packet["state_epoch"]),
        str(packet["state_digest"]),
    )


def canonical_members(
    packets: list[dict[str, Any]], proof: dict[str, Any]
) -> list[dict[str, Any]]:
    ready_rows = proof.get("ready")
    if not isinstance(ready_rows, list) or len(ready_rows) != N:
        raise FabricError("COHORT_READY_PROOF_INVALID")
    ready_by_node = {str(row["node_id"]): row for row in ready_rows}
    if len(ready_by_node) != N:
        raise FabricError("COHORT_READY_NODE_ID_DUPLICATE")

    members: list[dict[str, Any]] = []
    for packet in packets:
        node_id = str(packet["source_node_id"])
        ready = ready_by_node.get(node_id)
        if ready is None:
            raise FabricError("COHORT_READY_BINDING_MISSING")
        producer_pid = int(packet["payload"]["process_pid"])
        ready_pid = int(ready["pid"])
        if producer_pid != ready_pid:
            raise FabricError("COHORT_PID_PACKET_BINDING_MISMATCH")
        packet_identity = identity_from_packet(packet)
        ready_identity = (
            int(ready["generation"]),
            int(ready["state_epoch"]),
            str(ready["state_digest"]),
        )
        if packet_identity != ready_identity:
            raise FabricError("COHORT_READY_PACKET_SNAPSHOT_MISMATCH")
        members.append(
            {
                "source_node_id": node_id,
                "packet_digest": str(packet["packet_digest"]),
                "producer_pid": producer_pid,
                "generation": packet_identity[0],
                "state_epoch": packet_identity[1],
                "state_digest": packet_identity[2],
            }
        )
    return sorted(members, key=lambda row: (row["source_node_id"], row["packet_digest"]))


def derive_cohort_id(
    *,
    packets: list[dict[str, Any]],
    proof: dict[str, Any],
    lease: dict[str, Any],
) -> str:
    members = canonical_members(packets, proof)
    if not members:
        raise FabricError("EMPTY_COHORT")
    start_identity = (
        members[0]["generation"],
        members[0]["state_epoch"],
        members[0]["state_digest"],
    )
    return "cohort-" + dg(
        {
            "schema": COHORT_SCHEMA,
            "scope": SCOPE,
            "coordinator_lease_id": lease["lease_id"],
            "start_identity": start_identity,
            "members": members,
        }
    )[:32]


class AtomicCohortFabric(ExactSnapshotFabric):
    """Test-only deterministic batch-admission successor; not canonical production state."""

    def __init__(self, path: Path):
        super().__init__(path)
        self.con.executescript(
            """
            CREATE TABLE IF NOT EXISTS cohort_admissions(
              cohort_id TEXT PRIMARY KEY,
              scope TEXT NOT NULL,
              coordinator_lease_id TEXT NOT NULL,
              start_generation INTEGER NOT NULL,
              start_epoch INTEGER NOT NULL,
              start_digest TEXT NOT NULL,
              member_count INTEGER NOT NULL,
              member_digests_json TEXT NOT NULL,
              resulting_epoch INTEGER NOT NULL,
              summary_digest TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cohort_members(
              cohort_id TEXT NOT NULL,
              source_node_id TEXT NOT NULL,
              producer_pid INTEGER NOT NULL,
              packet_digest TEXT NOT NULL,
              PRIMARY KEY(cohort_id, packet_digest),
              UNIQUE(cohort_id, source_node_id),
              UNIQUE(cohort_id, producer_pid)
            );
            """
        )

    def atomic_cohort_commit(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        packets: list[dict[str, Any]],
        proof: dict[str, Any],
        expected_cohort_id: str,
        expected_generation: int,
        expected_epoch: int,
        expected_digest: str,
    ) -> dict[str, Any]:
        if len(packets) != N:
            raise FabricError("COHORT_PACKET_COUNT_INVALID")
        if proof.get("distinct_os_pids") != N:
            raise FabricError("COHORT_PHYSICAL_PID_COUNT_INVALID")
        if not proof.get("all_alive_at_barrier"):
            raise FabricError("COHORT_ALL_LIVE_PROOF_MISSING")
        if not proof.get("pid_binding_ok") or not proof.get("packet_pid_binding_ok"):
            raise FabricError("COHORT_PID_BINDING_INVALID")
        if not proof.get("same_snapshot_identity"):
            raise FabricError("COHORT_MIXED_SNAPSHOT")
        if not proof.get("explicit_read_transaction"):
            raise FabricError("COHORT_READ_TRANSACTION_PROOF_MISSING")
        if not proof.get("all_hold_readonly_s1_fd_at_barrier"):
            raise FabricError("COHORT_READONLY_S1_FD_PROOF_MISSING")
        if not proof.get("writer_free_full_probe"):
            raise FabricError("COHORT_WRITER_FREE_PROOF_MISSING")

        expected_identity = (expected_generation, expected_epoch, expected_digest)
        packet_digests: list[str] = []
        source_nodes: list[str] = []
        producer_pids: list[int] = []
        for packet in packets:
            if packet.get("schema") != "NODE_RESULT/v1":
                raise FabricError("COHORT_PACKET_SCHEMA_INVALID")
            if packet.get("source_kind") != "ORDINARY_NODE":
                raise FabricError("COHORT_SOURCE_KIND_INVALID")
            if packet.get("scope") != SCOPE:
                raise FabricError("COHORT_MIXED_SCOPE")
            if packet.get("s1_write_intent") is not False:
                raise FabricError("COHORT_SOURCE_PACKET_MUST_NOT_SELF_WRITE")
            if identity_from_packet(packet) != expected_identity:
                raise FabricError("COHORT_MEMBER_SNAPSHOT_MISMATCH")
            core = {
                k: packet[k]
                for k in packet
                if k not in ("packet_digest", "s1_write_intent")
            }
            if packet.get("packet_digest") != dg(core):
                raise FabricError("COHORT_PACKET_DIGEST_MISMATCH")
            node_id = str(packet["source_node_id"])
            row = self.con.execute(
                "SELECT capability,healthy FROM nodes WHERE node_id=?", (node_id,)
            ).fetchone()
            if row is None or int(row["healthy"]) != 1 or row["capability"] != "reason":
                raise FabricError("COHORT_MEMBER_RUNTIME_MEMBERSHIP_INVALID")
            packet_digests.append(str(packet["packet_digest"]))
            source_nodes.append(node_id)
            producer_pids.append(int(packet["payload"]["process_pid"]))

        if len(set(packet_digests)) != N:
            raise FabricError("COHORT_DUPLICATE_PACKET")
        if len(set(source_nodes)) != N:
            raise FabricError("COHORT_DUPLICATE_NODE_ID")
        if len(set(producer_pids)) != N:
            raise FabricError("COHORT_DUPLICATE_PROCESS_IDENTITY")

        # This also verifies every packet PID and snapshot against its exact barrier-ready row.
        members = canonical_members(packets, proof)
        derived_cohort_id = derive_cohort_id(
            packets=packets,
            proof=proof,
            lease=lease,
        )
        if derived_cohort_id != expected_cohort_id:
            raise FabricError("COHORT_ID_BINDING_MISMATCH")

        # Exact replay is checked BEFORE requiring the historical starting snapshot to still
        # be current. Replay causes no mutation, so the already-admitted cohort remains
        # idempotent even though S1 necessarily advanced during the original commit.
        existing = self.con.execute(
            "SELECT * FROM cohort_admissions WHERE cohort_id=?",
            (derived_cohort_id,),
        ).fetchone()
        if existing is not None:
            stored_digests = json.loads(existing["member_digests_json"])
            requested_digests = [row["packet_digest"] for row in members]
            if (
                int(existing["start_generation"]) != expected_generation
                or int(existing["start_epoch"]) != expected_epoch
                or str(existing["start_digest"]) != expected_digest
                or int(existing["member_count"]) != N
                or stored_digests != requested_digests
            ):
                raise FabricError("COHORT_REPLAY_BINDING_MISMATCH")
            return {
                "cohort_id": derived_cohort_id,
                "replay": True,
                "state_delta": 0,
                "resulting_epoch": int(existing["resulting_epoch"]),
            }

        current = self.snapshot()
        if identity_from_snapshot(current) != expected_identity:
            raise FabricError("COHORT_START_SNAPSHOT_STALE")

        # Deterministic coordinator authority is required for a new state transition.
        self._lease_row(lease, token, SCOPE)

        ordered_packet_digests = [row["packet_digest"] for row in members]
        summary_payload = {
            "schema": "GRID10_COHORT_SUMMARY/v1",
            "cohort_id": derived_cohort_id,
            "member_count": N,
            "ordered_packet_digests": ordered_packet_digests,
            "ordered_source_node_ids": [row["source_node_id"] for row in members],
            "starting_snapshot": {
                "generation": expected_generation,
                "epoch": expected_epoch,
                "state_digest": expected_digest,
            },
            "observation_relabelled_as_current": False,
        }
        summary_digest = dg(summary_payload)

        self.con.execute("BEGIN IMMEDIATE")
        try:
            inside = self.snapshot()
            if identity_from_snapshot(inside) != expected_identity:
                raise FabricError("COHORT_CAS_FAILED")
            self._lease_row(lease, token, SCOPE)

            scope_row = self.con.execute(
                "SELECT * FROM scopes WHERE scope=?", (SCOPE,)
            ).fetchone()
            if scope_row is None:
                raise FabricError("UNKNOWN_SCOPE")
            for packet_digest in ordered_packet_digests:
                if self.con.execute(
                    "SELECT 1 FROM admitted_results WHERE result_digest=?",
                    (packet_digest,),
                ).fetchone():
                    raise FabricError("COHORT_MEMBER_ALREADY_ADMITTED")

            new_epoch = expected_epoch + 1
            merged = {
                "previous": json.loads(scope_row["summary_json"]),
                "latest": summary_payload,
                "source_schema": COHORT_SCHEMA,
            }
            self.con.execute(
                "UPDATE scopes SET summary_json=?,evidence_count=evidence_count+?,"
                "last_writer_lease_id=?,last_result_digest=?,state_epoch=? WHERE scope=?",
                (
                    cj(merged),
                    N,
                    lease["lease_id"],
                    summary_digest,
                    new_epoch,
                    SCOPE,
                ),
            )
            packet_by_digest = {str(p["packet_digest"]): p for p in packets}
            for member in members:
                packet = packet_by_digest[member["packet_digest"]]
                self.con.execute(
                    "INSERT INTO admitted_results VALUES(?,?,?,?,?)",
                    (
                        packet["packet_digest"],
                        packet["source_node_id"],
                        lease["lease_id"],
                        SCOPE,
                        new_epoch,
                    ),
                )
                self.con.execute(
                    "INSERT INTO cohort_members VALUES(?,?,?,?)",
                    (
                        derived_cohort_id,
                        member["source_node_id"],
                        member["producer_pid"],
                        member["packet_digest"],
                    ),
                )
            self.con.execute(
                "INSERT INTO cohort_admissions VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    derived_cohort_id,
                    SCOPE,
                    lease["lease_id"],
                    expected_generation,
                    expected_epoch,
                    expected_digest,
                    N,
                    cj(ordered_packet_digests),
                    new_epoch,
                    summary_digest,
                ),
            )
            self._set("epoch", str(new_epoch))
            self.con.execute("COMMIT")
        except Exception:
            self.con.execute("ROLLBACK")
            raise

        return {
            "cohort_id": derived_cohort_id,
            "replay": False,
            "state_delta": 1,
            "prior_epoch": expected_epoch,
            "resulting_epoch": new_epoch,
            "member_count": N,
            "summary_digest": summary_digest,
            "canonical_truth": False,
            "effect_authority": False,
        }


def make_fixture(root: Path, label: str) -> tuple[
    AtomicCohortFabric,
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
    str,
    Any,
]:
    db = root / f"{label}.sqlite"
    barrier = root / f"{label}-barrier"
    fabric = AtomicCohortFabric(db)
    ids = [f"x{i:02d}" for i in range(1, N + 1)]
    scopes = [SCOPE] * N
    for node_id in ids:
        fabric.runtime_register_node(node_id, "reason")
    fabric.seed_scope(SCOPE)
    for i in range(N):
        fabric.seed_task(f"t{i:02d}", SCOPE, 100 - i, "reason", {"q": i})
    lease, token = fabric.elect_coordinator(SCOPE)
    start = fabric.snapshot()
    source_script = Path(__file__).with_name("xeno_physical_grid10_acceptance_v2.py")
    packets, proof = concurrent_probe(
        source_script,
        db,
        ids,
        scopes,
        barrier,
    )
    return fabric, packets, proof, lease, token, start


def expect_error(fn, code: str) -> bool:
    try:
        fn()
    except FabricError as exc:
        return str(exc) == code
    return False


def run() -> dict[str, Any]:
    tests: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="trigger2-grid10-atomic-cohort-") as td:
        root = Path(td)

        # Positive: exact simultaneous cohort -> one atomic state transition -> replay +0.
        fabric, packets, proof, lease, token, start = make_fixture(root, "positive")
        try:
            cohort_id = derive_cohort_id(packets=packets, proof=proof, lease=lease)
            before_packets = cj(packets)
            receipt = fabric.atomic_cohort_commit(
                lease=lease,
                token=token,
                packets=packets,
                proof=proof,
                expected_cohort_id=cohort_id,
                expected_generation=start.generation,
                expected_epoch=start.epoch,
                expected_digest=start.state_digest,
            )
            after = fabric.snapshot()
            replay = fabric.atomic_cohort_commit(
                lease=lease,
                token=token,
                packets=packets,
                proof=proof,
                expected_cohort_id=cohort_id,
                expected_generation=start.generation,
                expected_epoch=start.epoch,
                expected_digest=start.state_digest,
            )
            tests["A1_TRUE_SIMULTANEOUS_COHORT"] = bool(
                proof["distinct_os_pids"] == N
                and proof["all_alive_at_barrier"]
                and proof["same_snapshot_identity"]
                and proof["all_hold_readonly_s1_fd_at_barrier"]
                and proof["writer_free_full_probe"]
            )
            tests["A2_EXACT_COHORT_PACKET_SET_COMMITTED"] = bool(
                receipt["member_count"] == N
                and receipt["state_delta"] == 1
                and receipt["resulting_epoch"] == start.epoch + 1
            )
            tests["A3_ONE_BATCH_ONE_EPOCH_ADVANCE"] = after.epoch == start.epoch + 1
            tests["A4_ORIGINAL_NODE_RESULTS_IMMUTABLE"] = cj(packets) == before_packets
            tests["A5_IDENTICAL_COHORT_REPLAY_ZERO_DELTA"] = bool(
                replay["replay"] is True
                and replay["state_delta"] == 0
                and fabric.snapshot().epoch == after.epoch
            )
        finally:
            fabric.close()

        # Negative: tampering any packet without updating its source-bound digest fails.
        fabric, packets, proof, lease, token, start = make_fixture(root, "tamper")
        try:
            cohort_id = derive_cohort_id(packets=packets, proof=proof, lease=lease)
            tampered = [dict(p) for p in packets]
            tampered[0] = dict(tampered[0])
            tampered[0]["payload"] = dict(tampered[0]["payload"])
            tampered[0]["payload"]["observation"] = "tampered"
            tests["N1_PACKET_TAMPER_REJECTED"] = expect_error(
                lambda: fabric.atomic_cohort_commit(
                    lease=lease,
                    token=token,
                    packets=tampered,
                    proof=proof,
                    expected_cohort_id=cohort_id,
                    expected_generation=start.generation,
                    expected_epoch=start.epoch,
                    expected_digest=start.state_digest,
                ),
                "COHORT_PACKET_DIGEST_MISMATCH",
            )
        finally:
            fabric.close()

        # Negative: an external S1 mutation after observation invalidates the whole batch.
        fabric, packets, proof, lease, token, start = make_fixture(root, "stale")
        try:
            cohort_id = derive_cohort_id(packets=packets, proof=proof, lease=lease)
            fabric.runtime_set_health("x10", True)
            tests["N2_STALE_BEFORE_BATCH_REJECTED"] = expect_error(
                lambda: fabric.atomic_cohort_commit(
                    lease=lease,
                    token=token,
                    packets=packets,
                    proof=proof,
                    expected_cohort_id=cohort_id,
                    expected_generation=start.generation,
                    expected_epoch=start.epoch,
                    expected_digest=start.state_digest,
                ),
                "COHORT_START_SNAPSHOT_STALE",
            )
        finally:
            fabric.close()

        # Negative: replacing one exact cohort member while retaining the preregistered
        # cohort_id must fail binding rather than silently splice a different cohort.
        fabric, packets, proof, lease, token, start = make_fixture(root, "splice")
        try:
            cohort_id = derive_cohort_id(packets=packets, proof=proof, lease=lease)
            replacement = [dict(p) for p in packets]
            replacement[0] = dict(replacement[0])
            replacement[0]["source_node_id"] = "x99"
            replacement[0]["payload"] = dict(replacement[0]["payload"])
            replacement[0]["payload"]["node"] = "x99"
            replacement_core = {
                k: replacement[0][k]
                for k in replacement[0]
                if k not in ("packet_digest", "s1_write_intent")
            }
            replacement[0]["packet_digest"] = dg(replacement_core)
            tests["N3_DISJOINT_MEMBER_SPLICE_REJECTED"] = expect_error(
                lambda: fabric.atomic_cohort_commit(
                    lease=lease,
                    token=token,
                    packets=replacement,
                    proof=proof,
                    expected_cohort_id=cohort_id,
                    expected_generation=start.generation,
                    expected_epoch=start.epoch,
                    expected_digest=start.state_digest,
                ),
                "COHORT_MEMBER_RUNTIME_MEMBERSHIP_INVALID",
            )
        finally:
            fabric.close()

        passed = all(tests.values())
        return {
            "schema": SCHEMA,
            "pass": passed,
            "tests": tests,
            "contract_scope": "TEST_ONLY_SINGLE_SCOPE_ATOMIC_SAME_COHORT_GRID10_CANDIDATE",
            "known_boundary": (
                "Producer packets are source-bound to the current physical-v2 child path and exact "
                "barrier snapshot/PID evidence; a stronger independent consumed-read attestation "
                "remains a later discriminator and is not claimed by this fixture."
            ),
            "promotion": "BLOCKED_PENDING_EXACT_CURRENT_REVIEW_AND_REPOSITORY_BOUND_RUNTIME_AUTHORITY",
            "credit_boundary": {
                "source_or_local_acceptance_only": True,
                "physical_grid10_runtime_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
                "jspace_model_credit": 0,
                "training_credit": 0,
                "canonical_truth": False,
                "effect_authority": False,
            },
        }


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
