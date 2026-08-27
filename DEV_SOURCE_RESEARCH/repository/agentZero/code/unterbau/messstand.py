#!/usr/bin/env python3
"""messstand.py — misst drei Wege zur selben Antwort.

grep      ueber die Rohdateien, kein Index, kein Zusammenhang
fts       nur Wortsuche im Index
voll      Artikel + Kanten beidseitig + Metadaten + Kuration + Gegenseite

Gemessen wird je Weg: Millisekunden, zurueckgegebene Bytes, und wie viele
belegte Fakten in der Antwort stecken. Dichte = Fakten je 1000 Token.
Token, nicht Zeichen.
"""
import json, os, subprocess, sys, time

# Modulgrenze: dieses Werkzeug oeffnet die Datenbank NICHT mehr selbst.
# udb ist die Vordertuer -- busy_timeout, query_only und Wiederholung
# stehen dort an EINER Stelle statt hier noch einmal.
sys.path.insert(0, "/opt/unifieddb")
import udb
KORPUS = "/opt/clayverse/baeume/clay-global-research-entity/research_entity"

FRAGEN = [
    ("F1", "widerlegte Behauptungen",
     "Wie viele Behauptungen sind widerlegt und wie viele gelten noch?", "REFUTED"),
    ("F2", "EffectGate",
     "Was ist ueber das EffectGate bekannt und was ist daran offen?", "EffectGate"),
    ("F3", "Nutzen des Graphen",
     "Welche Messung belegt den Nutzen des Graphen?", "HYBRID"),
    ("F4", "Gegenhypothesen",
     "Welche Aussagen widersprechen einander?", "NEGATIVE_RESULT"),
    ("F5", "Herkunft",
     "Wer hat zuletzt an den Wissenspaketen gearbeitet?", "packet_id"),
]


def ms(t0):
    return (time.perf_counter() - t0) * 1000


def weg_grep(wort):
    t0 = time.perf_counter()
    r = subprocess.run(["grep", "-rl", "--include=*.md", "--include=*.json",
                        "--include=*.jsonl", wort, KORPUS],
                       capture_output=True, text=True, timeout=300)
    aus = r.stdout
    return ms(t0), len(aus.encode()), aus.count("\n"), 0


def weg_fts(con, wort):
    t0 = time.perf_counter()
    try:
        rows = con.execute(
            "SELECT a.id, a.titel FROM fts_index_artikel f "
            "JOIN artikel_suchtext s ON s.id = f.rowid "
            "JOIN artikel a ON a.id = s.artikel_id "
            "WHERE fts_index_artikel MATCH ? LIMIT 20", (wort,)).fetchall()
    except Exception:
        rows = con.execute(
            "SELECT id, titel FROM artikel WHERE titel LIKE ? OR metadaten LIKE ? LIMIT 20",
            (f"%{wort}%", f"%{wort}%")).fetchall()
    aus = json.dumps(rows, ensure_ascii=False)
    return ms(t0), len(aus.encode()), len(rows), len(rows)


def weg_voll(con, wort):
    """Ein Aufruf: Treffer + Kanten beidseitig + Metadaten + Kuration + Probleme."""
    t0 = time.perf_counter()
    try:
        treffer = [r[0] for r in con.execute(
            "SELECT a.id FROM fts_index_artikel f "
            "JOIN artikel_suchtext s ON s.id = f.rowid "
            "JOIN artikel a ON a.id = s.artikel_id "
            "WHERE fts_index_artikel MATCH ? LIMIT 8", (wort,))]
    except Exception:
        treffer = [r[0] for r in con.execute(
            "SELECT id FROM artikel WHERE titel LIKE ? LIMIT 8", (f"%{wort}%",))]
    ergebnis, fakten = [], 0
    for aid in treffer:
        a = con.execute(
            "SELECT id,art,titel,quelle,datum,zuletzt_bearbeitet,zuletzt_von,"
            "epistemic_class,status,projekt,logical_id FROM artikel WHERE id=?",
            (aid,)).fetchone()
        if not a:
            continue
        kanten = con.execute(
            "SELECT von,nach,art FROM kante WHERE von=? OR nach=? LIMIT 24",
            (aid, aid)).fetchall()
        kur = con.execute(
            "SELECT klasse,status FROM kuration WHERE artikel_id=?", (aid,)).fetchall()
        fakten += sum(1 for x in a if x not in (None, "")) + len(kanten) + len(kur)
        ergebnis.append({"a": a, "k": kanten, "kur": kur})
    aus = json.dumps(ergebnis, ensure_ascii=False, default=str)
    return ms(t0), len(aus.encode()), len(treffer), fakten


def main():
    con = udb.verbindung()
    print(f"{'Frage':4} {'Weg':6} {'ms':>10} {'Bytes':>10} {'Treffer':>8} {'Fakten':>7}")
    print("-" * 52)
    gesamt = {}
    for kuerzel, name, frage, wort in FRAGEN:
        for weg, fn in (("grep", lambda w: weg_grep(w)),
                        ("fts", lambda w: weg_fts(con, w)),
                        ("voll", lambda w: weg_voll(con, w))):
            try:
                d, b, t, f = fn(wort)
            except Exception as e:
                print(f"{kuerzel:4} {weg:6} FEHLER {e}")
                continue
            print(f"{kuerzel:4} {weg:6} {d:10.2f} {b:10} {t:8} {f:7}")
            g = gesamt.setdefault(weg, [0, 0, 0, 0])
            g[0] += d; g[1] += b; g[2] += t; g[3] += f
    print("-" * 52)
    for weg, g in gesamt.items():
        print(f"{'SUM':4} {weg:6} {g[0]:10.2f} {g[1]:10} {g[2]:8} {g[3]:7}")
    json.dump({k: v for k, v in gesamt.items()},
              open("/var/lib/clay/messstand-ergebnis.json", "w"))


if __name__ == "__main__":
    main()
