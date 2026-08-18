#!/usr/bin/env python3
"""Seltenheitsmassstab fuer Alias-Woerter (vp_alias_df).

WARUM. Die bisherige Bewertung kennt nur DECKUNG: wie viel Prozent der Woerter
eines Alias in der Frage vorkommen. Damit ist ein Treffer auf "die" genauso viel
wert wie ein Treffer auf "unifieddb" -- und weil lange Dateinamen-Aliasse viele
Woerter haben, koennen sie die Schwelle 2,5 strukturell nie erreichen.
Gemessen: max. erreichbarer Score fuer einen dreiwortigen Alias mit einem
Treffer = 2*0,33 + 1,0 = 1,67. Die Schwelle liegt bei 2,5.

Was fehlt, ist SPEZIFITAET: ein Wort, das nur in drei von 358.280 Aliassen
vorkommt, ist ein starker Beleg. Eines, das in 90.000 vorkommt, ist keiner.
Diese Tabelle haelt genau das fest -- einmal berechnet, danach nachgeschlagen.

Sie wird bewusst als eigene Tabelle gebaut und nicht bei jeder Frage gezaehlt:
ein COUNT ueber 358.280 Zeilen je Suchwort waere der Latenz-Ruin.
"""
import sys, re, time, collections
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

SCHEMA = """
CREATE TABLE IF NOT EXISTS vp_alias_df (
  wort TEXT PRIMARY KEY,
  df INTEGER NOT NULL,          -- in wie vielen Aliassen kommt das Wort vor
  gebaut_am TEXT
);
CREATE INDEX IF NOT EXISTS idx_vp_alias_df_df ON vp_alias_df(df);
"""


def bauen(c=None, mindest_df: int = 1) -> dict:
    eigen = c is None
    c = c or P._connect()
    c.executescript(SCHEMA)
    t = time.perf_counter()
    zaehler = collections.Counter()
    n_alias = 0
    for (an,) in c.execute("SELECT alias_norm FROM vp_alias"):
        n_alias += 1
        # Dieselbe Zerlegung wie die Abfrage sie nutzt -- sonst zaehlt man
        # andere Woerter, als spaeter nachgeschlagen werden.
        zaehler.update(set(P._tokens(an or "")))
    jetzt = P._now()
    c.execute("DELETE FROM vp_alias_df")
    c.executemany("INSERT INTO vp_alias_df(wort,df,gebaut_am) VALUES(?,?,?)",
                  [(w, n, jetzt) for w, n in zaehler.items() if n >= mindest_df])
    c.commit()
    dauer = time.perf_counter() - t
    if eigen:
        c.close()
    return {"aliasse": n_alias, "woerter": len(zaehler), "sekunden": round(dauer, 1)}


if __name__ == "__main__":
    print(bauen())
    c = P._ro()
    print("\n=== Seltenste und haeufigste Woerter ===")
    for r in c.execute("SELECT wort,df FROM vp_alias_df ORDER BY df DESC LIMIT 8"):
        print(f"  haeufig  {r[1]:>7}  {r[0][:40]}")
    for r in c.execute("SELECT wort,df FROM vp_alias_df WHERE df<=2 LIMIT 4"):
        print(f"  selten   {r[1]:>7}  {r[0][:40]}")
    for w in ("unifieddb", "die", "was", "clayverse", "feuerschneise"):
        r = c.execute("SELECT df FROM vp_alias_df WHERE wort=?", (w,)).fetchone()
        print(f"  df({w:<14}) = {r[0] if r else 'fehlt'}")
    c.close()
