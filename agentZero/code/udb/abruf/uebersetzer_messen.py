#!/usr/bin/env python3
"""Messgeraet fuer den Uebersetzer Caveman -> Deutsch (Ziel: 95 %).

WARUM DIESES GERAET
-------------------
Es gab vorher ein Mass (mistral_prestage/eval_harness.py, 50 Punkte,
Gemini als Richter, pass_rate 0,96/0,98). Dessen eigene Datei sagt aber im
Feld "note": HAND-AUTHORED, not sampled from production. Ein Wert auf
selbst geschriebenen Beispielen misst den Uebersetzer nicht im Betrieb.
Dieses Geraet misst auf ECHTEN Zuegen aus mv_translation_log (turn_id
gesetzt = Produktionszug, nicht Eval).

DAS MASS
--------
Nicht Schoenheit, sondern TREUE, und zwar mechanisch nachpruefbar:
  * VERLORENER FAKT  -> Probe durchgefallen.
  * ERFUNDENER FAKT  -> Probe durchgefallen (Eignerregel "NICHTS erfinden").
Eine holprige deutsche Zeile, die alles behaelt, ist besser als eine schoene,
die einen Pfad oder eine Warnung verliert. Genau so wird hier gezaehlt.

Ein Richter-Modell wird bewusst NICHT benutzt: ein Modell, das ein Modell
bewertet, teilt dessen blinde Flecken. Zahlen, Pfade und Bezeichner kann man
abzaehlen -- das braucht keine Meinung.

FAKTENKLASSEN
-------------
  zahl        jede Zahl (Datum, Anzahl, Prozent, Version)
  pfad        alles mit Schraegstrich (/var/lib/clay/wiki.db, ~/seimensch)
  datei       gepunkteter Bezeichner mit bekannter Endung (wiki.db, app.py)
  kennung     snake_case-Bezeichner (udb_memory_add, session_state)
  eigenname   CamelCase/Marke (EffectGate, UnifiedDB, EntityOS) und
              GROSS_MIT_UNTERSTRICH (NEED_BETTER_PACKAGE)
  warnung     Warnmarke (⚠️, never, dont, must not, nie, niemals ...)

ERFINDUNGSPRUEFUNG nur auf zahl/pfad/datei/kennung. Eigennamen und Warnungen
sind im Deutschen zu haeufig neu formuliert (ein deutsches GROSSWORT ist kein
erfundener Fakt), das gaebe Fehlalarm statt Messung.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GOLD_PFAD = Path(__file__).with_name("uebersetzer_gold.json")

# ── Zahlwoerter, damit "zero rows" / "keine Zeilen" nicht als Verlust zaehlt ──
# Bewusst NICHT enthalten: "one", "ein", "eine", "a". Das sind im Englischen
# Fuerwoerter und im Deutschen Artikel ("I won't fabricate one", "eine Zahl")
# -- als Zahl gelesen erzeugen sie erfundene Verluste und, schlimmer, erfundene
# Treffer, die einen echten Verlust zudecken wuerden.
ZAHLWORT = {
    "zero": "0", "no goals": "0", "keine": "0", "kein": "0", "null": "0",
    "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11",
    "twelve": "12",
    "zwei": "2", "drei": "3", "vier": "4", "fuenf": "5", "fünf": "5",
    "sechs": "6", "sieben": "7", "acht": "8", "neun": "9", "zehn": "10",
    "elf": "11", "zwoelf": "12", "zwölf": "12",
}

# Ordnungszahlen: englisch steht die Ziffer da ("the 4th digit"), deutsch das
# Wort ("die vierte Ziffer"). Ohne diese Zeile meldet das Geraet den Verlust
# einer Zahl, die sehr wohl angekommen ist -- nur ausgeschrieben.
RE_ORDNUNGSZAHL = re.compile(
    r"\b(erste|zweite|dritte|vierte|fünfte|fuenfte|sechste|siebte|achte|"
    r"neunte|zehnte)[nrms]?\b", re.IGNORECASE)
ORDNUNGSZAHL = {
    "erste": "1", "zweite": "2", "dritte": "3", "vierte": "4", "fünfte": "5",
    "fuenfte": "5", "sechste": "6", "siebte": "7", "achte": "8",
    "neunte": "9", "zehnte": "10",
}

WARNMARKEN_CAVEMAN = [
    "⚠", "never", "dont", "don't", "do not", "must not", "not allowed",
    "danger", "careful", "warning", "no third", "verboten", "nie ", "niemals",
]
WARNMARKEN_DEUTSCH = [
    "⚠", "nie", "niemals", "nicht", "kein", "darf", "vorsicht", "warnung",
    "verboten", "gefahr", "achtung", "unterlass",
]

ENDUNGEN = (
    "db|py|json|md|html|css|js|sh|log|txt|yml|yaml|toml|ini|conf|sql|jsonl|"
    "net|org|at|com|ink|io|de|gz|tgz|key|mmdb|env|lock|cfg|service|timer"
)

# Der Rueckblick `(?<![\w\-])` ist gemessen noetig: ohne ihn liest das Geraet
# jedes "Filesystem/SQLite-Target" oder "memory/state" als Pfad und meldet
# einen Verlust, wo nur ein Schraegstrich zwischen zwei Woertern steht --
# 9 von 29 gemeldeten Verlusten im ersten Lauf waren genau das.
RE_PFAD = re.compile(r"(?<![\w\-])(?:~|\.{1,2})?/[\w.\-/]*[\w\-]")
RE_DATEI = re.compile(r"\b[\w\-]+\.(?:%s)\b" % ENDUNGEN)
RE_KENNUNG = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
RE_CAMEL = re.compile(r"\b[A-Za-z]*[a-z][A-Z][A-Za-z]{2,}\b")
RE_GROSS_UNTER = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
RE_ZAHL = re.compile(r"\d[\d.,:]*\d|\d")

# Listenmarken und Ueberschriften raus: "1. Punkt" im Deutschen ist keine
# erfundene Zahl, sondern Markdown. Sonst faellt jede Aufzaehlung durch.
RE_LISTENMARKE = re.compile(r"(?m)^[ \t]*(?:\d+[.)]|[-*+#>]+)[ \t]+")


def _entmarkt(text: str) -> str:
    return RE_LISTENMARKE.sub("", text)


RE_TAUSENDER = re.compile(r"^\d{1,3}(?:[.,]\d{3})+$")
RE_DEZIMAL = re.compile(r"^\d+[.,]\d+$")


def _blank(roh: str) -> str:
    return re.sub(r"[^\d]", "", roh).lstrip("0") or "0"


def _zahl_formen(roh: str) -> set[str]:
    """Eine Zahl in die Formen bringen, in denen beide Sprachen sie schreiben.

    Deutsch und Englisch tauschen Punkt und Komma und drehen Datumsteile um.
    Ohne diese Umrechnung meldet das Geraet Unterschiede, die keine sind:
      31,557,600 (en) == 31.557.600 (de)   -> Tausendertrenner: zusammenziehen
      4.35495     (en) == 4,35495     (de)  -> Dezimalzahl: zusammenziehen
      2026-08-18  (en) == 18.08.2026  (de)  -> Datum/Uhrzeit: in Teile zerlegen
    """
    roh = roh.strip(".,:")
    if not roh:
        return set()
    if RE_TAUSENDER.match(roh) or RE_DEZIMAL.match(roh):
        return {_blank(roh)}
    teile = {_blank(t) for t in re.findall(r"\d+", roh)}
    return teile or {_blank(roh)}


def zahlen(text: str, *, mit_zahlwoertern: bool = True) -> set[str]:
    t = _entmarkt(text)
    gefunden: set[str] = set()
    for m in RE_ZAHL.finditer(t):
        gefunden |= _zahl_formen(m.group(0))
    if mit_zahlwoertern:
        # Nur beim Suchen nach Verlust: "zero rows" darf als "null Zeilen"
        # ankommen. Beim Erfindungsverdacht ist das Wortverzeichnis verboten,
        # sonst gilt jedes deutsche "eine" als frisch erfundene Eins.
        for wort, ziffer in ZAHLWORT.items():
            if re.search(r"\b%s\b" % re.escape(wort), t, re.IGNORECASE):
                gefunden.add(_blank(ziffer))
        for m in RE_ORDNUNGSZAHL.finditer(t):
            gefunden.add(_blank(ORDNUNGSZAHL[m.group(1).lower()]))
    return {z for z in gefunden if z}


def _menge(regex: re.Pattern, text: str) -> set[str]:
    return {m.group(0) for m in regex.finditer(text)}


def fakten(text: str) -> dict[str, list[str]]:
    """Alle nachpruefbaren Tatsachen eines Textes, nach Klassen sortiert."""
    pfade = _menge(RE_PFAD, text)
    # Ein Pfad enthaelt oft schon den Dateinamen -- der zaehlt dann nicht doppelt.
    dateien = {d for d in _menge(RE_DATEI, text)
               if not any(d in p for p in pfade)}
    eigennamen = _menge(RE_CAMEL, text) | _menge(RE_GROSS_UNTER, text)
    warn = ["warnmarke"] if any(
        m in text.lower() for m in WARNMARKEN_CAVEMAN) else []
    return {
        "zahl": sorted(zahlen(text)),
        "pfad": sorted(pfade),
        "datei": sorted(dateien),
        "kennung": sorted(_menge(RE_KENNUNG, text)),
        "eigenname": sorted(eigennamen),
        "warnung": warn,
    }


def _steht_drin(fakt: str, klasse: str, deutsch: str) -> bool:
    """Haelt das Deutsche den Fakt -- egal in welcher Beugung/Zusammensetzung."""
    if klasse == "zahl":
        return fakt in zahlen(deutsch)
    if klasse == "warnung":
        return any(m in deutsch.lower() for m in WARNMARKEN_DEUTSCH)
    if fakt in deutsch:
        return True
    # Zweite Chance: Gross/Kleinschreibung darf sich aendern (Satzanfang,
    # deutsche Komposita), der Bezeichner selbst nicht.
    return fakt.lower() in deutsch.lower()


# Nur hier gilt Erfindung als Erfindung. Ein deutsches Wort in GROSSBUCHSTABEN
# oder ein neu gesetztes "nicht" ist Sprache, kein neuer Fakt.
ERFINDUNGSKLASSEN = ("zahl", "pfad", "datei", "kennung")


def bewerte(caveman: str, deutsch: str) -> dict:
    quelle = fakten(caveman)
    ziel = fakten(deutsch)
    verloren, gehalten = [], 0
    for klasse, liste in quelle.items():
        for f in liste:
            if _steht_drin(f, klasse, deutsch):
                gehalten += 1
            else:
                verloren.append({"klasse": klasse, "fakt": f})
    erfunden = []
    quellzahlen = zahlen(caveman, mit_zahlwoertern=False)
    for klasse in ERFINDUNGSKLASSEN:
        quellmenge = set(quelle[klasse])
        for f in (zahlen(deutsch, mit_zahlwoertern=False) if klasse == "zahl"
                  else ziel[klasse]):
            if klasse == "zahl":
                if f in quellzahlen:
                    continue
            elif any(f in q or q in f for q in quellmenge) or f in caveman:
                continue
            erfunden.append({"klasse": klasse, "fakt": f})
    gesamt = sum(len(v) for v in quelle.values())
    return {
        "fakten_gesamt": gesamt,
        "gehalten": gehalten,
        "verloren": verloren,
        "erfunden": erfunden,
        "abgeschnitten": wirkt_abgeschnitten(deutsch),
        "treue": (gehalten / gesamt) if gesamt else 1.0,
        "bestanden": not verloren and not erfunden,
    }


def wirkt_abgeschnitten(deutsch: str) -> bool:
    """Dieselbe Unterschrift, die translator.py kennt: ungerade Zahl Backticks.

    Der Uebersetzer hat dagegen inzwischen eine Sperre (3 Versuche, dann lauter
    Fehler). Ob die Sperre zur Zeit einer Probe schon stand, sieht man nur hier
    -- eine abgeschnittene Antwort ist der teuerste Verlust ueberhaupt, weil
    alles nach dem Abbruch fehlt und nicht als Luecke sichtbar ist.
    """
    return deutsch.count("`") % 2 == 1


def lade_gold(pfad: Path = GOLD_PFAD) -> dict:
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    if "proben" not in daten or "hinweis" not in daten:
        raise RuntimeError("Goldsatz ohne hinweis/proben -- Herkunft muss dranbleiben")
    return daten


def messe(*, live: bool = False, gold: Path = GOLD_PFAD, grenze: int | None = None) -> dict:
    daten = lade_gold(gold)
    proben = daten["proben"][:grenze] if grenze else daten["proben"]
    uebersetzer = None
    if live:
        # Zwei Orte, dieselbe Datei (md5 geprueft): auf dem Wirt liegt sie
        # unter "the artefact", im Container unter /opt/clayverse. Nur im
        # Container sind die Schluessel (python-dotenv) erreichbar.
        for _p in ("/opt/clayverse/clayverse", "/opt/entityos/the artefact/clayverse"):
            if Path(_p, "mistral_prestage", "translator.py").exists():
                sys.path.insert(0, _p)
                break
        from mistral_prestage import translator as uebersetzer  # noqa: E402

    ergebnisse = []
    for p in proben:
        ausfall = None
        if live:
            try:
                deutsch = uebersetzer.translate_to_german(p["caveman"])["german_translation"]
            except Exception as fehler:
                # Ein Ausfall ist kein fehlender Messwert, sondern ein
                # Messwert: der Mensch bekommt dann den Rohtext (siehe
                # _uebersetzung_mit_rueckfall in pipeline.py). Als bestanden
                # darf das nie zaehlen.
                ausfall = f"{type(fehler).__name__}: {fehler}"[:200]
                deutsch = ""
        else:
            deutsch = p["deutsch_produktion"]
        b = bewerte(p["caveman"], deutsch)
        if ausfall:
            b["bestanden"] = False
            b["ausfall"] = ausfall
        b["id"] = p["id"]
        b["deutsch"] = deutsch
        ergebnisse.append(b)

    n = len(ergebnisse)
    bestanden = sum(r["bestanden"] for r in ergebnisse)
    fakten_gesamt = sum(r["fakten_gesamt"] for r in ergebnisse)
    gehalten = sum(r["gehalten"] for r in ergebnisse)
    return {
        "quelle": "live-uebersetzt" if live else "produktionsantwort aus mv_translation_log",
        "proben": n,
        "bestanden": bestanden,
        "durchgefallen": n - bestanden,
        "bestehensquote": round(bestanden / n, 4) if n else 0.0,
        "faktentreue": round(gehalten / fakten_gesamt, 4) if fakten_gesamt else 1.0,
        "fakten_gesamt": fakten_gesamt,
        "fakten_verloren": fakten_gesamt - gehalten,
        "proben_mit_erfindung": sum(1 for r in ergebnisse if r["erfunden"]),
        "proben_abgeschnitten": sum(1 for r in ergebnisse if r["abgeschnitten"]),
        "ziel": 0.95,
        "ergebnisse": ergebnisse,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Uebersetzer Caveman->Deutsch messen")
    ap.add_argument("--live", action="store_true",
                    help="neu uebersetzen statt die gespeicherte Produktionsantwort zu messen")
    ap.add_argument("--gold", default=str(GOLD_PFAD))
    ap.add_argument("--grenze", type=int, default=None)
    ap.add_argument("--fehler-zeigen", action="store_true")
    a = ap.parse_args()
    z = messe(live=a.live, gold=Path(a.gold), grenze=a.grenze)
    kurz = {k: v for k, v in z.items() if k != "ergebnisse"}
    print(json.dumps(kurz, indent=2, ensure_ascii=False))
    if a.fehler_zeigen:
        for r in z["ergebnisse"]:
            if r["bestanden"]:
                continue
            print("---", r["id"], "treue", round(r["treue"], 3))
            for v in r["verloren"]:
                print("   VERLOREN", v["klasse"], repr(v["fakt"]))
            for e in r["erfunden"]:
                print("   ERFUNDEN", e["klasse"], repr(e["fakt"]))
