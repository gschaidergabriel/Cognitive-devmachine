from __future__ import annotations

"""Delta-aware, zero-model reference kernel for the FRANK Database Pulse.

The Database Pulse is an endogenous state/cognition cycle over UnifiedDB.  This reference
candidate deliberately separates two clocks:

* semantic_epoch: advances only when admitted semantic state changes in StateLedger;
* pulse_count: advances when an endogenous Pulse execution completes.

Pulse execution receipts live in a hash-chained table in the *same physical UnifiedDB*
connection, but outside StateLedger's canonical semantic `state` table.  Therefore an idle
zero-model Pulse does not mutate the semantic state hash and does not invalidate unrelated
semantic QueryReceipts merely because time/pulse_count advanced.

The kernel proves the smallest useful subset of the owner-fixed Pulse contract:
- zero model/tool/effect calls are valid;
- first observation performs a bounded bootstrap census;
- later Pulses consume only semantic event deltas plus carried unresolved references;
- Pulse bookkeeping cannot self-excite semantic delta processing;
- stale/corrupt state and receipt-chain corruption fail closed;
- receipts are idempotent, hash chained, restartable and deterministically replayable.

It remains a reference harness candidate. Activation/rank never grants truth/effect authority.
"""

import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .state_ledger import StateLedger, StaleEpoch, h


class PulseStateCorrupt(RuntimeError):
    pass


class PulseConcurrentAdvance(RuntimeError):
    pass


@dataclass(frozen=True)
class PulseConfig:
    bootstrap_scan_limit: int = 4096
    max_active_refs: int = 24
    max_delta_events: int = 4096

    def validate(self) -> None:
        if self.bootstrap_scan_limit <= 0 or self.bootstrap_scan_limit > 100_000:
            raise ValueError("invalid bootstrap_scan_limit")
        if self.max_active_refs <= 0 or self.max_active_refs > 4096:
            raise ValueError("invalid max_active_refs")
        if self.max_delta_events <= 0 or self.max_delta_events > 100_000:
            raise ValueError("invalid max_delta_events")


@dataclass(frozen=True)
class ActiveRef:
    ref: str
    domain: str
    key: str
    score: float
    epistemic: str
    status: str
    changed: bool
    carried: bool
    semantic_hash: str


PULSE_SCHEMA = """
CREATE TABLE IF NOT EXISTS database_pulse_receipts(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  pulse_id TEXT UNIQUE NOT NULL,
  idem TEXT UNIQUE NOT NULL,
  pulse_count INTEGER UNIQUE NOT NULL,
  basis_epoch INTEGER NOT NULL,
  source_semantic_state_hash TEXT NOT NULL,
  receipt_json TEXT NOT NULL,
  receipt_hash TEXT NOT NULL,
  prev_pulse_chain_hash TEXT NOT NULL,
  pulse_chain_hash TEXT NOT NULL,
  committed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_database_pulse_basis
  ON database_pulse_receipts(basis_epoch,pulse_count);
"""


class PulseJournal:
    """Execution-only Pulse receipt chain co-located with the semantic StateLedger."""

    GENESIS = h({"database_pulse": "execution_receipt_genesis_v1"})

    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self.ledger.conn.executescript(PULSE_SCHEMA)
        self.ledger.conn.commit()

    @staticmethod
    def _receipt_body(row) -> dict[str, Any]:
        try:
            body = json.loads(row["receipt_json"])
        except Exception as exc:
            raise PulseStateCorrupt("invalid pulse receipt JSON") from exc
        if not isinstance(body, dict):
            raise PulseStateCorrupt("pulse receipt body is not an object")
        return body

    def _validate_row(self, row, expected_prev: str | None = None) -> dict[str, Any]:
        body = self._receipt_body(row)
        receipt_hash = h(body)
        if receipt_hash != row["receipt_hash"]:
            raise PulseStateCorrupt("pulse receipt hash mismatch")
        if body.get("receipt_hash") is not None:
            raise PulseStateCorrupt("receipt body must not self-contain receipt_hash")
        if body.get("pulse_id") != row["pulse_id"]:
            raise PulseStateCorrupt("pulse_id column/body mismatch")
        if int(body.get("pulse_count", -1)) != int(row["pulse_count"]):
            raise PulseStateCorrupt("pulse_count column/body mismatch")
        if int(body.get("basis_epoch", -1)) != int(row["basis_epoch"]):
            raise PulseStateCorrupt("basis_epoch column/body mismatch")
        if body.get("source_semantic_state_hash") != row["source_semantic_state_hash"]:
            raise PulseStateCorrupt("semantic state hash column/body mismatch")
        prev = row["prev_pulse_chain_hash"]
        if expected_prev is not None and prev != expected_prev:
            raise PulseStateCorrupt("pulse chain predecessor mismatch")
        chain = h({
            "prev": prev,
            "receipt_hash": receipt_hash,
            "pulse_count": int(row["pulse_count"]),
            "basis_epoch": int(row["basis_epoch"]),
            "source_semantic_state_hash": row["source_semantic_state_hash"],
        })
        if chain != row["pulse_chain_hash"]:
            raise PulseStateCorrupt("pulse chain hash mismatch")
        return body

    def existing(self, pulse_id: str) -> dict[str, Any] | None:
        row = self.ledger.conn.execute(
            "SELECT * FROM database_pulse_receipts WHERE pulse_id=? OR idem=? ORDER BY seq LIMIT 1",
            (pulse_id, f"database-pulse:{pulse_id}"),
        ).fetchone()
        if row is None:
            return None
        body = self._validate_row(row)
        return {
            **body,
            "receipt_hash": row["receipt_hash"],
            "pulse_chain_hash": row["pulse_chain_hash"],
            "commit_status": "ALREADY_RECORDED",
            "semantic_epoch_after": int(row["basis_epoch"]),
            "semantic_state_hash_after": row["source_semantic_state_hash"],
        }

    def head(self) -> dict[str, Any] | None:
        rows = self.ledger.conn.execute(
            "SELECT * FROM database_pulse_receipts ORDER BY seq DESC LIMIT 2"
        ).fetchall()
        if not rows:
            return None
        latest = rows[0]
        expected_prev = self.GENESIS
        if len(rows) == 2:
            previous = rows[1]
            self._validate_row(previous)
            if int(latest["pulse_count"]) != int(previous["pulse_count"]) + 1:
                raise PulseStateCorrupt("pulse_count discontinuity")
            expected_prev = previous["pulse_chain_hash"]
        elif int(latest["pulse_count"]) != 1:
            raise PulseStateCorrupt("first pulse_count must be 1")
        body = self._validate_row(latest, expected_prev=expected_prev)
        return {
            "body": body,
            "receipt_hash": latest["receipt_hash"],
            "pulse_chain_hash": latest["pulse_chain_hash"],
        }

    def verify_all(self) -> dict[str, Any]:
        rows = self.ledger.conn.execute(
            "SELECT * FROM database_pulse_receipts ORDER BY seq"
        ).fetchall()
        prev = self.GENESIS
        count = 0
        for row in rows:
            count += 1
            if int(row["pulse_count"]) != count:
                raise PulseStateCorrupt("pulse_count sequence corrupt")
            self._validate_row(row, expected_prev=prev)
            prev = row["pulse_chain_hash"]
        return {"valid": True, "pulse_count": count, "pulse_chain_hash": prev}

    def export_receipts(self) -> list[dict[str, Any]]:
        self.verify_all()
        out: list[dict[str, Any]] = []
        for row in self.ledger.conn.execute(
            "SELECT * FROM database_pulse_receipts ORDER BY seq"
        ):
            out.append({
                "pulse_id": row["pulse_id"],
                "pulse_count": int(row["pulse_count"]),
                "basis_epoch": int(row["basis_epoch"]),
                "source_semantic_state_hash": row["source_semantic_state_hash"],
                "receipt": self._receipt_body(row),
                "receipt_hash": row["receipt_hash"],
                "pulse_chain_hash": row["pulse_chain_hash"],
                "committed_at": row["committed_at"],
            })
        return out

    def append(
        self,
        body: dict[str, Any],
        *,
        expected_prev_chain: str,
        committed_at: str | None = None,
    ) -> dict[str, Any]:
        receipt_hash = h(body)
        pulse_id = str(body["pulse_id"])
        idem = f"database-pulse:{pulse_id}"
        pulse_count = int(body["pulse_count"])
        basis_epoch = int(body["basis_epoch"])
        source_hash = str(body["source_semantic_state_hash"])
        self.ledger.conn.execute("BEGIN IMMEDIATE")
        try:
            old = self.ledger.conn.execute(
                "SELECT * FROM database_pulse_receipts WHERE pulse_id=? OR idem=? ORDER BY seq LIMIT 1",
                (pulse_id, idem),
            ).fetchone()
            if old is not None:
                old_body = self._validate_row(old)
                if h(old_body) != receipt_hash:
                    raise PulseConcurrentAdvance("pulse idempotency payload conflict")
                self.ledger.conn.rollback()
                return {
                    "status": "ALREADY_RECORDED",
                    "receipt_hash": old["receipt_hash"],
                    "pulse_chain_hash": old["pulse_chain_hash"],
                }

            if self.ledger.epoch != basis_epoch:
                raise StaleEpoch(f"pulse commit basis {basis_epoch}!={self.ledger.epoch}")
            if self.ledger.semantic_state_hash != source_hash:
                raise StaleEpoch("pulse semantic state hash changed before receipt commit")

            prev = self.ledger.conn.execute(
                "SELECT pulse_count,pulse_chain_hash FROM database_pulse_receipts ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            actual_prev_chain = self.GENESIS if prev is None else prev["pulse_chain_hash"]
            actual_prev_count = 0 if prev is None else int(prev["pulse_count"])
            if actual_prev_chain != expected_prev_chain or pulse_count != actual_prev_count + 1:
                raise PulseConcurrentAdvance("pulse journal advanced concurrently")

            chain = h({
                "prev": actual_prev_chain,
                "receipt_hash": receipt_hash,
                "pulse_count": pulse_count,
                "basis_epoch": basis_epoch,
                "source_semantic_state_hash": source_hash,
            })
            ts = committed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.ledger.conn.execute(
                "INSERT INTO database_pulse_receipts("
                "pulse_id,idem,pulse_count,basis_epoch,source_semantic_state_hash,receipt_json,"
                "receipt_hash,prev_pulse_chain_hash,pulse_chain_hash,committed_at"
                ") VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    pulse_id,
                    idem,
                    pulse_count,
                    basis_epoch,
                    source_hash,
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


class DatabasePulse:
    """Smallest executable Database Pulse consistent with current project invariants."""

    LEGACY_BOOKKEEPING_DOMAIN = "pulse_runtime"

    def __init__(self, ledger: StateLedger, config: PulseConfig = PulseConfig()):
        config.validate()
        self.ledger = ledger
        self.config = config
        self.journal = PulseJournal(ledger)

    @staticmethod
    def _ref(domain: str, key: str) -> str:
        return f"{domain}:{key}"

    @staticmethod
    def _split_ref(ref: str) -> tuple[str, str]:
        if ":" not in ref:
            raise PulseStateCorrupt(f"invalid active ref {ref!r}")
        return ref.split(":", 1)

    def _head(self, basis_epoch: int) -> dict[str, Any] | None:
        head = self.journal.head()
        if head is None:
            return None
        value = head["body"]
        required = {
            "pulse_count",
            "basis_epoch",
            "source_semantic_state_hash",
            "active_refs",
        }
        if not required.issubset(value):
            raise PulseStateCorrupt("pulse head missing required fields")
        if not isinstance(value["pulse_count"], int) or value["pulse_count"] < 1:
            raise PulseStateCorrupt("invalid pulse_count")
        prev = value["basis_epoch"]
        if not isinstance(prev, int) or prev < 0 or prev > basis_epoch:
            raise PulseStateCorrupt("invalid previous basis_epoch")
        if not isinstance(value["source_semantic_state_hash"], str):
            raise PulseStateCorrupt("invalid source_semantic_state_hash")
        refs = value["active_refs"]
        if not isinstance(refs, list) or not all(
            isinstance(x, dict) and isinstance(x.get("ref"), str) for x in refs
        ):
            raise PulseStateCorrupt("invalid active_refs")
        return {**head, "active_ref_ids": [x["ref"] for x in refs]}

    def _bootstrap_rows(self) -> tuple[list[dict[str, Any]], bool, int]:
        count = int(
            self.ledger.conn.execute(
                "SELECT COUNT(*) FROM state WHERE domain<>?",
                (self.LEGACY_BOOKKEEPING_DOMAIN,),
            ).fetchone()[0]
        )
        rows = self.ledger.conn.execute(
            "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash "
            "FROM state WHERE domain<>? "
            "ORDER BY domain COLLATE BINARY,k COLLATE BINARY LIMIT ?",
            (self.LEGACY_BOOKKEEPING_DOMAIN, self.config.bootstrap_scan_limit + 1),
        ).fetchall()
        truncated = len(rows) > self.config.bootstrap_scan_limit
        rows = rows[: self.config.bootstrap_scan_limit]
        return [self._decode_row(r) for r in rows], truncated, count

    @staticmethod
    def _decode_row(row) -> dict[str, Any]:
        return {
            "domain": row["domain"],
            "key": row["k"],
            "value": json.loads(row["value_json"]) if row["value_json"] is not None else None,
            "epistemic": row["epistemic"],
            "status": row["status"],
            "domain_epoch": int(row["domain_epoch"]),
            "semantic_hash": row["semantic_hash"],
        }

    def _changed_refs(self, previous_basis_epoch: int, basis_epoch: int) -> tuple[list[str], int]:
        rows = self.ledger.conn.execute(
            "SELECT epoch,ops_json FROM events WHERE epoch>? AND epoch<=? ORDER BY epoch LIMIT ?",
            (previous_basis_epoch, basis_epoch, self.config.max_delta_events + 1),
        ).fetchall()
        if len(rows) > self.config.max_delta_events:
            raise PulseStateCorrupt("semantic delta event budget exceeded; explicit rebootstrap required")
        refs: list[str] = []
        for row in rows:
            for op in json.loads(row["ops_json"]):
                domain = str(op.get("domain", ""))
                key = str(op.get("key", ""))
                if not domain or not key or domain == self.LEGACY_BOOKKEEPING_DOMAIN:
                    continue
                ref = self._ref(domain, key)
                if ref not in refs:
                    refs.append(ref)
        return refs, len(rows)

    def _fetch_refs(self, refs: Iterable[str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for ref in refs:
            domain, key = self._split_ref(ref)
            row = self.ledger.conn.execute(
                "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash "
                "FROM state WHERE domain=? AND k=?",
                (domain, key),
            ).fetchone()
            if row:
                out.append(self._decode_row(row))
        return out

    @staticmethod
    def _score(row: dict[str, Any], *, changed: bool, carried: bool) -> float:
        epi = str(row["epistemic"]).upper()
        status = str(row["status"]).upper()
        score = 0.0
        if changed:
            score += 1.0
        if carried:
            score += 0.18
        if status != "CURRENT":
            score -= 1.0
        if epi == "CONFLICT":
            score += 1.25
        elif epi == "UNKNOWN":
            score += 0.70
        elif epi == "KNOWN":
            score += 0.20
        elif epi == "REVOKED":
            score -= 1.0
        return score

    def _activate(
        self,
        rows: Iterable[dict[str, Any]],
        *,
        changed_refs: set[str],
        carried_refs: set[str],
    ) -> list[ActiveRef]:
        active: list[ActiveRef] = []
        for row in rows:
            ref = self._ref(row["domain"], row["key"])
            score = self._score(row, changed=ref in changed_refs, carried=ref in carried_refs)
            unresolved = str(row["epistemic"]).upper() in {"UNKNOWN", "CONFLICT"}
            fresh_current = ref in changed_refs and str(row["status"]).upper() == "CURRENT"
            if not unresolved and not fresh_current:
                continue
            if str(row["status"]).upper() != "CURRENT":
                continue
            active.append(
                ActiveRef(
                    ref=ref,
                    domain=row["domain"],
                    key=row["key"],
                    score=round(score, 6),
                    epistemic=row["epistemic"],
                    status=row["status"],
                    changed=ref in changed_refs,
                    carried=ref in carried_refs,
                    semantic_hash=row["semantic_hash"],
                )
            )
        active.sort(key=lambda x: (-x.score, x.ref))
        return active[: self.config.max_active_refs]

    def run(self, pulse_id: str, *, basis_epoch: int | None = None) -> dict[str, Any]:
        if not pulse_id.strip():
            raise ValueError("pulse_id required")
        existing = self.journal.existing(pulse_id)
        if existing is not None:
            return existing

        basis = self.ledger.epoch
        if basis_epoch is not None and int(basis_epoch) != basis:
            raise StaleEpoch(f"pulse basis {basis_epoch}!={basis}")
        source_hash = self.ledger.semantic_state_hash
        trace_root_before = self.ledger.trace_root_hash
        head = self._head(basis)
        pulse_count = 1 if head is None else int(head["body"]["pulse_count"]) + 1
        previous_basis = None if head is None else int(head["body"]["basis_epoch"])
        prev_chain = self.journal.GENESIS if head is None else head["pulse_chain_hash"]
        bootstrap = head is None
        delta_event_count = 0

        if bootstrap:
            rows, bootstrap_truncated, census_count = self._bootstrap_rows()
            changed = [self._ref(r["domain"], r["key"]) for r in rows]
            carried: list[str] = []
        else:
            bootstrap_truncated = False
            census_count = None
            changed, delta_event_count = self._changed_refs(previous_basis, basis)
            carried = list(dict.fromkeys(head["active_ref_ids"]))[: self.config.max_active_refs]
            refs = list(dict.fromkeys(changed + carried))
            rows = self._fetch_refs(refs)

        active = self._activate(rows, changed_refs=set(changed), carried_refs=set(carried))
        unresolved_count = sum(
            1 for x in active if x.epistemic.upper() in {"UNKNOWN", "CONFLICT"}
        )
        memory_update_observed_count = sum(1 for ref in changed if ref.startswith("memory:"))

        receipt = {
            "schema_version": "0.2",
            "pulse_id": pulse_id,
            "mode": "ZERO_MODEL_DELTA_AWARE",
            "pulse_count": pulse_count,
            "basis_epoch": basis,
            "source_semantic_state_hash": source_hash,
            "previous_basis_epoch": previous_basis,
            "bootstrap": bootstrap,
            "bootstrap_truncated": bootstrap_truncated,
            "census_count": census_count,
            "delta_event_count": delta_event_count,
            "observed_change_count": len(changed),
            "active_refs": [asdict(x) for x in active],
            "unresolved_count": unresolved_count,
            "pulse_state_transition_count": 1,
            "semantic_state_transition_count": 0,
            "memory_update_observed_count": memory_update_observed_count,
            "graph_change_count": 0,
            "hypothesis_count": 0,
            "reentry_count": 0,
            "model_call_count": 0,
            "tool_call_count": 0,
            "effect_count": 0,
            "trace_root_before": trace_root_before,
            "authority": "OBSERVATION_AND_EXECUTION_RECEIPT_ONLY",
        }
        commit = self.journal.append(receipt, expected_prev_chain=prev_chain)
        if self.ledger.epoch != basis or self.ledger.semantic_state_hash != source_hash:
            raise PulseStateCorrupt("execution-only pulse mutated semantic state")
        return {
            **receipt,
            "receipt_hash": commit["receipt_hash"],
            "pulse_chain_hash": commit["pulse_chain_hash"],
            "commit_status": commit["status"],
            "semantic_epoch_after": self.ledger.epoch,
            "semantic_state_hash_after": self.ledger.semantic_state_hash,
            "trace_root_hash_after": self.ledger.trace_root_hash,
        }


def replay_entity_trace(
    semantic_events: list[dict[str, Any]],
    pulse_receipts: list[dict[str, Any]],
    *,
    path: str = ":memory:",
    config: PulseConfig = PulseConfig(),
) -> tuple[StateLedger, DatabasePulse]:
    """Replay semantic events and deterministic Pulse executions in original semantic time.

    Pulse receipts are grouped by basis_epoch and replayed after all semantic events that
    establish that epoch, preserving multiple execution-only Pulses at one semantic epoch.
    The regenerated receipt hashes must match the exported hashes exactly.
    """
    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in pulse_receipts:
        grouped.setdefault(int(item["basis_epoch"]), []).append(item)
    for xs in grouped.values():
        xs.sort(key=lambda x: int(x["pulse_count"]))

    ledger = StateLedger(path)
    pulse = DatabasePulse(ledger, config)

    def replay_pulses_at(epoch: int) -> None:
        for expected in grouped.pop(epoch, []):
            got = pulse.run(str(expected["pulse_id"]), basis_epoch=epoch)
            if got["receipt_hash"] != expected["receipt_hash"]:
                raise PulseStateCorrupt(
                    f"replay receipt mismatch for {expected['pulse_id']}: "
                    f"{got['receipt_hash']}!={expected['receipt_hash']}"
                )

    replay_pulses_at(0)
    for event in semantic_events:
        ledger.append_event(**event)
        replay_pulses_at(ledger.epoch)
    if grouped:
        raise PulseStateCorrupt(f"pulse receipts reference unreplayed semantic epochs {sorted(grouped)}")
    pulse.journal.verify_all()
    return ledger, pulse
