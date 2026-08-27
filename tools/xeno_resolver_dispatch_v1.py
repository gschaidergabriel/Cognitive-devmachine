"""XENO_RESOLVER_DISPATCH/v1 -- 2026-08-27, closes a real gap found while pursuing
Gabriel's "computational unit, not average-good" bar.

Testing each of the 16 family resolvers only against its OWN family's data proved
each is 100% correct in isolation -- but a naive "try every resolver, use whichever
returns non-None" dispatcher is NOT safe: 165 real cross-family false positives were
found (e.g. B0_WRITE_BASELINE's plain CODEBOOK-lookup resolver ignores the
STALE_REJECTED marker and returns a wrong ordinal for B2_STALE_BINDING_REJECTION
prompts, which share the same CODEBOOK/STATE surface structure). A real
computational unit must identify which family a prompt belongs to BEFORE picking a
resolver, not guess from whichever resolver happens to return something.

classify_family() below is a priority-ordered set of mutually-disambiguating
structural checks (most-specific/constrained markers first), verified in this
session to produce EXACTLY the correct family label for all 16,172 real rows
across all 16 families combined -- zero misroutes, not a sample. See
RUN4_DISPATCH_VERIFICATION_20260827.json for the exact counts.
"""
from __future__ import annotations

import re
from typing import Optional


def classify_family(prompt: str) -> Optional[str]:
    if "marked STALE_REJECTED" in prompt:
        return "B2_STALE_BINDING_REJECTION"
    if "NOTE (reference only" in prompt:
        return "B2_PRIOR_OVERRIDE"
    if "UPDATE: from this point forward" in prompt:
        return "B2_MID_EPISODE_REMAP"
    if "LEXICON (entry points)" in prompt:
        return "B3_UNRESOLVABLE_CHAIN_REJECTION" if "UNRESOLVABLE" in prompt else "B3_MULTI_HOP_DEREF"
    if "INTERVENING:" in prompt:
        return "B4_CAPACITY_INTERFERENCE"
    if "Which atom is bound to" in prompt:
        return "B5_VARIABLE_N_EQUIVARIANCE"
    if "Hyperposition branches" in prompt:
        return "B6_HYPERPOSITION_EVIDENCE_AUTHORITY"
    if "won the discriminator-score competition" in prompt:
        return "B6_GWT_UPTAKE"
    if re.search(r"ROUND 1:\s*discriminator scores", prompt):
        return "B6_GWT_CAUSAL_REENTRY"
    if "discriminator scores" in prompt.lower() or "Discriminator scores" in prompt:
        return "B6_GWT_COMPETITION_BROADCAST"
    if "Claim under review" in prompt:
        return "B6_DB_VS_SIM"
    if "Statement under review" in prompt:
        return "B6_CLAUDE_HANDOFF_REENTRY"
    if "EVIDENCE:" in prompt and "QUERY:" in prompt and "CODEBOOK:" in prompt:
        return "B1_TRAIN_BALANCED_2ORDER"
    if "EVIDENCE:" in prompt and "QUERY:" in prompt:
        return "B0_READ_BASELINE"
    if re.search(r"^(?:CODEBOOK|LEXICON)", prompt) or "CODEBOOK:" in prompt:
        return "B0_WRITE_BASELINE"
    return None


def resolve(prompt: str):
    """Full pipeline: classify, then dispatch to the exact family's resolver.
    Returns (family_or_None, answer_or_None). answer is None if either the family
    could not be classified or that family's resolver itself declines (fails
    closed both ways -- never guesses)."""
    import xeno_structured_prompt_resolver_v1 as struct_resolvers

    fam = classify_family(prompt)
    if fam is None:
        return None, None
    resolver_fn = struct_resolvers.FAMILY_RESOLVERS.get(fam)
    if resolver_fn is None:
        return fam, None
    return fam, resolver_fn(prompt)
