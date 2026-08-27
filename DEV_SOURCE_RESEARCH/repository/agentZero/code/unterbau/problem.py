#!/usr/bin/env python3
"""problem.py — erntet `problem`-Zeilen aus dem `offen`-Feld von protokoll.jsonl.

Mechanical only. No model calls, no network calls, stdlib only.
Reads /opt/clayverse/bau/protokoll.jsonl (owned by bau.py — NEVER written here).
Writes ONLY into the `problem` table of /var/lib/clay/wiki.db. Everything
else in that DB (artikel/kante/datei/fundort/messung/...) is read-only from
here; three other agents write it concurrently, hence WAL + busy_timeout +
short transactions, matching the pattern already used by werkzeug/wiki.py.

zeile_hash = sha256 of the individual JSONL LINE (raw bytes, exact line),
NEVER of the whole file. This is deliberate: wiki.py's artikel.quell_hash
hashes the whole protokoll.jsonl, which is a documented, known defect
(protokoll entry idx35/B27: "34 der 35 Warteschlangeneintraege zeigen auf
DIESELBE Datei ... jeder neue Bauschritt markiert alle 34 als geaendert").
We do not repeat it here.

Splitting rule (mechanical, see SPLIT_RE below):
    split the `offen` string on sentence boundaries: a sentence-final
    punctuation mark (. ! ?) followed by whitespace and then an uppercase
    letter, a digit, or an opening parenthesis. This catches explicit
    enumerations ("Zweitens:", "Drittens:", "(1)", "(2)", "WEITER:", ...)
    for free, because in every observed case they are their own sentence
    starting with a capital letter or a digit/paren. It does NOT split on
    semicolons, commas, or em-dashes, because those routinely separate
    sub-clauses of the SAME hurdle in this data (see report) and splitting
    there would require semantic judgment, which is forbidden here.
    Known limitation: a sentence that starts with a lowercase proper noun
    (e.g. "clayverse-alt (srv1563149) ...") is NOT split off, because the
    rule requires an uppercase/digit/paren start. This under-splits rather
    than over-splits, which is the safer failure mode given "no invention".

Classification rule (art) — MECHANICAL, literal keyword match only:
    'problem'       if the fragment contains the literal substring "problem"
    'huerde'        if it contains "hürde"/"huerde"
    'risiko'        if it contains "risik" (risiko/riskant) or "gefahr"
    'offene_frage'  otherwise (neutral default; also covers ambiguous wording)
No stemming beyond this, no synonym guessing (e.g. "blockt", "Fehler",
"KONSTRUKTIONSFEHLER" are NOT treated as hurdle/problem synonyms — that
would be guessing severity, which is explicitly forbidden).

CLI:
    problem.py ernten            harvest offen-fields into `problem` (idempotent)
    problem.py stand              counts by art / bauteil / status
    problem.py zu <bauteil>       list problems for one Bauteil
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone

DB_PATH = "/var/lib/clay/wiki.db"
PROTOKOLL = "/opt/clayverse/bau/protokoll.jsonl"

import sqlite3


def connect_db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def ensure_schema(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS problem (
            id TEXT PRIMARY KEY,
            bauteil TEXT,
            quelle TEXT NOT NULL,
            zeile_hash TEXT NOT NULL,
            text TEXT NOT NULL,
            art TEXT NOT NULL CHECK (art IN ('problem','huerde','risiko','offene_frage')),
            erkannt_am TEXT,
            status TEXT NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','geloest')),
            geloest_am TEXT,
            geloest_durch TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_problem_bauteil ON problem(bauteil)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_problem_status ON problem(status)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_problem_zeile_hash ON problem(zeile_hash)")
    con.commit()


# sentence-boundary split: after . ! ? + whitespace, before an uppercase
# letter (incl. Umlaut-capitals), a digit, or an opening parenthesis.
SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9(])")

KW_PROBLEM = re.compile(r"problem", re.IGNORECASE)
KW_HUERDE = re.compile(r"h(ü|ue)rde", re.IGNORECASE)
KW_RISIKO = re.compile(r"risik|gefahr", re.IGNORECASE)


def classify(text: str) -> str:
    if KW_PROBLEM.search(text):
        return "problem"
    if KW_HUERDE.search(text):
        return "huerde"
    if KW_RISIKO.search(text):
        return "risiko"
    return "offene_frage"


def split_offen(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = [p.strip() for p in SPLIT_RE.split(text)]
    return [p for p in parts if p]


def sha256_line(raw_line: str) -> str:
    # hash the exact raw line bytes as they appear in the file (no strip,
    # no reserialization) -- this is what "zeile_hash = sha256 of the
    # individual JSONL LINE" means: reproducible from the file on disk.
    return hashlib.sha256(raw_line.encode("utf-8")).hexdigest()


def ernten(con, verbose=True):
    with open(PROTOKOLL, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    total_offen = 0
    total_rows = 0
    inserted = 0
    already = 0
    split_counts = []  # (bauteil, n_parts) for lines that split into >1

    cur = con.cursor()
    for raw_line in raw_lines:
        if not raw_line.strip():
            continue
        try:
            d = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        offen = d.get("offen")
        if not offen:
            continue
        total_offen += 1
        zhash = sha256_line(raw_line)
        bauteil = d.get("bauteil")
        zeit = d.get("zeit")
        parts = split_offen(offen)
        if len(parts) > 1:
            split_counts.append((bauteil, len(parts)))
        for idx, part in enumerate(parts):
            total_rows += 1
            pid = f"{zhash[:16]}-{idx}"
            art = classify(part)
            cur.execute(
                "INSERT OR IGNORE INTO problem "
                "(id, bauteil, quelle, zeile_hash, text, art, erkannt_am, status) "
                "VALUES (?,?,?,?,?,?,?,'offen')",
                (pid, bauteil, PROTOKOLL, zhash, part, art, zeit),
            )
            if cur.rowcount == 1:
                inserted += 1
            else:
                already += 1
    con.commit()
    if verbose:
        print(f"offen-Felder gelesen: {total_offen}")
        print(f"Problem-Zeilen (nach Split): {total_rows}")
        print(f"neu eingefuegt: {inserted}, bereits vorhanden (idempotent): {already}")
        print(f"offen-Felder mit >1 Teil: {len(split_counts)}")
        for b, n in split_counts:
            print(f"  {b}: {n} Teile")
    return {"offen": total_offen, "rows": total_rows, "inserted": inserted, "already": already,
            "multi_split": split_counts}


def stand(con):
    print("-- nach art --")
    for row in con.execute("SELECT art, COUNT(*) FROM problem GROUP BY art ORDER BY art"):
        print(f"  {row[0]:14s} {row[1]}")
    print("-- nach bauteil --")
    for row in con.execute("SELECT bauteil, COUNT(*) FROM problem GROUP BY bauteil ORDER BY bauteil"):
        print(f"  {row[0]:8s} {row[1]}")
    print("-- nach status --")
    for row in con.execute("SELECT status, COUNT(*) FROM problem GROUP BY status ORDER BY status"):
        print(f"  {row[0]:8s} {row[1]}")
    total = con.execute("SELECT COUNT(*) FROM problem").fetchone()[0]
    print(f"gesamt: {total}")


def zu(con, bauteil):
    rows = con.execute(
        "SELECT id, art, status, erkannt_am, text FROM problem WHERE bauteil=? ORDER BY erkannt_am",
        (bauteil,),
    ).fetchall()
    for r in rows:
        print(f"[{r[1]:12s}] [{r[2]:5s}] {r[3]}  {r[0]}")
        print(f"    {r[4]}")
    print(f"({len(rows)} Zeilen)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ernten")
    sub.add_parser("stand")
    p_zu = sub.add_parser("zu")
    p_zu.add_argument("bauteil")
    args = ap.parse_args()

    con = connect_db()
    ensure_schema(con)
    if args.cmd == "ernten":
        ernten(con)
    elif args.cmd == "stand":
        stand(con)
    elif args.cmd == "zu":
        zu(con, args.bauteil)
    con.close()


if __name__ == "__main__":
    main()
