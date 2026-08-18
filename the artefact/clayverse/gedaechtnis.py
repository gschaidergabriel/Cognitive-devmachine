"""Dauerhaftes Gedaechtnis aus normalem Gespraech -- statt aus einer Markersyntax.

BEFUND, beziffert: 0 von 24 Zuegen enthalten einen Marker. Die vorhandene
Extraktion greift nur, wenn jemand woertlich "FACT:" an einen Zeilenanfang
schreibt. Kein Mensch tut das, und Zero auch nicht. Folge: durable_memory 0 --
und damit steht die ganze Lernkette still. Nichts zu erinnern, also nichts
abzurufen, also alle Abrufepisoden UNKNOWN, also keine Eintrittspunkte, also
keine Wegehierarchie. Und die Verdichtung kommt nie durch ihr Extraktionstor.

Eine Ursache, fuenf stillstehende Systeme.

⭐ DIE GEFAHR UND DIE ABWEHR
Ein Modell, das "Fakten extrahiert", erfindet Fakten -- und ein erfundener Fakt
im dauerhaften Gedaechtnis ist schlimmer als gar keiner: er wird spaeter
abgerufen und dann geglaubt, mit Provenienz und allem.

Deshalb ist die Regel hier nicht "extrahiere gut", sondern WOERTLICHKEIT:
jeder Eintrag muss eine Belegstelle mitliefern, und diese Belegstelle muss
ZEICHENGENAU im Quelltext vorkommen. Was das nicht erfuellt, wird verworfen --
auch wenn es klug klingt. Die Zahl der Verwuerfe wird mitgeschrieben; steigt sie,
ist das ein Befund ueber das Modell, nicht ueber den Text.

Die Extraktion laeuft ueber den Bahnrouter (billige Bahn), nicht ueber Zero
selbst: wer den Zug geschrieben hat, soll nicht auch entscheiden, was davon
erinnernswert ist.
"""
from __future__ import annotations

import json
import re

from .bahnen import BahnErschoepft, Bahnrouter

ARTEN = ("fact", "decision", "task", "commitment", "preference", "open_question")

ANWEISUNG = """Du bist ein Extraktor. Lies den Text und gib NUR JSON zurueck, kein Markdown.

{"eintraege":[{"art":"fact|decision|task|commitment|preference|open_question",
               "inhalt":"<kurz, eigenstaendig verstaendlich>",
               "beleg":"<WOERTLICHER Ausschnitt aus dem Text, zeichengenau>"}]}

Regeln:
- beleg MUSS zeichengenau im Text vorkommen. Erfinde nichts, paraphrasiere den Beleg nicht.
- Nur was wirklich behauptet oder entschieden wird. Keine Hoeflichkeiten, keine Fragen des
  Nutzers an dich, keine Zusammenfassung des Gespraechsverlaufs.
- Nichts gefunden ist ein gueltiges Ergebnis: {"eintraege":[]}
- Hoechstens 6 Eintraege."""


def _normalisieren(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def extrahiere(db, *, turn_id: str, user_id: str, content: str,
               rolle: str = "user", max_zeichen: int = 6000) -> dict:
    """Typisierte Gedaechtniseintraege aus einem Zug ziehen. Verwirft Unbelegtes."""
    text = (content or "").strip()
    if len(text) < 40:
        # Zu kurz, um etwas Dauerhaftes zu enthalten. Ein Aufruf dafuer waere
        # Kontingent fuer nichts.
        return {"eintraege": 0, "verworfen": 0, "grund": "zu kurz"}

    router = Bahnrouter(db)
    try:
        antwort = router.rufe("schema_antwort", text[:max_zeichen], system=ANWEISUNG, max_token=700)
    except BahnErschoepft as e:
        # Kein Gedaechtnis ist besser als ein erratenes. Der Zug laeuft weiter.
        return {"eintraege": 0, "verworfen": 0, "grund": f"keine Bahn: {e}"}
    except Exception as e:
        return {"eintraege": 0, "verworfen": 0, "grund": f"{type(e).__name__}: {e}"}

    roh = (antwort.get("text") or "").strip()
    if roh.startswith("```"):
        roh = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", roh).strip()
    try:
        d = json.loads(roh[roh.index("{"):roh.rindex("}") + 1])
    except Exception:
        return {"eintraege": 0, "verworfen": 0, "grund": "Antwort war kein JSON",
                "bahn": antwort.get("bahn")}

    quelle_norm = _normalisieren(text)
    genommen, verworfen, gruende = 0, 0, []
    for e in (d.get("eintraege") or [])[:6]:
        art = str(e.get("art") or "").lower().strip()
        inhalt = str(e.get("inhalt") or "").strip()
        beleg = str(e.get("beleg") or "").strip()
        if art not in ARTEN or not inhalt:
            verworfen += 1; gruende.append("Art oder Inhalt fehlt"); continue
        if len(beleg) < 8:
            verworfen += 1; gruende.append("Beleg zu kurz"); continue
        if _normalisieren(beleg) not in quelle_norm:
            # Der wichtigste Zweig der ganzen Datei.
            verworfen += 1; gruende.append("Beleg steht nicht im Text"); continue
        db.add_memory(
            art, user_id, inhalt, turn_id, user_id,
            {
                "extractor": "bahn-extraktor-v1",
                "bahn": antwort.get("bahn"),
                "modell": antwort.get("modell"),
                "rolle": rolle,
                "beleg": beleg[:400],
                "regel": "beleg zeichengenau im Quelltext verifiziert",
            },
        )
        genommen += 1
    return {"eintraege": genommen, "verworfen": verworfen, "gruende": gruende,
            "bahn": antwort.get("bahn"), "ms": antwort.get("ms")}
