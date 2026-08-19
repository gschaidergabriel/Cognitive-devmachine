from __future__ import annotations

import re
from typing import Any

from . import secrets, transport
from .prestage import NEGOTIATION_SENTINEL

TRANSLATOR_MODEL = "mistral-small-latest"

# prompt_version tag persisted with every eval run, bumped on any system-prompt
# change so mv_eval_runs stays comparable across iterations.
# v5 (2026-08-19): Maskierung der Maschinenteile + Nachpruefung, siehe unten.
PROMPT_VERSION = "v5"

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

ZUSATZREGELN (gemessen am 2026-08-19 an 26 echten Produktionszuegen):

7. MASKEN. Stellen der Form [[C0]], [[C1]], [[C2]] ... sind bereits ausmaskierte \
   Maschinenteile: Codeabschnitte, Pfade, Bezeichner, Maschinenmarken. Uebernimm jede Maske \
   ZEICHENGENAU und GENAU SO OFT, wie sie im Quelltext steht -- an der inhaltlich passenden \
   Stelle im deutschen Satz. Uebersetze eine Maske nicht, erklaere sie nicht, lass keine weg \
   und erfinde keine neue. Der deutsche Satz wird um die Maske herum gebaut, die Maske selbst \
   bleibt unangetastet. Eine Maske wird NIE ausgelassen -- auch nicht in einer \
   Ueberschrift, einer Tabellenzelle oder einer Aufzaehlung, und auch dann nicht, wenn sie \
   dir wie technischer Ballast vorkommt.
8. MASCHINENMARKEN. Woerter in GROSSBUCHSTABEN_MIT_UNTERSTRICH (z. B. NEED_BETTER_PACKAGE, \
   PROPOSAL_ONLY) sind Signale, die eine MASCHINE liest, keine Woerter. Sie werden nie \
   uebersetzt, nie eingedeutscht, nie umschrieben. "FEHLT BESSERES PAKET" ist keine \
   Uebersetzung von NEED_BETTER_PACKAGE, sondern die Zerstoerung des Signals.
9. BEZEICHNER. snake_case (effect_id, causal_id, session_state), CamelCase (EffectJournal, \
   EffectGate, UnifiedDB), Dateinamen (wiki.db, index.html), Pfade (/var/lib/clay) und alles \
   in `Backticks` werden buchstabengetreu uebernommen -- keine deutsche Fassung, keine \
   Bindestrich-Version. Aus effect_id wird nie "Effekt-ID", aus causal_id nie "Kausal-ID". \
   Ein erklaerendes deutsches Wort darf DANEBEN stehen, ersetzen darf es den Bezeichner nie.

Return exactly one JSON object with a single key: german (string, the German translation \
only, nothing else)."""


# ── Warum es hier eine Maskierung gibt ──────────────────────────────────────
# Gemessen 2026-08-18/19 an uebersetzer_gold.json (26 echte Produktionszuege,
# uebersetzer_messen.py):
#
#   * 6 von 9 durchgefallenen Proben scheiterten NUR daran, dass die
#     Maschinenmarke NEED_BETTER_PACKAGE eingedeutscht wurde. Die Marke wird
#     von pipeline.py maschinell gelesen (Verhandlungsschleife, Runde 1/2) --
#     uebersetzt ist sie nicht mehr auffindbar. Ein Signal, kein Wort.
#   * 2 weitere Proben brachen mitten im Wort ab. Nachgemessen mit zwei
#     unabhaengigen Anfragen je Probe: derselbe Abbruch an derselben Stelle,
#     jedes Mal genau dort, wo ein Markdown-Codespan ein Anfuehrungszeichen
#     traegt (`capabilities: ["state.noop"]`, `"effect_authority": ...`).
#     finish_reason bleibt "stop", das JSON bleibt gueltig -- der Inhalt endet
#     einfach. Das ist KEIN Zufallsausfall und kein Fehlalarm der Sperre:
#     Wiederholen half nachweislich nicht (gleicher request_sha256, gleicher
#     Abbruch). Nur die Ursache half.
#   * 1 Probe verlor einen Bezeichner (effect_id).
#
# Die Antwort auf alle drei: was eine Maschine liest, geht gar nicht erst durch
# das Modell. Codeabschnitte und Maschinenmarken werden vor der Anfrage durch
# [[C<n>]] ersetzt, das Modell uebersetzt nur die Prosa dazwischen, und
# danach werden die Originalteile Zeichen fuer Zeichen wieder eingesetzt. Damit
# kann ein Bezeichner nicht mehr eingedeutscht werden, und das
# Anfuehrungszeichen im Codespan erreicht das Modell nie.
RE_CODEZAUN = re.compile(r"```.*?```", re.DOTALL)
RE_CODESPANNE = re.compile(r"`[^`\n]*`")
# Dieselbe Form wie NEGOTIATION_SENTINEL in prestage.py und wie
# model_authority="PROPOSAL_ONLY" in autonomy_context.py. Bewusst als MUSTER
# und nicht als Liste: eine Liste veraltet, sobald jemand eine neue Marke
# einfuehrt, und schweigt dann still.
RE_MASCHINENMARKE = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
RE_MASKE = re.compile(r"\[\[C\d+\]\]")

# Weiche Nachpruefung (loest einen neuen Versuch aus, verwirft aber nicht):
RE_KENNUNG = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
RE_CAMEL = re.compile(r"\b[A-Za-z]*[a-z][A-Z][A-Za-z]{2,}\b")
RE_PFAD = re.compile(r"(?<![\w\-])(?:~|\.{1,2})?/[\w.\-/]*[\w\-]")
RE_DATEI = re.compile(
    r"\b[\w\-]+\.(?:db|py|json|md|html|css|js|sh|log|txt|yml|yaml|toml|ini|"
    r"conf|sql|jsonl|net|org|at|com|ink|io|de|key|mmdb|env|service|timer)\b")
# Nur Gruppen ab zwei Ziffern: die einstellige Zahl ist im Deutschen zu oft
# ausgeschrieben ("die vierte Ziffer" fuer "the 4th digit"), das gaebe
# Fehlalarm statt Messung.
RE_ZIFFERNGRUPPE = re.compile(r"\d{2,}")
RE_TAUSENDERTRENNER = re.compile(r"(?<=\d)[.,](?=\d{3}\b)")

MAX_UEBERSETZUNGSVERSUCHE = 3


def _wirkt_abgeschnitten(text: str, quelle: str = "") -> bool:
    """Traegt das gemessene Abbruchmuster: ein ungeschlossener Inline-Codespan.

    Der Vergleich mit der Quelle ist der Unterschied zwischen Sperre und
    Fehlalarm: traegt schon der Quelltext eine ungerade Zahl Backticks, ist die
    Unwucht GEERBT und kein Abbruch -- eine gute Uebersetzung darf dafuer nicht
    weggeworfen werden. Neu entstandene Unwucht dagegen ist immer ein Abbruch
    und wird nie durchgelassen.
    """
    if text.count("`") % 2 == 0:
        return False
    return quelle.count("`") % 2 == 0


def _maskiere(text: str) -> tuple[str, dict[str, str]]:
    """Maschinenteile durch [[C<n>]] ersetzen. Reihenfolge: Zaun, Spanne, Marke."""
    karte: dict[str, str] = {}

    def ersetze(treffer: re.Match) -> str:
        roh = treffer.group(0)
        for marke, vorhanden in karte.items():
            if vorhanden == roh:
                return marke  # gleiches Teil, gleiche Maske -- Zaehlprobe bleibt sauber
        marke = f"[[C{len(karte)}]]"
        karte[marke] = roh
        return marke

    maskiert = RE_CODEZAUN.sub(ersetze, text)
    maskiert = RE_CODESPANNE.sub(ersetze, maskiert)
    maskiert = RE_MASCHINENMARKE.sub(ersetze, maskiert)
    return maskiert, karte


def _entmaskiere(text: str, karte: dict[str, str]) -> str:
    for marke, roh in karte.items():
        text = text.replace(marke, roh)
    return text


def _maschinenmarken(text: str) -> list[str]:
    """Alle Signale, die eine Maschine liest -- Muster plus die harte Marke."""
    marken = set(RE_MASCHINENMARKE.findall(text))
    blank = NEGOTIATION_SENTINEL.rstrip(":")
    if blank in text:
        marken.add(blank)
    return sorted(marken)


def _fehlende_marken(quelle: str, deutsch: str) -> list[str]:
    unten = deutsch.lower()
    return [m for m in _maschinenmarken(quelle) if m.lower() not in unten]


def _bezeichner(text: str) -> set[str]:
    gefunden: set[str] = set()
    for muster in (RE_KENNUNG, RE_CAMEL, RE_PFAD, RE_DATEI):
        gefunden |= set(muster.findall(text))
    return gefunden


def _zahlgruppen(text: str) -> set[str]:
    """Zahlen beider Sprachen auf eine Form bringen.

    Deutsch und Englisch tauschen Punkt und Komma (31,557,600 gegen
    31.557.600). Ohne dieses Zusammenziehen meldet die Pruefung Unterschiede,
    die keine sind, und schickt das Modell in sinnlose Wiederholungen.
    """
    zusammen = RE_TAUSENDERTRENNER.sub("", text)
    return {g.lstrip("0") or "0" for g in RE_ZIFFERNGRUPPE.findall(zusammen)}


def _fehlende_bezeichner(quelle: str, deutsch: str) -> list[str]:
    """Was aus der Quelle fehlt UND was im Deutschen dazugekommen ist.

    Die zweite Haelfte ist die Eignerregel "NICHTS erfinden" als Pruefung:
    gemessen 2026-08-19 tippte das Modell in einem von 78 Laeufen eine
    Jahreszahl falsch ab (206 statt 2026) -- eine Zahl, die es in der Quelle
    nicht gibt. Ein zusaetzlicher Versuch kostet wenig, eine erfundene Zahl im
    Text des Menschen kostet viel.
    """
    unten = deutsch.lower()
    fehlt = [b for b in _bezeichner(quelle) if b.lower() not in unten]
    quellzahlen = _zahlgruppen(quelle)
    zielzahlen = _zahlgruppen(deutsch)
    fehlt += sorted(quellzahlen - zielzahlen)
    fehlt += sorted(zielzahlen - quellzahlen)
    return sorted(fehlt)


# Ein deutscher Satz hoert auf einem Schlusszeichen auf. Hoert der Text auf
# einem Wortzeichen auf, ist er mit hoher Wahrscheinlichkeit mitten im Satz
# abgebrochen. Wird NUR benutzt, um zu entscheiden, ob eine ohnehin schon
# mangelhafte Fassung noch aufgehoben werden darf -- nie, um eine saubere
# Fassung zu verwerfen.
_SCHLUSSZEICHEN = ".!?\u2026:;)]}\"'\u00bb\u00ab\u201c\u201d\u201e*_\u2013\u2014-"


def _wirkt_unfertig(text: str) -> bool:
    schwanz = text.rstrip()
    if not schwanz:
        return True
    return schwanz[-1] not in _SCHLUSSZEICHEN and not schwanz[-1].isdigit()


def _als_masken(teile: list[str], karte: dict[str, str]) -> list[str]:
    """Fehlende Originalteile in die Masken uebersetzen, die das Modell SIEHT.

    Gemessen 2026-08-19: ein Hinweis, der den Rohtext nennt ("uebernimm
    NEED_BETTER_PACKAGE"), verlangt vom Modell etwas, das in seiner Eingabe gar
    nicht vorkommt -- dort steht die Maske. Der Hinweis machte es dadurch
    schlechter statt besser. Ein Korrekturhinweis muss in derselben Sprache
    reden wie die Eingabe.
    """
    raus: list[str] = []
    for teil in teile:
        treffer = [m for m, roh in karte.items() if teil in roh]
        raus.extend(treffer or [teil])
    return raus


def _hinweis(fehlt: list[str], grund: str) -> str:
    """Korrekturhinweis fuer den naechsten Versuch -- konkret, nicht allgemein.

    Es wird NICHTS vorgesagt, was nicht schon in der Eingabe steht: die Liste
    besteht ausschliesslich aus Zeichenketten bzw. Masken des Originals.
    """
    liste = ", ".join(sorted(set(fehlt))[:25])
    return (f"\n\nKORREKTUR ({grund}). Das hier steht in der Eingabe und fehlte oder "
            f"stimmte nicht in deiner letzten Fassung. Uebernimm es unveraendert und "
            f"genau so oft, wie es in der Eingabe steht: {liste}")


def translate_to_german(
    caveman_text: str,
    *,
    model: str = TRANSLATOR_MODEL,
    api_key: str | None = None,
) -> dict[str, Any]:
    keys = [api_key] if api_key else secrets.mistral_keys()
    if not keys:
        raise RuntimeError("no Mistral key available")
    if not caveman_text or len(caveman_text) > 20_000:
        raise ValueError("invalid caveman text")

    maskiert, karte = _maskiere(caveman_text)
    zusatz = ""
    bester: tuple[int, str, dict, list[str]] | None = None
    grund = "unbekannt"

    for _versuch in range(1, MAX_UEBERSETZUNGSVERSUCHE + 1):
        result = transport.mistral_chat_json_rotating(
            keys=keys,
            model=model,
            system=TRANSLATOR_SYSTEM,
            user=f"CAVEMAN TEXT:\n{maskiert}{zusatz}",
            temperature=0.1,
            max_tokens=1200,
        )
        payload = result["payload"]
        if not isinstance(payload, dict) or not isinstance(payload.get("german"), str) or not payload["german"]:
            raise RuntimeError("translator envelope missing 'german'")
        roh = payload["german"]

        # 1. Abbruch. Nicht still weiterreichen: ein Satz, der mitten im Wort
        #    endet, ist keine Uebersetzung.
        if _wirkt_abgeschnitten(roh, maskiert):
            grund = "abgeschnitten"
            zusatz = "\n\nKORREKTUR: die letzte Fassung brach mitten im Text ab. Gib den GANZEN Text."
            continue

        # 2. Maskenzaehlung. Weicht sie ab, ist etwas schiefgegangen: eine
        #    fehlende Maske ist ein verlorenes Maschinenteil, eine doppelte ein
        #    zweimal gesetztes. Beides loest zuerst einen neuen Versuch aus.
        #    Bleibt es dabei, wird die beste Fassung trotzdem ausgeliefert und
        #    der Mangel in der Quittung vermerkt -- sie ist immer noch besser
        #    als der englische Rohtext, den der Rueckfall in pipeline.py sonst
        #    ausliefert. NICHT ausgeliefert wird eine Fassung, der eine
        #    Maschinenmarke fehlt (Schritt 3) oder die unfertig aussieht.
        #    Eine doppelte Maske ist KEINE Erfindung im Sinne der Eignerregel:
        #    zurueckgesetzt steht dort dieselbe Zeichenkette aus der Quelle,
        #    kein neuer Fakt -- nur eine Wiederholung, die die Quelle nicht hat.
        maskenfehler = [m for m in karte if roh.count(m) != maskiert.count(m)]
        deutsch = _entmaskiere(roh, karte)
        if RE_MASKE.search(deutsch):
            # Eine erfundene Maske, die es in der Karte nie gab.
            grund = "maske"
            zusatz = "\n\nKORREKTUR: erfinde keine [[C...]]-Masken, benutze nur die vorhandenen."
            continue

        # 3. Harte Sperre: eine Maschinenmarke der Quelle fehlt im Deutschen.
        #    Das darf nie durchgehen -- pipeline.py liest sie.
        marken_weg = _fehlende_marken(caveman_text, deutsch)
        if marken_weg:
            grund = "maschinenmarke"
            zusatz = _hinweis(_als_masken(marken_weg, karte),
                              "Maschinenmarken fehlten oder wurden uebersetzt")
            continue

        # 4. Weiche Pruefung: Bezeichner und Zahlen. Fehlt etwas, wird ein
        #    neuer Versuch unternommen -- aber die beste Fassung wird behalten
        #    statt verworfen. Eine Uebersetzung, der ein Bezeichner fehlt, ist
        #    schlechter als eine vollstaendige und besser als gar keine.
        fehlt = _fehlende_bezeichner(caveman_text, deutsch) + maskenfehler
        if not fehlt:
            return {
                "caveman_original": caveman_text,
                "german_translation": deutsch,
                "translator_model": model,
                "translator_receipt": result["receipt"],
            }
        # Nur eine Fassung merken, die nicht mitten im Text aufhoert.
        if not _wirkt_unfertig(roh) and (bester is None or len(fehlt) < bester[0]):
            bester = (len(fehlt), deutsch, result, fehlt)
        grund = "maske" if maskenfehler else "bezeichner"
        zusatz = _hinweis(_als_masken(fehlt, karte),
                          "Masken, Bezeichner oder Zahlen stimmten nicht -- "
                          "was hier nicht in der Eingabe steht, gehoert geloescht, "
                          "nicht ergaenzt")

    if bester is not None:
        _, deutsch, result, fehlt = bester
        # Mitschreiben statt schoenreden: der Beleg traegt, was fehlte.
        quittung = dict(result["receipt"])
        quittung["maengel"] = fehlt[:25]
        quittung["versuche"] = MAX_UEBERSETZUNGSVERSUCHE
        return {
            "caveman_original": caveman_text,
            "german_translation": deutsch,
            "translator_model": model,
            "translator_receipt": quittung,
        }

    raise RuntimeError(
        f"translator: {MAX_UEBERSETZUNGSVERSUCHE} Versuche, jedesmal derselbe Mangel "
        f"({grund}) -- unvollstaendige Ausgabe verworfen statt als Uebersetzung "
        "durchgereicht"
    )
