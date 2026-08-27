#!/usr/bin/env python3
"""verdichtung.py — ClayVerse verdichtet seine Datenstroeme selbst, wenn genug
angekommen ist. Keine Uhr, eine SCHWELLE.

    Aufnahme zaehlen -> Schwelle ueberschritten? -> Portion an Mistral
        -> PRUEFUNG (Schema / Quellen / Zahlen) -> anreicherung + kante
                                                -> sonst verworfen und gezaehlt

Drei Saetze, die diese Datei tragen:

  1. Der Takt kommt aus dem STOFF, nicht aus der Uhr. Der Zeitgeber schaut alle
     10 Minuten nach, arbeitet aber nur, wenn ein Strom SEINE eigene Schwelle
     ueberschritten hat. Die Schwellen sind aus der GEMESSENEN Aufnahmerate
     abgeleitet (siehe `raten`), nicht geraten: ein Strom mit 6.400 Zeilen je
     Stunde darf nicht so oft zuenden wie einer mit 8.

  2. Ein Kondensat ist ein VORSCHLAG. Es landet in `anreicherung`, nie direkt
     in `artikel` — dieselbe Regel wie in bahn.py:

         model_output_is_not_authority

  3. Ein Kondensat ERSETZT seine Quellen nicht. Es steht ueber ihnen: je Quelle
     eine Kante in `kante` (art='verdichtet_aus'), damit der Rueckweg immer
     existiert und nichts verwaist.

Die wichtigste Pruefung ist der Erfindungsmelder: jede Zahl im Kondensat muss in
mindestens einer Quelle dieser Portion vorkommen. Ein Zyklus, der nie etwas
verwirft, ist kaputt, nicht perfekt.
"""
import argparse
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DB = os.environ.get("CLAY_DB", "/var/lib/clay/wiki.db")
ENV = "/etc/clayverse/freie-zugaenge.env"
KONTINGENT = "/opt/clayverse/werkzeug/kontingent.py"
ABSENDER = "clayverse-verdichtung/1.0"

# ── DIE BAHN ───────────────────────────────────────────────────────────
# Genau eine, mit Absicht: Mistral kann ECHTES json_schema. Deshalb ist die
# Antwort maschinell pruefbar statt Fliesstext, den jemand auseinandernehmen
# muss. Das ist der ganze Grund, warum hier Mistral steht und nicht die
# schnellste Bahn.
# ⚠️ Mistral veroeffentlicht seine Freigrenzen NICHT (siehe
# bau/ZUGAENGE-GEMESSEN.md). Es steht deshalb KEINE erfundene RPM in dieser
# Datei. 429 wird abgefangen, zurueckgenommen und in vd_grenze gelernt.
# ⭐ RUECKFALL, 2026-08-21 nachgebaut. Er war seit jeher VORGESEHEN --
# `werkzeug/ratgeber.py` sagt es woertlich: "MISTRAL_API_KEY gehoert
# verdichtung.py, MISTRAL2 ist dessen Rueckfall." Gebaut war er nie.
#
# Was das gekostet hat: der Chat-Endpunkt des ersten Kontos antwortet seit
# dem 19.08. mit HTTP 402 ("Check your subscription"). Der Schluessel LEBT --
# die /models-Sonde der Schluesselwacht ist gruen -- nur Chat-Vervollstaendi-
# gungen verlangen dort ein Abo. Die Verdichtung lief deshalb alle 10 Minuten,
# meldete "gearbeitet" und richtete nichts aus; der Rueckstau wuchs auf das
# 7- bis 17-Fache der jeweiligen Schwelle. Zwei gesunde Mistral-Schluessel
# lagen die ganze Zeit daneben (MISTRAL2 gemessen 50.000 Token/min).
#
# WARUM NICHT EINFACH UMHAENGEN: die Kontingent-Ordnung dieses Systems gibt
# jedem Dienst einen EIGENEN Topf, damit sie sich nicht gegenseitig die
# Grenze wegfressen (siehe wikiarbeit.py: "Ausschliesslich GROQ3_API_KEY").
# MISTRAL3 gehoert dem Ratgeber und bleibt unangetastet. Der Rueckfall
# greift deshalb NUR, wenn der eigene Schluessel nicht arbeiten kann --
# nicht als zweiter Topf im Normalbetrieb.
RUECKFALL_ENV = "MISTRAL2_API_KEY"

# HTTP-Antworten, bei denen ein Wechsel ueberhaupt sinnvoll ist: das Konto
# darf nicht (402 Abo, 401 ungueltig, 403 gesperrt). NICHT dabei: 429 --
# eine Ratenbremse ist kein kaputtes Konto, die wird zurueckgenommen und in
# vd_grenze gelernt, wie bisher. Wer bei 429 das Konto wechselt, verlagert
# nur die Last und lernt nichts.
WECHSEL_BEI = (401, 402, 403)

BAHN = {
    "name": "mistral",
    "env": "MISTRAL_API_KEY",
    "zugang": "mistral",
    "konto": "clayverse",
    "url": "https://api.mistral.ai/v1/chat/completions",
    "modell": "mistral-small-latest",
}

# Zuschnitt einer Portion. Keine Schwellenwerte — reine Groessenbremse, damit
# eine Anfrage in ein vernuenftiges Fenster passt.
QUELLEN_JE_RUF = 20
ZEICHEN_JE_QUELLE = 700
ZEICHEN_BUDGET = 14000
RUFE_JE_ZYKLUS = 3          # Startwert; 429 senkt ihn fuer diesen Lauf
# GEMESSEN: bei 900 und bei 1200 wurde die Antwort fuer dichte Stroeme
# (protokoll) an der Grenze abgeschnitten -> halbes JSON. Die Schemazusage
# gilt nur fuer eine VOLLSTAENDIGE Antwort.
MAX_TOKEN_AUS = 2000

BUSY_MS = 30000
VERSUCHE = 8
WARTE_BASIS = 0.25


# ── SCHEMA ─────────────────────────────────────────────────────────────
# Genau das, was Mistral zugesichert bekommt. Wir GLAUBEN die Zusage nicht,
# wir pruefen sie danach mit _schema_ok gegen dieselbe Form.
SCHEMA = {
    "type": "object",
    "properties": {
        "titel": {"type": "string"},
        "kern": {"type": "string"},
        "aussagen": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "quellen": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "quellen"],
                "additionalProperties": False,
            },
        },
        "offene_fragen": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["titel", "kern", "aussagen", "offene_fragen"],
    "additionalProperties": False,
}

SYSTEM = (
    "you condense source rows into one short record. answer ONLY the json object.\n"
    "rules, hard:\n"
    "- every aussage MUST list the Q-labels it comes from, in quellen.\n"
    "- NEVER write a number that is not literally in the sources. do not count,\n"
    "  do not add, do not compute percentages, do not estimate.\n"
    "- do not invent names, paths, dates.\n"
    "- if sources say little, say little. short is fine.\n"
    "- german, no umlauts needed."
)


# ── DIE STROEME ────────────────────────────────────────────────────────
# Ein Strom ist eine Quelle laufenden Stoffs mit einer aufloesbaren Kennung.
# `zeitspalte` dient NUR der Ratenmessung, nicht der Auswahl.
def _t_baeume(r):
    return "art=%s | titel=%s | %s" % (r["art"], r["titel"] or "", r["metadaten"] or "")


def _t_protokoll(r):
    return "%s | %s" % (r["titel"] or "", r["metadaten"] or "")


def _t_taetigkeit(r):
    return "zeit=%s wirt=%s werkzeug=%s aktion=%s ziel=%s ergebnis=%s" % (
        r["zeit"], r["wirt"], r["werkzeug"], r["aktion"], r["ziel_pfad"], r["ergebnis"])


def _t_anreicherung(r):
    return "artikel=%s art=%s quelle=%s auszug=%s" % (
        r["artikel_id"], r["art"], r["quelle_url"], r["auszug"])


def _t_bahn(r):
    return "zeit=%s bahn=%s art=%s ergebnis=%s pruefung=%s antwort=%s" % (
        r["zeit"], r["bahn"], r["art"], r["ergebnis"], r["pruefung"] or "", r["antwort"] or "")


def _t_kuration(r):
    return "artikel=%s quelle=%s klasse=%s ereignis=%s" % (
        r["artikel_id"], r["quelle"], r["klasse"], r["ereignis"] or "")


STROEME = {
    "baeume": {
        "tabelle": "artikel", "id_spalte": "id", "zeitspalte": "erzeugt_am",
        "artikel_kennung": True,
        "wo": "t.quelle LIKE ?", "wo_p": ("/opt/clayverse/baeume/%",),
        "felder": "t.id AS quell_id, t.art, t.titel, t.metadaten",
        "sortierung": "t.erzeugt_am, t.id",
        "text": _t_baeume,
        "was": "Wissen aus den Projektbaeumen (Dateien der Projekte)",
    },
    "protokoll": {
        # ⚠️ NICHT erzeugt_am: die 63 Zeilen kamen in EINEM Zug in die DB, das
        # ergibt Spanne 0 und keine messbare Rate. zuletzt_bearbeitet traegt hier
        # die Zeit AUS DEM STROM selbst (zeitquelle='strom' bei allen 63) und
        # misst damit, wie schnell das Protokoll wirklich Stoff produziert.
        "tabelle": "artikel", "id_spalte": "id", "zeitspalte": "zuletzt_bearbeitet",
        "artikel_kennung": True,
        "wo": "t.quelle = ?", "wo_p": ("/opt/clayverse/bau/protokoll.jsonl",),
        "felder": "t.id AS quell_id, t.art, t.titel, t.metadaten",
        "sortierung": "t.id",
        "text": _t_protokoll,
        "was": "Bauprotokoll: was gebaut, geprueft, belegt wurde",
    },
    "taetigkeit": {
        "tabelle": "taetigkeit", "id_spalte": "id", "zeitspalte": "zeit",
        "artikel_kennung": False,
        "wo": "1=1", "wo_p": (),
        "felder": ("CAST(t.id AS TEXT) AS quell_id, t.zeit, t.wirt, t.werkzeug, "
                   "t.aktion, t.ziel_pfad, t.ergebnis"),
        "sortierung": "t.id",
        "text": _t_taetigkeit,
        "was": "Werkzeugeinsaetze der Instanzen (wer hat was womit getan)",
    },
    "anreicherung": {
        "tabelle": "anreicherung", "id_spalte": "id", "zeitspalte": "geholt_am",
        "artikel_kennung": False,
        # ⚠️ Ohne diesen Ausschluss frisst der Zyklus seine eigenen Kondensate
        # wieder auf und verdichtet Verdichtetes. Genau einmal ist genug.
        "wo": "t.art IS NOT ?", "wo_p": ("verdichtung",),
        "felder": ("CAST(t.id AS TEXT) AS quell_id, t.artikel_id, t.art, "
                   "t.quelle_url, t.auszug"),
        "sortierung": "t.id",
        "text": _t_anreicherung,
        "was": "Vorschlaege der Bahnen zu einzelnen Artikeln",
    },
    "bahn": {
        "tabelle": "bahn_lauf", "id_spalte": "id", "zeitspalte": "zeit",
        "artikel_kennung": False,
        "wo": "1=1", "wo_p": (),
        "felder": ("CAST(t.id AS TEXT) AS quell_id, t.zeit, t.bahn, t.art, "
                   "t.ergebnis, t.pruefung, t.antwort"),
        "sortierung": "t.id",
        "text": _t_bahn,
        "was": "ausgelagerte Laeufe: welche Bahn trug, was durchfiel",
    },
    "kuration": {
        "tabelle": "kuration", "id_spalte": "artikel_id", "zeitspalte": "erkannt_am",
        "artikel_kennung": True,
        "wo": "t.klasse = ?", "wo_p": ("quelle_geaendert",),
        "felder": ("t.artikel_id AS quell_id, t.artikel_id, t.quelle, t.klasse, "
                   "t.ereignis"),
        "sortierung": "t.erkannt_am, t.artikel_id",
        "text": _t_kuration,
        "was": "Quellen, die sich seit der Aufnahme geaendert haben",
    },
}


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def verbinden() -> sqlite3.Connection:
    if not os.path.exists(DB):
        raise SystemExit("FATAL: %s existiert nicht." % DB)
    c = sqlite3.connect(DB, timeout=30, isolation_level=None)
    c.execute("PRAGMA busy_timeout=%d" % BUSY_MS)
    c.row_factory = sqlite3.Row
    return c


def schreiben(c: sqlite3.Connection, sql: str, p=()) -> None:
    """Viele Schreiber auf einer WAL-DB. Sperre = warten, alles andere = laut."""
    letzter = None
    for i in range(VERSUCHE):
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute(sql, p)
            c.execute("COMMIT")
            return
        except sqlite3.OperationalError as e:
            letzter = e
            try:
                c.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            s = str(e).lower()
            if "locked" in s or "busy" in s:
                time.sleep(WARTE_BASIS * (2 ** i))
                continue
            raise
    raise RuntimeError("nach %d Versuchen gesperrt: %s" % (VERSUCHE, letzter))


def tabellen(c: sqlite3.Connection) -> None:
    schreiben(c, """CREATE TABLE IF NOT EXISTS vd_strom (
        strom            TEXT PRIMARY KEY,
        schwelle         INTEGER NOT NULL,
        rate_je_stunde   REAL,
        rate_beleg       TEXT,
        aktiv            INTEGER NOT NULL DEFAULT 1,
        angelegt         TEXT NOT NULL,
        letzte_pruefung  TEXT,
        letzter_lauf     TEXT
    )""")
    schreiben(c, """CREATE TABLE IF NOT EXISTS vd_aufnahme (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit          TEXT NOT NULL,
        strom         TEXT NOT NULL,
        neu           INTEGER NOT NULL,
        geaendert     INTEGER NOT NULL,
        offen_gesamt  INTEGER NOT NULL,
        schwelle      INTEGER NOT NULL,
        ausgeloest    INTEGER NOT NULL
    )""")
    schreiben(c, """CREATE TABLE IF NOT EXISTS vd_gesehen (
        strom            TEXT NOT NULL,
        quell_id         TEXT NOT NULL,
        zeit             TEXT NOT NULL,
        anreicherung_id  INTEGER,
        PRIMARY KEY (strom, quell_id)
    )""")
    schreiben(c, """CREATE TABLE IF NOT EXISTS vd_lauf (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit             TEXT NOT NULL,
        strom            TEXT NOT NULL,
        quellen          INTEGER NOT NULL,
        bahn             TEXT,
        modell           TEXT,
        http             INTEGER,
        dauer_ms         REAL,
        token_ein        INTEGER,
        token_aus        INTEGER,
        ergebnis         TEXT NOT NULL,
        grund            TEXT,
        detail           TEXT,
        anreicherung_id  INTEGER,
        verdichtung_id   TEXT
    )""")
    schreiben(c, """CREATE TABLE IF NOT EXISTS vd_grenze (
        zugang            TEXT PRIMARY KEY,
        anzahl_429        INTEGER NOT NULL DEFAULT 0,
        erste_429         TEXT,
        letzte_429        TEXT,
        letzte_wartezeit  REAL,
        rufe_ohne_429     INTEGER NOT NULL DEFAULT 0,
        bemerkung         TEXT
    )""")
    # Merkposten: mit welcher Portionsgroesse dieser Strom zuletzt durchkam.
    # Ohne den verbrennt ein dichter Strom in JEDEM Zyklus wieder zwei Rufe,
    # bis er sich auf dieselbe Groesse heruntergetastet hat.
    if not any(r[1] == "portion" for r in c.execute("PRAGMA table_info(vd_strom)")):
        schreiben(c, "ALTER TABLE vd_strom ADD COLUMN portion INTEGER")
    schreiben(c, "CREATE INDEX IF NOT EXISTS idx_vd_lauf_strom ON vd_lauf(strom, zeit)")
    schreiben(c, "CREATE INDEX IF NOT EXISTS idx_vd_aufnahme_strom ON vd_aufnahme(strom, zeit)")


# ── RATEN MESSEN ───────────────────────────────────────────────────────
def rate_messen(c: sqlite3.Connection, strom: str):
    """Gemessene Aufnahmerate in Zeilen je Stunde. Kein Schaetzwert.

    Gemessen wird ueber die Zeitspalte des Stroms selbst: (Anzahl-1) Zwischen-
    raeume auf der Spanne zwischen erster und letzter Zeile. Ist die Spanne 0
    oder gibt es keine brauchbaren Zeiten, ist die Rate UNBEKANNT — dann wird
    hier KEINE Zahl erfunden.
    """
    s = STROEME[strom]
    sql = ("SELECT COUNT(*) AS n, MIN(t.%s) AS a, MAX(t.%s) AS b FROM %s t WHERE %s"
           % (s["zeitspalte"], s["zeitspalte"], s["tabelle"], s["wo"]))
    r = c.execute(sql, s["wo_p"]).fetchone()
    n, a, b = r["n"], r["a"], r["b"]
    if not n or n < 2 or not a or not b:
        return None, "zu wenige Zeilen mit Zeit (n=%s) — UNBEKANNT" % n
    try:
        ta = datetime.fromisoformat(str(a).replace("Z", "+00:00"))
        tb = datetime.fromisoformat(str(b).replace("Z", "+00:00"))
    except ValueError:
        return None, "Zeitspalte nicht lesbar (%r .. %r) — UNBEKANNT" % (a, b)
    span_h = (tb - ta).total_seconds() / 3600.0
    if span_h <= 0:
        return None, "Spanne 0 (alle %d Zeilen tragen dieselbe Zeit) — UNBEKANNT" % n
    rate = n / span_h
    return rate, ("%d Zeilen ueber %.3f h (%s .. %s)" % (n, span_h, a, b))


def cmd_raten(a) -> None:
    c = verbinden()
    tabellen(c)
    print("Gemessene Aufnahmerate je Strom (Zeilen/Stunde) und die daraus")
    print("abgeleitete Schwelle = Aufnahme EINER Stunde, aufgerundet.\n")
    for strom in STROEME:
        rate, beleg = rate_messen(c, strom)
        if rate is None:
            print("  %-13s RATE UNBEKANNT — %s" % (strom, beleg))
            continue
        print("  %-13s %10.1f /h   Schwelle %7d   [%s]"
              % (strom, rate, math.ceil(rate), beleg))
    c.close()


def cmd_init(a) -> None:
    """Legt die Schwellen an — abgeleitet, nicht getippt."""
    c = verbinden()
    tabellen(c)
    for strom in STROEME:
        rate, beleg = rate_messen(c, strom)
        aktiv = 1 if rate is not None else 0
        schwelle = math.ceil(rate) if rate is not None else 0
        vorhanden = c.execute("SELECT strom FROM vd_strom WHERE strom=?",
                              (strom,)).fetchone()
        if vorhanden and not a.neu:
            print("  %-13s bleibt (init laesst Bestehendes stehen, --neu ueberschreibt)"
                  % strom)
            continue
        schreiben(c, """INSERT INTO vd_strom
            (strom, schwelle, rate_je_stunde, rate_beleg, aktiv, angelegt,
             letzte_pruefung, letzter_lauf)
            VALUES (?,?,?,?,?,?,NULL,NULL)
            ON CONFLICT(strom) DO UPDATE SET
                schwelle=excluded.schwelle,
                rate_je_stunde=excluded.rate_je_stunde,
                rate_beleg=excluded.rate_beleg,
                aktiv=excluded.aktiv""",
                  (strom, schwelle, rate, beleg, aktiv, jetzt()))
        print("  %-13s Schwelle %7d  (Rate %s)"
              % (strom, schwelle, ("%.1f/h" % rate) if rate else "UNBEKANNT"))
    c.close()


def cmd_schwelle(a) -> None:
    c = verbinden()
    tabellen(c)
    schreiben(c, "UPDATE vd_strom SET schwelle=? WHERE strom=?", (a.wert, a.strom))
    print("Schwelle %s = %d" % (a.strom, a.wert))
    c.close()


# ── AUFNAHME ZAEHLEN ───────────────────────────────────────────────────
def geaenderte_nachfuehren(c: sqlite3.Connection) -> dict:
    """Eine Quelle, die sich geaendert hat, ist wieder frischer Stoff.

    Ihr `gesehen`-Eintrag wird zurueckgenommen — nur wenn die Aenderung NACH
    dem Verdichten erkannt wurde. Das alte Kondensat bleibt bestehen; es wird
    nicht geloescht, nur ueberholt.
    """
    raus = {}
    for strom, s in STROEME.items():
        if not s["artikel_kennung"]:
            continue
        rows = c.execute(
            "SELECT g.quell_id FROM vd_gesehen g JOIN kuration k "
            "ON k.artikel_id = g.quell_id "
            "WHERE g.strom = ? AND k.klasse = ? AND k.zuletzt_geprueft_am > g.zeit",
            (strom, "quelle_geaendert")).fetchall()
        for r in rows:
            schreiben(c, "DELETE FROM vd_gesehen WHERE strom=? AND quell_id=?",
                      (strom, r["quell_id"]))
        if rows:
            raus[strom] = len(rows)
    return raus


def offen_zaehlen(c: sqlite3.Connection, strom: str) -> int:
    s = STROEME[strom]
    sql = ("SELECT COUNT(*) AS n FROM %s t "
           "LEFT JOIN vd_gesehen g ON g.strom = ? AND g.quell_id = t.%s "
           "WHERE %s AND g.quell_id IS NULL"
           % (s["tabelle"], s["id_spalte"], s["wo"]))
    return c.execute(sql, (strom,) + s["wo_p"]).fetchone()["n"]


def offen_holen(c: sqlite3.Connection, strom: str, limit: int):
    s = STROEME[strom]
    sql = ("SELECT %s FROM %s t "
           "LEFT JOIN vd_gesehen g ON g.strom = ? AND g.quell_id = t.%s "
           "WHERE %s AND g.quell_id IS NULL ORDER BY %s LIMIT ?"
           % (s["felder"], s["tabelle"], s["id_spalte"], s["wo"], s["sortierung"]))
    return c.execute(sql, (strom,) + s["wo_p"] + (limit,)).fetchall()


# ── PRUEFUNG ───────────────────────────────────────────────────────────
ZAHL = re.compile(r"\d+(?:[.,]\d+)?")
QLABEL = re.compile(r"\bQ\d+\b")


def zahl_marken(text: str) -> list:
    """Alle Zahlen eines Textes, roh. Q-Marken vorher raus: 'Q7' ist eine
    Fussnote, keine Behauptung."""
    return ZAHL.findall(QLABEL.sub(" ", text or ""))


def schluessel(roh: str) -> set:
    """Vergleichsformen EINER Zahl.

    ⚠️ GEMESSEN an echten Antworten: das Modell schreibt deutsch, also '4.957'
    fuer die 4957 aus der Quelle. Ohne die trennerfreie Form meldet der
    Erfindungsmelder korrekte Zahlen als erfunden — genau das ist beim ersten
    Lauf passiert (1.000, 4.957, 14.268 ...). Deshalb traegt jede Zahl mehrere
    Schluessel, und ein Treffer in EINEM davon genuegt.
    """
    k = {roh, roh.replace(",", ".")}
    nur = re.sub(r"[.,]", "", roh)
    if nur:
        k.add(nur)
        k.add(nur.lstrip("0") or "0")
    try:
        f = float(roh.replace(",", "."))
        k.add(("%d" % f) if f == int(f) else repr(f))
    except ValueError:
        pass
    return k


def zahlen(text: str) -> set:
    """Alle Vergleichsformen aller Zahlen eines Textes (fuer die Quellseite)."""
    raus = set()
    for m in zahl_marken(text):
        raus |= schluessel(m)
    return raus


def _typ_ok(wert, schema) -> bool:
    t = schema["type"]
    if t == "string":
        return isinstance(wert, str)
    if t == "array":
        if not isinstance(wert, list):
            return False
        return all(_typ_ok(x, schema["items"]) for x in wert)
    if t == "object":
        if not isinstance(wert, dict):
            return False
        for k in schema.get("required", []):
            if k not in wert:
                return False
        if schema.get("additionalProperties") is False:
            if set(wert) - set(schema.get("properties", {})):
                return False
        for k, v in wert.items():
            if k in schema.get("properties", {}) and not _typ_ok(v, schema["properties"][k]):
                return False
        return True
    return False


def schema_ok(d) -> bool:
    """Mistrals Zusage wird NACHGERECHNET, nicht geglaubt."""
    return _typ_ok(d, SCHEMA)


def pruefe(c: sqlite3.Connection, strom: str, d: dict, marken: dict, quell_text: str):
    """(gut, grund, detail). Reihenfolge wie befohlen: Schema, Quellen, Zahlen."""
    # a) Schema
    if not schema_ok(d):
        return False, "schema_bruch", "Antwort erfuellt das zugesicherte Schema nicht"
    if not d["aussagen"]:
        return False, "leer", "keine einzige Aussage"

    # b) jede Aussage nennt mindestens eine Quelle, die es WIRKLICH gibt
    s = STROEME[strom]
    for i, au in enumerate(d["aussagen"]):
        roh_marken = []
        for q in au["quellen"]:
            m = QLABEL.search(str(q))
            if m:
                roh_marken.append(m.group())
        ids = [marken[m] for m in roh_marken if m in marken]
        if not ids:
            return (False, "quelle_unbekannt",
                    "Aussage %d nennt keine Marke aus dieser Portion: %r"
                    % (i, au["quellen"][:4]))
        echt = 0
        for qid in ids:
            r = c.execute("SELECT 1 FROM %s WHERE %s = ? LIMIT 1"
                          % (s["tabelle"], s["id_spalte"]), (qid,)).fetchone()
            if r:
                echt += 1
        if echt == 0:
            return (False, "quelle_existiert_nicht",
                    "Aussage %d nennt nur Kennungen ohne Zeile in %s: %r"
                    % (i, s["tabelle"], ids[:4]))

    # c) DER ERFINDUNGSMELDER: jede Zahl im Kondensat muss in einer Quelle stehen
    hat = zahlen(quell_text)
    text = d["titel"] + " " + d["kern"] + " " + " ".join(
        a["text"] for a in d["aussagen"]) + " " + " ".join(d["offene_fragen"])
    erfunden = sorted({m for m in zahl_marken(text) if not (schluessel(m) & hat)})
    if erfunden:
        return (False, "zahl_erfunden",
                "Zahlen ohne Quelle: %s" % ", ".join(erfunden[:8]))
    return True, None, None


# ── DIE BAHN RUFEN ─────────────────────────────────────────────────────
def umgebung() -> dict:
    d = {}
    try:
        for z in open(ENV, encoding="utf-8"):
            z = z.strip()
            if z and not z.startswith("#") and "=" in z:
                k, v = z.split("=", 1)
                d[k.strip()] = v.strip()
    except OSError:
        pass
    return d


def darf(menge: int):
    try:
        r = subprocess.run(["python3", KONTINGENT, "darf", "--konto", BAHN["konto"],
                            "--zugang", BAHN["zugang"], "--menge", str(menge)],
                           capture_output=True, text=True, timeout=30)
        for z in r.stdout.splitlines():
            if "erlaubt" in z and "von" in z:
                return int(float(z.split()[0])), z.strip()
        return menge, "keine Antwort vom Kontingentbuch — vorsichtshalber erlaubt"
    except Exception as e:
        return 0, "Kontingentbuch nicht erreichbar: %s" % e


def buchen(menge: float, zweck: str) -> None:
    try:
        subprocess.run(["python3", KONTINGENT, "buchen", "--konto", BAHN["konto"],
                        "--zugang", BAHN["zugang"], "--menge", str(menge),
                        "--zweck", zweck], capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def rufen(schluessel: str, frage: str) -> dict:
    body = {
        "model": BAHN["modell"],
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": frage}],
        "max_tokens": MAX_TOKEN_AUS,
        "temperature": 0,
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "verdichtung",
                                            "schema": SCHEMA, "strict": True}},
    }
    req = urllib.request.Request(
        BAHN["url"], data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + schluessel,
                 "Content-Type": "application/json",
                 "User-Agent": ABSENDER})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            roh = json.loads(r.read().decode())
            u = roh.get("usage") or {}
            w = roh["choices"][0]
            return {"ok": True, "http": r.status,
                    "ms": (time.perf_counter() - t0) * 1000,
                    "text": (w["message"]["content"] or "").strip(),
                    # ⚠️ GEMESSEN: Mistrals Schemazusage gilt nur fuer eine
                    # VOLLSTAENDIGE Antwort. Wird sie an max_tokens abgeschnitten,
                    # kommt halbes JSON zurueck. Das ist unser Fehler, nicht seine
                    # Luege — deshalb ein eigener Grund und ein zweiter Versuch
                    # mit kleinerer Portion.
                    "ende": w.get("finish_reason"),
                    "ein": u.get("prompt_tokens"), "aus": u.get("completion_tokens")}
    except urllib.error.HTTPError as e:
        warte = None
        try:
            warte = float(e.headers.get("Retry-After") or 0) or None
        except (TypeError, ValueError):
            warte = None
        return {"ok": False, "http": e.code, "ms": (time.perf_counter() - t0) * 1000,
                "fehler": e.read()[:300].decode("utf-8", "replace"), "warte": warte}
    except Exception as e:
        return {"ok": False, "http": 0, "ms": (time.perf_counter() - t0) * 1000,
                "fehler": str(e)[:300], "warte": None}


def grenze_lernen(c: sqlite3.Connection, http: int, warte) -> None:
    """Was der Anbieter nicht veroeffentlicht, lernen wir aus seinen Absagen."""
    if http == 429:
        schreiben(c, """INSERT INTO vd_grenze
            (zugang, anzahl_429, erste_429, letzte_429, letzte_wartezeit,
             rufe_ohne_429, bemerkung)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(zugang) DO UPDATE SET
                anzahl_429 = vd_grenze.anzahl_429 + 1,
                letzte_429 = excluded.letzte_429,
                letzte_wartezeit = excluded.letzte_wartezeit,
                rufe_ohne_429 = 0""",
                  (BAHN["zugang"], 1, jetzt(), jetzt(), warte, 0,
                   "Grenze vom Anbieter NICHT veroeffentlicht — hier nur Beobachtung"))
    else:
        schreiben(c, """INSERT INTO vd_grenze
            (zugang, anzahl_429, erste_429, letzte_429, letzte_wartezeit,
             rufe_ohne_429, bemerkung)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(zugang) DO UPDATE SET
                rufe_ohne_429 = vd_grenze.rufe_ohne_429 + 1""",
                  (BAHN["zugang"], 0, None, None, None, 1,
                   "Grenze vom Anbieter NICHT veroeffentlicht — hier nur Beobachtung"))


# ── EIN KONDENSAT ──────────────────────────────────────────────────────
def portion_bauen(strom: str, rows):
    """(frage, marken, quell_text, benutzt) — Q-Marken sind der Rueckweg."""
    s = STROEME[strom]
    marken, teile, roh = {}, [], []
    benutzt = []
    zeichen = 0
    for i, r in enumerate(rows, 1):
        t = s["text"](r)
        t = " ".join(str(t).split())[:ZEICHEN_JE_QUELLE]
        if zeichen + len(t) > ZEICHEN_BUDGET and benutzt:
            break
        marke = "Q%d" % i
        marken[marke] = r["quell_id"]
        teile.append("[%s] %s" % (marke, t))
        roh.append(t)
        benutzt.append(r["quell_id"])
        zeichen += len(t)
    # ⚠️ KEINE Zahl in den eigenen Prompt schreiben. Sonst schreibt das Modell
    # sie ab und der Erfindungsmelder schlaegt auf die eigene Kopfzeile an.
    frage = ("strom=%s (%s)\nverdichte diese quellzeilen zu EINEM datensatz.\n\n%s"
             % (strom, s["was"], "\n".join(teile)))
    return frage, marken, "\n".join(roh), benutzt


def verdichtung_id(c: sqlite3.Connection, strom: str) -> str:
    stempel = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    grund = "VD-%s-%s" % (strom, stempel)
    n = 0
    kand = grund
    while c.execute("SELECT 1 FROM vd_lauf WHERE verdichtung_id=? LIMIT 1",
                    (kand,)).fetchone():
        n += 1
        kand = "%s-%d" % (grund, n)
    return kand


def einen_ruf(c: sqlite3.Connection, strom: str, schluessel: str,
              quellen_max: int = QUELLEN_JE_RUF) -> str:
    """Eine Portion verdichten.

    Rueckgabe: angenommen | verworfen | abgeschnitten | fehler | leer | 429
    """
    rows = offen_holen(c, strom, quellen_max)
    if not rows:
        return "leer"
    frage, marken, quell_text, benutzt = portion_bauen(strom, rows)

    erlaubt, grund = darf(1)
    if erlaubt <= 0:
        print("   Kontingentbuch sperrt: %s" % grund)
        return "fehler"

    res = rufen(schluessel, frage)
    # ⭐ RUECKFALL -- siehe RUECKFALL_ENV oben. Er sitzt hier und nicht im
    # Zyklus, weil nur hier der Ruf und seine Frage beisammen sind. Ein
    # erster Versuch, ihn eine Ebene hoeher zu legen, waere ein NameError
    # ausschliesslich auf dem FEHLERPFAD geworden -- also genau in dem
    # Moment, in dem man ihn braucht, und bis dahin unsichtbar.
    #
    # Genau EIN Wechsel, dann ist Schluss: durchprobieren wuerde die Ursache
    # verschleiern. `grenze_lernen` sieht bewusst das ERGEBNIS nach dem
    # Wechsel, damit die 429-Kurve zum tatsaechlich benutzten Konto passt.
    if (res.get("http") in WECHSEL_BEI) and not res.get("ok"):
        rueckfall = umgebung().get(RUECKFALL_ENV)
        if rueckfall and rueckfall != schluessel:
            print("   RUECKFALL auf %s (eigenes Konto darf nicht: HTTP %s)"
                  % (RUECKFALL_ENV, res.get("http")))
            res2 = rufen(rueckfall, frage)
            if res2.get("ok"):
                print("   Rueckfall trug.")
                res = res2
            else:
                print("   Rueckfall trug NICHT: HTTP %s" % res2.get("http"))
    grenze_lernen(c, res.get("http") or 0, res.get("warte"))
    buchen(1, "verdichtung/%s" % strom)

    if not res["ok"]:
        schreiben(c, """INSERT INTO vd_lauf
            (zeit, strom, quellen, bahn, modell, http, dauer_ms, token_ein,
             token_aus, ergebnis, grund, detail, anreicherung_id, verdichtung_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (jetzt(), strom, len(benutzt), BAHN["name"], BAHN["modell"],
                   res["http"], round(res["ms"], 1), None, None, "fehler",
                   "http_%s" % res["http"], str(res.get("fehler"))[:300], None, None))
        if res["http"] == 429:
            w = res.get("warte") or 30.0
            print("   429 — Decke beobachtet, %.0f s zurueck." % w)
            time.sleep(min(w, 60.0))
            return "429"
        print("   Bahnfehler HTTP %s: %s" % (res["http"], str(res.get("fehler"))[:120]))
        return "fehler"

    abgeschnitten = res.get("ende") == "length"
    try:
        d = json.loads(res["text"])
    except Exception as e:
        d = None
        gut = False
        kgrund = "abgeschnitten" if abgeschnitten else "kein_json"
        detail = ("Antwort an max_tokens=%d abgeschnitten, JSON unvollstaendig"
                  % MAX_TOKEN_AUS) if abgeschnitten else ("Antwort ist kein JSON: %s" % e)
    else:
        gut, kgrund, detail = pruefe(c, strom, d, marken, quell_text)
        if abgeschnitten and gut:
            gut, kgrund = False, "abgeschnitten"
            detail = "vollstaendig geparst, aber an max_tokens beschnitten"

        # EINE Reparatur bei erfundenen Zahlen. Der haeufigste Fall ist, dass
        # das Modell die Quellen ZAEHLT ("20 Dokumente") — eine Zahl, die in
        # keiner Quelle steht. Die Quellen dafuer wegzuwerfen waere teurer als
        # ein zweiter, gezielter Ruf. Genau einer, nicht in Schleife.
        if not gut and kgrund == "zahl_erfunden":
            frage2 = (frage + "\n\nDU HAST GEGEN DIE REGEL VERSTOSSEN. "
                      + str(detail) + ". schreibe es neu und lasse JEDE zahl weg, "
                      "die nicht woertlich in einer quellzeile oben steht. "
                      "zaehle nichts, rechne nichts.")
            res2 = rufen(schluessel, frage2)
            grenze_lernen(c, res2.get("http") or 0, res2.get("warte"))
            buchen(1, "verdichtung/%s/reparatur" % strom)
            schreiben(c, """INSERT INTO vd_lauf
                (zeit, strom, quellen, bahn, modell, http, dauer_ms, token_ein,
                 token_aus, ergebnis, grund, detail, anreicherung_id, verdichtung_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (jetzt(), strom, len(benutzt), BAHN["name"], BAHN["modell"],
                       res["http"], round(res["ms"], 1), res.get("ein"),
                       res.get("aus"), "verworfen", kgrund, detail, None, None))
            print("   Reparaturruf nach %s: %s" % (kgrund, str(detail)[:80]))
            if res2["ok"]:
                res = res2
                try:
                    d = json.loads(res2["text"])
                except Exception as e:
                    gut, kgrund, detail = False, "kein_json", "Reparatur kein JSON: %s" % e
                else:
                    gut, kgrund, detail = pruefe(c, strom, d, marken, quell_text)
                    if gut:
                        kgrund = None
                    else:
                        kgrund = kgrund + "_nach_reparatur"
            else:
                kgrund, detail = "reparatur_fehler", str(res2.get("fehler"))[:200]

    # Abgeschnitten ist KEIN Urteil ueber die Quellen. Sie bleiben unverbraucht,
    # damit der naechste Ruf sie mit kleinerer Portion noch einmal bekommt.
    nochmal = bool(abgeschnitten and len(benutzt) > 4)
    if nochmal:
        schreiben(c, """INSERT INTO vd_lauf
            (zeit, strom, quellen, bahn, modell, http, dauer_ms, token_ein, token_aus,
             ergebnis, grund, detail, anreicherung_id, verdichtung_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (jetzt(), strom, len(benutzt), BAHN["name"], BAHN["modell"],
                   res["http"], round(res["ms"], 1), res.get("ein"), res.get("aus"),
                   "verworfen", kgrund, detail, None, None))
        print("   abgeschnitten — Portion wird halbiert, Quellen bleiben offen")
        return "abgeschnitten"

    vid = verdichtung_id(c, strom) if gut else None
    anr_id = None
    if gut:
        # ⚠️ Der Vorschlag landet in anreicherung, NICHT in artikel. Erst die
        # Kuration hebt ihn. Die Quellen bleiben unangetastet.
        nutzlast = {
            "verdichtung_id": vid, "strom": strom, "modell": BAHN["modell"],
            "quellen": [marken[m] for m in sorted(marken, key=lambda x: int(x[1:]))],
            "titel": d["titel"], "kern": d["kern"],
            "aussagen": d["aussagen"], "offene_fragen": d["offene_fragen"],
        }
        schreiben(c, """INSERT INTO anreicherung
            (artikel_id, quelle_url, art, auszug, geholt_am, hash)
            VALUES (?,?,?,?,?,?)""",
                  (vid, "bahn://%s/%s" % (BAHN["name"], BAHN["modell"]),
                   "verdichtung", json.dumps(nutzlast, ensure_ascii=False),
                   jetzt(), ""))
        anr_id = c.execute("SELECT id FROM anreicherung WHERE artikel_id=? "
                           "ORDER BY id DESC LIMIT 1", (vid,)).fetchone()["id"]
        # je Quelle eine Kante — der Rueckweg. art='verdichtet_aus' gehoert
        # keinem anderen Werkzeug, kanten.py loescht es nicht mit.
        for qid in benutzt:
            ziel = qid if STROEME[strom]["artikel_kennung"] else "%s:%s" % (
                STROEME[strom]["tabelle"], qid)
            schreiben(c, """INSERT INTO kante
                (von, nach, art, beleg, konfidenz, erzeugt_am, zeitquelle)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(von, nach, art) DO NOTHING""",
                      (vid, ziel, "verdichtet_aus",
                       "anreicherung:%s strom=%s" % (anr_id, strom),
                       None, jetzt(), "verdichtung"))

    # Verbraucht ist verbraucht: auch verworfene Portionen werden vermerkt,
    # sonst laeuft derselbe Stoff endlos in dieselbe Verwerfung.
    for qid in benutzt:
        schreiben(c, """INSERT INTO vd_gesehen (strom, quell_id, zeit, anreicherung_id)
            VALUES (?,?,?,?)
            ON CONFLICT(strom, quell_id) DO UPDATE SET
                zeit=excluded.zeit, anreicherung_id=excluded.anreicherung_id""",
                  (strom, qid, jetzt(), anr_id))

    schreiben(c, """INSERT INTO vd_lauf
        (zeit, strom, quellen, bahn, modell, http, dauer_ms, token_ein, token_aus,
         ergebnis, grund, detail, anreicherung_id, verdichtung_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (jetzt(), strom, len(benutzt), BAHN["name"], BAHN["modell"],
               res["http"], round(res["ms"], 1), res.get("ein"), res.get("aus"),
               "angenommen" if gut else "verworfen", kgrund, detail, anr_id, vid))
    schreiben(c, "UPDATE vd_strom SET letzter_lauf=? WHERE strom=?", (jetzt(), strom))

    if gut:
        print("   angenommen %s  %d Quellen  %s ein / %s aus"
              % (vid, len(benutzt), res.get("ein"), res.get("aus")))
        return "angenommen"
    print("   verworfen (%s): %s" % (kgrund, str(detail)[:120]))
    return "verworfen"


# ── DER ZYKLUS ─────────────────────────────────────────────────────────
def cmd_zyklus(a) -> None:
    """Der autonome Griff. Schaut nach, arbeitet nur bei ueberschrittener Schwelle."""
    c = verbinden()
    tabellen(c)
    if not c.execute("SELECT 1 FROM vd_strom LIMIT 1").fetchone():
        print("vd_strom leer — erst 'init' laufen lassen.")
        c.close()
        return

    zurueckgenommen = geaenderte_nachfuehren(c)
    u = umgebung()
    schluessel = u.get(BAHN["env"])
    gearbeitet = False
    zeile = []

    for row in c.execute("SELECT strom, schwelle, aktiv, portion FROM vd_strom "
                         "ORDER BY strom").fetchall():
        strom = row["strom"]
        if strom not in STROEME:
            continue
        offen = offen_zaehlen(c, strom)
        geaend = zurueckgenommen.get(strom, 0)
        schwelle = row["schwelle"]
        aus = 1 if (row["aktiv"] and schwelle > 0 and offen >= schwelle) else 0
        schreiben(c, "UPDATE vd_strom SET letzte_pruefung=? WHERE strom=?",
                  (jetzt(), strom))

        letzte = c.execute("SELECT neu, geaendert FROM vd_aufnahme WHERE strom=? "
                           "ORDER BY id DESC LIMIT 1", (strom,)).fetchone()
        if aus or letzte is None or letzte["neu"] != offen or letzte["geaendert"] != geaend:
            schreiben(c, """INSERT INTO vd_aufnahme
                (zeit, strom, neu, geaendert, offen_gesamt, schwelle, ausgeloest)
                VALUES (?,?,?,?,?,?,?)""",
                      (jetzt(), strom, offen, geaend, offen, schwelle, aus))
        zeile.append("%s %d/%d%s" % (strom, offen, schwelle, "!" if aus else ""))

        if not aus or a.nur_zaehlen:
            continue
        if not schluessel:
            print("KEIN SCHLUESSEL fuer %s — kein Aufruf." % BAHN["name"])
            continue

        gearbeitet = True
        print("ZUENDET %s: %d offen >= Schwelle %d" % (strom, offen, schwelle))
        rufe = a.rufe if a.rufe else RUFE_JE_ZYKLUS
        portion = row["portion"] or QUELLEN_JE_RUF
        for _ in range(rufe):
            erg = einen_ruf(c, strom, schluessel, portion)
            if erg == "abgeschnitten":
                portion = max(4, portion // 2)
                schreiben(c, "UPDATE vd_strom SET portion=? WHERE strom=?",
                          (portion, strom))
                continue
            if erg == "angenommen" and portion < QUELLEN_JE_RUF:
                # vorsichtig wieder aufmachen: sonst bleibt ein Strom fuer immer
                # auf der Notgroesse stehen, die ein einzelner langer Eintrag
                # erzwungen hat.
                portion += 1
                schreiben(c, "UPDATE vd_strom SET portion=? WHERE strom=?",
                          (portion, strom))
            if erg in ("leer", "429", "fehler"):
                break

    # ⚠️ LEBENSZEICHEN. Auch wenn nichts zu tun war. Ohne diese Zeile ist
    # 'ruht' von 'tot' nicht zu unterscheiden — das hat hier schon geschadet.
    if a.nur_zaehlen:
        lage = "nur gezaehlt (--nur-zaehlen)"
    elif gearbeitet:
        lage = "gearbeitet"
    else:
        lage = "nichts ueber der Schwelle"
    print("LEBENSZEICHEN %s | %s | %s" % (jetzt(), lage, " · ".join(zeile)))
    c.close()


def cmd_stand(a) -> None:
    c = verbinden()
    tabellen(c)
    print("== Stroeme ==")
    print("  %-13s %9s %9s %10s %7s  %-19s %s"
          % ("Strom", "offen", "Schwelle", "Rate/h", "Portion",
             "letzte Pruefung", "letzter Lauf"))
    for r in c.execute("SELECT strom, schwelle, rate_je_stunde, aktiv, portion, "
                       "letzte_pruefung, letzter_lauf FROM vd_strom ORDER BY strom"):
        if r["strom"] not in STROEME:
            continue
        offen = offen_zaehlen(c, r["strom"])
        print("  %-13s %9d %9d %10s %7d  %-19s %s"
              % (r["strom"], offen, r["schwelle"],
                 ("%.1f" % r["rate_je_stunde"]) if r["rate_je_stunde"] else "UNBEKANNT",
                 r["portion"] or QUELLEN_JE_RUF,
                 (r["letzte_pruefung"] or "-")[:19], (r["letzter_lauf"] or "-")[:19]))

    print("\n== Zyklen je Strom ==")
    for r in c.execute("SELECT strom, COUNT(*) n, "
                       "SUM(ergebnis='angenommen') an, SUM(ergebnis='verworfen') ver, "
                       "SUM(ergebnis='fehler') fe, SUM(COALESCE(token_ein,0)) te, "
                       "SUM(COALESCE(token_aus,0)) ta, SUM(quellen) q "
                       "FROM vd_lauf GROUP BY strom ORDER BY strom"):
        print("  %-13s %3d Rufe · angenommen %d · verworfen %d · Fehler %d · "
              "%d Quellen · Token ein %d aus %d"
              % (r["strom"], r["n"], r["an"], r["ver"], r["fe"], r["q"] or 0,
                 r["te"], r["ta"]))

    print("\n== Verwerfungen nach Grund ==")
    leer = True
    for r in c.execute("SELECT grund, COUNT(*) n FROM vd_lauf "
                       "WHERE ergebnis IN (?,?) GROUP BY grund ORDER BY n DESC",
                       ("verworfen", "fehler")):
        leer = False
        print("  %4d x %s" % (r["n"], r["grund"]))
    if leer:
        print("  keine. ⚠️ Ein Zyklus, der NIE verwirft, ist verdaechtig, nicht gut.")

    print("\n== Aufnahme (letzte 12 Messpunkte) ==")
    for r in c.execute("SELECT zeit, strom, neu, geaendert, schwelle, ausgeloest "
                       "FROM vd_aufnahme ORDER BY id DESC LIMIT 12"):
        print("  %s %-13s offen %6d (geaendert %d) / Schwelle %6d %s"
              % (r["zeit"][:19], r["strom"], r["neu"], r["geaendert"],
                 r["schwelle"], "ZUENDET" if r["ausgeloest"] else ""))

    print("\n== Kondensate ==")
    n = c.execute("SELECT COUNT(*) n FROM anreicherung WHERE art=?",
                  ("verdichtung",)).fetchone()["n"]
    k = c.execute("SELECT COUNT(*) n FROM kante WHERE art=?",
                  ("verdichtet_aus",)).fetchone()["n"]
    print("  %d in anreicherung (art='verdichtung', noch NICHT in artikel) · "
          "%d Rueckkanten" % (n, k))

    print("\n== beobachtete Decke (Anbieter veroeffentlicht keine) ==")
    r = c.execute("SELECT zugang, anzahl_429, letzte_429, letzte_wartezeit, "
                  "rufe_ohne_429 FROM vd_grenze").fetchall()
    if not r:
        print("  noch keine Beobachtung")
    for x in r:
        print("  %-10s 429 gesehen: %d (zuletzt %s, Wartewunsch %s) · "
              "Rufe seit dem letzten 429: %d"
              % (x["zugang"], x["anzahl_429"], x["letzte_429"] or "-",
                 x["letzte_wartezeit"] if x["letzte_wartezeit"] is not None else "UNBEKANNT",
                 x["rufe_ohne_429"]))
    c.close()


def cmd_zeigen(a) -> None:
    c = verbinden()
    r = c.execute("SELECT id, artikel_id, auszug, geholt_am FROM anreicherung "
                  "WHERE art=? ORDER BY id DESC LIMIT ?",
                  ("verdichtung", a.anzahl)).fetchall()
    for x in r:
        print("── %s  (anreicherung #%d, %s)" % (x["artikel_id"], x["id"], x["geholt_am"]))
        try:
            d = json.loads(x["auszug"])
            print("   %s" % d["titel"])
            print("   %s" % d["kern"])
            for au in d["aussagen"]:
                print("    · %s   [%s]" % (au["text"], ", ".join(au["quellen"])))
            for f in d["offene_fragen"]:
                print("    ? %s" % f)
            print("   Quellen: %s" % ", ".join(d["quellen"][:6]))
        except Exception as e:
            print("   (nicht lesbar: %s)" % e)
    c.close()


def cmd_selbsttest(a) -> None:
    """Beweist mechanisch, dass die Pruefung ueberhaupt ablehnen KANN.

    Ohne diesen Beweis ist eine Annahmequote von 100 % nicht von einer
    ausgeschalteten Pruefung zu unterscheiden. Kein Modellaufruf, kein Schreiben.
    """
    c = verbinden()
    tabellen(c)
    strom = "protokoll"
    echt = c.execute("SELECT id FROM artikel WHERE quelle = ? LIMIT 1",
                     ("/opt/clayverse/bau/protokoll.jsonl",)).fetchone()
    if not echt:
        print("kein Artikel aus dem Protokollstrom vorhanden — Test nicht moeglich")
        c.close()
        return
    marken = {"Q1": echt["id"], "Q2": "gibt-es-nicht-" + echt["id"]}
    quell_text = "der lauf dauerte 63 sekunden und fand 11 zeilen, 14268 gesamt"

    faelle = [
        ("Schema: Pflichtfeld fehlt",
         {"titel": "t", "kern": "k", "aussagen": [{"text": "a", "quellen": ["Q1"]}]},
         "schema_bruch"),
        ("Schema: Feld zu viel",
         {"titel": "t", "kern": "k", "offene_fragen": [],
          "aussagen": [{"text": "a", "quellen": ["Q1"]}], "extra": 1},
         "schema_bruch"),
        ("Quelle: keine Marke genannt",
         {"titel": "t", "kern": "k", "offene_fragen": [],
          "aussagen": [{"text": "a", "quellen": []}]},
         "quelle_unbekannt"),
        ("Quelle: Kennung ohne Zeile in der Tabelle",
         {"titel": "t", "kern": "k", "offene_fragen": [],
          "aussagen": [{"text": "a", "quellen": ["Q2"]}]},
         "quelle_existiert_nicht"),
        ("Zahl erfunden (der Erfindungsmelder)",
         {"titel": "t", "kern": "der lauf dauerte 99 sekunden", "offene_fragen": [],
          "aussagen": [{"text": "a", "quellen": ["Q1"]}]},
         "zahl_erfunden"),
        ("deutsche Tausendertrennung darf NICHT als erfunden gelten",
         {"titel": "t", "kern": "es waren 14.268 zeilen", "offene_fragen": [],
          "aussagen": [{"text": "a", "quellen": ["Q1"]}]},
         None),
        ("sauber: muss durchgehen",
         {"titel": "t", "kern": "der lauf dauerte 63 sekunden", "offene_fragen": [],
          "aussagen": [{"text": "11 zeilen gefunden", "quellen": ["Q1"]}]},
         None),
    ]
    fehl = 0
    for name, d, erwartet in faelle:
        gut, grund, detail = pruefe(c, strom, d, marken, quell_text)
        ist = None if gut else grund
        ok = (ist == erwartet)
        fehl += 0 if ok else 1
        print("  %-42s erwartet %-24s ist %-24s %s"
              % (name, str(erwartet), str(ist), "ok" if ok else "FEHLER"))
    print("Selbsttest: %d von %d Faellen richtig." % (len(faelle) - fehl, len(faelle)))
    c.close()
    if fehl:
        raise SystemExit(1)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="b", required=True)
    s.add_parser("raten", help="gemessene Aufnahmerate je Strom")
    q = s.add_parser("init", help="Schwellen aus den gemessenen Raten ableiten")
    q.add_argument("--neu", action="store_true", help="bestehende Schwellen ueberschreiben")
    q = s.add_parser("schwelle", help="eine Schwelle von Hand setzen")
    q.add_argument("--strom", required=True)
    q.add_argument("--wert", required=True, type=int)
    q = s.add_parser("zyklus", help="nachschauen und nur bei Schwelle arbeiten")
    q.add_argument("--rufe", type=int, default=0, help="Rufe je zuendendem Strom")
    q.add_argument("--nur-zaehlen", dest="nur_zaehlen", action="store_true")
    s.add_parser("stand", help="Aufnahme, Schwellen, Zyklen, Verwerfungen, Token")
    s.add_parser("selbsttest", help="Beweis, dass die Pruefung ablehnen kann")
    q = s.add_parser("zeigen", help="die letzten Kondensate im Klartext")
    q.add_argument("--anzahl", type=int, default=3)
    a = p.parse_args()
    {"raten": cmd_raten, "init": cmd_init, "schwelle": cmd_schwelle,
     "zyklus": cmd_zyklus, "stand": cmd_stand, "zeigen": cmd_zeigen,
     "selbsttest": cmd_selbsttest}[a.b](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
