#!/usr/bin/env python3
"""
kanten.py — mechanical orphan-edge builder for wiki.db `kante`.

Zero model calls. Zero invention. Every edge's `beleg` names the exact
field/comparison that proves it. Reads artikel/datei/fundort READ-ONLY,
writes only to `kante` (composite PK von,nach,art). Owns exactly the
kante.art values listed in OWNED_ARTS below -- idempotent: `bauen` first
deletes any existing rows with those art values, then reinserts, so
re-running produces identical row counts (proof of idempotence is in
`pruefen`).

Tiers (decreasing evidence strength):
  T1 geschwister_datei       -- two+ artikel rows share the EXACT SAME
                                 quelle path (multiple records extracted
                                 from one file). Star topology per group,
                                 anchor = the group's manifest/report/index
                                 file if one is present by filename, else
                                 min(id). beleg names the shared quelle path.
  T2 geschwister_verzeichnis -- two+ artikel rows share the same
                                 dirname(quelle) but not full quelle (weak:
                                 same directory only). Star per dirname
                                 group, same anchor-preference rule.
  T3 gleicher_inhalt         -- two+ artikel rows share quell_hash (byte-
                                 identical source content ingested at two
                                 different locations/records). Star per
                                 hash group.
  T4 nachfolge_version       -- directed chain within a logical_id group
                                 (size>=2), ordered by date ascending.
                                 older -> newer ("this record supersedes
                                 that one" per the owner's SUPERSESSION
                                 framing).
  T5 eltern_hypothese        -- directed: artikel.metadaten.parent value
                                 resolves to another real artikel.id.
  T5 packet_referenz         -- directed: artikel.metadaten.packet_id
                                 resolves to another real artikel.id
                                 (self-loops dropped).
  T5 lauf_referenz           -- directed: artikel.metadaten.run_id
                                 resolves to another real artikel.id.

Subcommands:
  bauen     (re)build the OWNED_ARTS rows in kante from current artikel.
  stand     counts per owned art, before/after orphan comparison.
  pruefen   idempotence proof: run bauen twice, diff row sets, must be empty.
"""
import sys, os, json, sqlite3, time, argparse

# Modulgrenze: der LESE-Zweig oeffnet die Datenbank nicht mehr selbst.
# udb ist die Vordertuer fuer den nur-lesenden Fall; der Schreib-Zweig
# bleibt lokal, weil udb.verbindung() strukturell nur liest.
sys.path.insert(0, "/opt/unifieddb")
import udb
from collections import defaultdict, Counter
from datetime import datetime, timezone

DB_PATH = "/var/lib/clay/wiki.db"

OWNED_ARTS = [
    "geschwister_datei",
    "geschwister_verzeichnis",
    "gleicher_inhalt",
    "nachfolge_version",
    "eltern_hypothese",
    "packet_referenz",
    "lauf_referenz",
]

# filenames that make a good "star anchor" for a directory/file group --
# mechanical substring match on the basename, case-insensitive. Order = priority.
ANCHOR_PRIORITY = [
    "run_manifest", "run_report", "final_report", "receipt", "manifest",
    "readme", "index",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def connect_db(readonly=False):
    if readonly:
        con = udb.verbindung()
    else:
        con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    return con


def retry_locked(fn, tries=8, base_sleep=0.5):
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


def load_artikel(con):
    cols = ("id", "art", "quelle", "quell_hash", "logical_id", "metadaten",
            "erzeugt_am", "zuletzt_bearbeitet", "datum")
    rows = retry_locked(lambda: con.execute(
        f"SELECT {','.join(cols)} FROM artikel"
    ).fetchall())
    out = []
    for r in rows:
        out.append(dict(zip(cols, r)))
    return out


def anchor_of(members):
    """members: list of dicts with 'id','quelle'. Prefer a manifest/report/
    readme/index-named file as the star center; else the lexicographically
    smallest id (deterministic, no invention)."""
    def basename(quelle):
        if not quelle:
            return ""
        return quelle.rsplit("/", 1)[-1].lower()

    for pat in ANCHOR_PRIORITY:
        for m in members:
            if pat in basename(m.get("quelle")):
                return m
    return min(members, key=lambda m: m["id"])


def build_tier_t1_t2(artikel):
    """T1: exact-quelle groups. T2: dirname(quelle) groups (weak), minus
    pairs already covered by T1 (same exact quelle)."""
    by_quelle = defaultdict(list)
    by_dir = defaultdict(list)
    for a in artikel:
        q = a.get("quelle")
        if not q:
            continue
        by_quelle[q].append(a)
        d = q.rsplit("/", 1)[0] if "/" in q else ""
        if d:
            by_dir[d].append(a)

    t1_edges = []
    t1_pairs = set()  # frozenset({von,nach}) already linked by T1
    for quelle, members in by_quelle.items():
        if len(members) < 2:
            continue
        anchor = anchor_of(members)
        for m in members:
            if m["id"] == anchor["id"]:
                continue
            t1_edges.append((m["id"], anchor["id"], "geschwister_datei",
                              f"gleiche quelle-Datei: {quelle}"))
            t1_pairs.add(frozenset((m["id"], anchor["id"])))

    t2_edges = []
    for dirname, members in by_dir.items():
        if len(members) < 2:
            continue
        anchor = anchor_of(members)
        for m in members:
            if m["id"] == anchor["id"]:
                continue
            pair = frozenset((m["id"], anchor["id"]))
            if pair in t1_pairs:
                continue  # already linked by the stronger exact-file tier
            t2_edges.append((m["id"], anchor["id"], "geschwister_verzeichnis",
                              f"gleiches Verzeichnis: {dirname}"))
    return t1_edges, t2_edges


def build_tier_t3(artikel):
    by_hash = defaultdict(list)
    for a in artikel:
        h = a.get("quell_hash")
        if not h:
            continue
        by_hash[h].append(a)
    edges = []
    for h, members in by_hash.items():
        if len(members) < 2:
            continue
        anchor = anchor_of(members)
        for m in members:
            if m["id"] == anchor["id"]:
                continue
            edges.append((m["id"], anchor["id"], "gleicher_inhalt",
                           f"gleicher quell_hash: {h}"))
    return edges


def _sort_key(a):
    # prefer zuletzt_bearbeitet, fallback erzeugt_am, fallback datum, fallback id
    return (a.get("zuletzt_bearbeitet") or a.get("erzeugt_am") or a.get("datum") or "", a["id"])


def build_tier_t4(artikel):
    by_lid = defaultdict(list)
    for a in artikel:
        lid = a.get("logical_id")
        if not lid:
            continue
        by_lid[lid].append(a)
    edges = []
    for lid, members in by_lid.items():
        if len(members) < 2:
            continue
        ordered = sorted(members, key=_sort_key)
        for older, newer in zip(ordered, ordered[1:]):
            if older["id"] == newer["id"]:
                continue
            edges.append((older["id"], newer["id"], "nachfolge_version",
                           f"gleicher logical_id: {lid}, Datumsreihenfolge"))
    return edges


def build_tier_t5(artikel, all_ids):
    """Scan metadaten JSON of every artikel for keys parent/packet_id/run_id.
    Only keep values that resolve to a REAL artikel.id (rule 4), and never a
    self-loop."""
    field_to_art = {
        "parent": "eltern_hypothese",
        "packet_id": "packet_referenz",
        "run_id": "lauf_referenz",
    }
    edges = []
    per_field_seen = Counter()
    per_field_resolved = Counter()
    for a in artikel:
        meta = a.get("metadaten")
        if not meta:
            continue
        try:
            d = json.loads(meta)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for field, art in field_to_art.items():
            if field not in d:
                continue
            per_field_seen[field] += 1
            v = d[field]
            if not isinstance(v, str):
                continue
            if v == a["id"]:
                continue  # self-loop, drop
            if v in all_ids:
                per_field_resolved[field] += 1
                edges.append((a["id"], v, art, f"metadaten.{field}"))
    return edges, per_field_seen, per_field_resolved


def build_all(con):
    artikel = load_artikel(con)
    all_ids = set(a["id"] for a in artikel)
    t1, t2 = build_tier_t1_t2(artikel)
    t3 = build_tier_t3(artikel)
    t4 = build_tier_t4(artikel)
    t5, f_seen, f_resolved = build_tier_t5(artikel, all_ids)

    all_edges = t1 + t2 + t3 + t4 + t5

    # rule 4 hard check
    bad = [e for e in all_edges if e[0] not in all_ids or e[1] not in all_ids]
    assert not bad, f"BUG: {len(bad)} edges with unresolved endpoint(s): {bad[:5]}"
    # no self loops
    bad2 = [e for e in all_edges if e[0] == e[1]]
    assert not bad2, f"BUG: {len(bad2)} self-loop edges: {bad2[:5]}"

    stats = {
        "geschwister_datei": len(t1),
        "geschwister_verzeichnis": len(t2),
        "gleicher_inhalt": len(t3),
        "nachfolge_version": len(t4),
        "eltern_hypothese": sum(1 for e in t5 if e[2] == "eltern_hypothese"),
        "packet_referenz": sum(1 for e in t5 if e[2] == "packet_referenz"),
        "lauf_referenz": sum(1 for e in t5 if e[2] == "lauf_referenz"),
        "_field_seen": dict(f_seen),
        "_field_resolved": dict(f_resolved),
    }
    return all_edges, stats


def cmd_bauen(args):
    con = connect_db()
    try:
        edges, stats = build_all(con)
        con.execute("BEGIN")
        placeholders = ",".join("?" * len(OWNED_ARTS))
        before = con.execute(
            f"SELECT COUNT(*) FROM kante WHERE art IN ({placeholders})", OWNED_ARTS
        ).fetchone()[0]
        con.execute(f"DELETE FROM kante WHERE art IN ({placeholders})", OWNED_ARTS)
        con.executemany(
            "INSERT OR IGNORE INTO kante(von, nach, art, beleg) VALUES (?,?,?,?)",
            edges,
        )
        after = con.execute(
            f"SELECT COUNT(*) FROM kante WHERE art IN ({placeholders})", OWNED_ARTS
        ).fetchone()[0]
        con.commit()
        print(f"vorher (owned arts rows): {before}")
        print(f"eingefuegt (dedup nach PK): {after}")
        print("stats:", json.dumps(stats, indent=2, ensure_ascii=False))
    finally:
        con.close()


def cmd_stand(args):
    con = connect_db(readonly=True)
    try:
        total = con.execute("SELECT COUNT(*) FROM artikel").fetchone()[0]
        orphans = con.execute("""
          SELECT COUNT(*) FROM artikel a
          WHERE NOT EXISTS (SELECT 1 FROM kante k WHERE k.von=a.id OR k.nach=a.id)
        """).fetchone()[0]
        print(f"artikel gesamt: {total}")
        print(f"waisen: {orphans} ({100*orphans/total:.2f}%)")
        print()
        print("orphans per art:")
        for art, cnt in con.execute(
            "SELECT art, COUNT(*) FROM artikel GROUP BY art ORDER BY 2 DESC"
        ).fetchall():
            orph = con.execute("""
              SELECT COUNT(*) FROM artikel a WHERE a.art=?
              AND NOT EXISTS (SELECT 1 FROM kante k WHERE k.von=a.id OR k.nach=a.id)
            """, (art,)).fetchone()[0]
            if orph:
                print(f"  {art}: {orph}/{cnt} ({100*orph/cnt:.1f}%)")
        print()
        print("kante rows per art:")
        for art, cnt in con.execute(
            "SELECT art, COUNT(*) FROM kante GROUP BY art ORDER BY 2 DESC"
        ).fetchall():
            print(f"  {art}: {cnt}")
        print()
        print("kante total:", con.execute("SELECT COUNT(*) FROM kante").fetchone()[0])
    finally:
        con.close()


def cmd_pruefen(args):
    """Idempotence proof: build, snapshot owned rows, build again, diff."""
    con = connect_db()
    try:
        placeholders = ",".join("?" * len(OWNED_ARTS))

        def snapshot():
            rows = con.execute(
                f"SELECT von,nach,art,beleg FROM kante WHERE art IN ({placeholders}) ORDER BY von,nach,art",
                OWNED_ARTS,
            ).fetchall()
            return rows

        edges, _ = build_all(con)
        con.execute("BEGIN")
        con.execute(f"DELETE FROM kante WHERE art IN ({placeholders})", OWNED_ARTS)
        con.executemany("INSERT OR IGNORE INTO kante(von,nach,art,beleg) VALUES (?,?,?,?)", edges)
        con.commit()
        snap1 = snapshot()

        edges2, _ = build_all(con)
        con.execute("BEGIN")
        con.execute(f"DELETE FROM kante WHERE art IN ({placeholders})", OWNED_ARTS)
        con.executemany("INSERT OR IGNORE INTO kante(von,nach,art,beleg) VALUES (?,?,?,?)", edges2)
        con.commit()
        snap2 = snapshot()

        print("run1 rows:", len(snap1), " run2 rows:", len(snap2))
        print("identical:", snap1 == snap2)
        if snap1 != snap2:
            s1, s2 = set(snap1), set(snap2)
            print("only in run1:", list(s1 - s2)[:5])
            print("only in run2:", list(s2 - s1)[:5])
    finally:
        con.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bauen")
    sub.add_parser("stand")
    sub.add_parser("pruefen")
    args = ap.parse_args()
    {"bauen": cmd_bauen, "stand": cmd_stand, "pruefen": cmd_pruefen}[args.cmd](args)
