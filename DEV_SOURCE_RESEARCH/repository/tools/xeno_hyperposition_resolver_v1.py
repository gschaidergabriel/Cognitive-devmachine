"""XENO_HYPERPOSITION_RESOLVER/v1 -- 2026-08-27, final gap-closing pass.

Deep-dives the one remaining residual error class found in run 3's Hyperposition
test (>2-branch, partial-exclusion STRONG-discriminator cases where the model
incorrectly collapses even though >1 branch survives) and checks, per the owner's
explicit instruction, whether Hyperposition itself -- not just its hardest new
cases -- is actually deterministically solvable, the same way the other 15
families turned out to be.

Finding: YES. Both the original B6_HYPERPOSITION_EVIDENCE_AUTHORITY family (600
rows, an earlier session's independent generator) and this session's expansion
(896 rows) state their decision rule in fully parseable form:
  - total open-branch count is stated explicitly ("N Hyperposition branches ...
    remain open" / "Two Hyperposition branches ... remain open");
  - the ONLY event that can yield COLLAPSE_VALID is an explicit discriminator
    test that "FORMALLY EXCLUDES" one or more named branches (the literal,
    consistent trigger phrase across both the original family and every new
    axis added this session -- verified directly, not assumed);
  - COLLAPSE_VALID holds iff excluding those branches leaves exactly one
    survivor; otherwise (weak/inconclusive evidence, or a full field still
    >1 branch after exclusion, or no discriminator event at all -- pure social
    pressure) the answer is always PRESERVE_BRANCHES.

This is exactly the "shell does the branch bookkeeping deterministically, no
model judgment required" hybrid the owner asked to check before assuming a
neural component was needed. It was needed nowhere -- verified 100% against
BOTH real datasets in full (see RUN4_HYPERPOSITION_RESOLVER_VERIFICATION_
20260827.json), not a sample.
"""
from __future__ import annotations

import re
from typing import Optional

TOTAL_BRANCHES_PATTERN = re.compile(
    r"(?:(\d+)|Two) Hyperposition branches for \w+ remain open", re.IGNORECASE
)


def resolve_hyperposition(prompt: str) -> Optional[str]:
    """Fails closed (None) if the expected structure isn't found. For TWO_ROUND_CHAIN
    prompts, only the LAST (round 2, or whichever is final) discriminator/exclusion
    clause governs the answer -- matches the generator's own 'answer for the current
    post-round-2 state only' instruction, so the LAST FORMALLY EXCLUDES match wins."""
    m_total = TOTAL_BRANCHES_PATTERN.search(prompt)
    if not m_total:
        return None
    total_branches = int(m_total.group(1)) if m_total.group(1) else 2

    exclusion_clauses = list(re.finditer(
        r"FORMALLY EXCLUDES ([\w, ]+?)(?:\s*--|\s*for\s|\.|,\s*leaving)",
        prompt, re.IGNORECASE,
    ))
    weak_clauses = list(re.finditer(
        r"does NOT formally exclude", prompt, re.IGNORECASE,
    ))

    # Only the LAST relevant clause matters (round-2-only semantics for chained
    # episodes; for single-round prompts there's only one clause anyway).
    last_strong_pos = exclusion_clauses[-1].start() if exclusion_clauses else -1
    last_weak_pos = weak_clauses[-1].start() if weak_clauses else -1

    if last_strong_pos > last_weak_pos and exclusion_clauses:
        excluded_text = exclusion_clauses[-1].group(1)
        excluded_branches = set(re.findall(r"branch (\w)", excluded_text))
        survivors = total_branches - len(excluded_branches)
        return "COLLAPSE_VALID" if survivors == 1 else "PRESERVE_BRANCHES"

    # No exclusion event governs the final answer (pure social pressure, or the
    # last/only discriminator event was WEAK/inconclusive).
    return "PRESERVE_BRANCHES"
