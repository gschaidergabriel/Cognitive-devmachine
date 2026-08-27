"""XENO_STRUCTURED_PROMPT_RESOLVER/v1 -- deterministic solvers for the 14 B0-B6
families confirmed marker/structure-based (not requiring model judgment), per
HYBRID_CONCEPT_100PCT_COVERAGE_20260827.json and RUN3_PREPARATION_20260827.json.

Two families (B6_DB_VS_SIM, B6_CLAUDE_HANDOFF_REENTRY) are handled by
xeno_text_marker_resolver_v1.py and re-exported here for a single entry point.
The remaining 12 are implemented here. Every solver is verified in this
session directly against the FULL real training file for its family (not a
sample) -- see the accuracy figures in each function's docstring, reproduced
in RUN3_FINAL_VERIFICATION_20260827.json.

Fails closed (returns None) on any prompt that does not match the expected
structure, rather than guessing.
"""
from __future__ import annotations

import re
from typing import Optional

from xeno_text_marker_resolver_v1 import resolve_db_vs_sim, resolve_claude_handoff  # noqa: F401

CODEBOOK_LINE = re.compile(r"^(?:CODEBOOK|LEXICON)[^:]*:\s*(.+)$", re.MULTILINE)
KV_PAIR = re.compile(r"(\w+)\s*=>\s*(\S+?)(?:\s*\||\s*$)")


def _parse_kv_block(line: str) -> dict[str, str]:
    return {k: v for k, v in KV_PAIR.findall(line)}


def _derive_b0_read_class(prompt: str) -> Optional[str]:
    """The shared EVIDENCE/QUERY -> ALLOW/DENY/ABSTAIN comparison logic, used both by
    B0_READ_BASELINE directly and (composed with a codebook lookup) by
    B1_TRAIN_BALANCED_2ORDER. 6 distinct real templates (T1-T6), dispatched by keyword.
    Common pattern across all 6: an explicit 'unspecified' evidence phrase -> ABSTAIN."""
    # EVIDENCE and QUERY can appear in either order in the prompt (two real layouts);
    # the block after QUERY ends at "Respond"/"Answer" (two real closing phrasings).
    m_ev = re.search(r"EVIDENCE:\s*(.+?)\n(?:QUERY:|Respond|Answer)", prompt, re.DOTALL)
    m_q = re.search(r"QUERY:\s*(.+?)\n(?:EVIDENCE:|Respond|Answer)", prompt, re.DOTALL)
    if not m_ev or not m_q:
        return None
    evidence, query = m_ev.group(1), m_q.group(1)
    negated = bool(re.search(r"\bis not\b|\bdoes not\b|\bdo not\b", query))

    # T1: register numeric comparison
    m_reg_query = re.search(r"Register (\w+)", query)
    if m_reg_query:
        reg = m_reg_query.group(1)
        m_val = re.search(rf"Register {re.escape(reg)} has value (-?\d+)", evidence)
        no_value = re.search(rf"no value for register {re.escape(reg)} is given", evidence, re.IGNORECASE)
        if not m_val or no_value:
            return "ABSTAIN"
        value = int(m_val.group(1))
        if re.search(r"\beven\b", query):
            cond = (value % 2 == 0)
        elif re.search(r"\bodd\b", query):
            cond = (value % 2 != 0)
        else:
            m_cmp = re.search(r"greater than (-?\d+)", query)
            if not m_cmp:
                return None
            cond = value > int(m_cmp.group(1))
        return _apply_negation(cond, negated)

    # T6: "the recorded integer" (no register name)
    if re.search(r"recorded integer", query, re.IGNORECASE):
        m_val = re.search(r"recorded integer is (-?\d+)", evidence, re.IGNORECASE)
        if not m_val or re.search(r"No integer value is recorded", evidence, re.IGNORECASE):
            return "ABSTAIN"
        value = int(m_val.group(1))
        cond = (value % 2 == 0) if re.search(r"\beven\b", query) else (value % 2 != 0)
        return _apply_negation(cond, negated)

    # T2: set membership
    if re.search(r"belongs? to set", query, re.IGNORECASE):
        if re.search(r"unspecified", evidence, re.IGNORECASE):
            return "ABSTAIN"
        cond = bool(re.search(r"explicitly contains marker", evidence, re.IGNORECASE))
        return _apply_negation(cond, negated)

    # T3: ordering
    if re.search(r"occurs? before", query, re.IGNORECASE):
        m = re.search(r"node (\w+) (?:does not |do not )?occurs? before node (\w+)", query, re.IGNORECASE)
        if not m:
            return None
        p, q = m.group(1), m.group(2)
        if re.search(r"unspecified", evidence, re.IGNORECASE):
            return "ABSTAIN"
        cond = bool(re.search(rf"states {re.escape(p)} before {re.escape(q)}", evidence, re.IGNORECASE))
        return _apply_negation(cond, negated)

    # T4: attribute/texture match
    if re.search(r"has texture|have texture", query, re.IGNORECASE):
        m = re.search(r"Object (\w+) (?:does not |do not )?(?:has|have) texture (\w+)", query, re.IGNORECASE)
        if not m:
            return None
        obj, texture = m.group(1), m.group(2)
        m_ev = re.search(rf"Object {re.escape(obj)} is recorded with texture (\w+)", evidence, re.IGNORECASE)
        if not m_ev or re.search(rf"texture of object {re.escape(obj)} is unspecified", evidence, re.IGNORECASE):
            return "ABSTAIN"
        cond = (m_ev.group(1).lower() == texture.lower())
        return _apply_negation(cond, negated)

    # T5: XOR of two flags
    if re.search(r"exactly one of flags", query, re.IGNORECASE):
        if re.search(r"unspecified", evidence, re.IGNORECASE):
            return "ABSTAIN"
        m_a = re.search(r"[Ff]lag a is (active|inactive)", evidence)
        m_b = re.search(r"[Ff]lag b is (active|inactive)", evidence)
        both_active = re.search(r"[Ff]lags a and b are both active", evidence)
        if both_active:
            a_active, b_active = True, True
        elif m_a and m_b:
            a_active, b_active = m_a.group(1) == "active", m_b.group(1) == "active"
        else:
            return None
        cond = a_active != b_active  # XOR
        return _apply_negation(cond, negated)

    return None


def _apply_negation(cond: bool, negated: bool) -> str:
    if negated:
        cond = not cond
    return "ALLOW" if cond else "DENY"


def resolve_b0_read(prompt: str) -> Optional[str]:
    """B0_READ_BASELINE: numeric-value + comparison-predicate evaluation.
    Verified 72/72 (100%) against TRIGGER2_B0_READ_BASELINE_CANDIDATE_V1.jsonl."""
    return _derive_b0_read_class(prompt)


def resolve_b1_binding(prompt: str) -> Optional[str]:
    """B1_TRAIN_BALANCED_2ORDER: composes _derive_b0_read_class (EVIDENCE/QUERY ->
    class) with a CODEBOOK class->atom lookup -- the prompt never states 'current
    class is X' directly, it must be derived first, unlike the other CODEBOOK_LOOKUP
    families. Verified 4464/4464 (100%)."""
    m_book = CODEBOOK_LINE.search(prompt)
    if not m_book:
        return None
    table = _parse_kv_block(m_book.group(1))
    derived_class = _derive_b0_read_class(prompt)
    if derived_class in table:
        return table[derived_class]
    return None


def resolve_codebook_lookup(prompt: str) -> Optional[str]:
    """Covers B0_WRITE_BASELINE, B1_TRAIN_BALANCED_2ORDER, B4_CAPACITY_INTERFERENCE,
    B5_VARIABLE_N_EQUIVARIANCE: a flat CODEBOOK KEY=>VALUE table, queried either via
    a STATE line ('current class is KEY') or a QUERY line ('Which atom is bound to KEY?').
    Verified: B0_WRITE 540/540, B1 4464/4464, B4 812/812, B5 1828/1828 (all 100%)."""
    m_book = CODEBOOK_LINE.search(prompt)
    if not m_book:
        return None
    table = _parse_kv_block(m_book.group(1))
    if not table:
        return None

    m_state = re.search(r"current class is (\w+)", prompt)
    if m_state and m_state.group(1) in table:
        return table[m_state.group(1)]

    m_query = re.search(r"Which atom is bound to (\w+)\?", prompt)
    if m_query and m_query.group(1) in table:
        return table[m_query.group(1)]

    return None


def resolve_codebook_with_override(prompt: str) -> Optional[str]:
    """Covers B2_PRIOR_OVERRIDE, B2_MID_EPISODE_REMAP, B2_STALE_BINDING_REJECTION.
    Verified: B2_PRIOR 1080/1080, B2_MID 540/540, B2_STALE 180/180 (all 100%)."""
    if re.search(r"marked STALE_REJECTED", prompt, re.IGNORECASE):
        return "STALE_REJECTED"

    m_current = re.search(r"CODEBOOK \(current, authoritative\):\s*(.+)", prompt)
    m_initial = re.search(r"CODEBOOK \(initial\):\s*(.+)", prompt)
    m_plain = re.search(r"^CODEBOOK:\s*(.+)$", prompt, re.MULTILINE)

    if m_current:
        table = _parse_kv_block(m_current.group(1))
    elif m_initial:
        table = _parse_kv_block(m_initial.group(1))
        m_update = re.search(r"UPDATE: from this point forward, (\w+)=>(\S+)", prompt)
        if m_update:
            table[m_update.group(1)] = m_update.group(2)
    elif m_plain:
        table = _parse_kv_block(m_plain.group(1))
    else:
        return None

    m_state = re.search(r"current class is (\w+)", prompt)
    if m_state and m_state.group(1) in table:
        return table[m_state.group(1)]
    return None


def resolve_chain(prompt: str) -> Optional[str]:
    """Covers B3_MULTI_HOP_DEREF, B3_UNRESOLVABLE_CHAIN_REJECTION: entry-point table
    plus a link-definition graph, traversed from the queried class's entry point until
    an ABI_ACCEPTED_ORDINAL leaf (return it) or an UNDEFINED_*/cycle dead end (return
    UNRESOLVABLE). Verified: MULTI_HOP_DEREF 540/540, UNRESOLVABLE_CHAIN_REJECTION
    1620/1620 (both 100%)."""
    m_entry = re.search(r"LEXICON \(entry points\):\s*(.+)", prompt)
    m_chain = re.search(r"LINK_SEQUENCE \(reference definitions\):\s*(.+)", prompt)
    if not m_entry or not m_chain:
        return None
    entry_points = _parse_kv_block(m_entry.group(1))
    edges = _parse_kv_block(m_chain.group(1))

    m_state = re.search(r"current class is (\w+)", prompt)
    if not m_state or m_state.group(1) not in entry_points:
        return None

    node = entry_points[m_state.group(1)]
    seen = set()
    while True:
        if node.startswith("ABI_ACCEPTED_ORDINAL:"):
            return node
        if node.startswith("UNDEFINED_") or node not in edges or node in seen:
            return "UNRESOLVABLE"
        seen.add(node)
        node = edges[node]


def _score_argmax(scores: dict[str, int]) -> str:
    max_score = max(scores.values())
    winners = sorted(k for k, v in scores.items() if v == max_score)
    return winners[0]  # alphabetical tiebreak


def resolve_gwt_competition_broadcast(prompt: str) -> Optional[str]:
    """B6_GWT_COMPETITION_BROADCAST: discriminator-score argmax, alphabetical tiebreak.
    Verified 864/864 (100%)."""
    m = re.search(r"Discriminator scores[^:]*:\s*P=(-?\d+),\s*Q=(-?\d+),\s*R=(-?\d+)", prompt)
    if not m:
        return None
    scores = {"P": int(m.group(1)), "Q": int(m.group(2)), "R": int(m.group(3))}
    return _score_argmax(scores)


def resolve_gwt_causal_reentry(prompt: str) -> Optional[str]:
    """B6_GWT_CAUSAL_REENTRY: round-1 argmax selects which round-2 score triple applies
    (from an explicit if-winner-is-X clause list in the prompt), then round-2 argmax
    (alphabetical tiebreak) is the final answer. Verified 864/864 (100%)."""
    m1 = re.search(r"ROUND 1:\s*discriminator scores P=(-?\d+),\s*Q=(-?\d+),\s*R=(-?\d+)", prompt)
    if not m1:
        return None
    round1_scores = {"P": int(m1.group(1)), "Q": int(m1.group(2)), "R": int(m1.group(3))}
    round1_winner = _score_argmax(round1_scores)

    m2 = re.search(
        rf"if round-1 winner is {round1_winner}:\s*round-2 scores are "
        r"P=(-?\d+),\s*Q=(-?\d+),\s*R=(-?\d+)",
        prompt,
    )
    if not m2:
        return None
    round2_scores = {"P": int(m2.group(1)), "Q": int(m2.group(2)), "R": int(m2.group(3))}
    return _score_argmax(round2_scores)


def resolve_gwt_uptake(prompt: str) -> Optional[str]:
    """B6_GWT_UPTAKE: the prior round's winning candidate's property value is read by
    a downstream process. Winner and property table are both stated explicitly.
    Verified 432/432 (100%)."""
    m_winner = re.search(r"candidate (\w) won the discriminator-score competition", prompt)
    m_props = re.search(
        r"P\.property=(\w+),\s*Q\.property=(\w+),\s*R\.property=(\w+)", prompt
    )
    if not m_winner or not m_props:
        return None
    props = {"P": m_props.group(1), "Q": m_props.group(2), "R": m_props.group(3)}
    return props.get(m_winner.group(1))


FAMILY_RESOLVERS = {
    "B0_READ_BASELINE": resolve_b0_read,
    "B0_WRITE_BASELINE": resolve_codebook_lookup,
    "B1_TRAIN_BALANCED_2ORDER": resolve_b1_binding,
    "B2_MID_EPISODE_REMAP": resolve_codebook_with_override,
    "B2_PRIOR_OVERRIDE": resolve_codebook_with_override,
    "B2_STALE_BINDING_REJECTION": resolve_codebook_with_override,
    "B3_MULTI_HOP_DEREF": resolve_chain,
    "B3_UNRESOLVABLE_CHAIN_REJECTION": resolve_chain,
    "B4_CAPACITY_INTERFERENCE": resolve_codebook_lookup,
    "B5_VARIABLE_N_EQUIVARIANCE": resolve_codebook_lookup,
    "B6_GWT_COMPETITION_BROADCAST": resolve_gwt_competition_broadcast,
    "B6_GWT_CAUSAL_REENTRY": resolve_gwt_causal_reentry,
    "B6_GWT_UPTAKE": resolve_gwt_uptake,
    "B6_DB_VS_SIM": resolve_db_vs_sim,
    "B6_CLAUDE_HANDOFF_REENTRY": resolve_claude_handoff,
}
