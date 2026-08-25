#!/usr/bin/env python3
"""Fail-closed provenance boundary for Trigger-2 physical GRID10 cohort evidence.

This module does not create a second cohort authority. The existing FusedFabric atomic
cohort transaction remains the sole deterministic persistence primitive. This wrapper
adds a capability-style, in-process provenance boundary around the *physical evidence*
claim:

* callers cannot present an arbitrary ``dict`` as a physical cohort witness;
* the only public mint path invokes the retained ``spawn_held_cohort`` observer itself;
* the witness is bound to one boundary instance, one FusedFabric instance, the exact
  observer script bytes/path, database path, observed node set, packet digests, and the
  complete proof payload;
* tamper/transplant/raw-dictionary paths fail before delegation;
* the delegated FusedFabric receipt still grants zero runtime/promotion credit by itself.

The seal is intentionally an in-process capability seal, not a security claim against
arbitrary code execution or memory introspection inside the same Python interpreter.
Physical GRID10 runtime credit still requires separately admitted exact-source execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
from pathlib import Path
import secrets
from typing import Any, Mapping, Sequence

try:
    from tools.trigger2_grid10_fused_physical_membership_cohort_acceptance_v1 import (
        N,
        spawn_held_cohort,
    )
except ModuleNotFoundError:  # direct tool execution compatibility
    from trigger2_grid10_fused_physical_membership_cohort_acceptance_v1 import (
        N,
        spawn_held_cohort,
    )

SCHEMA = "CLAY_TRIGGER2_PHYSICAL_COHORT_WITNESS_BOUNDARY/v1"
WITNESS_SCHEMA = "CLAY_TRIGGER2_PHYSICAL_COHORT_WITNESS/v1"


class PhysicalWitnessError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise PhysicalWitnessError(code)


@dataclass(frozen=True, slots=True)
class PhysicalCohortWitness:
    schema: str
    boundary_id: str
    fabric_instance_id: int
    observer_script_path: str
    observer_script_sha256: str
    observed_db_path: str
    observed_node_ids: tuple[str, ...]
    packet_digests: tuple[str, ...]
    proof_json: str
    witness_sha256: str
    seal_sha256: str

    def proof_copy(self) -> dict[str, Any]:
        value = json.loads(self.proof_json)
        if not isinstance(value, dict):
            raise PhysicalWitnessError("PHYSICAL_WITNESS_PROOF_NOT_OBJECT")
        return value


class PhysicalCohortWitnessBoundary:
    """Request-local capability boundary for the retained physical observation path."""

    __slots__ = ("__seal_key", "__boundary_id")

    def __init__(self) -> None:
        key = secrets.token_bytes(32)
        self.__seal_key = key
        self.__boundary_id = sha256(b"trigger2-physical-witness-boundary:" + key).hexdigest()

    @property
    def boundary_id(self) -> str:
        return self.__boundary_id

    @staticmethod
    def _validate_observed_proof(proof: Mapping[str, Any]) -> None:
        _require(
            proof.get("synthetic_source_fixture_only") is not True,
            "SYNTHETIC_SOURCE_FIXTURE_FORBIDDEN_AT_PHYSICAL_BOUNDARY",
        )
        required = {
            "all_alive_at_barrier": proof.get("all_alive_at_barrier") is True,
            "ten_distinct_os_pids": proof.get("distinct_os_pids") == N,
            "parent_child_pid_binding": proof.get("parent_child_pid_binding") is True,
            "same_snapshot_identity": proof.get("same_snapshot_identity") is True,
            "all_transactions_open_at_barrier": proof.get("all_transactions_open_at_barrier") is True,
            "all_hold_readonly_s1_fd_at_barrier": proof.get("all_hold_readonly_s1_fd_at_barrier") is True,
            "writer_free_identity_stable": proof.get("writer_free_identity_stable") is True,
            "process_intervals_overlap_release": proof.get("process_intervals_overlap_release") is True,
        }
        failed = sorted(name for name, ok in required.items() if not ok)
        _require(
            not failed,
            "PHYSICAL_OBSERVER_PROOF_INCOMPLETE:" + ",".join(failed),
        )

    def observe(
        self,
        fabric: Any,
        *,
        script: Path,
        db: Path,
        node_ids: Sequence[str],
        root: Path,
    ) -> tuple[list[dict[str, Any]], PhysicalCohortWitness]:
        """Invoke the retained observer and mint a sealed witness from its direct result."""
        _require(len(node_ids) == N, "PHYSICAL_OBSERVER_NODE_COUNT_INVALID")
        _require(len(set(node_ids)) == N, "PHYSICAL_OBSERVER_NODE_ID_DUPLICATE")
        script = script.resolve()
        db = db.resolve()
        _require(script.is_file(), "PHYSICAL_OBSERVER_SCRIPT_NOT_FILE")

        packets, proof = spawn_held_cohort(
            fabric,
            script,
            db,
            list(node_ids),
            root,
        )
        _require(isinstance(proof, Mapping), "PHYSICAL_OBSERVER_PROOF_NOT_MAPPING")
        self._validate_observed_proof(proof)
        _require(len(packets) == N, "PHYSICAL_OBSERVER_PACKET_COUNT_INVALID")

        packet_digests: list[str] = []
        for packet in packets:
            _require(isinstance(packet, Mapping), "PHYSICAL_OBSERVER_PACKET_NOT_MAPPING")
            packet_digest = packet.get("packet_digest")
            _require(
                isinstance(packet_digest, str) and len(packet_digest) == 64,
                "PHYSICAL_OBSERVER_PACKET_DIGEST_INVALID",
            )
            packet_digests.append(packet_digest)
        _require(
            len(set(packet_digests)) == N,
            "PHYSICAL_OBSERVER_PACKET_DIGEST_DUPLICATE",
        )

        proof_json = canonical_json(dict(proof))
        core = {
            "schema": WITNESS_SCHEMA,
            "boundary_id": self.__boundary_id,
            "fabric_instance_id": id(fabric),
            "observer_script_path": str(script),
            "observer_script_sha256": sha256(script.read_bytes()).hexdigest(),
            "observed_db_path": str(db),
            "observed_node_ids": tuple(node_ids),
            "packet_digests": tuple(sorted(packet_digests)),
            "proof": json.loads(proof_json),
        }
        witness_sha256 = digest(core)
        seal_sha256 = hmac.new(
            self.__seal_key,
            witness_sha256.encode("ascii"),
            sha256,
        ).hexdigest()
        witness = PhysicalCohortWitness(
            schema=WITNESS_SCHEMA,
            boundary_id=self.__boundary_id,
            fabric_instance_id=id(fabric),
            observer_script_path=str(script),
            observer_script_sha256=core["observer_script_sha256"],
            observed_db_path=str(db),
            observed_node_ids=tuple(node_ids),
            packet_digests=tuple(sorted(packet_digests)),
            proof_json=proof_json,
            witness_sha256=witness_sha256,
            seal_sha256=seal_sha256,
        )
        return packets, witness

    def _validate_witness(
        self,
        fabric: Any,
        witness: PhysicalCohortWitness,
        envelopes: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        _require(
            isinstance(witness, PhysicalCohortWitness),
            "PHYSICAL_COHORT_WITNESS_REQUIRED",
        )
        _require(witness.schema == WITNESS_SCHEMA, "PHYSICAL_WITNESS_SCHEMA_INVALID")
        _require(
            witness.boundary_id == self.__boundary_id,
            "PHYSICAL_WITNESS_BOUNDARY_TRANSPLANT",
        )
        _require(
            witness.fabric_instance_id == id(fabric),
            "PHYSICAL_WITNESS_FABRIC_TRANSPLANT",
        )
        proof = witness.proof_copy()
        self._validate_observed_proof(proof)

        core = {
            "schema": witness.schema,
            "boundary_id": witness.boundary_id,
            "fabric_instance_id": witness.fabric_instance_id,
            "observer_script_path": witness.observer_script_path,
            "observer_script_sha256": witness.observer_script_sha256,
            "observed_db_path": witness.observed_db_path,
            "observed_node_ids": witness.observed_node_ids,
            "packet_digests": witness.packet_digests,
            "proof": proof,
        }
        _require(
            digest(core) == witness.witness_sha256,
            "PHYSICAL_WITNESS_DIGEST_MISMATCH",
        )
        expected_seal = hmac.new(
            self.__seal_key,
            witness.witness_sha256.encode("ascii"),
            sha256,
        ).hexdigest()
        _require(
            hmac.compare_digest(expected_seal, witness.seal_sha256),
            "PHYSICAL_WITNESS_SEAL_MISMATCH",
        )

        envelope_packet_digests: list[str] = []
        for envelope in envelopes:
            _require(isinstance(envelope, Mapping), "PHYSICAL_COMMIT_ENVELOPE_NOT_MAPPING")
            packet = envelope.get("node_result")
            _require(isinstance(packet, Mapping), "PHYSICAL_COMMIT_NODE_RESULT_REQUIRED")
            packet_digest = packet.get("packet_digest")
            _require(
                isinstance(packet_digest, str) and len(packet_digest) == 64,
                "PHYSICAL_COMMIT_PACKET_DIGEST_INVALID",
            )
            _require(
                envelope.get("node_result_digest") == packet_digest,
                "PHYSICAL_COMMIT_PACKET_REFERENCE_MISMATCH",
            )
            envelope_packet_digests.append(packet_digest)
        _require(len(envelopes) == N, "PHYSICAL_COMMIT_MEMBER_COUNT_INVALID")
        _require(
            tuple(sorted(envelope_packet_digests)) == witness.packet_digests,
            "PHYSICAL_WITNESS_ENVELOPE_PACKET_SET_MISMATCH",
        )
        return proof

    def atomic_fused_physical_commit(
        self,
        fabric: Any,
        *,
        witness: PhysicalCohortWitness,
        envelopes: Sequence[Mapping[str, Any]],
        **commit_kwargs: Any,
    ) -> dict[str, Any]:
        """Validate provenance first, then delegate once to the existing fused transaction."""
        proof = self._validate_witness(fabric, witness, envelopes)
        receipt = fabric.atomic_fused_cohort_commit(
            envelopes=list(envelopes),
            proof=proof,
            **commit_kwargs,
        )
        return {
            "schema": SCHEMA,
            "physical_witness_sha256": witness.witness_sha256,
            "physical_witness_boundary_id": witness.boundary_id,
            "raw_proof_dictionary_accepted_at_physical_boundary": False,
            "delegated_effect_path": "EXISTING_FUSED_FABRIC_ATOMIC_COHORT_COMMIT_ONLY",
            "fused_coordinator_receipt": receipt,
            "canonical_truth": False,
            "effect_authority": False,
            "credit_boundary": {
                "source_boundary_credit": 1,
                "physical_grid10_runtime_credit": 0,
                "model_call_runtime_credit": 0,
                "jspace_model_credit": 0,
                "training_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
            },
        }
