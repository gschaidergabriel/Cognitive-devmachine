"""Deterministic H1 reference compiler for FRANK's bounded ActiveAssembly.

This is an ordinary-code semantic reference, not a production ClayCode implementation.
It preserves identity/ancestry/conflict/provenance, excludes stale packets, emits
re-expansion references for omitted detail, enforces an optional hard model-facing
context-cost budget, and never converts model/peer/visual/capability state into
execution authority.
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
    # Deterministic model-facing context-cost estimate. Once a target tokenizer is
    # bound this can be tokenizer tokens; H1 synthetic fixtures may use abstract units.
    context_cost: int = 1


def packet_score(packet: AssemblyPacket) -> float:
    for name in ("relevance", "impact", "novelty", "uncertainty"):
        value = getattr(packet, name)
        if not 0.0 <= value <= 1.0:
            raise ActiveAssemblyError(f"BAD_SCORE:{packet.packet_id}:{name}")
    if isinstance(packet.context_cost, bool) or not isinstance(packet.context_cost, int) or packet.context_cost <= 0:
        raise ActiveAssemblyError(f"BAD_CONTEXT_COST:{packet.packet_id}")
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
    max_context_cost: Optional[int] = None,
) -> dict:
    if max_items <= 0 or max_per_ancestry <= 0:
        raise ActiveAssemblyError("BAD_BUDGET")
    if max_context_cost is not None and (
        isinstance(max_context_cost, bool)
        or not isinstance(max_context_cost, int)
        or max_context_cost <= 0
    ):
        raise ActiveAssemblyError("BAD_CONTEXT_BUDGET")

    # Packet identity is a replay/provenance boundary. Exact duplicate deliveries are
    # idempotent; the same packet_id bound to different content fails closed rather than
    # allowing ranking/order to silently choose which semantic object "wins".
    unique: list[AssemblyPacket] = []
    identity_by_id: dict[str, str] = {}
    input_duplicate_count = 0
    for packet in candidates:
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
    selection_roles: dict[str, str] = {}
    selection_block_reason: dict[str, str] = {}
    used_context_cost = 0

    def add(packet: AssemblyPacket, *, conflict_visibility: bool = False) -> bool:
        nonlocal used_context_cost
        if packet.packet_id in selected_ids:
            return False
        if len(selected) >= max_items:
            selection_block_reason.setdefault(packet.packet_id, "ITEM_BUDGET")
            return False
        # Ancestry caps prevent repeated shared ancestry from masquerading as
        # independent support. They must not erase an explicit opposite proposition.
        # Conflict representatives may therefore bypass the family cap, but they still
        # consume the same hard item and model-facing context-cost budgets and receive
        # zero independent-replication credit.
        if not conflict_visibility and ancestry_counts.get(packet.ancestry_family, 0) >= max_per_ancestry:
            selection_block_reason.setdefault(packet.packet_id, "ANCESTRY_CAP")
            return False
        if max_context_cost is not None and used_context_cost + packet.context_cost > max_context_cost:
            selection_block_reason.setdefault(packet.packet_id, "CONTEXT_COST_BUDGET")
            return False
        selected.append(packet)
        selected_ids.add(packet.packet_id)
        ancestry_counts[packet.ancestry_family] = ancestry_counts.get(packet.ancestry_family, 0) + 1
        selection_roles[packet.packet_id] = "CONFLICT_VISIBILITY" if conflict_visibility else "ORDINARY"
        used_context_cost += packet.context_cost
        return True

    # Preserve contradictory alternatives before general fill. This is observability,
    # not evidence multiplication: same-ancestry opposites remain visible when the hard
    # total context budgets permit, without being counted as independent replication.
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
        add(packet, conflict_visibility=True)

    # One high-value ordinary packet per ancestry family first prevents repeated shared
    # ancestry from consuming the complete small-model slice. A second pass may use
    # remaining ordinary family budget when space is still available.
    seen_families: set[str] = set()
    for packet in eligible:
        if packet.ancestry_family not in seen_families:
            add(packet)
            seen_families.add(packet.ancestry_family)
    for packet in eligible:
        add(packet)

    for packet in eligible:
        if packet.packet_id not in selected_ids:
            omitted.append((packet, selection_block_reason.get(packet.packet_id, "BUDGET_OR_ANCESTRY_CAP")))

    items = []
    for packet in selected:
        role = selection_roles[packet.packet_id]
        item = asdict(packet)
        item["packet_identity_sha256"] = identity_by_id[packet.packet_id]
        item["score"] = packet_score(packet)
        item["selection_role"] = role
        item["independent_replication_credit"] = False if role == "CONFLICT_VISIBILITY" else None
        item["execution_authority"] = False
        items.append(item)

    assembly = {
        "schema": "frank.active-assembly.v1.2",
        "current_epoch": current_epoch,
        "max_items": max_items,
        "max_per_ancestry": max_per_ancestry,
        "max_context_cost": max_context_cost,
        "context_cost_used": used_context_cost,
        "context_cost_remaining": None if max_context_cost is None else max_context_cost - used_context_cost,
        "items": items,
        "reexpand_refs": sorted({packet.reexpand_ref or packet.packet_id for packet, _ in omitted}),
        "omitted_count": len(omitted),
        "omitted_reasons": {
            reason: sum(1 for _, omitted_reason in omitted if omitted_reason == reason)
            for reason in sorted({omitted_reason for _, omitted_reason in omitted})
        },
    }
    canonical = json.dumps(assembly, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assembly["assembly_sha256"] = hashlib.sha256(canonical).hexdigest()
    # Delivery duplication is transport/input telemetry, not part of semantic identity.
    assembly["input_duplicate_count"] = input_duplicate_count
    return assembly
