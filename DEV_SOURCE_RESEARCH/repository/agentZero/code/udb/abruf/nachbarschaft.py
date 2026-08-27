"""Messgeraet fuer den WALK -- das, was der Goldsatz nicht sehen kann.

WARUM ES DIESES ZWEITE GERAET BRAUCHT

Der Goldsatz misst Frage -> Dokument. Er wird auf Tiefe 0 entschieden: der
richtige Artikel wird ueber den Namen gefunden oder gar nicht. Der Graph-Walk
traegt zum Ergebnis nichts bei -- weshalb ZWEI verschiedene Walk-Reparaturen an
einem Tag (Kantengewichte, Kantenrichtung) exakt 0,0 Punkte Veraenderung
zeigten. Das war kein Beweis, dass sie nichts taugen, sondern dass das Geraet
sie nicht sieht.

WAS HIER GEMESSEN WIRD, OHNE UMWEG UEBER EINE FRAGE

    Erreichbarkeit: steht B im Walk von A aus, wenn A und B eine Kante teilen?

Keine Frageformulierung, kein Sprachmodell, keine Mehrdeutigkeit -- eine Kante
ist eine Kante. Damit ist die Zahl schwer zu beschoenigen, und genau darum geht
es. Getrennt ausgewiesen nach Richtung, denn dort sitzt der reparierte Fehler:

    vorwaerts    A -> B   ging schon immer
    rueckwaerts  B -> A   ging nie, betrifft 29,7 % der Artikel
"""
import sys, json, random, time, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

random.seed(20260818)


def paare(c, n=120):
    """Kantenpaare ziehen, getrennt nach Richtung, nur zwischen echten Artikeln."""
    vor, rueck = [], []
    rows = c.execute(
        "SELECT von, nach, art FROM kante WHERE COALESCE(verfallen,0)=0 "
        "AND art IN ('geschwister_verzeichnis','geschwister_datei','gleicher_inhalt') "
        "ORDER BY rowid LIMIT 40000").fetchall()
    random.shuffle(rows := list(rows))
    artikel = {r[0] for r in c.execute("SELECT id FROM artikel")}
    for von, nach, art in rows:
        if von not in artikel or nach not in artikel:
            continue
        if len(vor) < n:
            vor.append((von, nach, art))     # von A aus B finden -- vorwaerts
        elif len(rueck) < n:
            rueck.append((nach, von, art))   # von B aus A finden -- rueckwaerts
        else:
            break
    return vor, rueck


def messen(c, proben, marke):
    bias = {r["edge_art"]: r["gewicht"] for r in
            c.execute("SELECT edge_art,gewicht FROM vp_edge_lern WHERE query_class='global'")}
    treffer = 0
    leer = 0
    zeiten = []
    for start, ziel, _art in proben:
        t = time.perf_counter()
        rows = P._walk(c, start, bias)
        zeiten.append((time.perf_counter() - t) * 1000)
        ids = {r["record_id"] for r in rows}
        if not ids:
            leer += 1
        if ziel in ids:
            treffer += 1
    n = len(proben)
    print(f"  {marke:<34} erreicht {treffer:>3}/{n}  = {100*treffer/n:5.1f} %   "
          f"leere Walks {leer:>3}   median {statistics.median(zeiten):6.1f} ms")
    return 100 * treffer / n


if __name__ == "__main__":
    c = P._connect()
    P._ensure_vp_tables(c)
    vor, rueck = paare(c)
    print(f"=== {len(vor)} Vorwaertspaare, {len(rueck)} Rueckwaertspaare "
          f"(nur wechselseitige Kantenarten) ===\n")

    echt = P._SYMMETRISCHE_ARTEN
    P._SYMMETRISCHE_ARTEN = ()
    print("OHNE Symmetrie (Zustand vor der Reparatur):")
    a1 = messen(c, vor, "vorwaerts  A->B")
    a2 = messen(c, rueck, "rueckwaerts B->A")

    P._SYMMETRISCHE_ARTEN = echt
    print("\nMIT Symmetrie:")
    b1 = messen(c, vor, "vorwaerts  A->B")
    b2 = messen(c, rueck, "rueckwaerts B->A")

    print(f"\n=== Veraenderung ===")
    print(f"  vorwaerts  : {a1:5.1f} % -> {b1:5.1f} %   ({b1-a1:+.1f})")
    print(f"  rueckwaerts: {a2:5.1f} % -> {b2:5.1f} %   ({b2-a2:+.1f})")
    c.close()
