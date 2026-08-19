#!/usr/bin/env python3
"""
adapter.py — READ-ONLY bridge from EntityOS wiki.db to the invariants engine.

The invariants engine (engine/energy.py, engine/entropy.py, engine/core_kernel.py)
expects a "titan_store" object with a `.sqlite._get_conn()` context manager that
yields a sqlite3 connection exposing tables named `nodes` and `edges` (and,
optionally, `claims`) with specific columns (id/label/confidence/created_at,
src/dst/relation).

wiki.db (EntityOS' real knowledge base, /var/lib/clay/wiki.db) uses different,
German-language table/column names:

    artikel(id, titel, konfidenz, erzeugt_am, verfallen, protected, ...)
        -> one row per knowledge article. This is the closest analogue of
           Titan's "nodes". konfidenz is NULL for ~99% of rows (only 184/17797
           articles carry an explicit confidence) -> defaulted to 0.5, exactly
           like the original engine already does for its own "nodes" table.

    kante(von, nach, art, konfidenz, erzeugt_am, verfallen, ...)
        -> directed edges between articles. This is the closest analogue of
           Titan's "edges". `art` (edge kind) already contains real
           contradiction-shaped relations in production data:
             - 'widerspricht' (German: "contradicts")  — 20 edges
             - 'attacks'                                — 20 edges
           Both are remapped to the literal string 'contradicts' so the
           engine's built-in contradiction detector
           (entropy.py: `relation IN ('contradicts','conflicts_with','negates')`)
           finds them without any invented semantics.

There is NO separate "claims" table in wiki.db — articles already carry
confidence directly (unlike Titan's subject/predicate/object claims). No
`claims` view is created; the engine's `SELECT ... FROM claims` queries hit
"no such table" and are silently skipped (this is existing, expected behavior
in the upstream code, wrapped in try/except).

SAFETY — enforced twice, independently:
  1. The sqlite3 connection is opened with `mode=ro` in the URI. SQLite
     refuses ANY write on such a connection at the driver level
     ("attempt to write a readonly database"), regardless of what SQL the
     engine code above us tries to run.
  2. `nodes`/`edges` are SQLite VIEWs (not real tables), so even an UPDATE/
     DELETE that somehow reached them would additionally fail with
     "cannot modify <x> because it is a view" before the read-only check is
     even reached.
  3. Views are created as TEMP views. TEMP objects live in SQLite's private
     temp database attached to the connection (usually an anonymous temp
     file or memory, controlled by SQLite itself) -- they are NEVER written
     into wiki.db itself, and creating them does not require (and is not
     blocked by) the main database's read-only flag.

This adapter never opens wiki.db for writing, never calls the engine's
mutating methods (enforce_conservation / soft_consolidation /
hard_consolidation / quarantine_* / restore_item / _reduce_confidence),
and does not use immutable=1 (so it correctly reads through wiki.db's WAL
file while clayverse-wikiarbeit.service is writing, instead of risking a
stale/pre-checkpoint snapshot).
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Edge kinds in `kante.art` that already express a real contradiction in the
# production data (verified against wiki.db on 2026-08-19: 20 'widerspricht'
# + 20 'attacks' edges). Nothing invented -- these are the two kinds present.
CONTRADICTION_EDGE_KINDS = ("widerspricht", "attacks")

_VIEW_SQL = """
CREATE TEMP VIEW IF NOT EXISTS nodes AS
    SELECT
        id                          AS id,
        titel                       AS label,
        COALESCE(konfidenz, 0.5)    AS confidence,
        erzeugt_am                  AS created_at,
        art                         AS type
    FROM artikel
    WHERE verfallen = 0;

CREATE TEMP VIEW IF NOT EXISTS edges AS
    SELECT
        von                         AS src,
        nach                        AS dst,
        CASE WHEN art IN ({placeholders}) THEN 'contradicts' ELSE art END
                                     AS relation
    FROM kante
    WHERE verfallen = 0;
""".format(placeholders=",".join("'%s'" % k for k in CONTRADICTION_EDGE_KINDS))


class ReadOnlyWikiAccessor:
    """Mimics Titan's `titan_store.sqlite` accessor: `._get_conn()` context manager."""

    def __init__(self, db_path):
        self.db_path = str(Path(db_path).resolve())

    @contextmanager
    def _get_conn(self):
        uri = f"file:{self.db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(_VIEW_SQL)
            yield conn
        finally:
            conn.close()


class WikiDBTitanAdapter:
    """
    Drop-in replacement for Frank's `tools.titan.titan_core.get_titan()` object,
    backed by EntityOS' wiki.db instead of a Titan knowledge store.

    Only exposes `.sqlite` (the attribute every engine module actually uses).
    No write path exists anywhere on this object.
    """

    def __init__(self, db_path="/var/lib/clay/wiki.db"):
        self.sqlite = ReadOnlyWikiAccessor(db_path)
        self.db_path = db_path

    def describe(self):
        with self.sqlite._get_conn() as conn:
            n_articles = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            n_edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            n_contra = conn.execute(
                "SELECT COUNT(*) FROM edges WHERE relation = 'contradicts'"
            ).fetchone()[0]
        return {
            "source": self.db_path,
            "articles_as_nodes": n_articles,
            "edges": n_edges,
            "contradiction_edges": n_contra,
        }


def get_titan(db_path="/var/lib/clay/wiki.db"):
    return WikiDBTitanAdapter(db_path)


if __name__ == "__main__":
    import json
    t = get_titan()
    print(json.dumps(t.describe(), indent=2))
