#!/usr/bin/env python3
"""sitzung.py -- Sitzungsregistrierung fuer udb.schreiben() (AP2/AP5, erster Schritt).

GRUNDLINIE [M 15.08.]: drei gleichzeitige Schreiber auf wiki.db (WAL,
busy_timeout=5000) OHNE Koordination:
  * spaced writes (10-50ms Pause): 1474 Schreibungen gesamt, 0 Kollisionen.
  * tight-loop worst case (kein Pause): 25730 Schreibungen gesamt, 2 harte
    OperationalError (busy_timeout ausgeschoepft), ABER eine Sitzung wurde
    auf 12 von >12000 moeglichen Schreibungen ausgehungert (Fairness-Problem,
    kein Datenverlust -- SQLite serialisiert korrekt, verteilt aber nicht
    fair). SQLite+WAL loest also "database is locked" fast vollstaendig
    selbst. Was es NICHT loest: zwei Sitzungen ueberschreiben denselben
    Wert still, ohne dass die andere es merkt (logischer Verlust, kein
    Fehler). DAFUER ist dieses Modul da, nicht fuer Lock-Fehler.

Form nach F44 Paragraph 2 (Eigentuemer-Entscheidung, aus UEBERGABE-GLM.md):
Koordination ueber eine Tabelle, Schreiben versioniert statt ueberschreibend,
je Sitzung eigene Kennung. Hoechstens 3 gleichzeitige Sitzungen (F15).

Dies ist der ERSTE Schritt: Sitzungsregistrierung + Herzschlag. Die generelle
schreiben()-Funktion (versionierte Werte je Tabelle/Feld) ist NICHT Teil
dieser Datei -- das ist eine groessere Entscheidung (welche Tabellen, welche
Felder versioniert werden) und gehoert vor den Bau in den Abgleich mit AP3/
AP5, nicht in einen Alleingang. Absichtlich unvollstaendig (F45): so viel wie
traegt, Nachfragen bleibt billig.
"""
from __future__ import annotations

import os
import sqlite3
import time
import uuid

DB_PATH = os.environ.get("UDB_DB_PATH", "/var/lib/clay/wiki.db")
MAX_SITZUNGEN = 3
LEBENSZEICHEN_TIMEOUT_S = 120.0  # aelter als das gilt als tot, nicht "belegt"


def _rw(path: str = DB_PATH) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{path}?mode=rwc", uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c


def _ensure(c: sqlite3.Connection) -> None:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS vp_sitzung (
      id TEXT PRIMARY KEY,
      rechner TEXT NOT NULL,
      rolle TEXT NOT NULL,           -- z.B. 'clayverse' / 'gabriel' / 'andreas'
      gestartet REAL NOT NULL,
      lebenszeichen REAL NOT NULL
    );
    """)
    c.commit()


def registrieren(rechner: str, rolle: str) -> str:
    """Neue Sitzung anmelden. Wirft RuntimeError, wenn bereits 3 LEBENDE
    Sitzungen bestehen (F15) -- tote werden vorher aufgeraeumt, keine geraten."""
    c = _rw()
    _ensure(c)
    now = time.time()
    c.execute("DELETE FROM vp_sitzung WHERE lebenszeichen < ?", (now - LEBENSZEICHEN_TIMEOUT_S,))
    n = c.execute("SELECT COUNT(*) FROM vp_sitzung").fetchone()[0]
    if n >= MAX_SITZUNGEN:
        c.commit(); c.close()
        raise RuntimeError(f"{n} lebende Sitzungen, Obergrenze {MAX_SITZUNGEN} (F15)")
    sid = str(uuid.uuid4())
    c.execute("INSERT INTO vp_sitzung (id, rechner, rolle, gestartet, lebenszeichen) VALUES (?,?,?,?,?)",
              (sid, rechner, rolle, now, now))
    c.commit()
    c.close()
    return sid


def lebenszeichen(sid: str) -> None:
    c = _rw()
    _ensure(c)
    c.execute("UPDATE vp_sitzung SET lebenszeichen=? WHERE id=?", (time.time(), sid))
    c.commit()
    c.close()


def aktive() -> list[dict]:
    c = _rw()
    _ensure(c)
    now = time.time()
    c.execute("DELETE FROM vp_sitzung WHERE lebenszeichen < ?", (now - LEBENSZEICHEN_TIMEOUT_S,))
    c.commit()
    rows = [dict(r) for r in c.execute("SELECT * FROM vp_sitzung ORDER BY gestartet").fetchall()]
    c.close()
    return rows


def abmelden(sid: str) -> None:
    c = _rw()
    _ensure(c)
    c.execute("DELETE FROM vp_sitzung WHERE id=?", (sid,))
    c.commit()
    c.close()
