#!/usr/bin/env python3
"""folgerung.py — die Schlussfolgerungs-Ablage: hypothese | implikation | lehre.

Mechanical vessel only. This script authors NOTHING: it stores and lists
what a human/coordinator hands it via --aussage/--begruendung. No model
calls, no network calls, stdlib only.

Writes ONLY into `folgerung` and `folgerung_beleg` in /var/lib/clay/wiki.db
(WAL, busy_timeout, short transactions -- same pattern as werkzeug/wiki.py,
because three other agents write this DB concurrently). Everything else in
that DB is read-only from here.

THE HARD RULE, enforced in code: a folgerung row cannot be inserted without
at least one folgerung_beleg row. This is checked TWICE:
  1. Before touching the DB at all: `neu()` raises ValueError if `belege` is
     empty -- so an empty --beleg list never even opens a transaction.
  2. Inside the transaction: folgerung + all folgerung_beleg rows are
     inserted together; if any beleg insert fails, the whole transaction is
     rolled back (BEGIN IMMEDIATE ... COMMIT, no partial state possible).
This is application-level enforcement, not a comment or a convention.

CLI:
    folgerung.py neu --art ... --aussage ... --begruendung ... \\
                 --gilt-fuer ... [--autor ...] --beleg <art>:<id> [--beleg ...]
    folgerung.py stand
    folgerung.py zu <gilt_fuer>
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone

DB_PATH = "/var/lib/clay/wiki.db"

FOLGERUNG_ARTEN = ("hypothese", "implikation", "lehre")
FOLGERUNG_STATUS = ("offen", "gestuetzt", "widerlegt", "abgeloest")
BELEG_ARTEN = ("protokoll", "artikel", "messung", "problem", "kante", "datei")


def connect_db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def ensure_schema(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS folgerung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            art TEXT NOT NULL CHECK (art IN ('hypothese','implikation','lehre')),
            aussage TEXT NOT NULL,
            begruendung TEXT,
            gilt_fuer TEXT NOT NULL,
            autor TEXT,
            zeit TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','gestuetzt','widerlegt','abgeloest')),
            widerlegt_durch INTEGER REFERENCES folgerung(id)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS folgerung_beleg (
            folgerung_id INTEGER NOT NULL REFERENCES folgerung(id),
            beleg_art TEXT NOT NULL CHECK (beleg_art IN
                ('protokoll','artikel','messung','problem','kante','datei')),
            beleg_id TEXT NOT NULL,
            PRIMARY KEY (folgerung_id, beleg_art, beleg_id)
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_folgerung_gilt_fuer ON folgerung(gilt_fuer)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_folgerung_beleg_fid ON folgerung_beleg(folgerung_id)")
    con.commit()


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")


def neu(con, art, aussage, begruendung, gilt_fuer, belege, autor=None, status="offen"):
    """belege: list of (beleg_art, beleg_id) tuples. Raises ValueError if empty
    BEFORE any DB write -- this is check #1 of the hard rule."""
    if art not in FOLGERUNG_ARTEN:
        raise ValueError(f"unbekannte art '{art}', erlaubt: {FOLGERUNG_ARTEN}")
    if not belege:
        raise ValueError(
            "REJECTED: folgerung braucht mindestens einen --beleg "
            "(eine Schlussfolgerung ohne Beleg ist eine Meinung, keine Erkenntnis)."
        )
    for (ba, bid) in belege:
        if ba not in BELEG_ARTEN:
            raise ValueError(f"unbekannte beleg_art '{ba}', erlaubt: {BELEG_ARTEN}")
        if not bid:
            raise ValueError(f"leere beleg_id fuer beleg_art '{ba}'")

    zeit = now_iso()
    cur = con.cursor()
    try:
        con.execute("BEGIN IMMEDIATE")
        cur.execute(
            "INSERT INTO folgerung (art, aussage, begruendung, gilt_fuer, autor, zeit, status) "
            "VALUES (?,?,?,?,?,?,?)",
            (art, aussage, begruendung, gilt_fuer, autor, zeit, status),
        )
        fid = cur.lastrowid
        for (ba, bid) in belege:
            cur.execute(
                "INSERT INTO folgerung_beleg (folgerung_id, beleg_art, beleg_id) VALUES (?,?,?)",
                (fid, ba, bid),
            )
        # check #2: verify at least one beleg row actually landed before commit
        n = cur.execute(
            "SELECT COUNT(*) FROM folgerung_beleg WHERE folgerung_id=?", (fid,)
        ).fetchone()[0]
        if n == 0:
            raise ValueError("REJECTED: kein folgerung_beleg nach Insert -- rollback")
        con.commit()
        return fid
    except Exception:
        con.rollback()
        raise


def stand(con):
    print("-- nach art --")
    for row in con.execute("SELECT art, COUNT(*) FROM folgerung GROUP BY art ORDER BY art"):
        print(f"  {row[0]:12s} {row[1]}")
    print("-- nach status --")
    for row in con.execute("SELECT status, COUNT(*) FROM folgerung GROUP BY status ORDER BY status"):
        print(f"  {row[0]:12s} {row[1]}")
    total = con.execute("SELECT COUNT(*) FROM folgerung").fetchone()[0]
    orphan = con.execute(
        "SELECT COUNT(*) FROM folgerung f WHERE NOT EXISTS "
        "(SELECT 1 FROM folgerung_beleg b WHERE b.folgerung_id=f.id)"
    ).fetchone()[0]
    print(f"gesamt: {total}, ohne Beleg (sollte immer 0 sein): {orphan}")


def zu(con, gilt_fuer):
    rows = con.execute(
        "SELECT id, art, status, zeit, aussage FROM folgerung WHERE gilt_fuer=? ORDER BY zeit",
        (gilt_fuer,),
    ).fetchall()
    for r in rows:
        belege = con.execute(
            "SELECT beleg_art, beleg_id FROM folgerung_beleg WHERE folgerung_id=?", (r[0],)
        ).fetchall()
        bstr = ", ".join(f"{a}:{i}" for a, i in belege)
        print(f"#{r[0]} [{r[1]:11s}] [{r[2]:10s}] {r[3]}  {r[4]}")
        print(f"    Belege: {bstr}")
    print(f"({len(rows)} Zeilen fuer gilt_fuer='{gilt_fuer}')")


def parse_beleg(s):
    if ":" not in s:
        raise argparse.ArgumentTypeError(f"--beleg braucht Form <art>:<id>, bekam '{s}'")
    ba, bid = s.split(":", 1)
    return (ba, bid)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_neu = sub.add_parser("neu")
    p_neu.add_argument("--art", required=True, choices=FOLGERUNG_ARTEN)
    p_neu.add_argument("--aussage", required=True)
    p_neu.add_argument("--begruendung", default=None)
    p_neu.add_argument("--gilt-fuer", required=True, dest="gilt_fuer")
    p_neu.add_argument("--autor", default=None)
    p_neu.add_argument("--status", default="offen", choices=FOLGERUNG_STATUS)
    p_neu.add_argument("--beleg", action="append", type=parse_beleg, default=[],
                        help="Form <art>:<id>, wiederholbar. MINDESTENS EINER ist Pflicht.")

    sub.add_parser("stand")
    p_zu = sub.add_parser("zu")
    p_zu.add_argument("gilt_fuer")

    args = ap.parse_args()
    con = connect_db()
    ensure_schema(con)

    if args.cmd == "neu":
        try:
            fid = neu(con, args.art, args.aussage, args.begruendung, args.gilt_fuer,
                      args.beleg, autor=args.autor, status=args.status)
            print(f"folgerung #{fid} angelegt, {len(args.beleg)} Beleg(e).")
        except ValueError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
    elif args.cmd == "stand":
        stand(con)
    elif args.cmd == "zu":
        zu(con, args.gilt_fuer)
    con.close()


if __name__ == "__main__":
    main()
