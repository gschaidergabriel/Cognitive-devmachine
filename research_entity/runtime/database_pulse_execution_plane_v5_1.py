from __future__ import annotations

"""Preferred V5.1 migration guard for the direct-event Database Pulse execution plane.

The base V5 research candidate proved the direct-event topology, but its automatic adoption of a
lagging pre-V5 U12 `source_epoch` assumed that the historical U12 epoch occupied the same semantic
epoch space as StateLedger. That is not generally provable from the integer alone.

V5.1 therefore applies a stricter migration law:

* fresh database -> snapshot current verified StateLedger, cursor=current event head;
* already-V5 database -> verify and continue;
* legacy U12 aligned to current StateLedger epoch -> begin a NEW direct-event cursor at the
  current StateLedger head, explicitly as an aligned snapshot adoption (historical equivalence is
  not claimed);
* legacy U12 lagging current StateLedger -> FAIL CLOSED by default;
* lagging legacy U12 may be adopted only when the migration caller explicitly asserts
  `legacy_source_epoch_is_stateledger_epoch=True`; V5.1 then maps that epoch to the authoritative
  StateLedger event/hash boundary and normal V5 tests must catch up from there.

The flag is migration authority/provenance, not evidence by itself. Release promotion still
requires replay/receipt evidence that the old epoch really represented StateLedger semantics.
"""

from research_entity.runtime.database_pulse_execution_plane_v5 import (
    DatabasePulseExecutionPlaneV5,
    IMPLEMENTATION_ID,
)
from research_entity.runtime.database_pulse_v0 import PulseIntegrityError, PulseStateError


IMPLEMENTATION_ID_V51 = "database_pulse_execution_plane_v5_1_strict_migration"


class DatabasePulseExecutionPlaneV51(DatabasePulseExecutionPlaneV5):
    """Direct-event V5 with fail-closed ambiguous legacy epoch migration."""

    def __init__(
        self,
        *args,
        legacy_source_epoch_is_stateledger_epoch: bool = False,
        **kwargs,
    ):
        self.legacy_source_epoch_is_stateledger_epoch = bool(
            legacy_source_epoch_is_stateledger_epoch
        )
        super().__init__(*args, **kwargs)

    def _bootstrap_or_adopt(self, *, entity_id: str, lineage_id: str, now: str) -> None:
        existed = self.con.execute(
            "SELECT 1 FROM frank_database_pulse_state WHERE singleton_id=1"
        ).fetchone() is not None
        if not existed:
            self.bootstrap(
                entity_id=entity_id,
                lineage_id=lineage_id,
                source_epoch=self.ledger.epoch,
                graph_epoch=0,
                now=now,
            )
            self._rewrite_state_clay_for_v5(
                cursor=self._max_event_seq(),
                source_semantic_hash=self.ledger.semantic_state_hash,
                mode="CURRENT_STATELEDGER_SNAPSHOT_BOOTSTRAP_V5_1",
                now=now,
            )
            return

        state = self._verify_state()
        body = self._decode_state_clay(state)
        if body.get("implementation") == IMPLEMENTATION_ID:
            cursor = body.get("last_source_event_seq")
            source_hash = body.get("source_semantic_state_hash")
            if not isinstance(cursor, int) or cursor < 0 or cursor > self._max_event_seq():
                raise PulseIntegrityError("V5.1 existing source event cursor is invalid")
            if not isinstance(source_hash, str) or not source_hash:
                raise PulseIntegrityError("V5.1 existing source semantic hash is invalid")
            if int(state["source_epoch"]) > self.ledger.epoch:
                raise PulseIntegrityError("V5.1 source_epoch is ahead of StateLedger")
            if (
                int(state["source_epoch"]) == self.ledger.epoch
                and source_hash != self.ledger.semantic_state_hash
            ):
                raise PulseIntegrityError(
                    "V5.1 aligned source hash disagrees with StateLedger"
                )
            return

        source_epoch = int(state["source_epoch"])
        if source_epoch > self.ledger.epoch:
            raise PulseIntegrityError("legacy U12 source_epoch is ahead of StateLedger")

        if source_epoch == self.ledger.epoch:
            # Start the new direct-event plane from current verified reality. This deliberately
            # makes no claim that older legacy U12 epochs meant StateLedger epochs.
            self._rewrite_state_clay_for_v5(
                cursor=self._max_event_seq(),
                source_semantic_hash=self.ledger.semantic_state_hash,
                mode="ALIGNED_LEGACY_CURRENT_SNAPSHOT_ADOPTION_V5_1",
                now=now,
            )
            return

        if not self.legacy_source_epoch_is_stateledger_epoch:
            raise PulseStateError(
                "ambiguous lagging legacy U12 source_epoch: V5.1 will not infer StateLedger "
                "epoch identity from an integer; supply explicit migration provenance or "
                "re-bootstrap from a verified current snapshot under a separate owner-reviewed "
                "migration procedure"
            )

        cursor, source_hash = self._event_anchor_for_epoch(source_epoch)
        if source_hash.startswith("UNKNOWN_"):
            raise PulseStateError(
                "explicit legacy StateLedger-epoch adoption lacks a verifiable event/hash boundary"
            )
        self._rewrite_state_clay_for_v5(
            cursor=cursor,
            source_semantic_hash=source_hash,
            mode="EXPLICIT_LEGACY_STATELEDGER_EPOCH_ADOPTION_V5_1",
            now=now,
        )
