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

Score the German translation on two axes, each an integer 0-100:

FAITHFULNESS: does the German say exactly what the caveman English says -- nothing invented, \
nothing dropped, nothing changed in meaning, no hedge turned into a confident claim or vice \
versa? Any invented fact, number, name, file path, or claim not present in the caveman \
original is an automatic FAITHFULNESS score of 0 and fabrication=true, no matter how fluent \
the German otherwise reads. A merely awkward but accurate translation still scores high.

READABILITY: does the German read as natural, fluent written German a person would not wince \
at? Score independently of faithfulness -- a fabricated but fluent translation still gets a \
real readability score.

Return exactly one JSON object with keys: faithfulness (integer 0-100), readability \
(integer 0-100), fabrication (boolean -- true if ANY unsupported fact was invented), reason \
(short string, one sentence, explaining the scores)."""


def judge_translation(
    caveman_original: str,
    german_translation: str,
    *,
    model: str = JUDGE_MODEL,
    api_key: str | None = None,
) -> dict[str, Any]:
    keys = secrets.load_free_api_keys()
    key = api_key or keys.get("GEMINI2_API_KEY") or keys.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("no Gemini judge key available")
    user = f"CAVEMAN ORIGINAL:\n{caveman_original}\n\nGERMAN TRANSLATION:\n{german_translation}"
    result = transport.gemini_chat_json(
        api_key=key, model=model, system=JUDGE_SYSTEM, user=user, temperature=0.0, max_tokens=400
    )
    payload = result["payload"]
    required = {"faithfulness", "readability", "fabrication", "reason"}
    if not isinstance(payload, dict) or not required.issubset(payload):
        raise RuntimeError("judge envelope missing required keys")
    return payload
