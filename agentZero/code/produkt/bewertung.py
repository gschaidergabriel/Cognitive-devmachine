"""Bewertung: Daumen hoch/runter je Zero-Antwort (Zug), fuer spaetere Auswertung.

Eigner-Auftrag 2026-08-21 (Teil B): jede Zero-Antwort im Chat bekommt eine
Bewertung, gespeichert mit genug Metadaten, dass sich das spaeter tatsaechlich
auswerten laesst -- nicht nur ein nackter Zaehler.

⚠️ Ablage: /var/lib/clay/wiki.db -- dieselbe UnifiedDB (db.db) wie `turns`,
NICHT eine eigene Datei. Begruendung: eine Bewertung OHNE den Zug, den sie
bewertet, ist wertlos fuer die Auswertung (JOIN auf turn_id waere ueber eine
zweite Datei nur ueber ATTACH moeglich, WAL-Kopplung waere ein zweites
Betriebsrisiko fuer denselben fachlichen Bereich). Eine neue Tabelle in
derselben Datei ist der schmalste Eingriff.

⚠️ NIE executescript() hier -- siehe store.tx()-Kommentar in store.py und der
f-77-Zwischenfall (erfolge.py-Kommentar): executescript() committet implizit
und reisst jede offene Transaktion auseinander, die auf DERSELBEN Verbindung
laeuft. Genau EIN CREATE TABLE + EIN CREATE INDEX, je ein eigenes execute().

Metadaten je Zeile (Auftrag: "Zug, Sitzung, wer, wann, Wert, Frage und
Antwort -- oder Hash+Laenge -- Modell, und was der Zug schon billig hergibt"):
  turn_id/session_id      -- der bewertete Zug (Fremdschluessel-artig, kein
                              echtes REFERENCES: turns lebt in derselben
                              Tabelle derselben Datei, aber dieses Modul soll
                              nie einen Zug loeschen koennen, nur lesen).
  user_id                 -- wer bewertet hat (NICHT zwingend turns.user_id:
                              der Zug "gehoert" der Sitzung, bewerten kann
                              nur, wem die Sitzung gehoert -- siehe Pruefung
                              unten, ist_kanonische_sitzung).
  wert                    -- +1/-1. wert=0 (keine Bewertung mehr) LOESCHT die
                              Zeile, statt eine dritte Wert-Auspraegung zu
                              fuehren -- "keine Meinung" ist keine Metrik.
  frage_turn_id/-hash/-laenge, antwort_hash/-laenge
                           -- NICHT der Klartext: turns.content traegt Frage
                              und Antwort schon kanonisch (siehe store.py),
                              ein zweiter Klartext hier waere eine zweite
                              Quelle, die mit der ersten auseinanderlaufen
                              kann. Hash+Laenge reichen, um bei der Auswertung
                              per turn_id auf turns zurueckzujoinen UND um
                              "gleiche Antwort nochmal gefragt" zu erkennen,
                              ohne den Text zweimal zu halten.
  modell                  -- best effort aus mv_translation_log (siehe
                              _modell_fuer_zug unten); ehrlich NULL, wenn sich
                              keine Zeile findet (z.B. ein Terminal-/CLI-Zug
                              ohne Uebersetzung) -- NIE erfunden.
  ts                       -- Zeitpunkt DIESER Bewertung (aendert sich bei
                              jedem Meinungswechsel).
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
import uuid

from .identity import ist_kanonische_sitzung

SCHEMA_SQL = (
    "CREATE TABLE IF NOT EXISTS eos_bewertungen("
    "bewertung_id TEXT PRIMARY KEY,"
    "turn_id TEXT NOT NULL,"
    "session_id TEXT NOT NULL,"
    "user_id TEXT NOT NULL,"
    "wert INTEGER NOT NULL CHECK(wert IN (-1,1)),"
    "frage_turn_id TEXT,"
    "frage_hash TEXT,"
    "frage_laenge INTEGER,"
    "antwort_hash TEXT NOT NULL,"
    "antwort_laenge INTEGER NOT NULL,"
    "modell TEXT,"
    "ts REAL NOT NULL,"
    "UNIQUE(turn_id, user_id))"
)
SCHEMA_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS eos_bewertungen_session_idx "
    "ON eos_bewertungen(session_id, ts)"
)


class BewertungFehler(ValueError):
    """Unbekannter Zug, kein Antwort-Zug, oder ein ungueltiger Wert."""


def sicherstellen(db) -> None:
    """Idempotent, billig -- wie erfolge.sicherstellen(): vor jeder Operation
    aufgerufen statt einmalig beim App-Start, damit dieses Modul keinen
    eigenen Start-Hook braucht."""
    db.db.execute(SCHEMA_SQL)
    db.db.execute(SCHEMA_INDEX_SQL)


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _modell_fuer_zug(db, session_id: str, antwort_content: str) -> str | None:
    """Bestes verfuegbares Modell zu diesem Zug, best effort.

    Der Zug selbst (turns) traegt kein Modellfeld -- die Vorstufe schreibt es
    in mv_translation_log (clayverse/mistral_prestage/store.py). Deren
    turn_id zeigt auf den BENUTZER-Zug, nicht den Antwort-Zug (siehe
    terminal_gateway._history_page-Kommentar) -- ein Join ueber turn_id traefe
    hier also nie. Stattdessen dieselbe inhaltsbasierte Bruecke wie dort:
    m.caveman_original IST identisch mit turns.content des Assistenten (beides
    = Zeros unuebersetzte Antwort). Bei Mehrdeutigkeit (zwei wortgleiche kurze
    Antworten in derselben Sitzung) gewinnt die juengste Uebersetzung -- fuer
    ein Auswertungs-Metadatum reicht das; anders als in der Live-Anzeige gibt
    es hier keine Ordinal-Naehe zum Entzerren. mv_translation_log kann fehlen
    (noch kein Chat-Zug je gelaufen) -- dann ehrlich NULL, kein Fehler.
    """
    try:
        row = db.db.execute(
            "SELECT m.translator_model FROM mv_translation_log m "
            "JOIN turns t ON t.turn_id = m.turn_id "
            "WHERE t.session_id = ? AND m.caveman_original = ? "
            "ORDER BY m.created_at DESC LIMIT 1",
            (session_id, antwort_content),
        ).fetchone()
    except sqlite3.OperationalError:
        return None  # Tabelle existiert noch nicht -- kein Chat-Zug ist je gelaufen
    return row[0] if row and row[0] else None


def setzen(db, *, turn_id: str, user_id: str, wert: int) -> dict:
    """Stimme setzen/aendern/entfernen -- immer eine Zeile je (turn_id, user_id).

    wert=0 entfernt die Bewertung (DELETE). wert in (-1,1) legt sie an oder
    ersetzt sie (INSERT ... ON CONFLICT DO UPDATE) -- idempotent: derselbe
    Aufruf zweimal hintereinander erzeugt nie eine zweite Zeile, das UNIQUE(
    turn_id,user_id) plus der Conflict-Handler sorgen dafuer serverseitig,
    nicht nur per Konvention im Frontend.
    """
    if wert not in (-1, 0, 1):
        raise BewertungFehler("wert muss -1, 0 oder 1 sein")
    sicherstellen(db)

    zug = db.db.execute(
        "SELECT session_id, role, content, ordinal FROM turns WHERE turn_id=?",
        (turn_id,),
    ).fetchone()
    if zug is None:
        raise BewertungFehler("unbekannter Zug")
    if zug["role"] != "assistant":
        raise BewertungFehler("nur Zeros Antworten lassen sich bewerten")

    session_id = zug["session_id"]
    # Dieselbe Sitzungspruefung wie /api/history: bewerten darf nur, wem die
    # Sitzung gehoert -- session_id kommt hier NICHT von der Anfrage, sondern
    # aus dem Zug selbst, aber user_id ist der AUFRUFER, und der muss zur
    # Sitzung passen, sonst koennte ein Mensch die Zuege des anderen bewerten.
    if not ist_kanonische_sitzung(session_id, user_id):
        raise PermissionError("fremde Sitzung")

    if wert == 0:
        with db.tx() as sql:
            sql.execute(
                "DELETE FROM eos_bewertungen WHERE turn_id=? AND user_id=?",
                (turn_id, user_id),
            )
        return {"ok": True, "turn_id": turn_id, "wert": 0}

    frage = db.db.execute(
        "SELECT turn_id, content FROM turns WHERE session_id=? AND role='user' "
        "AND ordinal<? ORDER BY ordinal DESC LIMIT 1",
        (session_id, zug["ordinal"]),
    ).fetchone()
    modell = _modell_fuer_zug(db, session_id, zug["content"])

    bewertung_id = uuid.uuid4().hex
    now = time.time()
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO eos_bewertungen(bewertung_id,turn_id,session_id,user_id,wert,"
            "frage_turn_id,frage_hash,frage_laenge,antwort_hash,antwort_laenge,modell,ts) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(turn_id,user_id) DO UPDATE SET wert=excluded.wert,"
            "frage_turn_id=excluded.frage_turn_id,frage_hash=excluded.frage_hash,"
            "frage_laenge=excluded.frage_laenge,antwort_hash=excluded.antwort_hash,"
            "antwort_laenge=excluded.antwort_laenge,modell=excluded.modell,ts=excluded.ts",
            (
                bewertung_id, turn_id, session_id, user_id, wert,
                frage["turn_id"] if frage else None,
                _hash(frage["content"]) if frage else None,
                len(frage["content"]) if frage else None,
                _hash(zug["content"]), len(zug["content"]),
                modell, now,
            ),
        )
    return {"ok": True, "turn_id": turn_id, "wert": wert}


def lesen_fuer_sitzung(db, *, session_id: str, user_id: str) -> dict:
    """turn_id -> wert, nur die eigenen Stimmen dieses Menschen in dieser
    Sitzung -- die Oberflaeche markiert damit beim Laden des Verlaufs, welche
    Antworten schon bewertet wurden."""
    if not ist_kanonische_sitzung(session_id, user_id):
        raise PermissionError("fremde Sitzung")
    sicherstellen(db)
    zeilen = db.db.execute(
        "SELECT turn_id, wert FROM eos_bewertungen WHERE session_id=? AND user_id=?",
        (session_id, user_id),
    ).fetchall()
    return {r["turn_id"]: r["wert"] for r in zeilen}
