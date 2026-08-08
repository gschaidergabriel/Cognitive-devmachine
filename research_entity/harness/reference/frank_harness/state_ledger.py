"""Canonical state/event ledger for the FRANK Test-1 Reference Harness.

Design goals:
- deterministic canonical identities;
- explicit per-domain epochs;
- optimistic precondition checks (fail closed on stale state);
- provenance attached to every accepted transition;
- append-only hash-chained events;
- snapshot/checkpoint export + replay verification;
- no hidden wall-clock entropy in semantic hashes.

This module is architecture-generic. Higher FRANK modules own their domain
schemas; the ledger owns identity, ordering, epochs, provenance and replay.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


GENESIS_EVENT_HASH = "0" * 64


class LedgerError(RuntimeError):
    """Base class for deterministic ledger failures."""


class StaleEpochError(LedgerError):
    """Raised when a transition is based on stale domain state."""


class EventChainError(LedgerError):
    """Raised when the append-only event chain is invalid."""


class ReplayMismatchError(LedgerError):
    """Raised when replay does not reproduce a recorded semantic state."""


class InvalidTransitionError(LedgerError):
    """Raised when a transition is structurally invalid."""


def _normalize(value: Any) -> Any:
    """Normalize supported values into canonical JSON-compatible data."""
    if isinstance(value, Mapping):
        return {str(k): _normalize(value[k]) for k in sorted(value, key=lambda x: str(x))}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        normalized = [_normalize(v) for v in value]
        return sorted(normalized, key=lambda x: canonical_json(x))
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise InvalidTransitionError("NaN/Infinity are forbidden in canonical state")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if hasattr(value, "__dataclass_fields__"):
        return _normalize(asdict(value))
    raise InvalidTransitionError(f"unsupported canonical value type: {type(value)!r}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        _normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def semantic_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProvenanceRef:
    source_id: str
    source_kind: str
    source_epoch: int | None = None
    evidence_status: str | None = None
    content_hash: str | None = None

    def canonical(self) -> dict[str, Any]:
        return _normalize(asdict(self))


@dataclass
class DomainState:
    name: str
    epoch: int = 0
    value: Any = field(default_factory=dict)
    provenance: tuple[ProvenanceRef, ...] = field(default_factory=tuple)

    @property
    def value_hash(self) -> str:
        return semantic_hash(self.value)

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "epoch": self.epoch,
            "value": _normalize(self.value),
            "value_hash": self.value_hash,
            "provenance": [p.canonical() for p in self.provenance],
        }


@dataclass(frozen=True)
class DomainMutation:
    domain: str
    op: str
    payload: Any
    expected_epoch: int
    provenance: tuple[ProvenanceRef, ...] = field(default_factory=tuple)

    def canonical(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "op": self.op,
            "payload": _normalize(self.payload),
            "expected_epoch": self.expected_epoch,
            "provenance": [p.canonical() for p in self.provenance],
        }


@dataclass(frozen=True)
class LedgerEvent:
    seq: int
    event_type: str
    basis_state_hash: str
    result_state_hash: str
    previous_event_hash: str
    mutations: tuple[DomainMutation, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    nondeterminism_receipts: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    event_hash: str = ""

    def without_hash(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "event_type": self.event_type,
            "basis_state_hash": self.basis_state_hash,
            "result_state_hash": self.result_state_hash,
            "previous_event_hash": self.previous_event_hash,
            "mutations": [m.canonical() for m in self.mutations],
            "metadata": _normalize(dict(self.metadata)),
            "nondeterminism_receipts": [_normalize(dict(x)) for x in self.nondeterminism_receipts],
        }

    def recomputed_hash(self) -> str:
        return semantic_hash(self.without_hash())

    def canonical(self) -> dict[str, Any]:
        data = self.without_hash()
        data["event_hash"] = self.event_hash
        return data


@dataclass(frozen=True)
class LedgerSnapshot:
    schema_version: str
    event_seq: int
    last_event_hash: str
    state_hash: str
    domains: Mapping[str, Mapping[str, Any]]

    def canonical(self) -> dict[str, Any]:
        return _normalize(asdict(self))

    @property
    def snapshot_hash(self) -> str:
        return semantic_hash(self.canonical())


def _deep_merge(base: Any, patch: Any) -> Any:
    """Deterministic recursive object merge; lists/scalars replace."""
    if isinstance(base, MutableMapping) and isinstance(patch, Mapping):
        out = deepcopy(dict(base))
        for key in sorted(patch, key=lambda x: str(x)):
            k = str(key)
            if k in out:
                out[k] = _deep_merge(out[k], patch[key])
            else:
                out[k] = deepcopy(patch[key])
        return out
    return deepcopy(patch)


def _delete_path(value: Any, path: Sequence[str]) -> Any:
    if not path:
        raise InvalidTransitionError("delete_path requires a non-empty path")
    out = deepcopy(value)
    cur = out
    for part in path[:-1]:
        if not isinstance(cur, MutableMapping) or part not in cur:
            raise InvalidTransitionError(f"delete_path missing segment: {part}")
        cur = cur[part]
    if not isinstance(cur, MutableMapping) or path[-1] not in cur:
        raise InvalidTransitionError(f"delete_path missing leaf: {path[-1]}")
    del cur[path[-1]]
    return out


def apply_mutation_value(current: Any, mutation: DomainMutation) -> Any:
    op = mutation.op
    payload = mutation.payload
    if op == "replace":
        return deepcopy(payload)
    if op == "merge":
        if not isinstance(payload, Mapping):
            raise InvalidTransitionError("merge payload must be a mapping")
        if not isinstance(current, Mapping):
            raise InvalidTransitionError("merge requires mapping domain state")
        return _deep_merge(current, payload)
    if op == "append":
        if not isinstance(current, list):
            raise InvalidTransitionError("append requires list domain state")
        out = deepcopy(current)
        out.append(deepcopy(payload))
        return out
    if op == "extend":
        if not isinstance(current, list) or not isinstance(payload, list):
            raise InvalidTransitionError("extend requires list state and list payload")
        return deepcopy(current) + deepcopy(payload)
    if op == "delete_path":
        if not isinstance(payload, list) or not all(isinstance(x, str) for x in payload):
            raise InvalidTransitionError("delete_path payload must be list[str]")
        return _delete_path(current, payload)
    raise InvalidTransitionError(f"unsupported mutation op: {op}")


class StateLedger:
    """Append-only canonical state ledger with deterministic replay."""

    SNAPSHOT_SCHEMA_VERSION = "frank-harness-state-1.0"

    def __init__(self, initial_domains: Mapping[str, Any] | None = None):
        self._domains: dict[str, DomainState] = {}
        self._events: list[LedgerEvent] = []
        for name, value in sorted((initial_domains or {}).items()):
            self._domains[str(name)] = DomainState(name=str(name), epoch=0, value=deepcopy(value))

    @property
    def events(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)

    @property
    def domains(self) -> Mapping[str, DomainState]:
        return {k: deepcopy(v) for k, v in self._domains.items()}

    @property
    def last_event_hash(self) -> str:
        return self._events[-1].event_hash if self._events else GENESIS_EVENT_HASH

    @property
    def state_hash(self) -> str:
        return semantic_hash(self._state_identity_payload())

    def _state_identity_payload(self) -> dict[str, Any]:
        return {
            name: {
                "epoch": state.epoch,
                "value": _normalize(state.value),
                "provenance": [p.canonical() for p in state.provenance],
            }
            for name, state in sorted(self._domains.items())
        }

    def domain_epoch(self, domain: str) -> int:
        return self._domains.get(domain, DomainState(name=domain)).epoch

    def read(self, domain: str) -> DomainState:
        if domain not in self._domains:
            return DomainState(name=domain)
        return deepcopy(self._domains[domain])

    def snapshot(self) -> LedgerSnapshot:
        domains = {name: state.canonical() for name, state in sorted(self._domains.items())}
        return LedgerSnapshot(
            schema_version=self.SNAPSHOT_SCHEMA_VERSION,
            event_seq=len(self._events),
            last_event_hash=self.last_event_hash,
            state_hash=self.state_hash,
            domains=domains,
        )

    def apply(
        self,
        event_type: str,
        mutations: Iterable[DomainMutation],
        *,
        metadata: Mapping[str, Any] | None = None,
        nondeterminism_receipts: Iterable[Mapping[str, Any]] = (),
    ) -> LedgerEvent:
        muts = tuple(mutations)
        if not event_type:
            raise InvalidTransitionError("event_type is required")
        if not muts:
            raise InvalidTransitionError("at least one mutation is required")

        seen_domains: set[str] = set()
        for m in muts:
            if m.domain in seen_domains:
                raise InvalidTransitionError(
                    f"multiple mutations to domain {m.domain!r} in one atomic event are forbidden; compose them first"
                )
            seen_domains.add(m.domain)
            current = self._domains.get(m.domain, DomainState(name=m.domain))
            if current.epoch != m.expected_epoch:
                raise StaleEpochError(
                    f"{m.domain}: expected epoch {m.expected_epoch}, current {current.epoch}"
                )

        basis_hash = self.state_hash
        staged = deepcopy(self._domains)
        for m in muts:
            current = staged.get(m.domain, DomainState(name=m.domain))
            new_value = apply_mutation_value(current.value, m)
            _normalize(new_value)
            staged[m.domain] = DomainState(
                name=m.domain,
                epoch=current.epoch + 1,
                value=new_value,
                provenance=tuple(m.provenance),
            )

        result_hash = semantic_hash({
            name: {
                "epoch": state.epoch,
                "value": _normalize(state.value),
                "provenance": [p.canonical() for p in state.provenance],
            }
            for name, state in sorted(staged.items())
        })

        provisional = LedgerEvent(
            seq=len(self._events) + 1,
            event_type=event_type,
            basis_state_hash=basis_hash,
            result_state_hash=result_hash,
            previous_event_hash=self.last_event_hash,
            mutations=muts,
            metadata=_normalize(dict(metadata or {})),
            nondeterminism_receipts=tuple(_normalize(dict(x)) for x in nondeterminism_receipts),
            event_hash="",
        )
        event = LedgerEvent(**{**asdict(provisional), "mutations": muts,
                               "event_hash": provisional.recomputed_hash()})
        self._domains = staged
        self._events.append(event)
        return event

    def verify_chain(self) -> None:
        expected_prev = GENESIS_EVENT_HASH
        replay = StateLedger()
        for event in self._events:
            if event.previous_event_hash != expected_prev:
                raise EventChainError(
                    f"event {event.seq}: prev hash mismatch {event.previous_event_hash} != {expected_prev}"
                )
            if event.event_hash != event.recomputed_hash():
                raise EventChainError(f"event {event.seq}: event hash mismatch")
            if replay.state_hash != event.basis_state_hash:
                raise ReplayMismatchError(
                    f"event {event.seq}: basis hash mismatch during replay"
                )
            replayed = replay.apply(
                event.event_type,
                event.mutations,
                metadata=event.metadata,
                nondeterminism_receipts=event.nondeterminism_receipts,
            )
            if replayed.result_state_hash != event.result_state_hash:
                raise ReplayMismatchError(
                    f"event {event.seq}: result state hash mismatch during replay"
                )
            if replayed.event_hash != event.event_hash:
                raise ReplayMismatchError(
                    f"event {event.seq}: event identity mismatch during replay"
                )
            expected_prev = event.event_hash

        if replay.state_hash != self.state_hash:
            raise ReplayMismatchError("final state hash mismatch")

    def export_log(self) -> dict[str, Any]:
        return {
            "schema_version": self.SNAPSHOT_SCHEMA_VERSION,
            "genesis_event_hash": GENESIS_EVENT_HASH,
            "events": [event.canonical() for event in self._events],
            "final_snapshot": self.snapshot().canonical(),
        }

    @classmethod
    def replay(cls, exported: Mapping[str, Any]) -> "StateLedger":
        if exported.get("genesis_event_hash") != GENESIS_EVENT_HASH:
            raise EventChainError("unknown genesis hash")
        ledger = cls()
        expected_prev = GENESIS_EVENT_HASH
        for raw in exported.get("events", []):
            muts = tuple(
                DomainMutation(
                    domain=m["domain"],
                    op=m["op"],
                    payload=m["payload"],
                    expected_epoch=int(m["expected_epoch"]),
                    provenance=tuple(ProvenanceRef(**p) for p in m.get("provenance", [])),
                )
                for m in raw["mutations"]
            )
            if raw["previous_event_hash"] != expected_prev:
                raise EventChainError(f"event {raw['seq']}: previous hash mismatch")
            event = ledger.apply(
                raw["event_type"],
                muts,
                metadata=raw.get("metadata", {}),
                nondeterminism_receipts=raw.get("nondeterminism_receipts", []),
            )
            for field_name in (
                "seq", "basis_state_hash", "result_state_hash",
                "previous_event_hash", "event_hash"
            ):
                if getattr(event, field_name) != raw[field_name]:
                    raise ReplayMismatchError(
                        f"event {raw['seq']}: {field_name} mismatch"
                    )
            expected_prev = event.event_hash

        final = exported.get("final_snapshot")
        if final:
            if ledger.state_hash != final["state_hash"]:
                raise ReplayMismatchError("final snapshot state hash mismatch")
            if ledger.last_event_hash != final["last_event_hash"]:
                raise ReplayMismatchError("final snapshot event hash mismatch")
        ledger.verify_chain()
        return ledger
