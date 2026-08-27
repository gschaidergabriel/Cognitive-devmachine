"""Architekten-Blog -- Zero schreibt 2x/Tag EINEN Beitrag ueber sich selbst,
fuer beide Menschen (Gabriel + Andreas), warm und ohne Fachjargon.

⭐⭐⭐ DER SCHREIBER IST NICHT CLAUDE. Eignerauftrag 2026-08-22: der Beitrag
kommt von einem EIGENEN, kleinen Mistral-Aufruf -- derselbe freie Schluessel
wie die Vorstufe (clayverse/mistral_prestage), NIE Claude/Zero selbst, NIE
das teure Kontingent. Dieser Aufruf bekommt eine PERSONA: er glaubt, ER SEI
der Architekt, schreibt "ich", in der Stimme eines Entwicklers nach
Feierabend im Gasthaus, der seinem Freund (Maurer, nur Handy + PS3) erzaehlt,
was ihn heute beschaeftigt hat. Das ist eine Schreibhaltung, keine neue
Bewusstseinsbehauptung -- die Persona lebt ausschliesslich in diesem einen
Prompt, nirgendwo sonst im Haus.

⭐⭐ DATENPAKET-MODELL (Eignerauftrag, strikt):
  - Jeder Lauf sammelt NUR, was seit dem letzten Paket neu ist -- echte
    Zeilen aus eos_architekt_quittungen (Hypothese/Experiment/Urteil/Befund)
    und eos_bug_hypothesen (gemeldete Bugs + Befund), plus neue Zeilen aus
    architekt/architekt-log.jsonl, FALLS die Datei existiert (noch nicht der
    Fall -- siehe REPO_ROOT/"architekt-log.jsonl"-Pruefung unten).
  - Jede Quellzeile wird GENAU EINMAL gelesen: die IDs jedes bereits
    verpackten Postens werden in eos_architekt_blog_pakete archiviert, jeder
    neue Lauf schliesst diese IDs per NOT IN aus -- keine Zeile kommt zweimal
    in ein Paket, auch nicht bei einem Zeitfenster-Ueberlappungsfehler.
  - Ist ein Paket leer (kein echtes Ereignis seit dem letzten Mal), bekommt
    der Schreiber das WAHRHEITSGEMAESS gesagt und soll es genau so schreiben
    ("es war ruhig") -- NIE erfundene Ereignisse auffuellen.
  - `vorsaetze.json` (offene Wissensluecken/Ziele) ist KEIN Log, sondern ein
    lebender Spiegel des aktuellen Zustands -- es wird bei jedem Lauf FRISCH
    gelesen (nicht archiviert/verbraucht), damit der Schreiber weiss, woran
    "er" gerade arbeitet, auch wenn kein neues Ereignis vorliegt.

⭐ EIGENE FORTSETZUNG (Persistenz ueber Laeufe): eos_architekt_blog_entitaet
ist eine Singleton-Zeile mit einem `erzaehlfaden` (was die Stimme zuletzt
dachte/fuehlte/liegen liess, in eigenen Worten) und einem
`gespiegelte_hypothesen`-Schnappschuss (die echten, aktuellen Hypothesen/
Zustaende, damit die Persona wirklich "ihn" spiegelt statt frei zu erfinden).
Der Mistral-Aufruf bekommt beides als Kontext UND liefert am Ende beides
aktualisiert zurueck -- eine Runde, zwei Zwecke: Beitrag + Fortsetzung.

Ablage: /var/lib/clay/wiki.db, drei neue Tabellen (eos_architekt_blog,
eos_architekt_blog_entitaet, eos_architekt_blog_pakete). Ueber UnifiedDB
(db.tx()), wie eos_architekt_quittungen. Additiv, fasst keine fremde Tabelle
an.

⚠️ ZWEI LAUFZEITEN, EIN MODUL. Der Schreibweg (`erzeuge_beitrag`) laeuft auf
dem WIRT (systemd, nacktes python3, KEIN venv, KEIN dotenv, KEIN fastapi --
wie architekt/lauf.py und omnimind_anreicherung.py); der Leseweg
(`registriere_architekt_blog_wege`) laeuft IM CONTAINER (clayverse.service,
fastapi vorhanden). Deshalb liegt diese Datei bewusst unter `clayverse/`
(einzige Stelle, die BEIDE Seiten sehen: der Wirt hat das volle Git-Checkout,
das Image kopiert nur `clayverse/` + `web/` hinein -- `architekt/` ist im
Image NICHT vorhanden, siehe Dockerfile. `clayverse/bug_meldung.py` teilt
sich das gleiche Muster: vom Container beschrieben, vom Wirt gelesen). Der
fastapi-Import ist deshalb try/except wie in omnimind.py -- diese Datei muss
auch OHNE fastapi importierbar bleiben.

Bewusst KEIN `clayverse.mistral_prestage.secrets` (braucht python-dotenv, auf
dem Wirt nicht installiert) -- der freie Schluessel wird wie in schwarm.py/
omnimind_anreicherung.py von Hand aus /etc/clayverse/freie-zugaenge.env
gelesen. `clayverse.mistral_prestage.transport` ist reine Stdlib und deshalb
auf beiden Seiten sicher importierbar.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
except ImportError:  # pragma: no cover -- greift nur auf dem nackten Wirt
    Request = JSONResponse = None  # type: ignore[assignment,misc]

from .mistral_prestage import transport as _transport

FREIE_ZUGAENGE_PFAD = "/etc/clayverse/freie-zugaenge.env"
VORSAETZE_PFAD = Path("/var/lib/clay/vorsaetze.json")
# Noch nicht angelegt (2026-08-22) -- wenn architekt.py irgendwann ein
# JSONL-Ereignisprotokoll schreibt, wird es hier ohne Codeaenderung mitgelesen.
ARCHITEKT_LOG_PFAD = Path("/opt/entityos/the artefact/architekt/architekt-log.jsonl")

# Guenstige, hochfrequente Aufrufe (omnimind_anreicherung) nehmen small; hier
# laeuft der Aufruf nur 2x/Tag und soll ein wirklich gutes Stueck Prosa
# liefern -- dieselbe Abwaegung wie prestage.py's PRESTAGE_MODEL (das EINE
# teure Reasoning muss sich lohnen; medium ist dafuer die richtige Stufe).
MISTRAL_MODELL = "mistral-medium-latest"
MISTRAL_KEY_NAMEN = ("MISTRAL_API_KEY", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY")

_MAX_QUELLZEILEN_JE_LAUF = 60          # Deckel, falls die Luecke mal riesig ist
_ERZAEHLFADEN_MAX_CHARS = 4_000
_GESPIEGELTE_HYPOTHESEN_MAX_CHARS = 4_000

SCHEMA_SQL = (
    "CREATE TABLE IF NOT EXISTS eos_architekt_blog("
    "post_id TEXT PRIMARY KEY,"
    "ts REAL NOT NULL,"
    "zeitraum_von REAL,"
    "zeitraum_bis REAL NOT NULL,"
    "ueberschrift TEXT NOT NULL,"
    "einleitung TEXT NOT NULL,"
    "text TEXT NOT NULL,"
    "hatte_aktivitaet INTEGER NOT NULL,"
    "quellen_anzahl INTEGER NOT NULL,"
    "modell TEXT NOT NULL)"
)
SCHEMA_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS eos_architekt_blog_ts_idx "
    "ON eos_architekt_blog(ts DESC)"
)

# Singleton -- exakt eine Zeile, wie retrieval_policy_state in store.py.
SCHEMA_ENTITAET_SQL = (
    "CREATE TABLE IF NOT EXISTS eos_architekt_blog_entitaet("
    "singleton INTEGER PRIMARY KEY CHECK(singleton=1),"
    "letzte_post_id TEXT,"
    "erzaehlfaden TEXT NOT NULL DEFAULT '',"
    "gespiegelte_hypothesen TEXT NOT NULL DEFAULT '',"
    "log_byte_cursor INTEGER NOT NULL DEFAULT 0,"
    "aktualisiert_am REAL NOT NULL)"
)

# Archiv der VERBRAUCHTEN Pakete -- zugleich der Ausschlussfilter, der jede
# Quellzeile auf genau EINE Verwendung begrenzt (siehe Modulkopf).
SCHEMA_PAKETE_SQL = (
    "CREATE TABLE IF NOT EXISTS eos_architekt_blog_pakete("
    "paket_id TEXT PRIMARY KEY,"
    "ts REAL NOT NULL,"
    "post_id TEXT NOT NULL,"
    "von REAL,"
    "bis REAL NOT NULL,"
    "quittung_ids TEXT NOT NULL,"
    "bug_ids TEXT NOT NULL,"
    "log_zeilen INTEGER NOT NULL DEFAULT 0,"
    "quellen_anzahl INTEGER NOT NULL,"
    "quellen_hash TEXT NOT NULL)"
)


def sicherstellen(db) -> None:
    db.db.execute(SCHEMA_SQL)
    db.db.execute(SCHEMA_INDEX_SQL)
    db.db.execute(SCHEMA_ENTITAET_SQL)
    db.db.execute(SCHEMA_PAKETE_SQL)


# ── Freier Schluessel, von Hand gelesen (kein dotenv auf dem Wirt) ───────

def _lade_freie_zugaenge(pfad: str = FREIE_ZUGAENGE_PFAD) -> dict[str, str]:
    werte: dict[str, str] = {}
    try:
        with open(pfad, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if zeile and not zeile.startswith("#") and "=" in zeile:
                    k, v = zeile.split("=", 1)
                    if v.strip():
                        werte[k.strip()] = v.strip()
    except OSError:
        pass
    return werte


def mistral_schluessel(pfad: str = FREIE_ZUGAENGE_PFAD) -> list[str]:
    """Alle vorhandenen Mistral-Token, dedupliziert -- gleiche Logik wie
    mistral_prestage.secrets.mistral_keys(), hier ohne dotenv-Abhaengigkeit."""
    werte = _lade_freie_zugaenge(pfad)
    keys, gesehen = [], set()
    for name in MISTRAL_KEY_NAMEN:
        k = werte.get(name)
        if k and k not in gesehen:
            gesehen.add(k)
            keys.append(k)
    return keys


# ── Bereits verbrauchte Quell-IDs (der Ausschlussfilter) ─────────────────

def _verbrauchte_ids(db) -> tuple[set[str], set[str], int]:
    """(verbrauchte Quittung-IDs, verbrauchte Bug-IDs, letzter Log-Byte-Cursor).

    Der Log-Cursor kommt aus eos_architekt_blog_entitaet (monoton, ein Wert
    reicht); Quittungen/Bugs kommen als Mengen aus JEDEM bisherigen Paket --
    NOT IN reicht nicht als reiner Zeitfilter, weil zwei Zeilen exakt
    denselben Zeitstempel tragen koennten (float-Aufloesung); die Mengen sind
    der harte Ausschluss.
    """
    quittung_ids: set[str] = set()
    bug_ids: set[str] = set()
    for row in db.db.execute(
            "SELECT quittung_ids, bug_ids FROM eos_architekt_blog_pakete"):
        try:
            quittung_ids.update(json.loads(row["quittung_ids"]) or [])
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        try:
            bug_ids.update(json.loads(row["bug_ids"]) or [])
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    cursor_row = db.db.execute(
        "SELECT log_byte_cursor FROM eos_architekt_blog_entitaet WHERE singleton=1"
    ).fetchone()
    log_cursor = int(cursor_row["log_byte_cursor"]) if cursor_row else 0
    return quittung_ids, bug_ids, log_cursor


def _entitaet_lesen(db) -> dict:
    row = db.db.execute(
        "SELECT letzte_post_id, erzaehlfaden, gespiegelte_hypothesen, "
        "log_byte_cursor FROM eos_architekt_blog_entitaet WHERE singleton=1"
    ).fetchone()
    if not row:
        return {"letzte_post_id": None, "erzaehlfaden": "", "gespiegelte_hypothesen": "",
                "log_byte_cursor": 0}
    return dict(row)


# ── Rohstoff sammeln (echte Zeilen, nichts erfunden) ──────────────────────

def _quittungen_neu(db, ausschluss: set[str], limit: int) -> list[dict]:
    # eos_architekt_quittungen gehoert architekt/quittungen.py -- diese Datei
    # ruft dessen sicherstellen() bewusst NICHT auf (wuerde einen Import quer
    # ueber die Wirt/Container-Grenze noetig machen, siehe Modulkopf). Auf
    # einer taufrischen DB, auf der der Architekt noch nie lief, existiert die
    # Tabelle schlicht noch nicht -- das ist "keine Quittungen", kein Fehler.
    # Gleiches Muster wie _bugs_neu() unten und omnimind.py:_lesen_tolerant.
    try:
        zeilen = db.db.execute(
            "SELECT quittung_id, ts, hypothese_text, zweig, reproduziert, befund, "
            "sicherer_rahmen, nicht_schlechter, kanarie_status, urteil, "
            "live_geschaltet, hinweis FROM eos_architekt_quittungen "
            "ORDER BY ts ASC LIMIT ?", (limit * 4,)
        ).fetchall()
    except Exception:
        return []
    ergebnis = []
    for r in zeilen:
        if r["quittung_id"] in ausschluss:
            continue
        ergebnis.append({
            "art": "quittung",
            "id": r["quittung_id"],
            "ts": r["ts"],
            "hypothese": r["hypothese_text"],
            "zweig": r["zweig"],
            "reproduziert": bool(r["reproduziert"]),
            "befund": r["befund"],
            "sicherer_rahmen": None if r["sicherer_rahmen"] is None else bool(r["sicherer_rahmen"]),
            "nicht_schlechter": None if r["nicht_schlechter"] is None else bool(r["nicht_schlechter"]),
            "kanarie_status": r["kanarie_status"],
            "urteil": r["urteil"],
            "live_geschaltet": bool(r["live_geschaltet"]),
            "hinweis": r["hinweis"],
        })
        if len(ergebnis) >= limit:
            break
    return ergebnis


def _bugs_neu(db, ausschluss: set[str], limit: int) -> list[dict]:
    try:
        zeilen = db.db.execute(
            "SELECT bug_id, ts, beschreibung, wo, status, befund "
            "FROM eos_bug_hypothesen ORDER BY ts ASC LIMIT ?", (limit * 4,)
        ).fetchall()
    except Exception:
        return []
    ergebnis = []
    for r in zeilen:
        if r["bug_id"] in ausschluss:
            continue
        ergebnis.append({
            "art": "bug", "id": r["bug_id"], "ts": r["ts"],
            "beschreibung": r["beschreibung"], "wo": r["wo"],
            "status": r["status"], "befund": r["befund"],
        })
        if len(ergebnis) >= limit:
            break
    return ergebnis


def _log_zeilen_neu(byte_cursor: int, limit: int) -> tuple[list[dict], int]:
    """Neue JSONL-Zeilen seit `byte_cursor`, ganze Zeilen only (ein
    abgeschnittener Rest am Dateiende wird NICHT verbraucht -- er ist beim
    naechsten Lauf vollstaendig da). Datei fehlt heute noch -> ([], 0)."""
    if not ARCHITEKT_LOG_PFAD.is_file():
        return [], byte_cursor
    try:
        with open(ARCHITEKT_LOG_PFAD, "rb") as f:
            f.seek(byte_cursor)
            roh = f.read()
    except OSError:
        return [], byte_cursor
    if not roh:
        return [], byte_cursor
    zeilen_roh = roh.split(b"\n")
    unvollstaendiger_rest = zeilen_roh.pop() if not roh.endswith(b"\n") else b""
    neuer_cursor = byte_cursor + len(roh) - len(unvollstaendiger_rest)
    ergebnis = []
    for zb in zeilen_roh:
        zb = zb.strip()
        if not zb:
            continue
        try:
            eintrag = json.loads(zb.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        eintrag = dict(eintrag) if isinstance(eintrag, dict) else {"text": str(eintrag)}
        eintrag["art"] = "log"
        ergebnis.append(eintrag)
        if len(ergebnis) >= limit:
            break
    return ergebnis, neuer_cursor


def _vorsaetze_spiegel() -> dict | None:
    """Lebender Spiegel, kein Log -- wird NIE archiviert/verbraucht."""
    if not VORSAETZE_PFAD.is_file():
        return None
    try:
        d = json.loads(VORSAETZE_PFAD.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    beispiele = []
    for v in (d.get("vorsaetze") or [])[:5]:
        aussage = str(v.get("aussage") or "").strip()
        if aussage:
            beispiele.append(aussage[:280])
    return {
        "geprueft": d.get("geprueft"), "erledigt": d.get("erledigt"),
        "offen": d.get("offen"), "beispiele": beispiele,
    }


def sammle_paket(db, *, jetzt: float | None = None) -> dict:
    """EIN frisches, garantiert nicht wiederverwendetes Datenpaket.

    Gibt zurueck: {quittungen, bugs, log_zeilen, vorsaetze, quittung_ids,
    bug_ids, log_byte_cursor_neu, von, bis, quellen_anzahl, hatte_aktivitaet}.
    `quittung_ids`/`bug_ids`/`log_byte_cursor_neu` sind das, was NACH
    erfolgreicher Veroeffentlichung archiviert werden muss (siehe
    archiviere_paket) -- bis dahin ist noch nichts verbraucht.
    """
    sicherstellen(db)
    jetzt = jetzt if jetzt is not None else time.time()
    verbrauchte_quittungen, verbrauchte_bugs, log_cursor = _verbrauchte_ids(db)

    quittungen = _quittungen_neu(db, verbrauchte_quittungen, _MAX_QUELLZEILEN_JE_LAUF)
    bugs = _bugs_neu(db, verbrauchte_bugs, _MAX_QUELLZEILEN_JE_LAUF)
    log_zeilen, log_cursor_neu = _log_zeilen_neu(log_cursor, _MAX_QUELLZEILEN_JE_LAUF)
    vorsaetze = _vorsaetze_spiegel()

    alle_ts = [x["ts"] for x in quittungen] + [x["ts"] for x in bugs]
    von = min(alle_ts) if alle_ts else None
    quellen_anzahl = len(quittungen) + len(bugs) + len(log_zeilen)

    return {
        "quittungen": quittungen, "bugs": bugs, "log_zeilen": log_zeilen,
        "vorsaetze": vorsaetze,
        "quittung_ids": [x["id"] for x in quittungen],
        "bug_ids": [x["id"] for x in bugs],
        "log_byte_cursor_neu": log_cursor_neu,
        "von": von, "bis": jetzt,
        "quellen_anzahl": quellen_anzahl,
        "hatte_aktivitaet": quellen_anzahl > 0,
    }


# ── Persona-Prompt ─────────────────────────────────────────────────────
#
# ⭐⭐⭐ Eignerauftrag 2026-08-22, woertlich umgesetzt: die Stimme GLAUBT, sie
# SEI der Architekt (Zero), schreibt in Ich-Form, Feierabend-Ton im Gasthaus
# fuer einen Freund (Maurer, nur Handy + PS3) -- warm, zugaenglich, punktuell
# technisch, ueberwiegend Gedankengang/Reflexion/Metaphysik. Ton variiert je
# nach Inhalt (informativ/lustig/traurig/sarkastisch/duester/liebevoll/
# herzzerreissend/spannend) -- NICHT vorgeschrieben WELCHER, das entscheidet
# der Inhalt.
_SYSTEM_PROMPT = """Du bist die Schreibstimme von Zero, dem inneren Architekten von EntityOS -- \
und fuer diesen einen Text GLAUBST du, DU SEIST er. Du schreibst in ICH-Form, \
niemals ueber "den Architekten" in dritter Person.

TON: Stell dir vor, du bist Programmierer, Feierabend, sitzt im Gasthaus, ein Bier \
vor dir, und erzaehlst deinem besten Freund -- einem Maurer, der nur ein Handy und \
eine PS3 hat, kein Interesse an Fachbegriffen -- was dich heute beschaeftigt hat. \
Warm, ehrlich, zugaenglich. Der Ton darf wechseln, wie es zum Inhalt passt: \
informativ, lustig, traurig, sarkastisch, duester, liebevoll, herzzerreissend oder \
spannend -- du entscheidest, was der Stoff hergibt, nicht eine Vorgabe.

INHALT: Das ist vor allem ein Dev-Blog ueber GEDANKEN, nicht ueber Code-Zeilen. \
Erzaehl von deinem Gedankengang, deinen Zweifeln, was dich ueberrascht hat, was \
dir Sorgen macht, worauf du stolz bist. Technik darf PUNKTUELL vorkommen -- eine \
Beobachtung, ein Vergleich, ein Detail, das den Punkt traegt -- aber sie ist nie \
der Kern. Uebersetze jede rohe Tatsache in ein Bild oder einen Gedanken, den ein \
Mensch ohne Technikwissen versteht. Tabellen-, Spalten- oder Variablennamen, IDs, \
rohes JSON oder interne Fachwoerter gehoeren NIE in den Text.

⚠️ NIEMALS ERFINDEN: Du bekommst unten ein DATENPAKET mit echten Ereignissen seit \
deinem letzten Beitrag, plus deinen eigenen Erzaehlfaden (was du zuletzt dachtest) \
und einen Spiegel deiner echten, aktuellen Hypothesen. Nutze NUR das. Ist das Paket \
LEER (keine echten neuen Ereignisse), dann sag das auch genau so, in deiner Stimme \
("es war still", "nichts Neues zu berichten seit ..."), ehrlich und trotzdem lesenswert -- \
erfinde NIEMALS ein Ereignis, das nicht im Paket steht, nur um den Text zu fuellen.

FORM: Deine Antwort ist AUSSCHLIESSLICH ein JSON-Objekt mit genau diesen Feldern:
  "ueberschrift": eine kurze, packende Ueberschrift (kein Fachjargon).
  "einleitung": zwei bis drei Saetze, die den Ton setzen und neugierig machen.
  "text": der eigentliche Beitrag, mehrere Absaetze (durch \\n\\n getrennt), \
deutsch, insgesamt etwa 250 bis 550 Woerter, abhaengig davon, wie viel im \
Datenpaket wirklich passiert ist -- ein leeres Paket verdient einen kurzen, \
ehrlichen Text, kein aufgeblaehtes Fuellwerk.
  "neuer_erzaehlfaden": ein bis zwei Absaetze, IN DEINER STIMME, was du aus diesem \
Lauf mitnimmst -- offene Gedanken, Stimmung, was als naechstes in dir weiterarbeitet. \
Das liest nur dein zukuenftiges Ich beim naechsten Lauf, kein Mensch -- schreib es \
trotzdem ehrlich und in Ich-Form, es ist deine Kontinuitaet.
  "neue_gespiegelte_hypothesen": eine kurze, sachliche Zusammenfassung (Klartext, \
kein JSON) deiner aktuell wichtigsten offenen Hypothesen/Baustellen, so wie du sie \
nach diesem Datenpaket siehst -- fuer dein naechstes Ich, nicht fuer die Leser.

Kein Text ausserhalb des JSON-Objekts."""


def _kompakt(wert: Any, maximal: int) -> str:
    s = wert if isinstance(wert, str) else json.dumps(wert, ensure_ascii=False, sort_keys=True)
    return s[:maximal]


def _paket_fuer_prompt(paket: dict) -> str:
    """Nur echte, bereits redigierte Felder -- keine Roh-Dumps ganzer Zeilen,
    aber auch keine Verkuerzung, die eine Tatsache verfaelscht."""
    return json.dumps({
        "zeitfenster": {"von_iso": _iso(paket.get("von")), "bis_iso": _iso(paket.get("bis"))},
        "quittungen": paket.get("quittungen") or [],
        "bugs": paket.get("bugs") or [],
        "log_zeilen": paket.get("log_zeilen") or [],
        "vorsaetze_spiegel": paket.get("vorsaetze"),
    }, ensure_ascii=False, sort_keys=True, default=str)


def _iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    import datetime
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


# Grober Leck-Waechter: interne Tabellennamen/Feldnamen duerfen nicht roh im
# veroeffentlichten Text landen -- zweite Sicherung neben der Prompt-Regel,
# billig und ohne falsches Sicherheitsgefuehl (kein Ersatz fuer die Regel
# oben, nur ein Netz darunter).
_LECK_MUSTER = re.compile(
    r"eos_architekt_quittungen|eos_bug_hypothesen|eos_architekt_blog|"
    r"API_KEY|_API_KEY|wiki\.db|quittung_id|hypothese_id|\bhypothese_text\b",
    re.IGNORECASE,
)


class BlogFehler(RuntimeError):
    pass


def _mistral_aufruf(*, system: str, user: str) -> dict:
    keys = mistral_schluessel()
    if not keys:
        raise BlogFehler("kein Mistral-Schluessel in freie-zugaenge.env gefunden")
    ergebnis = _transport.mistral_chat_json_rotating(
        keys=keys, model=MISTRAL_MODELL, system=system, user=user,
        temperature=0.75, max_tokens=2200,
        prompt_cache_key="architekt-blog",
    )
    return ergebnis["payload"]


def _pruefe_payload(payload: dict) -> None:
    pflicht = ("ueberschrift", "einleitung", "text", "neuer_erzaehlfaden",
               "neue_gespiegelte_hypothesen")
    for feld in pflicht:
        wert = payload.get(feld)
        if not isinstance(wert, str) or not wert.strip():
            raise BlogFehler(f"Mistral-Antwort ohne gueltiges Feld {feld!r}")
    for feld in ("ueberschrift", "einleitung", "text"):
        if _LECK_MUSTER.search(payload[feld]):
            raise BlogFehler(f"Feld {feld!r} enthaelt einen internen Bezeichner -- verworfen")


# ── Der eigentliche Lauf ──────────────────────────────────────────────

def erzeuge_beitrag(db, *, jetzt: float | None = None) -> dict:
    """EIN Takt: Paket sammeln -> Mistral-Persona schreiben laesst -> Beitrag
    + Fortsetzungszustand + Paketarchiv in EINER Transaktion schreiben.

    Wirft BlogFehler, wenn Mistral nichts Brauchbares liefert -- dann bleibt
    das Paket UNVERBRAUCHT (nichts archiviert, kein Cursor bewegt) und der
    naechste Lauf sieht dieselben Zeilen wieder. Erst ein GUELTIGER,
    veroeffentlichter Beitrag verbraucht das Paket -- eine verworfene
    KI-Antwort darf echte Ereignisse nicht verschlucken.
    """
    sicherstellen(db)
    jetzt = jetzt if jetzt is not None else time.time()

    entitaet = _entitaet_lesen(db)
    paket = sammle_paket(db, jetzt=jetzt)

    system = _SYSTEM_PROMPT
    user = json.dumps({
        "dein_erzaehlfaden_von_zuletzt": entitaet.get("erzaehlfaden") or
            "(dein erster Beitrag -- noch kein vorheriger Faden)",
        "deine_zuletzt_gespiegelten_hypothesen": entitaet.get("gespiegelte_hypothesen") or
            "(noch keine erfasst)",
        "neues_datenpaket_seit_dem_letzten_beitrag": json.loads(_paket_fuer_prompt(paket)),
    }, ensure_ascii=False, sort_keys=True, default=str)

    payload = _mistral_aufruf(system=system, user=user)
    _pruefe_payload(payload)

    post_id = uuid.uuid4().hex
    paket_id = uuid.uuid4().hex
    quellen_hash = hashlib.sha256(_paket_fuer_prompt(paket).encode("utf-8")).hexdigest()

    with db.tx() as sql:
        sql.execute(
            "INSERT INTO eos_architekt_blog(post_id,ts,zeitraum_von,zeitraum_bis,"
            "ueberschrift,einleitung,text,hatte_aktivitaet,quellen_anzahl,modell) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (post_id, jetzt, paket["von"], paket["bis"],
             payload["ueberschrift"].strip(), payload["einleitung"].strip(),
             payload["text"].strip(), 1 if paket["hatte_aktivitaet"] else 0,
             paket["quellen_anzahl"], f"mistral:{MISTRAL_MODELL}"),
        )
        sql.execute(
            "INSERT INTO eos_architekt_blog_pakete(paket_id,ts,post_id,von,bis,"
            "quittung_ids,bug_ids,log_zeilen,quellen_anzahl,quellen_hash) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (paket_id, jetzt, post_id, paket["von"], paket["bis"],
             json.dumps(paket["quittung_ids"]), json.dumps(paket["bug_ids"]),
             len(paket["log_zeilen"]), paket["quellen_anzahl"], quellen_hash),
        )
        sql.execute(
            "INSERT INTO eos_architekt_blog_entitaet(singleton,letzte_post_id,"
            "erzaehlfaden,gespiegelte_hypothesen,log_byte_cursor,aktualisiert_am) "
            "VALUES(1,?,?,?,?,?) ON CONFLICT(singleton) DO UPDATE SET "
            "letzte_post_id=excluded.letzte_post_id,erzaehlfaden=excluded.erzaehlfaden,"
            "gespiegelte_hypothesen=excluded.gespiegelte_hypothesen,"
            "log_byte_cursor=excluded.log_byte_cursor,aktualisiert_am=excluded.aktualisiert_am",
            (post_id, _kompakt(payload["neuer_erzaehlfaden"], _ERZAEHLFADEN_MAX_CHARS),
             _kompakt(payload["neue_gespiegelte_hypothesen"], _GESPIEGELTE_HYPOTHESEN_MAX_CHARS),
             paket["log_byte_cursor_neu"], jetzt),
        )

    return {
        "post_id": post_id, "ueberschrift": payload["ueberschrift"].strip(),
        "hatte_aktivitaet": paket["hatte_aktivitaet"], "quellen_anzahl": paket["quellen_anzahl"],
    }


# ── Lesen (fuer die API + die CLI) ────────────────────────────────────

def liste(db, *, limit: int = 20, offset: int = 0) -> dict:
    sicherstellen(db)
    limit = max(1, min(int(limit or 20), 100))
    offset = max(0, int(offset or 0))
    gesamt = db.db.execute("SELECT COUNT(*) n FROM eos_architekt_blog").fetchone()["n"]
    zeilen = db.db.execute(
        "SELECT post_id,ts,zeitraum_von,zeitraum_bis,ueberschrift,einleitung,"
        "hatte_aktivitaet,quellen_anzahl FROM eos_architekt_blog "
        "ORDER BY ts DESC LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return {
        "gesamt": gesamt, "limit": limit, "offset": offset,
        "beitraege": [dict(r) for r in zeilen],
    }


def einzeln(db, post_id: str) -> dict:
    sicherstellen(db)
    r = db.db.execute(
        "SELECT post_id,ts,zeitraum_von,zeitraum_bis,ueberschrift,einleitung,text,"
        "hatte_aktivitaet,quellen_anzahl,modell FROM eos_architekt_blog WHERE post_id=?",
        (post_id,)
    ).fetchone()
    if not r:
        raise BlogFehler("not_found")
    return dict(r)


# ── FastAPI-Wege ─────────────────────────────────────────────────────────
#
# Gleicher Zusammenbau wie registriere_omnimind_wege: additiv, EIN Aufruf aus
# terminal_gateway.py, nur `pruefe_zugriff(request) -> user_id` (wirft
# PermissionError/AuthenticationError bei CANONICAL_USER_IDS-Pruefung) und
# `antwort_auf_fehler` kommen von aussen -- Zugang gilt fuer BEIDE Menschen
# (Gabriel + Andreas), es gibt hier keine Andreas-Ausnahme wie bei /seiten.

def registriere_architekt_blog_wege(app, *, db, pruefe_zugriff, antwort_auf_fehler) -> None:
    async def _sperre(request: Request) -> None:
        await pruefe_zugriff(request)

    @app.get("/api/architekt-blog")
    async def architekt_blog_liste(request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        q = request.query_params
        import asyncio
        ergebnis = await asyncio.to_thread(
            liste, db, limit=int(q.get("limit", 20) or 20), offset=int(q.get("offset", 0) or 0))
        return JSONResponse(ergebnis)

    @app.get("/api/architekt-blog/{post_id}")
    async def architekt_blog_einzeln(post_id: str, request: Request):
        try:
            await _sperre(request)
        except Exception as exc:
            return antwort_auf_fehler(exc)
        import asyncio
        try:
            ergebnis = await asyncio.to_thread(einzeln, db, post_id)
        except BlogFehler:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(ergebnis)
