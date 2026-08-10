from __future__ import annotations

"""Guarded V3 Database Pulse candidate.

This module closes a coherence hole found during review of database_pulse_runtime_v3:
ActiveField observes current authoritative StateLedger state, while U12 deliberately consumes a
bounded delta batch.  If the U12 queue is larger than the requested batch, publishing a cognitive
focus from the newest StateLedger state would let cognition run ahead of the Pulse source epoch.

Guarded V3 therefore enforces:

  all authoritative StateLedger domains -> idempotent U12 delta bridge
  backlog <= cognitive Pulse delta budget -> cognition allowed
  backlog > budget -> fail closed; caller may run bounded zero-cognition catch-up Pulses

The bridge cursor is global across semantic domains.  A Pulse selecting only one source domain
must not make older events from another domain permanently invisible to the entity-level delta
plane.  Catch-up advances only the dedicated U12 Pulse/entity state, never StateLedger semantic
truth or external effect authority.
"""

from typing import Any

from research_entity.harness.reference.state_ledger import StaleEpoch
from research_entity.runtime.database_pulse_runtime_v3 import (
    DatabasePulseRuntimeV3,
    PulseReceiptV3,
)
from research_entity.runtime.database_pulse_v0 import DatabasePulseV0, PulseStateError


IMPLEMENTATION_ID_GUARDED = "database_pulse_runtime_v3_guarded"


class DatabasePulseRuntimeV3Guarded(DatabasePulseRuntimeV3):
    """Coherence-gated V3; current preferred V3 research candidate."""

    def __init__(self, *args, **kwargs):
        self._integrity_cache: dict[str, str] | None = None
        super().__init__(*args, **kwargs)

    def _full_ledger_integrity(self) -> dict[str, str]:
        # Cache only inside one guarded operation. run_pulse/drain_backlog always reset it,
        # so direct SQL corruption between Pulses is still detected on the next operation.
        if self._integrity_cache is None:
            self._integrity_cache = super()._full_ledger_integrity()
        return dict(self._integrity_cache)

    def _all_semantic_domains(self) -> tuple[str, ...]:
        return tuple(
            str(r[0])
            for r in self.con.execute(
                "SELECT DISTINCT domain FROM state "
                "WHERE domain NOT IN ('pulse','pulse_control') ORDER BY domain"
            )
        )

    def bridge_stateledger_events(
        self,
        *,
        source_domains: tuple[str, ...],
        now: str,
    ) -> dict[str, Any]:
        # Deliberately ignore the cognitive selection subset here.  U12 is an entity-level
        # change plane, not a per-query projection, so its source cursor must cover all
        # authoritative semantic domains or future source-domain changes could be skipped.
        domains = self._all_semantic_domains()
        if not domains:
            # Parent requires at least one source domain; an empty authoritative state has no
            # semantic delta to bridge and is represented explicitly.
            current_seq = int(
                self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
            )
            return {
                "mode": "EMPTY_STATE",
                "events_consumed": 0,
                "admitted_deltas": 0,
                "changed_refs": [],
                "last_event_seq": current_seq,
            }
        return super().bridge_stateledger_events(source_domains=domains, now=now)

    def backlog_count(self) -> int:
        return int(
            self.con.execute(
                "SELECT COUNT(*) FROM frank_database_pulse_delta_queue "
                "WHERE applied_pulse_id IS NULL"
            ).fetchone()[0]
        )

    def drain_backlog(
        self,
        *,
        basis_epoch: int,
        max_deltas: int = 32,
        now: str,
    ):
        """Run one bounded zero-cognition U12 catch-up Pulse.

        This is intentionally not a cognitive assembly.  It exists so large semantic bursts can
        be acknowledged over several bounded entity Pulses without letting ActiveField cognition
        consume a future semantic state relative to the U12 source epoch.
        """
        if int(basis_epoch) != self.ledger.epoch:
            raise StaleEpoch(f"Pulse V3 catch-up basis {basis_epoch}!={self.ledger.epoch}")
        if not (1 <= max_deltas <= self.MAX_DELTAS_HARD):
            raise ValueError("max_deltas out of bounds")
        self._integrity_cache = None
        try:
            self._full_ledger_integrity()
            self.bridge_stateledger_events(source_domains=(), now=now)
            before_epoch = self.ledger.epoch
            before_hash = self.ledger.semantic_state_hash
            before_trace = self.ledger.trace_root_hash
            receipt = DatabasePulseV0.pulse(
                self,
                max_deltas=max_deltas,
                now=now,
                model_call_count=0,
                tool_call_count=0,
                effect_count=0,
            )
            if self.ledger.epoch != before_epoch:
                raise PulseStateError("catch-up Pulse changed authoritative semantic epoch")
            if self.ledger.semantic_state_hash != before_hash:
                raise PulseStateError("catch-up Pulse changed authoritative semantic root")
            if self.ledger.trace_root_hash != before_trace:
                raise PulseStateError("catch-up Pulse changed authoritative trace root")
            return receipt
        finally:
            self._integrity_cache = None

    def run_pulse(self, *args, **kwargs) -> PulseReceiptV3:
        basis_epoch = int(kwargs.get("basis_epoch"))
        max_deltas = int(kwargs.get("max_deltas", 32))
        now = str(kwargs.get("now"))
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"Pulse V3 guarded basis {basis_epoch}!={self.ledger.epoch}")
        if not (0 <= max_deltas <= self.MAX_DELTAS_HARD):
            raise ValueError("max_deltas out of bounds")

        self._integrity_cache = None
        try:
            self._full_ledger_integrity()
            # Global entity bridge first; parent run_pulse will call the same bridge again but
            # the second call is a constant NO_CHANGE check and does not duplicate deltas.
            self.bridge_stateledger_events(source_domains=(), now=now)
            backlog = self.backlog_count()
            if backlog > max_deltas:
                raise PulseStateError(
                    f"V3 cognitive Pulse blocked: U12 backlog {backlog} exceeds max_deltas "
                    f"{max_deltas}; run bounded drain_backlog() until backlog is within budget"
                )
            receipt = super().run_pulse(*args, **kwargs)
            # With one SQLite writer and an admitted backlog <= max_deltas, cognitive commit
            # should close the queue.  Anything left means an invariant changed unexpectedly.
            if self.backlog_count() != 0:
                raise PulseStateError("V3 cognitive Pulse committed with residual U12 backlog")
            return receipt
        finally:
            self._integrity_cache = None
