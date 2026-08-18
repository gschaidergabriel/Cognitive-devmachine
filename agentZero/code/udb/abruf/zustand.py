#!/usr/bin/env python3
"""zustand.py — EIN Aufruf, der ganze Lebendzustand des Systems.

Die Umkehrung: die vereinigte Datenbank IST das System, ClayVerse ist ein Modul
darauf. Damit das stimmt, muss es genau EINEN Aufruf geben, der die Frage
"was tut dieses System gerade" beantwortet -- ohne dass der Fragende wissen
muss, welches Werkzeug welche Tabelle fuehrt.

    from udb import zustand
    z = zustand()          # dict
    zustand_text()         # eine Zeile je Teilsystem, noch knapper

ZUSICHERUNGEN (strukturell, nicht als Absicht):
  * KEIN MODELLAUFRUF, auf keinem Pfad. Dieses Modul importiert nur die
    Standardbibliothek (os, json, sqlite3, time, datetime, statistics).
    Es gibt keine Netz-, Prozess- oder Subprozess-Verwendung. `modellaufrufe: 0`
    ist hier eine Eigenschaft des Codes, keine Zusage.
  * NUR LESEND. Die Verbindung wird mit mode=ro geoeffnet und zusaetzlich
    mit PRAGMA query_only=ON abgesichert. Es existiert kein INSERT/UPDATE/
    DELETE/CREATE in dieser Datei. wm_* und vd_* werden ausschliesslich
    gelesen -- daran bauen gerade andere.
  * SPARSAM. Es wird aggregiert, nie werden Zeilen ausgeschuettet. Ziel und
    gemessene Groesse: siehe zustand_mess.py.
    ⚠️ ZEICHEN SIND NICHT TOKEN. An genau diesen Daten gemessen:
    2,46 Zeichen je Token (1800 Zeichen = 730 Token, tiktoken cl100k_base).
    Die verbreitete Faustregel "Zeichen/4" haette 450 Token behauptet und
    damit um 38 % zu niedrig gelegen -- das Budget waere gerissen worden,
    ohne dass es jemand gemerkt haette. Wer diese Struktur erweitert, misst
    mit zustand_mess.py nach, nicht mit len().
    EINSCHRAENKUNG: tiktoken ist NICHT Claudes Tokenizer. Die Zahl ist eine
    belastbare Groessenordnung, kein Abrechnungswert.
  * LEERLAUF IST NICHT TOD. Jedes Teilsystem bekommt `lage` UND `alt_s`
    (Alter des juengsten Herzschlags) UND `takt_s` (aus den Daten GEMESSENER
    Median-Abstand, nicht geraten). "wach" heisst: der Herzschlag ist juenger
    als das Dreifache des eigenen Taktes -- unabhaengig davon, ob das
    Teilsystem etwas gefunden hat. Wo ein Teilsystem gar keinen Taktgeber
    hat, steht das ausdruecklich als lage="kein_taktgeber" da und wird NICHT
    als "aus" ausgegeben.

lage-Werte:
    wach            juengster Herzschlag <= 3x eigener GEMESSENER Takt
    still           <= 20x eigener Takt  (laeuft vermutlich, aber lange nichts)
    aus?            aelter als 20x eigener Takt -- Verdacht, keine Tatsache
    nie             ueberhaupt keine Zeile -- noch nie gelaufen
    unbekannt       zu wenige Runden, um einen Takt zu MESSEN. Dann wird NIE
                    "aus?" behauptet -- nur alt_s ausgewiesen. Lieber
                    unbekannt als ein erfundener Schwellwert.
    kein_taktgeber  das Teilsystem schreibt nur bei Arbeit; Leerlauf und
                    Stillstand sind aus der Datenbank NICHT unterscheidbar
"""
from __future__ import annotations

import json
import os
import sqlite3
import statistics
import time
from datetime import datetime, timedelta, timezone

DB_PATH = os.environ.get("UDB_DB_PATH", "/var/lib/clay/wiki.db")

# Wie oft ein Teilsystem laut eigener Vergangenheit schlaegt, wird gemessen.
# Nur wo weniger als GRUND_N Herzschlaege vorliegen, greift der Rueckfall.
GRUND_N = 8
RUECKFALL_TAKT_S = 60.0
WACH_FAKTOR = 3.0
STILL_FAKTOR = 20.0

# Wiederholung: wiki.db ist 3,5 GB, WAL, mit mehreren aktiven Schreibern.
BUSY_MS = 30000
VERSUCHE = 4
BACKOFF_S = 0.15


# ── Verbindung ────────────────────────────────────────────────────────────
def _verbinden(pfad: str = DB_PATH) -> sqlite3.Connection:
    """Nur-lesende Verbindung mit busy_timeout und Wiederholung."""
    letzte = None
    for versuch in range(VERSUCHE):
        try:
            c = sqlite3.connect(
                "file:%s?mode=ro" % pfad, uri=True, timeout=BUSY_MS / 1000.0
            )
            c.execute("PRAGMA busy_timeout=%d" % BUSY_MS)
            c.execute("PRAGMA query_only=ON")
            return c
        except sqlite3.Error as e:      # pragma: no cover -- nur unter Last
            letzte = e
            time.sleep(BACKOFF_S * (2 ** versuch))
    raise letzte  # type: ignore[misc]


def verbindung(pfad: str = DB_PATH) -> sqlite3.Connection:
    """Die nur-lesende Standardverbindung des Hauses.

    Genau EINE Stelle setzt busy_timeout, query_only und die Wiederholung --
    statt in jedem Werkzeug noch einmal. Wer sie benutzt, kann die geteilte
    3,5-GB-WAL-Datei nicht mehr aus Versehen sperren.
    """
    return _verbinden(pfad)


def _verbinden_schreibend(pfad: str = DB_PATH) -> sqlite3.Connection:
    """Schreibende Verbindung mit demselben busy_timeout/Wiederholung wie
    _verbinden(), aber ohne query_only=ON. journal_mode wird NICHT gesetzt --
    wiki.db ist bereits WAL mit mehreren aktiven Schreibern (siehe Kopf), ein
    PRAGMA journal_mode hier waere ein zweiter Ort, der das behauptet statt
    es zu lassen."""
    letzte = None
    for versuch in range(VERSUCHE):
        try:
            c = sqlite3.connect(pfad, timeout=BUSY_MS / 1000.0)
            c.execute("PRAGMA busy_timeout=%d" % BUSY_MS)
            return c
        except sqlite3.Error as e:      # pragma: no cover -- nur unter Last
            letzte = e
            time.sleep(BACKOFF_S * (2 ** versuch))
    raise letzte  # type: ignore[misc]


def schreib_verbindung(pfad: str = DB_PATH) -> sqlite3.Connection:
    """Die schreibende Standardverbindung des Hauses (Gegenstueck zu
    verbindung()). Wer hierueber schreibt, teilt sich busy_timeout und
    Wiederholung mit den vier Dauerlaeufern statt sofort auf 'database is
    locked' zu laufen. Nur fuer NEUE Tabellen/Zeilen gedacht -- keine
    bestehende Tabelle dieses Hauses wird ueber diesen Weg veraendert.
    """
    return _verbinden_schreibend(pfad)


def _eine(c: sqlite3.Connection, sql: str, args: tuple = ()):
    """Eine Zeile, mit Ruecklauf. Fehlt die Tabelle, kommt None."""
    for versuch in range(VERSUCHE):
        try:
            return c.execute(sql, args).fetchone()
        except sqlite3.OperationalError as e:
            if "locked" in str(e) or "busy" in str(e):
                time.sleep(BACKOFF_S * (2 ** versuch))
                continue
            return None
    return None


def _alle(c: sqlite3.Connection, sql: str, args: tuple = ()) -> list:
    for versuch in range(VERSUCHE):
        try:
            return c.execute(sql, args).fetchall()
        except sqlite3.OperationalError as e:
            if "locked" in str(e) or "busy" in str(e):
                time.sleep(BACKOFF_S * (2 ** versuch))
                continue
            return []
    return []


# ── Zeit ──────────────────────────────────────────────────────────────────
def _jetzt() -> datetime:
    return datetime.now(timezone.utc)


def _parse(s) -> "datetime | None":
    """ISO-Zeitstempel dieses Hauses: mit +00:00, mit Z, oder ohne Zone."""
    if not s:
        return None
    t = str(s).strip().replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(t)
    except ValueError:
        try:
            d = datetime.fromisoformat(t[:19])
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def _alter_s(s, jetzt: datetime):
    d = _parse(s)
    if d is None:
        return None
    return round((jetzt - d).total_seconds(), 1)


def _takt_aus_folge(zeiten: list) -> "float | None":
    """Median-Abstand aus einer absteigend sortierten Zeitliste. GEMESSEN."""
    ds = [_parse(z) for z in zeiten]
    ds = [d for d in ds if d is not None]
    if len(ds) < 3:
        return None
    abst = [
        abs((ds[i] - ds[i + 1]).total_seconds()) for i in range(len(ds) - 1)
    ]
    abst = [a for a in abst if a > 0]
    if not abst:
        return None
    return round(statistics.median(abst), 1)


def _takt_je_entitaet(zeilen: list) -> "float | None":
    """Takt einer RUNDE, nicht der Abstand innerhalb einer Runde.

    Wachten pruefen pro Runde alle Faecher dicht hintereinander; der Abstand
    zwischen zwei Zeilen waere dann der Abstand ZWEIER FAECHER, nicht der
    Rundentakt. Deshalb: nach Entitaet gruppieren, die Entitaet mit den
    meisten Zeilen nehmen, deren Abstaende messen.
    zeilen = [(entitaet, zeit), ...]
    """
    nach = {}
    for e, z in zeilen:
        nach.setdefault(e, []).append(z)
    if not nach:
        return None
    beste = max(nach.values(), key=len)
    return _takt_aus_folge(sorted(beste, reverse=True))


def _lage(alt_s, takt_s, hat_zeilen: bool) -> str:
    """Nie "aus?" ohne gemessenen Takt. Lieber "unbekannt" als geraten."""
    if not hat_zeilen or alt_s is None:
        return "nie"
    if takt_s is None:
        # Zu wenige Runden, um einen Takt zu messen. Ein Schwellwert waere
        # hier erfunden -- also wird keiner behauptet.
        return "unbekannt"
    if alt_s <= WACH_FAKTOR * takt_s:
        return "wach"
    if alt_s <= STILL_FAKTOR * takt_s:
        return "still"
    return "aus?"


# ── Teilsysteme ───────────────────────────────────────────────────────────
def _puls(c, jetzt) -> dict:
    lage = {k: v for k, v in _alle(c, "SELECT schluessel, wert FROM pu_lage")}
    # Der Puls schreibt pu_lage.letzter_takt bei JEDEM Takt, auch bei
    # art='leer'. DAS ist der Herzschlag. pu_takt ist nur eine STICHPROBE
    # (157 Zeilen bei Folge 2231 -- gemessen, nicht geschaetzt), deshalb waere
    # der blosse Zeitabstand zweier pu_takt-Zeilen der Stichprobenabstand,
    # NICHT der Takt. Der echte Takt = Zeitdifferenz je Folgenschritt.
    zeilen = _alle(
        c, "SELECT folge, zeit FROM pu_takt ORDER BY folge DESC LIMIT ?", (24,))
    takte = []
    for i in range(len(zeilen) - 1):
        f1, z1 = zeilen[i]
        f2, z2 = zeilen[i + 1]
        d1, d2 = _parse(z1), _parse(z2)
        if d1 and d2 and f1 > f2:
            takte.append((d1 - d2).total_seconds() / (f1 - f2))
    takt = round(statistics.median(takte), 2) if len(takte) >= 3 else None
    alt = _alter_s(lage.get("letzter_takt"), jetzt)
    arten = {a: n for a, n in _alle(
        c, "SELECT art, COUNT(*) FROM pu_takt GROUP BY art")}
    wach_seit = _parse(lage.get("wach_seit"))
    schlaf_seit = _parse(lage.get("schlaf_seit"))
    wacht = bool(wach_seit and (not schlaf_seit or wach_seit > schlaf_seit))
    d = {
        "lage": _lage(alt, takt, bool(lage)),
        "alt_s": alt,
        "takt_s": takt,
        "wacht": wacht,
        "folge": int(lage.get("letzte_folge") or 0),
        "neustarts": int(lage.get("neustarts") or 0),
        "uebersprungen": int(lage.get("uebersprungen") or 0),
        "stichprobe": arten,          # leer/arbeit/fehler in pu_takt
    }
    if wach_seit and wacht:
        d["wach_s"] = round((jetzt - wach_seit).total_seconds())
    d["arbeit_alt_s"] = _alter_s(lage.get("letzte_arbeit"), jetzt)
    return d


def _bahnen(c, jetzt, heute: str) -> dict:
    zeiten = [r[0] for r in _alle(
        c, "SELECT zeit FROM bahn_lauf ORDER BY id DESC LIMIT ?", (24,))]
    alt = _alter_s(zeiten[0] if zeiten else None, jetzt)
    takt = _takt_aus_folge(zeiten)
    je = {}
    for bahn, erg, n in _alle(
        c,
        "SELECT bahn, ergebnis, COUNT(*) FROM bahn_lauf "
        "WHERE zeit >= ? GROUP BY bahn, ergebnis",
        (heute,),
    ):
        e = je.setdefault(bahn or "?", {"an": 0, "ver": 0, "feh": 0})
        e["an" if erg == "angenommen" else
          ("ver" if erg == "verworfen" else "feh")] += n
    gesund = sorted(k for k, v in je.items() if v["feh"] == 0 and
                    (v["an"] + v["ver"]) > 0)
    krank = sorted(k for k, v in je.items() if v["feh"] > 0)
    del gesund   # ergibt sich aus heute minus krank -- nicht doppelt senden
    # bahn_lage ist der vorgesehene Taktgeber (Lebenszeichen auch im
    # Leerlauf). Solange dort nichts steht, laesst sich Leerlauf nicht von
    # Stillstand unterscheiden -- dann wird das GESAGT statt geraten.
    # Sobald jemand bahn_lage befuellt, wird von hier an daraus gelesen:
    # der Herzschlag schlaegt Vorrang vor dem Arbeitslog.
    herz = _eine(c, "SELECT MAX(zeit) FROM bahn_lage")
    if herz and herz[0]:
        alt = _alter_s(herz[0], jetzt)
        lage = _lage(alt, takt, True)
    else:
        lage = "kein_taktgeber"
    return {
        "lage": lage,
        "alt_s": alt,
        # je Bahn heute: [angenommen, verworfen, fehler]
        "heute": {k: [v["an"], v["ver"], v["feh"]] for k, v in
                  sorted(je.items())},
        "krank": krank,
    }


ENG_ANTEIL = 0.2   # ab hier gilt ein Zugang als eng: Rest < 20 % des Limits


def _kontingent(c, jetzt, heute: str, voll: bool = False) -> dict:
    """Kontingente. Sparsam: es werden nur die Zugaenge einzeln genannt, die
    HEUTE benutzt wurden oder eng werden. Die uebrigen sind nur eine Zahl --
    eine Liste von 33 unbenutzten Zugaengen ist keine Lage, sondern ein
    Katalog (den liefert voll=True)."""
    zugaenge = _alle(
        c,
        "SELECT zugang, einheit, fenster_limit, tag_limit, woche_limit "
        "FROM kb_zugang",
    )
    verbraucht_tag = {z: m for z, m in _alle(
        c,
        "SELECT zugang, SUM(menge) FROM kb_buchung WHERE zeit >= ? "
        "GROUP BY zugang",
        (heute,),
    )}
    je = {}
    eng = []
    n_limit = 0
    for (zg, einh, fl, tl, wl) in zugaenge:
        genutzt = round(verbraucht_tag.get(zg, 0.0), 2)
        limit = tl if tl is not None else (wl if wl is not None else fl)
        fenster = "tag" if tl is not None else (
            "woche" if wl is not None else ("fenster" if fl is not None
                                            else None))
        if limit is not None:
            n_limit += 1
        # Ein Limit wird NIE erfunden. Wo der Anbieter keins veroeffentlicht,
        # steht rest=null -- nicht "unbegrenzt".
        rest = round(limit - genutzt, 2) if (limit is not None and
                                             fenster == "tag") else None
        if rest is not None and limit and rest < ENG_ANTEIL * limit:
            eng.append(zg)
        if voll or genutzt or (rest is not None and
                               rest < ENG_ANTEIL * (limit or 1)):
            # Ohne belegtes Limit nur die Zahl -- vier Nullwerte je Zugang
            # sind reine Tokenkosten ohne Aussage.
            je[zg] = (genutzt if limit is None
                      else [genutzt, rest, limit, fenster, einh])
    warn = (_eine(c, "SELECT COUNT(*) FROM kb_warnung WHERE zeit >= ?",
                  (heute,)) or (0,))[0]
    letzte = (_eine(c, "SELECT MAX(zeit) FROM kb_buchung") or (None,))[0]
    return {
        "konten": (_eine(c, "SELECT COUNT(*) FROM kb_konto") or (0,))[0],
        "zugaenge": len(zugaenge),
        "mit_limit": n_limit,
        # zugang -> [heute_genutzt, rest, limit, fenster, einheit]
        "heute": je,
        "eng": eng,
        "tag_reset": (jetzt + timedelta(days=1)).strftime("%Y-%m-%dT00:00Z"),
        "warnungen_heute": warn,
        "letzte_buchung_alt_s": _alter_s(letzte, jetzt),
    }


def _schluessel(c, jetzt) -> dict:
    zeilen = _alle(
        c,
        "SELECT schluessel, einordnung, seit, zuletzt_geprueft, "
        "geprueft_gesamt, gesund_gesamt FROM schluessel_lage",
    )
    # Rundentakt: Abstaende EINES Schluesselfachs, nicht Abstaende zwischen
    # zwei Faechern derselben Runde (das waeren Millisekunden).
    takt = _takt_je_entitaet(_alle(
        c, "SELECT schluessel, zeit FROM schluessel_lauf "
           "ORDER BY id DESC LIMIT ?", (60,)))
    juengste = max((r[3] for r in zeilen if r[3]), default=None)
    alt = _alter_s(juengste, jetzt)
    nicht_gesund = {}
    for (s, einordnung, seit, _zp, _g, _gg) in zeilen:
        if einordnung != "GESUND":
            # NIE einen Schluesselwert ausgeben -- nur den Namen des Faches.
            nicht_gesund[s] = [einordnung, _alter_s(seit, jetzt)]
    return {
        "lage": _lage(alt, takt, bool(zeilen)),
        "alt_s": alt,
        "takt_s": takt,
        "n": len(zeilen),
        "gesund": sum(1 for r in zeilen if r[1] == "GESUND"),
        "nicht_gesund": nicht_gesund,      # name -> [einordnung, seit_s]
    }


def _verdichtung(c, jetzt) -> dict:
    stroeme = _alle(
        c,
        "SELECT strom, schwelle, aktiv, letzte_pruefung, letzter_lauf "
        "FROM vd_strom",
    )
    juengste = max((r[3] for r in stroeme if r[3]), default=None)
    alt = _alter_s(juengste, jetzt)
    # Takt je Strom, nicht Abstand zwischen zwei Stroemen derselben Runde.
    takt = _takt_je_entitaet(_alle(
        c, "SELECT strom, zeit FROM vd_aufnahme ORDER BY id DESC LIMIT ?",
        (60,)))
    erg = {e: n for e, n in _alle(
        c, "SELECT ergebnis, COUNT(*) FROM vd_lauf GROUP BY ergebnis")}
    offen = (_eine(
        c, "SELECT SUM(offen_gesamt) FROM vd_aufnahme WHERE id IN "
           "(SELECT MAX(id) FROM vd_aufnahme GROUP BY strom)") or (0,))[0]
    grenzen = {z: [n429, ohne] for z, n429, ohne in _alle(
        c, "SELECT zugang, anzahl_429, rufe_ohne_429 FROM vd_grenze")}
    return {
        "lage": _lage(alt, takt, bool(stroeme)),
        "alt_s": alt,
        "takt_s": takt,
        "stroeme": len(stroeme),
        "aktiv": sum(1 for r in stroeme if r[2]),
        # noch nie gelaufen != untaetig: beides steht hier getrennt.
        "nie_gelaufen": sorted(r[0] for r in stroeme if not r[4]),
        "offen_gesamt": int(offen or 0),
        "laeufe": erg,
        "grenze_429": grenzen,
    }


def _wache(c, jetzt) -> dict:
    zeilen = _alle(
        c, "SELECT ziel, zeit, active_state FROM wa_snapshot")
    juengste = max((r[1] for r in zeilen if r[1]), default=None)
    alt = _alter_s(juengste, jetzt)
    # wa_snapshot hat den Primaerschluessel auf ziel und wird UEBERSCHRIEBEN --
    # es gibt keine Historie, aus der sich ein Takt messen liesse. Also wird
    # keiner behauptet: takt_s=None -> lage="unbekannt", plus alt_s als Fakt.
    takt = None
    n_ereignis = (_eine(c, "SELECT COUNT(*) FROM wa_ereignis") or (0,))[0]
    letztes = _eine(
        c, "SELECT zeit, art, ziel FROM wa_ereignis ORDER BY id DESC LIMIT 1")
    nicht_aktiv = sorted(r[0] for r in zeilen if r[2] != "active")
    return {
        # wa_snapshot wird bei JEDEM Lauf neu geschrieben, auch wenn nichts
        # gefunden wurde. Deshalb heisst 0 Ereignisse hier "ruhig", nicht "tot".
        "lage": _lage(alt, takt, bool(zeilen)),
        "alt_s": alt,
        "takt_s": takt,
        "ziele": len(zeilen),
        "nicht_aktiv": nicht_aktiv,
        "ereignisse": n_ereignis,
        "letztes": (list(letztes) if letztes else None),
        "befund": "ruhig" if not n_ereignis else "auffaellig",
    }


def _arbeit(c, jetzt, stunde_her: str) -> dict:
    kur = {s: n for s, n in _alle(
        c, "SELECT status, COUNT(*) FROM kuration GROUP BY status")}
    kur_art = {s: n for s, n in _alle(
        c, "SELECT noetig, COUNT(*) FROM kuration WHERE status='offen' "
           "GROUP BY noetig")}
    prob = {s: n for s, n in _alle(
        c, "SELECT status, COUNT(*) FROM problem GROUP BY status")}
    folg = {s: n for s, n in _alle(
        c, "SELECT status, COUNT(*) FROM folgerung GROUP BY status")}
    durchsatz = {}
    for name, tab, spalte in (
        ("bahn", "bahn_lauf", "zeit"),
        ("verdichtung", "vd_lauf", "zeit"),
        ("buchung", "kb_buchung", "zeit"),
        ("anreicherung", "anreicherung", "geholt_am"),
        ("taetigkeit", "taetigkeit", "zeit"),
    ):
        r = _eine(c, "SELECT COUNT(*) FROM %s WHERE %s >= ?" % (tab, spalte),
                  (stunde_her,))
        if r:
            durchsatz[name] = r[0]
    return {
        "kuration": {"offen": kur.get("offen", 0),
                     "erledigt": kur.get("erledigt", 0),
                     "offen_art": kur_art},
        "problem": prob,
        "folgerung": folg,
        "durchsatz_1h": durchsatz,
    }


def _weltmodell(c, jetzt) -> dict:
    """wm_* wird hier AUSSCHLIESSLICH gelesen -- daran bauen gerade andere.

    Beide Aggregate ueber wm_lesart laufen in EINEM Tabellendurchlauf; das
    war vorher zweimal derselbe Scan ueber 28k Zeilen. Der Griff nach
    (artikel_id, gueltig_bis) laeuft ueber wm_lesart_ix1 und beruehrt die
    Tabelle nicht.
    """
    # Ein Durchlauf: Kandidatenstand + juengste Lesart.
    r1 = _eine(
        c,
        "SELECT SUM(CASE WHEN offen=1 THEN 1 ELSE 0 END), "
        "       SUM(CASE WHEN offen=0 THEN 1 ELSE 0 END), "
        "       COUNT(*), MAX(erzeugt_am) FROM wm_lesart",
    ) or (0, 0, 0, None)
    # Lesarten je Artikel: 1 = unwidersprochen, 2+ = mehrere Lesarten.
    r2 = _eine(
        c,
        "SELECT SUM(CASE WHEN n=1 THEN 1 ELSE 0 END), "
        "       SUM(CASE WHEN n>1 THEN 1 ELSE 0 END), COUNT(*) FROM "
        "(SELECT artikel_id, COUNT(*) AS n FROM wm_lesart "
        " WHERE gueltig_bis IS NULL GROUP BY artikel_id)",
    ) or (0, 0, 0)
    topo = _eine(
        c, "SELECT COUNT(*), SUM(offen) FROM wm_topologie") or (0, 0)
    guss = {e: n for e, n in _alle(
        c, "SELECT ergebnis, COUNT(*) FROM wm_guss_log GROUP BY ergebnis")}
    return {
        "artikel_1_lesart": r2[0] or 0,
        "artikel_2plus": r2[1] or 0,
        # offen=1 heisst KANDIDAT, also unbestimmt -- nicht bestaetigt.
        "unbestimmt": r1[0] or 0,
        "bestimmt": r1[1] or 0,
        "topologie": topo[0] or 0,
        "topologie_unbestimmt": topo[1] or 0,
        "guss": guss,
        "juengste_lesart_alt_s": _alter_s(r1[3], jetzt),
    }


# Dateien, die Zustand tragen, aber KEINE Tabelle sind. Sie stehen hier,
# damit sie ueberhaupt jemand sieht: eine Beweisdatei, die in keiner Lage
# vorkommt, wird beim naechsten Aufraeumen geloescht, weil niemand weiss,
# wozu sie da ist. Grund und Ort gehoeren zusammen an EINE Stelle.
BEWEISDATEIEN = (
    # register.db: Abstammung der gepraegten Entitaeten (ORIGIN/COPY,
    # Eltern, Linienwurzel, Koerper-Hash). Steht NIRGENDS sonst -- wiki.db
    # kennt nur die eine aktive clay_id als nackte Zeichenkette.
    ("/var/lib/microclay/register.db", "Abstammung, einzige Kopie"),
    # puls.jsonl: das luekenlose Journal. pu_takt ist nur die Stichprobe
    # (157 Zeilen bei Folge 2231 -- gemessen).
    ("/var/lib/clay/puls.jsonl", "Puls-Journal, luekenlos"),
)


def _platte(pfad: str = "/var/lib") -> dict:
    """Freier Plattenplatz. Ein System, das nicht weiss, wann ihm der Platz
    ausgeht, merkt es erst, wenn das Schreiben fehlschlaegt.
    os.statvfs, kein Subprozess -- die Zusicherung oben bleibt gueltig."""
    try:
        s = os.statvfs(pfad)
    except OSError:
        return {"pfad": pfad, "lage": "unbekannt"}
    frei = s.f_bavail * s.f_frsize
    gesamt = s.f_blocks * s.f_frsize
    belegt = 1 - (frei / gesamt) if gesamt else 0
    return {
        "pfad": pfad,
        "frei_gb": round(frei / 1024 ** 3, 1),
        "belegt_pct": round(belegt * 100),
        # Schwellen benannt, nicht versteckt: ab 90 % wird es eng, ab 95 %
        # scheitert SQLite beim Wachsen der WAL-Datei.
        "lage": "eng" if belegt >= 0.95 else ("knapp" if belegt >= 0.90
                                              else "gut"),
    }


def _beweise() -> dict:
    """Nennt die Zustandsdateien ausserhalb der Datenbank -- mit Grund."""
    aus = {}
    for pfad, grund in BEWEISDATEIEN:
        try:
            st = os.stat(pfad)
        except OSError:
            aus[pfad] = {"da": False, "grund": grund}
            continue
        aus[pfad] = {
            "da": True,
            "kb": round(st.st_size / 1024, 1),
            "alt_s": round(time.time() - st.st_mtime),
            "grund": grund,
        }
    return aus


# ── Der eine Aufruf ───────────────────────────────────────────────────────
def zustand(pfad: str = DB_PATH, c: "sqlite3.Connection | None" = None,
            voll: bool = False) -> dict:
    """Der ganze Lebendzustand in einer Struktur. KEIN MODELLAUFRUF.

    Nur Standardbibliothek, nur lesend, nur Aggregate. Wer eine eigene
    Verbindung mitgibt, ist selbst fuer mode=ro verantwortlich.
    voll=True haengt den ganzen Zugangskatalog an -- das ist eine Vertiefung,
    keine Lage, und kostet Tokens.
    """
    eigen = c is None
    if eigen:
        c = _verbinden(pfad)
    try:
        jetzt = _jetzt()
        heute = jetzt.strftime("%Y-%m-%d")
        stunde_her = (jetzt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        return {
            "zeit": jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "modellaufrufe": 0,
            "puls": _puls(c, jetzt),
            "bahnen": _bahnen(c, jetzt, heute),
            "kontingent": _kontingent(c, jetzt, heute, voll),
            "schluessel": _schluessel(c, jetzt),
            "verdichtung": _verdichtung(c, jetzt),
            "wache": _wache(c, jetzt),
            "arbeit": _arbeit(c, jetzt, stunde_her),
            "weltmodell": _weltmodell(c, jetzt),
            "platte": _platte(),
            "beweise": _beweise(),
        }
    finally:
        if eigen:
            c.close()


def zustand_json(pfad: str = DB_PATH) -> str:
    """Dieselbe Struktur als sparsamstes JSON (keine Leerzeichen)."""
    return json.dumps(zustand(pfad), ensure_ascii=False,
                      separators=(",", ":"), sort_keys=False)


def zustand_text(pfad: str = DB_PATH) -> str:
    """Eine Zeile je Teilsystem -- die knappste Form, fuer Menschen."""
    z = zustand(pfad)
    p, b, k = z["puls"], z["bahnen"], z["kontingent"]
    s, v, w, a, m = (z["schluessel"], z["verdichtung"], z["wache"],
                     z["arbeit"], z["weltmodell"])
    zeilen = [
        "zeit %s  modellaufrufe 0" % z["zeit"],
        "puls %s alt=%ss takt=%ss folge=%s neustarts=%s" % (
            p["lage"], p["alt_s"], p["takt_s"], p["folge"], p["neustarts"]),
        "bahnen %s heute=%s krank=%s" % (
            b["lage"], b["heute"], ",".join(b["krank"]) or "-"),
        "kontingent zugaenge=%s mit_limit=%s heute=%s eng=%s warn=%s" % (
            k["zugaenge"], k["mit_limit"], k["heute"],
            ",".join(k["eng"]) or "-", k["warnungen_heute"]),
        "schluessel %s %s/%s gesund nicht_gesund=%s" % (
            s["lage"], s["gesund"], s["n"], s["nicht_gesund"] or "-"),
        "verdichtung %s stroeme=%s/%s offen=%s laeufe=%s nie=%s" % (
            v["lage"], v["aktiv"], v["stroeme"], v["offen_gesamt"],
            v["laeufe"], ",".join(v["nie_gelaufen"]) or "-"),
        "wache %s ziele=%s ereignisse=%s befund=%s" % (
            w["lage"], w["ziele"], w["ereignisse"], w["befund"]),
        "arbeit kuration_offen=%s problem=%s durchsatz_1h=%s" % (
            a["kuration"]["offen"], a["problem"], a["durchsatz_1h"]),
        "weltmodell 1lesart=%s 2plus=%s unbestimmt=%s topo=%s" % (
            m["artikel_1_lesart"], m["artikel_2plus"], m["unbestimmt"],
            m["topologie"]),
        "platte %s frei=%sG belegt=%s%%" % (
            z["platte"].get("lage"), z["platte"].get("frei_gb"),
            z["platte"].get("belegt_pct")),
        "beweisdateien (nicht loeschen) %s" % ", ".join(
            "%s%s" % (k, "" if v["da"] else " FEHLT")
            for k, v in z["beweise"].items()),
    ]
    return "\n".join(zeilen)


if __name__ == "__main__":
    import sys
    if "--text" in sys.argv:
        print(zustand_text())
    else:
        print(json.dumps(zustand(), ensure_ascii=False, indent=1))
