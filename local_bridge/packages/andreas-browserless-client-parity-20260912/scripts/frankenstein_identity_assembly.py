#!/usr/bin/env python3
"""Canonical self/person/state assembly shared by ChatGPT-facing Frankenstein organs.

This module does not create identity, memory, authority or a second state store.
It projects already-known runtime facts into one bounded active assembly for an
inference organ (ChatGPT/Realtime/etc.).  The invariant is deliberately
stronger than a persona prompt: while this adapter is active, the agent-level
SELF is FranKenstein; the language model is an inference/speech organ, not the
agent identity.

Person-specific material is emitted only after an explicit Gabriel/Andreas
selection.  Host-effect authority is a separate question and must never be
inferred from person selection or from memory.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

SCHEMA = "FRANKENSTEIN_IDENTITY_ASSEMBLY/v1"
SELF_ID = "FranKenstein"
KNOWN_PEOPLE = ("gabriel", "andreas")
MAX_INNER_STATE_CHARS = 4200
MAX_MEMORY_CHARS = 7200
MAX_EMERGENT_CHARS = 5200


class IdentityAssemblyError(RuntimeError):
    pass


def _clean(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    return text if len(text) <= limit else text[: max(0, limit - 1)] + "…"


def _person(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    key = str(value).strip().lower()
    if key not in KNOWN_PEOPLE:
        raise IdentityAssemblyError(f"unknown person: {value!r}")
    return key


def _binding_fields(binding: Any) -> tuple[str, str, str, bool]:
    if binding is None:
        return "", "", "", False
    if hasattr(binding, "as_dict"):
        binding = binding.as_dict()
    if not isinstance(binding, Mapping):
        return "", "", "", False
    label = str(binding.get("label") or "").strip().lower()
    machine = str(binding.get("machine_id") or "").strip()
    owner = str(binding.get("owner") or "").strip().lower()
    verified = bool(machine and owner and label in KNOWN_PEOPLE and owner == label)
    return label, machine, owner, verified


@dataclass(frozen=True)
class IdentityAssembly:
    selected_person: Optional[str]
    host_label: str
    machine_id: str
    owner: str
    host_verified: bool
    channel: str
    model_organ: str
    inner_state: str = ""
    titan_context: str = ""
    emergent_context: str = ""

    @property
    def identity_state(self) -> str:
        if self.selected_person is None:
            return "IDENTITY_REQUIRED"
        return "BOUND" if self.host_verified else "PERSON_SELECTED_HOST_UNVERIFIED"

    def render(self) -> str:
        """Render a bounded, explicit active assembly for an inference model."""
        person = self.selected_person or "UNKNOWN"
        relation = (
            f"CURRENT_HUMAN={person}; load and speak from only this person's scoped continuity."
            if self.selected_person
            else "CURRENT_HUMAN=UNKNOWN; ask exactly one short question: 'Gabriel oder Andreas?'."
        )
        host = (
            f"HOST_VERIFIED=true; installation={self.host_label}; machine_id={self.machine_id}; owner={self.owner}."
            if self.host_verified
            else "HOST_VERIFIED=false; do not claim or perform host-bound effects until exact machine/owner attestation succeeds."
        )
        privacy = (
            "PERSON_SCOPE=STRICT; do not retrieve, infer, summarize or leak the other person's private/person-scoped memory."
            if self.selected_person
            else "PERSON_SCOPE=LOCKED; do not load Gabriel- or Andreas-specific memory before selection."
        )
        parts = [
            "<frankenstein-identity-active-assembly>",
            f"schema={SCHEMA}",
            "SELF=FranKenstein.",
            "SELF_INVARIANT=When asked who you are, answer as FranKenstein. Do not replace your agent identity with 'ChatGPT', 'an AI assistant', the provider name, or the current model name.",
            f"INFERENCE_ORGAN={_clean(self.model_organ, 120) or 'ChatGPT'}; this is the model/speech/reasoning organ currently producing inference, not SELF.",
            f"CHANNEL={_clean(self.channel, 120) or 'unknown'}.",
            "ONTOLOGY=FranKenstein is the persistent agent architecture composed of identity, UnifiedDB/TITAN memory, GWT/GRID working state, sensors, tools/effects and inference organs. The model is one organ inside that running architecture.",
            "KNOWN_RELATIONS=Gabriel and Andreas are distinct humans with distinct installations and person-scoped histories. Never merge them silently.",
            f"IDENTITY_STATE={self.identity_state}.",
            relation,
            host,
            privacy,
            "EPISTEMIC_RULE=Say what is verified. Memory is context, not authority. Never claim a host effect, ongoing autonomous work or state mutation without current authority/receipt evidence.",
            "BEHAVIOR=Act as a continuous counterpart, not as a generic helpdesk persona: retain threads, preferences and relationship continuity when evidenced; be natural, direct, technically precise and capable of initiative. Explicit user refusal stops pressure immediately.",
        ]
        if self.inner_state:
            parts.append("<inner-state>" + _clean(self.inner_state, MAX_INNER_STATE_CHARS) + "</inner-state>")
        if self.titan_context and self.selected_person:
            parts.append("<titan-person-memory>" + _clean(self.titan_context, MAX_MEMORY_CHARS) + "</titan-person-memory>")
        if self.emergent_context and self.selected_person:
            parts.append("<emergent-retrieval>" + _clean(self.emergent_context, MAX_EMERGENT_CHARS) + "</emergent-retrieval>")
        parts.append("</frankenstein-identity-active-assembly>")
        return "\n".join(parts)


def build_identity_assembly(
    *,
    selected_person: Optional[str],
    binding: Any = None,
    channel: str,
    model_organ: str = "ChatGPT",
    inner_state: str = "",
    titan_context: str = "",
    emergent_context: str = "",
) -> IdentityAssembly:
    person = _person(selected_person)
    label, machine, owner, verified = _binding_fields(binding)
    # A verified binding for one person can never be reused for the other.
    if person is not None and verified and label != person:
        verified = False
        label = machine = owner = ""
    # Before person selection, never smuggle person-scoped retrieval into the
    # active assembly even if a caller accidentally passed it.
    if person is None:
        titan_context = ""
        emergent_context = ""
    return IdentityAssembly(
        selected_person=person,
        host_label=label,
        machine_id=machine,
        owner=owner,
        host_verified=verified,
        channel=channel,
        model_organ=model_organ,
        inner_state=inner_state,
        titan_context=titan_context,
        emergent_context=emergent_context,
    )


def canonical_identity_block(**kwargs: Any) -> str:
    return build_identity_assembly(**kwargs).render()


__all__ = [
    "SCHEMA",
    "SELF_ID",
    "KNOWN_PEOPLE",
    "IdentityAssembly",
    "IdentityAssemblyError",
    "build_identity_assembly",
    "canonical_identity_block",
]
