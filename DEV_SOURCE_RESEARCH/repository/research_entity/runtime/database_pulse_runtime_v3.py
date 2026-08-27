from __future__ import annotations

"""FRANK Database Pulse Runtime V3 research candidate.

V3 keeps the owner-fixed Database Pulse continuity/scheduler/provenance/model-quarantine and
re-entry contract, but removes the second Active Field candidate table. Candidate ordering is
served by a rebuildable SQLite partial expression index directly over the authoritative
StateLedger state table.

The index is physical implementation state only. It never becomes semantic truth or effect
authority. Pulse receipt/metric writes are observability bookkeeping, and optional model output
remains an UNKNOWN hypothesis; neither is counted as an admitted semantic state transition.

Research candidate only. No canonical/Harness promotion is implied.
"""

import json
from typing import Any, Callable

from research_entity.harness.reference.state_ledger import StaleEpoch, cjson, h
from research_entity.runtime.database_pulse_candidate_v1 import (
    DatabasePulseRuntime,
    PulseIntegrityError,
    PulseReceipt,
    PulseSpec,
    PULSE_CONTRACT,
)
from research_entity.runtime.database_pulse_rank_index_v3 import (
    AuthoritativeRankIndexV3,
    IMPLEMENTATION_ID as RANK_INDEX_IMPLEMENTATION_ID,
    INDEX_NAME,
    REENTRY_BOOST,
    SCORE_EXPR,
)


IMPLEMENTATION_ID_V3 = "database_pulse_runtime_v3_authoritative_rank_index"


class DatabasePulseRuntimeV3(DatabasePulseRuntime):
    """StateLedger Pulse with no second candidate table."""

    def __init__(self, ledger):
        super().__init__(ledger)
        self.rank_index = AuthoritativeRankIndexV3(ledger)

    def _authoritative_focus_row(self, ref: str) -> dict[str, Any]:
        if ":" not in ref:
            raise PulseIntegrityError(f"invalid rank-index ref: {ref}")
        domain, key = ref.split(":", 1)
        row = self.ledger.get(domain, key)
        if row is None or row["status"] != "CURRENT" or row["epistemic"] != "KNOWN":
            raise PulseIntegrityError(f"rank-index selected missing/non-admissible ref: {ref}")
        return row

    @staticmethod
    def _reentry_targets(
        *,
        mode: str,
        previous: dict[str, Any] | None,
        candidate_refs: tuple[str, ...],
    ) -> set[str]:
        if previous is None or mode in {"NO_REENTRY", "PROVENANCE_BROKEN_CONTROL"}:
            return set()
        previous_focus = [str(x) for x in previous.get("focus_refs", [])]
        if mode == "TRUTHFUL":
            return set(previous_focus) & set(candidate_refs)
        salt = h({"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"})
        shuffled = sorted(candidate_refs, key=lambda ref: h({"salt": salt, "ref": ref}))
        return set(shuffled[: min(len(previous_focus), len(shuffled))])

    def run_pulse(
        self,
        spec: PulseSpec,
        *,
        writer: str = "database-pulse-runtime-v3",
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
            shuffle_salt = h(
                {"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"}
            )

        root_before_index = (
            self.ledger.epoch,
            self.ledger.semantic_state_hash,
            self.ledger.trace_root_hash,
        )
        selection = self.rank_index.select(
            source_domains=tuple(dict.fromkeys(spec.source_domains)),
            basis_epoch=spec.basis_epoch,
            max_candidates=spec.max_candidates,
            max_focus=spec.max_focus,
            reentry_mode=mode,
            previous_focus_refs=previous_focus,
            shuffle_salt=shuffle_salt,
        )
        if root_before_index != (
            self.ledger.epoch,
            self.ledger.semantic_state_hash,
            self.ledger.trace_root_hash,
        ):
            raise PulseIntegrityError("physical rank-index operation mutated semantic ledger roots")
        if selection.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch("rank-index semantic root changed before pulse commit")

        reentry_targets = self._reentry_targets(
            mode=mode,
            previous=previous,
            candidate_refs=selection.candidate_refs,
        )
        focus: list[dict[str, Any]] = []
        for ref in selection.focus_refs:
            row = self._authoritative_focus_row(ref)
            base_score, signals = self._signal_score(row.get("value"))
            boost = REENTRY_BOOST if ref in reentry_targets else 0.0
            focus.append(
                {
                    "ref": ref,
                    "score": round(base_score + boost, 8),
                    "base_score": round(base_score, 8),
                    "reentry_boost": boost,
                    "signals": signals,
                    "source_semantic_hash": row["semantic_hash"],
                    "domain_epoch": int(row["domain_epoch"]),
                    "value": row.get("value"),
                }
            )
        focus_refs = [x["ref"] for x in focus]
        assembly_hash = h(
            {
                "basis_epoch": spec.basis_epoch,
                "input_semantic_state_hash": selection.semantic_state_hash,
                "reentry_mode": mode,
                "candidate_generation": RANK_INDEX_IMPLEMENTATION_ID,
                "rank_index_selection_hash": selection.selection_hash,
                "focus": [
                    {k: x[k] for k in ("ref", "score", "source_semantic_hash", "domain_epoch")}
                    for x in focus
                ],
            }
        )

        model_output: Any = None
        model_call_delta = 0
        model_candidate_hash: str | None = None
        if model_assistant is not None:
            model_context = {
                "pulse_id": spec.pulse_id,
                "basis_epoch": spec.basis_epoch,
                "assembly_hash": assembly_hash,
                "focus": focus,
                "candidate_generation": RANK_INDEX_IMPLEMENTATION_ID,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            }
            model_output = model_assistant(model_context)
            cjson(model_output)
            model_candidate_hash = h(model_output)
            model_call_delta = 1

        truthful_reentry = int(mode == "TRUTHFUL" and bool(reentry_targets))
        model_hypothesis_delta = int(model_output is not None)
        # No admitted KNOWN semantic-domain mutation occurs inside V3. Receipt/metrics are
        # bookkeeping; model output is explicitly UNKNOWN. Keep the observables orthogonal.
        state_transition_delta = 0
        deltas = {
            "pulse_count": 1,
            "state_transition_count": state_transition_delta,
            "graph_change": 0,
            "hypothesis_count": model_hypothesis_delta,
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
            "implementation": IMPLEMENTATION_ID_V3,
            "pulse_contract": PULSE_CONTRACT,
            "pulse_id": spec.pulse_id,
            "basis_epoch": spec.basis_epoch,
            "committed_epoch": spec.basis_epoch + 1,
            "input_semantic_state_hash": selection.semantic_state_hash,
            "query_hash": selection.selection_hash,
            "query_truncated": selection.query_truncated,
            "candidate_generation": RANK_INDEX_IMPLEMENTATION_ID,
            "candidate_count": len(selection.candidate_refs),
            "candidate_universe_count": selection.candidate_universe_count,
            "rank_index_name": INDEX_NAME,
            "rank_index_score_expression_hash": h(SCORE_EXPR),
            "rank_index_query_plan": list(selection.query_plan),
            "scheduler_semantic_hash": scheduler_hash,
            "schema_fingerprint": self.schema_fingerprint,
            "source_domains": list(spec.source_domains),
            "focus_refs": focus_refs,
            "focus_source_hashes": [x["source_semantic_hash"] for x in focus],
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
            {
                "op": "SET",
                "domain": "pulse",
                "key": "latest",
                "value": body,
                "epistemic": "KNOWN",
                "status": "CURRENT",
            },
            {
                "op": "SET",
                "domain": "pulse",
                "key": "metrics",
                "value": cumulative,
                "epistemic": "KNOWN",
                "status": "CURRENT",
            },
        ]
        if model_output is not None:
            ops.append(
                {
                    "op": "SET",
                    "domain": "pulse",
                    "key": "model_candidate",
                    "value": {
                        "pulse_id": spec.pulse_id,
                        "candidate": model_output,
                        "candidate_hash": model_candidate_hash,
                        "authority": "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
                    },
                    "epistemic": "UNKNOWN",
                    "status": "CURRENT",
                }
            )

        event_id = f"database-pulse:{spec.pulse_id}"
        append_kwargs = dict(
            event_id=event_id,
            idem=event_id,
            base_epoch=spec.basis_epoch,
            event_type="DATABASE_PULSE",
            writer=writer,
            ops=ops,
            provenance={
                "pulse_contract": PULSE_CONTRACT,
                "implementation": IMPLEMENTATION_ID_V3,
                "candidate_generation": RANK_INDEX_IMPLEMENTATION_ID,
                "rank_index_selection_hash": selection.selection_hash,
                "receipt_hash": body["receipt_hash"],
                "reentry_mode": mode,
            },
            source={
                "basis_semantic_state_hash": selection.semantic_state_hash,
                "query_hash": selection.selection_hash,
                "focus_source_hashes": body["focus_source_hashes"],
                "rank_index_name": INDEX_NAME,
            },
            execution={
                "model_call_count": model_call_delta,
                "tool_call_count": 0,
                "effect_count": 0,
                "effect_authority": "NONE",
            },
        )
        result = self.ledger.append_event(
            **append_kwargs,
            **({"committed_at": committed_at} if committed_at is not None else {}),
        )
        return PulseReceipt(
            status=str(result["status"]),
            pulse_id=spec.pulse_id,
            basis_epoch=spec.basis_epoch,
            committed_epoch=int(result["epoch"]),
            input_semantic_state_hash=selection.semantic_state_hash,
            output_semantic_state_hash=str(result["semantic_state_hash"]),
            trace_root_hash=str(result["trace_root_hash"]),
            focus_refs=tuple(focus_refs),
            assembly_hash=assembly_hash,
            conflicts_present=selection.conflicts_present,
            unknown_present=selection.unknown_present,
            pulse_count=deltas["pulse_count"],
            state_transition_count=deltas["state_transition_count"],
            graph_change=deltas["graph_change"],
            hypothesis_count=deltas["hypothesis_count"],
            memory_update=deltas["memory_update"],
            reentry_count=deltas["reentry_count"],
            model_call_count=deltas["model_call_count"],
            tool_call_count=deltas["tool_call_count"],
            effect_count=deltas["effect_count"],
            schema_fingerprint=self.schema_fingerprint,
            receipt_hash=body["receipt_hash"],
        )
