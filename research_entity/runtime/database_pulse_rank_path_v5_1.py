from __future__ import annotations

"""V5.1 concurrency guard for two-phase Pulse rank-index maintenance.

V5 correctly removes schema mutation from cognition/read selection. V5.1 narrows one remaining
TOCTOU window in the separate maintenance phase: a lifecycle plan must still match the
StateLedger *after* this connection acquires SQLite's writer lock. CREATE/DROP then executes in
the same transaction and is committed only after semantic/trace roots are verified unchanged.

This is performance-maintenance authority only. StateLedger remains semantic authority; rank
index presence never becomes truth or effect authority.
"""

from research_entity.harness.reference.state_ledger import StaleEpoch
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME, SCORE_EXPR
from research_entity.runtime.database_pulse_rank_path_v5 import (
    AdaptiveAuthoritativeRankPathV5,
    RankLifecyclePlan,
    RankMaintenanceReceipt,
)

IMPLEMENTATION_ID = "PULSE_TWO_PHASE_AUTHORITATIVE_RANK_PATH_V5_1_LOCKED_MAINTENANCE"


class AdaptiveAuthoritativeRankPathV51(AdaptiveAuthoritativeRankPathV5):
    def _begin_maintenance(self) -> None:
        """Fault-injection seam: production behavior is one BEGIN IMMEDIATE."""
        self.con.execute("BEGIN IMMEDIATE")

    def _roots(self) -> tuple[int, str, str]:
        return (
            self.ledger.epoch,
            self.ledger.semantic_state_hash,
            self.ledger.trace_root_hash,
        )

    def _validate_plan_locked(self, plan: RankLifecyclePlan) -> None:
        if (
            plan.basis_epoch != self.ledger.epoch
            or plan.semantic_state_hash != self.ledger.semantic_state_hash
        ):
            raise StaleEpoch(
                "rank maintenance plan no longer matches authoritative ledger after writer lock"
            )

    def apply_maintenance(self, plan: RankLifecyclePlan) -> RankMaintenanceReceipt:
        action = plan.maintenance_action
        if action not in {"BUILD_INDEX", "DROP_INDEX", "NONE"}:
            raise ValueError(f"unsupported maintenance action: {action}")

        # NONE has no physical effect. Preserve V5's stale-plan rejection without acquiring a
        # writer lock unnecessarily.
        if action == "NONE":
            if (
                plan.basis_epoch != self.ledger.epoch
                or plan.semantic_state_hash != self.ledger.semantic_state_hash
            ):
                raise StaleEpoch("rank maintenance plan no longer matches authoritative ledger")
            before = self.index_exists()
            state_before = self.ledger.semantic_state_hash
            trace_before = self.ledger.trace_root_hash
            return RankMaintenanceReceipt(
                basis_epoch=plan.basis_epoch,
                action=action,
                status="NO_CHANGE",
                index_present_before=before,
                index_present_after=before,
                semantic_state_hash_before=state_before,
                semantic_state_hash_after=state_before,
                trace_root_hash_before=trace_before,
                trace_root_hash_after=trace_before,
                plan_hash=plan.plan_hash,
            )

        # BUILD/DROP is a physical write. Acquire the SQLite writer lock first, then revalidate
        # the plan basis while competing StateLedger writers are excluded.
        try:
            self._begin_maintenance()
            self._validate_plan_locked(plan)
            before = self.index_exists()
            epoch_before, state_before, trace_before = self._roots()

            if action == "BUILD_INDEX":
                self.con.execute(
                    f"""CREATE INDEX IF NOT EXISTS {INDEX_NAME}
                        ON state(
                          {SCORE_EXPR} DESC,
                          domain COLLATE BINARY,
                          k COLLATE BINARY,
                          semantic_hash COLLATE BINARY
                        )
                        WHERE status='CURRENT' AND epistemic='KNOWN'"""
                )
                status = "BUILT"
            else:
                self.con.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
                status = "DROPPED"

            after = self.index_exists()
            epoch_after, state_after, trace_after = self._roots()
            if (epoch_before, state_before, trace_before) != (
                epoch_after,
                state_after,
                trace_after,
            ):
                raise AssertionError(
                    "physical rank-index maintenance changed or crossed authoritative roots"
                )
            self.con.commit()
            return RankMaintenanceReceipt(
                basis_epoch=plan.basis_epoch,
                action=action,
                status=status,
                index_present_before=before,
                index_present_after=after,
                semantic_state_hash_before=state_before,
                semantic_state_hash_after=state_after,
                trace_root_hash_before=trace_before,
                trace_root_hash_after=trace_after,
                plan_hash=plan.plan_hash,
            )
        except StaleEpoch:
            self.con.rollback()
            raise
        except Exception:
            # DDL is transactional here, so rollback prevents a failed/stale partial lifecycle
            # mutation from escaping. Semantic correctness is still provided by the online path.
            self.con.rollback()
            after = self.index_exists()
            state = self.ledger.semantic_state_hash
            trace = self.ledger.trace_root_hash
            return RankMaintenanceReceipt(
                basis_epoch=plan.basis_epoch,
                action=action,
                status="FAILED_RETRYABLE_PHYSICAL_MAINTENANCE",
                index_present_before=after,
                index_present_after=after,
                semantic_state_hash_before=state,
                semantic_state_hash_after=state,
                trace_root_hash_before=trace,
                trace_root_hash_after=trace,
                plan_hash=plan.plan_hash,
            )


__all__ = ["AdaptiveAuthoritativeRankPathV51", "IMPLEMENTATION_ID"]
