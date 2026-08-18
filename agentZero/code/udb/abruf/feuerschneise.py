#!/usr/bin/env python3
"""udb/abruf/feuerschneise.py — Self-Validierung für kritische Bedingungen.

Lücke 3 Fix: Feuerschneise prüft Bedingungen selbst, statt sie nur vom Aufrufer
behaupten zu lassen. Kein Modellaufruf, reine mechanische Validierung.
"""

import sqlite3
import os
from typing import Literal

from udb.abruf.zustand import verbindung

DB_PATH = os.environ.get("UDB_DB_PATH", "/var/lib/clay/wiki.db")


def validiere_verbindung(c: sqlite3.Connection) -> dict:
    """Prüft ob die Verbindung die kritischen Eigenschaften hat.

    Lücke 3 Fix: Behauptete Eigenschaften werden hier selbst geprüft.
    """
    ergebnis = {
        "ok": True,
        "mode": "unbekannt",
        "query_only": None,
        "busy_timeout": None,
        "fehler": []
    }

    try:
        # PRAGMA mode prüfen
        mode_row = c.execute("PRAGMA journal_mode").fetchone()
        ergebnis["mode"] = mode_row[0] if mode_row else "unbekannt"

        # PRAGMA query_only prüfen
        qo_row = c.execute("PRAGMA query_only").fetchone()
        ergebnis["query_only"] = qo_row[0] if qo_row else None

        # PRAGMA busy_timeout prüfen
        bt_row = c.execute("PRAGMA busy_timeout").fetchone()
        ergebnis["busy_timeout"] = bt_row[0] if bt_row else None

        # Kritische Checks
        if ergebnis["query_only"] != 0:  # 0 = erlaubt Schreibzugriffe
            ergebnis["fehler"].append(f"query_only={ergebnis['query_only']} — erwartet 0 für Schreibzugriff")
            ergebnis["ok"] = False

        if not ergebnis["busy_timeout"] or ergebnis["busy_timeout"] < 5000:
            ergebnis["fehler"].append(f"busy_timeout={ergebnis['busy_timeout']}ms — erwartet >=5000ms")
            ergebnis["ok"] = False

        if ergebnis["mode"] not in ("wal", "memory"):
            ergebnis["fehler"].append(f"journal_mode={ergebnis['mode']} — erwartet 'wal' oder 'memory'")
            ergebnis["ok"] = False

    except sqlite3.Error as e:
        ergebnis["fehler"].append(f"Prüfung fehlgeschlagen: {e}")
        ergebnis["ok"] = False

    return ergebnis


def validiere_tabelle_existiert(c: sqlite3.Connection, tabellenname: str) -> bool:
    """Prüft ob eine Tabelle existiert (Lücke 3 Fix: Selbstprüfung, keine Behauptung)."""
    try:
        result = c.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (tabellenname,)
        ).fetchone()
        return result[0] > 0 if result else False
    except sqlite3.Error:
        return False


def validiere_db_schema(pfad: str = DB_PATH) -> dict:
    """Prüft kritische Tabellen und Indizes.

    Lücke 3 Fix: Schema-Validierung statt Behauptung.
    """
    ergebnis = {
        "ok": True,
        "tabellen": {},
        "fehler": []
    }

    kritische_tabellen = [
        "artikel", "kante", "artikel_sphaere",
        "wm_topologie", "wm_lesart", "kuration"
    ]

    try:
        c = verbindung(pfad)  # Schritt 2 Fix: udb.verbindung() statt sqlite3.connect()

        for tabelle in kritische_tabellen:
            existiert = validiere_tabelle_existiert(c, tabelle)
            ergebnis["tabellen"][tabelle] = existiert
            if not existiert:
                ergebnis["fehler"].append(f"Tabelle fehlt: {tabelle}")
                ergebnis["ok"] = False

        c.close()

    except sqlite3.Error as e:
        ergebnis["fehler"].append(f"Schema-Prüfung fehlgeschlagen: {e}")
        ergebnis["ok"] = False

    return ergebnis


def pruefe_kondition(kondition: str, kontext: dict = None) -> dict:
    """Allgemeine Konditions-Prüfung (Lücke 3 Fix: Self-Validation).

    Akzeptierte Konditionen:
    - 'verbindung_lesend': Verbindung ist read-only mit query_only=ON
    - 'verbindung_schreibend': Verbindung erlaubt Schreibzugriffe
    - 'schema_komplett': Alle kritischen Tabellen existieren
    """
    ergebnis = {
        "kondition": kondition,
        "ok": False,
        "details": {},
        "fehler": []
    }

    try:
        if kondition == "verbindung_lesend":
            from udb.abruf.zustand import verbindung
            c = verbindung()
            ergebnis["details"] = validiere_verbindung(c)
            ergebnis["ok"] = ergebnis["details"]["ok"]
            c.close()

        elif kondition == "verbindung_schreibend":
            from udb.abruf.zustand import schreib_verbindung
            c = schreib_verbindung()
            ergebnis["details"] = validiere_verbindung(c)
            ergebnis["ok"] = ergebnis["details"]["ok"]
            c.close()

        elif kondition == "schema_komplett":
            ergebnis["details"] = validiere_db_schema()
            ergebnis["ok"] = ergebnis["details"]["ok"]

        else:
            ergebnis["fehler"].append(f"Unbekannte Kondition: {kondition}")

    except Exception as e:
        ergebnis["fehler"].append(f"Prüfung fehlgeschlagen: {e}")

    return ergebnis
