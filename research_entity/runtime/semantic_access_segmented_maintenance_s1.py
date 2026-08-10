from __future__ import annotations

"""Collision-free public research identity for segmented Pulse maintenance SPM-S1.

SPM-S1 keeps the V16 copy-on-write segmented projection and adds publication concurrency
invariants at the public maintenance boundary:

- at most one access generation may be CURRENT (database integrity backstop);
- after the writer has acquired the inherited U12/V16 ``BEGIN IMMEDIATE`` transaction, the
  publication path rechecks that ``access_head`` still equals the parent generation observed
  before the transaction;
- if another writer won in that TOCTOU window, the stale pulse aborts and rolls back.

UnifiedDB/StateLedger remains semantic truth authority. This projection remains disposable,
rebuildable context state and grants no effect authority.
"""

from semantic_access_pulse_v12 import PulseInvariantError, StalePulse
from semantic_access_pulse_v16 import SegmentedPulseProjectionV16

IMPLEMENTATION_ID = "UNIFIEDDB_SEGMENTED_PULSE_MAINTENANCE_S1"
UNIQUE_CURRENT_INDEX = "uq_spm_s1_access_generation_single_current"


class SegmentedPulseMaintenanceS1(SegmentedPulseProjectionV16):
    def __init__(self, path: str = ":memory:"):
        super().__init__(path)
        current_count = int(
            self.con.execute(
                "SELECT count(*) FROM access_generation WHERE status='CURRENT'"
            ).fetchone()[0]
        )
        if current_count > 1:
            raise PulseInvariantError(
                "SPM-S1 refuses a database with multiple CURRENT access generations"
            )
        self.con.execute(
            f"""CREATE UNIQUE INDEX IF NOT EXISTS {UNIQUE_CURRENT_INDEX}
                ON access_generation(status) WHERE status='CURRENT'"""
        )
        self.con.commit()

    def _stage_publish_generation(
        self,
        *,
        event_id: str,
        source_epoch: int,
        graph_epoch: int,
        mapping,
        previous_generation_id: str | None,
        receipt_meta: dict,
    ):
        # Inherited apply_pulse() has already acquired BEGIN IMMEDIATE here. Re-reading the
        # head is therefore an in-lock compare-and-swap check against the stale pre-lock parent.
        if previous_generation_id is not None:
            row = self.con.execute(
                "SELECT generation_id FROM access_head WHERE head_key='CURRENT'"
            ).fetchone()
            actual = str(row[0]) if row is not None else None
            if actual != previous_generation_id:
                raise StalePulse(
                    "SPM-S1 parent generation moved before publication: "
                    f"expected {previous_generation_id}, got {actual}"
                )
        return super()._stage_publish_generation(
            event_id=event_id,
            source_epoch=source_epoch,
            graph_epoch=graph_epoch,
            mapping=mapping,
            previous_generation_id=previous_generation_id,
            receipt_meta=receipt_meta,
        )

    def audit_current_generation(self) -> dict:
        current_count = int(
            self.con.execute(
                "SELECT count(*) FROM access_generation WHERE status='CURRENT'"
            ).fetchone()[0]
        )
        if current_count != 1:
            raise PulseInvariantError(
                f"SPM-S1 deep audit requires exactly one CURRENT generation, got {current_count}"
            )
        receipt = dict(super().audit_current_generation())
        receipt["implementation"] = IMPLEMENTATION_ID
        receipt["single_current_generation"] = True
        receipt["stale_parent_cas"] = "IN_LOCK"
        return receipt
