"""Wikiverdichtung -- viele Baunotizen zu wenigen lesbaren Artikeln, mit Beleg je Aussage.

Eignerauftrag woertlich: "alles was passiert muss in das zentrale wiki ... und
muss dann auch in wiki beitraege verarbeitet werden." baunotizen.py erledigt die
erste Haelfte: 2250+ Zeilen art='baunotiz', eine je Commit/Bauverlauf-Eintrag.
Das ist ein LOG, kein Wiki -- 2250 Zeilen "fix(x): adjust y" beantworten keine
Frage, die je jemand stellt. Dieses Modul erledigt die zweite Haelfte:
VERARBEITEN. Viele Rohnotizen werden zu WENIGEN Artikeln gruppiert, die
tatsaechlich etwas sagen -- was geaendert wurde, wieso, was gemessen wurde, was
kaputt ging. Verlinkt zu den Rohnotizen, die sie kondensieren -- ersetzt oder
loescht sie nie. Die Rohnotiz ist der Beleg, der Artikel ist die Lesart.

⭐ DREI REGELN, DIE ENTSCHEIDEN OB DAS ETWAS WERT IST

1. VERDICHTEN HEISST WEGLASSEN, NICHT NACHERZAEHLEN. Ein Artikel, der so lang
   ist wie seine Quellen, ist eine Kopie und hilft niemandem. Jeder Lauf
   berichtet das Verhaeltnis Zeichen-Quellen zu Zeichen-Artikel; ein Artikel
   ohne Schrumpfung ist ein Fehlschlag, kein Teilerfolg.

2. JEDE AUSSAGE FUEHRT AUF EINE QUELLNOTIZ ZURUECK. Woertlichkeitspruefung wie
   in gedaechtnis.py (Funktion von dort direkt wiederverwendet, nicht neu
   erfunden): eine vom Modell gelieferte Aussage braucht einen woertlichen
   Beleg, ZEICHENGENAU in GENAU der Rohnotiz, die als Quelle angegeben wird --
   nicht irgendwo in der Gruppe. Ohne das: verworfen, gezaehlt. Die
   Eigner-Grundregel NICHTS ERFINDEN gilt hier woertlich.

3. FEHLSCHLAEGE UEBERLEBEN DIE VERDICHTUNG. Der natuerliche Zug einer
   Zusammenfassung geht zur glatten Geschichte. Der Bauverlauf vom 18.08.
   enthaelt (gemessen, siehe Testlauf in diesem Modulordner) ein
   Cross-user-Gedaechtnisleck, eine 77-rote-Tests-Regression (executescript()
   committet implizit, reisst eine laufende Transaktion auseinander), zwei
   still falsche Feld-/Spaltennamen (`gehoert` statt `gehoert_zu`; ein
   Einfuegeanker, der nie traf, weil eine Wache auf einen nicht vorhandenen
   Trenner splittete) und einen Fehlalarm aus einem veralteten Docstring. Sieht
   ein Verdichtungsartikel so aus, als sei alles gut gelaufen, hat er genau den
   nuetzlichsten Teil der Aufzeichnung zerstoert. DAGEGEN sichert dieses Modul:
   die Modellanweisung nennt Fehlschlaege ausdruecklich als Pflichtinhalt, und
   die Woertlichkeitspruefung entfernt nur UNBELEGTE Aussagen -- nie
   unbequeme. Ein Fehlschlag mit Beleg ist eine so gute Aussage wie ein Erfolg
   mit Beleg.

ZWEI PFADE JE GRUPPE
---------------------
MECHANISCH: wenn keine Rohnotiz der Gruppe Fliesstext ab NARRATIV_SCHWELLE
Zeichen traegt (die Mehrzahl der Git-Commits hier ist eine einzeilige
Betreffzeile ohne Koerper -- vgl. baunotizen.py-Kopf: "kein einziger Commit
... traegt eine Hypothese-Zeile", derselbe Bestand ist meist auch sonst
wortkarg), gibt es nichts zu lesen ausser der Zaehlung selbst. Der Artikel wird
dann rein mechanisch aus Anzahl/Zeitraum/Titeln gebaut, OHNE Modellaufruf --
eine gezaehlte Tatsache braucht keine Woertlichkeitspruefung, sie ist bereits
ihr eigener Beleg.

NARRATIV: sobald mindestens eine Rohnotiz der Gruppe echten Fliesstext traegt,
lohnt sich Lesen. Hier laeuft der Bahnrouter (Faehigkeit 'kondensieren',
bahnen.py) -- das Modell liefert Aussage + woertlicher Beleg + Quellnotiz-
Kennung je Aussage, jede wird einzeln geprueft. Liefert der Router nichts
(BahnErschoepft), wird die Gruppe DIESEN Lauf uebersprungen, nicht mechanisch
nachgebaut -- eine erschoepfte Bahn ist eine Ablehnung, kein Anlass, den Text
selbst mit Vorlage zu schreiben (siehe bahnen.py-Kopf, Regel 3).

GRUPPIERUNG, MECHANISCH
------------------------
(Kalendertag UTC, Thema). Thema = der Text vor dem ersten ':' in den ersten 60
Zeichen des Betreffs, kleingeschrieben -- trifft das maschinelle Muster dieses
Bestands: "claycode supervisor: ...", "receipt(go): ...", "test(clayverse):
..." (gemessen: das ist die ueberwiegende Form der Git-Commit-Betreffs seit
GIT_CUTOFF). Ohne Doppelpunkt dort: fester Eimer "vorgang" -- das faengt genau
die von Menschen verfassten Bauverlauf-Titel auf (kein Doppelpunkt-Schema am
Anfang), die den informativsten Text im Bestand tragen und sonst in lauter
Einzelgruppen zerfallen wuerden.
Gruppen unter MIN_GRUPPENGROESSE Notizen werden NICHT verdichtet -- ein
Artikel aus ein oder zwei Notizen ist keine Verdichtung, nur eine
Umformulierung, und bleibt ungruppiert liegen (in `notizen_ohne_gruppe`
gezaehlt, nicht stillschweigend verworfen).

HYPOTHESE/GEGENHYPOTHESE: NIE vom Modell erfragt -- exakt dieselbe mechanische
Regex-Extraktion wie baunotizen.py (`_extrahiere_hypothesen`, importiert, nicht
neu geschrieben), angewandt auf den vollen Gruppentext. Gemessen (18.08., alle
2250+ baunotiz-Zeilen durchsucht): 0 Treffer im ganzen Bestand. Bleibt also
fast immer null -- das ist der Befund ueber den Bestand, kein Bug im
Extraktor. Eine geratene Hypothese waere Gift in einem Forschungswiki.

IDEMPOTENZ
----------
id = deterministisch aus (Tag, Thema) -- stabil ueber Laeufe hinweg, gleiches
Vorbild wie baunotizen.py. quell_hash = sha256 ueber alle Quellnotiz-IDs samt
ihrem Rohtext (Titel+wieso) -- aendert sich eine Quelle oder kommt eine neue in
die Gruppe, aendert sich der Hash und die Zeile wird neu verdichtet (Upsert per
`ON CONFLICT(id) DO UPDATE`, keine Duplikate: PRIMARY KEY(id)). Unveraendert ->
zweiter Lauf ueberspringt die Gruppe VOR jedem Modellaufruf: 0 neue Bahn-
Anfragen, 0 neue Zeilen, 0 Duplikate.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from .bahnen import BahnErschoepft, Bahnrouter
from .baunotizen import (
    _extrahiere_hypothesen,
    _hat_artikel_tabelle,
    _jetzt_iso,
    _sha256,
    _schreibe,
    _slugify,
    _UPSERT_BAUNOTIZ as _UPSERT,
    _vorhandene,
    _zeile_baunotiz as _zeile,
)
from .gedaechtnis import _normalisieren

ART = "verdichtung"
QUELLE = "wikiverdichtung"

MIN_GRUPPENGROESSE = 3      # Notizen je Gruppe, unterhalb keine Verdichtung
NARRATIV_SCHWELLE = 250     # Zeichen wieso, ab der eine Notiz als "hat Fliesstext" zaehlt
MAX_NOTIZEN_FUER_MODELL = 12  # Promptdeckel -- laengste zuerst, falls mehr in der Gruppe
SNIPPET_KAPPUNG = 900        # Zeichen je Notiz im Prompt

_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_artikel_verdichtung_lookup "
    "ON artikel(art, von_quelle, datum)"
)


def sicherstellen(db) -> None:
    """Nur Index anlegen, wie baunotizen.sicherstellen -- artikel gehoert nicht
    zu UnifiedDB.SCHEMA (Altbestand). Auf einer frischen Test-DB ohne artikel-
    Tabelle ist hier nichts zu tun."""
    if not _hat_artikel_tabelle(db):
        return
    db.db.executescript(_INDEX_SQL)


# ---------------------------------------------------------------------------
# Rohnotizen laden + gruppieren -- rein mechanisch, kein Modellaufruf.
# ---------------------------------------------------------------------------

def _lade_baunotizen(db) -> list[dict]:
    rows = db.db.execute(
        "SELECT id, titel, datum, metadaten, von_quelle FROM artikel WHERE art='baunotiz'"
    ).fetchall()
    out = []
    for r in rows:
        try:
            meta = json.loads(r["metadaten"] or "{}")
        except Exception:
            meta = {}
        out.append({
            "id": r["id"],
            "titel": (r["titel"] or "").strip(),
            "datum": r["datum"],
            "von_quelle": r["von_quelle"],
            "wieso": (meta.get("wieso") or "").strip(),
        })
    return out


def _tag_utc(datum: str | None) -> str | None:
    """Kalendertag in UTC -- ISO-Datum mit +07:00 und +00:00 landen sonst auf
    verschiedenen Tagen fuer dieselbe Uhrzeitregion."""
    if not datum:
        return None
    try:
        d = datetime.fromisoformat(str(datum).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).date().isoformat()
    except Exception:
        return None


def _thema(betreff: str) -> str:
    """Text vor dem ersten ':' in den ersten 60 Zeichen -- trifft das
    maschinelle Commit-Muster ("claycode supervisor: ..."). Kein Treffer oder
    unplausibel lang: fester Eimer 'vorgang' (faengt die Bauverlauf-Klartexte
    ohne Doppelpunkt-Kopf auf, die sonst in Einzelgruppen zerfallen)."""
    kopf = (betreff or "")[:60]
    idx = kopf.find(":")
    if idx <= 0:
        return "vorgang"
    thema = re.sub(r"\s+", " ", kopf[:idx]).strip(" -_").lower()
    if not thema or len(thema) > 40:
        return "vorgang"
    return thema


def _gruppieren(zeilen: list[dict]) -> dict[tuple[str, str], list[dict]]:
    gruppen: dict[tuple[str, str], list[dict]] = {}
    for z in zeilen:
        tag = _tag_utc(z["datum"]) or "unbekanntes-datum"
        thema = _thema(z["titel"])
        gruppen.setdefault((tag, thema), []).append(z)
    return gruppen


def _hash_gruppe(gruppe: list[dict]) -> str:
    payload = "\x1f".join(
        f"{z['id']}\x1e{z['titel']}\x1e{z['wieso']}"
        for z in sorted(gruppe, key=lambda z: z["id"])
    )
    return _sha256(payload)


def _ist_narrativ(gruppe: list[dict]) -> bool:
    return any(len(z["wieso"]) >= NARRATIV_SCHWELLE for z in gruppe)


# ---------------------------------------------------------------------------
# Pfad A: mechanisch -- reine Zaehlung, kein Modellaufruf, keine
# Woertlichkeitspruefung noetig (eine Zaehlung ist schon ihr eigener Beleg).
# ---------------------------------------------------------------------------

def _mechanischer_artikel(tag: str, thema: str, gruppe: list[dict]) -> dict:
    n = len(gruppe)
    daten = sorted(z["datum"] for z in gruppe if z["datum"])
    von, bis = (daten[0], daten[-1]) if daten else (None, None)
    quellen_mix = sorted({z["von_quelle"] for z in gruppe if z["von_quelle"]})
    beispiele, gesehen = [], set()
    for z in gruppe:
        if z["titel"] and z["titel"] not in gesehen:
            gesehen.add(z["titel"])
            beispiele.append(z["titel"])
        if len(beispiele) >= 5:
            break
    zeilen = [
        f"{n} Baunotizen vom {tag}, Thema \"{thema}\", "
        f"Quelle(n): {', '.join(quellen_mix) or 'unbekannt'}.",
        f"Zeitraum: {von or '?'} bis {bis or '?'}.",
        f"Rohtext ohne Fliesstext ueber {NARRATIV_SCHWELLE} Zeichen in dieser "
        "Gruppe -- mechanisch gezaehlt, kein Modellaufruf, keine Einzelaussage.",
    ]
    if beispiele:
        zeilen.append("Beispieltitel: " + " | ".join(beispiele))
    return {
        "titel": f"{tag}: {thema} ({n} Notizen, mechanisch gezaehlt)",
        "body": "\n".join(zeilen),
        "pfad": "mechanisch", "bahn": None, "modell": None,
        "claims_geprueft": 0, "claims_verworfen": 0, "gruende": [],
        "von": von, "bis": bis, "quellen_mix": quellen_mix,
    }


# ---------------------------------------------------------------------------
# Pfad B: narrativ -- Bahnrouter + Woertlichkeitspruefung je Aussage.
# ---------------------------------------------------------------------------

_SYS_PROMPT = """Du bist ein Verdichter fuer ein Forschungswiki. Du bekommst mehrere
Rohnotizen (mit Kennung) aus einem Bausystem. Fasse zusammen, was passiert ist:
was geaendert wurde, wieso, was gemessen wurde, was kaputt ging. Fehlschlaege,
Regressionen und gemeldete Zahlen MUESSEN erhalten bleiben, wenn sie in den
Notizen stehen -- eine Zusammenfassung, die nur Erfolge nennt, ist falsch.

Gib NUR JSON zurueck, kein Markdown:
{"titel": "<kurzer, konkreter Titel auf Deutsch>",
 "claims": [{"text": "<kurze, eigenstaendige Aussage auf Deutsch>",
             "beleg": "<KURZER woertlicher Ausschnitt aus GENAU DER Notiz unten, zeichengenau, unter 150 Zeichen>",
             "quelle_id": "<Kennung der Notiz, aus der der Beleg stammt>"}]}

Regeln:
- beleg MUSS zeichengenau in der bei quelle_id genannten Notiz vorkommen. Nicht
  paraphrasieren, nichts erfinden, keinen Beleg aus einer anderen Notiz nehmen.
- beleg so KURZ wie moeglich waehlen (ein Satz oder Zahlenbeleg reicht) --
  lang zitieren kostet Platz, der einer weiteren Aussage fehlt.
- Hoechstens 6 Aussagen. Nichts Brauchbares gefunden ist gueltig: {"titel":"...","claims":[]}
- Keine Hoeflichkeiten, keine blosse Wiederholung der Kennungen als Aussage."""


def _prompt(notizen: list[dict]) -> str:
    teile = []
    for z in notizen:
        text = (z["wieso"] or z["titel"])[:SNIPPET_KAPPUNG]
        teile.append(f"[{z['id']}] {z['titel']}\n{text}")
    return "\n\n---\n\n".join(teile)


def _parse_antwort(roh: str) -> dict | None:
    """JSON aus der Modellantwort lesen -- mit EINEM mechanischen
    Reparaturversuch bei abgeschnittener Antwort (Token-Deckel getroffen,
    mitten in einem claims-Objekt abgerissen): beim letzten vollstaendigen
    Eintrag kappen und die Klammern syntaktisch schliessen. Das erfindet
    keinen Inhalt -- es entfernt nur einen unvollstaendigen letzten Eintrag,
    den json.loads sonst komplett verwerfen wuerde."""
    roh = (roh or "").strip()
    if roh.startswith("```"):
        roh = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", roh).strip()
    kandidaten = [roh]
    schnitt = roh.rfind("},")
    if schnitt > 0:
        kandidaten.append(roh[:schnitt + 1] + "]}")
    for k in kandidaten:
        try:
            return json.loads(k[k.index("{"):k.rindex("}") + 1])
        except Exception:
            continue
    return None


def _narrativer_artikel(router: Bahnrouter, tag: str, thema: str, gruppe: list[dict]) -> dict | None:
    daten = sorted(z["datum"] for z in gruppe if z["datum"])
    von, bis = (daten[0], daten[-1]) if daten else (None, None)
    quellen_mix = sorted({z["von_quelle"] for z in gruppe if z["von_quelle"]})

    kandidaten = sorted(gruppe, key=lambda z: len(z["wieso"]), reverse=True)
    gelesen = kandidaten[:MAX_NOTIZEN_FUER_MODELL]
    quelltext_je_id = {
        z["id"]: _normalisieren(z["titel"] + " " + z["wieso"]) for z in gruppe
    }

    # Bis zu 2 Versuche derselben Bahn -- kein Abstieg, keine selbst
    # geschriebene Vorlage (Regel 3, bahnen.py), nur ein zweiter Wurf, wenn
    # der erste syntaktisch kaputtes JSON zurueckgab (bei freien Modellen
    # gemessen: nicht selten, meist bei laengeren Antworten).
    antwort, daten_json = None, None
    for versuch in range(2):
        try:
            antwort = router.rufe("kondensieren", _prompt(gelesen), system=_SYS_PROMPT, max_token=2600)
        except BahnErschoepft:
            # Regel 3 aus bahnen.py: erschoepft heisst Ablehnung, nicht Abstieg
            # auf eine selbst geschriebene Vorlage. Gruppe bleibt fuer den
            # naechsten Lauf liegen (kein Eintrag in `vorhandene`).
            return None
        daten_json = _parse_antwort(antwort.get("text", ""))
        if daten_json is not None:
            break

    if daten_json is None:
        return {
            "titel": f"{tag}: {thema} ({len(gruppe)} Notizen, Modellantwort kein JSON)",
            "body": (
                f"{len(gruppe)} Notizen gruppiert, Bahn '{antwort.get('bahn')}' antwortete, "
                "aber nicht als lesbares JSON -- keine Aussage extrahiert."
            ),
            "pfad": "narrativ", "bahn": antwort.get("bahn"), "modell": antwort.get("modell"),
            "claims_geprueft": 0, "claims_verworfen": 0,
            "gruende": ["Antwort war kein JSON"],
            "von": von, "bis": bis, "quellen_mix": quellen_mix,
            "gelesene_notizen": [z["id"] for z in gelesen],
        }

    aussagen = (daten_json.get("claims") or [])[:6]
    behalten, gruende = [], []
    verworfen = 0
    for c in aussagen:
        text = str(c.get("text") or "").strip()
        beleg = str(c.get("beleg") or "").strip()
        qid = str(c.get("quelle_id") or "").strip()
        if not text or len(beleg) < 8:
            verworfen += 1
            gruende.append(f"{qid or '?'}: Aussage oder Beleg fehlt/zu kurz")
            continue
        quelltext = quelltext_je_id.get(qid)
        if quelltext is None:
            verworfen += 1
            gruende.append(f"{qid or '?'}: unbekannte Quellnotiz-Kennung")
            continue
        if _normalisieren(beleg) not in quelltext:
            # Der wichtigste Zweig -- exakt wie in gedaechtnis.py: der Beleg
            # muss in GENAU der angegebenen Quelle stehen, nicht irgendwo in
            # der Gruppe.
            verworfen += 1
            gruende.append(f"{qid}: Beleg nicht zeichengenau in dieser Notiz")
            continue
        behalten.append({"text": text, "beleg": beleg[:400], "quelle_id": qid})

    modell_titel = str(daten_json.get("titel") or "").strip()
    if modell_titel and len(modell_titel) <= 120:
        titel = f"{tag}: {thema} -- {modell_titel}"
    else:
        titel = f"{tag}: {thema} ({len(gruppe)} Notizen)"

    if behalten:
        body = "\n".join(f"- {c['text']} [{c['quelle_id']}]" for c in behalten)
    else:
        body = (
            f"{len(gruppe)} Notizen gruppiert, {len(aussagen)} Aussagen vom Modell erhalten, "
            f"0 bestanden die Woertlichkeitspruefung (verworfen: {verworfen}). "
            "Artikel bleibt bei der Zaehlung, keine erfundene Einzelaussage."
        )

    return {
        "titel": titel, "body": body, "pfad": "narrativ",
        "bahn": antwort.get("bahn"), "modell": antwort.get("modell"),
        "claims_geprueft": len(aussagen), "claims_verworfen": verworfen, "gruende": gruende,
        "von": von, "bis": bis, "quellen_mix": quellen_mix,
        "gelesene_notizen": [z["id"] for z in gelesen],
    }


# ---------------------------------------------------------------------------
# Oeffentlicher Einstieg
# ---------------------------------------------------------------------------

def verdichten(db, *, tage: int | None = None) -> dict:
    """Baunotizen zu wenigen Wiki-Artikeln verdichten.

    tage=N beschraenkt die Eingangsmenge auf die letzten N Kalendertage (UTC,
    gemessen an jetzt) -- sonst der komplette baunotiz-Bestand. Idempotent:
    unveraenderte Gruppen werden VOR jedem Modellaufruf uebersprungen (0 neue
    Bahn-Anfragen, 0 neue Zeilen, 0 Duplikate bei unveraenderter Quelle).
    """
    sicherstellen(db)
    if not _hat_artikel_tabelle(db):
        return {"hinweis": "keine artikel-Tabelle auf dieser DB (Testinstanz?) -- nichts zu tun",
                "gruppen": 0, "artikel_neu": 0, "artikel_aktualisiert": 0, "uebersprungen": 0}

    zeilen = _lade_baunotizen(db)
    notizen_gesamt = len(zeilen)
    if tage is not None:
        grenze = (datetime.now(timezone.utc) - timedelta(days=tage)).date().isoformat()
        zeilen = [z for z in zeilen if (_tag_utc(z["datum"]) or "9999") >= grenze]

    gruppen = _gruppieren(zeilen)
    vorhandene = _vorhandene(db, ART, QUELLE)
    router = Bahnrouter(db)
    jetzt = _jetzt_iso()

    ergebnis = {
        "notizen_gesamt": notizen_gesamt, "notizen_betrachtet": len(zeilen),
        "notizen_ohne_gruppe": 0, "gruppen": 0,
        "artikel_neu": 0, "artikel_aktualisiert": 0, "uebersprungen": 0,
        "narrativ": 0, "mechanisch": 0, "bahn_erschoepft": 0,
        "claims_geprueft": 0, "claims_verworfen": 0,
        "zeichen_quellen": 0, "zeichen_artikel": 0,
        "fehler": [],
    }

    for (tag, thema), gruppe in sorted(gruppen.items()):
        if len(gruppe) < MIN_GRUPPENGROESSE:
            ergebnis["notizen_ohne_gruppe"] += len(gruppe)
            continue
        ergebnis["gruppen"] += 1

        id_ = f"verdichtung-{tag}-{_slugify(thema)}"
        quell_hash = _hash_gruppe(gruppe)
        if vorhandene.get(id_) == quell_hash:
            ergebnis["uebersprungen"] += 1
            continue

        narrativ = _ist_narrativ(gruppe)
        if narrativ:
            r = _narrativer_artikel(router, tag, thema, gruppe)
            if r is None:
                ergebnis["bahn_erschoepft"] += 1
                ergebnis["fehler"].append(f"{id_}: Bahn erschoepft -- uebersprungen, naechster Lauf")
                continue
            ergebnis["narrativ"] += 1
        else:
            r = _mechanischer_artikel(tag, thema, gruppe)
            ergebnis["mechanisch"] += 1

        ergebnis["claims_geprueft"] += r["claims_geprueft"]
        ergebnis["claims_verworfen"] += r["claims_verworfen"]

        hyp, gegenhyp = _extrahiere_hypothesen(
            "\n".join(z["wieso"] for z in gruppe if z["wieso"])
        )

        zeichen_quellen = sum(len(z["titel"]) + len(z["wieso"]) for z in gruppe)
        zeichen_artikel = len(r["titel"]) + len(r["body"])
        ergebnis["zeichen_quellen"] += zeichen_quellen
        ergebnis["zeichen_artikel"] += zeichen_artikel

        meta = {
            "text": r["body"],
            "quellnotizen": sorted(z["id"] for z in gruppe),
            "zeitraum": {"von": r["von"], "bis": r["bis"]},
            "herkunft": "+".join(r["quellen_mix"]) or "unbekannt",
            "hypothese": hyp,
            "gegenhypothese": gegenhyp,
            "erzeugt_von": f"wikiverdichtung:{r['pfad']}" + (f":{r['bahn']}" if r.get("bahn") else ""),
            "timestamp": jetzt,
            "tag": tag,
            "thema": thema,
            "notizen_in_gruppe": len(gruppe),
            "gelesene_notizen": r.get("gelesene_notizen"),
            "claims_geprueft": r["claims_geprueft"],
            "claims_verworfen": r["claims_verworfen"],
            "verwurfsgruende": r["gruende"][:20],
            "kompression": {
                "zeichen_quellen": zeichen_quellen,
                "zeichen_artikel": zeichen_artikel,
                "verhaeltnis": round(zeichen_quellen / zeichen_artikel, 2) if zeichen_artikel else None,
            },
            "modell": r.get("modell"),
        }

        _schreibe(db, _UPSERT, _zeile(
            id=id_, art=ART, titel=r["titel"], quelle=QUELLE, quell_hash=quell_hash,
            datum=r["bis"] or r["von"],
            metadaten=json.dumps(meta, ensure_ascii=False, sort_keys=True),
            belegt=1, erzeugt_am=jetzt, wirt="clayverse", zuletzt_von="wikiverdichtung",
            von_quelle=QUELLE, status=r["pfad"], konfidenz=None,
            projekt="EntityOS", projekt_art="eigen", sphaere="entityos", herkunft="gemessen",
        ))
        bisher = vorhandene.get(id_)
        vorhandene[id_] = quell_hash
        if bisher is None:
            ergebnis["artikel_neu"] += 1
        else:
            ergebnis["artikel_aktualisiert"] += 1

    ergebnis["kompression_gesamt"] = (
        round(ergebnis["zeichen_quellen"] / ergebnis["zeichen_artikel"], 2)
        if ergebnis["zeichen_artikel"] else None
    )
    return ergebnis
