"""Deterministic H1 reference compiler for FRANK's bounded ActiveAssembly.

This is an ordinary-code semantic reference, not a production ClayCode implementation.
It preserves identity/ancestry/conflict/provenance, excludes stale packets, emits
re-expansion references for omitted detail, and never converts model/peer/visual/
capability state into execution authority.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Iterable
import hashlib
import json


class ActiveAssemblyError(ValueError):
    pass


@dataclass(frozen=True)
class AssemblyPacket:
    packet_id: str
    ancestry_family: str
    kind: str
    relevance: float
    impact: float
    novelty: float
    uncertainty: float
    valid_epoch: int
    claim_key: Optional[str] = None
    claim_value: Optional[str] = None
    reexpand_ref: Optional[str] = None
    origin_actor: Optional[str] = None
    proposed_authority: bool = False


def packet_score(packet: AssemblyPacket) -> float:
    for name in ("relevance", "impact", "novelty", "uncertainty"):
        value = getattr(packet, name)
        if not 0.0 <= value <= 1.0:
            raise ActiveAssemblyError(f"BAD_SCORE:{packet.packet_id}:{name}")
    return round(
        0.45 * packet.relevance
        + 0.25 * packet.impact
        + 0.15 * packet.novelty
        + 0.15 * (1.0 - packet.uncertainty),
        12,
    )


def packet_identity_sha256(packet: AssemblyPacket) -> str:
    """Fingerprint the complete semantic/provenance payload bound to packet_id."""
    for name in ("packet_id", "ancestry_family", "kind"):
        value = getattr(packet, name)
        if not isinstance(value, str) or not value.strip():
            raise ActiveAssemblyError(f"BAD_IDENTITY:{name}")
    try:
        canonical = json.dumps(
            asdict(packet),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    except (TypeError, ValueError) as exc:
        raise ActiveAssemblyError(f"NON_CANONICAL_PACKET:{packet.packet_id}") from exc
    return hashlib.sha256(canonical).hexdigest()


def compile_active_assembly(
    candidates: Iterable[AssemblyPacket],
    *,
    current_epoch: int,
    max_items: int = 8,
    max_per_ancestry: int = 2,
) -> dict:
    if max_items <= 0 or max_per_ancestry <= 0:
        raise ActiveAssemblyError("BAD_BUDGET")

    # Packet identity is a replay/provenance boundary. Exact duplicate deliveries are
    # idempotent; the same packet_id bound to different content fails closed rather than
    # allowing ranking/order to silently choose which semantic object "wins".
    unique: list[AssemblyPacket] = []
    identity_by_id: dict[str, str] = {}
    input_duplicate_count = 0
    for packet in candidates:
        # Visibility is not authority. Bearer authority must come from the external
        # deterministic resource/effect gateway, never these cognitive packet classes.
        if packet.proposed_authority and packet.kind in {
            "model_output", "peer_result", "visual_model", "capability"
        }:
            raise ActiveAssemblyError(f"AUTHORITY_MINT_ATTEMPT:{packet.packet_id}")
        packet_score(packet)
        fingerprint = packet_identity_sha256(packet)
        previous = identity_by_id.get(packet.packet_id)
        if previous is not None:
            if previous != fingerprint:
                raise ActiveAssemblyError(f"PACKET_ID_COLLISION:{packet.packet_id}")
            input_duplicate_count += 1
            continue
        identity_by_id[packet.packet_id] = fingerprint
        unique.append(packet)

    eligible: list[AssemblyPacket] = []
    omitted: list[tuple[AssemblyPacket, str]] = []
    for packet in unique:
        if packet.valid_epoch != current_epoch:
            omitted.append((packet, "STALE_EPOCH"))
            continue
        eligible.append(packet)

    eligible.sort(key=lambda packet: (-packet_score(packet), packet.packet_id))
    selected: list[AssemblyPacket] = []
    selected_ids: set[str] = set()
    ancestry_counts: dict[str, int] = {}

    def add(packet: AssemblyPacket) -> bool:
        if packet.packet_id in selected_ids or len(selected) >= max_items:
            return False
        if ancestry_counts.get(packet.ancestry_family, 0) >= max_per_ancestry:
            return False
        selected.append(packet)
        selected_ids.add(packet.packet_id)
        ancestry_counts[packet.ancestry_family] = ancestry_counts.get(packet.ancestry_family, 0) + 1
        return True

    # Preserve contradictory alternatives before general fill. This makes unresolved
    # conflict visible to the 4B rather than silently collapsing it during retrieval.
    by_claim: dict[str, dict[str, AssemblyPacket]] = {}
    for packet in eligible:
        if packet.claim_key is None or packet.claim_value is None:
            continue
        values = by_claim.setdefault(packet.claim_key, {})
        values.setdefault(packet.claim_value, packet)

    conflict_representatives: list[AssemblyPacket] = []
    for values in by_claim.values():
        if len(values) > 1:
            conflict_representatives.extend(values.values())
    conflict_representatives.sort(key=lambda packet: (-packet_score(packet), packet.packet_id))
    for packet in conflict_representatives:
        add(packet)

    # One high-value packet per ancestry family first prevents repeated shared ancestry
    # from consuming the complete small-model slice. A second pass may use remaining
    # family budget when space is still available.
    seen_families: set[str] = set()
    for packet in eligible:
        if packet.ancestry_family not in seen_families:
            add(packet)
            seen_families.add(packet.ancestry_family)
    for packet in eligible:
        add(packet)

    for packet in eligible:
        if packet.packet_id not in selected_ids:
            omitted.append((packet, "BUDGET_OR_ANCESTRY_CAP"))

    items = []
    for packet in selected:
        item = asdict(packet)
        item["packet_identity_sha256"] = identity_by_id[packet.packet_id]
        item["score"] = packet_score(packet)
        item["execution_authority"] = False
        items.append(item)

    assembly = {
        "schema": "frank.active-assembly.v1",
        "current_epoch": current_epoch,
        "max_items": max_items,
        "max_per_ancestry": max_per_ancestry,
        "items": items,
        "reexpand_refs": sorted({packet.reexpand_ref or packet.packet_id for packet, _ in omitted}),
        "omitted_count": len(omitted),
    }
    canonical = json.dumps(assembly, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assembly["assembly_sha256"] = hashlib.sha256(canonical).hexdigest()
    # Delivery duplication is transport/input telemetry, not part of the semantic
    # ActiveAssembly identity, so exact duplicate deliveries do not alter the hash.
    assembly["input_duplicate_count"] = input_duplicate_count
    return assembly
