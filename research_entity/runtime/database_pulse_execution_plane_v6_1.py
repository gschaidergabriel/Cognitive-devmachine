from __future__ import annotations

"""Database Pulse execution plane V6.1 hardening.

V6.1 does not change the V6 topology.  It closes two evidence/epistemic gaps:

1. every persisted receipt row is hash-verified even when discovered inside the concurrent
   same-invocation commit race path;
2. optional model output is wrapped explicitly as epistemic UNKNOWN/context-only before it is
   hashed and stored in the execution receipt.

No new truth/effect authority is created.
"""

from typing import Any, Callable

from research_entity.harness.reference.state_ledger import h
from research_entity.runtime.database_pulse_execution_plane_v6 import (
    DatabasePulseExecutionPlaneV6,
    PulseReceiptV6,
    PulseSpecV6,
    PulseV6IntegrityError,
)


IMPLEMENTATION_ID = "database_pulse_execution_plane_v6_1_receipt_epistemic_hardening"


class DatabasePulseExecutionPlaneV6_1(DatabasePulseExecutionPlaneV6):
    """Preferred hardening tip for V6 while preserving the exact execution topology."""

    def _receipt_row(self, invocation_id: str):
        row = super()._receipt_row(invocation_id)
        if row is None:
            return None
        body = {
            key: row[key]
            for key in row.keys()
            if key not in {"receipt_hash", "created_at"}
        }
        if h(body) != str(row["receipt_hash"]):
            raise PulseV6IntegrityError(
                f"persisted V6 receipt hash mismatch for invocation={invocation_id}"
            )
        return row

    def run_pulse(
        self,
        spec: PulseSpecV6,
        *,
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        now: str = "V6_1_PULSE",
    ) -> PulseReceiptV6:
        if model_assistant is None:
            return super().run_pulse(spec, model_assistant=None, now=now)

        def unknown_model_context(context: dict[str, Any]) -> dict[str, Any]:
            raw = model_assistant(context)
            return {
                "epistemic": "UNKNOWN",
                "candidate": raw,
                "authority": "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
                "implementation": IMPLEMENTATION_ID,
            }

        return super().run_pulse(spec, model_assistant=unknown_model_context, now=now)
