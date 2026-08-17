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
        data["backend"] = "set-valued-faceted-runtime-v1"
        return data


class HyperpositionProjector:
    """Backend-neutral set-valued runtime projection over bounded world evidence.

    This implements the non-authority part of the Hyperposition research contract:
    incompatible/source-distinct facets may coexist under one semantic relation. The
    projection never chooses truth and never grants effect authority. ClayGraph and
    UnifiedDB remain the underlying topology/state authorities.
    """

    @staticmethod
    def _stable_json(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except TypeError:
            return json.dumps(str(value), ensure_ascii=False)

    @classmethod
    def from_world(cls, world: dict, *, max_relations: int = 32, max_facets: int = 8) -> list[dict]:
        groups: dict[tuple[str, str], list[Facet]] = {}
        for memory in world.get("durable_memory", []):
            if not isinstance(memory, dict):
                continue
            kind = str(memory.get("kind", "memory"))
            subject = str(memory.get("subject", "shared"))
            value = str(memory.get("value", ""))
            if not value or kind in {"compression_receipt", "source_archive"}:
                continue
            facet = Facet(
                value=value,
                source_turn_id=memory.get("source_turn_id"),
                user_id=memory.get("user_id"),
                ts=float(memory["ts"]) if isinstance(memory.get("ts"), (int, float)) else None,
                provenance=memory.get("provenance"),
            )
            groups.setdefault((kind, subject), []).append(facet)

        readouts: list[dict] = []
        for (kind, subject), facets in sorted(groups.items()):
            unique: dict[str, Facet] = {}
            for facet in sorted(facets, key=lambda x: (x.ts or 0.0, x.value), reverse=True):
                unique.setdefault(facet.value, facet)
            # A single value is an ordinary state claim, not a Hyperposition.
            if len(unique) < 2:
                continue
            bounded = tuple(list(unique.values())[:max_facets])
            semantic_payload = {
                "kind": kind,
                "subject": subject,
                "members": sorted(x.value for x in bounded),
            }
            semantic_hash = hashlib.sha256(cls._stable_json(semantic_payload).encode()).hexdigest()
            relation_id = "hyper:" + semantic_hash[:24]
            readout = HyperpositionReadout(
                relation_id=relation_id,
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
