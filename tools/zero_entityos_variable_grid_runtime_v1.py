from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable, Mapping, Protocol


class GridRuntimeError(RuntimeError):
    pass


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class StateAuthority(Protocol):
    """External deterministic state authority. The grid runtime is read/propose only."""

    def current_generation(self) -> int: ...

    def snapshot_digest(self, generation: int) -> str: ...

    def read_slice(self, generation: int, keys: tuple[str, ...]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class EphemeralGridLease:
    generation: int
    lease_id: str
    executor_instance_id: str
    eligible_process_ids: tuple[str, ...]
    budget_digest: str
    expires_at: int

    @property
    def lease_digest(self) -> str:
        return canonical_digest(
            {
                "generation": self.generation,
                "lease_id": self.lease_id,
                "executor_instance_id": self.executor_instance_id,
                "eligible_process_ids": list(self.eligible_process_ids),
                "budget_digest": self.budget_digest,
                "expires_at": self.expires_at,
            }
        )


@dataclass(frozen=True)
class CognitiveWork:
    causal_event_id: str
    admission_id: str
    generation: int
    work_id: str
    process_id: str
    parent_work_ids: tuple[str, ...]
    db_snapshot_digest: str
    workspace_digest: str
    input_digest: str
    capability_scope_digest: str
    budget_digest: str
    provenance_digest: str
    state_keys: tuple[str, ...]
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class CognitiveResult:
    causal_event_id: str
    admission_id: str
    generation: int
    work_id: str
    process_id: str
    executor_instance_id: str
    model_artifact_digest: str
    input_digest: str
    output_digest: str
    result_kind: str
    uncertainty: str
    provenance_digest: str
    output: Mapping[str, Any]

    def wire(self) -> dict[str, Any]:
        return {
            "causal_event_id": self.causal_event_id,
            "admission_id": self.admission_id,
            "generation": self.generation,
            "work_id": self.work_id,
            "process_id": self.process_id,
            "executor_instance_id": self.executor_instance_id,
            "model_artifact_digest": self.model_artifact_digest,
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
            "result_kind": self.result_kind,
            "uncertainty": self.uncertainty,
            "provenance_digest": self.provenance_digest,
        }


ProcessHandler = Callable[[CognitiveWork, Mapping[str, Any]], tuple[str, str, Mapping[str, Any]]]


class VariableGridNode:
    """One role-free logical node. It can execute any leased process handler.

    It has no canonical DB write or real-effect method by design. Those outputs are proposals.
    """

    def __init__(
        self,
        *,
        executor_instance_id: str,
        model_artifact_digest: str,
        state_authority: StateAuthority,
        handlers: Mapping[str, ProcessHandler],
    ) -> None:
        if not executor_instance_id:
            raise GridRuntimeError("EXECUTOR_ID_REQUIRED")
        if not model_artifact_digest:
            raise GridRuntimeError("MODEL_ARTIFACT_DIGEST_REQUIRED")
        self.executor_instance_id = executor_instance_id
        self.model_artifact_digest = model_artifact_digest
        self._state = state_authority
        self._handlers = dict(handlers)

    def execute(self, work: CognitiveWork, lease: EphemeralGridLease, *, logical_tick: int) -> CognitiveResult:
        if lease.executor_instance_id != self.executor_instance_id:
            raise GridRuntimeError("LEASE_EXECUTOR_MISMATCH")
        if logical_tick > lease.expires_at:
            raise GridRuntimeError("LEASE_EXPIRED")
        if work.process_id not in lease.eligible_process_ids:
            raise GridRuntimeError("PROCESS_NOT_LEASED")
        if work.process_id not in self._handlers:
            raise GridRuntimeError("PROCESS_HANDLER_UNAVAILABLE")
        if work.budget_digest != lease.budget_digest:
            raise GridRuntimeError("BUDGET_BINDING_MISMATCH")

        current_generation = self._state.current_generation()
        if work.generation != current_generation or lease.generation != current_generation:
            raise GridRuntimeError("STALE_GENERATION")
        observed_snapshot = self._state.snapshot_digest(work.generation)
        if work.db_snapshot_digest != observed_snapshot:
            raise GridRuntimeError("DB_SNAPSHOT_DIGEST_MISMATCH")

        state_slice = self._state.read_slice(work.generation, work.state_keys)
        result_kind, uncertainty, output = self._handlers[work.process_id](work, state_slice)
        if result_kind not in {"CANDIDATE", "PROJECTION", "MEASUREMENT", "ABSTAINED", "BLOCKED"}:
            raise GridRuntimeError("CANONICAL_RESULT_KIND_FORBIDDEN")
        output_dict = dict(output)
        output_digest = canonical_digest(
            {
                "causal_event_id": work.causal_event_id,
                "generation": work.generation,
                "work_id": work.work_id,
                "process_id": work.process_id,
                "executor_instance_id": self.executor_instance_id,
                "state_slice_digest": canonical_digest(dict(state_slice)),
                "payload_digest": canonical_digest(dict(work.payload)),
                "output": output_dict,
            }
        )
        return CognitiveResult(
            causal_event_id=work.causal_event_id,
            admission_id=work.admission_id,
            generation=work.generation,
            work_id=work.work_id,
            process_id=work.process_id,
            executor_instance_id=self.executor_instance_id,
            model_artifact_digest=self.model_artifact_digest,
            input_digest=work.input_digest,
            output_digest=output_digest,
            result_kind=result_kind,
            uncertainty=uncertainty,
            provenance_digest=work.provenance_digest,
            output=output_dict,
        )

    @staticmethod
    def propose_db_write(work: CognitiveWork, expected_db_snapshot_digest: str, proposal: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema": "DB_WRITE_PROPOSAL/v1",
            "causal_event_id": work.causal_event_id,
            "generation": work.generation,
            "expected_db_snapshot_digest": expected_db_snapshot_digest,
            "proposal_digest": canonical_digest(dict(proposal)),
            "provenance_digest": work.provenance_digest,
            "authority": "PROPOSAL_ONLY",
            "commit_rule": "DETERMINISTIC_DB_GATE_AND_CAS_REQUIRED",
        }

    @staticmethod
    def propose_effect(work: CognitiveWork, effect_request: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema": "EFFECT_PROPOSAL/v1",
            "causal_event_id": work.causal_event_id,
            "generation": work.generation,
            "effect_request_digest": canonical_digest(dict(effect_request)),
            "capability_scope_digest": work.capability_scope_digest,
            "provenance_digest": work.provenance_digest,
            "authority": "PROPOSAL_ONLY",
            "execution_rule": "EFFECTGATE_EFFECTJOURNAL_REQUIRED",
        }


class VariableGridRuntime:
    """Scheduler shell. `n` affects available executors, never packet semantics or authority."""

    def __init__(self, n: int) -> None:
        if n < 1:
            raise GridRuntimeError("GRID_N_MUST_BE_POSITIVE")
        self.n = n

    @staticmethod
    def wire_semantics_fingerprint() -> str:
        return canonical_digest(
            {
                "schema": "ZERO_ENTITYOS_VARIABLE_GRID_RUNTIME/v1",
                "work": "COGNITIVE_WORK/v1",
                "result": "COGNITIVE_RESULT/v1",
                "lease": "EPHEMERAL_GRID_LEASE/v1",
                "db_write": "PROPOSAL_ONLY_DETERMINISTIC_GATE_CAS",
                "effect": "PROPOSAL_ONLY_EFFECTGATE_EFFECTJOURNAL",
                "grid_size_law": "N_IS_RUNTIME_PARAMETER",
            }
        )
