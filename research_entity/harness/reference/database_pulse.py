from __future__ import annotations

"""Deterministic zero-model reference kernel for the FRANK Database Pulse.

The Database Pulse is an endogenous state/cognition cycle over the canonical UnifiedDB
ledger. This reference implementation deliberately proves the smallest useful subset:

* a pulse can complete with zero model/tool/effect calls;
* first observation may bootstrap from bounded current state;
* later pulses consume only source deltas plus carried unresolved references;
* pulse bookkeeping does not self-excite subsequent pulses;
* stale or corrupt state fails closed;
* every committed pulse is idempotent, provenance-bound and replayable through StateLedger.

This module is a reference harness candidate. It does not grant truth or effect authority.
"""

import json
from dataclasses import asdict, dataclass
from typing import Any

from .state_ledger import StateLedger, StaleEpoch, h


class PulseStateCorrupt(RuntimeError):
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


class DatabasePulse:
    """Smallest executable Database Pulse consistent with the owner-fixed contract."""

    BOOKKEEPING_DOMAIN = "pulse_runtime"
    IDEM_PREFIX = "database-pulse:"

    def __init__(self, ledger: StateLedger, config: PulseConfig = PulseConfig()):
        config.validate()
        self.ledger = ledger
        self.config = config

    @staticmethod
    def _ref(domain: str, key: str) -> str:
        return f"{domain}:{key}"

    @staticmethod
    def _split_ref(ref: str) -> tuple[str, str]:
        if ":" not in ref:
            raise PulseStateCorrupt(f"invalid active ref {ref!r}")
        return ref.split(":", 1)

    def _existing(self, pulse_id: str) -> dict[str, Any] | None:
        idem = self.IDEM_PREFIX + pulse_id
        row = self.ledger.conn.execute(
            "SELECT epoch,base_epoch,semantic_state_hash,trace_root_hash,execution_json "
            "FROM events WHERE idem=?",
            (idem,),
        ).fetchone()
        if not row:
            return None
        execution = json.loads(row["execution_json"])
        body = execution.get("database_pulse_receipt")
        if not isinstance(body, dict):
            raise PulseStateCorrupt("existing pulse event lacks receipt")
        return {
            **body,
            "commit_status": "ALREADY_COMMITTED",
            "commit_epoch": int(row["epoch"]),
            "post_semantic_state_hash": row["semantic_state_hash"],
            "trace_root_hash": row["trace_root_hash"],
        }

    def _head(self, basis_epoch: int) -> dict[str, Any] | None:
        row = self.ledger.get(self.BOOKKEEPING_DOMAIN, "head")
        if row is None:
            return None
        if row.get("epistemic") != "KNOWN" or row.get("status") != "CURRENT":
            raise PulseStateCorrupt("pulse head is not KNOWN/CURRENT")
        value = row.get("value")
        if not isinstance(value, dict):
            raise PulseStateCorrupt("pulse head value is not an object")
        required = {
            "pulse_count",
            "observed_basis_epoch",
            "source_semantic_state_hash",
            "active_refs",
        }
        if not required.issubset(value):
            raise PulseStateCorrupt("pulse head missing required fields")
        if not isinstance(value["pulse_count"], int) or value["pulse_count"] < 1:
            raise PulseStateCorrupt("invalid pulse_count")
        prev = value["observed_basis_epoch"]
        if not isinstance(prev, int) or prev < 0 or prev > basis_epoch:
            raise PulseStateCorrupt("invalid observed_basis_epoch")
        if not isinstance(value["source_semantic_state_hash"], str):
            raise PulseStateCorrupt("invalid source_semantic_state_hash")
        if not isinstance(value["active_refs"], list) or not all(
            isinstance(x, str) for x in value["active_refs"]
        ):
            raise PulseStateCorrupt("invalid active_refs")
        return value

    def _bootstrap_rows(self) -> tuple[list[dict[str, Any]], bool, int]:
        count = int(
            self.ledger.conn.execute(
                "SELECT COUNT(*) FROM state WHERE domain<>?",
                (self.BOOKKEEPING_DOMAIN,),
            ).fetchone()[0]
        )
        rows = self.ledger.conn.execute(
            "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash "
            "FROM state WHERE domain<>? "
            "ORDER BY domain COLLATE BINARY,k COLLATE BINARY LIMIT ?",
            (self.BOOKKEEPING_DOMAIN, self.config.bootstrap_scan_limit + 1),
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

    def _changed_refs(self, previous_observed_epoch: int, basis_epoch: int) -> tuple[list[str], int]:
        rows = self.ledger.conn.execute(
            "SELECT epoch,ops_json FROM events WHERE epoch>? AND epoch<=? ORDER BY epoch LIMIT ?",
            (previous_observed_epoch, basis_epoch, self.config.max_delta_events + 1),
        ).fetchall()
        if len(rows) > self.config.max_delta_events:
            raise PulseStateCorrupt("delta event budget exceeded; explicit rebootstrap required")
        refs: list[str] = []
        for row in rows:
            for op in json.loads(row["ops_json"]):
                domain = str(op.get("domain", ""))
                key = str(op.get("key", ""))
                if not domain or not key or domain == self.BOOKKEEPING_DOMAIN:
                    continue
                ref = self._ref(domain, key)
                if ref not in refs:
                    refs.append(ref)
        return refs, len(rows)

    def _fetch_refs(self, refs: list[str]) -> list[dict[str, Any]]:
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
        rows: list[dict[str, Any]],
        *,
        changed_refs: set[str],
        carried_refs: set[str],
    ) -> list[ActiveRef]:
        active: list[ActiveRef] = []
        for row in rows:
            ref = self._ref(row["domain"], row["key"])
            score = self._score(
                row, changed=ref in changed_refs, carried=ref in carried_refs
            )
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
        existing = self._existing(pulse_id)
        if existing is not None:
            return existing

        basis = self.ledger.epoch
        if basis_epoch is not None and int(basis_epoch) != basis:
            raise StaleEpoch(f"pulse basis {basis_epoch}!={basis}")

        source_hash = self.ledger.semantic_state_hash
        head = self._head(basis)
        pulse_count = 1 if head is None else int(head["pulse_count"]) + 1
        delta_event_count = 0
        bootstrap = head is None

        if bootstrap:
            rows, bootstrap_truncated, census_count = self._bootstrap_rows()
            changed = [self._ref(r["domain"], r["key"]) for r in rows]
            carried: list[str] = []
        else:
            bootstrap_truncated = False
            census_count = None
            previous = int(head["observed_basis_epoch"])
            changed, delta_event_count = self._changed_refs(previous, basis)
            carried = list(dict.fromkeys(head["active_refs"]))[: self.config.max_active_refs]
            refs = list(dict.fromkeys(changed + carried))
            rows = self._fetch_refs(refs)

        active = self._activate(
            rows,
            changed_refs=set(changed),
            carried_refs=set(carried),
        )
        active_refs = [x.ref for x in active]
        unresolved_count = sum(
            1 for x in active if x.epistemic.upper() in {"UNKNOWN", "CONFLICT"}
        )
        memory_update_observed_count = sum(
            1 for ref in changed if ref.startswith("memory:")
        )

        precommit_receipt = {
            "schema_version": "0.1",
            "pulse_id": pulse_id,
            "mode": "ZERO_MODEL",
            "pulse_count": pulse_count,
            "basis_epoch": basis,
            "source_semantic_state_hash": source_hash,
            "bootstrap": bootstrap,
            "bootstrap_truncated": bootstrap_truncated,
            "census_count": census_count,
            "delta_event_count": delta_event_count,
            "observed_change_count": len(changed),
            "active_refs": [asdict(x) for x in active],
            "unresolved_count": unresolved_count,
            "pulse_state_transition_count": 1,
            "memory_update_observed_count": memory_update_observed_count,
            "graph_change_count": 0,
            "hypothesis_count": 0,
            "reentry_count": 0,
            "model_call_count": 0,
            "tool_call_count": 0,
            "effect_count": 0,
            "authority": "OBSERVATION_AND_INTERNAL_STATE_ONLY",
        }
        precommit_receipt["receipt_hash"] = h(precommit_receipt)

        head_value = {
            "pulse_count": pulse_count,
            "observed_basis_epoch": basis,
            "source_semantic_state_hash": source_hash,
            "active_refs": active_refs,
            "last_pulse_id": pulse_id,
            "last_receipt_hash": precommit_receipt["receipt_hash"],
            "mode": "ZERO_MODEL",
        }
        commit = self.ledger.append_event(
            event_id=self.IDEM_PREFIX + pulse_id,
            idem=self.IDEM_PREFIX + pulse_id,
            base_epoch=basis,
            event_type="DATABASE_PULSE_ZERO_MODEL",
            writer="frank-database-pulse-reference",
            ops=[
                {
                    "op": "SET",
                    "domain": self.BOOKKEEPING_DOMAIN,
                    "key": "head",
                    "value": head_value,
                    "epistemic": "KNOWN",
                    "status": "CURRENT",
                }
            ],
            provenance={
                "contract": "research_entity/global/FRANK_DATABASE_PULSE_CONTRACT.md",
                "implementation": "research_entity/harness/reference/database_pulse.py",
                "basis_epoch": basis,
            },
            source={
                "semantic_state_hash": source_hash,
                "changed_refs": changed,
                "carried_refs": carried,
            },
            execution={"database_pulse_receipt": precommit_receipt},
        )
        return {
            **precommit_receipt,
            "commit_status": commit["status"],
            "commit_epoch": int(commit["epoch"]),
            "post_semantic_state_hash": commit["semantic_state_hash"],
            "trace_root_hash": commit["trace_root_hash"],
        }
