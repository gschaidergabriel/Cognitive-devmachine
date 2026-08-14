"""Clay Live Delta Router v1 candidate.

Research candidate only. Git/UnifiedDB remains semantic durability authority.
This module implements deterministic dependency-aware routing, identity conflict
guards, dual-time event semantics, revision guards, hybrid fail-broad routing,
and monotonic delivery/use receipt stages. An external transport (e.g. NATS
JetStream) may carry envelopes, but cannot mint truth or effect authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import IntEnum
from hashlib import sha256
import json
import re
from typing import Dict, Iterable, Mapping, Optional, Set, Tuple


_SUBJECT_TOKEN = re.compile(r"[^A-Za-z0-9_-]+")


class ReceiptStage(IntEnum):
    DELIVERED = 1
    RECONSTRUCTED = 2
    USED = 3
    LOCAL_EFFECT = 4
    VERIFIED_OUTCOME = 5
    REENTRY = 6


@dataclass(frozen=True)
class DeltaEnvelope:
    event_id: str
    source: str
    event_type: str
    subject: str
    causal_origin_epoch: int
    arrival_epoch: int
    applicability: str = "CURRENT"
    work_spec_rev: Optional[int] = None
    affected_work_ids: Tuple[str, ...] = ()
    invalidated_claim_ids: Tuple[str, ...] = ()
    ancestry_ids: Tuple[str, ...] = ()
    parent_event_ids: Tuple[str, ...] = ()
    evidence_refs: Tuple[str, ...] = ()
    payload: Mapping[str, object] = field(default_factory=dict)

    def canonical_json(self) -> str:
        obj = asdict(self)
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @property
    def content_hash(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @property
    def identity_key(self) -> str:
        # CloudEvents-compatible duplicate identity is source+id.
        return f"{self.source}|{self.event_id}"

    @property
    def dedupe_key(self) -> str:
        return f"{self.identity_key}|{self.content_hash}"


@dataclass(frozen=True)
class WorkNode:
    work_id: str
    branch: str
    depends_on: Tuple[str, ...] = ()
    premise_claim_ids: Tuple[str, ...] = ()
    spec_rev: int = 0
    current_epoch: int = 0


@dataclass(frozen=True)
class RouteDecision:
    event_id: str
    destinations: Tuple[str, ...]
    destination_branches: Tuple[str, ...]
    priority: str
    mode: str
    reason: str
    dedupe_key: str
    parent_event_ids: Tuple[str, ...]


class IdentityConflictError(ValueError):
    pass


class StaleWorkRevisionError(ValueError):
    pass


class MissingPredecessorError(ValueError):
    pass


class LiveDeltaRouter:
    def __init__(
        self,
        work_nodes: Iterable[WorkNode],
        *,
        dependency_index_complete: bool = True,
        dense_fanout_fraction: float = 0.60,
    ) -> None:
        self._nodes: Dict[str, WorkNode] = {n.work_id: n for n in work_nodes}
        self._dependents: Dict[str, Set[str]] = {k: set() for k in self._nodes}
        self._claim_consumers: Dict[str, Set[str]] = {}
        self._identity_hash: Dict[str, str] = {}
        self._seen_event_ids: Set[str] = set()
        self._receipt_stage: Dict[Tuple[str, str], ReceiptStage] = {}
        self.dependency_index_complete = dependency_index_complete
        self.dense_fanout_fraction = dense_fanout_fraction

        for node in self._nodes.values():
            for dep in node.depends_on:
                if dep not in self._nodes:
                    raise KeyError(f"unknown dependency {dep!r} for {node.work_id!r}")
                self._dependents[dep].add(node.work_id)
            for claim in node.premise_claim_ids:
                self._claim_consumers.setdefault(claim, set()).add(node.work_id)

    def _closure(self, seeds: Iterable[str]) -> Set[str]:
        out: Set[str] = set()
        queue = list(seeds)
        while queue:
            work_id = queue.pop()
            if work_id in out:
                continue
            if work_id not in self._nodes:
                continue
            out.add(work_id)
            queue.extend(self._dependents[work_id] - out)
        return out

    def admit_once(self, event: DeltaEnvelope) -> bool:
        """Admit identical source+id+content once; conflicting content fails closed."""
        existing = self._identity_hash.get(event.identity_key)
        if existing is None:
            self._identity_hash[event.identity_key] = event.content_hash
            self._seen_event_ids.add(event.event_id)
            return True
        if existing != event.content_hash:
            raise IdentityConflictError(
                f"{event.identity_key}: same source+id arrived with conflicting content hash"
            )
        return False

    def route(self, event: DeltaEnvelope) -> RouteDecision:
        # Causal origin age is evidence history, not automatic staleness.
        if event.applicability == "HISTORICALLY_VALID_ONLY":
            return RouteDecision(
                event_id=event.event_id,
                destinations=(),
                destination_branches=(),
                priority="INDEX_ONLY",
                mode="DIGEST_ONLY",
                reason="historically valid event preserved without current plan churn",
                dedupe_key=event.dedupe_key,
                parent_event_ids=event.parent_event_ids,
            )

        # A material effect must not consume an event before declared causal parents are seen.
        missing = [p for p in event.parent_event_ids if p not in self._seen_event_ids]
        if missing:
            raise MissingPredecessorError(
                f"{event.event_id}: missing causal predecessors {sorted(missing)}"
            )

        # Work revision, not causal origin time, is the fail-closed current-plan guard.
        if event.work_spec_rev is not None:
            for work_id in event.affected_work_ids:
                node = self._nodes.get(work_id)
                if node and event.work_spec_rev < node.spec_rev:
                    raise StaleWorkRevisionError(
                        f"{event.event_id}: spec_rev {event.work_spec_rev} < {work_id} rev {node.spec_rev}"
                    )

        seeds: Set[str] = set(event.affected_work_ids)
        for claim in event.invalidated_claim_ids:
            seeds.update(self._claim_consumers.get(claim, ()))

        destinations = self._closure(seeds)
        priority = "INTERRUPT" if event.invalidated_claim_ids else "NORMAL"
        mode = "TARGETED_DELTA"
        reason = (
            "claim invalidation propagated to premise consumers and transitive dependents"
            if event.invalidated_claim_ids
            else "explicit affected work plus transitive dependents"
        )

        # Missing dependency knowledge plus a material invalidation is unsafe for targeted-only.
        if event.invalidated_claim_ids and not self.dependency_index_complete:
            destinations = set(self._nodes)
            mode = "DENSE_FANOUT"
            reason = "dependency index incomplete during invalidation; fail-broad until anti-entropy repair"
        elif self._nodes and len(destinations) / len(self._nodes) >= self.dense_fanout_fraction:
            destinations = set(self._nodes)
            mode = "DENSE_FANOUT"
            reason = "predicted dependency span is dense; deduplicated dense fanout is safer"

        branches = sorted({self._nodes[w].branch for w in destinations})
        return RouteDecision(
            event_id=event.event_id,
            destinations=tuple(sorted(destinations)),
            destination_branches=tuple(branches),
            priority=priority,
            mode=mode,
            reason=reason,
            dedupe_key=event.dedupe_key,
            parent_event_ids=event.parent_event_ids,
        )

    def record_receipt(self, event_id: str, work_id: str, stage: ReceiptStage) -> None:
        key = (event_id, work_id)
        previous = self._receipt_stage.get(key)
        if previous is not None and stage < previous:
            raise ValueError(f"receipt regression {previous.name}->{stage.name}")
        if stage > ReceiptStage.DELIVERED and previous is None:
            raise ValueError("cannot skip DELIVERED as first receipt")
        if previous is not None and stage > previous + 1:
            raise ValueError(f"receipt stage gap {previous.name}->{stage.name}")
        self._receipt_stage[key] = stage

    @staticmethod
    def nats_subject(branch: str, event_class: str, priority: str) -> str:
        def tok(value: str) -> str:
            value = _SUBJECT_TOKEN.sub("-", value).strip("-")
            return value or "unknown"
        return f"clay.delta.{tok(branch)}.{tok(event_class)}.{tok(priority).lower()}"


def cloud_event_projection(event: DeltaEnvelope) -> dict:
    """Minimal protocol-neutral CloudEvents-style projection.

    Extensions carry Clay semantics and observability only; they do not grant authority.
    """
    return {
        "specversion": "1.0",
        "id": event.event_id,
        "source": event.source,
        "type": event.event_type,
        "subject": event.subject,
        "claycausaloriginepoch": event.causal_origin_epoch,
        "clayarrivalepoch": event.arrival_epoch,
        "clayapplicability": event.applicability,
        "clayworkrev": event.work_spec_rev,
        "clayhash": event.content_hash,
        "clayparents": list(event.parent_event_ids),
        "data": {
            "affected_work_ids": list(event.affected_work_ids),
            "invalidated_claim_ids": list(event.invalidated_claim_ids),
            "ancestry_ids": list(event.ancestry_ids),
            "evidence_refs": list(event.evidence_refs),
            "payload": dict(event.payload),
        },
    }
