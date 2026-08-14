from __future__ import annotations

"""Evidence-gated Database Pulse reference candidate for FRANK research.

This is a research/runtime candidate, not a promoted FRANK Harness component.
It realizes the owner-fixed Database Pulse boundary over the existing authoritative
StateLedger/UnifiedDB surfaces without making an LLM loop the entity loop.

Design constraints:
- UnifiedDB/StateLedger remains semantic authority.
- Pulse activation/focus is context-only and never effect authority.
- model assistance is optional; model output is persisted UNKNOWN and cannot directly
  alter authoritative source state or execute effects.
- Pulse scheduler state is persistent and explicit (no implicit "alive" claim).
- every Pulse is epoch-bound, provenance-bound and replayable through StateLedger events.
- re-entry is bounded and lesionable; it only biases selection among already-admitted
  KNOWN/CURRENT source rows.
"""

from dataclasses import asdict, dataclass
import json
from typing import Any, Callable

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, cjson, h
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane


IMPLEMENTATION_ID = "database_pulse_candidate_v1"
PULSE_CONTRACT = "research_entity/global/FRANK_DATABASE_PULSE_CONTRACT.md"
REENTRY_MODES = {
    "TRUTHFUL",
    "NO_REENTRY",
    "SHUFFLED_CONTROL",
    "PROVENANCE_BROKEN_CONTROL",
}

REQUIRED_SCHEMA: dict[str, set[str]] = {
    "meta": {"k", "v"},
    "domain_epochs": {"domain", "epoch"},
    "state": {
        "domain", "k", "value_json", "epistemic", "status",
        "domain_epoch", "semantic_hash",
    },
    "events": {
        "seq", "event_id", "idem", "base_epoch", "epoch", "event_type",
        "writer", "ops_json", "provenance_json", "source_json", "execution_json",
        "semantic_event_hash", "semantic_chain_hash", "execution_chain_hash",
        "semantic_state_hash", "trace_root_hash", "committed_at",
    },
    "snapshots": {
        "id", "epoch", "semantic_state_hash", "trace_root_hash", "state_json",
        "domain_epochs_json", "semantic_chain_hash", "execution_chain_hash", "created_at",
    },
}


class PulseError(RuntimeError):
    pass


class PulseIntegrityError(PulseError):
    pass


class PulseControlError(PulseError):
    pass


@dataclass(frozen=True)
class PulseSpec:
    pulse_id: str
    basis_epoch: int
    source_domains: tuple[str, ...] = (
        "self", "world", "memory", "goal", "task", "semantic", "capability", "percept"
    )
    max_candidates: int = 128
    max_focus: int = 12
    reentry_mode: str = "TRUTHFUL"
    purpose: str = "ENDOGENOUS_DATABASE_PULSE"


@dataclass(frozen=True)
class PulseReceipt:
    status: str
    pulse_id: str
    basis_epoch: int
    committed_epoch: int | None
    input_semantic_state_hash: str
    output_semantic_state_hash: str | None
    trace_root_hash: str | None
    focus_refs: tuple[str, ...]
    assembly_hash: str
    conflicts_present: int
    unknown_present: int
    pulse_count: int
    state_transition_count: int
    graph_change: int
    hypothesis_count: int
    memory_update: int
    reentry_count: int
    model_call_count: int
    tool_call_count: int
    effect_count: int
    schema_fingerprint: str
    receipt_hash: str
    authority: str = "ASSEMBLY_CONTEXT_ONLY"


class DatabasePulseRuntime:
    """Bounded endogenous Pulse over one authoritative StateLedger.

    The runtime deliberately has no tool/effect API. A future effect proposal must cross
    the external authority gateway after the Pulse. Optional model assistance can only emit
    an UNKNOWN candidate row in the pulse domain.
    """

    REENTRY_BOOST = 0.30
    MAX_CANDIDATES_HARD = 512
    MAX_FOCUS_HARD = 64

    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self.query_plane = UnifiedDBQueryPlane(ledger)
        self.schema_fingerprint = self.validate_integrity(full=True)

    def _schema(self) -> tuple[str, dict[str, list[tuple[str, str, int, int]]]]:
        schema: dict[str, list[tuple[str, str, int, int]]] = {}
        for table, required in sorted(REQUIRED_SCHEMA.items()):
            rows = list(self.ledger.conn.execute(f"PRAGMA table_info({table})"))
            if not rows:
                raise PulseIntegrityError(f"required table missing: {table}")
            names = {str(r[1]) for r in rows}
            missing = sorted(required - names)
            if missing:
                raise PulseIntegrityError(f"schema incompatible: {table} missing {missing}")
            schema[table] = [
                (str(r[1]), str(r[2]), int(r[3]), int(r[5]))
                for r in rows
            ]
        return h(schema), schema

    def validate_integrity(self, *, full: bool = False) -> str:
        """Fail closed on schema/state-root corruption; full mode adds SQLite quick_check."""
        fingerprint, _ = self._schema()
        if full:
            try:
                checks = [str(r[0]) for r in self.ledger.conn.execute("PRAGMA quick_check")]
            except Exception as exc:  # sqlite corruption may itself raise
                raise PulseIntegrityError(f"sqlite quick_check failed: {exc}") from exc
            if checks != ["ok"]:
                raise PulseIntegrityError(f"sqlite quick_check: {checks[:4]}")
        try:
            state_root, trace_root = self.ledger._roots()  # same authoritative hash law
        except Exception as exc:
            raise PulseIntegrityError(f"cannot recompute ledger roots: {exc}") from exc
        if state_root != self.ledger.semantic_state_hash:
            raise PulseIntegrityError("semantic state root mismatch")
        if trace_root != self.ledger.trace_root_hash:
            raise PulseIntegrityError("trace root mismatch")
        return fingerprint

    def _scheduler(self) -> tuple[bool, str]:
        row = self.ledger.get("pulse_control", "scheduler")
        if row is None:
            raise PulseControlError("pulse scheduler has no explicit persisted state")
        if row["status"] != "CURRENT" or row["epistemic"] != "KNOWN":
            raise PulseControlError("pulse scheduler state is not KNOWN/CURRENT")
        value = row.get("value")
        if not isinstance(value, dict) or not isinstance(value.get("enabled"), bool):
            raise PulseControlError("pulse scheduler state is malformed")
        return bool(value["enabled"]), row["semantic_hash"]

    def set_scheduler(
        self,
        *,
        enabled: bool,
        event_id: str,
        base_epoch: int,
        actor: str,
        reason: str,
        committed_at: str | None = None,
    ) -> dict[str, Any]:
        if not event_id.strip() or not actor.strip() or not reason.strip():
            raise ValueError("event_id, actor and reason required")
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be bool")
        return self.query_plane.transact(
            event_id=event_id,
            idem=event_id,
            base_epoch=base_epoch,
            event_type="DATABASE_PULSE_SCHEDULER_SET",
            writer=actor,
            ops=[{
                "op": "SET",
                "domain": "pulse_control",
                "key": "scheduler",
                "value": {
                    "enabled": enabled,
                    "reason": reason,
                    "authority": "PERSISTED_RUNTIME_CONTROL",
                },
                "epistemic": "KNOWN",
                "status": "CURRENT",
            }],
            provenance={"pulse_contract": PULSE_CONTRACT, "implementation": IMPLEMENTATION_ID},
            source={"control_actor": actor},
            execution={"effect": "PULSE_SCHEDULER_STATE_ONLY"},
        ) if committed_at is None else self.ledger.append_event(
            event_id=event_id,
            idem=event_id,
            base_epoch=base_epoch,
            event_type="DATABASE_PULSE_SCHEDULER_SET",
            writer=actor,
            ops=[{
                "op": "SET",
                "domain": "pulse_control",
                "key": "scheduler",
                "value": {
                    "enabled": enabled,
                    "reason": reason,
                    "authority": "PERSISTED_RUNTIME_CONTROL",
                },
                "epistemic": "KNOWN",
                "status": "CURRENT",
            }],
            provenance={"pulse_contract": PULSE_CONTRACT, "implementation": IMPLEMENTATION_ID},
            source={"control_actor": actor},
            execution={"effect": "PULSE_SCHEDULER_STATE_ONLY"},
            committed_at=committed_at,
        )

    def _metrics(self) -> dict[str, int]:
        base = {
            "pulse_count": 0,
            "state_transition_count": 0,
            "graph_change": 0,
            "hypothesis_count": 0,
            "memory_update": 0,
            "reentry_count": 0,
            "model_call_count": 0,
            "tool_call_count": 0,
            "effect_count": 0,
        }
        row = self.ledger.get("pulse", "metrics")
        if row is None:
            return base
        if row["status"] != "CURRENT" or row["epistemic"] != "KNOWN":
            raise PulseIntegrityError("pulse metrics are not KNOWN/CURRENT")
        value = row.get("value")
        if not isinstance(value, dict):
            raise PulseIntegrityError("pulse metrics malformed")
        for key in base:
            raw = value.get(key, 0)
            if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
                raise PulseIntegrityError(f"invalid pulse metric: {key}")
            base[key] = raw
        return base

    @staticmethod
    def _signal_score(value: Any) -> tuple[float, dict[str, float]]:
        if not isinstance(value, dict):
            return 1.0, {}
        weights = {"priority": 0.40, "urgency": 0.25, "salience": 0.20, "novelty": 0.15}
        used: dict[str, float] = {}
        score = 1.0
        for key, weight in weights.items():
            raw = value.get(key)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                continue
            bounded = max(0.0, min(1.0, float(raw)))
            used[key] = bounded
            score += weight * bounded
        return score, used

    def _event_pulse_body(self, pulse_id: str) -> tuple[Any, dict[str, Any]] | None:
        row = self.ledger.conn.execute(
            "SELECT * FROM events WHERE idem=? AND event_type='DATABASE_PULSE'",
            (f"database-pulse:{pulse_id}",),
        ).fetchone()
        if row is None:
            return None
        try:
            ops = json.loads(row["ops_json"])
        except Exception as exc:
            raise PulseIntegrityError(f"pulse event ops unreadable: {exc}") from exc
        for op in ops:
            if op.get("domain") == "pulse" and op.get("key") == "latest":
                value = op.get("value")
                if not isinstance(value, dict):
                    raise PulseIntegrityError("stored pulse body malformed")
                return row, value
        raise PulseIntegrityError("pulse event missing latest receipt body")

    @staticmethod
    def _verify_body_hash(body: dict[str, Any]) -> None:
        supplied = body.get("receipt_hash")
        if not isinstance(supplied, str):
            raise PulseIntegrityError("pulse receipt hash missing")
        plain = dict(body)
        plain.pop("receipt_hash", None)
        if h(plain) != supplied:
            raise PulseIntegrityError("pulse receipt hash mismatch")

    def _previous_pulse(self) -> dict[str, Any] | None:
        row = self.ledger.get("pulse", "latest")
        if row is None:
            return None
        if row["status"] != "CURRENT" or row["epistemic"] != "KNOWN":
            raise PulseIntegrityError("latest pulse state is not KNOWN/CURRENT")
        body = row.get("value")
        if not isinstance(body, dict):
            raise PulseIntegrityError("latest pulse state malformed")
        self._verify_body_hash(body)
        pulse_id = str(body.get("pulse_id") or "")
        stored = self._event_pulse_body(pulse_id)
        if stored is None:
            raise PulseIntegrityError("latest pulse has no provenance event")
        _, event_body = stored
        self._verify_body_hash(event_body)
        if event_body.get("receipt_hash") != body.get("receipt_hash"):
            raise PulseIntegrityError("latest pulse/event provenance mismatch")
        return body

    def _reentry_targets(
        self,
        *,
        mode: str,
        previous: dict[str, Any] | None,
        candidate_refs: list[str],
    ) -> set[str]:
        if previous is None or mode in {"NO_REENTRY", "PROVENANCE_BROKEN_CONTROL"}:
            return set()
        previous_focus = [str(x) for x in previous.get("focus_refs", [])]
        if mode == "TRUTHFUL":
            return set(previous_focus) & set(candidate_refs)
        # Deterministic shuffled control: preserve exposure count, break identity relation.
        salt = h({"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"})
        shuffled = sorted(candidate_refs, key=lambda ref: h({"salt": salt, "ref": ref}))
        return set(shuffled[: min(len(previous_focus), len(shuffled))])

    def _existing_receipt(self, spec: PulseSpec) -> PulseReceipt | None:
        found = self._event_pulse_body(spec.pulse_id)
        if found is None:
            return None
        row, body = found
        self._verify_body_hash(body)
        obs = body["observables"]
        return PulseReceipt(
            status="ALREADY_COMMITTED",
            pulse_id=spec.pulse_id,
            basis_epoch=int(body["basis_epoch"]),
            committed_epoch=int(row["epoch"]),
            input_semantic_state_hash=str(body["input_semantic_state_hash"]),
            output_semantic_state_hash=str(row["semantic_state_hash"]),
            trace_root_hash=str(row["trace_root_hash"]),
            focus_refs=tuple(map(str, body.get("focus_refs", ()))),
            assembly_hash=str(body["assembly_hash"]),
            conflicts_present=int(body["conflicts_present"]),
            unknown_present=int(body["unknown_present"]),
            pulse_count=int(obs["pulse_count"]),
            state_transition_count=int(obs["state_transition_count"]),
            graph_change=int(obs["graph_change"]),
            hypothesis_count=int(obs["hypothesis_count"]),
            memory_update=int(obs["memory_update"]),
            reentry_count=int(obs["reentry_count"]),
            model_call_count=int(obs["model_call_count"]),
            tool_call_count=int(obs["tool_call_count"]),
            effect_count=int(obs["effect_count"]),
            schema_fingerprint=str(body["schema_fingerprint"]),
            receipt_hash=str(body["receipt_hash"]),
        )

    def run_pulse(
        self,
        spec: PulseSpec,
        *,
        writer: str = "database-pulse-runtime",
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        committed_at: str | None = None,
    ) -> PulseReceipt:
        if not spec.pulse_id.strip():
            raise ValueError("pulse_id required")
        mode = spec.reentry_mode.upper()
        if mode not in REENTRY_MODES:
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
            return PulseReceipt(
                status="PAUSED",
                pulse_id=spec.pulse_id,
                basis_epoch=self.ledger.epoch,
                committed_epoch=None,
                input_semantic_state_hash=self.ledger.semantic_state_hash,
                output_semantic_state_hash=None,
                trace_root_hash=self.ledger.trace_root_hash,
                focus_refs=(),
                assembly_hash=h({"status": "PAUSED", "scheduler_hash": scheduler_hash}),
                conflicts_present=0,
                unknown_present=0,
                pulse_count=0,
                state_transition_count=0,
                graph_change=0,
                hypothesis_count=0,
                memory_update=0,
                reentry_count=0,
                model_call_count=0,
                tool_call_count=0,
                effect_count=0,
                schema_fingerprint=self.schema_fingerprint,
                receipt_hash=h({"pulse_id": spec.pulse_id, "status": "PAUSED", "scheduler_hash": scheduler_hash}),
            )

        if int(spec.basis_epoch) != self.ledger.epoch:
            raise StaleEpoch(f"pulse basis {spec.basis_epoch}!={self.ledger.epoch}")

        query = self.query_plane.query(QuerySpec(
            query_id=f"pulse-census:{spec.pulse_id}",
            domains=tuple(dict.fromkeys(spec.source_domains)),
            statuses=("CURRENT",),
            epistemic=("KNOWN", "UNKNOWN", "CONFLICT"),
            limit=spec.max_candidates,
            basis_epoch=spec.basis_epoch,
            purpose=spec.purpose,
        ))
        previous = self._previous_pulse()

        conflicts = [r for r in query.rows if r["epistemic"] == "CONFLICT"]
        unknown = [r for r in query.rows if r["epistemic"] == "UNKNOWN"]
        admissible = [r for r in query.rows if r["epistemic"] == "KNOWN" and r["status"] == "CURRENT"]
        refs = [f"{r['domain']}:{r['key']}" for r in admissible]
        reentry_targets = self._reentry_targets(mode=mode, previous=previous, candidate_refs=refs)

        ranked: list[dict[str, Any]] = []
        for row in admissible:
            ref = f"{row['domain']}:{row['key']}"
            base_score, signals = self._signal_score(row.get("value"))
            reentry_boost = self.REENTRY_BOOST if ref in reentry_targets else 0.0
            ranked.append({
                "ref": ref,
                "score": round(base_score + reentry_boost, 8),
                "base_score": round(base_score, 8),
                "reentry_boost": reentry_boost,
                "signals": signals,
                "source_semantic_hash": row["semantic_hash"],
                "domain_epoch": row["domain_epoch"],
                "value": row.get("value"),
            })
        ranked.sort(key=lambda x: (-x["score"], x["ref"], x["source_semantic_hash"]))
        focus = ranked[: spec.max_focus]
        focus_refs = [x["ref"] for x in focus]
        assembly_hash = h({
            "basis_epoch": spec.basis_epoch,
            "input_semantic_state_hash": query.semantic_state_hash,
            "reentry_mode": mode,
            "focus": [
                {k: x[k] for k in ("ref", "score", "source_semantic_hash", "domain_epoch")}
                for x in focus
            ],
        })

        model_output: Any = None
        model_call_delta = 0
        model_candidate_hash: str | None = None
        if model_assistant is not None:
            model_context = {
                "pulse_id": spec.pulse_id,
                "basis_epoch": spec.basis_epoch,
                "assembly_hash": assembly_hash,
                "focus": focus,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            }
            model_output = model_assistant(model_context)
            cjson(model_output)  # reject non-canonical/non-finite outputs before any write
            model_candidate_hash = h(model_output)
            model_call_delta = 1

        truthful_reentry = int(mode == "TRUTHFUL" and bool(reentry_targets))
        model_hypothesis_delta = int(model_output is not None)
        state_transition_delta = 2 + model_hypothesis_delta  # latest + metrics + optional model candidate
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
            "implementation": IMPLEMENTATION_ID,
            "pulse_contract": PULSE_CONTRACT,
            "pulse_id": spec.pulse_id,
            "basis_epoch": spec.basis_epoch,
            "committed_epoch": spec.basis_epoch + 1,
            "input_semantic_state_hash": query.semantic_state_hash,
            "query_hash": query.query_hash,
            "query_truncated": query.truncated,
            "scheduler_semantic_hash": scheduler_hash,
            "schema_fingerprint": self.schema_fingerprint,
            "source_domains": list(spec.source_domains),
            "focus_refs": focus_refs,
            "focus_source_hashes": [x["source_semantic_hash"] for x in focus],
            "assembly_hash": assembly_hash,
            "conflicts_present": len(conflicts),
            "unknown_present": len(unknown),
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
                "op": "SET", "domain": "pulse", "key": "latest", "value": body,
                "epistemic": "KNOWN", "status": "CURRENT",
            },
            {
                "op": "SET", "domain": "pulse", "key": "metrics", "value": cumulative,
                "epistemic": "KNOWN", "status": "CURRENT",
            },
        ]
        if model_output is not None:
            ops.append({
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
            })

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
                "implementation": IMPLEMENTATION_ID,
                "receipt_hash": body["receipt_hash"],
                "reentry_mode": mode,
            },
            source={
                "basis_semantic_state_hash": query.semantic_state_hash,
                "query_hash": query.query_hash,
                "focus_source_hashes": body["focus_source_hashes"],
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
            input_semantic_state_hash=query.semantic_state_hash,
            output_semantic_state_hash=str(result["semantic_state_hash"]),
            trace_root_hash=str(result["trace_root_hash"]),
            focus_refs=tuple(focus_refs),
            assembly_hash=assembly_hash,
            conflicts_present=len(conflicts),
            unknown_present=len(unknown),
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

    def status(self) -> dict[str, Any]:
        """Runtime/state-backed operational status; never infers phenomenal properties."""
        fingerprint = self.validate_integrity(full=False)
        enabled, scheduler_hash = self._scheduler()
        latest = self._previous_pulse()
        return {
            "state": "PULSING_READY" if enabled else "PAUSED",
            "scheduler_enabled": enabled,
            "scheduler_semantic_hash": scheduler_hash,
            "ledger_epoch": self.ledger.epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "trace_root_hash": self.ledger.trace_root_hash,
            "schema_fingerprint": fingerprint,
            "latest_pulse_id": latest.get("pulse_id") if latest else None,
            "latest_receipt_hash": latest.get("receipt_hash") if latest else None,
            "identity_claim": "FRANK_RUNTIME_STATE_CONTINUITY_ONLY",
            "phenomenal_claim": "NONE",
        }


def receipt_dict(receipt: PulseReceipt) -> dict[str, Any]:
    return asdict(receipt)
