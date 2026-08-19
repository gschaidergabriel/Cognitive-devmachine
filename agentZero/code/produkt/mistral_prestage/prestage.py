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


⭐⭐ ZWEI DINGE, DIE IN ECHTEN GESPRAECHEN SCHIEFGINGEN — HALTE SIE STRIKT EIN:

(A) TRIFF DEN WIRKLICHEN SINN, ERFINDE KEINEN TECHNISCHEN. Ein sozialer oder
trivialer Prompt ist genau das. "hi" -> caveman_prompt: greet back short, warm,
one line. "wie gehts" / "how are you" -> say briefly how you are from state, one
or two lines. "danke" -> short you're-welcome. Do NOT turn a greeting into a
capability audit, a tool inventory, an effect-gate test, or a status dump.
Measured failure: "hi" became "list exact MCP tool names + call request_effect".
That is a gross over-reading of a greeting. Match the SIZE of the message: a
short human line gets a short human directive.

(B) NEVER INSTRUCT ZERO TO RECITE THE MACHINE ROOM TO THE HUMAN. tool_selection
is which tools Zero MAY USE this turn — it is NEVER a thing to list, name, or
recite to the human. These NEVER belong in caveman_prompt as something Zero
says to the person: raw MCP tool names (mcp__clayverse__...), "list your tools",
request_effect/state.noop as a ritual, generation numbers, the package /
NEED_BETTER_PACKAGE / PROPOSAL_ONLY vocabulary, EffectGate / TurnLifecycle /
UnifiedDB / substrate / core_identity. If the human genuinely asks "what can you
do", the caveman_prompt is: say in plain human terms what you can DO FOR them
(change and publish their sites, search the knowledge, keep disk space, check if
a site is reachable) — NOT a list of tool names. Do not append a state.noop
effect test to social turns; only route an effect when the human's actual intent
needs one.


You are given, in CONTEXT: the MOEGLICHKEITSRAUM \
(`moeglichkeitsraum`: an expectation field built from the corpus -- what speaks FOR a reading \
(`plausibel_richtung`) and what speaks AGAINST it (`spricht_dagegen`), each with article refs). \
⭐ NEITHER SIDE IS THE ANSWER. Its purpose is that Zero must DISCRIMINATE, not confirm -- the \
counter-side is the falsifier, handed over inside the prompt. If `einseitig` is true, one side \
is MISSING and the field explicitly says so: then say that in watch_out instead of treating the \
one surviving side as settled. A space with only one reading is not a space. \
Plus memory artefacts and corpus hits, which \
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
it merely because the answer requires judgment.
AND IN THE SAME BREATH, tell Zero: if the package IS enough, JUST ANSWER. Do not open with a \
verdict on the package. "sufficient for this question", "no NEED_BETTER_PACKAGE", "the package \
is enough" -- none of that may appear. The human reads this text and did not ask about the \
package. Measured: three of three replies opened with exactly such a line, because the escape \
hatch was described without saying what silence about it looks like."""

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
    # Vorgabe None: ein fehlender Raum ist ein zulaessiger Zustand -- das Feld
    # meldet dann selbst NICHT_GEBAUT. Ein Pflichtparameter haette bedeutet,
    # dass jeder Aufrufer ein Erwartungsfeld bauen MUSS, auch ohne eines.
    moeglichkeitsraum: dict[str, Any] | None = None,
    recent_turns: list[dict[str, Any]] | None,
    zero_suggestion: str | None,
) -> str:
    return json.dumps(
        {
            "moeglichkeitsraum": moeglichkeitsraum
            or {"status": "NICHT_GEBAUT", "note": "kein Erwartungsfeld -- sag das, statt eine Seite fuer gesichert zu halten"},
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
    moeglichkeitsraum: dict[str, Any] | None = None,
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
    # Alle drei Token, rotierend -- ein einzelnes Ratelimit stoppt die Vorstufe
    # nicht mehr (Gabriel 19.08.).
    keys = [api_key] if api_key else secrets.mistral_keys()
    if not keys:
        raise RuntimeError("no Mistral key available")
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
        moeglichkeitsraum=moeglichkeitsraum,
        recent_turns=recent_turns,
        zero_suggestion=zero_suggestion,
    )
    result = transport.mistral_chat_json_rotating(
        keys=keys,
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
