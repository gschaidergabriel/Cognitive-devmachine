#!/usr/bin/env python3
"""
ClayVerse Messung — mechanische Zahlenextraktion aus dem Bauprotokoll.

Mechanical only. No model calls, no network calls, stdlib only (sqlite3,
hashlib, re, json). Reads /opt/clayverse/bau/protokoll.jsonl (one JSON
object per line) and the `ergebnis` prose field of each entry, and
regex-extracts NUMBER+UNIT pairs against a fixed, known unit whitelist.
Writes only ONE new table (messung) + ONE view (messung_kompakt) into
/var/lib/clay/wiki.db. Never touches artikel/kante/kuration/anreicherung/
fts_*/datei/fundort -- this tool does not even SELECT from them.

Extraction rule: a number is only extracted if it is immediately followed
by a whitespace and a unit from UNITS below. No unit -> not extracted.
No exceptions, no model-assisted guessing. See `stand --skipped` reasoning
in the build report; the skip list is deliberately large (the corpus is
full of IPs, ports, version numbers, ratios like "5/6", timestamps -- all
correctly left alone).

Subcommands:
  bauen           (re)extract into messung, idempotent full rebuild
  stand           counts per bauteil / unit
  zu <bauteil>    condensed facts (was/wert/einheit/zeit/quelle) for one
                  Bauteil, via the messung_kompakt view
"""
import sys, os, re, json, sqlite3, hashlib, time, argparse

# Modulgrenze: der LESE-Zweig oeffnet die Datenbank nicht mehr selbst.
# udb ist die Vordertuer fuer den nur-lesenden Fall; der Schreib-Zweig
# bleibt lokal, weil udb.verbindung() strukturell nur liest.
sys.path.insert(0, "/opt/unifieddb")
import udb
from datetime import datetime, timezone

DB_PATH = "/var/lib/clay/wiki.db"
PROTOKOLL_PATH = "/opt/clayverse/bau/protokoll.jsonl"

# --- known unit whitelist ---------------------------------------------------
# Owner-given seed: ms, µs/us, s, %, MB, KB, Bytes, Zeilen, Knoten, Kanten,
# Artikel, Commits. Extended by 3 direct siblings of those same families,
# flagged explicitly in the report: GB (sibling of MB/KB/Bytes -- size),
# min (sibling of s/ms/us -- time), USD (currency value, same "number unit"
# shape). Nothing else added; anything not in this list is skipped, not
# guessed.
UNITS = ["ms", "us", "s", "%", "MB", "KB", "GB", "Bytes",
         "Zeilen", "Knoten", "Kanten", "Artikel", "Commits", "USD", "min"]
UNITS_SORTED = sorted(set(UNITS), key=len, reverse=True)
UNIT_ALT = "|".join(re.escape(u) for u in UNITS_SORTED)

NUM_RE = r"(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)"
# Bug caught during dev (see report): a trailing \b after a symbol unit
# like "%" never fires -- \b needs a word<->non-word transition and both
# "%" and the following space/punctuation are non-word, so \b silently
# swallowed every percent measurement. Fixed with an explicit
# "next char is not alnum" lookahead. The µs (micro sign, U+00B5) branch
# is matched separately and normalized to "us" (character-level Unicode
# normalization only, not a semantic reinterpretation of the unit).
PAIR_RE = re.compile(
    r"(?P<num>" + NUM_RE + r") (?:µs|(?P<unit>" + UNIT_ALT + r"))(?![A-Za-zÀ-ÿ0-9])"
)

# Boundary = a real clause break. Comma/semicolon/colon/period only count
# when followed by whitespace (protects German decimal commas "15,7" and
# thousands-grouping dots "1.089.536", neither of which has surrounding
# whitespace). Parentheses always count immediately -- they never occur
# inside a number.
BOUNDARY_RE = re.compile(r"[,;:]\s|\.\s|[()]")
LABEL_MAXLEN = 100

# ---------------------------------------------------------------- utilities

def connect_db(readonly=False):
    if readonly:
        con = udb.verbindung()
    else:
        con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    return con


def retry_locked(fn, tries=6, base_sleep=0.5):
    last = None
    for i in range(tries):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                last = e
                time.sleep(base_sleep * (i + 1))
                continue
            raise
    raise last


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def ensure_schema(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS messung(
            id TEXT PRIMARY KEY,
            bauteil TEXT NOT NULL,
            quelle TEXT NOT NULL,
            zeile_hash TEXT NOT NULL,
            was TEXT NOT NULL,
            wert REAL NOT NULL,
            einheit TEXT NOT NULL,
            zeit TEXT NOT NULL,
            wirt TEXT,
            instanz TEXT,
            roh TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messung_bauteil ON messung(bauteil);
        CREATE INDEX IF NOT EXISTS idx_messung_einheit ON messung(einheit);
        CREATE INDEX IF NOT EXISTS idx_messung_zeile ON messung(zeile_hash);
        CREATE TABLE IF NOT EXISTS messung_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    # The view IS the condensation surface the owner asked for: one row =
    # label + value + unit + date + source, nothing else. It is a plain
    # SELECT over `messung`, not a JOIN against a second table, because
    # protokoll.jsonl is a flat file (not a SQL table anywhere in wiki.db)
    # and the only two candidate join targets that DO live in wiki.db --
    # `datei`/`fundort` -- are currently EMPTY (0 rows each) and are keyed
    # by whole-file checksum/path, not by JSONL line, so there is nothing
    # real to join against without inventing an assumption about how a
    # future agent will populate them. `messung` already carries bauteil/
    # zeit/wirt/instanz/quelle per row (by design, matching the exact
    # column list given), so the "combined with its protocol context"
    # requirement is satisfied by that denormalization at extraction time,
    # not by a JOIN keyword. Flagged in the build report for the
    # coordinator to correct if a literal multi-table JOIN was intended.
    con.executescript("""
        DROP VIEW IF EXISTS messung_kompakt;
        CREATE VIEW messung_kompakt AS
        SELECT
            bauteil AS bauteil,
            was     AS was,
            wert    AS wert,
            einheit AS einheit,
            zeit    AS zeit,
            quelle  AS quelle
        FROM messung
        ORDER BY zeit DESC, bauteil;
    """)
    con.commit()


def parse_number(s):
    return float(s.replace(".", "").replace(",", "."))


def label_for(ergebnis, start, titel):
    ends = [m.end() for m in BOUNDARY_RE.finditer(ergebnis) if m.end() <= start]
    ends.append(0)
    ends.sort()
    for e in reversed(ends):
        label = ergebnis[e:start].strip().strip("()").strip()
        if label:
            return label, e, False
    return titel, None, True  # fallback: titel verbatim, number sits at pos 0


def extract_line(ergebnis, titel):
    """Mechanical, regex-only. Returns a list of dicts, one per matched
    NUMBER+UNIT pair. Never invents a label; never emits a number with no
    matched unit."""
    out = []
    for m in PAIR_RE.finditer(ergebnis):
        num_s = m.group("num")
        matched_text = m.group(0)
        unit_s = m.group("unit")
        if unit_s is None:
            unit_s = "us"  # the µs branch has no named group hit
        wert = parse_number(num_s)
        was, e, used_fallback = label_for(ergebnis, m.start(), titel)
        was_disp = was if len(was) <= LABEL_MAXLEN else "…" + was[-LABEL_MAXLEN:]
        roh = (titel + " :: " + matched_text) if used_fallback else ergebnis[e:m.end()]
        out.append({
            "was": was_disp, "wert": wert, "einheit": unit_s, "roh": roh,
            "start": m.start(),
        })
    return out


def row_id(zeile_hash, start, einheit, wert):
    h = hashlib.sha256(f"{zeile_hash}|{start}|{einheit}|{wert}".encode("utf-8")).hexdigest()
    return f"m_{h[:32]}"

# ---------------------------------------------------------------- bauen

def cmd_bauen(args):
    t0 = time.time()
    if not os.path.exists(PROTOKOLL_PATH):
        raise SystemExit(f"protokoll not found: {PROTOKOLL_PATH}")

    rows = []
    total_lines = 0
    parse_errors = 0
    with open(PROTOKOLL_PATH, encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, 1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            total_lines += 1
            zeile_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            ergebnis = d.get("ergebnis") or ""
            titel = d.get("titel") or ""
            bauteil = d.get("bauteil") or ""
            zeit = d.get("zeit") or ""
            wirt = d.get("wirt")
            instanz = d.get("instanz")
            quelle = f"{PROTOKOLL_PATH}:{lineno}"
            for m in extract_line(ergebnis, titel):
                rid = row_id(zeile_hash, m["start"], m["einheit"], m["wert"])
                rows.append((
                    rid, bauteil, quelle, zeile_hash, m["was"], m["wert"],
                    m["einheit"], zeit, wirt, instanz, m["roh"],
                ))

    con = retry_locked(lambda: connect_db(readonly=False))
    try:
        db_size_before = os.path.getsize(DB_PATH)
        ensure_schema(con)

        con.execute("BEGIN")
        con.execute("DELETE FROM messung")
        con.executemany(
            "INSERT INTO messung(id,bauteil,quelle,zeile_hash,was,wert,"
            "einheit,zeit,wirt,instanz,roh) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        con.execute(
            "INSERT INTO messung_meta(key,value) VALUES('built_at',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (now_iso(),),
        )
        con.execute(
            "INSERT INTO messung_meta(key,value) VALUES('source_lines',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(total_lines),),
        )
        con.commit()

        by_unit = {}
        for r in rows:
            by_unit[r[6]] = by_unit.get(r[6], 0) + 1

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        db_size_after = os.path.getsize(DB_PATH)
        print(json.dumps({
            "source_lines": total_lines,
            "json_parse_errors": parse_errors,
            "rows_written": len(rows),
            "rows_by_unit": by_unit,
            "build_runtime_ms": elapsed_ms,
            "db_size_before_bytes": db_size_before,
            "db_size_after_bytes": db_size_after,
        }, indent=2, ensure_ascii=False))
    finally:
        con.close()

# ---------------------------------------------------------------- stand

def cmd_stand(args):
    con = retry_locked(lambda: connect_db(readonly=True))
    try:
        by_bauteil = con.execute(
            "SELECT bauteil, COUNT(*) FROM messung GROUP BY bauteil ORDER BY 2 DESC"
        ).fetchall()
        by_unit = con.execute(
            "SELECT einheit, COUNT(*) FROM messung GROUP BY einheit ORDER BY 2 DESC"
        ).fetchall()
        meta = dict(con.execute("SELECT key,value FROM messung_meta").fetchall())
        total = con.execute("SELECT COUNT(*) FROM messung").fetchone()[0]
        print(json.dumps({
            "meta": meta,
            "total_rows": total,
            "by_bauteil": dict(by_bauteil),
            "by_einheit": dict(by_unit),
        }, indent=2, ensure_ascii=False))
    finally:
        con.close()

# ---------------------------------------------------------------- zu

def cmd_zu(args):
    t0 = time.time()
    con = retry_locked(lambda: connect_db(readonly=True))
    try:
        rows = con.execute(
            "SELECT bauteil, was, wert, einheit, zeit, quelle "
            "FROM messung_kompakt WHERE bauteil=?",
            (args.bauteil,),
        ).fetchall()
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        out = [
            {"bauteil": b, "was": w, "wert": v, "einheit": e, "zeit": z, "quelle": q}
            for (b, w, v, e, z, q) in rows
        ]
        print(json.dumps({
            "bauteil": args.bauteil,
            "count": len(out),
            "ms": elapsed_ms,
            "facts": out,
        }, indent=2, ensure_ascii=False))
    finally:
        con.close()

# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description="ClayVerse Messung")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("bauen", help="(re)extract from protokoll.jsonl into messung").set_defaults(func=cmd_bauen)
    sub.add_parser("stand", help="counts per bauteil/unit").set_defaults(func=cmd_stand)

    p_zu = sub.add_parser("zu", help="condensed facts for one Bauteil")
    p_zu.add_argument("bauteil")
    p_zu.set_defaults(func=cmd_zu)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
