"""Halbsatz-Messung: A=gerade Indizes (kalibrieren), B=ungerade (nur berichten).
Reine SQLite-Messung, kein Modellaufruf. Kopie der Logik aus messgeraet.py,
aber auf eine Haelfte beschraenkt und mehrfach lauffaehig fuer Streuung."""
import sys, json, time, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

GOLD = "/opt/unifieddb/udb/abruf/goldsatz.json"


def messen(halbe: str, marke: str = "") -> dict:
    satz_all = json.load(open(GOLD, encoding="utf-8"))
    if halbe == "A":
        satz = satz_all[0::2]
    elif halbe == "B":
        satz = satz_all[1::2]
    else:
        satz = satz_all
    c = P._connect()
    P._ensure_vp_tables(c)

    mit_anker = treffsicher = auffindbar = 0
    zeiten = []
    for e in satz:
        t = time.perf_counter()
        pk = P.paket(e["frage"], conn=c)
        zeiten.append((time.perf_counter() - t) * 1000)

        r = pk["resolution"]
        anker = tuple(r.get("anker") or ())
        if anker:
            mit_anker += 1
            if e["erwartet"] in anker:
                treffsicher += 1
        ids = {t2.get("id") for t2 in pk.get("treffer", []) if isinstance(t2, dict)}
        if e["erwartet"] in ids:
            auffindbar += 1
    c.close()

    n = len(satz)
    erg = {
        "marke": marke, "halbe": halbe, "fragen": n,
        "ankerquote": round(100 * mit_anker / n, 1),
        "treffsicher_von_gesetzten": (round(100 * treffsicher / mit_anker, 1) if mit_anker else None),
        "ausbeute": round(100 * treffsicher / n, 1),
        "auffindbar": round(100 * auffindbar / n, 1),
        "latenz_median_ms": round(statistics.median(zeiten), 1),
        "latenz_p95_ms": round(sorted(zeiten)[int(0.95 * n)] if n > 1 else zeiten[0], 1),
    }
    return erg


if __name__ == "__main__":
    halbe = sys.argv[1] if len(sys.argv) > 1 else "B"
    marke = sys.argv[2] if len(sys.argv) > 2 else "lauf"
    erg = messen(halbe, marke)
    print(json.dumps(erg, ensure_ascii=False))
