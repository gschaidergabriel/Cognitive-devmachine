from __future__ import annotations

"""Adaptive physical rank path V4 for FRANK Database Pulse candidate generation.

Semantic rule: candidate ordering is always the same deterministic SCORE_EXPR over the
AUTHORITATIVE StateLedger `state` table before the candidate LIMIT. A physical expression
index is only an acceleration. Missing/sparse lifetime history must not force a cold index
build into a cognition Pulse: the online path remains correct and fail-available.

Compile admission reuses U16 economics plus the Pulse-informed conservative horizon estimator.
The controller has performance-routing authority only; it never decides semantic truth or
effect authority.
"""

from dataclasses import dataclass
from typing import Any, Iterable

from research_entity.harness.reference.state_ledger import StaleEpoch, h
from research_entity.runtime.database_pulse_rank_index_v3 import (
    AuthoritativeRankIndexV3,
    INDEX_NAME,
    REENTRY_BOOST,
    SCORE_EXPR,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import (
    EpochReadLifetime,
    HorizonEstimate,
    decide_compile_from_pulse_history,
)


IMPLEMENTATION_ID = "PULSE_ADAPTIVE_AUTHORITATIVE_RANK_PATH_V4"


@dataclass(frozen=True)
class AdaptiveRankSelection:
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
    physical_mode: str
    index_present_before: bool
    index_present_after: bool
    horizon_status: str
    horizon_reads_lower_bound: float
    compile_reason: str
    guarded_break_even_reads: float | None
    authority: str = "PERFORMANCE_ROUTING_ONLY_CONTEXT_NO_EFFECT_AUTHORITY"


class AdaptiveAuthoritativeRankPathV4:
    def __init__(self, ledger):
        self.ledger = ledger
        self.con = ledger.conn
        self.v3 = AuthoritativeRankIndexV3(ledger)

    def index_exists(self) -> bool:
        return self.con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (INDEX_NAME,)
        ).fetchone() is not None

    @staticmethod
    def _domain_clause(domains: tuple[str, ...]) -> tuple[str, list[Any]]:
        ds = tuple(dict.fromkeys(domains))
        if not ds:
            raise ValueError("source_domains required")
        return f"domain IN ({','.join('?' for _ in ds)})", list(ds)

    def _count(self, domains: tuple[str, ...], epistemic: str) -> int:
        clause, args = self._domain_clause(domains)
        return int(self.con.execute(
            f"SELECT COUNT(*) FROM state WHERE status='CURRENT' AND epistemic=? AND {clause}",
            [epistemic, *args],
        ).fetchone()[0])

    def _online_rows(self, domains: tuple[str, ...], limit: int):
        clause, args = self._domain_clause(domains)
        sql = f"""SELECT domain,k,value_json,domain_epoch,semantic_hash,{SCORE_EXPR} AS score
                  FROM state
                  WHERE status='CURRENT' AND epistemic='KNOWN' AND {clause}
                  ORDER BY {SCORE_EXPR} DESC,
                           domain COLLATE BINARY,k COLLATE BINARY,semantic_hash COLLATE BINARY
                  LIMIT ?"""
        final_args = [*args, limit]
        plan = tuple(str(r[3]) for r in self.con.execute("EXPLAIN QUERY PLAN " + sql, final_args))
        return list(self.con.execute(sql, final_args)), plan

    def _row_by_ref(self, ref: str):
        if ":" not in ref:
            return None
        domain, key = ref.split(":", 1)
        return self.con.execute(
            f"""SELECT domain,k,value_json,domain_epoch,semantic_hash,{SCORE_EXPR} AS score
                FROM state WHERE status='CURRENT' AND epistemic='KNOWN' AND domain=? AND k=?""",
            (domain, key),
        ).fetchone()

    def _rank_rows(
        self,
        *,
        rows,
        domains: tuple[str, ...],
        max_candidates: int,
        max_focus: int,
        reentry_mode: str,
        previous_focus_refs: tuple[str, ...],
        shuffle_salt: str | None,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[float, ...]]:
        mode = reentry_mode.upper()
        by_ref = {f"{r['domain']}:{r['k']}": r for r in rows}
        reentry_targets: set[str] = set()
        if mode == "TRUTHFUL":
            allowed = set(domains)
            for ref in previous_focus_refs:
                if ":" not in ref or ref.split(":", 1)[0] not in allowed:
                    continue
                row = self._row_by_ref(ref)
                if row is not None:
                    by_ref[ref] = row
                    reentry_targets.add(ref)
        elif mode == "SHUFFLED_CONTROL" and previous_focus_refs:
            salt = shuffle_salt or h({"control": "SHUFFLED", "basis": self.ledger.epoch})
            shuffled = sorted(by_ref, key=lambda ref: h({"salt": salt, "ref": ref}))
            reentry_targets = set(shuffled[: min(len(previous_focus_refs), len(shuffled))])

        ranked = []
        for ref, row in by_ref.items():
            score = float(row["score"]) + (REENTRY_BOOST if ref in reentry_targets else 0.0)
            ranked.append((score, ref, str(row["semantic_hash"])))
        ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
        ranked = ranked[:max_candidates]
        candidates = tuple(x[1] for x in ranked)
        return candidates, candidates[:max_focus], tuple(round(float(x[0]), 8) for x in ranked)

    def select(
        self,
        *,
        source_domains: tuple[str, ...],
        basis_epoch: int,
        max_candidates: int,
        max_focus: int,
        economics_without_horizon: CompileEconomics,
        pulse_history: Iterable[EpochReadLifetime],
        reentry_mode: str = "NO_REENTRY",
        previous_focus_refs: tuple[str, ...] = (),
        shuffle_salt: str | None = None,
        **horizon_kwargs,
    ) -> AdaptiveRankSelection:
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"adaptive-rank basis {basis_epoch}!={self.ledger.epoch}")
        if not (1 <= max_candidates <= 512):
            raise ValueError("max_candidates out of bounds")
        if not (1 <= max_focus <= min(64, max_candidates)):
            raise ValueError("max_focus out of bounds")
        mode = reentry_mode.upper()
        if mode not in {"TRUTHFUL", "NO_REENTRY", "SHUFFLED_CONTROL", "PROVENANCE_BROKEN_CONTROL"}:
            raise ValueError(mode)
        domains = tuple(dict.fromkeys(source_domains))
        if not domains:
            raise ValueError("source_domains required")

        root_before = (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash)
        before = self.index_exists()
        horizon, decision = decide_compile_from_pulse_history(
            economics_without_horizon, list(pulse_history), **horizon_kwargs
        )

        physical_mode = "ONLINE_NO_COMPILE"
        if decision.mode == "COMPILE":
            try:
                self.v3.ensure_index()
                physical_mode = "COMPILED_INDEX"
            except Exception:
                # Optimization failure must not destroy the already-correct online semantic path.
                physical_mode = "ONLINE_COMPILE_FAILED_FALLBACK"
        after = self.index_exists()

        # Intentionally do not use INDEXED BY here. If the index exists, SQLite may select it;
        # if it does not, the same SQL remains semantically correct by sorting online.
        rows, plan = self._online_rows(domains, max_candidates)
        candidate_refs, focus_refs, scores = self._rank_rows(
            rows=rows,
            domains=domains,
            max_candidates=max_candidates,
            max_focus=max_focus,
            reentry_mode=mode,
            previous_focus_refs=previous_focus_refs,
            shuffle_salt=shuffle_salt,
        )
        universe = self._count(domains, "KNOWN")
        conflicts = self._count(domains, "CONFLICT")
        unknown = self._count(domains, "UNKNOWN")
        if root_before != (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash):
            raise AssertionError("adaptive physical rank route mutated semantic ledger roots")

        body = {
            "implementation": IMPLEMENTATION_ID,
            "basis_epoch": basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "domains": list(domains),
            "reentry_mode": mode,
            "candidate_refs": list(candidate_refs),
            "candidate_scores": list(scores),
            "focus_refs": list(focus_refs),
            "candidate_universe_count": universe,
            "query_truncated": universe > len(candidate_refs),
            "physical_mode": physical_mode,
            "index_present_before": before,
            "index_present_after": after,
            "horizon_status": horizon.status,
            "horizon_reads_lower_bound": horizon.expected_reads_lower_bound,
            "compile_reason": decision.reason,
            "guarded_break_even_reads": decision.guarded_break_even_reads,
        }
        return AdaptiveRankSelection(
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
            physical_mode=physical_mode,
            index_present_before=before,
            index_present_after=after,
            horizon_status=horizon.status,
            horizon_reads_lower_bound=horizon.expected_reads_lower_bound,
            compile_reason=decision.reason,
            guarded_break_even_reads=decision.guarded_break_even_reads,
        )
