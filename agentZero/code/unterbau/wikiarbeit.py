#!/usr/bin/env python3
"""wikiarbeit.py — ein Groq-Konto, das dauerhaft an der Wissensbasis arbeitet.

    Auftrag des Eigentuemers: "ein groq account soll im wiki permanent
    arbeiten aber sinnvoll".

Das zweite Wort ist die eigentliche Vorschrift. Ein Arbeiter, der pausenlos
laeuft und Rauschen erzeugt, ist SCHLECHTER als einer, der schlaeft: er sieht
fleissig aus, waehrend er den Bestand verdirbt. Deshalb gilt hier:

  * Nichts wird zweimal getan. Vor jedem Aufruf wird geprueft, ob die Arbeit
    inzwischen von jemand anderem erledigt wurde.
  * Es wird das WERTVOLLSTE offene Stueck genommen, nicht das naechste in der
    Zeilenreihenfolge.
  * Ist nichts Sinnvolles offen, wird geschlafen und das gesagt — es wird
    keine Arbeit erfunden.
  * Alles, was herauskommt, ist ein VORSCHLAG und landet in `anreicherung`,
    nie direkt in `artikel`:

        model_output_is_not_authority          (owner-fixed, ClayGraph)

DATENBANK
    Genau eine: /var/lib/clay/wiki.db. Das ist zugleich die vereinheitlichte
    Datenbank (/opt/unifieddb/udb/ zeigt darauf). Kein zweiter Speicher, kein
    privates Ablagefach. Eigene Tabellen tragen den Vorsatz `wk_`
    (`wa_` gehoert bereits der Wache), die Ergebnisse gehen in die
    BESTEHENDE `bahn_lauf` — ein Ort zum Nachsehen, kein neues Silo.

KONTO
    Ausschliesslich GROQ3_API_KEY. Das ist ein eigener Topf, gemessen an
    x-ratelimit-remaining-requests: 14.400 Anfragen/Tag, 30/min, 6.000
    Token/min fuer llama-3.1-8b-instant. 14.400/Tag heisst EINE ANFRAGE ALLE
    6 SEKUNDEN im Dauerbetrieb. Kein Stossbetrieb.
"""
import argparse
import json
import math
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone, timedelta

DB = os.environ.get("CLAY_DB", "/var/lib/clay/wiki.db")
ENV = "/etc/clayverse/freie-zugaenge.env"
KONTINGENT = "/opt/clayverse/werkzeug/kontingent.py"

KONTO = "clayverse"          # ⚠️ 'clayverse_grundlast' GIBT ES NICHT — kontingent.py
ZUGANG = "groq"              #    bricht bei unbekanntem Konto hart ab.
SCHLUESSEL_NAME = "GROQ3_API_KEY"
URL = "https://api.groq.com/openai/v1/chat/completions"
ABSENDER = "clayverse-wikiarbeit/1.0"   # urllib-Kennung wird von Cloudflare abgewiesen

# ── GEMESSENE DECKEL (aus Live-Kopfzeilen, nicht aus einer Doku) ───────
MODELL_KLEIN = "llama-3.1-8b-instant"      # 14.400 Anfragen/Tag,  6.000 Token/min
MODELL_GROSS = "llama-3.3-70b-versatile"   #  1.000 Anfragen/Tag, 12.000 Token/min
TAGESBUDGET = 14400

# ── WELCHES MODELL FUER WELCHE ARBEIT — GEMESSEN, NICHT GERATEN ───────
# A/B am 2026-08-15, 50 identische Stuecke der Art `titel`, gleiche Pruefung:
#     llama-3.1-8b-instant       angenommen  5 / 50  =  10,0 %
#     llama-3.3-70b-versatile    angenommen 26 / 50  =  52,0 %
# Das Kleine scheitert MESSBAR: es haengt Dateiendungen an (10x), gibt
# Kennungen mit Unterstrich zurueck (5x) und erfindet Woerter, die im Text
# nicht stehen (10x). Deshalb — und nur deshalb — laeuft `titel` auf dem
# grossen Modell. Das kostet: es hat 1.000 statt 14.400 Anfragen am Tag,
# also einen EIGENEN Deckel, damit es die Grundarbeit nicht auffrisst.
MODELL_JE_ART = {"sphaere": MODELL_KLEIN, "titel": MODELL_GROSS}
DECKEL_JE_MODELL = {MODELL_KLEIN: 14400, MODELL_GROSS: 1000}
TAKT_S = 6.0                 # 86.400 s / 14.400 = 6,0 s
TPM_DECKEL = 5200            # von 6.000 gemessenen, mit Sicherheitsabstand
LEERLAUF_SCHLAF_S = 30.0     # so oft wird die Warteschlange nachgesehen
LEBENSZEICHEN_S = 300.0      # so oft wird im Leerlauf eine Zeile geschrieben
REST_STOPP = 50              # Kopfzeile sagt weniger als das uebrig -> Feierabend

SPHAEREN = ("frank_v0_1", "seimensch", "iar", "andreas", "gabriel",
            "clayverse", "fremd", "unklar")

# Titel, die nur der Dateiname sind — fuer die Wiederauffindung wertlos.
ENDUNGEN = (".md", ".py", ".txt", ".json", ".log", ".sh", ".yml", ".yaml",
            ".html", ".csv", ".db", ".sql", ".jsonl", ".ini", ".toml",
            ".js", ".ts", ".css", ".xml", ".cfg", ".conf")

# ── WERT: woraus er kommt und warum ───────────────────────────────────
# ⚠️ ECHTE REICHWEITE IST HIER NICHT MESSBAR. Gemessen am 2026-08-15:
#   vp_paket_log  223 Zeilen, alle aus EINER Frage, und die Treffer sind
#                 datei-Kennungen ("d854"), keine artikel-Kennungen.
#   vp_lese_log     9 Zeilen.
#   taetigkeit_kante deckt 62 von 14.284 Artikeln ab = 0,4 %.
# Damit laesst sich "wie oft wird dieser Artikel erreicht" NICHT belegen.
# ERSATZMASS (bewusst als solches benannt, damit es spaeter durch ein echtes
# ersetzt und nicht mit einem verwechselt wird): der ZITIERGRAD im Kantennetz.
# Wer oft als Beleg genannt wird, wird auch oft gebraucht.
#   semantische Kanten (Beleg/Stuetze/Ableitung) zaehlen dreifach,
#   strukturelle Kanten (gleiches Verzeichnis) fast gar nicht — von 19.383
#   Kanten sind 12.239 blosse Verzeichnisnachbarschaft, das ist kein Zitat.
SEM_ARTEN = ("source_refs", "stuetzt", "verdichtet_aus", "evidence",
             "evidence_refs", "artifacts", "lauf_referenz", "gleicher_inhalt",
             "nachfolge_version")
# SETZUNG, keine Messung: Wissenstraeger vor Rohdatei. Klein gehalten, damit
# sie den gemessenen Anteil nicht ueberstimmt.
ART_BONUS = {"hypothese": 1.5, "gegenhypothese": 1.5, "forschungsergebnis": 1.5,
             "begriff": 1.5, "vorfall": 1.5, "iar_seite": 1.5, "lehre": 1.5,
             "quelldatei": 0.0}
ART_BONUS_SONST = 0.5

_laeuft = True


def _halt(signum, rahmen):
    global _laeuft
    _laeuft = False


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def tagesanfang() -> str:
    n = datetime.now(timezone.utc)
    return n.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def umgebung() -> dict:
    """Liest die Schluessel. Gibt sie NIE aus und legt sie NIE in argv."""
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


def oeffne() -> sqlite3.Connection:
    c = sqlite3.connect(DB, timeout=60)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    return c


def schreib(c: sqlite3.Connection, sql: str, p: tuple = ()) -> None:
    """Viele Schreiber auf einer WAL-Datei. Nicht sterben, sondern warten."""
    for versuch in range(6):
        try:
            c.execute(sql, p)
            c.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" not in str(e) and "busy" not in str(e):
                raise
            time.sleep(0.5 * (versuch + 1))
    raise sqlite3.OperationalError("Datenbank blieb belegt")


def tabellen(c: sqlite3.Connection) -> None:
    """Vorsatz `wk_`. `wa_` gehoert der Wache (wa_ereignis/wa_grenze/wa_snapshot)."""
    c.execute("""CREATE TABLE IF NOT EXISTS wk_aufgabe (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        art           TEXT NOT NULL,
        artikel_id    TEXT NOT NULL,
        wert          REAL NOT NULL DEFAULT 0,
        zustand       TEXT NOT NULL DEFAULT 'offen'
                      CHECK (zustand IN ('offen','laeuft','fertig','verworfen','unbedienbar')),
        versuche      INTEGER NOT NULL DEFAULT 0,
        letzter_grund TEXT,
        angelegt      TEXT NOT NULL,
        geaendert     TEXT NOT NULL,
        UNIQUE (art, artikel_id)
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_wk_aufgabe_wahl "
              "ON wk_aufgabe(zustand, wert DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_wk_aufgabe_art "
              "ON wk_aufgabe(art, zustand)")
    # bahn_lauf waechst um bis zu 14.400 Zeilen am Tag, und der Tagesdeckel
    # zaehlt bei JEDEM Schleifendurchlauf darin. Ohne Index waere das nach
    # wenigen Wochen der teuerste Teil der Schleife.
    c.execute("CREATE INDEX IF NOT EXISTS idx_bahn_lauf_art_zeit "
              "ON bahn_lauf(art, zeit)")
    c.commit()


def lage(c: sqlite3.Connection, schluessel: str, wert) -> None:
    """Lebenszeichen in bahn_lage. Leerlauf und tot duerfen sich nicht gleichen."""
    try:
        schreib(c, "INSERT INTO bahn_lage(schluessel,wert,zeit) VALUES (?,?,?) "
                   "ON CONFLICT(schluessel) DO UPDATE SET wert=excluded.wert, "
                   "zeit=excluded.zeit", (schluessel, str(wert), jetzt()))
    except Exception:
        pass


# ── KONTINGENTBUCH ─────────────────────────────────────────────────────

def darf(menge: int) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["python3", KONTINGENT, "darf", "--konto", KONTO,
             "--zugang", ZUGANG, "--menge", str(menge)],
            capture_output=True, text=True, timeout=30)
        for z in r.stdout.splitlines():
            if "erlaubt" in z and "von" in z:
                return int(float(z.split()[0])), z.strip()
        return 0, "keine verwertbare Antwort vom Kontingentbuch — kein Aufruf"
    except Exception as e:
        return 0, f"Kontingentbuch nicht erreichbar: {e}"


def buchen(menge: float, zweck: str) -> None:
    try:
        subprocess.run(["python3", KONTINGENT, "buchen", "--konto", KONTO,
                        "--zugang", ZUGANG, "--menge", str(menge),
                        "--zweck", zweck], capture_output=True, text=True,
                       timeout=30)
    except Exception:
        pass


def heute_verbraucht(c: sqlite3.Connection, modell: str | None = None) -> int:
    """Harter Tagesdeckel — auch ueber Neustarts hinweg.

    Gezaehlt wird aus bahn_lauf, nicht aus einem eigenen Zaehler: ein Zaehler
    im Speicher waere nach jedem Neustart wieder auf null, und genau darueber
    liesse sich der Deckel umgehen. Gezaehlt wird ALLES, was eine Anfrage
    verbraucht hat — auch Fehler; nur Leerlaufzeilen kosten nichts.
    """
    ta = tagesanfang()
    if modell:
        r = c.execute("SELECT count(*) FROM bahn_lauf "
                      "WHERE art IN ('wikiarbeit','wikiarbeit_ab') "
                      "AND ergebnis <> 'leerlauf' AND modell = ? AND zeit >= ?",
                      (modell, ta)).fetchone()
    else:
        r = c.execute("SELECT count(*) FROM bahn_lauf "
                      "WHERE art IN ('wikiarbeit','wikiarbeit_ab') "
                      "AND ergebnis <> 'leerlauf' AND zeit >= ?", (ta,)).fetchone()
    return int(r[0] or 0)


def freie_arten(c: sqlite3.Connection) -> list:
    """Welche Arbeitsarten haben heute noch Kontingent auf ihrem Modell?"""
    frei = []
    for art, modell in MODELL_JE_ART.items():
        if heute_verbraucht(c, modell) < DECKEL_JE_MODELL.get(modell, TAGESBUDGET):
            frei.append(art)
    return frei


# ── DER AUFRUF ─────────────────────────────────────────────────────────

class Takt:
    """Haelt 6 s Abstand und den Token-Deckel von 6.000/min ein."""

    def __init__(self):
        self.letzte = 0.0
        self.fenster = deque()   # (zeit, token)

    def warte(self, geschaetzt: int) -> None:
        rest = TAKT_S - (time.monotonic() - self.letzte)
        while rest > 0 and _laeuft:
            time.sleep(min(0.25, rest))
            rest = TAKT_S - (time.monotonic() - self.letzte)
        while _laeuft:
            n = time.monotonic()
            while self.fenster and n - self.fenster[0][0] > 60:
                self.fenster.popleft()
            if sum(t for _, t in self.fenster) + geschaetzt <= TPM_DECKEL:
                break
            time.sleep(1.0)
        self.letzte = time.monotonic()

    def bucheTokens(self, n: int) -> None:
        self.fenster.append((time.monotonic(), max(0, n)))


def rufen(schluessel: str, modell: str, system: str, frage: str,
          max_token: int) -> dict:
    daten = json.dumps({
        "model": modell,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": frage}],
        "max_tokens": max_token, "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        URL, data=daten,
        headers={"Authorization": f"Bearer {schluessel}",
                 "Content-Type": "application/json",
                 "User-Agent": ABSENDER})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            roh = json.loads(r.read().decode())
            u = roh.get("usage") or {}
            rest = r.headers.get("x-ratelimit-remaining-requests")
            return {"ok": True, "http": r.status,
                    "ms": (time.perf_counter() - t0) * 1000,
                    "text": (roh["choices"][0]["message"]["content"] or "").strip(),
                    "ein": u.get("prompt_tokens"), "aus": u.get("completion_tokens"),
                    "rest": int(rest) if rest and rest.isdigit() else None}
    except urllib.error.HTTPError as e:
        koerper = e.read()[:200].decode("utf-8", "replace")
        return {"ok": False, "http": e.code,
                "ms": (time.perf_counter() - t0) * 1000, "text": "",
                "fehler": koerper, "warte": e.headers.get("retry-after"),
                "rest": None}
    except Exception as e:
        return {"ok": False, "http": 0, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": str(e)[:200], "warte": None, "rest": None}


# ── DIE PRUEFUNG ───────────────────────────────────────────────────────
# HTTP 200 ist kein Ergebnis, sondern ein Vorschlag. Was hier durchfaellt,
# wird verworfen UND mit Grund gezaehlt.
# ⚠️ Ein Arbeiter, der nie etwas verwirft, ist kaputt, nicht perfekt.

_FLOSKEL = ("i cannot", "i can't", "as an ai", "sorry", "hier ist", "here is",
            "der titel", "titel:", "title:", "based on", "ich kann")

# ⚠️ GEMESSEN im ersten A/B-Anlauf: das Modell gab als "Titel" die eigene
# Ingest-Floskel des Artikels zurueck ("KEIN STRUKTURIERTES TITEL-METADATEN-
# FELD GEFUNDET"). Woertlich im Text belegt — und trotzdem wertlos. Die
# Erdungspruefung allein reicht also NICHT; ein Titel, der nur sagt, dass es
# keinen Titel gibt, ist Rauschen.
_INGEST_FLOSKEL = ("kein titel", "kein strukturier", "titelfeld",
                   "metadatenfeld", "mechanisch als duenn", "keine angabe",
                   "kein sub-record", "nicht gefunden", "kein listenschema",
                   "unbenannt", "ohne titel", "leere datei")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = (s.replace("ä", "ae").replace("ö", "oe")
          .replace("ü", "ue").replace("ß", "ss"))
    return re.sub(r"[^a-z0-9]+", " ", s)


def pruefe_sphaere(text: str) -> tuple[bool, str, str]:
    """Genau eines von acht Woertern. Kein Zurechtbiegen."""
    t = (text or "").strip().strip(".").strip('"').lower()
    t = t.split()[0] if t else ""
    if not t:
        return False, "", "leere Antwort"
    if t not in SPHAEREN:
        return False, t, f"ausserhalb der erlaubten Menge: {text[:50]!r}"
    if t == "unklar":
        return False, t, "Modell sagt selbst unklar — richtig, wird nicht gesetzt"
    return True, t, ""


def pruefe_titel(text: str, alt_titel: str, beleg_text: str) -> tuple[bool, str, str]:
    """Ein Titel muss aus dem Text kommen, nicht aus dem Modell.

    Die Erdung ist der eigentliche Riegel: mindestens 60 % der Inhaltswoerter
    des Vorschlags muessen woertlich im Quelltext (oder im Dateinamen) stehen.
    Damit kann das Modell keinen huebschen Titel erfinden, der nichts mit der
    Datei zu tun hat.
    """
    roh = (text or "").strip()
    if not roh:
        return False, "", "leere Antwort"
    zeilen = [z.strip() for z in roh.splitlines() if z.strip()]
    if len(zeilen) > 1:
        return False, roh[:60], "mehrzeilige Antwort statt eines Titels"
    t = zeilen[0].strip().strip('"').strip("'").strip("*").strip("`").strip()
    t = re.sub(r"\s+", " ", t).rstrip(".")
    if t.upper().startswith("UNKLAR"):
        return False, t, "Modell sagt selbst unklar — richtig, wird nicht gesetzt"
    n = t.lower()
    for f in _FLOSKEL:
        if n.startswith(f):
            return False, t[:60], "Floskel statt Titel"
    if len(t) < 12 or len(t) > 90:
        return False, t[:60], f"Laenge {len(t)} ausserhalb 12..90"
    if re.search(r"\.[a-z]{1,6}\b", n):
        return False, t[:60], "enthaelt eine Dateiendung"
    for f in _INGEST_FLOSKEL:
        if f in n:
            return False, t[:60], "gibt nur die Ingest-Floskel zurueck"
    if t == t.upper() and len(re.sub(r"[^A-Za-z]", "", t)) > 6:
        return False, t[:60], "durchgehend Grossbuchstaben — kein Titel"
    # ⚠️ GEMESSEN: "koordination_id claycode-multiworker-20260809T0128p0700"
    # kam durch die Erdung — es STEHT woertlich im Text. Ein Schluessel-Wert-
    # Paar oder eine Kennung ist trotzdem kein Titel.
    if "_" in t:
        return False, t[:60], "Kennung statt Titel (Unterstrich)"
    if "=" in t:
        return False, t[:60], "Schluessel-Wert-Paar statt Titel"
    for w in t.split():
        if len(w) >= 16 and any(z.isdigit() for z in w):
            return False, t[:60], "enthaelt eine lange Kennung statt eines Wortes"
    alle = _norm(t).split()
    if len(alle) < 3 or len(alle) > 12:
        return False, t[:60], f"{len(alle)} Woerter — verlangt sind 3 bis 9"
    if _norm(t).strip() == _norm(alt_titel).strip():
        return False, t[:60], "wiederholt nur den Dateinamen"
    woerter = [w for w in alle if len(w) >= 4]
    if len(woerter) < 2:
        return False, t[:60], "zu wenige Inhaltswoerter"
    heu = " " + _norm(beleg_text + " " + alt_titel) + " "
    treffer = sum(1 for w in woerter if (" " + w + " ") in heu or w in heu)
    if treffer / len(woerter) < 0.6:
        return False, t[:60], f"nicht im Text belegt ({treffer}/{len(woerter)} Woerter)"
    return True, t, ""


# ── DIE WARTESCHLANGE ──────────────────────────────────────────────────

SYS_SPHAERE = ("you sort. answer ONE word from this list, nothing else:\n"
               + " ".join(SPHAEREN) + "\n"
               "frank_v0_1=frank the entity. seimensch=the association website.\n"
               "iar=research institute. andreas / gabriel=that person own work.\n"
               "clayverse=the server itself. fremd=third party. unklar=you not sure.\n"
               "if not clear, say unklar. never invent.")

# ⚠️ GEMESSEN: ein Beispieltitel im Systemteil wird vom 8B WOERTLICH
# nachgeplappert — 3 von 27 Antworten waren mein eigenes Beispiel, egal
# welche Datei. Deshalb steht hier KEIN Beispieltitel, nur die Form.
SYS_TITEL = ("you name file. answer ONE german title, 3 to 9 words, normal\n"
             "writing. use ONLY words that stand in the text below.\n"
             "never invent. never repeat these instructions.\n"
             "forbidden: file name, ending like .md or .py, quotes, colon,\n"
             "ALL CAPS, under_scores, long ids, key=value, any explanation.\n"
             "one line only. the title must say what THIS text is about.\n"
             "text tell nothing? answer exactly: UNKLAR")


def _kandidaten_sphaere(c) -> list:
    """Ohne Sphaere — und ohne dass schon jemand anderer eine vorgeschlagen hat.

    Gemessen 2026-08-15: 11.859 Artikel ohne Sphaere; 0 davon haben eine
    wm_lesart der Achse 'sphaere'; 20 haben bereits einen bahn.py-Vorschlag
    in `anreicherung` — die bleiben draussen (nichts zweimal tun).
    """
    return c.execute("""
        SELECT a.id, a.art
          FROM artikel a
         WHERE (a.sphaere IS NULL OR a.sphaere = '')
           AND coalesce(a.verfallen,0) = 0
           AND a.titel IS NOT NULL AND length(a.titel) >= 10
           AND NOT EXISTS (SELECT 1 FROM artikel_sphaere s
                            WHERE s.artikel_id = a.id)
           AND NOT EXISTS (SELECT 1 FROM wm_lesart l
                            WHERE l.artikel_id = a.id AND l.achse = 'sphaere')
           AND NOT EXISTS (SELECT 1 FROM anreicherung n
                            WHERE n.artikel_id = a.id
                              AND n.auszug LIKE '%"feld": "sphaere"%')
    """).fetchall()


def _kandidaten_titel(c) -> list:
    """Titel ist nur der Dateiname UND es gibt genug Text, um einen zu belegen.

    Ohne Text kann ein Titel nur erfunden werden. Solche Artikel kommen gar
    nicht erst in die Schlange — sie sind unbedienbar, nicht offen.
    """
    wo = " OR ".join("a.titel LIKE '%" + e + "'" for e in ENDUNGEN)
    return c.execute(f"""
        SELECT a.id, a.art
          FROM artikel a
          JOIN artikel_suchtext s ON s.artikel_id = a.id
         WHERE coalesce(a.verfallen,0) = 0
           AND ({wo})
           AND length(coalesce(s.text,'')) >= 200
           AND NOT EXISTS (SELECT 1 FROM anreicherung n
                            WHERE n.artikel_id = a.id
                              AND n.auszug LIKE '%"feld": "titel"%')
    """).fetchall()


def _unbedienbar_titel(c) -> list:
    """Dateiname als Titel, aber KEIN Text, aus dem ein Titel zu belegen waere.

    Gemessen 2026-08-15: von 4.776 solchen Artikeln haben 3.071 weniger als
    200 Zeichen Text. Ein Titel dafuer waere reine Erfindung. Sie werden
    trotzdem eingetragen — als `unbedienbar` mit Grund, damit im `stand`
    SICHTBAR ist, dass hier etwas offen bleibt, statt still zu verschwinden.
    """
    wo = " OR ".join("a.titel LIKE '%" + e + "'" for e in ENDUNGEN)
    return c.execute(f"""
        SELECT a.id, a.art
          FROM artikel a
          LEFT JOIN artikel_suchtext s ON s.artikel_id = a.id
         WHERE coalesce(a.verfallen,0) = 0
           AND ({wo})
           AND length(coalesce(s.text,'')) < 200
    """).fetchall()


ARTEN = {"sphaere": _kandidaten_sphaere, "titel": _kandidaten_titel}
UNBEDIENBAR = {"titel": (_unbedienbar_titel,
                         "kein Text vorhanden — ein Titel waere Erfindung")}


def _zitiergrad(c) -> dict:
    """Ersatzmass fuer Reichweite. Siehe Kopf der Datei — es ist ein Ersatz."""
    sem, struct = {}, {}
    p = ",".join("?" * len(SEM_ARTEN))
    for nach, n in c.execute(
            f"SELECT nach, count(*) FROM kante WHERE art IN ({p}) "
            "GROUP BY nach", SEM_ARTEN):
        sem[nach] = n
    for nach, n in c.execute(
            f"SELECT nach, count(*) FROM kante WHERE art NOT IN ({p}) "
            "GROUP BY nach", SEM_ARTEN):
        struct[nach] = n
    return {"sem": sem, "struct": struct}


def wert_von(aid: str, art: str, z: dict) -> float:
    return round(1.0
                 + 3.0 * math.log(1 + z["sem"].get(aid, 0))
                 + 0.5 * math.log(1 + z["struct"].get(aid, 0))
                 + ART_BONUS.get(art, ART_BONUS_SONST), 4)


def cmd_plan(a) -> None:
    """Warteschlange bauen/auffrischen. Idempotent — legt nie doppelt an."""
    c = oeffne()
    tabellen(c)
    z = _zitiergrad(c)
    print(f"Zitiergrad geladen: {len(z['sem'])} Artikel mit semantischen, "
          f"{len(z['struct'])} mit strukturellen Eingangskanten\n")
    for art, hol in ARTEN.items():
        if a.art and a.art != art:
            continue
        kand = hol(c)
        neu = 0
        for r in kand:
            w = wert_von(r["id"], r["art"], z)
            cur = c.execute("SELECT id, zustand FROM wk_aufgabe "
                            "WHERE art=? AND artikel_id=?", (art, r["id"])).fetchone()
            if cur is None:
                c.execute("INSERT INTO wk_aufgabe(art,artikel_id,wert,zustand,"
                          "versuche,letzter_grund,angelegt,geaendert) "
                          "VALUES (?,?,?,?,?,?,?,?)",
                          (art, r["id"], w, "offen", 0, None, jetzt(), jetzt()))
                neu += 1
            elif cur["zustand"] == "offen":
                c.execute("UPDATE wk_aufgabe SET wert=?, geaendert=? WHERE id=?",
                          (w, jetzt(), cur["id"]))
        c.commit()
        offen = c.execute("SELECT count(*) FROM wk_aufgabe WHERE art=? "
                          "AND zustand='offen'", (art,)).fetchone()[0]
        print(f"  {art:10} Kandidaten {len(kand):6}  neu angelegt {neu:6}  "
              f"offen jetzt {offen:6}")
        if art in UNBEDIENBAR:
            hol_u, grund = UNBEDIENBAR[art]
            nu = 0
            for r in hol_u(c):
                if c.execute("SELECT 1 FROM wk_aufgabe WHERE art=? AND artikel_id=?",
                             (art, r["id"])).fetchone() is None:
                    c.execute("INSERT INTO wk_aufgabe(art,artikel_id,wert,zustand,"
                              "versuche,letzter_grund,angelegt,geaendert) "
                              "VALUES (?,?,?,?,?,?,?,?)",
                              (art, r["id"], 0.0, "unbedienbar", 0, grund,
                               jetzt(), jetzt()))
                    nu += 1
            c.commit()
            if nu:
                print(f"  {'':10} davon {nu} als unbedienbar vermerkt — {grund}")
    c.close()


def _last(c, art: str, aid: str) -> dict | None:
    """Holt die Nutzdaten FRISCH — der Zustand kann sich geaendert haben."""
    r = c.execute("SELECT id, art, titel, quelle, projekt, sphaere "
                  "FROM artikel WHERE id=?", (aid,)).fetchone()
    if r is None:
        return None
    if art == "sphaere":
        if r["sphaere"]:
            return {"weg": "hat inzwischen eine Sphaere"}
        return {"system": SYS_SPHAERE, "max": 8,
                "frage": f"projekt={r['projekt']} art={r['art']} "
                         f"titel={(r['titel'] or '')[:140]}",
                "alt": r["titel"] or "", "beleg": ""}
    if art == "titel":
        s = c.execute("SELECT text FROM artikel_suchtext WHERE artikel_id=?",
                      (aid,)).fetchone()
        txt = (s["text"] if s else "") or ""
        if len(txt) < 200:
            return {"weg": "kein Text mehr vorhanden, Titel nur erfindbar"}
        if not (r["titel"] or "").lower().endswith(ENDUNGEN):
            return {"weg": "hat inzwischen einen echten Titel"}
        # ⚠️ Token-Deckel: 6.000/min bei 10 Aufrufen/min = 600 je Aufruf.
        # 1.100 Zeichen sind rund 300 Token.
        auszug = re.sub(r"\s+", " ", txt)[:1100]
        pfad = (r["quelle"] or "").rsplit("/", 3)[-3:]
        return {"system": SYS_TITEL, "max": 40,
                "frage": f"dateiname={r['titel']}\npfad={'/'.join(pfad)}\n"
                         f"text: {auszug}",
                "alt": r["titel"] or "", "beleg": auszug}
    return None


def _pruefe(art: str, text: str, l: dict) -> tuple[bool, str, str]:
    if art == "sphaere":
        return pruefe_sphaere(text)
    return pruefe_titel(text, l["alt"], l["beleg"])


def _protokoll(c, art_lauf, modell, aid, res, ergebnis, grund, text) -> None:
    schreib(c, "INSERT INTO bahn_lauf(zeit,art,bahn,modell,ziel_id,dauer_ms,http,"
               "token_ein,token_aus,ergebnis,pruefung,antwort) "
               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (jetzt(), art_lauf, "groq3", modell, aid,
             round(res.get("ms", 0), 1), res.get("http"),
             res.get("ein"), res.get("aus"), ergebnis, grund,
             (text or "")[:120]))


def ein_stueck(c, u, takt: Takt, trocken: bool, arten: list,
               bevorzugt: str | None = None) -> str:
    """Genau ein Arbeitsstueck — das WERTVOLLSTE offene, nicht das naechste.

    `arten` sind die Arbeitsarten, deren Modell heute noch Kontingent hat.
    Ist das grosse Modell aufgebraucht, ruhen die `titel`-Stuecke und die
    Schleife arbeitet weiter an dem, was das kleine Modell kann.
    """
    if not arten:
        return "leer"
    r = None
    if bevorzugt and bevorzugt in arten:
        r = c.execute("SELECT id, art, artikel_id, wert, versuche FROM wk_aufgabe "
                      "WHERE zustand='offen' AND art=? "
                      "ORDER BY wert DESC, id ASC LIMIT 1", (bevorzugt,)).fetchone()
    if r is None:
        p = ",".join("?" * len(arten))
        r = c.execute(f"SELECT id, art, artikel_id, wert, versuche FROM wk_aufgabe "
                      f"WHERE zustand='offen' AND art IN ({p}) "
                      f"ORDER BY wert DESC, id ASC LIMIT 1", tuple(arten)).fetchone()
    if r is None:
        return "leer"
    modell = MODELL_JE_ART.get(r["art"], MODELL_KLEIN)
    schreib(c, "UPDATE wk_aufgabe SET zustand='laeuft', geaendert=? WHERE id=?",
            (jetzt(), r["id"]))

    l = _last(c, r["art"], r["artikel_id"])
    if l is None or "weg" in l:
        grund = l["weg"] if l else "Artikel nicht mehr vorhanden"
        schreib(c, "UPDATE wk_aufgabe SET zustand='fertig', letzter_grund=?, "
                   "geaendert=? WHERE id=?", (grund, jetzt(), r["id"]))
        return "uebersprungen"          # ⚠️ kostet KEINE Anfrage

    # a) darf — vor JEDEM Aufruf
    erlaubt, wortlaut = darf(1)
    if erlaubt < 1:
        schreib(c, "UPDATE wk_aufgabe SET zustand='offen', letzter_grund=?, "
                   "geaendert=? WHERE id=?", (wortlaut[:200], jetzt(), r["id"]))
        lage(c, "wikiarbeit_zustand", "vom Kontingentbuch gebremst")
        return "gebremst"

    takt.warte(len(l["system"]) // 3 + len(l["frage"]) // 3 + l["max"])
    res = rufen(u[SCHLUESSEL_NAME], modell, l["system"], l["frage"], l["max"])
    takt.bucheTokens((res.get("ein") or 0) + (res.get("aus") or 0))
    buchen(1, f"wikiarbeit/{r['art']}")   # b) buchen — nach dem Aufruf

    if not res["ok"]:
        v = r["versuche"] + 1
        zu = "unbedienbar" if v >= 3 else "offen"
        schreib(c, "UPDATE wk_aufgabe SET zustand=?, versuche=?, letzter_grund=?, "
                   "geaendert=? WHERE id=?",
                (zu, v, f"HTTP {res['http']}: {res.get('fehler','')[:120]}",
                 jetzt(), r["id"]))
        _protokoll(c, "wikiarbeit", modell, r["artikel_id"], res, "fehler",
                   f"HTTP {res['http']}", res.get("fehler", ""))
        if res["http"] == 429:
            w = res.get("warte")
            time.sleep(min(120.0, float(w) if w and str(w).isdigit() else 30.0))
        return "fehler"

    gut, wert, grund = _pruefe(r["art"], res["text"], l)
    if gut and not trocken:
        # ⚠️ NICHT in artikel. Ein Modellvorschlag ist keine Tatsache.
        schreib(c, "INSERT INTO anreicherung(artikel_id,quelle_url,art,auszug,"
                   "geholt_am,hash) VALUES (?,?,?,?,?,?)",
                (r["artikel_id"], f"bahn://groq3/{modell}", "ergaenzt",
                 json.dumps({"feld": r["art"], "vorschlag": wert},
                            ensure_ascii=False), jetzt(), ""))
    # ⚠️ Im Trockenlauf bleibt das Stueck OFFEN. Sonst frisst ein Probelauf
    # still die Warteschlange auf, ohne je etwas zu hinterlegen.
    schreib(c, "UPDATE wk_aufgabe SET zustand=?, versuche=?, letzter_grund=?, "
               "geaendert=? WHERE id=?",
            ("offen" if trocken else ("fertig" if gut else "verworfen"),
             r["versuche"] + 1, grund or None, jetzt(), r["id"]))
    _protokoll(c, "wikiarbeit", modell, r["artikel_id"], res,
               "angenommen" if gut else "verworfen", grund or None, res["text"])
    lage(c, "wikiarbeit_zustand", f"arbeitet an {r['art']}")
    lage(c, "wikiarbeit_letztes_stueck", jetzt())
    if res.get("rest") is not None and res["rest"] < REST_STOPP:
        return "kontingent_ende"
    return "angenommen" if gut else "verworfen"


def cmd_lauf(a) -> None:
    """Der Dauerbetrieb. Laeuft, bis nichts mehr offen ist — und sagt das."""
    signal.signal(signal.SIGTERM, _halt)
    signal.signal(signal.SIGINT, _halt)
    c = oeffne()
    tabellen(c)
    u = umgebung()
    if SCHLUESSEL_NAME not in u:
        print(f"{SCHLUESSEL_NAME} nicht hinterlegt — kein Aufruf moeglich.")
        lage(c, "wikiarbeit_zustand", "kein Schluessel")
        return 1
    # Ein Stueck, das beim Absturz auf 'laeuft' stand, waere sonst fuer immer
    # blockiert — es sieht beschaeftigt aus und ist doch verwaist.
    zurueck = c.execute("SELECT count(*) FROM wk_aufgabe WHERE zustand='laeuft'"
                        ).fetchone()[0]
    if zurueck:
        schreib(c, "UPDATE wk_aufgabe SET zustand='offen', letzter_grund=?, "
                   "geaendert=? WHERE zustand='laeuft'",
                ("beim Neustart verwaist vorgefunden", jetzt()))
        print(f"wikiarbeit: {zurueck} verwaiste Stuecke zurueckgestellt", flush=True)
    takt = Takt()
    zaehler = {"angenommen": 0, "verworfen": 0, "fehler": 0,
               "uebersprungen": 0, "gebremst": 0}
    letztes_lebenszeichen = 0.0
    letzte_planung = time.monotonic()
    grenze = a.anzahl or 10**9
    getan = 0
    zug = 0
    print(f"wikiarbeit: wach. Takt {TAKT_S} s. Modelle je Art "
          + ", ".join(f"{k}->{v}" for k, v in MODELL_JE_ART.items())
          + f". Heute schon {heute_verbraucht(c)} Anfragen.", flush=True)

    while _laeuft and getan < grenze:
        arten = freie_arten(c)
        if not arten:
            v = heute_verbraucht(c)
            lage(c, "wikiarbeit_zustand", f"Tagesdeckel erreicht ({v} Anfragen)")
            if time.monotonic() - letztes_lebenszeichen > LEBENSZEICHEN_S:
                _leerzeile(c, MODELL_KLEIN, f"Tagesdeckel erreicht ({v})")
                letztes_lebenszeichen = time.monotonic()
            _schlaf(60.0)
            continue

        # ⚠️ Reine Wertreihung hat einen Haken, der beim Zusehen auffiel: die
        # wertvollsten Stuecke sind fast alle `sphaere`, also kaeme `titel`
        # tagelang nicht dran — und die 1.000 Anfragen des grossen Modells
        # VERFALLEN jeden Tag ungenutzt. Das kleine Modell hat mit 14.400 weit
        # mehr, als die Schlange verbraucht. Darum bekommt `titel` jeden
        # 14. Zug (14.400 / 1.000 = 14,4): das verderbliche Kontingent wird
        # ueber den Tag verteilt aufgebraucht, ohne die Wertreihung sonst
        # anzutasten.
        zug += 1
        bevorzugt = "titel" if (zug % 14 == 0 and "titel" in arten) else None
        was = ein_stueck(c, u, takt, a.trocken, arten, bevorzugt)
        if was == "leer":
            # Bevor Leerlauf gemeldet wird: nachsehen, ob inzwischen neue
            # Artikel eingetroffen sind. Das kostet keine Anfrage (rund 1 s
            # reine Datenbankarbeit) und verhindert, dass der Arbeiter
            # schlaeft, waehrend Arbeit daliegt.
            if time.monotonic() - letzte_planung > 900:
                letzte_planung = time.monotonic()
                try:
                    cmd_plan(argparse.Namespace(art=None))
                except Exception as e:
                    print(f"Planung fehlgeschlagen: {e}", flush=True)
                if c.execute("SELECT count(*) FROM wk_aufgabe "
                             "WHERE zustand='offen'").fetchone()[0]:
                    continue
            # ⚠️ Leerlauf ist ein gueltiger Zustand — er muss von aussen
            # sichtbar anders aussehen als "gestorben".
            lage(c, "wikiarbeit_zustand", "Leerlauf — nichts Sinnvolles offen")
            lage(c, "wikiarbeit_lebenszeichen", jetzt())
            if time.monotonic() - letztes_lebenszeichen > LEBENSZEICHEN_S:
                _leerzeile(c, MODELL_KLEIN, "nichts Sinnvolles offen")
                letztes_lebenszeichen = time.monotonic()
                print(f"[{jetzt()}] Leerlauf — nichts Sinnvolles offen", flush=True)
            _schlaf(LEERLAUF_SCHLAF_S)
            continue
        if was == "kontingent_ende":
            lage(c, "wikiarbeit_zustand", "Groq meldet Kontingent fast leer")
            _leerzeile(c, MODELL_KLEIN, "Groq-Kopfzeile: Rest unter Schwelle")
            _schlaf(600.0)
            continue
        if was == "gebremst":
            _schlaf(60.0)
            continue
        zaehler[was] = zaehler.get(was, 0) + 1
        lage(c, "wikiarbeit_lebenszeichen", jetzt())
        if was != "uebersprungen":
            getan += 1
        if getan and getan % 25 == 0:
            print(f"[{jetzt()}] {getan} Stuecke: " +
                  " ".join(f"{k}={v}" for k, v in zaehler.items() if v),
                  flush=True)

    lage(c, "wikiarbeit_zustand", "angehalten")
    print("wikiarbeit: angehalten. " +
          " ".join(f"{k}={v}" for k, v in zaehler.items()), flush=True)
    an, ver = zaehler["angenommen"], zaehler["verworfen"]
    if an + ver:
        print(f"Annahmequote {100*an/(an+ver):.1f} %")
    c.close()
    return 0


def _leerzeile(c, modell: str, grund: str) -> None:
    """Ein Lebenszeichen in bahn_lauf — kostet keine Anfrage, zaehlt nicht."""
    schreib(c, "INSERT INTO bahn_lauf(zeit,art,bahn,modell,ergebnis,pruefung) "
               "VALUES (?,?,?,?,?,?)",
            (jetzt(), "wikiarbeit", "groq3", modell, "leerlauf", grund[:160]))


def _schlaf(s: float) -> None:
    ende = time.monotonic() + s
    while _laeuft and time.monotonic() < ende:
        time.sleep(min(0.5, ende - time.monotonic()))


# ── A/B: taugt das kleine Modell? ──────────────────────────────────────

def cmd_ab(a) -> None:
    """Dieselben Stuecke durch beide Modelle. Trocken — nichts wird behalten.

    ⚠️ Das grosse Modell hat nur 1.000 Anfragen/Tag. Es darf nur benutzt
    werden, wenn das kleine hier MESSBAR durchfaellt.
    """
    c = oeffne()
    tabellen(c)
    u = umgebung()
    rows = c.execute("SELECT artikel_id FROM wk_aufgabe WHERE art=? "
                     "AND zustand IN ('offen','fertig','verworfen') "
                     "ORDER BY wert DESC, id ASC LIMIT ?",
                     (a.art, a.anzahl)).fetchall()
    print(f"A/B auf {len(rows)} Stuecken der Art {a.art}\n")
    takt = Takt()
    erg = {}
    for modell in (MODELL_KLEIN, MODELL_GROSS):
        an = ver = fe = 0
        gruende = {}
        t0 = time.time()
        for r in rows:
            l = _last(c, a.art, r["artikel_id"])
            if l is None or "weg" in l:
                continue
            erlaubt, _ = darf(1)
            if erlaubt < 1:
                print("  Kontingentbuch bremst — A/B abgebrochen")
                break
            takt.warte(len(l["frage"]) // 3 + l["max"])
            res = rufen(u[SCHLUESSEL_NAME], modell, l["system"], l["frage"], l["max"])
            takt.bucheTokens((res.get("ein") or 0) + (res.get("aus") or 0))
            buchen(1, f"wikiarbeit-ab/{a.art}")
            if not res["ok"]:
                fe += 1
                _protokoll(c, "wikiarbeit_ab", modell, r["artikel_id"], res,
                           "fehler", f"HTTP {res['http']}", res.get("fehler", ""))
                continue
            gut, wert, grund = _pruefe(a.art, res["text"], l)
            if gut:
                an += 1
            else:
                ver += 1
                gruende[grund] = gruende.get(grund, 0) + 1
            _protokoll(c, "wikiarbeit_ab", modell, r["artikel_id"], res,
                       "angenommen" if gut else "verworfen", grund or None,
                       res["text"])
        erg[modell] = (an, ver, fe, gruende, time.time() - t0)
        q = 100 * an / (an + ver) if an + ver else 0
        print(f"{modell:26} angenommen {an:3}  verworfen {ver:3}  Fehler {fe:3}"
              f"  Quote {q:5.1f} %  {time.time()-t0:.0f} s")
        for g, n in sorted(gruende.items(), key=lambda x: -x[1])[:5]:
            print(f"    {n:3}x {str(g)[:70]}")
    k, g = erg.get(MODELL_KLEIN), erg.get(MODELL_GROSS)
    if k and g:
        qk = 100 * k[0] / (k[0] + k[1]) if k[0] + k[1] else 0
        qg = 100 * g[0] / (g[0] + g[1]) if g[0] + g[1] else 0
        print(f"\nUnterschied {qg-qk:+.1f} Prozentpunkte zugunsten "
              f"{'des grossen' if qg > qk else 'des kleinen'} Modells.")
        print("Entscheidung: das grosse Modell wird NUR eingesetzt, wenn es "
              "hier deutlich besser ist — es hat 1.000 statt 14.400 "
              "Anfragen/Tag.")
    c.close()


# ── STAND ──────────────────────────────────────────────────────────────

def cmd_treffer(a) -> None:
    """⚠️ Annahmequote misst die FORM, nicht die WAHRHEIT.

    "frank_v0_1" ist ein formal gueltiges Wort, auch wenn der Artikel zu
    seimensch gehoert. Deshalb dieselbe Frage an Artikel, deren Sphaere
    BEREITS feststeht (2.425 Stueck, gesetzt aus der Quelle, nicht von einem
    Modell) — und dann verglichen. Das ist die einzige Zahl, die etwas ueber
    die Brauchbarkeit sagt. Nichts wird dabei geschrieben.
    """
    c = oeffne()
    tabellen(c)
    u = umgebung()
    rows = c.execute(
        "SELECT id, art, titel, projekt, sphaere FROM artikel "
        "WHERE sphaere IS NOT NULL AND sphaere <> '' AND titel IS NOT NULL "
        "AND length(titel) >= 10 ORDER BY random() LIMIT ?", (a.anzahl,)).fetchall()
    print(f"Trefferprobe: {len(rows)} Artikel mit bereits bekannter Sphaere, "
          f"Modell {a.modell}\n")
    takt = Takt()
    treffer = daneben = unklar = fehler = 0
    verwechselt = {}
    for r in rows:
        erlaubt, _ = darf(1)
        if erlaubt < 1:
            print("  Kontingentbuch bremst — Probe abgebrochen")
            break
        frage = (f"projekt={r['projekt']} art={r['art']} "
                 f"titel={(r['titel'] or '')[:140]}")
        takt.warte(len(frage) // 3 + 8)
        res = rufen(u[SCHLUESSEL_NAME], a.modell, SYS_SPHAERE, frage, 8)
        takt.bucheTokens((res.get("ein") or 0) + (res.get("aus") or 0))
        buchen(1, "wikiarbeit-treffer/sphaere")
        if not res["ok"]:
            fehler += 1
            continue
        gut, wert, _ = pruefe_sphaere(res["text"])
        if not gut:
            unklar += 1
        elif wert == r["sphaere"]:
            treffer += 1
        else:
            daneben += 1
            k = f"{r['sphaere']} -> {wert}"
            verwechselt[k] = verwechselt.get(k, 0) + 1
        _protokoll(c, "wikiarbeit_treffer", a.modell, r["id"], res,
                   "angenommen" if (gut and wert == r["sphaere"]) else "verworfen",
                   f"wahr={r['sphaere']}", res["text"])
    gewertet = treffer + daneben
    print(f"Treffer {treffer} · daneben {daneben} · keine Antwort verwertbar "
          f"{unklar} · Fehler {fehler}")
    if gewertet:
        print(f"TREFFERQUOTE {100*treffer/gewertet:.1f} % "
              f"(von {gewertet} verwertbaren Antworten)")
    if verwechselt:
        print("haeufigste Verwechslungen (wahr -> geraten):")
        for k, n in sorted(verwechselt.items(), key=lambda x: -x[1])[:6]:
            print(f"  {n:3}x {k}")
    c.close()


def cmd_stand(a) -> None:
    c = oeffne()
    tabellen(c)
    ta = tagesanfang()
    print("WARTESCHLANGE (wk_aufgabe)")
    print(f"  {'Art':10} {'offen':>7} {'fertig':>7} {'verworfen':>10} "
          f"{'unbedienbar':>12} {'laeuft':>7}")
    for art in ARTEN:
        z = {k: 0 for k in ("offen", "fertig", "verworfen", "unbedienbar", "laeuft")}
        for k, n in c.execute("SELECT zustand, count(*) FROM wk_aufgabe "
                              "WHERE art=? GROUP BY zustand", (art,)):
            z[k] = n
        print(f"  {art:10} {z['offen']:7} {z['fertig']:7} {z['verworfen']:10} "
              f"{z['unbedienbar']:12} {z['laeuft']:7}")

    print("\nHEUTE (seit " + ta[:10] + ", UTC)")
    for art, ergebnis, n in c.execute(
            "SELECT art, ergebnis, count(*) FROM bahn_lauf "
            "WHERE art IN ('wikiarbeit','wikiarbeit_ab') AND zeit >= ? "
            "GROUP BY art, ergebnis ORDER BY art, ergebnis", (ta,)):
        print(f"  {art:15} {ergebnis:12} {n}")
    for m, deckel in DECKEL_JE_MODELL.items():
        v = heute_verbraucht(c, m)
        arten = [a for a, mm in MODELL_JE_ART.items() if mm == m]
        print(f"  {m:26} {v:5} von {deckel} Anfragen "
              f"({100*v/deckel:.1f} %) — Rest {deckel-v}  [{', '.join(arten)}]")
    print(f"  zusammen: {heute_verbraucht(c)} Anfragen auf GROQ3_API_KEY")
    tk = c.execute("SELECT coalesce(sum(token_ein),0), coalesce(sum(token_aus),0) "
                   "FROM bahn_lauf WHERE art LIKE 'wikiarbeit%' AND zeit >= ?",
                   (ta,)).fetchone()
    print(f"  Token: ein {tk[0]} · aus {tk[1]}")

    print("\nVERWERFUNGSGRUENDE (heute)")
    ge = c.execute("SELECT pruefung, count(*) FROM bahn_lauf "
                   "WHERE art='wikiarbeit' AND ergebnis='verworfen' AND zeit >= ? "
                   "GROUP BY pruefung ORDER BY 2 DESC LIMIT 8", (ta,)).fetchall()
    if not ge:
        print("  keine — ⚠️ ein Arbeiter, der NIE etwas verwirft, ist kaputt, "
              "nicht perfekt.")
    for g, n in ge:
        print(f"  {n:5}x {str(g)[:78]}")

    print("\nZUSTAND")
    for k, w, z in c.execute("SELECT schluessel, wert, zeit FROM bahn_lage "
                             "WHERE schluessel LIKE 'wikiarbeit%' "
                             "ORDER BY schluessel"):
        print(f"  {k:28} {w}   ({z})")
    letzt = c.execute("SELECT zeit, ergebnis, pruefung FROM bahn_lauf "
                      "WHERE art='wikiarbeit' ORDER BY id DESC LIMIT 1").fetchone()
    if letzt:
        alt = (datetime.now(timezone.utc)
               - datetime.fromisoformat(letzt["zeit"])).total_seconds()
        print(f"  letzte Zeile vor {alt:.0f} s: {letzt['ergebnis']} "
              f"{(letzt['pruefung'] or '')[:50]}")
        if alt > 900:
            print("  ⚠️ aelter als 15 min — der Dienst schreibt nicht mehr. "
                  "Das ist NICHT Leerlauf, Leerlauf schreibt alle 5 min.")
    else:
        print("  noch nie gelaufen")
    c.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="b", required=True)

    q = s.add_parser("plan", help="Warteschlange bauen/auffrischen (idempotent)")
    q.add_argument("--art", default=None, choices=list(ARTEN))

    q = s.add_parser("lauf", help="Dauerbetrieb")
    q.add_argument("--anzahl", type=int, default=0,
                   help="0 = endlos; sonst nach N Stuecken beenden")
    q.add_argument("--trocken", action="store_true",
                   help="prueft, schreibt aber keine anreicherung")

    q = s.add_parser("ab", help="A/B klein gegen gross, trocken")
    q.add_argument("--art", default="titel", choices=list(ARTEN))
    q.add_argument("--anzahl", type=int, default=50)

    q = s.add_parser("treffer", help="Trefferquote gegen bekannte Sphaeren, trocken")
    q.add_argument("--anzahl", type=int, default=60)
    q.add_argument("--modell", default=MODELL_KLEIN)

    s.add_parser("stand", help="was ist offen, was lief, was wurde verworfen")

    a = p.parse_args()
    return {"plan": cmd_plan, "lauf": cmd_lauf, "ab": cmd_ab,
            "treffer": cmd_treffer, "stand": cmd_stand}[a.b](a) or 0


if __name__ == "__main__":
    sys.exit(main())
