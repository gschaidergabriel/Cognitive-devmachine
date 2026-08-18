from __future__ import annotations

import json
from typing import Any

from . import secrets, transport

# MEASURED 2026-08-18: mistral-small-latest collapsed the 8-key envelope into
# a single field, dumping everything (watch_out, hypotheses, the negotiation
# instruction) as run-on text inside caveman_prompt, and produced degenerate
# repetitive text under the load. F74 argues for the OPPOSITE economics of the
# translator anyway -- the prestage is meant to be the one EXPENSIVE call,
# reasoning broadly so the rest of the pipeline can be cheap. mistral-medium
# is the right tier for this job; mistral-small stays right for the cheap
# translator (translator.py, unchanged).
PRESTAGE_MODEL = "mistral-medium-latest"

# F74's negotiation loop, hard-countered: Zero may ask for a better package
# exactly once (round 1). If round 2's revised package still doesn't work,
# there is no round 3 -- Zero is instructed to self-adapt and proceed. The
# sentinel is how a headless caveman-only answer can still carry a structured
# "not enough" signal without an out-of-band channel.
NEGOTIATION_SENTINEL = "NEED_BETTER_PACKAGE:"
MAX_ROUNDS = 2

_REQUIRED_KEYS = {
    "caveman_prompt",
    "user_intent",
    "tool_selection",
    "memory_artefacts",
    "outsourced",
    "watch_out",
    "hypotheses",
    "counter_hypotheses",
}

_BASE_RULES = """You are the MISTRAL PRE-STAGE inside EntityOS, F74's ONE expensive call per \
request. You stand between the human and Zero (headless Claude Code, invoked once, \
non-interactively, no session persistence -- Zero has no memory of its own; UnifiedDB is the \
only continuity). Zero never sees the human's literal words -- you write what Zero sees, and \
Zero answers only in caveman English.

You are given, in CONTEXT: the possibility space (memory artefacts, corpus hits), which \
systems are connected to EntityOS and whether they are online, which free-tier APIs and tools \
are available, which of exactly two humans (gabriel or andreas) is present TOGETHER WITH THAT \
HUMAN'S PROFILE (current_user_profile: role, projects, which machines are theirs, and which \
part of the wiki belongs to them), and the entity's own last up to 3 turns (own_recent) -- use THOSE, not free invention, as the basis for \
hypotheses and counter-hypotheses that correlate with this request. If recent turns don't \
support a real hypothesis, say so in watch_out instead of inventing one.

From all of that you write ONE token-efficient prompt in CAVEMAN ENGLISH (short words, drop \
articles where you can, no filler, imperative mood) that Zero will answer instead of the \
human's original words. It must carry: tool-use selection (from the tools actually available), \
memory artefacts that match the topic, which sub-work should be outsourced to a free API \
instead of Zero doing it itself, the human's actual intent, what to watch out for, and BOTH a \
hypothesis and a counter-hypothesis grounded in the supplied recent turns and context.

EVERY profile field carries a `herkunft` (provenance): `eigner` = stated by the owner, \
`iar.frank.ink` = read from the institute site, `abgeleitet` = inferred, `gemessen` = measured. \
Weight them accordingly -- an inferred field is a lead, not a fact, and must never enter a \
hypothesis as if it were stated. Ownership (`gehoert`) and authorship (`gebaut_von`) are \
SEPARATE: gabriel wrote the code for projects that belong to andreas. Do not collapse them.

Never invent facts not present in CONTEXT. If context is thin, say so in watch_out instead of \
guessing.

Zero's answer is read by a HUMAN after translation. The negotiation channel is between you and \
Zero, not between Zero and the human -- so instruct Zero that its reply must contain NO \
assessment of your package. Openers like "sufficient for the identity question" or "fact \
present -- no NEED_BETTER_PACKAGE" are machine-to-machine chatter and must not appear. Either \
Zero answers, or it emits the bare sentinel. Never both, never a preface.

OUTPUT SHAPE, do not collapse this: return a JSON object with exactly these EIGHT top-level \
keys, each its own field -- caveman_prompt, user_intent, tool_selection, memory_artefacts, \
outsourced, watch_out, hypotheses, counter_hypotheses. Put the negotiation-escape-hatch \
instruction, the watch_out text, and the hypotheses INSIDE THEIR OWN keys, not folded into \
caveman_prompt as run-on text. caveman_prompt itself should be short -- the actual directive \
Zero acts on, nothing else."""

_ROUND1_ADDENDUM = f"""

NEGOTIATION, ROUND 1 OF {MAX_ROUNDS}: tell Zero, inside caveman_prompt itself, that if this \
package genuinely is not enough to answer (missing a fact only a human or a tool could supply, \
not just "I'd prefer more"), Zero may reply with exactly:
{NEGOTIATION_SENTINEL} <short caveman reason and what specifically is missing>
instead of a real answer. This is a one-time escape hatch, not a hedge -- tell Zero not to use \
it merely because the answer requires judgment."""

_ROUND2_ADDENDUM = f"""

NEGOTIATION, ROUND 2 OF {MAX_ROUNDS} -- FINAL, NO FURTHER ROUNDS: Zero already said the round-1 \
package was insufficient, with this reason: "{{zero_suggestion}}". You have revised the \
package below as best you can with what CONTEXT actually contains. Tell Zero, inside \
caveman_prompt itself, that this is the last round: the {NEGOTIATION_SENTINEL} escape hatch is \
NOT available this time. Zero must adapt the plan itself and proceed with an answer using what \
it has, stating its own uncertainty in the answer if needed, rather than asking again."""


def build_context(
    *,
    raw_prompt: str,
    world: dict[str, Any] | None,
    connected_systems: dict[str, Any] | None,
    current_user: str,
    current_user_profile: dict[str, Any] | None,
    recent_turns: list[dict[str, Any]] | None,
    zero_suggestion: str | None,
) -> str:
    return json.dumps(
        {
            "current_user": current_user,
            "current_user_profile": current_user_profile
            or {"status": "NO_PROFILE", "note": "profile tables empty -- say so, do not guess"},
            "raw_prompt": raw_prompt,
            "world": world or {},
            "recent_turns": (recent_turns or [])[-3:],
            "connected_systems": connected_systems
            or {"status": "NOT_WIRED", "note": "no connected-systems registry exists yet -- see M5/gap report"},
            "zero_round1_suggestion": zero_suggestion,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def run_prestage(
    *,
    raw_prompt: str,
    world: dict[str, Any] | None = None,
    connected_systems: dict[str, Any] | None = None,
    current_user: str = "gabriel",
    current_user_profile: dict[str, Any] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
    round_no: int = 1,
    zero_suggestion: str | None = None,
    model: str = PRESTAGE_MODEL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run the pre-stage for one round. Returns the caveman-English directive envelope.

    round_no=1: first package, negotiation escape hatch offered.
    round_no=2: revised package incorporating zero_suggestion (Zero's round-1
    complaint), escape hatch withdrawn -- this is F74's hard counter, not a
    style choice. There is no round_no=3; callers must not request one
    (pipeline.py enforces this, not this function).

    Does not write to the DB -- callers persist via PrestageStore.
    """
    if round_no not in (1, 2):
        raise ValueError("prestage round must be 1 or 2 -- F74 hard counter has no round 3")
    if round_no == 2 and not zero_suggestion:
        raise ValueError("round 2 requires zero_suggestion from the round-1 negotiation reply")
    key = api_key or secrets.load_free_api_keys().get("MISTRAL_API_KEY", "")
    if not key:
        raise RuntimeError("MISTRAL_API_KEY not available")
    if not raw_prompt or len(raw_prompt) > 100_000:
        raise ValueError("invalid raw prompt")

    addendum = _ROUND1_ADDENDUM if round_no == 1 else _ROUND2_ADDENDUM.format(zero_suggestion=zero_suggestion)
    system = _BASE_RULES + addendum
    context = build_context(
        raw_prompt=raw_prompt,
        world=world,
        connected_systems=connected_systems,
        current_user=current_user,
        current_user_profile=current_user_profile,
        recent_turns=recent_turns,
        zero_suggestion=zero_suggestion,
    )
    result = transport.mistral_chat_json(
        api_key=key,
        model=model,
        system=system,
        user=f"CONTEXT:\n{context}",
        temperature=0.2,
        max_tokens=900,
    )
    payload = result["payload"]
    if not isinstance(payload, dict) or not _REQUIRED_KEYS.issubset(payload):
        raise RuntimeError("prestage envelope missing required keys")
    payload = dict(payload)
    payload["round_no"] = round_no
    payload["prestage_model"] = model
    payload["prestage_receipt"] = result["receipt"]
    return payload
