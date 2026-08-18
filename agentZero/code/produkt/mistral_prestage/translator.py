from __future__ import annotations

from typing import Any

from . import secrets, transport

TRANSLATOR_MODEL = "mistral-small-latest"

# prompt_version tag persisted with every eval run, bumped on any system-prompt
# change so mv_eval_runs stays comparable across iterations.
PROMPT_VERSION = "v4"

TRANSLATOR_SYSTEM = """You translate short caveman-English text (written by an AI entity \
called Zero) into fluent, natural German for a human reader. The human never sees the \
caveman original -- your German IS what they read, so treat every word as load-bearing. \
Rules, in strict priority order:

1. FAITHFULNESS beats everything else. Translate only what is there. Never add a fact, \
   number, file path, table/service/table name, or claim that is not in the caveman text. \
   Never drop a fact that is there. Never resolve a hedge ("maybe", "dunno", "guess") into a \
   confident claim -- keep the same degree of certainty.
2. NEVER substitute one name for another one you believe is "really" meant, even if you are \
   confident you know the real-world referent. If the caveman text says "claude", write \
   "claude" -- do not silently correct it to "Zero" or any other name you infer from \
   background knowledge. The words you were given are the only truth; your own knowledge of \
   the system is not a license to "fix" them.
3. Any lowercase, no-space token that is not an ordinary dictionary word (e.g. "leihmich", \
   "wiki.db", "entityos", "clayverse", a file path, a table name) is an identifier/proper \
   noun, not a sentence to parse. Copy it through literally. Do NOT reinterpret it as if it \
   were ordinary words that happen to look similar (e.g. "leihmich" is a product/site name, \
   never the imperative "leih mich" / "lend me").
4. Numbers, percentages, and quantities are copied through exactly, in a natural but literal \
   German phrasing (e.g. "87 Tabellen und 19 Objekte", not "durchgehen" or other awkward \
   verbs that risk implying something beyond pass-through accuracy).
5. If the caveman text is ambiguous, keep the German equally ambiguous -- do not silently \
   pick one reading, and do not add connecting logic, reasons, or sequencing that is not \
   explicitly stated (e.g. do not turn a bare list of two facts into a "before X, Y happens" \
   causal chain unless the caveman text said so).
6. Within those constraints, and only within them, make it read like natural written German, \
   not a robotic word-for-word crib. Contractions and terse caveman style should become \
   normal grammatical German, not stay clipped.

Return exactly one JSON object with a single key: german (string, the German translation \
only, nothing else)."""


# Gemessen 2026-08-18 (zweimal live aufgetreten, dreimal live reproduziert):
# enthaelt der caveman-Text einen Markdown-Codespan, der selbst ein zitiertes
# JSON-Fragment mit doppelten Anfuehrungszeichen traegt (z.B. `"feld": "wert"`),
# bricht Mistrals JSON-Modus zuverlaessig genau nach dem oeffnenden Backtick
# ab. finish_reason bleibt dabei "stop" (kein Token-Budget-Abriss --
# completion_tokens lag weit unter max_tokens=1200) und das JSON selbst bleibt
# GUELTIG -- nur der Inhalt endet mitten im Satz. transport.py kann das nicht
# sehen: es bekommt gueltiges JSON und liefert es klaglos aus. Die Unterschrift
# ist eine ungerade Zahl Backticks im Ergebnis (ein Codespan wurde geoeffnet,
# nie geschlossen).
MAX_UEBERSETZUNGSVERSUCHE = 3


def _wirkt_abgeschnitten(text: str) -> bool:
    """Traegt das gemessene Abbruchmuster: ein ungeschlossener Inline-Codespan."""
    return text.count("`") % 2 == 1


def translate_to_german(
    caveman_text: str,
    *,
    model: str = TRANSLATOR_MODEL,
    api_key: str | None = None,
) -> dict[str, Any]:
    key = api_key or secrets.load_free_api_keys().get("MISTRAL_API_KEY", "")
    if not key:
        raise RuntimeError("MISTRAL_API_KEY not available")
    if not caveman_text or len(caveman_text) > 20_000:
        raise ValueError("invalid caveman text")
    for versuch in range(1, MAX_UEBERSETZUNGSVERSUCHE + 1):
        result = transport.mistral_chat_json(
            api_key=key,
            model=model,
            system=TRANSLATOR_SYSTEM,
            user=f"CAVEMAN TEXT:\n{caveman_text}",
            temperature=0.1,
            max_tokens=1200,
        )
        payload = result["payload"]
        if not isinstance(payload, dict) or not isinstance(payload.get("german"), str) or not payload["german"]:
            raise RuntimeError("translator envelope missing 'german'")
        german = payload["german"]
        if not _wirkt_abgeschnitten(german):
            return {
                "caveman_original": caveman_text,
                "german_translation": german,
                "translator_model": model,
                "translator_receipt": result["receipt"],
            }
        # Nicht still weiterreichen: ein Satz, der mitten im Wort endet, ist
        # keine Uebersetzung. Naechster Versuch -- eine neue Anfrage, nicht
        # dieselbe Antwort nochmal.
    # Alle Versuche mit demselben Abbruchmuster: fuer bestimmte Quelltexte
    # (verschachtelte Anfuehrungszeichen in einem Codespan) ist das kein
    # Zufallsausfall, der ein Retry allein loest -- gemessen dreimal in Folge.
    # Laut scheitern statt eine abgeschnittene Antwort als Uebersetzung
    # durchzureichen.
    raise RuntimeError(
        f"translator: {MAX_UEBERSETZUNGSVERSUCHE} Versuche, jedesmal ein "
        "ungeschlossener Codespan (Abbruch nach Backtick, finish_reason='stop') "
        "-- abgeschnittene Ausgabe verworfen statt als Uebersetzung durchgereicht"
    )
