#!/usr/bin/env python3
"""
ClayVerse: kuration.py -- Quellen-Ueberwachung + Kurations-Warteschlange.

Eigentuemer dieser Datei: kuration-Agent. NICHT anfassen: wiki.py (artikel/kante),
suche.py (suche.db). Diese Datei liest NUR aus artikel (SELECT), schreibt NIE dorthin.
Eigene Tabellen in derselben DB (/var/lib/clay/wiki.db): kuration, anreicherung.

Zero Modell-Aufrufe. Reine Datei-/Hash-/DB-Mechanik.
"""

import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

DB_PATH = "/var/lib/clay/wiki.db"
HASH_CHUNK = 1024 * 1024
MAX_RETRIES = 8
RETRY_BASE_DELAY = 0.25
BUSY_TIMEOUT_MS = 30000

NOETIG_MECHANISCH = "mechanisch"
NOETIG_MODELL = "modell"
NOETIG_NETZ = "netz"

KLASSE_UNVERAENDERT = "unveraendert"
KLASSE_GEAENDERT = "quelle_geaendert"
KLASSE_FEHLT = "quelle_fehlt"
KLASSE_NEU = "neu_dazugekommen"


def jetzt():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    if not os.path.exists(DB_PATH):
        raise SystemExit(
            "FATAL: %s existiert nicht. wiki.py muss die DB zuerst anlegen "
            "(artikel/kante). Kein Fallback, kein Erfinden einer eigenen DB." % DB_PATH
        )
    con = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=%d" % BUSY_TIMEOUT_MS)
    con.row_factory = sqlite3.Row
    return con


def retry_write(con, sql, params=()):
    """Never crash on a transient lock; retry with backoff. Raise (loud) on
    anything else -- never silently swallow a real error."""
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(sql, params)
            con.execute("COMMIT")
            return
        except sqlite3.OperationalError as e:
            last_err = e
            try:
                con.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
                continue
            raise
    raise RuntimeError(
        "Schreiben nach %d Versuchen weiterhin gesperrt: %s -- SQL=%s" % (MAX_RETRIES, last_err, sql)
    )


def ensure_schema(con):
    retry_write(con, """
        CREATE TABLE IF NOT EXISTS kuration (
            artikel_id           TEXT PRIMARY KEY,
            quelle                TEXT,
            ereignis              TEXT,
            klasse                TEXT NOT NULL,
            alt_hash              TEXT,
            neu_hash              TEXT,
            alt_groesse           INTEGER,
            alt_zeilen            INTEGER,
            neu_groesse           INTEGER,
            neu_zeilen            INTEGER,
            erkannt_am            TEXT NOT NULL,
            zuletzt_geprueft_am   TEXT NOT NULL,
            noetig                TEXT NOT NULL,
            status                TEXT NOT NULL DEFAULT 'offen'
        )
    """)
    retry_write(con, """
        CREATE TABLE IF NOT EXISTS anreicherung (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            artikel_id   TEXT NOT NULL,
            quelle_url   TEXT,
            art          TEXT,
            auszug       TEXT,
            geholt_am    TEXT,
            hash         TEXT
        )
    """)


def datei_zustand(pfad):
    """Liefert (ok, hash_or_None, groesse_or_None, zeilen_or_None, grund_or_None).
    Ein unlesbarer/fehlender Pfad ist IMMER ein Fund (quelle_fehlt), nie ein
    stillschweigend uebersprungener Erfolg."""
    try:
        if os.path.isdir(pfad):
            return False, None, None, None, "ist ein Verzeichnis, kein Datei-Hash moeglich"
        if not os.path.exists(pfad):
            return False, None, None, None, "Datei fehlt (existiert nicht)"
        h = hashlib.sha256()
        groesse = 0
        zeilen = 0
        with open(pfad, "rb") as f:
            while True:
                chunk = f.read(HASH_CHUNK)
                if not chunk:
                    break
                h.update(chunk)
                groesse += len(chunk)
                zeilen += chunk.count(b"\n")
        return True, h.hexdigest(), groesse, zeilen, None
    except PermissionError as e:
        return False, None, None, None, "keine Leseberechtigung: %s" % e
    except OSError as e:
        return False, None, None, None, "OS-Fehler beim Lesen: %s" % e


def noetig_fuer(quelle, klasse):
    if quelle and (quelle.startswith("http://") or quelle.startswith("https://")):
        return NOETIG_NETZ
    if klasse == KLASSE_GEAENDERT:
        return NOETIG_MODELL
    if klasse == KLASSE_FEHLT:
        return NOETIG_MECHANISCH
    if klasse == KLASSE_NEU:
        return NOETIG_MECHANISCH
    return NOETIG_MECHANISCH


def upsert_kuration(con, artikel_id, quelle, ereignis, klasse, alt_hash, neu_hash,
                     alt_groesse, alt_zeilen, neu_groesse, neu_zeilen, noetig, status,
                     erkannt_am):
    now = jetzt()
    retry_write(con, """
        INSERT INTO kuration
            (artikel_id, quelle, ereignis, klasse, alt_hash, neu_hash,
             alt_groesse, alt_zeilen, neu_groesse, neu_zeilen,
             erkannt_am, zuletzt_geprueft_am, noetig, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(artikel_id) DO UPDATE SET
            quelle=excluded.quelle,
            ereignis=excluded.ereignis,
            klasse=excluded.klasse,
            alt_hash=excluded.alt_hash,
            neu_hash=excluded.neu_hash,
            alt_groesse=excluded.alt_groesse,
            alt_zeilen=excluded.alt_zeilen,
            neu_groesse=excluded.neu_groesse,
            neu_zeilen=excluded.neu_zeilen,
            erkannt_am=excluded.erkannt_am,
            zuletzt_geprueft_am=excluded.zuletzt_geprueft_am,
            noetig=excluded.noetig,
            status=excluded.status
    """, (artikel_id, quelle, ereignis, klasse, alt_hash, neu_hash,
          alt_groesse, alt_zeilen, neu_groesse, neu_zeilen,
          erkannt_am, now, noetig, status))


def touch_zuletzt_geprueft(con, artikel_id):
    """Reines Idempotenz-Bookkeeping: darf Klasse/Status/erkannt_am NICHT anfassen."""
    retry_write(
        con,
        "UPDATE kuration SET zuletzt_geprueft_am=? WHERE artikel_id=?",
        (jetzt(), artikel_id),
    )


def pruefen(con):
    zaehler = {KLASSE_UNVERAENDERT: 0, KLASSE_GEAENDERT: 0, KLASSE_FEHLT: 0, KLASSE_NEU: 0}
    neu_inserts = 0
    updates = 0
    noops = 0

    is_bootstrap = con.execute("SELECT COUNT(*) c FROM kuration").fetchone()["c"] == 0

    artikel_rows = con.execute("SELECT id, quelle, quell_hash FROM artikel").fetchall()
    if not artikel_rows:
        print("WARNUNG: artikel-Tabelle ist leer -- nichts zu pruefen.")
        return zaehler

    artikel_ids_jetzt = set()

    for row in artikel_rows:
        artikel_id = row["id"]
        quelle = row["quelle"]
        quell_hash = row["quell_hash"]
        artikel_ids_jetzt.add(artikel_id)

        bestehend = con.execute(
            "SELECT * FROM kuration WHERE artikel_id=?", (artikel_id,)
        ).fetchone()

        ok, cur_hash, cur_groesse, cur_zeilen, grund = datei_zustand(quelle)

        if not ok:
            zaehler[KLASSE_FEHLT] += 1
            if bestehend is not None and bestehend["klasse"] == KLASSE_FEHLT:
                touch_zuletzt_geprueft(con, artikel_id)
                noops += 1
                continue
            alt_hash = bestehend["neu_hash"] if bestehend is not None else quell_hash
            alt_groesse = bestehend["neu_groesse"] if bestehend is not None else None
            alt_zeilen = bestehend["neu_zeilen"] if bestehend is not None else None
            upsert_kuration(
                con, artikel_id, quelle,
                "Quelle unlesbar/fehlt: %s" % grund,
                KLASSE_FEHLT, alt_hash, None,
                alt_groesse, alt_zeilen, None, None,
                noetig_fuer(quelle, KLASSE_FEHLT), "offen",
                jetzt(),
            )
            updates += 1
            continue

        # Datei lesbar.
        if bestehend is not None:
            baseline_hash = bestehend["neu_hash"]
            if cur_hash == baseline_hash:
                zaehler[KLASSE_UNVERAENDERT] += 1
                touch_zuletzt_geprueft(con, artikel_id)
                noops += 1
                continue
            # Hash weicht vom zuletzt erfassten Stand ab -> Aenderung.
            zaehler[KLASSE_GEAENDERT] += 1
            groessen_delta = (
                (cur_groesse - bestehend["neu_groesse"])
                if bestehend["neu_groesse"] is not None else None
            )
            zeilen_delta = (
                (cur_zeilen - bestehend["neu_zeilen"])
                if bestehend["neu_zeilen"] is not None else None
            )
            ereignis = "Hash geaendert. Groesse %s -> %s (delta %s). Zeilen %s -> %s (delta %s)." % (
                bestehend["neu_groesse"], cur_groesse, groessen_delta,
                bestehend["neu_zeilen"], cur_zeilen, zeilen_delta,
            )
            upsert_kuration(
                con, artikel_id, quelle, ereignis,
                KLASSE_GEAENDERT, baseline_hash, cur_hash,
                bestehend["neu_groesse"], bestehend["neu_zeilen"], cur_groesse, cur_zeilen,
                noetig_fuer(quelle, KLASSE_GEAENDERT), "offen",
                jetzt(),
            )
            updates += 1
            continue

        # Kein eigener kuration-Datensatz vorhanden.
        if is_bootstrap:
            if cur_hash == quell_hash:
                zaehler[KLASSE_UNVERAENDERT] += 1
                upsert_kuration(
                    con, artikel_id, quelle,
                    "Erstlauf: Hash entspricht quell_hash aus artikel.",
                    KLASSE_UNVERAENDERT, None, cur_hash,
                    None, None, cur_groesse, cur_zeilen,
                    NOETIG_MECHANISCH, "erledigt",
                    jetzt(),
                )
                neu_inserts += 1
            else:
                zaehler[KLASSE_GEAENDERT] += 1
                ereignis = (
                    "Erstlauf: Datei-Hash weicht bereits von artikel.quell_hash ab "
                    "(Quelle hat sich vor der ersten Pruefung veraendert). Groesse jetzt %s, Zeilen jetzt %s. "
                    "Alter Umfang unbekannt (nur Hash historisch, keine Bytes)." % (cur_groesse, cur_zeilen)
                )
                upsert_kuration(
                    con, artikel_id, quelle, ereignis,
                    KLASSE_GEAENDERT, quell_hash, cur_hash,
                    None, None, cur_groesse, cur_zeilen,
                    noetig_fuer(quelle, KLASSE_GEAENDERT), "offen",
                    jetzt(),
                )
                neu_inserts += 1
        else:
            zaehler[KLASSE_NEU] += 1
            upsert_kuration(
                con, artikel_id, quelle,
                "Neuer Artikel seit letztem Kurationslauf entdeckt (kein vorheriger kuration-Datensatz).",
                KLASSE_NEU, None, cur_hash,
                None, None, cur_groesse, cur_zeilen,
                noetig_fuer(quelle, KLASSE_NEU), "offen",
                jetzt(),
            )
            neu_inserts += 1

    print(json.dumps({
        "modus": "bootstrap" if is_bootstrap else "fortlaufend",
        "artikel_geprueft": len(artikel_rows),
        "klassen": zaehler,
        "neu_eingefuegt": neu_inserts,
        "aktualisiert": updates,
        "no_ops": noops,
    }, indent=2, ensure_ascii=False))
    return zaehler


def stand(con):
    print("== Stand kuration ==")
    for row in con.execute("SELECT klasse, COUNT(*) c FROM kuration GROUP BY klasse ORDER BY klasse"):
        print("  %-20s %d" % (row["klasse"], row["c"]))

    offen = con.execute("SELECT COUNT(*) c FROM kuration WHERE status='offen'").fetchone()["c"]
    print("Warteschlange (status=offen): %d" % offen)

    aeltester = con.execute(
        "SELECT artikel_id, erkannt_am FROM kuration WHERE status='offen' ORDER BY erkannt_am ASC LIMIT 1"
    ).fetchone()
    if aeltester:
        try:
            alt_dt = datetime.fromisoformat(aeltester["erkannt_am"])
            alter_sek = (datetime.now(timezone.utc) - alt_dt).total_seconds()
        except ValueError:
            alter_sek = None
        print("Aeltester offener Fund: %s (erkannt_am=%s, Alter_s=%s)" % (
            aeltester["artikel_id"], aeltester["erkannt_am"], alter_sek))
    else:
        print("Aeltester offener Fund: keiner")

    print("-- nach noetig (nur offen) --")
    for row in con.execute(
        "SELECT noetig, COUNT(*) c FROM kuration WHERE status='offen' GROUP BY noetig ORDER BY noetig"
    ):
        print("  %-12s %d" % (row["noetig"], row["c"]))

    total_kuration = con.execute("SELECT COUNT(*) c FROM kuration").fetchone()["c"]
    total_artikel = con.execute("SELECT COUNT(*) c FROM artikel").fetchone()["c"]
    print("kuration-Zeilen gesamt: %d / artikel gesamt: %d" % (total_kuration, total_artikel))

    anr = con.execute("SELECT COUNT(*) c FROM anreicherung").fetchone()["c"]
    print("anreicherung-Zeilen (sollten 0 sein -- kein Netzabruf diese Runde): %d" % anr)


def warteschlange(con, limit=50, noetig_filter=None):
    sql = "SELECT artikel_id, quelle, klasse, noetig, ereignis, erkannt_am FROM kuration WHERE status='offen'"
    params = []
    if noetig_filter:
        sql += " AND noetig=?"
        params.append(noetig_filter)
    sql += " ORDER BY erkannt_am ASC LIMIT ?"
    params.append(limit)
    for row in con.execute(sql, params):
        print(json.dumps(dict(row), ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Nutzung: kuration.py pruefen|stand|warteschlange [--limit N] [--noetig mechanisch|modell|netz]")
        sys.exit(2)

    cmd = sys.argv[1]
    con = connect()
    try:
        ensure_schema(con)
        if cmd == "pruefen":
            pruefen(con)
        elif cmd == "stand":
            stand(con)
        elif cmd == "warteschlange":
            limit = 50
            noetig_filter = None
            args = sys.argv[2:]
            i = 0
            while i < len(args):
                if args[i] == "--limit" and i + 1 < len(args):
                    limit = int(args[i + 1]); i += 2
                elif args[i] == "--noetig" and i + 1 < len(args):
                    noetig_filter = args[i + 1]; i += 2
                else:
                    i += 1
            warteschlange(con, limit, noetig_filter)
        else:
            print("Unbekannter Befehl: %s" % cmd)
            sys.exit(2)
    finally:
        con.close()


if __name__ == "__main__":
    main()
