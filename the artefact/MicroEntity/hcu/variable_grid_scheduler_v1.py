"""Deterministic variable-N logical cognitive-grid scheduler.

This is a source-level HCU primitive. It assigns already-identified semantic
process instances to logical cells. Assignment topology never changes semantic
process identity, and result aggregation never turns majority into truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Sequence

from cognitive_process_abi_v1 import (
    ASSIGNMENT_VERSION,
    CognitiveABIError,
    validate_process_request,
    validate_process_result,
)

SCHEDULER_VERSION = "ENTITYOS_HCU_VARIABLE_GRID_SCHEDULER/v1"


@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    process_instance_id: str
    cell_id: str
    grid_size: int
    replica_index: int
    scheduler_version: str = SCHEDULER_VERSION

    def as_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": ASSIGNMENT_VERSION,
            "assignment_id": self.assignment_id,
            "process_instance_id": self.process_instance_id,
            "cell_id": self.cell_id,
            "grid_size": self.grid_size,
            "replica_index": self.replica_index,
            "scheduler_version": self.scheduler_version,
        }


def _score(process_instance_id: str, cell_index: int, replica_index: int) -> bytes:
    material = (
        SCHEDULER_VERSION + "\x00" + process_instance_id + "\x00" +
        str(cell_index) + "\x00" + str(replica_index)
    ).encode("utf-8")
    return sha256(material).digest()


def assign_process(request: Mapping[str, Any], *, grid_size: int, replicas: int = 1) -> list[Assignment]:
    validate_process_request(request)
    if not isinstance(grid_size, int) or grid_size < 1:
        raise CognitiveABIError("GRID_SIZE_INVALID")
    if not isinstance(replicas, int) or replicas < 1 or replicas > grid_size:
        raise CognitiveABIError("REPLICA_COUNT_INVALID")

    process_instance_id = request["process_instance_id"]
    available = list(range(grid_size))
    assignments: list[Assignment] = []

    for replica_index in range(replicas):
        selected = max(available, key=lambda idx: _score(process_instance_id, idx, replica_index))
        available.remove(selected)
        cell_id = f"cell-{selected:04d}"
        assignment_material = (
            f"{SCHEDULER_VERSION}|{process_instance_id}|{grid_size}|"
            f"{replica_index}|{cell_id}"
        ).encode("utf-8")
        assignment_id = sha256(assignment_material).hexdigest()
        assignments.append(Assignment(
            assignment_id=assignment_id,
            process_instance_id=process_instance_id,
            cell_id=cell_id,
            grid_size=grid_size,
            replica_index=replica_index,
        ))
    return assignments


def aggregate_candidate_results(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Preserve alternatives and disagreement; never majority-promote truth."""
    if not results:
        raise CognitiveABIError("NO_RESULTS")
    checked = [validate_process_result(r) for r in results]
    ids = {r["process_instance_id"] for r in checked}
    process_ids = {r["process_id"] for r in checked}
    if len(ids) != 1 or len(process_ids) != 1:
        raise CognitiveABIError("RESULT_IDENTITY_MISMATCH")

    alternatives = []
    for idx, result in enumerate(checked):
        alternatives.append({
            "source_result_index": idx,
            "candidates": result.get("candidates", []),
            "evidence_refs": result.get("evidence_refs", []),
            "uncertainty": result.get("uncertainty"),
            "db_write_proposals": result.get("db_write_proposals", []),
            "effect_proposals": result.get("effect_proposals", []),
        })

    candidate_signatures = {repr(item["candidates"]) for item in alternatives}
    return {
        "schema_version": "ENTITYOS_HCU_AGGREGATED_CANDIDATES/v1",
        "process_instance_id": checked[0]["process_instance_id"],
        "process_id": checked[0]["process_id"],
        "alternatives": alternatives,
        "agreement_state": (
            "IDENTICAL_CANDIDATE_PAYLOADS" if len(candidate_signatures) == 1
            else "UNRESOLVED_DISAGREEMENT"
        ),
        "truth_promotion": "FORBIDDEN_BY_AGGREGATION",
        "next_authority": "DETERMINISTIC_EVIDENCE_ADMISSION_OR_EXTERNAL_DISCRIMINATOR",
    }
