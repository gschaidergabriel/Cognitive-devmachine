from __future__ import annotations

"""Incremental salience-aware active field for FRANK Database Pulse research.

This is a rebuildable, non-authoritative projection over the H1 StateLedger. It addresses a
specific falsifiable weakness in database_pulse_candidate_v1: QueryPlane max_candidates is
otherwise applied in lexicographic state order before Pulse salience scoring.

The active field performs one full rebuild at bootstrap/recovery, then incrementally updates
only StateLedger keys touched by new authoritative events. Salience is materialized before
the candidate budget cut. UnifiedDB/StateLedger remains truth authority; this projection can
be deleted and rebuilt at any time and never grants effect authority.
"""

from dataclasses import dataclass
import json
import sqlite3
from typing import Any, Iterable

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, h


SCHEMA = r"""
CREATE TABLE IF NOT EXISTS pulse_active_field_meta(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  last_event_seq INTEGER NOT NULL DEFAULT 0 CHECK(last_event_seq >= 0),
  ledger_epoch INTEGER NOT NULL DEFAULT 0 CHECK(ledger_epoch >= 0),
  semantic_state_hash TEXT NOT NULL,
  rebuild_count INTEGER NOT NULL DEFAULT 0 CHECK(rebuild_count >= 0),
  delta_refresh_count INTEGER NOT NULL DEFAULT 0 CHECK(delta_refresh_count >= 0),
  projection_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pulse_active_field(
  domain TEXT NOT NULL,
  k TEXT NOT NULL,
  value_json TEXT,
  epistemic TEXT NOT NULL,
  status TEXT NOT NULL,
  domain_epoch INTEGER NOT NULL,
  semantic_hash TEXT NOT NULL,
  base_score REAL NOT NULL,
  score_components_clay TEXT NOT NULL,
  last_event_seq INTEGER NOT NULL,
  PRIMARY KEY(domain,k)
);

CREATE INDEX IF NOT EXISTS idx_pulse_active_field_known_score
ON pulse_active_field(base_score DESC,domain,k,semantic_hash)
WHERE status='CURRENT' AND epistemic='KNOWN';

CREATE INDEX IF NOT EXISTS idx_pulse_active_field_domain_score
ON pulse_active_field(domain,base_score DESC,k,semantic_hash)
WHERE status='CURRENT' AND epistemic='KNOWN';

CREATE INDEX IF NOT EXISTS idx_pulse_active_field_observability
ON pulse_active_field(domain,epistemic,status,k);
"""

PROJECTION_VERSION = "PULSE_ACTIVE_FIELD_V2"
REENTRY_BOOST = 0.30


class ActiveFieldError(RuntimeError):
    pass


class ActiveFieldIntegrityError(ActiveFieldError):
    pass


@dataclass(frozen=True)
class ActiveFieldSelection:
    basis_epoch: int
    semantic_state_hash: str
    focus_refs: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    conflicts_present: int
    unknown_present: int
    projection_last_event_seq: int
    refresh_mode: str
    selection_hash: str
    authority: str = "CONTEXT_ONLY_NON_AUTHORITATIVE_PROJECTION"


def signal_score(value: Any) -> tuple[float, dict[str, float]]:
    """Byte-for-semantics match of database_pulse_candidate_v1._signal_score."""
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


class PulseActiveFieldV2:
    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self.con = ledger.conn
        self.con.executescript(SCHEMA)
        self.con.commit()

    def _max_event_seq(self) -> int:
        row = self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()
        return int(row[0])

    def _meta(self):
        return self.con.execute(
            "SELECT * FROM pulse_active_field_meta WHERE singleton_id=1"
        ).fetchone()

    @staticmethod
    def _decode_value(value_json: str | None) -> Any:
        return json.loads(value_json) if value_json is not None else None

    def _upsert_state_ref(self, domain: str, key: str, event_seq: int) -> None:
        row = self.con.execute(
            """SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash
               FROM state WHERE domain=? AND k=?""",
            (domain, key),
        ).fetchone()
        if row is None:
            self.con.execute(
                "DELETE FROM pulse_active_field WHERE domain=? AND k=?", (domain, key)
            )
            return
        value = self._decode_value(row["value_json"])
        score, components = signal_score(value)
        self.con.execute(
            """INSERT INTO pulse_active_field
              (domain,k,value_json,epistemic,status,domain_epoch,semantic_hash,base_score,
               score_components_clay,last_event_seq)
              VALUES(?,?,?,?,?,?,?,?,?,?)
              ON CONFLICT(domain,k) DO UPDATE SET
                value_json=excluded.value_json,
                epistemic=excluded.epistemic,
                status=excluded.status,
                domain_epoch=excluded.domain_epoch,
                semantic_hash=excluded.semantic_hash,
                base_score=excluded.base_score,
                score_components_clay=excluded.score_components_clay,
                last_event_seq=excluded.last_event_seq""",
            (
                row["domain"],
                row["k"],
                row["value_json"],
                row["epistemic"],
                row["status"],
                int(row["domain_epoch"]),
                row["semantic_hash"],
                float(score),
                json.dumps(components, sort_keys=True, separators=(",", ":")),
                event_seq,
            ),
        )

    def full_rebuild(self, *, now: str) -> dict[str, Any]:
        """Rebuild from authoritative StateLedger rows; used for bootstrap/recovery only."""
        self.con.execute("BEGIN IMMEDIATE")
        try:
            self.con.execute("DELETE FROM pulse_active_field")
            event_seq = self._max_event_seq()
            rows = list(self.con.execute("SELECT domain,k FROM state ORDER BY domain,k"))
            for row in rows:
                self._upsert_state_ref(str(row["domain"]), str(row["k"]), event_seq)
            old = self._meta()
            rebuild_count = (int(old["rebuild_count"]) if old else 0) + 1
            delta_count = int(old["delta_refresh_count"]) if old else 0
            self.con.execute(
                """INSERT INTO pulse_active_field_meta
                  (singleton_id,last_event_seq,ledger_epoch,semantic_state_hash,rebuild_count,
                   delta_refresh_count,projection_version,updated_at)
                  VALUES(1,?,?,?,?,?,?,?)
                  ON CONFLICT(singleton_id) DO UPDATE SET
                    last_event_seq=excluded.last_event_seq,
                    ledger_epoch=excluded.ledger_epoch,
                    semantic_state_hash=excluded.semantic_state_hash,
                    rebuild_count=excluded.rebuild_count,
                    delta_refresh_count=excluded.delta_refresh_count,
                    projection_version=excluded.projection_version,
                    updated_at=excluded.updated_at""",
                (
                    event_seq,
                    self.ledger.epoch,
                    self.ledger.semantic_state_hash,
                    rebuild_count,
                    delta_count,
                    PROJECTION_VERSION,
                    now,
                ),
            )
            self.con.commit()
            return {
                "mode": "FULL_REBUILD",
                "touched_refs": len(rows),
                "last_event_seq": event_seq,
                "ledger_epoch": self.ledger.epoch,
            }
        except Exception:
            self.con.rollback()
            raise

    def refresh(self, *, now: str) -> dict[str, Any]:
        """Incrementally apply only refs touched by new authoritative events."""
        meta = self._meta()
        current_seq = self._max_event_seq()
        if meta is None:
            return self.full_rebuild(now=now)
        if str(meta["projection_version"]) != PROJECTION_VERSION:
            return self.full_rebuild(now=now)
        if int(meta["last_event_seq"]) > current_seq or int(meta["ledger_epoch"]) > self.ledger.epoch:
            return self.full_rebuild(now=now)
        if int(meta["last_event_seq"]) == current_seq:
            if str(meta["semantic_state_hash"]) != self.ledger.semantic_state_hash:
                raise ActiveFieldIntegrityError(
                    "ledger semantic root changed without a new authoritative event"
                )
            return {
                "mode": "NO_CHANGE",
                "touched_refs": 0,
                "last_event_seq": current_seq,
                "ledger_epoch": self.ledger.epoch,
            }

        events = list(
            self.con.execute(
                "SELECT seq,ops_json FROM events WHERE seq>? ORDER BY seq",
                (int(meta["last_event_seq"]),),
            )
        )
        touched: dict[tuple[str, str], int] = {}
        for event in events:
            try:
                ops = json.loads(event["ops_json"])
            except Exception as exc:
                raise ActiveFieldIntegrityError(f"unreadable event ops at seq={event['seq']}: {exc}") from exc
            for op in ops:
                domain = str(op.get("domain") or "")
                key = str(op.get("key") or "")
                if domain and key:
                    touched[(domain, key)] = int(event["seq"])

        self.con.execute("BEGIN IMMEDIATE")
        try:
            for (domain, key), event_seq in sorted(touched.items()):
                self._upsert_state_ref(domain, key, event_seq)
            self.con.execute(
                """UPDATE pulse_active_field_meta SET
                   last_event_seq=?,ledger_epoch=?,semantic_state_hash=?,
                   delta_refresh_count=delta_refresh_count+1,updated_at=?
                   WHERE singleton_id=1""",
                (current_seq, self.ledger.epoch, self.ledger.semantic_state_hash, now),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise
        return {
            "mode": "DELTA_REFRESH",
            "touched_refs": len(touched),
            "events_consumed": len(events),
            "last_event_seq": current_seq,
            "ledger_epoch": self.ledger.epoch,
        }

    @staticmethod
    def _where_in(column: str, values: Iterable[str], where: list[str], args: list[Any]) -> None:
        vals = tuple(dict.fromkeys(values))
        if not vals:
            return
        where.append(f"{column} IN ({','.join('?' for _ in vals)})")
        args.extend(vals)

    def _known_candidates(self, domains: tuple[str, ...], limit: int) -> list[sqlite3.Row]:
        where = ["status='CURRENT'", "epistemic='KNOWN'"]
        args: list[Any] = []
        self._where_in("domain", domains, where, args)
        sql = (
            "SELECT * FROM pulse_active_field WHERE " + " AND ".join(where) +
            " ORDER BY base_score DESC,domain COLLATE BINARY,k COLLATE BINARY,semantic_hash COLLATE BINARY LIMIT ?"
        )
        args.append(limit)
        return list(self.con.execute(sql, args))

    def _rows_for_refs(self, refs: Iterable[str], domains: tuple[str, ...]) -> list[sqlite3.Row]:
        pairs = []
        allowed = set(domains)
        for ref in refs:
            if ":" not in ref:
                continue
            domain, key = ref.split(":", 1)
            if allowed and domain not in allowed:
                continue
            pairs.append((domain, key))
        out = []
        for domain, key in pairs:
            row = self.con.execute(
                """SELECT * FROM pulse_active_field
                   WHERE domain=? AND k=? AND status='CURRENT' AND epistemic='KNOWN'""",
                (domain, key),
            ).fetchone()
            if row is not None:
                out.append(row)
        return out

    def _count_epi(self, domains: tuple[str, ...], epistemic: str) -> int:
        where = ["status='CURRENT'", "epistemic=?"]
        args: list[Any] = [epistemic]
        self._where_in("domain", domains, where, args)
        return int(
            self.con.execute(
                "SELECT COUNT(*) FROM pulse_active_field WHERE " + " AND ".join(where), args
            ).fetchone()[0]
        )

    def select(
        self,
        *,
        source_domains: tuple[str, ...],
        basis_epoch: int,
        max_candidates: int,
        max_focus: int,
        reentry_mode: str = "NO_REENTRY",
        previous_focus_refs: tuple[str, ...] = (),
        shuffle_salt: str | None = None,
        now: str = "SELECT",
    ) -> ActiveFieldSelection:
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"active-field basis {basis_epoch}!={self.ledger.epoch}")
        if not source_domains:
            raise ValueError("source_domains required")
        if max_candidates <= 0 or max_candidates > 512:
            raise ValueError("max_candidates out of bounds")
        if max_focus <= 0 or max_focus > min(64, max_candidates):
            raise ValueError("max_focus out of bounds")
        mode = reentry_mode.upper()
        if mode not in {"TRUTHFUL", "NO_REENTRY", "SHUFFLED_CONTROL", "PROVENANCE_BROKEN_CONTROL"}:
            raise ValueError(mode)

        refresh = self.refresh(now=now)
        base_rows = self._known_candidates(source_domains, max_candidates)
        rows_by_ref = {f"{r['domain']}:{r['k']}": r for r in base_rows}

        reentry_targets: set[str] = set()
        if mode == "TRUTHFUL":
            for row in self._rows_for_refs(previous_focus_refs, source_domains):
                ref = f"{row['domain']}:{row['k']}"
                rows_by_ref[ref] = row
                reentry_targets.add(ref)
        elif mode == "SHUFFLED_CONTROL" and previous_focus_refs:
            # Use the same candidate universe as the base projection, then deterministically
            # break identity while preserving the number of boosted refs.
            salt = shuffle_salt or h({"control": "SHUFFLED", "basis": basis_epoch})
            shuffled = sorted(rows_by_ref, key=lambda ref: h({"salt": salt, "ref": ref}))
            reentry_targets = set(shuffled[: min(len(previous_focus_refs), len(shuffled))])

        ranked = []
        for ref, row in rows_by_ref.items():
            boost = REENTRY_BOOST if ref in reentry_targets else 0.0
            ranked.append((float(row["base_score"]) + boost, ref, row))
        ranked.sort(key=lambda x: (-x[0], x[1], str(x[2]["semantic_hash"])))
        candidate_ranked = ranked[:max_candidates]
        focus = candidate_ranked[:max_focus]
        focus_refs = tuple(x[1] for x in focus)
        candidate_refs = tuple(x[1] for x in candidate_ranked)
        conflicts = self._count_epi(source_domains, "CONFLICT")
        unknown = self._count_epi(source_domains, "UNKNOWN")
        body = {
            "projection": PROJECTION_VERSION,
            "basis_epoch": basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "source_domains": list(source_domains),
            "reentry_mode": mode,
            "candidate_refs": list(candidate_refs),
            "focus_refs": list(focus_refs),
            "conflicts_present": conflicts,
            "unknown_present": unknown,
            "projection_last_event_seq": int(self._meta()["last_event_seq"]),
            "refresh_mode": refresh["mode"],
        }
        return ActiveFieldSelection(
            basis_epoch=basis_epoch,
            semantic_state_hash=self.ledger.semantic_state_hash,
            focus_refs=focus_refs,
            candidate_refs=candidate_refs,
            conflicts_present=conflicts,
            unknown_present=unknown,
            projection_last_event_seq=body["projection_last_event_seq"],
            refresh_mode=str(refresh["mode"]),
            selection_hash=h(body),
        )

    def verify_projection(self) -> dict[str, Any]:
        """Exact differential check against authoritative current state."""
        mismatches = []
        state_rows = list(
            self.con.execute(
                "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash FROM state ORDER BY domain,k"
            )
        )
        projection = {
            (r["domain"], r["k"]): r
            for r in self.con.execute("SELECT * FROM pulse_active_field ORDER BY domain,k")
        }
        if len(state_rows) != len(projection):
            mismatches.append({"kind": "ROW_COUNT", "state": len(state_rows), "projection": len(projection)})
        for row in state_rows:
            key = (row["domain"], row["k"])
            projected = projection.get(key)
            if projected is None:
                mismatches.append({"kind": "MISSING", "ref": f"{key[0]}:{key[1]}"})
                continue
            value = self._decode_value(row["value_json"])
            score, _ = signal_score(value)
            if (
                projected["semantic_hash"] != row["semantic_hash"]
                or projected["epistemic"] != row["epistemic"]
                or projected["status"] != row["status"]
                or int(projected["domain_epoch"]) != int(row["domain_epoch"])
                or abs(float(projected["base_score"]) - score) > 1e-12
            ):
                mismatches.append({"kind": "DIVERGENCE", "ref": f"{key[0]}:{key[1]}"})
        return {
            "pass": not mismatches,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches[:32],
            "state_rows": len(state_rows),
            "projection_rows": len(projection),
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "authority": "DIFFERENTIAL_VERIFICATION_ONLY",
        }
