from __future__ import annotations

from typing import Any

from . import secrets, transport

# Deliberately a different provider family than the Mistral translator, so
# judge and judged never share a model / never share failure modes.
# gemini-flash-latest resolves to gemini-3.7-flash, whose free tier is
# GenerateRequestsPerDayPerProjectPerModel-FreeTier = 20/day (measured
# 2026-08-18 via the live 429 body) -- far too small for a 50-item eval.
# gemini-3.5-flash-lite has a workable free daily quota (measured: survived
# a 50-call eval run same day).
JUDGE_MODEL = "gemini-3.5-flash-lite"

JUDGE_SYSTEM = """You are an independent quality judge. You receive a short CAVEMAN ENGLISH \
original (written by an AI) and a GERMAN translation someone else produced from it. You did \
NOT write either one.

Score the German translation on three axes, each an integer 0-100:

FAITHFULNESS: does the German say exactly what the caveman English says -- nothing invented, \
nothing dropped, nothing changed in meaning, no hedge turned into a confident claim or vice \
versa? Any invented fact, number, name, file path, or claim not present in the caveman \
original is an automatic FAITHFULNESS score of 0 and fabrication=true, no matter how fluent \
the German otherwise reads. A merely awkward but accurate translation still scores high.

READABILITY: does the German read as natural, fluent written German a person would not wince \
at -- correct grammar, sensible word order, no dangling clauses? Score independently of \
faithfulness -- a fabricated but fluent translation still gets a real readability score. A \
text can be grammatically flawless and still score low here if it is stilted or unnatural \
(see MENSCHLICHKEIT below); readability is about correctness, not warmth.

MENSCHLICHKEIT (human/warm tone): does this read like a person wrote it -- warm, natural, the \
way a knowledgeable human would actually say it out loud to someone they respect -- or does it \
read like a machine-literal crib: clipped, robotic, word-for-word from the English, padded \
with stiff connector phrases ("es ist zu beachten, dass", "im Hinblick auf"), or unnaturally \
formal for the register of the content? A terse caveman original translated into equally terse \
but natural, idiomatic German sentences scores HIGH here even though it is short -- brevity is \
not robotic, stiffness is. Score this axis independently of faithfulness: a translation can be \
100% faithful and still sound stiff (medium menschlichkeit), or read warm and natural while \
also being unfaithful (low faithfulness, but menschlichkeit is scored on tone alone, not on \
whether the content is invented).

If a line "INTENDED TONE" is supplied below, ALSO score a fourth axis, integer 0-100:

TON_PASSEND: the translator was given a real, measured operational-tone hint (ruhig=calm, \
angespannt=tense, or no hint at all) and told to reflect it ONLY in word choice/warmth, never \
in content. Score whether the German's warmth register plausibly matches that hint WITHOUT \
adding, dropping, or exaggerating any fact, warning, or claim to do so. A translation that \
ignores the hint entirely (reads exactly as neutral as it would without one) scores medium, \
not zero -- Rule "when in doubt, neutral" makes that a safe outcome, not a failure. A \
translation that invents new content (e.g. adds an unsupported warning to sound "tense") \
scores 0 here AND must also be marked fabrication=true above, regardless of the hint.

Return exactly one JSON object with keys: faithfulness (integer 0-100), readability \
(integer 0-100), menschlichkeit (integer 0-100), fabrication (boolean -- true if ANY \
unsupported fact was invented), reason (short string, one sentence, explaining the scores), \
ton_passend (integer 0-100, or null if no INTENDED TONE line was supplied)."""


def judge_translation(
    caveman_original: str,
    german_translation: str,
    *,
    model: str = JUDGE_MODEL,
    api_key: str | None = None,
    ton_hint: str | None = None,
) -> dict[str, Any]:
    keys = secrets.load_free_api_keys()
    key = api_key or keys.get("GEMINI2_API_KEY") or keys.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("no Gemini judge key available")
    user = f"CAVEMAN ORIGINAL:\n{caveman_original}\n\nGERMAN TRANSLATION:\n{german_translation}"
    if ton_hint:
        # Appended, not woven into the original block: the judge must see this
        # as the SAME real operational-tone line the translator saw (see
        # translator.py's _betriebston_zeile), not as a caveman-content fact.
        user = f"INTENDED TONE: {ton_hint}\n\n{user}"
    result = transport.gemini_chat_json(
        api_key=key, model=model, system=JUDGE_SYSTEM, user=user, temperature=0.0, max_tokens=400
    )
    payload = result["payload"]
    required = {"faithfulness", "readability", "fabrication", "reason"}
    if not isinstance(payload, dict) or not required.issubset(payload):
        raise RuntimeError("judge envelope missing required keys")
    # menschlichkeit is additive (added 2026-08-19, owner request: Zero should
    # sound human/warm, not just faithful+readable). Default to readability
    # rather than raising if an older cached payload lacks it -- the two
    # original axes must keep working even if this one is ever missing.
    payload.setdefault("menschlichkeit", payload.get("readability", 0))
    # ton_passend is null/absent whenever no ton_hint was given -- that is the
    # correct, honest value (nothing to judge), not a defect to paper over.
    payload.setdefault("ton_passend", None)
    return payload
