"""Messgeraet fuer den Einstiegspunkt der Abrufentitaet.

Fuehrt vier Zahlen, und zwar GEGENEINANDER:

  ankerquote     wie oft ueberhaupt ein Anker gesetzt wird
  treffsicher    wie oft der gesetzte Anker der richtige ist   <-- die Bremse
  auffindbar     wie oft der richtige Artikel im Ergebnis auftaucht (egal wie)
  latenz         Median und p95

⚠️ Die Ankerquote allein waere eine Luege. Sie geht auf 100 %, sobald man die
Schwelle auf 0 setzt -- dann raet die Entitaet immer, und der Abruf wird
schlechter. `treffsicher` ist die Gegenkraft: sie faellt sofort, wenn geraten
wird. Nur wenn BEIDE steigen, ist es eine Verbesserung.

`auffindbar` misst getrennt davon, ob die Antwort ueberhaupt im Paket landet --
auch ueber den lexikalischen Weg. Damit laesst sich unterscheiden, ob eine
Aenderung den Einstieg verbessert oder nur den Anker verschiebt.
"""
import sys, json, time, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

GOLD = "/opt/unifieddb/udb/abruf/goldsatz.json"


def messen(marke: str = "", zeige_fehler: int = 0) -> dict:
    satz = json.load(open(GOLD, encoding="utf-8"))
    c = P._connect()
    P._ensure_vp_tables(c)

    mit_anker = treffsicher = auffindbar = 0
    zeiten, klassen, fehler = [], {}, []
    for e in satz:
        t = time.perf_counter()
        pk = P.paket(e["frage"], conn=c)
        zeiten.append((time.perf_counter() - t) * 1000)

        r = pk["resolution"]
        anker = tuple(r.get("anker") or ())
        kl = str(r.get("klasse"))
        klassen[kl] = klassen.get(kl, 0) + 1

        if anker:
            mit_anker += 1
            if e["erwartet"] in anker:
                treffsicher += 1
            else:
                fehler.append({"frage": e["frage"], "erwartet": e["erwartet"], "bekommen": list(anker)})
        ids = {t.get("id") for t in pk.get("treffer", []) if isinstance(t, dict)}
        if e["erwartet"] in ids:
            auffindbar += 1
    c.close()

    n = len(satz)
    erg = {
        "marke": marke,
        "fragen": n,
        "ankerquote": round(100 * mit_anker / n, 1),
        "treffsicher_von_gesetzten": (round(100 * treffsicher / mit_anker, 1) if mit_anker else None),
        "treffsicher_absolut": round(100 * treffsicher / n, 1),
        "auffindbar": round(100 * auffindbar / n, 1),
        "latenz_median_ms": round(statistics.median(zeiten), 1),
        "latenz_p95_ms": round(sorted(zeiten)[int(0.95 * n)], 1),
        "klassen": dict(sorted(klassen.items(), key=lambda x: -x[1])),
    }
    if zeige_fehler:
        erg["falsche_anker"] = fehler[:zeige_fehler]
    return erg


if __name__ == "__main__":
    marke = sys.argv[1] if len(sys.argv) > 1 else "lauf"
    erg = messen(marke, zeige_fehler=3)
    print(json.dumps(erg, ensure_ascii=False, indent=2))
    with open(f"/opt/unifieddb/udb/abruf/messung-{marke}.json", "w", encoding="utf-8") as f:
        json.dump(erg, f, ensure_ascii=False, indent=2)
