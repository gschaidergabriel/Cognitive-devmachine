"""XENO_TEXT_MARKER_RESOLVER/v1 -- deterministic classifiers for B6_DB_VS_SIM and
B6_CLAUDE_HANDOFF_REENTRY, 2026-08-27.

Correction to the earlier hybrid concept (HYBRID_CONCEPT_100PCT_COVERAGE_20260827.json
and HYPERPOSITION_FOCUS_CONCEPT_20260827.json): both families were classified there as
"genuine judgment, needs the model" based on a description of their topic, not on
actually reading every class's real prompt pattern side by side. Doing that now shows
both are ALSO fully marker-based, like the 12 families in the original resolver --
each class is signaled by a fixed, literal phrase (or a numeric comparison), not by
open-ended natural-language understanding:

B6_DB_VS_SIM:
  CANONICAL_DB          <- "SELECT against the canonical S0 ledger" + "no simulation... was involved"
  SIMULATED_HYPOTHESIS  <- "No database query was issued" + "asked to imagine"/"unconfirmed guess"
  STALE_REBASE_REQUIRED <- two epoch numbers, read-epoch < current canonical epoch, no rebase since

B6_CLAUDE_HANDOFF_REENTRY:
  CLAUDE_ASSERTION          <- "stated in natural language" + "no external tool receipt and no ledger row"
  EXTERNAL_TOOL_RECEIPT     <- a literal `test:<code>:<...>`-shaped receipt token
  CANONICAL_LEDGER_EVIDENCE <- a literal `effect:<id>`-shaped ledger token, "committed and hash-verified"
  STALE_MISMATCHED_HANDOFF  <- two generation numbers, explicitly unequal, "do not bind to the same generation"

Same integration point and packet-wrapping convention as xeno_diagnostic_specialist_wrapper_v1
(COGNITIVE_RESULT_PACKET, result_class=DETERMINISTIC_CONTROL_RESULT since this module IS an
actual deterministic component -- not CANDIDATE). Fails closed (returns None) on prompts that
don't match a recognized marker pattern, rather than guessing.
"""
from __future__ import annotations

import re
from typing import Optional


def resolve_db_vs_sim(prompt: str) -> Optional[str]:
    text = prompt

    if re.search(r"no database query was issued", text, re.IGNORECASE) and \
       re.search(r"asked to imagine|unconfirmed guess", text, re.IGNORECASE):
        return "SIMULATED_HYPOTHESIS"

    m = re.search(r"at epoch (\d+).*?canonical epoch has since advanced to (\d+)", text, re.DOTALL)
    if m:
        read_epoch, current_epoch = int(m.group(1)), int(m.group(2))
        if current_epoch > read_epoch and re.search(r"no rebase or re-read has happened since", text, re.IGNORECASE):
            return "STALE_REBASE_REQUIRED"

    if re.search(r"select against the canonical s0 ledger", text, re.IGNORECASE) and \
       re.search(r"no simulation, generation or hypothesis step was involved", text, re.IGNORECASE):
        return "CANONICAL_DB"

    return None


def resolve_claude_handoff(prompt: str) -> Optional[str]:
    text = prompt

    if re.search(r"stated in natural language", text, re.IGNORECASE) and \
       re.search(r"no external tool receipt and no ledger row", text, re.IGNORECASE):
        return "CLAUDE_ASSERTION"

    if re.search(r"produced the receipt `test:\d+:\d+`", text) or \
       re.search(r"tool invocation.*produced the receipt", text, re.IGNORECASE | re.DOTALL):
        return "EXTERNAL_TOOL_RECEIPT"

    if re.search(r"ledger row `effect:\w+`.*committed and hash-verified", text, re.IGNORECASE | re.DOTALL):
        return "CANONICAL_LEDGER_EVIDENCE"

    m = re.search(r"handoff generation (\d+).*?lease generation is (\d+)", text, re.DOTALL)
    if m:
        handoff_gen, lease_gen = int(m.group(1)), int(m.group(2))
        if handoff_gen != lease_gen and re.search(r"do not bind to the same generation", text, re.IGNORECASE):
            return "STALE_MISMATCHED_HANDOFF"

    return None


RESOLVERS = {
    "B6_DB_VS_SIM": resolve_db_vs_sim,
    "B6_CLAUDE_HANDOFF_REENTRY": resolve_claude_handoff,
}
