from __future__ import annotations

"""V16.1 integrity guard for UnifiedDB segmented Pulse maintenance.

V16 remains the maintenance primitive. This extension adds tamper-evident manifests and a
fail-closed DIRTY tripwire without changing semantic truth/effect authority. The historical
base implementation filenames still contain v12; the coordinated current identity is V16.
"""

import json
from pathlib import Path
import time
from typing import Sequence

from semantic_access_pulse_v12 import (
    AccessPath,
    PulseInvariantError,
    PulsePlan,
    PulseReceipt,
    SegmentedPulseProjection,
    _digest,
    _stable,
)


class SegmentIntegrityError(PulseInvariantError):
    pass


class IntegrityGuardedSegmentedPulseProjection(SegmentedPulseProjection):
    """V16 projection with segment manifests, mutation tripwires and fail-closed repair."""

    def __init__(self, path: str = ":memory:"):
        super().__init__(path)
        schema = Path(__file__).with_name("RAE_UNIFIEDDB_V16_1_SEGMENT_INTEGRITY.sql")
        self.con.executescript(schema.read_text(encoding="utf-8"))

    @staticmethod
    def _body(seed_id: str, paths: Sequence[AccessPath]) -> tuple[list[AccessPath], dict]:
        paths = SegmentedPulseProjection._validate_seed_paths(seed_id, paths)
        body = [
            [
                p.target_record_id,
                p.target_logical_id,
                p.path_rank,
                p.hop_count,
                round(p.path_weight, 12),
                round(p.authority_rank, 12),
                p.path_clay,
                sorted(set(p.dependencies)),
            ]
            for p in paths
        ]
        return paths, {"seed_id": seed_id, "paths": body}

    def integrity_state(self) -> dict:
        row = self.con.execute(
            "SELECT status,dirty_segment_id,dirty_reason,mutation_count,updated_ns "
            "FROM access_projection_integrity_v16_1 WHERE singleton_id=1"
        ).fetchone()
        return {
            "status": row[0],
            "dirty_segment_id": row[1],
            "dirty_reason": row[2],
            "mutation_count": int(row[3]),
            "updated_ns": int(row[4]),
        }

    def _mark_dirty(self, segment_id: str | None, reason: str) -> None:
        self.con.execute(
            """UPDATE access_projection_integrity_v16_1
               SET status='DIRTY',dirty_segment_id=?,dirty_reason=?,
                   mutation_count=mutation_count+1,updated_ns=? WHERE singleton_id=1""",
            (segment_id, reason, time.time_ns()),
        )
        self.con.commit()

    @staticmethod
    def _manifest_union_dependencies(manifest: dict) -> list[str]:
        return sorted({str(d) for row in manifest["paths"] for d in row[7]})

    def _stored_content_matches_manifest(self, segment_id: str, manifest: dict) -> bool:
        segment = self.con.execute(
            "SELECT seed_id,segment_hash,path_count FROM access_segment WHERE segment_id=?",
            (segment_id,),
        ).fetchone()
        if not segment:
            return False
        if segment[0] != manifest.get("seed_id"):
            return False
        expected_hash = _digest(manifest)
        if segment[1] != expected_hash:
            return False
        expected_paths = [tuple(row[:7]) for row in manifest["paths"]]
        stored_paths = [
            (
                r[0], r[1], int(r[2]), int(r[3]), round(float(r[4]), 12),
                round(float(r[5]), 12), r[6],
            )
            for r in self.con.execute(
                """SELECT target_record_id,target_logical_id,path_rank,hop_count,path_weight,
                          authority_rank,path_clay FROM access_segment_path WHERE segment_id=?
                   ORDER BY path_rank,path_weight DESC,authority_rank DESC,target_record_id""",
                (segment_id,),
            ).fetchall()
        ]
        if int(segment[2]) != len(expected_paths) or stored_paths != expected_paths:
            return False
        stored_deps = [r[0] for r in self.con.execute(
            "SELECT dependency_logical_id FROM access_segment_dependency "
            "WHERE segment_id=? ORDER BY dependency_logical_id", (segment_id,)
        ).fetchall()]
        return stored_deps == self._manifest_union_dependencies(manifest)

    def verify_segment(self, segment_id: str) -> dict:
        row = self.con.execute(
            "SELECT manifest_json,manifest_hash FROM access_segment_manifest_v16_1 WHERE segment_id=?",
            (segment_id,),
        ).fetchone()
        if not row:
            raise SegmentIntegrityError(f"segment manifest missing: {segment_id}")
        try:
            manifest = json.loads(row[0])
        except Exception as exc:
            raise SegmentIntegrityError(f"segment manifest invalid JSON: {segment_id}") from exc
        expected_hash = _digest(manifest)
        if row[1] != expected_hash:
            raise SegmentIntegrityError(f"segment manifest hash mismatch: {segment_id}")
        if not self._stored_content_matches_manifest(segment_id, manifest):
            raise SegmentIntegrityError(f"segment storage diverged from manifest: {segment_id}")
        return {"segment_id": segment_id, "manifest_hash": expected_hash, "verified": True}

    def _insert_manifested_segment(
        self, segment_id: str, seed_id: str, paths: Sequence[AccessPath], manifest: dict
    ) -> tuple[str, bool, int]:
        segment_hash = _digest(manifest)
        self.con.execute(
            "INSERT INTO access_segment VALUES(?,?,?,?,?)",
            (segment_id, seed_id, segment_hash, len(paths), time.time_ns()),
        )
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
        deps = self._manifest_union_dependencies(manifest)
        self.con.executemany(
            "INSERT INTO access_segment_dependency VALUES(?,?)",
            [(segment_id, d) for d in deps],
        )
        text = _stable(manifest)
        self.con.execute(
            "INSERT INTO access_segment_manifest_v16_1 VALUES(?,?,?,?)",
            (segment_id, text, segment_hash, time.time_ns()),
        )
        self.verify_segment(segment_id)
        return segment_id, True, len(paths)

    def _ensure_segment(self, seed_id: str, paths: Sequence[AccessPath]) -> tuple[str, bool, int]:
        paths, manifest = self._body(seed_id, paths)
        segment_hash = _digest(manifest)
        base_id = "seg-" + segment_hash[:24]
        exists = self.con.execute(
            "SELECT 1 FROM access_segment WHERE segment_id=?", (base_id,)
        ).fetchone()
        if not exists:
            return self._insert_manifested_segment(base_id, seed_id, paths, manifest)

        manifest_row = self.con.execute(
            "SELECT 1 FROM access_segment_manifest_v16_1 WHERE segment_id=?", (base_id,)
        ).fetchone()
        if manifest_row:
            try:
                self.verify_segment(base_id)
                return base_id, False, len(paths)
            except SegmentIntegrityError:
                pass
        elif self._stored_content_matches_manifest(base_id, manifest):
            # Safe migration/adoption of a pre-V16.1 segment: only after exact content comparison.
            self.con.execute(
                "INSERT INTO access_segment_manifest_v16_1 VALUES(?,?,?,?)",
                (base_id, _stable(manifest), segment_hash, time.time_ns()),
            )
            return base_id, False, len(paths)

        # A content-address collision exists physically but its stored rows no longer represent
        # the expected content. Never reuse it. Create a repair instance with the same semantic
        # manifest hash and a distinct physical identity so a full fallback can recover safely.
        salt = _digest({
            "manifest_hash": segment_hash,
            "integrity": self.integrity_state(),
            "created_ns": time.time_ns(),
        })[:12]
        repair_id = f"{base_id}-repair-{salt}"
        return self._insert_manifested_segment(repair_id, seed_id, paths, manifest)

    def query(self, seed_id: str, limit: int = 20) -> tuple[str, ...]:
        state = self.integrity_state()
        if state["status"] != "CLEAN":
            raise SegmentIntegrityError(
                f"projection DIRTY: {state['dirty_reason']} segment={state['dirty_segment_id']}"
            )
        head = self._head()
        if not head:
            return ()
        row = self.con.execute(
            "SELECT segment_id FROM access_generation_seed WHERE generation_id=? AND seed_id=?",
            (head["generation_id"], seed_id),
        ).fetchone()
        if not row:
            return ()
        try:
            self.verify_segment(row[0])
        except SegmentIntegrityError as exc:
            self._mark_dirty(row[0], "MANIFEST_VERIFICATION_FAILED")
            raise exc
        return super().query(seed_id, limit)

    def deep_verify_current(self) -> dict:
        state = self.integrity_state()
        if state["status"] != "CLEAN":
            raise SegmentIntegrityError(f"projection DIRTY before audit: {state['dirty_reason']}")
        head = self._head()
        if not head:
            return {"verified": True, "segment_count": 0, "generation_id": None}
        segments = [r[0] for r in self.con.execute(
            "SELECT DISTINCT segment_id FROM access_generation_seed WHERE generation_id=? ORDER BY segment_id",
            (head["generation_id"],),
        ).fetchall()]
        for segment_id in segments:
            self.verify_segment(segment_id)
        return {"verified": True, "segment_count": len(segments), "generation_id": head["generation_id"]}

    def apply_pulse(
        self,
        plan: PulsePlan,
        *,
        recompute_seed,
        recompute_all_seeds,
        incremental_fraction_limit: float = 0.25,
    ) -> PulseReceipt:
        before = self.integrity_state()
        effective = plan
        if before["status"] == "DIRTY":
            effective = PulsePlan(
                event_id=plan.event_id,
                change_class=plan.change_class,
                changed_logical_ids=plan.changed_logical_ids,
                impact_seed_ids=plan.impact_seed_ids,
                impact_complete=False,
                to_source_epoch=plan.to_source_epoch,
                to_graph_epoch=plan.to_graph_epoch,
            )
        receipt = super().apply_pulse(
            effective,
            recompute_seed=recompute_seed,
            recompute_all_seeds=recompute_all_seeds,
            incremental_fraction_limit=incremental_fraction_limit,
        )
        if before["status"] == "DIRTY":
            if receipt.mode != "FULL_FALLBACK":
                raise SegmentIntegrityError("DIRTY projection repaired without FULL_FALLBACK")
            audit = self.deep_verify_current_allow_dirty()
            with self.con:
                self.con.execute(
                    """INSERT INTO access_integrity_repair_receipt_v16_1
                       VALUES(?,?,?,?,?,?,?)""",
                    (
                        plan.event_id,
                        before["dirty_segment_id"],
                        before["dirty_reason"],
                        receipt.generation_id,
                        "FULL_FALLBACK",
                        _stable({"pulse_receipt": receipt.__dict__, "audit": audit}),
                        time.time_ns(),
                    ),
                )
                self.con.execute(
                    """UPDATE access_projection_integrity_v16_1
                       SET status='CLEAN',dirty_segment_id=NULL,dirty_reason=NULL,updated_ns=?
                       WHERE singleton_id=1""",
                    (time.time_ns(),),
                )
        return receipt

    def deep_verify_current_allow_dirty(self) -> dict:
        """Slow repair-gate audit; does not trust the pre-existing DIRTY status."""
        head = self._head()
        if not head:
            raise SegmentIntegrityError("repair produced no current head")
        segments = [r[0] for r in self.con.execute(
            "SELECT DISTINCT segment_id FROM access_generation_seed WHERE generation_id=? ORDER BY segment_id",
            (head["generation_id"],),
        ).fetchall()]
        for segment_id in segments:
            self.verify_segment(segment_id)
        return {"verified": True, "segment_count": len(segments), "generation_id": head["generation_id"]}
