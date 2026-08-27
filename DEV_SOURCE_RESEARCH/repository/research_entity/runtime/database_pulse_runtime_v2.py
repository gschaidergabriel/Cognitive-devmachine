from __future__ import annotations

"""FRANK Database Pulse Runtime V2 research candidate.

Fuses the evidence-gated StateLedger Pulse candidate v1 with PulseActiveFieldV2. The owner-
fixed semantics, scheduler, provenance, optional-model UNKNOWN boundary, re-entry controls and
no-effect-authority contract remain intact. The change is candidate generation: salience is
materialized in a rebuildable incremental projection BEFORE max_candidates is applied.

This is a research candidate, not a promoted FRANK Harness component.
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
from research_entity.runtime.database_pulse_active_field_v2 import (
    PROJECTION_VERSION,
    REENTRY_BOOST,
    PulseActiveFieldV2,
)


IMPLEMENTATION_ID_V2 = "database_pulse_runtime_v2_active_field"


class DatabasePulseRuntimeV2(DatabasePulseRuntime):
    """StateLedger Pulse with incremental salience-aware candidate generation."""

    def __init__(self, ledger):
        super().__init__(ledger)
        self.active_field = PulseActiveFieldV2(ledger)

    def _projection_row(self, ref: str):
        if ":" not in ref:
            raise PulseIntegrityError(f"invalid active-field ref: {ref}")
        domain, key = ref.split(":", 1)
        row = self.ledger.conn.execute(
            """SELECT * FROM pulse_active_field
               WHERE domain=? AND k=? AND status='CURRENT' AND epistemic='KNOWN'""",
            (domain, key),
        ).fetchone()
        if row is None:
            raise PulseIntegrityError(f"active-field selected missing/non-admissible ref: {ref}")
        return row

    def _reentry_targets_v2(
        self,
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
        writer: str = "database-pulse-runtime-v2",
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
            # Parent implementation performs no candidate query in PAUSED state and preserves
            # the exact owner-fixed pause semantics/receipt shape.
            return super().run_pulse(
                spec, writer=writer, model_assistant=model_assistant, committed_at=committed_at
            )
        if int(spec.basis_epoch) != self.ledger.epoch:
            raise StaleEpoch(f"pulse basis {spec.basis_epoch}!={self.ledger.epoch}")

        source_domains = tuple(dict.fromkeys(spec.source_domains))
        previous = self._previous_pulse()
        previous_focus = tuple(str(x) for x in (previous or {}).get("focus_refs", []))
        shuffle_salt = None
        if mode == "SHUFFLED_CONTROL" and previous is not None:
            shuffle_salt = h(
                {"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"}
            )
        selection = self.active_field.select(
            source_domains=source_domains,
            basis_epoch=spec.basis_epoch,
            max_candidates=spec.max_candidates,
            max_focus=spec.max_focus,
            reentry_mode=mode,
            previous_focus_refs=previous_focus,
            shuffle_salt=shuffle_salt,
            now=committed_at or f"pulse:{spec.pulse_id}",
        )
        if selection.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch("active-field semantic root changed before pulse commit")
        known_candidate_universe_count = self.active_field._count_epi(source_domains, "KNOWN")
        candidate_budget_truncated = known_candidate_universe_count > len(selection.candidate_refs)

        reentry_targets = self._reentry_targets_v2(
            mode=mode, previous=previous, candidate_refs=selection.candidate_refs
        )
        focus: list[dict[str, Any]] = []
        for ref in selection.focus_refs:
            row = self._projection_row(ref)
            value = json.loads(row["value_json"]) if row["value_json"] is not None else None
            base_score = float(row["base_score"])
            boost = REENTRY_BOOST if ref in reentry_targets else 0.0
            focus.append(
                {
                    "ref": ref,
                    "score": round(base_score + boost, 8),
                    "base_score": round(base_score, 8),
                    "reentry_boost": boost,
                    "signals": json.loads(row["score_components_clay"]),
                    "source_semantic_hash": row["semantic_hash"],
                    "domain_epoch": int(row["domain_epoch"]),
                    "value": value,
                }
            )
        focus_refs = [x["ref"] for x in focus]
        assembly_hash = h(
            {
                "basis_epoch": spec.basis_epoch,
                "input_semantic_state_hash": selection.semantic_state_hash,
                "reentry_mode": mode,
                "candidate_generation": PROJECTION_VERSION,
                "active_field_selection_hash": selection.selection_hash,
                "candidate_universe_count": known_candidate_universe_count,
                "candidate_budget_truncated": candidate_budget_truncated,
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
                "candidate_generation": PROJECTION_VERSION,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            }
            model_output = model_assistant(model_context)
            cjson(model_output)
            model_candidate_hash = h(model_output)
            model_call_delta = 1

        truthful_reentry = int(mode == "TRUTHFUL" and bool(reentry_targets))
        model_hypothesis_delta = int(model_output is not None)
        state_transition_delta = 2 + model_hypothesis_delta
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
            "implementation": IMPLEMENTATION_ID_V2,
            "pulse_contract": PULSE_CONTRACT,
            "pulse_id": spec.pulse_id,
            "basis_epoch": spec.basis_epoch,
            "committed_epoch": spec.basis_epoch + 1,
            "input_semantic_state_hash": selection.semantic_state_hash,
            "query_hash": selection.selection_hash,
            "query_truncated": candidate_budget_truncated,
            "candidate_generation": PROJECTION_VERSION,
            "candidate_count": len(selection.candidate_refs),
            "candidate_universe_count": known_candidate_universe_count,
            "candidate_budget": spec.max_candidates,
            "projection_last_event_seq": selection.projection_last_event_seq,
            "projection_refresh_mode": selection.refresh_mode,
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
                "implementation": IMPLEMENTATION_ID_V2,
                "candidate_generation": PROJECTION_VERSION,
                "active_field_selection_hash": selection.selection_hash,
                "candidate_universe_count": known_candidate_universe_count,
                "candidate_budget_truncated": candidate_budget_truncated,
                "receipt_hash": body["receipt_hash"],
                "reentry_mode": mode,
            },
            source={
                "basis_semantic_state_hash": selection.semantic_state_hash,
                "query_hash": selection.selection_hash,
                "focus_source_hashes": body["focus_source_hashes"],
                "projection_last_event_seq": selection.projection_last_event_seq,
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
