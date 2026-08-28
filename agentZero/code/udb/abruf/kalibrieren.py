"""Schwelle bestimmen -- auf Haelfte A, berichtet wird auf Haelfte B.

⭐ DIE REGEL STEHT VOR DER MESSUNG, NICHT DANACH

    Zulaessig ist nur eine Schwelle, deren GENAUIGKEIT (Anteil richtiger unter
    den gesetzten Ankern) nicht unter die Grundlinie faellt: 60 %.
    Unter dieser Nebenbedingung wird die AUSBEUTE maximiert.

Ohne diese Vorab-Regel waere die Kalibrierung nur eine Suche nach der Zahl, die
das Ergebnis am besten aussehen laesst. Und Haelfte B wird waehrend der Suche
nicht angefasst -- eine Schwelle, die auf demselben Satz gewaehlt und geprueft
wird, misst nur, wie gut man raten kann.
"""
import sys, json, time, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

GOLD = "/opt/unifieddb/udb/abruf/goldsatz.json"
GRUNDLINIE_GENAUIGKEIT = 60.0


def lauf(satz, c) -> dict:
    mit = treff = auffind = 0
    zeiten = []
    for e in satz:
        t = time.perf_counter()
        pk = P.paket(e["frage"], conn=c)
        zeiten.append((time.perf_counter() - t) * 1000)
        anker = tuple(pk["resolution"].get("anker") or ())
        if anker:
            mit += 1
            if e["erwartet"] in anker:
                treff += 1
        if e["erwartet"] in {t.get("id") for t in pk.get("treffer", []) if isinstance(t, dict)}:
            auffind += 1
    n = len(satz)
    return {
        "ankerquote": round(100 * mit / n, 1),
        "genauigkeit": round(100 * treff / mit, 1) if mit else 0.0,
        "ausbeute": round(100 * treff / n, 1),
        "auffindbar": round(100 * auffind / n, 1),
        "median_ms": round(statistics.median(zeiten), 1),
    }


if __name__ == "__main__":
    satz = json.load(open(GOLD, encoding="utf-8"))
    A = [e for i, e in enumerate(satz) if i % 2 == 0]
    B = [e for i, e in enumerate(satz) if i % 2 == 1]
    print(f"Kalibrierhaelfte A: {len(A)} Fragen | Pruefhaelfte B: {len(B)} Fragen (waehrend der Suche unberuehrt)")
    c = P._connect()
    P._ensure_vp_tables(c)

    print("\n=== Suche auf A ===")
    print(f"{'Schwelle':>9} {'Bonus':>6} {'Anker%':>7} {'Genau%':>7} {'Ausb%':>6} {'Auffind%':>9}")
    beste, bestwert = None, -1.0
    for bonus in (1.6, 2.0, 2.4, 3.0):
        for schwelle in (2.0, 2.2, 2.5, 2.8, 3.2, 3.6):
            P._SPEZ_BONUS = bonus
            P._ALIAS_MIN_SCORE = schwelle
            r = lauf(A, c)
            passt = r["genauigkeit"] >= GRUNDLINIE_GENAUIGKEIT
            marke = "  <= zulaessig" if passt else ""
            print(f"{schwelle:>9} {bonus:>6} {r['ankerquote']:>7} {r['genauigkeit']:>7} "
                  f"{r['ausbeute']:>6} {r['auffindbar']:>9}{marke}")
            if passt and r["ausbeute"] > bestwert:
                bestwert, beste = r["ausbeute"], (schwelle, bonus, r)

    if not beste:
        print("\n!! Keine Einstellung haelt die Genauigkeitsgrenze. Nichts wird uebernommen.")
        c.close(); sys.exit(0)

    schwelle, bonus, rA = beste
    print(f"\n=== Gewaehlt auf A: Schwelle={schwelle} Bonus={bonus} (Ausbeute {rA['ausbeute']} %) ===")
    P._SPEZ_BONUS = bonus
    P._ALIAS_MIN_SCORE = schwelle
    rB = lauf(B, c)
    print(f"=== Auf der unberuehrten Haelfte B ===")
    print(json.dumps(rB, ensure_ascii=False, indent=2))
    json.dump({"gewaehlt": {"schwelle": schwelle, "bonus": bonus}, "A": rA, "B": rB},
              open("/opt/unifieddb/udb/abruf/kalibrierung.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    c.close()
