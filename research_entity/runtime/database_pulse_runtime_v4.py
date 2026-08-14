from __future__ import annotations

"""FRANK Database Pulse Runtime V4 research candidate.

V4 preserves the owner-fixed semantic/runtime contract from Runtime V3 while separating the
semantic candidate-order invariant from its physical acceleration strategy.

Without an explicit measured rank policy provider V4 fails conservative to the correct online
StateLedger ORDER BY SCORE_EXPR path and MUST NOT create an index. A provider may inject U16
compile economics plus completed Pulse read-lifetime telemetry; only then may
AdaptiveAuthoritativeRankPathV4 admit the physical expression index.

Model output remains epistemic UNKNOWN. Pulse/model/selection state has no effect authority.
This is a candidate, not a promoted Harness component.
"""

from dataclasses import dataclass
from typing import Any, Callable

from research_entity.harness.reference.state_ledger import StaleEpoch, cjson, h
from research_entity.runtime.database_pulse_candidate_v1 import (
    DatabasePulseRuntime,
    PulseIntegrityError,
    PulseReceipt,
    PulseSpec,
    PULSE_CONTRACT,
)
from research_entity.runtime.database_pulse_rank_path_v4 import (
    AdaptiveAuthoritativeRankPathV4,
    IMPLEMENTATION_ID as RANK_IMPLEMENTATION_ID,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


IMPLEMENTATION_ID_V4 = "database_pulse_runtime_v4_adaptive_authoritative_rank"


@dataclass(frozen=True)
class PulseRankPolicyV4:
    economics_without_horizon: CompileEconomics
    pulse_history: tuple[EpochReadLifetime, ...]
    provenance_ref: str

    def validate(self) -> None:
        if not isinstance(self.provenance_ref, str) or not self.provenance_ref.strip():
            raise ValueError("rank policy provenance_ref required")


class DatabasePulseRuntimeV4(DatabasePulseRuntime):
    def __init__(
        self,
        ledger,
        *,
        rank_policy_provider: Callable[[PulseSpec], PulseRankPolicyV4] | None = None,
    ):
        super().__init__(ledger)
        self.rank_path = AdaptiveAuthoritativeRankPathV4(ledger)
        self.rank_policy_provider = rank_policy_provider

    @staticmethod
    def _safe_unmeasured_policy() -> PulseRankPolicyV4:
        # Zero read saving guarantees ONLINE. Empty history independently guarantees the
        # conservative insufficient-history path. Values are not claimed as measurements.
        return PulseRankPolicyV4(
            economics_without_horizon=CompileEconomics(
                build_cost_us=0.0,
                online_query_us=0.0,
                compiled_query_us=0.0,
                online_quality=1.0,
                compiled_quality=1.0,
                expected_reads_before_invalidation=0.0,
                safety_factor=1.2,
            ),
            pulse_history=(),
            provenance_ref="UNMEASURED_FAIL_ONLINE",
        )

    def run_pulse(
        self,
        spec: PulseSpec,
        *,
        writer: str = "database-pulse-runtime-v4",
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        committed_at: str | None = None,
    ) -> PulseReceipt:
        if not spec.pulse_id.strip():
            raise ValueError("pulse_id required")
        mode = spec.reentry_mode.upper()
        if mode not in {"TRUTHFUL", "NO_REENTRY", "SHUFFLED_CONTROL", "PROVENANCE_BROKEN_CONTROL"}:
            raise ValueError(f"unsupported reentry mode: {spec.reentry_mode}")
        if not spec.source_domains or any(d in {"pulse", "pulse_control"} for d in spec.source_domains):
            raise ValueError("source_domains must be explicit and exclude pulse control/output domains")
        if not (1 <= spec.max_candidates <= self.MAX_CANDIDATES_HARD):
            raise ValueError("max_candidates out of bounds")
        if not (1 <= spec.max_focus <= min(spec.max_candidates, self.MAX_FOCUS_HARD)):
            raise ValueError("max_focus out of bounds")

        existing = self._existing_receipt(spec)
        if existing is not None:
            return existing
        current_schema = self.validate_integrity(full=False)
        if current_schema != self.schema_fingerprint:
            raise PulseIntegrityError("runtime schema changed after initialization")
        enabled, scheduler_hash = self._scheduler()
        if not enabled:
            return super().run_pulse(
                spec, writer=writer, model_assistant=model_assistant, committed_at=committed_at
            )
        if int(spec.basis_epoch) != self.ledger.epoch:
            raise StaleEpoch(f"pulse basis {spec.basis_epoch}!={self.ledger.epoch}")

        previous = self._previous_pulse()
        previous_focus = tuple(str(x) for x in (previous or {}).get("focus_refs", []))
        shuffle_salt = None
        if mode == "SHUFFLED_CONTROL" and previous is not None:
            shuffle_salt = h({"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"})

        policy = self.rank_policy_provider(spec) if self.rank_policy_provider is not None else self._safe_unmeasured_policy()
        if not isinstance(policy, PulseRankPolicyV4):
            raise TypeError("rank_policy_provider must return PulseRankPolicyV4")
        policy.validate()
        selection = self.rank_path.select(
            source_domains=tuple(dict.fromkeys(spec.source_domains)),
            basis_epoch=spec.basis_epoch,
            max_candidates=spec.max_candidates,
            max_focus=spec.max_focus,
            economics_without_horizon=policy.economics_without_horizon,
            pulse_history=policy.pulse_history,
            reentry_mode=mode,
            previous_focus_refs=previous_focus,
            shuffle_salt=shuffle_salt,
        )
        if selection.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch("adaptive rank semantic root changed before pulse commit")

        focus_refs = list(selection.focus_refs)
        focus_source_hashes = []
        focus_context = []
        for ref, score in zip(selection.candidate_refs, selection.candidate_scores):
            if ref not in selection.focus_refs:
                continue
            domain, key = ref.split(":", 1)
            row = self.ledger.get(domain, key)
            if row is None or row["epistemic"] != "KNOWN" or row["status"] != "CURRENT":
                raise PulseIntegrityError(f"adaptive rank selected invalid current known ref: {ref}")
            focus_source_hashes.append(row["semantic_hash"])
            focus_context.append({
                "ref": ref,
                "score": score,
                "source_semantic_hash": row["semantic_hash"],
                "domain_epoch": row["domain_epoch"],
                "value": row["value"],
            })

        reentry_targets: set[str] = set()
        if previous is not None and mode == "TRUTHFUL":
            reentry_targets = set(previous_focus) & set(selection.candidate_refs)
        elif previous is not None and mode == "SHUFFLED_CONTROL":
            salt = shuffle_salt or h({"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"})
            shuffled = sorted(selection.candidate_refs, key=lambda ref: h({"salt": salt, "ref": ref}))
            reentry_targets = set(shuffled[: min(len(previous_focus), len(shuffled))])

        assembly_hash = h({
            "basis_epoch": spec.basis_epoch,
            "input_semantic_state_hash": selection.semantic_state_hash,
            "reentry_mode": mode,
            "candidate_generation": RANK_IMPLEMENTATION_ID,
            "selection_hash": selection.selection_hash,
            "physical_mode": selection.physical_mode,
            "focus_refs": focus_refs,
            "focus_source_hashes": focus_source_hashes,
        })

        model_output: Any = None
        model_call_delta = 0
        model_candidate_hash: str | None = None
        if model_assistant is not None:
            model_context = {
                "pulse_id": spec.pulse_id,
                "basis_epoch": spec.basis_epoch,
                "assembly_hash": assembly_hash,
                "focus": focus_context,
                "candidate_generation": RANK_IMPLEMENTATION_ID,
                "physical_rank_mode": selection.physical_mode,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            }
            model_output = model_assistant(model_context)
            cjson(model_output)
            model_candidate_hash = h(model_output)
            model_call_delta = 1

        # Pulse bookkeeping and an unadmitted UNKNOWN model hypothesis are not substantive
        # world/self state transitions. Keep this observable correction from Runtime V3.
        truthful_reentry = int(mode == "TRUTHFUL" and bool(reentry_targets))
        deltas = {
            "pulse_count": 1,
            "state_transition_count": 0,
            "graph_change": 0,
            "hypothesis_count": int(model_output is not None),
            "memory_update": 0,
            "reentry_count": truthful_reentry,
            "model_call_count": model_call_delta,
            "tool_call_count": 0,
            "effect_count": 0,
        }
        cumulative = self._metrics()
        for key, delta in deltas.items():
            cumulative[key] += delta

        body: dict[str, Any] = {
            "implementation": IMPLEMENTATION_ID_V4,
            "pulse_contract": PULSE_CONTRACT,
            "pulse_id": spec.pulse_id,
            "basis_epoch": spec.basis_epoch,
            "committed_epoch": spec.basis_epoch + 1,
            "input_semantic_state_hash": selection.semantic_state_hash,
            "query_hash": selection.selection_hash,
            "query_truncated": selection.query_truncated,
            "candidate_generation": RANK_IMPLEMENTATION_ID,
            "candidate_count": len(selection.candidate_refs),
            "candidate_universe_count": selection.candidate_universe_count,
            "candidate_budget": spec.max_candidates,
            "physical_rank_mode": selection.physical_mode,
            "rank_index_present_before": selection.index_present_before,
            "rank_index_present_after": selection.index_present_after,
            "rank_horizon_status": selection.horizon_status,
            "rank_horizon_reads_lower_bound": selection.horizon_reads_lower_bound,
            "rank_compile_reason": selection.compile_reason,
            "rank_guarded_break_even_reads": selection.guarded_break_even_reads,
            "rank_policy_provenance_ref": policy.provenance_ref,
            "rank_query_plan": list(selection.query_plan),
            "scheduler_semantic_hash": scheduler_hash,
            "schema_fingerprint": self.schema_fingerprint,
            "source_domains": list(spec.source_domains),
            "focus_refs": focus_refs,
            "focus_source_hashes": focus_source_hashes,
            "assembly_hash": assembly_hash,
            "conflicts_present": selection.conflicts_present,
            "unknown_present": selection.unknown_present,
            "reentry_mode": mode,
            "reentry_target_refs": sorted(reentry_targets),
            "model_candidate_hash": model_candidate_hash,
            "observables": deltas,
            "cumulative_observables": cumulative,
            "authority": "ASSEMBLY_CONTEXT_ONLY",
            "effect_authority": "NONE",
        }
        body["receipt_hash"] = h(body)

        ops: list[dict[str, Any]] = [
            {"op": "SET", "domain": "pulse", "key": "latest", "value": body,
             "epistemic": "KNOWN", "status": "CURRENT"},
            {"op": "SET", "domain": "pulse", "key": "metrics", "value": cumulative,
             "epistemic": "KNOWN", "status": "CURRENT"},
        ]
        if model_output is not None:
            ops.append({
                "op": "SET", "domain": "pulse", "key": "model_candidate",
                "value": {
                    "pulse_id": spec.pulse_id,
                    "candidate": model_output,
                    "candidate_hash": model_candidate_hash,
                    "authority": "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
                },
                "epistemic": "UNKNOWN", "status": "CURRENT",
            })

        event_id = f"database-pulse:{spec.pulse_id}"
        result = self.ledger.append_event(
            event_id=event_id,
            idem=event_id,
            base_epoch=spec.basis_epoch,
            event_type="DATABASE_PULSE",
            writer=writer,
            ops=ops,
            provenance={
                "pulse_contract": PULSE_CONTRACT,
                "implementation": IMPLEMENTATION_ID_V4,
                "candidate_generation": RANK_IMPLEMENTATION_ID,
                "selection_hash": selection.selection_hash,
                "rank_policy_provenance_ref": policy.provenance_ref,
                "physical_rank_mode": selection.physical_mode,
                "receipt_hash": body["receipt_hash"],
                "reentry_mode": mode,
            },
            source={
                "basis_semantic_state_hash": selection.semantic_state_hash,
                "query_hash": selection.selection_hash,
                "focus_source_hashes": focus_source_hashes,
            },
            execution={
                "model_call_count": model_call_delta,
                "tool_call_count": 0,
                "effect_count": 0,
                "effect_authority": "NONE",
            },
            **({"committed_at": committed_at} if committed_at is not None else {}),
        )
        return PulseReceipt(
            status=str(result["status"]), pulse_id=spec.pulse_id, basis_epoch=spec.basis_epoch,
            committed_epoch=int(result["epoch"]), input_semantic_state_hash=selection.semantic_state_hash,
            output_semantic_state_hash=str(result["semantic_state_hash"]), trace_root_hash=str(result["trace_root_hash"]),
            focus_refs=tuple(focus_refs), assembly_hash=assembly_hash,
            conflicts_present=selection.conflicts_present, unknown_present=selection.unknown_present,
            pulse_count=1, state_transition_count=0, graph_change=0,
            hypothesis_count=int(model_output is not None), memory_update=0,
            reentry_count=truthful_reentry,
            model_call_count=model_call_delta, tool_call_count=0, effect_count=0,
            schema_fingerprint=self.schema_fingerprint, receipt_hash=body["receipt_hash"],
        )
