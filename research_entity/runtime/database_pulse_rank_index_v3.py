from __future__ import annotations

"""Simpler counterbaseline for FRANK Database Pulse candidate generation.

Instead of maintaining a second Active Field table, V3 asks whether SQLite can maintain the
same salience ordering as a partial expression index directly over the authoritative H1
StateLedger `state` table. The index is physical/rebuildable; StateLedger rows and semantic
roots remain the only semantic authority.

This is intentionally a falsifier for PulseActiveFieldV2. If it preserves the same bounded
selection semantics with lower build/update/read complexity, the custom projection should not
be promoted merely because it is more Clay-specific.
"""

from dataclasses import dataclass
import hashlib
from typing import Any

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, h


IMPLEMENTATION_ID = "PULSE_AUTHORITATIVE_RANK_INDEX_V3"
INDEX_NAME = "idx_state_pulse_salience_known_current_v3"
REENTRY_BOOST = 0.30

# Must be byte-for-semantics equivalent to database_pulse_candidate_v1._signal_score.
# SQLite expression-index matching is syntactic, so the exact string is reused in CREATE and
# SELECT. Bool JSON values have type true/false and therefore do not count as numeric signals.
def _term(path: str, weight: float) -> str:
    return (
        f"{weight:.2f}*CASE WHEN json_type(value_json,'$.{path}') IN ('integer','real') "
        f"THEN max(0.0,min(1.0,CAST(json_extract(value_json,'$.{path}') AS REAL))) "
        "ELSE 0.0 END"
    )


SCORE_EXPR = "(1.0+" + "+".join(
    [_term("priority", 0.40), _term("urgency", 0.25), _term("salience", 0.20), _term("novelty", 0.15)]
) + ")"


class RankIndexError(RuntimeError):
    pass


@dataclass(frozen=True)
class RankIndexSelection:
    basis_epoch: int
    semantic_state_hash: str
    candidate_refs: tuple[str, ...]
    focus_refs: tuple[str, ...]
    candidate_scores: tuple[float, ...]
    candidate_universe_count: int
    query_truncated: bool
    conflicts_present: int
    unknown_present: int
    selection_hash: str
    query_plan: tuple[str, ...]
    reentry_mode: str
    authority: str = "CONTEXT_ONLY_PHYSICAL_INDEX_NO_EFFECT_AUTHORITY"


class AuthoritativeRankIndexV3:
    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self.con = ledger.conn

    def ensure_index(self) -> None:
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
        self.con.commit()

    def drop_index(self) -> None:
        self.con.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
        self.con.commit()

    @staticmethod
    def _domain_clause(domains: tuple[str, ...]) -> tuple[str, list[Any]]:
        ds = tuple(dict.fromkeys(domains))
        if not ds:
            raise ValueError("source_domains required")
        return f"domain IN ({','.join('?' for _ in ds)})", list(ds)

    def _count(self, domains: tuple[str, ...], epistemic: str) -> int:
        clause, args = self._domain_clause(domains)
        return int(
            self.con.execute(
                f"SELECT COUNT(*) FROM state WHERE status='CURRENT' AND epistemic=? AND {clause}",
                [epistemic, *args],
            ).fetchone()[0]
        )

    def _row_by_ref(self, ref: str):
        if ":" not in ref:
            return None
        domain, key = ref.split(":", 1)
        return self.con.execute(
            f"""SELECT domain,k,value_json,domain_epoch,semantic_hash,{SCORE_EXPR} AS score
                FROM state
                WHERE status='CURRENT' AND epistemic='KNOWN' AND domain=? AND k=?""",
            (domain, key),
        ).fetchone()

    def _base_query(self, domains: tuple[str, ...], limit: int):
        clause, args = self._domain_clause(domains)
        sql = f"""SELECT domain,k,value_json,domain_epoch,semantic_hash,{SCORE_EXPR} AS score
                  FROM state INDEXED BY {INDEX_NAME}
                  WHERE status='CURRENT' AND epistemic='KNOWN' AND {clause}
                  ORDER BY {SCORE_EXPR} DESC,
                           domain COLLATE BINARY,k COLLATE BINARY,semantic_hash COLLATE BINARY
                  LIMIT ?"""
        return sql, [*args, limit]

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
    ) -> RankIndexSelection:
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"rank-index basis {basis_epoch}!={self.ledger.epoch}")
        if max_candidates <= 0 or max_candidates > 512:
            raise ValueError("max_candidates out of bounds")
        if max_focus <= 0 or max_focus > min(64, max_candidates):
            raise ValueError("max_focus out of bounds")
        mode = reentry_mode.upper()
        if mode not in {"TRUTHFUL", "NO_REENTRY", "SHUFFLED_CONTROL", "PROVENANCE_BROKEN_CONTROL"}:
            raise ValueError(mode)

        self.ensure_index()
        domains = tuple(dict.fromkeys(source_domains))
        sql, args = self._base_query(domains, max_candidates)
        plan = tuple(str(r[3]) for r in self.con.execute("EXPLAIN QUERY PLAN " + sql, args))
        rows = list(self.con.execute(sql, args))
        by_ref = {f"{r['domain']}:{r['k']}": r for r in rows}

        reentry_targets: set[str] = set()
        if mode == "TRUTHFUL":
            allowed = set(domains)
            for ref in previous_focus_refs:
                if ":" not in ref:
                    continue
                domain, _ = ref.split(":", 1)
                if domain not in allowed:
                    continue
                row = self._row_by_ref(ref)
                if row is not None:
                    by_ref[ref] = row
                    reentry_targets.add(ref)
        elif mode == "SHUFFLED_CONTROL" and previous_focus_refs:
            salt = shuffle_salt or h({"control": "SHUFFLED", "basis": basis_epoch})
            shuffled = sorted(by_ref, key=lambda ref: h({"salt": salt, "ref": ref}))
            reentry_targets = set(shuffled[: min(len(previous_focus_refs), len(shuffled))])

        ranked = []
        for ref, row in by_ref.items():
            score = float(row["score"])
            if ref in reentry_targets:
                score += REENTRY_BOOST
            ranked.append((score, ref, row))
        ranked.sort(key=lambda x: (-x[0], x[1], str(x[2]["semantic_hash"])))
        ranked = ranked[:max_candidates]
        focus = ranked[:max_focus]
        candidate_refs = tuple(x[1] for x in ranked)
        focus_refs = tuple(x[1] for x in focus)
        scores = tuple(round(float(x[0]), 8) for x in ranked)
        universe = self._count(domains, "KNOWN")
        conflicts = self._count(domains, "CONFLICT")
        unknown = self._count(domains, "UNKNOWN")
        body = {
            "implementation": IMPLEMENTATION_ID,
            "basis_epoch": basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "domains": list(domains),
            "reentry_mode": mode,
            "candidate_refs": list(candidate_refs),
            "scores": list(scores),
            "focus_refs": list(focus_refs),
            "candidate_universe_count": universe,
            "query_truncated": universe > len(candidate_refs),
            "conflicts_present": conflicts,
            "unknown_present": unknown,
        }
        return RankIndexSelection(
            basis_epoch=basis_epoch,
            semantic_state_hash=self.ledger.semantic_state_hash,
            candidate_refs=candidate_refs,
            focus_refs=focus_refs,
            candidate_scores=scores,
            candidate_universe_count=universe,
            query_truncated=universe > len(candidate_refs),
            conflicts_present=conflicts,
            unknown_present=unknown,
            selection_hash=h(body),
            query_plan=plan,
            reentry_mode=mode,
        )

    def verify_index_semantics(self, *, domains: tuple[str, ...], max_candidates: int = 512) -> dict[str, Any]:
        """Differentially compare indexed order with full authoritative Python scoring."""
        from research_entity.runtime.database_pulse_active_field_v2 import signal_score
        ds = tuple(dict.fromkeys(domains))
        clause, args = self._domain_clause(ds)
        rows = list(
            self.con.execute(
                f"""SELECT domain,k,value_json,semantic_hash FROM state
                    WHERE status='CURRENT' AND epistemic='KNOWN' AND {clause}""",
                args,
            )
        )
        import json
        expected = []
        for row in rows:
            value = json.loads(row["value_json"]) if row["value_json"] is not None else None
            score, _ = signal_score(value)
            expected.append((float(score), f"{row['domain']}:{row['k']}", str(row["semantic_hash"])))
        expected.sort(key=lambda x: (-x[0], x[1], x[2]))
        expected_refs = tuple(x[1] for x in expected[:max_candidates])
        got = self.select(
            source_domains=ds,
            basis_epoch=self.ledger.epoch,
            max_candidates=min(max_candidates, 512),
            max_focus=1,
        )
        return {
            "pass": expected_refs[:len(got.candidate_refs)] == got.candidate_refs,
            "expected_refs": expected_refs[:32],
            "actual_refs": got.candidate_refs[:32],
            "candidate_universe_count": len(expected),
            "indexed_count": len(got.candidate_refs),
            "query_plan": list(got.query_plan),
            "index_name": INDEX_NAME,
            "score_expression_sha256": hashlib.sha256(SCORE_EXPR.encode()).hexdigest(),
            "authority": "DIFFERENTIAL_VERIFICATION_ONLY",
        }
