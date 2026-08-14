from __future__ import annotations

"""SPM-S1 persistent integrity tripwire and fail-closed recovery candidate.

SPM-S1 already owns deterministic deep audits. This extension closes the between-audit window:
post-publication mutation of CURRENT segment/mapping rows marks projection health DIRTY inside the
same SQLite transaction. Reads then fail closed and the next maintenance cycle is forced through
an authoritative FULL_FALLBACK plus SPM-S1 deep audit before CLEAN is restored.
"""

from dataclasses import replace
from pathlib import Path
import time
from typing import Sequence

from semantic_access_pulse_v12 import AccessPath, PulseInvariantError, PulsePlan, PulseReceipt, _digest, _stable
from semantic_access_segmented_maintenance_s1 import SegmentedPulseMaintenanceS1

IMPLEMENTATION_ID = "UNIFIEDDB_SEGMENTED_PULSE_MAINTENANCE_S1_GUARDED"


class SPMIntegrityError(PulseInvariantError):
    pass


class SegmentedPulseMaintenanceS1Guarded(SegmentedPulseMaintenanceS1):
    def __init__(self, path: str = ":memory:"):
        super().__init__(path)
        schema = Path(__file__).with_name("RAE_UNIFIEDDB_SPM_S1_INTEGRITY_TRIPWIRE.sql")
        self.con.executescript(schema.read_text(encoding="utf-8"))
        # Existing DB migration is fail-closed: never assume pre-tripwire content was intact.
        raw_head = self.con.execute(
            "SELECT 1 FROM access_head WHERE head_key='CURRENT'"
        ).fetchone()
        if raw_head:
            try:
                self.audit_current_generation()
            except PulseInvariantError:
                self._set_dirty(None, "BOOT_DEEP_AUDIT_FAILED")

    def integrity_state(self) -> dict:
        row = self.con.execute(
            "SELECT status,dirty_segment_id,dirty_reason,mutation_count,updated_ns "
            "FROM spm_s1_integrity_state WHERE singleton_id=1"
        ).fetchone()
        return {
            "status": str(row[0]),
            "dirty_segment_id": row[1],
            "dirty_reason": row[2],
            "mutation_count": int(row[3]),
            "updated_ns": int(row[4]),
        }

    def _set_dirty(self, segment_id: str | None, reason: str) -> None:
        nested = self.con.in_transaction
        if nested:
            self.con.execute("SAVEPOINT spm_s1_mark_dirty")
        else:
            self.con.execute("BEGIN IMMEDIATE")
        try:
            self.con.execute(
                """UPDATE spm_s1_integrity_state
                   SET status='DIRTY',dirty_segment_id=?,dirty_reason=?,
                       mutation_count=mutation_count+1,updated_ns=? WHERE singleton_id=1""",
                (segment_id, reason, time.time_ns()),
            )
            if nested:
                self.con.execute("RELEASE SAVEPOINT spm_s1_mark_dirty")
            else:
                self.con.commit()
        except Exception:
            if nested:
                self.con.execute("ROLLBACK TO SAVEPOINT spm_s1_mark_dirty")
                self.con.execute("RELEASE SAVEPOINT spm_s1_mark_dirty")
            else:
                self.con.rollback()
            raise

    def _expected_segment(self, seed_id: str, paths: Sequence[AccessPath]):
        paths = self._validate_seed_paths(seed_id, paths)
        path_rows, dependency_closure = self._canonical_segment_body(seed_id, paths)
        segment_hash = _digest({
            "seed_id": seed_id,
            "paths": path_rows,
            "dependency_closure": dependency_closure,
        })
        return paths, path_rows, dependency_closure, segment_hash, "seg-" + segment_hash[:24]

    def _segment_matches_expected(
        self,
        segment_id: str,
        seed_id: str,
        path_rows: Sequence[Sequence],
        dependency_closure: Sequence[str],
        segment_hash: str,
    ) -> bool:
        header = self.con.execute(
            "SELECT seed_id,segment_hash,path_count FROM access_segment WHERE segment_id=?",
            (segment_id,),
        ).fetchone()
        if not header:
            return False
        if str(header[0]) != seed_id or str(header[1]) != segment_hash or int(header[2]) != len(path_rows):
            return False
        stored_paths = [
            [
                str(r[0]), str(r[1]), int(r[2]), int(r[3]),
                round(float(r[4]), 12), round(float(r[5]), 12), str(r[6]),
            ]
            for r in self.con.execute(
                """SELECT target_record_id,target_logical_id,path_rank,hop_count,path_weight,
                          authority_rank,path_clay FROM access_segment_path
                   WHERE segment_id=?
                   ORDER BY path_rank,path_weight DESC,authority_rank DESC,target_record_id""",
                (segment_id,),
            ).fetchall()
        ]
        if stored_paths != list(path_rows):
            return False
        stored_deps = [str(r[0]) for r in self.con.execute(
            "SELECT dependency_logical_id FROM access_segment_dependency "
            "WHERE segment_id=? ORDER BY dependency_logical_id",
            (segment_id,),
        ).fetchall()]
        return stored_deps == list(dependency_closure)

    def _restore_segment_in_place(
        self,
        segment_id: str,
        seed_id: str,
        paths: Sequence[AccessPath],
        dependency_closure: Sequence[str],
        segment_hash: str,
    ) -> None:
        # Called only while the persistent health flag is already DIRTY and a full authoritative
        # recompute is in progress. Restoring exact hash-consistent content repairs the immutable
        # projection; old generations referring to this content-address id regain their original
        # intended bytes rather than being silently rewritten to new semantics.
        self.con.execute(
            "UPDATE access_segment SET seed_id=?,segment_hash=?,path_count=? WHERE segment_id=?",
            (seed_id, segment_hash, len(paths), segment_id),
        )
        self.con.execute("DELETE FROM access_segment_path WHERE segment_id=?", (segment_id,))
        self.con.execute("DELETE FROM access_segment_dependency WHERE segment_id=?", (segment_id,))
        self.con.executemany(
            "INSERT INTO access_segment_path VALUES(?,?,?,?,?,?,?,?)",
            [
                (
                    segment_id, p.target_record_id, p.target_logical_id, p.path_rank,
                    p.hop_count, p.path_weight, p.authority_rank, p.path_clay,
                )
                for p in paths
            ],
        )
        self.con.executemany(
            "INSERT INTO access_segment_dependency VALUES(?,?)",
            [(segment_id, d) for d in dependency_closure],
        )

    def _ensure_segment(self, seed_id: str, paths: Sequence[AccessPath]) -> tuple[str, bool, int]:
        paths, path_rows, deps, segment_hash, segment_id = self._expected_segment(seed_id, paths)
        exists = self.con.execute("SELECT 1 FROM access_segment WHERE segment_id=?", (segment_id,)).fetchone()
        if not exists:
            return super()._ensure_segment(seed_id, paths)
        if self._segment_matches_expected(segment_id, seed_id, path_rows, deps, segment_hash):
            return segment_id, False, len(paths)
        state = self.integrity_state()
        if state["status"] != "DIRTY":
            raise SPMIntegrityError(f"content-addressed segment mismatch while CLEAN: {segment_id}")
        self._restore_segment_in_place(segment_id, seed_id, paths, deps, segment_hash)
        if not self._segment_matches_expected(segment_id, seed_id, path_rows, deps, segment_hash):
            raise SPMIntegrityError(f"segment repair verification failed: {segment_id}")
        return segment_id, False, len(paths)

    def query(self, seed_id: str, limit: int = 20) -> tuple[str, ...]:
        state = self.integrity_state()
        if state["status"] != "CLEAN":
            raise SPMIntegrityError(
                f"SPM-S1 projection DIRTY: {state['dirty_reason']} segment={state['dirty_segment_id']}"
            )
        raw_head = self.con.execute(
            "SELECT generation_id,source_epoch,graph_epoch,generation_hash FROM access_head WHERE head_key='CURRENT'"
        ).fetchone()
        coherent_head = self._head()
        if raw_head is not None and coherent_head is None:
            self._set_dirty(None, "ACCESS_HEAD_INCOHERENT")
            raise SPMIntegrityError("SPM-S1 access_head is present but incoherent")
        return super().query(seed_id, limit)

    def apply_pulse(
        self,
        plan: PulsePlan,
        *,
        recompute_seed,
        recompute_all_seeds,
        incremental_fraction_limit: float = 0.25,
    ) -> PulseReceipt:
        before = self.integrity_state()
        effective = plan if before["status"] == "CLEAN" else replace(plan, impact_complete=False)
        receipt = super().apply_pulse(
            effective,
            recompute_seed=recompute_seed,
            recompute_all_seeds=recompute_all_seeds,
            incremental_fraction_limit=incremental_fraction_limit,
        )
        if before["status"] == "DIRTY":
            if receipt.mode != "FULL_FALLBACK":
                raise SPMIntegrityError("DIRTY projection escaped without FULL_FALLBACK")
            audit = self.audit_current_generation()
            quarantined_generation_id = None
            if (
                before["dirty_reason"] is not None
                and str(before["dirty_reason"]).startswith("CURRENT_GENERATION_MAP_")
                and receipt.previous_generation_id
            ):
                quarantined_generation_id = receipt.previous_generation_id
            with self.con:
                if quarantined_generation_id is not None:
                    self.con.execute(
                        "UPDATE access_generation SET status='QUARANTINED' "
                        "WHERE generation_id=? AND status='SUPERSEDED'",
                        (quarantined_generation_id,),
                    )
                self.con.execute(
                    "INSERT INTO spm_s1_integrity_repair_receipt VALUES(?,?,?,?,?,?,?)",
                    (
                        plan.event_id,
                        before["dirty_segment_id"],
                        before["dirty_reason"],
                        receipt.generation_id,
                        "FULL_FALLBACK",
                        _stable({
                            "audit": audit,
                            "pulse_receipt": receipt.__dict__,
                            "quarantined_previous_generation_id": quarantined_generation_id,
                        }),
                        time.time_ns(),
                    ),
                )
                self.con.execute(
                    """UPDATE spm_s1_integrity_state
                       SET status='CLEAN',dirty_segment_id=NULL,dirty_reason=NULL,updated_ns=?
                       WHERE singleton_id=1""",
                    (time.time_ns(),),
                )
        return receipt

    def guarded_audit(self) -> dict:
        receipt = dict(self.audit_current_generation())
        receipt["guard_implementation"] = IMPLEMENTATION_ID
        receipt["integrity_state"] = self.integrity_state()
        return receipt
