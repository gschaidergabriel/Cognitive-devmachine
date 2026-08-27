#!/usr/bin/env python3
"""Physical GRID10 acceptance harness v3: same-cohort evidence closure.

v2 proved that ten distinct OS processes were simultaneously alive on one read-only
S1 snapshot, but later admitted packets from a different sequential process cohort.
This successor closes that proof splice without relabeling old observations as current:

1. ten concurrently live children emit immutable NODE_RESULT/v1 packets;
2. each packet is bound to the exact barrier PID/process interval/snapshot identity;
3. coordinator integration consumes exactly that cohort packet-digest set;
4. after lease creation advances S1, the coordinator emits one NEW current-state
   COORDINATOR_SUMMARY/v1 that references the immutable old cohort evidence;
5. disjoint-cohort and unused/tampered-packet substitutions fail closed.

This is a deterministic local component harness only. A local PASS does not mint
repository-bound physical GRID10, HCU, EntityOS, J-Space, training, canonical-truth,
or effect-authority credit.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import tempfile
import time
from typing import Any

from xeno_physical_grid10_acceptance_v2 import (
    ExactSnapshotFabric,
    child_node,
    concurrent_probe,
    spawn_one,
)
from xeno_self_organizing_fabric_acceptance_v1 import (
    FabricError,
    Xeno,
    coordinator_summary,
    dg,
)

SCHEMA = "XENO_PHYSICAL_GRID10_ACCEPTANCE/v3"
COHORT_SCHEMA = "GRID10_COHORT_EVIDENCE_MANIFEST/v1"
DERIVED_SUMMARY_SCHEMA = "GRID10_COHORT_DERIVED_SUMMARY/v1"
N = 10


def expect_error(fn, code: str) -> None:
    got = None
    try:
        fn()
    except FabricError as exc:
        got = str(exc)
    if got != code:
        raise AssertionError(f"expected {code}, got {got}")


def _packet_core(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        k: packet[k]
        for k in packet
        if k not in ("packet_digest", "s1_write_intent")
    }


def _assert_packet_self_consistent(packet: dict[str, Any]) -> None:
    if packet.get("schema") != "NODE_RESULT/v1":
        raise FabricError("COHORT_PACKET_SCHEMA_INVALID")
    if packet.get("source_kind") != "ORDINARY_NODE":
        raise FabricError("COHORT_PACKET_SOURCE_KIND_INVALID")
    if packet.get("s1_write_intent") is not False:
        raise FabricError("COHORT_PACKET_WRITE_INTENT_INVALID")
    if packet.get("packet_digest") != dg(_packet_core(packet)):
        raise FabricError("COHORT_PACKET_DIGEST_INVALID")


def build_cohort_manifest(
    packets: list[dict[str, Any]], proof: dict[str, Any]
) -> dict[str, Any]:
    if len(packets) != N:
        raise FabricError("COHORT_PACKET_COUNT_INVALID")
    ready_rows = list(proof.get("ready", []))
    if len(ready_rows) != N:
        raise FabricError("COHORT_READY_COUNT_INVALID")
    ready_by_node = {str(r["node_id"]): r for r in ready_rows}
    if len(ready_by_node) != N:
        raise FabricError("COHORT_READY_NODE_ID_DUPLICATE")

    members: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()
    seen_pids: set[int] = set()
    for packet in packets:
        _assert_packet_self_consistent(packet)
        node_id = str(packet.get("source_node_id"))
        if node_id in seen_nodes:
            raise FabricError("COHORT_PACKET_NODE_ID_DUPLICATE")
        ready = ready_by_node.get(node_id)
        if ready is None:
            raise FabricError("COHORT_PACKET_WITHOUT_READY_WITNESS")
        payload = packet.get("payload")
        if not isinstance(payload, dict) or "process_pid" not in payload:
            raise FabricError("COHORT_PACKET_PID_MISSING")
        pid = int(payload["process_pid"])
        if pid != int(ready["pid"]):
            raise FabricError("COHORT_PACKET_PID_BINDING_INVALID")
        if pid in seen_pids:
            raise FabricError("COHORT_PACKET_PID_DUPLICATE")
        packet_identity = (
            int(packet.get("generation")),
            int(packet.get("state_epoch")),
            str(packet.get("state_digest")),
        )
        ready_identity = (
            int(ready["generation"]),
            int(ready["state_epoch"]),
            str(ready["state_digest"]),
        )
        if packet_identity != ready_identity:
            raise FabricError("COHORT_PACKET_SNAPSHOT_BINDING_INVALID")
        members.append(
            {
                "node_id": node_id,
                "pid": pid,
                "started_ns": int(ready["started_ns"]),
                "ready_ns": int(ready["ready_ns"]),
                "generation": packet_identity[0],
                "state_epoch": packet_identity[1],
                "state_digest": packet_identity[2],
                "packet_digest": str(packet["packet_digest"]),
            }
        )
        seen_nodes.add(node_id)
        seen_pids.add(pid)

    if set(ready_by_node) != seen_nodes:
        raise FabricError("COHORT_READY_PACKET_NODE_SET_MISMATCH")
    members.sort(key=lambda m: m["node_id"])
    source_identities = {
        (m["generation"], m["state_epoch"], m["state_digest"]) for m in members
    }
    if len(source_identities) != 1:
        raise FabricError("COHORT_SOURCE_SNAPSHOT_NOT_SHARED")
    manifest_core = {
        "schema": COHORT_SCHEMA,
        "member_count": N,
        "members": members,
        "source_snapshot_identity": list(next(iter(source_identities))),
        "all_alive_at_barrier": bool(proof.get("all_alive_at_barrier")),
        "interval_overlap_ok": bool(proof.get("interval_overlap_ok")),
        "released_ns": int(proof.get("released_ns")),
    }
    if not manifest_core["all_alive_at_barrier"]:
        raise FabricError("COHORT_NOT_ALL_ALIVE_AT_BARRIER")
    if not manifest_core["interval_overlap_ok"]:
        raise FabricError("COHORT_PROCESS_INTERVALS_NOT_OVERLAPPING")
    return {**manifest_core, "manifest_digest": dg(manifest_core)}


def validate_consumed_packet_set(
    manifest: dict[str, Any], packets: list[dict[str, Any]]
) -> dict[str, Any]:
    if manifest.get("schema") != COHORT_SCHEMA:
        raise FabricError("COHORT_MANIFEST_SCHEMA_INVALID")
    manifest_core = {k: manifest[k] for k in manifest if k != "manifest_digest"}
    if manifest.get("manifest_digest") != dg(manifest_core):
        raise FabricError("COHORT_MANIFEST_DIGEST_INVALID")
    if len(packets) != int(manifest.get("member_count", -1)):
        raise FabricError("COHORT_CONSUMED_COUNT_MISMATCH")
    for packet in packets:
        _assert_packet_self_consistent(packet)
    expected = sorted(str(m["packet_digest"]) for m in manifest["members"])
    actual = sorted(str(p["packet_digest"]) for p in packets)
    if actual != expected:
        raise FabricError("COHORT_PACKET_SET_MISMATCH")
    return {
        "manifest_digest": str(manifest["manifest_digest"]),
        "member_count": len(actual),
        "packet_digests": actual,
        "exact_set_match": True,
    }


class CohortBoundFabric(ExactSnapshotFabric):
    def coordinator_commit_cohort_summary(
        self,
        *,
        lease: dict[str, Any],
        token: str,
        manifest: dict[str, Any],
        cohort_packets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        consumed = validate_consumed_packet_set(manifest, cohort_packets)
        current = self.snapshot()
        source_identity = manifest["source_snapshot_identity"]
        payload = {
            "schema": DERIVED_SUMMARY_SCHEMA,
            "derivation": "EXACT_IMMUTABLE_COHORT_PACKET_SET_TO_NEW_CURRENT_SUMMARY",
            "cohort_manifest_digest": manifest["manifest_digest"],
            "cohort_member_count": manifest["member_count"],
            "cohort_packet_digests": consumed["packet_digests"],
            "cohort_source_snapshot": {
                "generation": int(source_identity[0]),
                "state_epoch": int(source_identity[1]),
                "state_digest": str(source_identity[2]),
            },
            "summary_observation_snapshot": {
                "generation": current.generation,
                "state_epoch": current.epoch,
                "state_digest": current.state_digest,
            },
            "relabels_cohort_observation_as_current": False,
        }
        packet = coordinator_summary(
            str(lease["node_id"]), current, str(lease["scope"]), payload
        )
        receipt = self.coordinator_commit(
            lease=lease,
            token=token,
            packet=packet,
            expected_epoch=current.epoch,
            expected_digest=current.state_digest,
        )
        return {
            "consumed": consumed,
            "summary_packet": packet,
            "commit_receipt": receipt,
        }


def run() -> dict[str, Any]:
    script = Path(__file__).resolve()
    tests: dict[str, bool] = {}
    t0 = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="xeno-grid10-v3-") as td:
        root = Path(td)
        db = root / "grid10.sqlite"
        barrier = root / "barrier"
        fabric = CohortBoundFabric(db)
        try:
            ids = [f"x{i:02d}" for i in range(1, N + 1)]
            scopes = ["branch:a" if i % 2 == 0 else "branch:b" for i in range(N)]
            for node_id in ids:
                fabric.runtime_register_node(node_id, "reason")
            for scope in ("branch:a", "branch:b", "GLOBAL"):
                fabric.seed_scope(scope)
            for i, scope in enumerate(scopes):
                fabric.seed_task(f"t{i:02d}", scope, 100 - i, "reason", {"q": i})

            cohort_packets, proof = concurrent_probe(script, db, ids, scopes, barrier)
            tests["P1_TEN_DISTINCT_OS_PIDS"] = proof["distinct_os_pids"] == N
            tests["P1_ALL_TEN_SIMULTANEOUSLY_LIVE"] = bool(proof["all_alive_at_barrier"])
            tests["P1_PARENT_CHILD_PID_BINDING"] = bool(proof["pid_binding_ok"])
            tests["P1_PROCESS_INTERVALS_OVERLAP_RELEASE_BARRIER"] = bool(
                proof["interval_overlap_ok"]
            )
            tests["P1_ONE_SHARED_READ_ONLY_S1_SNAPSHOT"] = bool(
                proof["same_snapshot_identity"]
            )
            tests["P2_ORDINARY_RESULTS_ARE_NONWRITING"] = all(
                p.get("s1_write_intent") is False for p in cohort_packets
            )
            expect_error(
                lambda: fabric.ordinary_write_attempt(),
                "ORDINARY_NODE_S1_WRITE_FORBIDDEN",
            )
            tests["P2_ORDINARY_DIRECT_S1_WRITE_REJECTED"] = True

            manifest = build_cohort_manifest(cohort_packets, proof)
            tests["P3_EXACT_PID_TO_PACKET_BINDING"] = len(manifest["members"]) == N
            tests["P3_COHORT_MANIFEST_DIGEST_VALID"] = manifest["manifest_digest"] == dg(
                {k: manifest[k] for k in manifest if k != "manifest_digest"}
            )
            exact_consumption = validate_consumed_packet_set(manifest, cohort_packets)
            tests["P3_EXACT_COHORT_PACKET_SET_CONSUMABLE"] = bool(
                exact_consumption["exact_set_match"]
            )

            # Hard negative: same logical node/snapshot but a different process instance is not C1.
            disjoint = list(cohort_packets)
            disjoint[0] = spawn_one(script, db, ids[0], scopes[0])
            expect_error(
                lambda: validate_consumed_packet_set(manifest, disjoint),
                "COHORT_PACKET_SET_MISMATCH",
            )
            tests["P4_DISJOINT_COHORT_REJECTED"] = True

            # Hard negative: an unused/tampered C1 packet cannot leave the integrated proof unchanged.
            tampered = copy.deepcopy(cohort_packets)
            tampered[1]["payload"]["observation"] = "tampered-unused-packet"
            tampered[1]["packet_digest"] = dg(_packet_core(tampered[1]))
            expect_error(
                lambda: validate_consumed_packet_set(manifest, tampered),
                "COHORT_PACKET_SET_MISMATCH",
            )
            tests["P4_UNUSED_OR_TAMPERED_COHORT_PACKET_REJECTED"] = True

            # Create coordinator authority only after C1 is frozen. This advances S1.
            # C1 remains immutable evidence of its original snapshot; it is not committed as current.
            lease, token = fabric.elect_coordinator("GLOBAL")
            before_summary = fabric.snapshot()
            source_epoch = int(manifest["source_snapshot_identity"][1])
            tests["P5_SOURCE_EVIDENCE_REMAINS_OLD_AFTER_LEASE"] = (
                source_epoch < before_summary.epoch
            )
            integrated = fabric.coordinator_commit_cohort_summary(
                lease=lease,
                token=token,
                manifest=manifest,
                cohort_packets=cohort_packets,
            )
            summary_packet = integrated["summary_packet"]
            tests["P5_SUMMARY_CONSUMES_EXACT_C1_PACKET_SET"] = (
                integrated["consumed"]["packet_digests"]
                == sorted(p["packet_digest"] for p in cohort_packets)
            )
            tests["P5_SUMMARY_REFERENCES_C1_MANIFEST"] = (
                summary_packet["payload"]["cohort_manifest_digest"]
                == manifest["manifest_digest"]
            )
            tests["P5_NO_SILENT_OBSERVATION_RELABEL"] = (
                summary_packet["payload"]["relabels_cohort_observation_as_current"] is False
                and summary_packet["payload"]["cohort_source_snapshot"]["state_epoch"]
                == source_epoch
                and summary_packet["state_epoch"] == before_summary.epoch
            )

            # Preserve v2 fail-closed currentness regression on ordinary results.
            stale_snap = fabric.snapshot()
            stale = Xeno("x01", "reason").result(
                stale_snap, "GLOBAL", {"probe": "stale_epoch"}
            )
            fabric.runtime_set_health("x10", True)
            current = fabric.snapshot()
            expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=stale,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                ),
                "RESULT_STALE_EPOCH",
            )
            tests["P6_STALE_EPOCH_REJECTED"] = True

            current = fabric.snapshot()
            forged = Xeno("x02", "reason").result(
                current, "GLOBAL", {"probe": "wrong_digest"}
            )
            forged = dict(forged)
            forged["state_digest"] = "0" * 64
            forged["packet_digest"] = dg(_packet_core(forged))
            expect_error(
                lambda: fabric.coordinator_commit(
                    lease=lease,
                    token=token,
                    packet=forged,
                    expected_epoch=current.epoch,
                    expected_digest=current.state_digest,
                ),
                "RESULT_STALE_DIGEST",
            )
            tests["P6_DIGEST_MISMATCH_REJECTED"] = True

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            passed = all(tests.values())
            return {
                "schema": SCHEMA,
                "pass": passed,
                "tests": tests,
                "process_overlap_proof": proof,
                "cohort_manifest": manifest,
                "cohort_integration": integrated,
                "metrics": {
                    "concurrent_cohort_members": N,
                    "cohort_packet_digests_consumed": len(
                        integrated["consumed"]["packet_digests"]
                    ),
                    "summary_commits": 1,
                    "elapsed_ms": elapsed_ms,
                },
                "cohort_policy": {
                    "source_packets_are_immutable_observations": True,
                    "source_packets_relabelled_as_current": False,
                    "integration_mode": "EXACT_C1_PACKET_SET_TO_NEW_CURRENT_COORDINATOR_SUMMARY",
                    "disjoint_process_instances_substitutable": False,
                    "missing_or_tampered_cohort_member_substitutable": False,
                },
                "credit_boundary": {
                    "local_component_candidate": "PASS" if passed else "FAIL",
                    "repository_bound_physical_grid10_runtime_credit": False,
                    "whole_hcu": False,
                    "entityos_whole_runtime": False,
                    "semantic_jspace": False,
                    "training": False,
                    "canonical_truth": False,
                    "effect_authority": False,
                },
            }
        finally:
            fabric.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node")
    parser.add_argument("--scope")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--barrier-dir", type=Path)
    args = parser.parse_args()
    if args.node:
        if args.db is None:
            raise SystemExit("--db required with --node")
        return child_node(args.db, args.node, args.scope, args.barrier_dir)
    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
