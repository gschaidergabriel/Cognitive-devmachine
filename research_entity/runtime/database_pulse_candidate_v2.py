from __future__ import annotations

"""Database Pulse candidate v2: dual-clock, delta-first, bounded cyclic census.

This research candidate fuses the strongest properties of database_pulse_candidate_v1
with the independently-developed delta/dual-clock lane:

FAST TIMESCALE
    Consume only semantic events since the previous Pulse receipt, then re-evaluate the
    changed refs plus carried unresolved/focus refs.

SLOW TIMESCALE
    Periodically perform one bounded keyset-paginated census page over admitted source
    domains.  The cursor advances and wraps, so a large state space is eventually exposed
    without a global scan on every Pulse.

DUAL CLOCK
    StateLedger semantic_epoch advances only for admitted semantic changes.  pulse_sequence
    advances for completed endogenous Pulse executions.  Pulse execution receipts are
    hash-chained in the same SQLite/UnifiedDB physical file but outside canonical semantic
    state, so an idle Pulse does not invalidate unrelated semantic QueryReceipts.

BOUNDARIES
    UnifiedDB/StateLedger remains semantic authority.  Activation and model candidates are
    context only.  This runtime exposes no tool/effect API.  Optional model output remains
    UNKNOWN execution context until separately admitted by an external authority path.

This is a research/runtime candidate, not a promoted FRANK Harness component.
"""

from dataclasses import asdict, dataclass
import json
import time
from typing import Any, Callable, Iterable

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, cjson, h
from research_entity.runtime.database_pulse_candidate_v1 import (
    DatabasePulseRuntime,
    PULSE_CONTRACT,
    REENTRY_MODES,
    PulseControlError,
    PulseIntegrityError,
)


IMPLEMENTATION_ID = "database_pulse_candidate_v2"
PULSE_JOURNAL_GENESIS = h({"database_pulse_v2": "execution_journal_genesis"})


class PulseV2Error(RuntimeError):
    pass


class PulseV2JournalCorrupt(PulseV2Error):
    pass


class PulseV2ConcurrentAdvance(PulseV2Error):
    pass


@dataclass(frozen=True)
class PulseSpecV2:
    pulse_id: str
    basis_epoch: int
    source_domains: tuple[str, ...] = (
        "self", "world", "memory", "goal", "task", "semantic", "capability", "percept"
    )
    max_candidates: int = 128
    max_focus: int = 12
    max_carry: int = 32
    refresh_every_pulses: int = 32
    max_event_scan: int = 4096
    reentry_mode: str = "TRUTHFUL"
    purpose: str = "ENDOGENOUS_DATABASE_PULSE_V2"


@dataclass(frozen=True)
class PulseReceiptV2:
    status: str
    pulse_id: str
    pulse_sequence: int
    basis_epoch: int
    semantic_state_hash: str
    source_event_seq: int
    focus_refs: tuple[str, ...]
    carry_refs: tuple[str, ...]
    scan_refs: tuple[str, ...]
    changed_refs: tuple[str, ...]
    assembly_hash: str
    conflicts_present: int
    unknown_present: int
    pulse_state_transition_count: int
    semantic_state_transition_count: int
    graph_change_count: int
    hypothesis_count: int
    memory_update_observed_count: int
    reentry_count: int
    model_call_count: int
    tool_call_count: int
    effect_count: int
    receipt_hash: str
    pulse_chain_hash: str
    authority: str = "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY"


PULSE_V2_SCHEMA = """
CREATE TABLE IF NOT EXISTS database_pulse_v2_receipts(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  pulse_id TEXT UNIQUE NOT NULL,
  idem TEXT UNIQUE NOT NULL,
  pulse_sequence INTEGER UNIQUE NOT NULL,
  basis_epoch INTEGER NOT NULL,
  semantic_state_hash TEXT NOT NULL,
  source_event_seq INTEGER NOT NULL,
  receipt_json TEXT NOT NULL,
  receipt_hash TEXT NOT NULL,
  prev_pulse_chain_hash TEXT NOT NULL,
  pulse_chain_hash TEXT NOT NULL,
  committed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_database_pulse_v2_basis
  ON database_pulse_v2_receipts(basis_epoch,pulse_sequence);
"""


class PulseExecutionJournalV2:
    """Execution receipt chain that does not alter StateLedger semantic state."""

    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self.ledger.conn.executescript(PULSE_V2_SCHEMA)
        self.ledger.conn.commit()

    @staticmethod
    def _decode(row) -> dict[str, Any]:
        try:
            body = json.loads(row["receipt_json"])
        except Exception as exc:
            raise PulseV2JournalCorrupt("receipt JSON unreadable") from exc
        if not isinstance(body, dict):
            raise PulseV2JournalCorrupt("receipt body must be object")
        return body

    def _validate_row(self, row, *, expected_prev: str | None = None) -> dict[str, Any]:
        body = self._decode(row)
        receipt_hash = h(body)
        if receipt_hash != row["receipt_hash"]:
            raise PulseV2JournalCorrupt("receipt hash mismatch")
        checks = {
            "pulse_id": row["pulse_id"],
            "pulse_sequence": int(row["pulse_sequence"]),
            "basis_epoch": int(row["basis_epoch"]),
            "semantic_state_hash": row["semantic_state_hash"],
            "source_event_seq": int(row["source_event_seq"]),
        }
        for key, expected in checks.items():
            if body.get(key) != expected:
                raise PulseV2JournalCorrupt(f"receipt column/body mismatch: {key}")
        prev = str(row["prev_pulse_chain_hash"])
        if expected_prev is not None and prev != expected_prev:
            raise PulseV2JournalCorrupt("pulse chain predecessor mismatch")
        chain = h({
            "prev": prev,
            "receipt_hash": receipt_hash,
            "pulse_sequence": int(row["pulse_sequence"]),
            "basis_epoch": int(row["basis_epoch"]),
            "semantic_state_hash": row["semantic_state_hash"],
            "source_event_seq": int(row["source_event_seq"]),
        })
        if chain != row["pulse_chain_hash"]:
            raise PulseV2JournalCorrupt("pulse chain hash mismatch")
        return body

    def existing(self, pulse_id: str) -> dict[str, Any] | None:
        row = self.ledger.conn.execute(
            "SELECT * FROM database_pulse_v2_receipts WHERE pulse_id=?",
            (pulse_id,),
        ).fetchone()
        if row is None:
            return None
        body = self._validate_row(row)
        return {
            **body,
            "receipt_hash": row["receipt_hash"],
            "pulse_chain_hash": row["pulse_chain_hash"],
            "commit_status": "ALREADY_RECORDED",
        }

    def head(self) -> dict[str, Any] | None:
        rows = self.ledger.conn.execute(
            "SELECT * FROM database_pulse_v2_receipts ORDER BY seq DESC LIMIT 2"
        ).fetchall()
        if not rows:
            return None
        latest = rows[0]
        if len(rows) == 1:
            if int(latest["pulse_sequence"]) != 1:
                raise PulseV2JournalCorrupt("first pulse sequence must equal one")
            expected_prev = PULSE_JOURNAL_GENESIS
        else:
            previous = rows[1]
            previous_body = self._validate_row(previous)
            if int(latest["pulse_sequence"]) != int(previous["pulse_sequence"]) + 1:
                raise PulseV2JournalCorrupt("pulse sequence discontinuity")
            expected_prev = str(previous["pulse_chain_hash"])
            if previous_body.get("pulse_sequence") != int(previous["pulse_sequence"]):
                raise PulseV2JournalCorrupt("previous pulse sequence corrupt")
        body = self._validate_row(latest, expected_prev=expected_prev)
        body_with_hash = dict(body)
        body_with_hash["receipt_hash"] = latest["receipt_hash"]
        return {
            "body": body_with_hash,
            "receipt_hash": latest["receipt_hash"],
            "pulse_chain_hash": latest["pulse_chain_hash"],
        }

    def verify_all(self) -> dict[str, Any]:
        rows = self.ledger.conn.execute(
            "SELECT * FROM database_pulse_v2_receipts ORDER BY seq"
        ).fetchall()
        prev = PULSE_JOURNAL_GENESIS
        expected_seq = 0
        for row in rows:
            expected_seq += 1
            if int(row["pulse_sequence"]) != expected_seq:
                raise PulseV2JournalCorrupt("pulse sequence corrupt")
            self._validate_row(row, expected_prev=prev)
            prev = str(row["pulse_chain_hash"])
        return {"valid": True, "pulse_sequence": expected_seq, "pulse_chain_hash": prev}

    def export_receipts(self) -> list[dict[str, Any]]:
        self.verify_all()
        out: list[dict[str, Any]] = []
        for row in self.ledger.conn.execute(
            "SELECT * FROM database_pulse_v2_receipts ORDER BY seq"
        ):
            out.append({
                "pulse_id": row["pulse_id"],
                "pulse_sequence": int(row["pulse_sequence"]),
                "basis_epoch": int(row["basis_epoch"]),
                "semantic_state_hash": row["semantic_state_hash"],
                "source_event_seq": int(row["source_event_seq"]),
                "receipt_hash": row["receipt_hash"],
                "pulse_chain_hash": row["pulse_chain_hash"],
                "committed_at": row["committed_at"],
            })
        return out

    def append(self, body: dict[str, Any], *, expected_prev_chain: str,
               committed_at: str | None = None) -> dict[str, str]:
        receipt_hash = h(body)
        pulse_id = str(body["pulse_id"])
        idem = f"database-pulse-v2:{pulse_id}"
        pulse_sequence = int(body["pulse_sequence"])
        basis_epoch = int(body["basis_epoch"])
        semantic_hash = str(body["semantic_state_hash"])
        source_event_seq = int(body["source_event_seq"])

        self.ledger.conn.execute("BEGIN IMMEDIATE")
        try:
            old = self.ledger.conn.execute(
                "SELECT * FROM database_pulse_v2_receipts WHERE pulse_id=? OR idem=? LIMIT 1",
                (pulse_id, idem),
            ).fetchone()
            if old is not None:
                old_body = self._validate_row(old)
                if h(old_body) != receipt_hash:
                    raise PulseV2ConcurrentAdvance("pulse idempotency payload conflict")
                self.ledger.conn.rollback()
                return {
                    "status": "ALREADY_RECORDED",
                    "receipt_hash": str(old["receipt_hash"]),
                    "pulse_chain_hash": str(old["pulse_chain_hash"]),
                }

            if self.ledger.epoch != basis_epoch:
                raise StaleEpoch(f"pulse receipt basis {basis_epoch}!={self.ledger.epoch}")
            if self.ledger.semantic_state_hash != semantic_hash:
                raise StaleEpoch("semantic state changed before Pulse receipt commit")

            previous = self.ledger.conn.execute(
                "SELECT pulse_sequence,pulse_chain_hash FROM database_pulse_v2_receipts "
                "ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            actual_prev_chain = (
                PULSE_JOURNAL_GENESIS if previous is None else str(previous["pulse_chain_hash"])
            )
            actual_prev_seq = 0 if previous is None else int(previous["pulse_sequence"])
            if actual_prev_chain != expected_prev_chain or pulse_sequence != actual_prev_seq + 1:
                raise PulseV2ConcurrentAdvance("Pulse journal advanced concurrently")

            chain = h({
                "prev": actual_prev_chain,
                "receipt_hash": receipt_hash,
                "pulse_sequence": pulse_sequence,
                "basis_epoch": basis_epoch,
                "semantic_state_hash": semantic_hash,
                "source_event_seq": source_event_seq,
            })
            ts = committed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.ledger.conn.execute(
                "INSERT INTO database_pulse_v2_receipts("
                "pulse_id,idem,pulse_sequence,basis_epoch,semantic_state_hash,source_event_seq,"
                "receipt_json,receipt_hash,prev_pulse_chain_hash,pulse_chain_hash,committed_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    pulse_id,
                    idem,
                    pulse_sequence,
                    basis_epoch,
                    semantic_hash,
                    source_event_seq,
                    json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    receipt_hash,
                    actual_prev_chain,
                    chain,
                    ts,
                ),
            )
            self.ledger.conn.commit()
            return {"status": "RECORDED", "receipt_hash": receipt_hash, "pulse_chain_hash": chain}
        except Exception:
            self.ledger.conn.rollback()
            raise


class DatabasePulseRuntimeV2(DatabasePulseRuntime):
    """v1 safety/control semantics + delta-first, dual-clock execution semantics."""

    MAX_CANDIDATES_HARD = 512
    MAX_FOCUS_HARD = 64
    MAX_CARRY_HARD = 256
    MAX_EVENT_SCAN_HARD = 65536
    MAX_MODEL_OUTPUT_BYTES = 65536
    DELTA_BOOST = 0.35

    def __init__(self, ledger: StateLedger):
        super().__init__(ledger)
        self.journal = PulseExecutionJournalV2(ledger)

    @staticmethod
    def _row_dict(row) -> dict[str, Any]:
        return {
            "domain": str(row["domain"]),
            "key": str(row["k"]),
            "value": json.loads(row["value_json"]) if row["value_json"] is not None else None,
            "epistemic": str(row["epistemic"]),
            "status": str(row["status"]),
            "domain_epoch": int(row["domain_epoch"]),
            "semantic_hash": str(row["semantic_hash"]),
        }

    @staticmethod
    def _ref(row: dict[str, Any]) -> str:
        return f"{row['domain']}:{row['key']}"

    def _event_seq(self) -> int:
        return int(self.ledger.conn.execute(
            "SELECT COALESCE(MAX(seq),0) FROM events"
        ).fetchone()[0])

    def _changed_refs(
        self,
        *,
        after_seq: int,
        through_seq: int,
        source_domains: tuple[str, ...],
        max_event_scan: int,
    ) -> tuple[list[str], int, int]:
        rows = self.ledger.conn.execute(
            "SELECT seq,ops_json FROM events WHERE seq>? AND seq<=? ORDER BY seq LIMIT ?",
            (after_seq, through_seq, max_event_scan + 1),
        ).fetchall()
        if len(rows) > max_event_scan:
            raise PulseV2Error("event scan budget exceeded; bounded refresh/recovery required")
        allowed = set(source_domains)
        refs: list[str] = []
        relevant_events = 0
        for event in rows:
            event_relevant = False
            try:
                ops = json.loads(event["ops_json"])
            except Exception as exc:
                raise PulseIntegrityError("semantic event ops unreadable") from exc
            for op in ops:
                domain = str(op.get("domain") or "")
                key = str(op.get("key") or "")
                if domain not in allowed or not key:
                    continue
                event_relevant = True
                ref = f"{domain}:{key}"
                if ref not in refs:
                    refs.append(ref)
            relevant_events += int(event_relevant)
        return refs, relevant_events, len(rows)

    def _fetch_refs(self, refs: Iterable[str], source_domains: tuple[str, ...]) -> list[dict[str, Any]]:
        allowed = set(source_domains)
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for ref in refs:
            if ref in seen or ":" not in ref:
                continue
            domain, key = ref.split(":", 1)
            if domain not in allowed:
                continue
            row = self.ledger.conn.execute(
                "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash "
                "FROM state WHERE domain=? AND k=?",
                (domain, key),
            ).fetchone()
            if row is not None:
                out.append(self._row_dict(row))
                seen.add(ref)
        return out

    def _scan_page(
        self,
        *,
        source_domains: tuple[str, ...],
        after_ref: str | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        domains = tuple(dict.fromkeys(source_domains))
        marks = ",".join("?" for _ in domains)
        where = [f"domain IN ({marks})", "status='CURRENT'", "epistemic IN ('KNOWN','UNKNOWN','CONFLICT')"]
        args: list[Any] = list(domains)
        if after_ref and ":" in after_ref:
            after_domain, after_key = after_ref.split(":", 1)
            where.append("(domain>? OR (domain=? AND k>?))")
            args.extend([after_domain, after_domain, after_key])
        sql = (
            "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash FROM state WHERE "
            + " AND ".join(where)
            + " ORDER BY domain COLLATE BINARY,k COLLATE BINARY LIMIT ?"
        )
        args.append(limit)
        rows = [self._row_dict(r) for r in self.ledger.conn.execute(sql, args).fetchall()]
        wrapped = False
        if len(rows) < limit and after_ref:
            wrapped = True
            need = limit - len(rows)
            wrap_sql = (
                "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash "
                f"FROM state WHERE domain IN ({marks}) AND status='CURRENT' "
                "AND epistemic IN ('KNOWN','UNKNOWN','CONFLICT') "
                "ORDER BY domain COLLATE BINARY,k COLLATE BINARY LIMIT ?"
            )
            existing = {self._ref(r) for r in rows}
            for raw in self.ledger.conn.execute(wrap_sql, [*domains, need + len(existing)]).fetchall():
                row = self._row_dict(raw)
                if self._ref(row) in existing:
                    continue
                rows.append(row)
                existing.add(self._ref(row))
                if len(rows) >= limit:
                    break
        cursor = self._ref(rows[-1]) if rows else after_ref
        return rows, cursor, wrapped

    @staticmethod
    def _merge_rows(*groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        order: list[str] = []
        for group in groups:
            for row in group:
                ref = f"{row['domain']}:{row['key']}"
                if ref not in merged:
                    order.append(ref)
                merged[ref] = row
        return [merged[ref] for ref in order]

    @staticmethod
    def _receipt_from_body(body: dict[str, Any], *, receipt_hash: str,
                           chain_hash: str, status: str) -> PulseReceiptV2:
        obs = body["observables"]
        return PulseReceiptV2(
            status=status,
            pulse_id=str(body["pulse_id"]),
            pulse_sequence=int(body["pulse_sequence"]),
            basis_epoch=int(body["basis_epoch"]),
            semantic_state_hash=str(body["semantic_state_hash"]),
            source_event_seq=int(body["source_event_seq"]),
            focus_refs=tuple(map(str, body.get("focus_refs", ()))),
            carry_refs=tuple(map(str, body.get("carry_refs", ()))),
            scan_refs=tuple(map(str, body.get("scan_refs", ()))),
            changed_refs=tuple(map(str, body.get("changed_refs", ()))),
            assembly_hash=str(body["assembly_hash"]),
            conflicts_present=int(body["conflicts_present"]),
            unknown_present=int(body["unknown_present"]),
            pulse_state_transition_count=int(obs["pulse_state_transition_count"]),
            semantic_state_transition_count=int(obs["semantic_state_transition_count"]),
            graph_change_count=int(obs["graph_change_count"]),
            hypothesis_count=int(obs["hypothesis_count"]),
            memory_update_observed_count=int(obs["memory_update_observed_count"]),
            reentry_count=int(obs["reentry_count"]),
            model_call_count=int(obs["model_call_count"]),
            tool_call_count=int(obs["tool_call_count"]),
            effect_count=int(obs["effect_count"]),
            receipt_hash=receipt_hash,
            pulse_chain_hash=chain_hash,
        )

    def run_pulse_v2(
        self,
        spec: PulseSpecV2,
        *,
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        committed_at: str | None = None,
    ) -> PulseReceiptV2:
        if not spec.pulse_id.strip():
            raise ValueError("pulse_id required")
        mode = spec.reentry_mode.upper()
        if mode not in REENTRY_MODES:
            raise ValueError(f"unsupported reentry mode: {spec.reentry_mode}")
        domains = tuple(dict.fromkeys(spec.source_domains))
        if not domains or any(d in {"pulse", "pulse_control"} for d in domains):
            raise ValueError("source_domains must be explicit and exclude pulse control/output domains")
        if not (1 <= spec.max_candidates <= self.MAX_CANDIDATES_HARD):
            raise ValueError("max_candidates out of bounds")
        if not (1 <= spec.max_focus <= min(spec.max_candidates, self.MAX_FOCUS_HARD)):
            raise ValueError("max_focus out of bounds")
        if not (1 <= spec.max_carry <= self.MAX_CARRY_HARD):
            raise ValueError("max_carry out of bounds")
        if not (1 <= spec.refresh_every_pulses <= 4096):
            raise ValueError("refresh_every_pulses out of bounds")
        if not (1 <= spec.max_event_scan <= self.MAX_EVENT_SCAN_HARD):
            raise ValueError("max_event_scan out of bounds")

        existing = self.journal.existing(spec.pulse_id)
        if existing is not None:
            return self._receipt_from_body(
                existing,
                receipt_hash=str(existing["receipt_hash"]),
                chain_hash=str(existing["pulse_chain_hash"]),
                status="ALREADY_RECORDED",
            )

        current_schema = self.validate_integrity(full=False)
        if current_schema != self.schema_fingerprint:
            raise PulseIntegrityError("runtime schema changed after initialization")
        enabled, scheduler_hash = self._scheduler()
        if not enabled:
            return PulseReceiptV2(
                status="PAUSED",
                pulse_id=spec.pulse_id,
                pulse_sequence=0,
                basis_epoch=self.ledger.epoch,
                semantic_state_hash=self.ledger.semantic_state_hash,
                source_event_seq=self._event_seq(),
                focus_refs=(), carry_refs=(), scan_refs=(), changed_refs=(),
                assembly_hash=h({"status":"PAUSED","scheduler_hash":scheduler_hash}),
                conflicts_present=0, unknown_present=0,
                pulse_state_transition_count=0, semantic_state_transition_count=0,
                graph_change_count=0, hypothesis_count=0,
                memory_update_observed_count=0, reentry_count=0,
                model_call_count=0, tool_call_count=0, effect_count=0,
                receipt_hash=h({"pulse_id":spec.pulse_id,"status":"PAUSED","scheduler_hash":scheduler_hash}),
                pulse_chain_hash=self.journal.verify_all()["pulse_chain_hash"],
            )
        if int(spec.basis_epoch) != self.ledger.epoch:
            raise StaleEpoch(f"pulse basis {spec.basis_epoch}!={self.ledger.epoch}")

        semantic_hash = self.ledger.semantic_state_hash
        trace_root_before = self.ledger.trace_root_hash
        head = self.journal.head()
        pulse_sequence = 1 if head is None else int(head["body"]["pulse_sequence"]) + 1
        previous = None if head is None else dict(head["body"])
        previous_seq = 0 if previous is None else int(previous["source_event_seq"])
        current_event_seq = self._event_seq()
        changed_refs, relevant_event_count, scanned_event_count = self._changed_refs(
            after_seq=previous_seq,
            through_seq=current_event_seq,
            source_domains=domains,
            max_event_scan=spec.max_event_scan,
        ) if previous is not None else ([], 0, 0)

        previous_focus = [] if previous is None else list(map(str, previous.get("focus_refs", ())))
        previous_carry = [] if previous is None else list(map(str, previous.get("carry_refs", ())))
        scan_cursor = None if previous is None else previous.get("scan_cursor")
        refresh_due = previous is None or pulse_sequence % spec.refresh_every_pulses == 0
        scan_rows: list[dict[str, Any]] = []
        scan_refs: list[str] = []
        scan_wrapped = False
        if refresh_due:
            scan_rows, scan_cursor, scan_wrapped = self._scan_page(
                source_domains=domains,
                after_ref=str(scan_cursor) if scan_cursor else None,
                limit=spec.max_candidates,
            )
            scan_refs = [self._ref(r) for r in scan_rows]

        direct_rows = self._fetch_refs(
            list(dict.fromkeys(changed_refs + previous_focus + previous_carry)),
            domains,
        )
        candidates = self._merge_rows(direct_rows, scan_rows)
        conflicts = [r for r in candidates if r["status"] == "CURRENT" and r["epistemic"] == "CONFLICT"]
        unknown = [r for r in candidates if r["status"] == "CURRENT" and r["epistemic"] == "UNKNOWN"]
        admissible = [r for r in candidates if r["status"] == "CURRENT" and r["epistemic"] == "KNOWN"]
        candidate_refs = [self._ref(r) for r in admissible]
        reentry_targets = self._reentry_targets(
            mode=mode,
            previous=previous,
            candidate_refs=candidate_refs,
        )

        ranked: list[dict[str, Any]] = []
        changed_set = set(changed_refs)
        for row in admissible:
            ref = self._ref(row)
            base_score, signals = self._signal_score(row.get("value"))
            delta_boost = self.DELTA_BOOST if ref in changed_set else 0.0
            reentry_boost = self.REENTRY_BOOST if ref in reentry_targets else 0.0
            ranked.append({
                "ref": ref,
                "score": round(base_score + delta_boost + reentry_boost, 8),
                "base_score": round(base_score, 8),
                "delta_boost": delta_boost,
                "reentry_boost": reentry_boost,
                "signals": signals,
                "source_semantic_hash": row["semantic_hash"],
                "domain_epoch": row["domain_epoch"],
            })
        ranked.sort(key=lambda x: (-x["score"], x["ref"], x["source_semantic_hash"]))
        focus = ranked[: spec.max_focus]
        focus_refs = [x["ref"] for x in focus]
        carry_refs = list(dict.fromkeys(
            [self._ref(r) for r in conflicts + unknown]
        ))[: spec.max_carry]

        assembly_hash = h({
            "basis_epoch": spec.basis_epoch,
            "semantic_state_hash": semantic_hash,
            "source_event_seq": current_event_seq,
            "reentry_mode": mode,
            "changed_refs": changed_refs,
            "scan_refs": scan_refs,
            "focus": [
                {k: x[k] for k in (
                    "ref", "score", "source_semantic_hash", "domain_epoch", "delta_boost", "reentry_boost"
                )}
                for x in focus
            ],
            "carry_refs": carry_refs,
        })

        model_output = None
        model_call_delta = 0
        model_candidate = None
        if model_assistant is not None:
            context = {
                "pulse_id": spec.pulse_id,
                "pulse_sequence": pulse_sequence,
                "basis_epoch": spec.basis_epoch,
                "assembly_hash": assembly_hash,
                "focus": focus,
                "carry_refs": carry_refs,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            }
            model_output = model_assistant(context)
            encoded = cjson(model_output)
            if len(encoded.encode("utf-8")) > self.MAX_MODEL_OUTPUT_BYTES:
                raise ValueError("model candidate exceeds bounded receipt size")
            model_call_delta = 1
            model_candidate = {
                "epistemic": "UNKNOWN",
                "candidate": model_output,
                "candidate_hash": h(model_output),
                "authority": "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
            }

        truthful_reentry = int(mode == "TRUTHFUL" and bool(reentry_targets & set(focus_refs)))
        memory_updates = sum(1 for ref in changed_refs if ref.startswith("memory:"))
        obs = {
            "pulse_state_transition_count": 1,
            "semantic_state_transition_count": 0,
            "graph_change_count": 0,
            "hypothesis_count": int(model_output is not None),
            "memory_update_observed_count": memory_updates,
            "reentry_count": truthful_reentry,
            "model_call_count": model_call_delta,
            "tool_call_count": 0,
            "effect_count": 0,
        }
        cumulative = {key: 0 for key in obs}
        if previous is not None:
            prior = previous.get("cumulative_observables", {})
            if not isinstance(prior, dict):
                raise PulseV2JournalCorrupt("cumulative observables malformed")
            for key in cumulative:
                raw = prior.get(key, 0)
                if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
                    raise PulseV2JournalCorrupt(f"invalid cumulative observable {key}")
                cumulative[key] = raw
        for key, delta in obs.items():
            cumulative[key] += delta

        body: dict[str, Any] = {
            "schema_version": "2.0-research",
            "implementation": IMPLEMENTATION_ID,
            "pulse_contract": PULSE_CONTRACT,
            "pulse_id": spec.pulse_id,
            "pulse_sequence": pulse_sequence,
            "basis_epoch": spec.basis_epoch,
            "semantic_state_hash": semantic_hash,
            "trace_root_before": trace_root_before,
            "source_event_seq": current_event_seq,
            "previous_source_event_seq": previous_seq,
            "scanned_event_count": scanned_event_count,
            "relevant_event_count": relevant_event_count,
            "changed_refs": changed_refs,
            "refresh_due": refresh_due,
            "scan_cursor": scan_cursor,
            "scan_wrapped": scan_wrapped,
            "scan_refs": scan_refs,
            "focus_refs": focus_refs,
            "focus": focus,
            "carry_refs": carry_refs,
            "conflicts_present": len(conflicts),
            "unknown_present": len(unknown),
            "assembly_hash": assembly_hash,
            "scheduler_semantic_hash": scheduler_hash,
            "schema_fingerprint": self.schema_fingerprint,
            "reentry_mode": mode,
            "reentry_target_refs": sorted(reentry_targets),
            "model_candidate": model_candidate,
            "observables": obs,
            "cumulative_observables": cumulative,
            "authority": "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            "effect_authority": "NONE",
        }
        prev_chain = PULSE_JOURNAL_GENESIS if head is None else str(head["pulse_chain_hash"])
        commit = self.journal.append(
            body,
            expected_prev_chain=prev_chain,
            committed_at=committed_at,
        )
        if self.ledger.epoch != spec.basis_epoch:
            raise PulseV2Error("execution-only Pulse changed semantic epoch")
        if self.ledger.semantic_state_hash != semantic_hash:
            raise PulseV2Error("execution-only Pulse changed semantic state hash")
        if self.ledger.trace_root_hash != trace_root_before:
            raise PulseV2Error("execution-only Pulse changed StateLedger trace root")
        return self._receipt_from_body(
            body,
            receipt_hash=commit["receipt_hash"],
            chain_hash=commit["pulse_chain_hash"],
            status=commit["status"],
        )
