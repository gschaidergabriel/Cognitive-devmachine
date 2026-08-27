#!/usr/bin/env python3
"""ratgeber.py — der Ratgeber, der bei JEDEM Prompt vorrechnet.

Drei Stufen. Die ersten beiden brauchen KEIN Modell.

  Stufe 1  SAMMELN, mechanisch:
           udb.zustand()      der ganze Lebendzustand in einem Aufruf
           kb_zugang          welche Bahnen es gibt und wie sie stehen
           kb_verdrahtung     welcher Prozess auf welcher Bahn faehrt
           schluessel_lage    welcher Zugang gesund ist (nur Namen, nie Werte)
           werkzeuge.py       welche Werkzeuge es gibt und was sie kosten
           das Wiki selbst    was wir dazu schon WISSEN (FTS zuerst)
           der Sitzungsverlauf  welcher Weg zu dieser Anfrage gefuehrt hat

  Stufe 2  MOEGLICHKEITSRAUM, ebenfalls mechanisch: aus dem Gemessenen wird
           abgeleitet, was JETZT wirklich ginge. Eine Bahn auf 429 ist keine
           Moeglichkeit. Ein Werkzeug mit totem Schluessel ist keine
           Moeglichkeit. Diese Menge wird GERECHNET, nie geraten -- das ist
           der Unterschied zwischen einem Ratgeber und einem Horoskop.

  Stufe 3  MISTRAL macht aus Stufe 1+2 EINEN Vorschlag. Mit
           response_format json_schema strict. Ohne das kam derselbe Prompt
           in einem ```json-Zaun mit erfundenen Feldnamen zurueck.

GRENZEN, die dieser Bau einhaelt:
  * ER BLOCKIERT NIE. Harte Frist auf den Mistral-Aufruf (Vorgabe 2,5 s).
    Bei Frist, 429 oder irgendeinem Fehler kommt der MECHANISCHE Teil allein
    zurueck, und es steht dabei, dass er allein kam.
  * ER IST NIE AUTORITAET. `model_output_is_not_authority` ist vom Eigner
    festgelegt. Alles, was aus dem Modell kommt, traegt ueberall die
    Aufschrift VORSCHLAG. Er raet; er entscheidet nicht und handelt nicht.
  * ER IST EHRLICH, WENN ER NICHTS WEISS. Findet Stufe 1 keinen Bezug und
    Stufe 2 keine passende Moeglichkeit, ist die richtige Antwort ein kurzes
    "kein Vorschlag, hier ist der Zustand" -- kein erzeugter Vorschlag.
    Ein Ratgeber, der immer raet, ist Rauschen.

⚠️ DATENSCHUTZ, ausdruecklich, damit es spaeter niemanden ueberrascht:
   Fuer das Feld `weg` werden die LETZTEN NACHRICHTEN DER SITZUNG gelesen
   (Anfragen des Eigners und kurze Antworten, NIE Werkzeugausgaben) und an
   MISTRAL geschickt -- einen Anbieter ausserhalb dieses Hauses. Der
   Sitzungsverlauf kann alles enthalten, was der Eigner getippt hat.
   Abschaltbar mit  CLAY_RATGEBER_VERLAUF=0  -- der Rest laeuft dann
   unveraendert weiter.

Schalter (alle mit gemessenen Vorgaben):
   CLAY_RATGEBER_VERLAUF=0     Sitzungsverlauf nicht lesen, nicht senden
   CLAY_RATGEBER_FRIST=2.5     harte Frist auf den Mistral-Aufruf, Sekunden
   CLAY_RATGEBER_MODELL=...    Vorgabe mistral-small-latest (GEMESSEN:
                               p50 2332 ms, Ausgabe p50 285 Token; die
                               Alternative ministral-3b-latest ist im Mittel
                               schneller, erzeugt aber MEHR Token)
   CLAY_RATGEBER_AUS=1         Stufe 3 gar nicht erst versuchen
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/unifieddb")

DB_PFAD = os.environ.get("UDB_DB_PATH", "/var/lib/clay/wiki.db")
ENV_PFAD = "/etc/clayverse/freie-zugaenge.env"
KONTINGENT = "/opt/clayverse/werkzeug/kontingent.py"

# Der Schluessel ist entschieden und wird hier nicht neu gewaehlt.
# GEMESSEN 2026-08-15: die drei Mistral-Schluessel sind DREI GETRENNTE TOEPFE
# (Beleg: ein Ruf auf Schluessel 2 kostete 17 Token, Schluessel 3 zeigte
# danach weiter 49983 statt 49966 -- ein geteilter Zaehler waere mitgegangen).
# MISTRAL_API_KEY gehoert verdichtung.py, MISTRAL2 ist dessen Rueckfall.
# MISTRAL3 gehoert allein dem Ratgeber, damit ein voller Verdichtungslauf ihn
# niemals aushungern kann.
SCHLUESSEL_NAME = "MISTRAL3_API_KEY"
URL = "https://api.mistral.ai/v1/chat/completions"
MODELL = os.environ.get("CLAY_RATGEBER_MODELL", "mistral-small-latest")

KONTO = "clayverse"          # steht so im Katalog; clayverse_grundlast gibt es
ZUGANG = "mistral_small"     # NICHT, und kontingent.py bricht dann hart ab.

FRIST_S = float(os.environ.get("CLAY_RATGEBER_FRIST", "2.5"))
# ⚠️ GEMESSEN: bei 900 und 1200 kam die Antwort mitten im JSON abgeschnitten
# zurueck -- das ist die eine Bedingung, unter der die Schemazusage still
# versagt. Deshalb hoch genug, und ein Abschnitt gilt als EIGENER
# Ablehnungsgrund, nicht als Schemabruch.
MAX_TOKEN = 2000

BUSY_MS = 30000
VERSUCHE = 4
BACKOFF_S = 0.15

# Gemessen auf genau diesem Bestand: 2,46 Zeichen je Token. Diese Zahl wird
# NUR benutzt, wenn kein echter Tokenzaehler da ist -- und dann steht
# ausdruecklich "geschaetzt" daran. Zeichen/4 hat hier um 38 % zu wenig
# gezaehlt, das ist der Grund fuer die ganze Vorsicht.
ZEICHEN_JE_TOKEN = 2.46
VERLAUF_TOKEN_DECKEL = 800
VERLAUF_N_ANFRAGEN = 4

# Zustaende aus kb_zugang, die KEINE Moeglichkeit sind -- je mit dem Grund,
# der spaeter im Feld `verworfen` auftauchen darf.
TOT = {
    "sammelzeile": "abgeloeste Sammelzeile, keine eigene Bahn",
    "schluessel_tot": "Schluessel antwortet mit 401",
    "unbrauchbar": "Kontingent zu klein, um eine Bahn zu sein",
    "konto_leer": "Guthaben aufgebraucht, Aufruf gibt 402",
}


# ── Tokenzaehler ──────────────────────────────────────────────────────────
_ENC = None
_ENC_ECHT = None


def _encoder():
    """Echter Tokenzaehler, wenn vorhanden. Sonst None."""
    global _ENC, _ENC_ECHT
    if _ENC_ECHT is not None:
        return _ENC
    try:
        os.environ.setdefault("TIKTOKEN_CACHE_DIR", "/var/lib/clay/tiktoken")
        import tiktoken
        _ENC = tiktoken.get_encoding("cl100k_base")
        _ENC_ECHT = True
    except Exception:
        _ENC = None
        _ENC_ECHT = False
    return _ENC


def token(text: str) -> tuple[int, bool]:
    """(Anzahl, echt_gemessen). Nie Zeichen/4 -- das zaehlt hier 38 % zu wenig."""
    e = _encoder()
    if e is not None:
        try:
            return len(e.encode(text or "")), True
        except Exception:
            pass
    return int(round(len(text or "") / ZEICHEN_JE_TOKEN)), False


# ── Schluessel ────────────────────────────────────────────────────────────
def schluessel(name: str = SCHLUESSEL_NAME) -> str:
    """Liest EINEN Wert aus der Tresordatei. Gibt ihn zurueck, gibt ihn nie
    aus -- kein print, kein log, keine Fehlermeldung mit dem Wert darin."""
    if not os.path.exists(ENV_PFAD):
        raise RuntimeError("Tresordatei fehlt: %s" % ENV_PFAD)
    for zeile in open(ENV_PFAD, encoding="utf-8"):
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        k, v = zeile.split("=", 1)
        if k.strip() == name:
            v = v.strip().strip('"').strip("'")
            if not v:
                raise RuntimeError("%s steht in der Tresordatei, ist leer." % name)
            return v
    raise RuntimeError("%s steht nicht in der Tresordatei." % name)


# ── Datenbank ─────────────────────────────────────────────────────────────
def verbindung(pfad: str = DB_PFAD) -> sqlite3.Connection:
    """Nur lesend, mit busy_timeout UND Wiederholung -- wiki.db ist 3,5 GB,
    WAL, und es schreiben mehrere Dauerlaeufer gleichzeitig darauf."""
    letzte = None
    for versuch in range(VERSUCHE):
        try:
            c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True,
                                timeout=BUSY_MS / 1000.0)
            c.execute("PRAGMA busy_timeout=%d" % BUSY_MS)
            c.execute("PRAGMA query_only=ON")
            c.row_factory = sqlite3.Row
            return c
        except sqlite3.Error as e:
            letzte = e
            time.sleep(BACKOFF_S * (2 ** versuch))
    raise letzte


def _alle(c, sql, args=()):
    for versuch in range(VERSUCHE):
        try:
            return c.execute(sql, args).fetchall()
        except sqlite3.OperationalError as e:
            if "locked" in str(e) or "busy" in str(e):
                time.sleep(BACKOFF_S * (2 ** versuch))
                continue
            return []
    return []


# ── Stufe 1a: Zustand ─────────────────────────────────────────────────────
def _zustand(c) -> dict:
    """udb.zustand() -- der ganze Lebendzustand, 0 Modellaufrufe, p95 33 ms.
    Die eigene Verbindung wird mitgegeben, damit nicht zweimal geoeffnet wird."""
    try:
        from udb.abruf import zustand as z
        return z.zustand(c=c)
    except Exception as e:
        return {"fehler": "udb.zustand nicht erreichbar: %s" % e}


# ── Stufe 1b: Bahnen, Verdrahtung, Schluessel ─────────────────────────────
def _bahnen(c) -> list:
    return [dict(r) for r in _alle(
        c,
        "SELECT zugang, anzeige, modell, zustand, zustand_grund, kann_schema, "
        "       kann_embedding, tag_limit, minute_limit, token_tag_limit, "
        "       ausgereizt, schluessel_namen, einheit "
        "FROM kb_zugang")]


def _verdrahtung(c) -> list:
    return [dict(r) for r in _alle(
        c,
        "SELECT prozess, bahn_erst, bahn_zweit, bahn_dritt, max_je_lauf, "
        "       schema_pflicht FROM kb_verdrahtung")]


def _schluessel_lage(c) -> dict:
    """Nur Fachname -> Einordnung. NIE ein Wert."""
    return {r["schluessel"]: r["einordnung"] for r in _alle(
        c, "SELECT schluessel, einordnung FROM schluessel_lage")}


# ── Stufe 1c: Werkzeuge ───────────────────────────────────────────────────
# Was werkzeuge.py wirklich kann, mit dem Zugang, an dem es haengt. Der
# ZUSTAND wird nicht hier hineingeschrieben, sondern in Stufe 2 aus
# kb_zugang und schluessel_lage GEMESSEN dazugerechnet.
WERKZEUGE = [
    {"name": "suche (Tavily)", "aufruf": "werkzeuge.py suche",
     "zugang": "tavily", "schluessel": "TAVILY",
     "kosten": "1 Tavily-Credit je Suche"},
    {"name": "suche (Exa)", "aufruf": "werkzeuge.py suche --dienst exa",
     "zugang": "exa", "schluessel": "EXA",
     "kosten": "1 Exa-Anfrage je Suche"},
    {"name": "literatur (OpenAlex)", "aufruf": "werkzeuge.py literatur",
     "zugang": "openalex", "schluessel": "OPENALEX",
     "kosten": "frei, hoefliche Kennung noetig"},
    {"name": "sandkasten (E2B)", "aufruf": "werkzeuge.py sandkasten",
     "zugang": "e2b", "schluessel": "E2B",
     "kosten": "E2B-Laufzeit je Sekunde"},
    {"name": "eigener Bestand (FTS)", "aufruf": "werkzeuge.py suche (Stufe 1)",
     "zugang": None, "schluessel": None,
     "kosten": "0 -- nur die eigene Datenbank"},
]


# ── Stufe 1d: das Wiki selbst ─────────────────────────────────────────────
def _fts_ausdruck(frage: str, verbinder: str):
    """Jedes Wort einzeln gequotet. Sonst wirft FTS5 bei Bindestrich,
    Doppelpunkt oder einem 'AND' im Fragetext einen Syntaxfehler."""
    woerter = [w for w in re.findall(r"[\wÀ-ɏ]+", frage, re.UNICODE)
               if len(w) > 3]
    if not woerter:
        return None
    return (" %s " % verbinder).join(
        '"' + w.replace('"', '') + '"' for w in woerter[:10])


def _eigener_bestand(c, frage: str, limit: int = 3) -> tuple:
    """Was wissen WIR schon dazu? Erst streng (alle Woerter), sonst weit."""
    for verbinder, streng in (("AND", True), ("OR", False)):
        m = _fts_ausdruck(frage, verbinder)
        if not m:
            return [], False
        zeilen = _alle(
            c,
            "SELECT s.artikel_id AS aid, s.titel AS titel, "
            "       snippet(fts_index_artikel, 1, '', '', ' … ', 14) AS auszug "
            "FROM fts_index_artikel "
            "JOIN artikel_suchtext s ON s.id = fts_index_artikel.rowid "
            "LEFT JOIN artikel a ON a.id = s.artikel_id "
            "WHERE fts_index_artikel MATCH ? "
            "  AND COALESCE(a.verfallen, 0) = 0 "
            "ORDER BY bm25(fts_index_artikel) LIMIT ?", (m, limit))
        if zeilen:
            return ([{"titel": (z["titel"] or z["aid"])[:90],
                      "auszug": " ".join((z["auszug"] or "").split())[:180]}
                     for z in zeilen], streng)
    return [], False


# ── Stufe 1e: der Weg -- die letzten Nachrichten ──────────────────────────
# ⚠️ Diese Daten gehen an MISTRAL. Siehe Kopf der Datei.
TRANS_MAX_ZEILE = 40000     # laengere Zeilen sind Werkzeugausgaben, nie Prompts
TRANS_ERST_BYTES = 256 * 1024
TRANS_MAX_BYTES = 4 * 1024 * 1024
RAUSCH = ("<task-notification", "<system-reminder", "<local-command",
          "<command-name", "<bash-input", "Caveat:")


def _transkript_finden(pfad_aus_haken=None):
    """Der Haken bekommt transcript_path mitgeliefert -- das ist die
    verlaessliche Quelle. Der Rueckfall (juengste mtime) gilt nur, wenn er
    fehlt."""
    if pfad_aus_haken and os.path.exists(pfad_aus_haken):
        return pfad_aus_haken
    wurzel = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    if not os.path.isdir(wurzel):
        return None
    bestes, best_t = None, -1.0
    try:
        for verz in os.scandir(wurzel):
            if not verz.is_dir():
                continue
            for f in os.scandir(verz.path):
                if not f.name.endswith(".jsonl"):
                    continue
                t = f.stat().st_mtime
                if t > best_t:
                    bestes, best_t = f.path, t
    except OSError:
        return None
    return bestes


def _schwanz_zeilen(pfad: str, bytes_n: int) -> list:
    """Die letzten bytes_n Bytes als Zeilen. Von HINTEN gelesen -- eine
    mehrere Megabyte grosse JSONL bei jedem Prompt von vorn zu parsen wuerde
    das Zeitbudget allein aufbrauchen."""
    groesse = os.path.getsize(pfad)
    ab = max(0, groesse - bytes_n)
    with open(pfad, "rb") as f:
        f.seek(ab)
        roh = f.read()
    if ab > 0:
        roh = roh.split(b"\n", 1)[1] if b"\n" in roh else b""
    return roh.decode("utf-8", "replace").splitlines()


def _sauber(t: str) -> str:
    t = re.sub(r"<system-reminder>.*?</system-reminder>", " ", t, flags=re.S)
    return " ".join(t.split())


def _verlauf(pfad_aus_haken=None, n_anfragen: int = VERLAUF_N_ANFRAGEN) -> dict:
    """Die letzten Anfragen des Eigners und die KURZEN Antworten dazu.

    ⚠️ NIE die Werkzeugausgaben. Einzelne davon laufen in die
    Zehntausende Token -- das ganze Eingabebudget des Ratgebers ist kleiner
    als eine einzige.
    """
    if os.environ.get("CLAY_RATGEBER_VERLAUF", "1") == "0":
        return {"an": False, "grund": "CLAY_RATGEBER_VERLAUF=0", "zeilen": [],
                "token": 0, "echt": False, "verworfen": 0}
    pfad = _transkript_finden(pfad_aus_haken)
    if not pfad:
        return {"an": True, "grund": "kein Transkript gefunden", "zeilen": [],
                "token": 0, "echt": False, "verworfen": 0}

    gesammelt, gesehen = [], 0
    bytes_n = TRANS_ERST_BYTES
    try:
        while True:
            gesammelt, gesehen = [], 0
            for zeile in reversed(_schwanz_zeilen(pfad, bytes_n)):
                if len(zeile) > TRANS_MAX_ZEILE or not zeile.startswith("{"):
                    continue          # Werkzeugausgabe: nie lesen, nie senden
                try:
                    d = json.loads(zeile)
                except Exception:
                    continue
                if d.get("isSidechain"):
                    continue          # Unteragenten sind nicht der Weg des Eigners
                art = d.get("type")
                if art not in ("user", "assistant"):
                    continue
                m = d.get("message")
                if not isinstance(m, dict):
                    continue
                inhalt = m.get("content")
                if art == "user":
                    if isinstance(inhalt, str):
                        t = inhalt
                    elif isinstance(inhalt, list):
                        if any(isinstance(b, dict) and b.get("type") == "tool_result"
                               for b in inhalt):
                            continue          # Werkzeugergebnis, kein Prompt
                        t = " ".join(b.get("text", "") for b in inhalt
                                     if isinstance(b, dict) and b.get("type") == "text")
                    else:
                        continue
                    t = _sauber(t)
                    if not t or t.startswith(RAUSCH):
                        continue
                    gesammelt.append(("EIGNER", t[:600]))
                    gesehen += 1
                    if gesehen >= n_anfragen:
                        break
                else:
                    if not isinstance(inhalt, list):
                        continue
                    # Nur `text`. `thinking` ist nicht gesagt worden, und
                    # `tool_use` ist eine Handlung, kein Satz.
                    t = _sauber(" ".join(
                        b.get("text", "") for b in inhalt
                        if isinstance(b, dict) and b.get("type") == "text"))
                    if not t or len(t) > 600:
                        continue      # lange Antworten sind Berichte, kein Weg
                    gesammelt.append(("ICH", t[:400]))
            if gesehen >= n_anfragen or bytes_n >= TRANS_MAX_BYTES:
                break
            if bytes_n >= os.path.getsize(pfad):
                break
            bytes_n *= 4
    except OSError as e:
        return {"an": True, "grund": "Transkript nicht lesbar: %s" % e,
                "zeilen": [], "token": 0, "echt": False, "verworfen": 0}

    gesammelt.reverse()               # aelteste zuerst
    zeilen = ["%s: %s" % (w, t) for w, t in gesammelt]
    # Harter Deckel. Ueber dem Deckel faellt das AELTESTE weg, und es wird
    # gesagt, wie viel weggefallen ist.
    verworfen = 0
    n, echt = token("\n".join(zeilen))
    while zeilen and n > VERLAUF_TOKEN_DECKEL:
        zeilen.pop(0)
        verworfen += 1
        n, echt = token("\n".join(zeilen))
    return {"an": True, "grund": None, "zeilen": zeilen, "token": n,
            "echt": echt, "verworfen": verworfen, "pfad": pfad}


# ── Stufe 1: alles zusammen ───────────────────────────────────────────────
def sammeln(frage: str, transkript=None) -> dict:
    t0 = time.time()
    c = verbindung()
    try:
        s = {
            "zustand": _zustand(c),
            "bahnen": _bahnen(c),
            "verdrahtung": _verdrahtung(c),
            "schluessel": _schluessel_lage(c),
            "werkzeuge": WERKZEUGE,
        }
        s["bestand"], s["bestand_streng"] = _eigener_bestand(c, frage)
    finally:
        c.close()
    s["verlauf"] = _verlauf(transkript)
    s["dauer_ms"] = round((time.time() - t0) * 1000, 1)
    return s


# ── Stufe 2: der Moeglichkeitsraum ────────────────────────────────────────
def _schluessel_gesund(namen, lage: dict):
    """schluessel_namen in kb_zugang heisst 'MISTRAL3_API_KEY', das Fach in
    schluessel_lage heisst 'MISTRAL3'. Ohne diese Abbildung waere jede Bahn
    grundlos gesund."""
    if not namen:
        return True, None
    schlecht = []
    for n in [x.strip() for x in str(namen).split(",") if x.strip()]:
        fach = re.sub(r"_(API_)?KEY$|_TOKEN$", "", n)
        e = lage.get(fach)
        if e is not None and e != "GESUND":
            schlecht.append("%s=%s" % (fach, e))
    # Kein Fach gefunden heisst NICHT krank -- es heisst ungeprueft. Eine
    # Bahn wegen eines fehlenden Eintrags auszuschliessen waere geraten.
    if schlecht and len(schlecht) == len(
            [x for x in str(namen).split(",") if x.strip()]):
        return False, "alle Schluessel nicht gesund: " + ", ".join(schlecht)
    if schlecht:
        return True, "einzelne Schluessel nicht gesund: " + ", ".join(schlecht)
    return True, None


def moeglichkeitsraum(s: dict) -> dict:
    """Was ginge JETZT wirklich -- gerechnet, nicht geraten."""
    z = s.get("zustand") or {}
    kont = z.get("kontingent") or {}
    eng = set(kont.get("eng") or [])
    heute = kont.get("heute") or {}
    lage = s.get("schluessel") or {}
    g429 = z.get("verdichtung", {}).get("grenze_429") or {}

    offen, zu = [], []
    for b in s.get("bahnen", []):
        zg, zust = b["zugang"], (b["zustand"] or "ungeprueft")
        if zust in TOT:
            zu.append({"weg": zg, "grund": TOT[zust]})
            continue
        ok, hinweis = _schluessel_gesund(b.get("schluessel_namen"), lage)
        if not ok:
            zu.append({"weg": zg, "grund": hinweis})
            continue
        if zg in eng:
            rest = (heute.get(zg) or [None, None])[1]
            zu.append({"weg": zg,
                       "grund": "Tagesrest fast auf -- nur noch %s" % rest})
            continue
        n429 = (g429.get(zg) or [0])[0]
        if n429:
            zu.append({"weg": zg, "grund": "%s x 429 gesehen" % n429})
            continue
        m = {"weg": zg, "modell": b.get("modell"), "zustand": zust,
             "schema": bool(b.get("kann_schema")),
             "einbettung": bool(b.get("kann_embedding")),
             "tag_limit": b.get("tag_limit"),
             "minute_limit": b.get("minute_limit"),
             "heute_genutzt": (heute.get(zg) or [0])[0]}
        if hinweis:
            m["hinweis"] = hinweis
        offen.append(m)

    # Werkzeuge: dieselbe Rechnung, aber ueber ihren Zugang.
    wz_offen, wz_zu = [], []
    bahn_nach_zugang = {b["zugang"]: b for b in s.get("bahnen", [])}
    for w in s.get("werkzeuge", []):
        if w["zugang"] is None:
            wz_offen.append(dict(w, zustand="immer da"))
            continue
        b = bahn_nach_zugang.get(w["zugang"])
        e = lage.get(w["schluessel"])
        if e is not None and e != "GESUND":
            wz_zu.append({"weg": w["name"], "grund": "Schluessel %s=%s"
                          % (w["schluessel"], e)})
            continue
        if b and (b["zustand"] or "") in TOT:
            wz_zu.append({"weg": w["name"],
                          "grund": TOT[b["zustand"]]})
            continue
        wz_offen.append(dict(w, zustand=(b or {}).get("zustand", "ungeprueft")))

    # Verdrahtung: welcher Prozess faehrt auf welcher OFFENEN Bahn.
    offene_namen = {m["weg"] for m in offen}
    prozesse = []
    for v in s.get("verdrahtung", []):
        kette = [v.get("bahn_erst"), v.get("bahn_zweit"), v.get("bahn_dritt")]
        traegt = [x for x in kette if x and x in offene_namen]
        prozesse.append({"prozess": v["prozess"],
                         "traegt_jetzt": traegt,
                         "erste_wahl": v.get("bahn_erst"),
                         "max_je_lauf": v.get("max_je_lauf")})
    return {"bahnen": offen, "werkzeuge": wz_offen,
            "prozesse": prozesse, "ausgeschlossen": zu + wz_zu}


# ── Ist ueberhaupt etwas zu sagen? ────────────────────────────────────────
def hat_bezug(s: dict, m: dict) -> tuple:
    """Ehrlichkeitstor. Findet Stufe 1 keinen Bezug UND Stufe 2 keine
    Moeglichkeit, ist 'kein Vorschlag' die richtige Antwort."""
    if not m["bahnen"] and not m["werkzeuge"]:
        return False, "kein einziger Weg ist gerade offen"
    z = s.get("zustand") or {}
    if z.get("fehler"):
        return False, "der Lebendzustand ist nicht abrufbar: %s" % z["fehler"]
    return True, None


# ── Stufe 3: Mistral ──────────────────────────────────────────────────────
def _schema() -> dict:
    st = lambda n: {"type": "string", "maxLength": n}   # noqa: E731
    return {
        "type": "object",
        "properties": {
            "vorschlag": st(160),
            "herleitung": st(320),
            "weshalb": st(160),
            "danach": st(160),
            "weg": st(200),
            "bahn": st(70),
            "kosten": st(90),
            "eigener_bestand": st(140),
            "verworfen": {
                "type": "array", "maxItems": 3,
                "items": {"type": "object",
                          "properties": {"weg": st(70), "grund": st(110)},
                          "required": ["weg", "grund"],
                          "additionalProperties": False}},
            "unsicherheit": st(140),
        },
        "required": ["vorschlag", "herleitung", "weshalb", "danach", "weg",
                     "bahn", "kosten", "eigener_bestand", "verworfen",
                     "unsicherheit"],
        "additionalProperties": False,
    }


SYSTEM = (
    "Du bist der Ratgeber von ClayVerse. Du raetst, du entscheidest nicht und "
    "du handelst nicht. Alles, was du lieferst, ist ein VORSCHLAG.\n"
    "SEHR KNAPP: jedes Feld hoechstens ein bis zwei kurze Saetze, hoechstens "
    "drei verworfene Wege. Deutsch.\n"
    "herleitung MUSS die Datenpunkte woertlich nennen, die du benutzt hast "
    "(Bahnnamen, Zahlen, Zustaende aus dem ZUSTAND-Block). Ohne genannte "
    "Datenpunkte ist die Herleitung wertlos.\n"
    "bahn DARF NUR aus dem MOEGLICHKEITSRAUM stammen. Eine Bahn, die dort "
    "nicht steht, existiert fuer dich nicht.\n"
    "kosten: nur beziffern, was im MOEGLICHKEITSRAUM beziffert ist. Sonst "
    "'unbekannt' schreiben. Nichts erfinden -- keine Preise, keine Grenzen.\n"
    "weg: ein bis zwei Saetze, welcher Weg zu dieser Anfrage gefuehrt hat, "
    "AUSSCHLIESSLICH aus dem VERLAUF-Block belegt. ⚠️ Steht dort nichts oder "
    "nichts Passendes, schreibe genau 'kein erkennbarer Weg'. Erfinde NIE "
    "eine Fortsetzung, einen Zusammenhang oder eine Absicht. Ein Ratgeber, "
    "der immer einen roten Faden findet, erfindet ihn.\n"
    "unsicherheit: was dieser Vorschlag NICHT weiss."
)


def _block(s: dict, m: dict, frage: str) -> str:
    z = s.get("zustand") or {}
    p = z.get("puls") or {}
    k = z.get("kontingent") or {}
    sc = z.get("schluessel") or {}
    a = z.get("arbeit") or {}
    v = z.get("verdichtung") or {}
    t = []
    t.append("ZUSTAND (gemessen, 0 Modellaufrufe):")
    t.append("  puls=%s takt=%ss folge=%s | verdichtung=%s stroeme %s/%s "
             "offen=%s" % (p.get("lage"), p.get("takt_s"), p.get("folge"),
                           v.get("lage"), v.get("aktiv"), v.get("stroeme"),
                           v.get("offen_gesamt")))
    t.append("  schluessel: %s von %s gesund; nicht gesund: %s"
             % (sc.get("gesund"), sc.get("n"),
                ", ".join("%s=%s" % (n, e[0]) for n, e in
                          (sc.get("nicht_gesund") or {}).items()) or "keine"))
    t.append("  kontingent: %s Zugaenge gefuehrt, %s davon mit hartem Limit; "
             "heute knapp: %s" % (k.get("zugaenge"), k.get("mit_limit"),
                                  ", ".join(k.get("eng") or []) or "keiner"))
    genutzt = {n: w[0] for n, w in (k.get("heute") or {}).items() if w[0]}
    if genutzt:
        t.append("  heute schon verbraucht: %s" % ", ".join(
            "%s %s" % (n, w) for n, w in sorted(genutzt.items())))
    t.append("  kuration offen=%s, problem=%s, durchsatz letzte Stunde=%s"
             % ((a.get("kuration") or {}).get("offen"), a.get("problem"),
                a.get("durchsatz_1h")))

    t.append("MOEGLICHKEITSRAUM (aus dem Gemessenen gerechnet -- nur diese "
             "Wege existieren):")
    for b in m["bahnen"]:
        gr = []
        if b["schema"]:
            gr.append("json_schema")
        if b["einbettung"]:
            gr.append("Einbettung")
        if b["tag_limit"]:
            gr.append("%s/Tag" % int(b["tag_limit"]))
        if b["minute_limit"]:
            gr.append("%s/min" % int(b["minute_limit"]))
        t.append("  Bahn %s (%s, %s)%s%s" % (
            b["weg"], b["modell"] or "kein Modellname gefuehrt", b["zustand"],
            (" — " + ", ".join(gr)) if gr else "",
            (" — heute %s benutzt" % b["heute_genutzt"]) if b["heute_genutzt"] else ""))
    for w in m["werkzeuge"]:
        t.append("  Werkzeug %s (%s) — %s" % (w["name"], w["zustand"], w["kosten"]))
    tragend = [p for p in m["prozesse"] if p["traegt_jetzt"]]
    if tragend:
        t.append("  verdrahtete Prozesse, die JETZT tragen: %s" % ", ".join(
            "%s→%s" % (p["prozess"], p["traegt_jetzt"][0]) for p in tragend))
    if m["ausgeschlossen"]:
        t.append("AUSGESCHLOSSEN (gemessen, keine Moeglichkeit):")
        for x in m["ausgeschlossen"][:10]:
            t.append("  %s — %s" % (x["weg"], x["grund"]))

    t.append("EIGENER BESTAND (Wiki-Volltext):")
    if s.get("bestand"):
        for b in s["bestand"]:
            t.append("  %s: %s" % (b["titel"], b["auszug"]))
    else:
        t.append("  keine Treffer — dazu steht bei uns nichts.")

    t.append("VERLAUF (die letzten Nachrichten dieser Sitzung):")
    vl = s.get("verlauf") or {}
    if vl.get("zeilen"):
        for zl in vl["zeilen"]:
            t.append("  " + zl)
        if vl.get("verworfen"):
            t.append("  (%s aeltere Nachrichten wegen Deckel weggelassen)"
                     % vl["verworfen"])
    else:
        t.append("  nichts lesbar — %s" % (vl.get("grund") or "leer"))

    t.append("FRAGE: " + frage.strip()[:1200])
    return "\n".join(t)


def frage_mistral(block: str, frist=None) -> dict:
    frist = FRIST_S if frist is None else frist
    body = {
        "model": MODELL, "max_tokens": MAX_TOKEN, "temperature": 0.2,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "ratgeber", "strict": True, "schema": _schema()}},
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": block}],
    }
    daten = json.dumps(body).encode("utf-8")
    r = urllib.request.Request(URL, data=daten, headers={
        "Authorization": "Bearer " + schluessel(),
        "Content-Type": "application/json",
        "User-Agent": "ClayVerse-Ratgeber/1.0 (+https://frank.ink)"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=frist) as a:
            st, leib = a.status, a.read()
    except urllib.error.HTTPError as e:
        ms = (time.time() - t0) * 1000
        return {"ok": False, "grund": "HTTP %s" % e.code, "ms": round(ms, 1),
                "http": e.code}
    except Exception as e:
        ms = (time.time() - t0) * 1000
        art = "Frist %.1fs ueberschritten" % frist if isinstance(
            e, (TimeoutError, OSError)) and "timed out" in str(e).lower() \
            else "Netzfehler: %s" % str(e)[:120]
        return {"ok": False, "grund": art, "ms": round(ms, 1), "http": 0}
    ms = (time.time() - t0) * 1000
    try:
        d = json.loads(leib)
        ch = d["choices"][0]
        # ⚠️ Ein Abschnitt ist ein EIGENER Ablehnungsgrund, kein Schemabruch.
        # Genau dort versagt die Schemazusage still.
        if ch.get("finish_reason") == "length":
            return {"ok": False, "grund": "Antwort abgeschnitten "
                    "(finish_reason=length) — max_tokens zu klein",
                    "ms": round(ms, 1), "http": st}
        inhalt = json.loads(ch["message"]["content"])
    except Exception as e:
        return {"ok": False, "grund": "Antwort nicht lesbar: %s" % str(e)[:120],
                "ms": round(ms, 1), "http": st}
    u = d.get("usage") or {}
    return {"ok": True, "vorschlag": inhalt, "ms": round(ms, 1), "http": st,
            "token_ein": u.get("prompt_tokens"),
            "token_aus": u.get("completion_tokens")}


# ── Buchung ───────────────────────────────────────────────────────────────
def buchen(zweck: str) -> None:
    """Jeder Ruf wird gebucht -- aber ABGEKOPPELT. Buchfuehrung darf einen
    Prompt niemals aufhalten, deshalb eigene Sitzung und kein wait().
    ⚠️ Folge, die sichtbar bleiben muss: wird der Prozess hart getoetet,
    bevor das Kind schreibt, fehlt genau diese eine Buchung."""
    try:
        import subprocess
        subprocess.Popen(
            ["/usr/bin/python3", KONTINGENT, "buchen", "--konto", KONTO,
             "--zugang", ZUGANG, "--menge", "1", "--einheit", "anfrage",
             "--zweck", zweck[:180],
             # Nur der NAME des Faches, nie sein Wert. `mistral` ist ein
             # mehrdeutiger Zugang -- ohne den Hinweis waere spaeter nicht
             # mehr feststellbar, welcher der drei Toepfe belastet wurde.
             "--schluessel-hinweis", SCHLUESSEL_NAME],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass


# ── Der eine Aufruf ───────────────────────────────────────────────────────
def ratgeber(frage: str, transkript=None, frist=None,
             nur_mechanisch: bool = False) -> dict:
    t0 = time.time()
    s = sammeln(frage, transkript)
    m = moeglichkeitsraum(s)
    bezug, warum_nicht = hat_bezug(s, m)
    erg = {"frage": frage, "mechanisch": {
        "dauer_ms": s["dauer_ms"],
        "zustand": s["zustand"], "moeglichkeitsraum": m,
        "bestand": s["bestand"], "bestand_streng": s["bestand_streng"],
        "verlauf": {k: v for k, v in s["verlauf"].items() if k != "pfad"}}}
    aus = os.environ.get("CLAY_RATGEBER_AUS") == "1"
    if nur_mechanisch or aus or not bezug:
        erg["vorschlag"] = None
        erg["grund"] = (warum_nicht if not bezug else
                        ("CLAY_RATGEBER_AUS=1" if aus else "nur mechanisch"))
        erg["dauer_ms"] = round((time.time() - t0) * 1000, 1)
        return erg
    block = _block(s, m, frage)
    erg["mechanisch"]["block_token"], erg["mechanisch"]["block_token_echt"] = \
        token(SYSTEM + block)
    a = frage_mistral(block, frist)
    erg["mistral"] = {k: v for k, v in a.items() if k != "vorschlag"}
    if a["ok"]:
        buchen("ratgeber/%s" % frage.strip()[:60])
        erg["vorschlag"] = a["vorschlag"]
        erg["grund"] = None
    else:
        erg["vorschlag"] = None
        erg["grund"] = a["grund"]
    erg["dauer_ms"] = round((time.time() - t0) * 1000, 1)
    return erg


# ── Darstellung ───────────────────────────────────────────────────────────
def als_text(e: dict) -> str:
    m = e["mechanisch"]
    mr = m["moeglichkeitsraum"]
    z = m["zustand"]
    t = []
    p = z.get("puls") or {}
    sc = z.get("schluessel") or {}
    k = z.get("kontingent") or {}
    t.append("ZUSTAND (gemessen, 0 Modellaufrufe, %.0f ms): puls %s · "
             "%s/%s Schluessel gesund · %s Zugaenge, knapp: %s"
             % (m["dauer_ms"], p.get("lage"), sc.get("gesund"), sc.get("n"),
                k.get("zugaenge"), ", ".join(k.get("eng") or []) or "keiner"))
    t.append("MOEGLICHKEITSRAUM (gerechnet): %s Bahnen offen (%s) · "
             "%s Werkzeuge · %s ausgeschlossen"
             % (len(mr["bahnen"]),
                ", ".join(b["weg"] for b in mr["bahnen"][:6]),
                len(mr["werkzeuge"]), len(mr["ausgeschlossen"])))
    if m["bestand"]:
        t.append("EIGENER BESTAND: " + " | ".join(
            b["titel"] for b in m["bestand"]))

    v = e.get("vorschlag")
    if not v:
        t.append("KEIN VORSCHLAG — %s. Oben steht der Zustand, mehr ist "
                 "gerade ehrlich nicht zu sagen." % e.get("grund"))
        return "\n".join(t)

    t.append("")
    t.append("VORSCHLAG (Ratgeber, KEINE Autoritaet — er raet, er entscheidet "
             "nicht):")
    t.append("  was:        " + v["vorschlag"])
    t.append("  herleitung: " + v["herleitung"])
    t.append("  weshalb so: " + v["weshalb"])
    t.append("  danach:     " + v["danach"])
    t.append("  weg hierher:" + v["weg"])
    t.append("  bahn:       %s (%s)" % (v["bahn"], v["kosten"]))
    t.append("  wir haben:  " + (v["eigener_bestand"] or "—"))
    if v.get("verworfen"):
        t.append("  verworfen:  " + " | ".join(
            "%s (%s)" % (x["weg"], x["grund"]) for x in v["verworfen"]))
    t.append("  weiss nicht:" + v["unsicherheit"])
    return "\n".join(t)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Ratgeber (Vorschlag, keine "
                                             "Autoritaet)")
    ap.add_argument("--frage", default=None)
    ap.add_argument("--frage-datei", default=None,
                    help="Frage aus einer DATEI lesen. Der Haken nimmt diesen "
                         "Weg: verschachtelte Anfuehrungszeichen auf der "
                         "Kommandozeile haben hier schon zweimal einen "
                         "Aufruf zerlegt.")
    ap.add_argument("--transkript", default=None)
    ap.add_argument("--frist", type=float, default=None)
    ap.add_argument("--nur-mechanisch", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--still", action="store_true",
                    help="nichts auf stdout -- nur die Spool-Datei schreiben")
    ap.add_argument("--spool", default=None,
                    help="Ergebnis atomar hierhin schreiben (fuer den Haken)")
    a = ap.parse_args()
    frage = a.frage
    if a.frage_datei:
        with open(a.frage_datei, encoding="utf-8") as f:
            frage = f.read()
    if not frage or not frage.strip():
        ap.error("--frage oder --frage-datei noetig (und nicht leer)")
    e = ratgeber(frage, a.transkript or None, a.frist, a.nur_mechanisch)
    if a.spool:
        tmp = a.spool + ".teil"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(e, f, ensure_ascii=False)
        os.replace(tmp, a.spool)      # atomar: der Haken sieht nie ein Halbes
    if a.still:
        return 0
    if a.json:
        print(json.dumps(e, ensure_ascii=False, indent=1))
    else:
        print(als_text(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
