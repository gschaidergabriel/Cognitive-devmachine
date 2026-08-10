from __future__ import annotations

"""Database Pulse physical rank maintenance V6: provenance-complete atomic audit.

V5 established the two-phase cognition/read vs inter-Pulse maintenance boundary and made
schema mutation atomic with a durable physical receipt. Its remaining audit gap is that the
physical receipt table does not carry the maintenance actor and policy provenance as first-class
columns. V6 closes that gap without changing StateLedger semantic authority or Pulse ranking
semantics.

Compatibility rule:
- V5 receipts remain untouched.
- On the first material V6 maintenance transaction, existing V5 receipts are copied into the V6
  audit plane with literal UNKNOWN provenance and an explicit LEGACY_V5_BACKFILL status.
- Native V6 BUILD/DROP refuses blank/UNKNOWN actor, policy provenance, or policy decision hash.
- Every persisted V6 audit row gets a transaction-local monotonic audit_sequence. This keeps
  repeated physical BUILD/DROP cycles auditable even when the semantic plan is identical.

The V6 audit table, legacy backfill, CREATE/DROP INDEX, root verification, and native receipt are
committed in one BEGIN IMMEDIATE transaction. Any failure rolls back the entire V6-side effect.
"""

from dataclasses import dataclass
from typing import Any

from research_entity.harness.reference.state_ledger import StaleEpoch, h
from research_entity.runtime.database_pulse_rank_path_v5 import (
    AdaptiveAuthoritativeRankPathV5,
    MAINTENANCE_LOG_TABLE as V5_MAINTENANCE_LOG_TABLE,
    RankLifecyclePlan,
    RankPhysicalStateStale,
)

IMPLEMENTATION_ID = "PULSE_TWO_PHASE_AUTHORITATIVE_RANK_PATH_V6_PROVENANCE_AUDIT"
MAINTENANCE_LOG_TABLE_V6 = "pulse_rank_maintenance_receipts_v6"
NATIVE_PROVENANCE_STATUS = "NATIVE_V6_PROVENANCE_BOUND"
LEGACY_PROVENANCE_STATUS = "LEGACY_V5_BACKFILL_UNKNOWN_PROVENANCE"
AUTHORITY = "PHYSICAL_INDEX_MAINTENANCE_ONLY_NO_SEMANTIC_AUTHORITY"


@dataclass(frozen=True)
class RankMaintenanceReceiptV6:
    basis_epoch: int
    action: str
    status: str
    index_present_before: bool
    index_present_after: bool
    semantic_state_hash_before: str
    semantic_state_hash_after: str
    trace_root_hash_before: str
    trace_root_hash_after: str
    plan_hash: str
    actor: str
    policy_provenance_ref: str
    policy_decision_hash: str
    provenance_status: str
    audit_sequence: int | None = None
    authority: str = AUTHORITY
    receipt_id: str | None = None
    legacy_source_receipt_id: str | None = None
    persisted: bool = False


class AdaptiveAuthoritativeRankPathV6(AdaptiveAuthoritativeRankPathV5):
    """V5 rank semantics plus provenance-complete physical maintenance receipts."""

    @staticmethod
    def _native_provenance(
        *, actor: str, policy_provenance_ref: str, policy_decision_hash: str
    ) -> tuple[str, str, str]:
        values = {
            "actor": str(actor).strip(),
            "policy_provenance_ref": str(policy_provenance_ref).strip(),
            "policy_decision_hash": str(policy_decision_hash).strip(),
        }
        for name, value in values.items():
            if not value or value.upper() == "UNKNOWN":
                raise ValueError(f"native V6 maintenance requires known {name}")
        return (
            values["actor"],
            values["policy_provenance_ref"],
            values["policy_decision_hash"],
        )

    def _v6_log_exists(self) -> bool:
        return self.con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (MAINTENANCE_LOG_TABLE_V6,),
        ).fetchone() is not None

    def _create_v6_log_no_commit(self) -> None:
        self.con.execute(
            f"""CREATE TABLE IF NOT EXISTS {MAINTENANCE_LOG_TABLE_V6}(
                receipt_id TEXT PRIMARY KEY,
                audit_sequence INTEGER NOT NULL UNIQUE,
                plan_hash TEXT NOT NULL,
                basis_epoch INTEGER NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                index_present_before INTEGER NOT NULL,
                index_present_after INTEGER NOT NULL,
                semantic_state_hash_before TEXT NOT NULL,
                semantic_state_hash_after TEXT NOT NULL,
                trace_root_hash_before TEXT NOT NULL,
                trace_root_hash_after TEXT NOT NULL,
                actor TEXT NOT NULL,
                policy_provenance_ref TEXT NOT NULL,
                policy_decision_hash TEXT NOT NULL,
                provenance_status TEXT NOT NULL,
                legacy_source_receipt_id TEXT,
                executed_at TEXT NOT NULL,
                authority TEXT NOT NULL
            )"""
        )
        self.con.execute(
            f"""CREATE INDEX IF NOT EXISTS idx_pulse_rank_maintenance_v6_plan
                ON {MAINTENANCE_LOG_TABLE_V6}(plan_hash, provenance_status)"""
        )
        self.con.execute(
            f"""CREATE UNIQUE INDEX IF NOT EXISTS idx_pulse_rank_maintenance_v6_legacy_source
                ON {MAINTENANCE_LOG_TABLE_V6}(legacy_source_receipt_id)
                WHERE legacy_source_receipt_id IS NOT NULL"""
        )

    def _next_audit_sequence_no_commit(self) -> int:
        row = self.con.execute(
            f"SELECT COALESCE(MAX(audit_sequence),0)+1 FROM {MAINTENANCE_LOG_TABLE_V6}"
        ).fetchone()
        if row is None:
            raise AssertionError("V6 audit sequence query returned no row")
        value = int(row[0])
        if value < 1:
            raise AssertionError("V6 audit sequence must be positive")
        return value

    def _migrate_v5_receipts_no_commit(self) -> int:
        """Backfill V5 audit rows honestly; absence of provenance remains literal UNKNOWN."""
        exists = self.con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (V5_MAINTENANCE_LOG_TABLE,),
        ).fetchone()
        if exists is None:
            return 0
        rows = self.con.execute(
            f"SELECT * FROM {V5_MAINTENANCE_LOG_TABLE} ORDER BY rowid"
        ).fetchall()
        inserted = 0
        for row in rows:
            source_receipt_id = str(row["receipt_id"])
            already = self.con.execute(
                f"SELECT 1 FROM {MAINTENANCE_LOG_TABLE_V6} WHERE legacy_source_receipt_id=?",
                (source_receipt_id,),
            ).fetchone()
            if already is not None:
                continue
            audit_sequence = self._next_audit_sequence_no_commit()
            body = {
                "migration": "V5_TO_V6_AUDIT_BACKFILL",
                "audit_sequence": audit_sequence,
                "legacy_source_receipt_id": source_receipt_id,
                "plan_hash": str(row["plan_hash"]),
                "basis_epoch": int(row["basis_epoch"]),
                "provenance_status": LEGACY_PROVENANCE_STATUS,
            }
            receipt_id = h(body)
            self.con.execute(
                f"""INSERT INTO {MAINTENANCE_LOG_TABLE_V6}(
                    receipt_id,audit_sequence,plan_hash,basis_epoch,action,status,
                    index_present_before,index_present_after,
                    semantic_state_hash_before,semantic_state_hash_after,
                    trace_root_hash_before,trace_root_hash_after,
                    actor,policy_provenance_ref,policy_decision_hash,provenance_status,
                    legacy_source_receipt_id,executed_at,authority
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    receipt_id,
                    audit_sequence,
                    str(row["plan_hash"]),
                    int(row["basis_epoch"]),
                    str(row["action"]),
                    str(row["status"]),
                    int(row["index_present_before"]),
                    int(row["index_present_after"]),
                    str(row["semantic_state_hash_before"]),
                    str(row["semantic_state_hash_after"]),
                    str(row["trace_root_hash_before"]),
                    str(row["trace_root_hash_after"]),
                    "UNKNOWN",
                    "UNKNOWN",
                    "UNKNOWN",
                    LEGACY_PROVENANCE_STATUS,
                    source_receipt_id,
                    str(row["executed_at"]),
                    AUTHORITY,
                ),
            )
            inserted += 1
        return inserted

    def maintenance_receipts_v6(self) -> list[dict[str, Any]]:
        if not self._v6_log_exists():
            return []
        rows = self.con.execute(
            f"SELECT * FROM {MAINTENANCE_LOG_TABLE_V6} ORDER BY audit_sequence"
        ).fetchall()
        return [dict(row) for row in rows]

    def apply_maintenance(
        self,
        plan: RankLifecyclePlan,
        *,
        actor: str,
        policy_provenance_ref: str,
        policy_decision_hash: str,
    ) -> RankMaintenanceReceiptV6:
        actor, policy_provenance_ref, policy_decision_hash = self._native_provenance(
            actor=actor,
            policy_provenance_ref=policy_provenance_ref,
            policy_decision_hash=policy_decision_hash,
        )

        if (
            plan.basis_epoch != self.ledger.epoch
            or plan.semantic_state_hash != self.ledger.semantic_state_hash
        ):
            raise StaleEpoch("rank maintenance plan no longer matches authoritative ledger")
        before = self.index_exists()
        if before != plan.actual_index_present:
            raise RankPhysicalStateStale(
                "rank maintenance physical precondition changed: "
                f"planned={plan.actual_index_present} actual={before}"
            )

        state_before = self.ledger.semantic_state_hash
        trace_before = self.ledger.trace_root_hash
        action = plan.maintenance_action
        if action == "NONE":
            return RankMaintenanceReceiptV6(
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
                actor=actor,
                policy_provenance_ref=policy_provenance_ref,
                policy_decision_hash=policy_decision_hash,
                provenance_status=NATIVE_PROVENANCE_STATUS,
            )
        if action not in {"BUILD_INDEX", "DROP_INDEX"}:
            raise ValueError(f"unsupported maintenance action: {action}")

        try:
            self.con.execute("BEGIN IMMEDIATE")
            if (
                plan.basis_epoch != self.ledger.epoch
                or plan.semantic_state_hash != self.ledger.semantic_state_hash
            ):
                raise StaleEpoch("rank maintenance plan became stale before physical commit")
            tx_before = self.index_exists()
            if tx_before != plan.actual_index_present:
                raise RankPhysicalStateStale(
                    "rank maintenance physical CAS failed: "
                    f"planned={plan.actual_index_present} actual={tx_before}"
                )

            self._create_v6_log_no_commit()
            self._migrate_v5_receipts_no_commit()
            if action == "BUILD_INDEX":
                self._create_index_no_commit()
                status = "BUILT"
            else:
                self._drop_index_no_commit()
                status = "DROPPED"
            after = self.index_exists()
            state_after = self.ledger.semantic_state_hash
            trace_after = self.ledger.trace_root_hash
            if (state_before, trace_before) != (state_after, trace_after):
                raise AssertionError(
                    "physical rank-index maintenance mutated semantic/trace roots"
                )

            audit_sequence = self._next_audit_sequence_no_commit()
            receipt_body = {
                "implementation": IMPLEMENTATION_ID,
                "audit_sequence": audit_sequence,
                "basis_epoch": plan.basis_epoch,
                "action": action,
                "status": status,
                "index_present_before": tx_before,
                "index_present_after": after,
                "semantic_state_hash_before": state_before,
                "semantic_state_hash_after": state_after,
                "trace_root_hash_before": trace_before,
                "trace_root_hash_after": trace_after,
                "plan_hash": plan.plan_hash,
                "actor": actor,
                "policy_provenance_ref": policy_provenance_ref,
                "policy_decision_hash": policy_decision_hash,
                "provenance_status": NATIVE_PROVENANCE_STATUS,
                "authority": AUTHORITY,
            }
            receipt_id = h(receipt_body)
            self.con.execute(
                f"""INSERT INTO {MAINTENANCE_LOG_TABLE_V6}(
                    receipt_id,audit_sequence,plan_hash,basis_epoch,action,status,
                    index_present_before,index_present_after,
                    semantic_state_hash_before,semantic_state_hash_after,
                    trace_root_hash_before,trace_root_hash_after,
                    actor,policy_provenance_ref,policy_decision_hash,provenance_status,
                    legacy_source_receipt_id,executed_at,authority
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)""",
                (
                    receipt_id,
                    audit_sequence,
                    plan.plan_hash,
                    plan.basis_epoch,
                    action,
                    status,
                    int(tx_before),
                    int(after),
                    state_before,
                    state_after,
                    trace_before,
                    trace_after,
                    actor,
                    policy_provenance_ref,
                    policy_decision_hash,
                    NATIVE_PROVENANCE_STATUS,
                    None,
                    AUTHORITY,
                ),
            )
            self.con.commit()
            return RankMaintenanceReceiptV6(
                basis_epoch=plan.basis_epoch,
                action=action,
                status=status,
                index_present_before=tx_before,
                index_present_after=after,
                semantic_state_hash_before=state_before,
                semantic_state_hash_after=state_after,
                trace_root_hash_before=trace_before,
                trace_root_hash_after=trace_after,
                plan_hash=plan.plan_hash,
                actor=actor,
                policy_provenance_ref=policy_provenance_ref,
                policy_decision_hash=policy_decision_hash,
                provenance_status=NATIVE_PROVENANCE_STATUS,
                audit_sequence=audit_sequence,
                receipt_id=receipt_id,
                persisted=True,
            )
        except (StaleEpoch, RankPhysicalStateStale):
            self.con.rollback()
            raise
        except Exception:
            self.con.rollback()
            after = self.index_exists()
            state_after = self.ledger.semantic_state_hash
            trace_after = self.ledger.trace_root_hash
            if (state_before, trace_before) != (state_after, trace_after):
                raise AssertionError(
                    "failed physical maintenance changed semantic/trace roots"
                )
            return RankMaintenanceReceiptV6(
                basis_epoch=plan.basis_epoch,
                action=action,
                status="FAILED_RETRYABLE_PHYSICAL_MAINTENANCE",
                index_present_before=before,
                index_present_after=after,
                semantic_state_hash_before=state_before,
                semantic_state_hash_after=state_after,
                trace_root_hash_before=trace_before,
                trace_root_hash_after=trace_after,
                plan_hash=plan.plan_hash,
                actor=actor,
                policy_provenance_ref=policy_provenance_ref,
                policy_decision_hash=policy_decision_hash,
                provenance_status=NATIVE_PROVENANCE_STATUS,
                persisted=False,
            )
