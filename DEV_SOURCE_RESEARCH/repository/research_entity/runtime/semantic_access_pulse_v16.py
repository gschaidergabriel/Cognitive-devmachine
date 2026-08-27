from __future__ import annotations

"""UnifiedDB V16 segmented Pulse maintenance candidate.

V16 is the renumbered successor of the provisional segmented-access V12 prototype. It keeps
that prototype's copy-on-write generation semantics but fixes one auditability defect: the
segment content identity is now defined over exactly the representation persisted by SQLite
(path rows + segment-wide dependency closure), so a deep audit can deterministically
reconstruct and verify every immutable segment.

This is a rebuildable maintenance/access projection. UnifiedDB/StateLedger remains semantic
truth authority. V16 never grants effect authority and is not the FRANK Database Pulse
cognitive cycle.
"""

from typing import Sequence

from semantic_access_pulse_v12 import (
    AccessPath,
    PulseInvariantError,
    SegmentedPulseProjection,
    _digest,
)


IMPLEMENTATION_ID = "UNIFIEDDB_V16_SEGMENTED_PULSE_MAINTENANCE"


class SegmentedPulseProjectionV16(SegmentedPulseProjection):
    """Audit-complete successor of the provisional segmented Pulse projection."""

    @staticmethod
    def _canonical_segment_body(seed_id: str, paths: Sequence[AccessPath]) -> tuple[list[list], list[str]]:
        path_rows = [
            [
                p.target_record_id,
                p.target_logical_id,
                p.path_rank,
                p.hop_count,
                round(p.path_weight, 12),
                round(p.authority_rank, 12),
                p.path_clay,
            ]
            for p in paths
        ]
        dependency_closure = sorted({d for p in paths for d in p.dependencies})
        return path_rows, dependency_closure

    def _ensure_segment(self, seed_id: str, paths: Sequence[AccessPath]) -> tuple[str, bool, int]:
        paths = self._validate_seed_paths(seed_id, paths)
        path_rows, dependency_closure = self._canonical_segment_body(seed_id, paths)
        segment_hash = _digest(
            {
                "seed_id": seed_id,
                "paths": path_rows,
                "dependency_closure": dependency_closure,
            }
        )
        segment_id = "seg-" + segment_hash[:24]
        exists = self.con.execute(
            "SELECT 1 FROM access_segment WHERE segment_id=?", (segment_id,)
        ).fetchone()
        if exists:
            return segment_id, False, len(paths)

        import time

        self.con.execute(
            "INSERT INTO access_segment VALUES(?,?,?,?,?)",
            (segment_id, seed_id, segment_hash, len(paths), time.time_ns()),
        )
        self.con.executemany(
            "INSERT INTO access_segment_path VALUES(?,?,?,?,?,?,?,?)",
            [
                (
                    segment_id,
                    p.target_record_id,
                    p.target_logical_id,
                    p.path_rank,
                    p.hop_count,
                    p.path_weight,
                    p.authority_rank,
                    p.path_clay,
                )
                for p in paths
            ],
        )
        self.con.executemany(
            "INSERT INTO access_segment_dependency VALUES(?,?)",
            [(segment_id, d) for d in dependency_closure],
        )
        actual = self.con.execute(
            "SELECT count(*) FROM access_segment_path WHERE segment_id=?", (segment_id,)
        ).fetchone()[0]
        if actual != len(paths):
            raise PulseInvariantError("segment path count mismatch")
        return segment_id, True, len(paths)

    def audit_current_generation(self) -> dict:
        """Slow integrity audit; intentionally not in the local-update hot path.

        Recomputes:
        - every referenced immutable segment's content hash and id;
        - path-count metadata;
        - seed/segment identity agreement;
        - the complete generation map hash and access-head binding.

        Any mismatch raises PulseInvariantError. This is recovery/release evidence, not a
        replacement for SQLite's own integrity checks.
        """
        head = self._head()
        if not head:
            raise PulseInvariantError("deep audit requires current generation")
        generation_id = str(head["generation_id"])
        mapping = [
            (str(r["seed_id"]), str(r["segment_id"]))
            for r in self.con.execute(
                "SELECT seed_id,segment_id FROM access_generation_seed WHERE generation_id=? ORDER BY seed_id",
                (generation_id,),
            )
        ]
        if not mapping:
            raise PulseInvariantError("deep audit found empty generation map")

        audited_paths = 0
        for seed_id, segment_id in mapping:
            segment = self.con.execute(
                "SELECT seed_id,segment_hash,path_count FROM access_segment WHERE segment_id=?",
                (segment_id,),
            ).fetchone()
            if segment is None:
                raise PulseInvariantError(f"deep audit missing segment: {segment_id}")
            if str(segment["seed_id"]) != seed_id:
                raise PulseInvariantError(f"deep audit seed/segment mismatch: {seed_id}")

            rows = list(
                self.con.execute(
                    """SELECT target_record_id,target_logical_id,path_rank,hop_count,
                              path_weight,authority_rank,path_clay
                       FROM access_segment_path
                       WHERE segment_id=?
                       ORDER BY path_rank,path_weight DESC,authority_rank DESC,target_record_id""",
                    (segment_id,),
                )
            )
            if len(rows) != int(segment["path_count"]):
                raise PulseInvariantError(f"deep audit path count mismatch: {segment_id}")
            if not rows:
                raise PulseInvariantError(f"deep audit empty segment: {segment_id}")
            audited_paths += len(rows)

            dependency_closure = [
                str(r[0])
                for r in self.con.execute(
                    """SELECT dependency_logical_id FROM access_segment_dependency
                       WHERE segment_id=? ORDER BY dependency_logical_id""",
                    (segment_id,),
                )
            ]
            path_rows = [
                [
                    str(r["target_record_id"]),
                    str(r["target_logical_id"]),
                    int(r["path_rank"]),
                    int(r["hop_count"]),
                    round(float(r["path_weight"]), 12),
                    round(float(r["authority_rank"]), 12),
                    str(r["path_clay"]),
                ]
                for r in rows
            ]
            recomputed_hash = _digest(
                {
                    "seed_id": seed_id,
                    "paths": path_rows,
                    "dependency_closure": dependency_closure,
                }
            )
            if recomputed_hash != str(segment["segment_hash"]):
                raise PulseInvariantError(f"deep audit segment hash mismatch: {segment_id}")
            if "seg-" + recomputed_hash[:24] != segment_id:
                raise PulseInvariantError(f"deep audit segment id mismatch: {segment_id}")

        generation_hash = self._generation_hash(
            int(head["source_epoch"]), int(head["graph_epoch"]), mapping
        )
        if generation_hash != str(head["generation_hash"]):
            raise PulseInvariantError("deep audit generation/head hash mismatch")
        stored = self.con.execute(
            "SELECT generation_hash,seed_count,status FROM access_generation WHERE generation_id=?",
            (generation_id,),
        ).fetchone()
        if stored is None or str(stored["status"]) != "CURRENT":
            raise PulseInvariantError("deep audit current generation metadata missing")
        if str(stored["generation_hash"]) != generation_hash:
            raise PulseInvariantError("deep audit generation metadata hash mismatch")
        if int(stored["seed_count"]) != len(mapping):
            raise PulseInvariantError("deep audit generation seed count mismatch")

        return {
            "pass": True,
            "implementation": IMPLEMENTATION_ID,
            "generation_id": generation_id,
            "source_epoch": int(head["source_epoch"]),
            "graph_epoch": int(head["graph_epoch"]),
            "generation_hash": generation_hash,
            "segments_audited": len(mapping),
            "paths_audited": audited_paths,
            "authority": "NON_AUTHORITATIVE_REBUILDABLE_ACCESS_PROJECTION",
        }
