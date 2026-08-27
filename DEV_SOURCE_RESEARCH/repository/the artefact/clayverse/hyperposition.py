from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Facet:
    value: str
    source_turn_id: str | None
    user_id: str | None
    ts: float | None
    provenance: Any


@dataclass(frozen=True)
class HyperpositionReadout:
    relation_id: str
    relation_key: str
    subject: str
    kind: str
    facets: tuple[Facet, ...]
    semantic_hash: str
    alternative_count: int
    uncertainty: float

    def as_dict(self) -> dict:
        data = asdict(self)
        data["facets"] = [asdict(x) for x in self.facets]
        data["truth_promoted"] = False
        data["effect_authority"] = False
        data["backend"] = "set-valued-faceted-runtime-v2"
        return data


class HyperpositionProjector:
    """Conservative set-valued projection over explicitly related evidence.

    A user, memory kind, or broad subject is not a semantic relation. Facets therefore
    coexist only when provenance supplies an explicit ``relation_key`` (preferred) or a
    predicate that can be combined with the subject. This prevents unrelated facts from
    being misclassified as competing alternatives. The projection never chooses truth
    and never grants effect authority.
    """

    @staticmethod
    def _stable_json(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except TypeError:
            return json.dumps(str(value), ensure_ascii=False)

    @staticmethod
    def _provenance(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError:
                return {}
            return decoded if isinstance(decoded, dict) else {}
        return {}

    @classmethod
    def _relation_key(cls, memory: dict[str, Any]) -> str | None:
        provenance = cls._provenance(memory.get("provenance"))
        explicit = provenance.get("relation_key")
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip()
        predicate = provenance.get("predicate")
        subject = memory.get("subject")
        if isinstance(predicate, str) and predicate.strip() and isinstance(subject, str) and subject.strip():
            return f"{subject.strip()}::{predicate.strip()}"
        return None

    @classmethod
    def from_world(cls, world: dict, *, max_relations: int = 32, max_facets: int = 8) -> list[dict]:
        groups: dict[tuple[str, str, str], list[Facet]] = {}
        for memory in world.get("durable_memory", []):
            if not isinstance(memory, dict):
                continue
            kind = str(memory.get("kind", "memory"))
            subject = str(memory.get("subject", "shared"))
            value = str(memory.get("value", ""))
            relation_key = cls._relation_key(memory)
            if not value or relation_key is None or kind in {"compression_receipt", "source_archive"}:
                continue
            facet = Facet(
                value=value,
                source_turn_id=memory.get("source_turn_id"),
                user_id=memory.get("user_id"),
                ts=float(memory["ts"]) if isinstance(memory.get("ts"), (int, float)) else None,
                provenance=memory.get("provenance"),
            )
            groups.setdefault((kind, subject, relation_key), []).append(facet)

        readouts: list[dict] = []
        for (kind, subject, relation_key), facets in sorted(groups.items()):
            unique: dict[str, Facet] = {}
            for facet in sorted(facets, key=lambda x: (x.ts or 0.0, x.value), reverse=True):
                unique.setdefault(facet.value, facet)
            if len(unique) < 2:
                continue
            bounded = tuple(list(unique.values())[:max_facets])
            semantic_payload = {
                "kind": kind,
                "relation_key": relation_key,
                "members": sorted(x.value for x in bounded),
            }
            semantic_hash = hashlib.sha256(cls._stable_json(semantic_payload).encode()).hexdigest()
            relation_id = "hyper:" + semantic_hash[:24]
            readout = HyperpositionReadout(
                relation_id=relation_id,
                relation_key=relation_key,
                subject=subject,
                kind=kind,
                facets=bounded,
                semantic_hash=semantic_hash,
                alternative_count=len(bounded),
                uncertainty=min(1.0, (len(bounded) - 1) / max(1, len(bounded))),
            )
            readouts.append(readout.as_dict())
            if len(readouts) >= max_relations:
                break
        return readouts
