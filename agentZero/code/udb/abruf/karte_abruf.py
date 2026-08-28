"""F93b -- Die Abrufkarte. Nicht der Graph, sondern der Wegweiser darueber.

Aus der Dokumentation (Gabriel, 16.08.):
    "dieser Entry-Point muss iterativ von der Entitaet selbst anhand der Karten,
     die sie schreibt, verbessert werden -- mit jedem Puls."
    "Der Bibliothekar merkt sich nicht die Buecher. Er merkt sich, wo die
     Regale stehen."

⭐ DIE HARTE EIGENSCHAFT, die den Bau ueberhaupt rechtfertigt:

    Eine Karte MUSS kleiner als der Graph und billiger zu lesen sein.
    Waechst sie proportional mit, ist sie keine Karte, sondern eine Kopie --
    und beschleunigt nichts.

Deshalb ist das Groessenverhaeltnis hier kein Bericht, sondern eine SPERRE:
`bauen()` verweigert eine Karte, die groesser als ein Fuenftel des Korpus ist.
Eine Kennzahl, die man nur ausdruckt, wird irgendwann ignoriert.

WAS DIE KARTE ENTHAELT

    Regionen     (projekt x art) -- die Grobgliederung, die im Korpus schon steckt
    Landmarken   je Region die am staerksten vernetzten Artikel = gute Startpunkte
    Wegweiser    Wort -> Region, aber NUR fuer UNTERSCHEIDENDE Woerter

Unterscheidend heisst: das Wort kommt in DIESER Region deutlich haeufiger vor
als im Korpus insgesamt (Lift). Ein Wort, das ueberall gleich haeufig ist, sagt
nichts darueber, wo man anfangen soll -- dieselbe Einsicht, die schon den
Einstiegspunkt repariert hat: Allgegenwart ist nicht Aussagekraft.

⚠️⚠️ DIE GEFAHR, die in der Dokumentation als die groesste von allen benannt ist

    "Eine selbstgeschriebene Karte ist die reinste Form des Echoproblems.
     Sie wird aus dem gebaut, was vorher funktioniert hat. Also lenkt sie in
     Gegenden, die schon einmal getragen haben -- und nicht in Gegenden, die nie
     betreten wurden. Das System wird schneller auf einem SCHRUMPFENDEN
     Fragenkorridor."

Das Gegenmittel gehoert in den Einstiegspunkt (ein fester Anteil der Eintritte
wird GEGEN die Karte gewaehlt) und ist hier noch NICHT eingebaut -- der
Einstiegspunkt liegt gerade in anderer Hand. Damit die Luecke nicht vergessen
wird, traegt jede Kartenversion das Feld `erkundungsanteil`. Steht dort 0.0,
laeuft die Karte ohne Gegenmittel, und das ist an der Version selbst ablesbar.

ZWEI TAKTE, BEWUSST GETRENNT

    bauen()    volle Neuberechnung, versioniert. Teuer. Langsamer Takt.
    pflegen()  Erfolgsmarken der letzten Runde einfalten. Billig. Schneller Takt.

Die Dokumentation sagt "mit jedem Puls" -- der Puls schlaegt alle 4 Sekunden.
Eine volle Karte je Takt waere alle 4 s ein paar tausend Zeilen; das ist keine
Kartenpflege, sondern ein Datenleck. Gemeint ist das Einfalten, und das ist
`pflegen()`.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
import time
import collections

DB_PATH = "/var/lib/clay/wiki.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS vp_karte_version (
  version INTEGER PRIMARY KEY AUTOINCREMENT,
  gebaut_am TEXT NOT NULL,
  anlass TEXT,
  regionen INTEGER, landmarken INTEGER, wegweiser INTEGER,
  korpus_artikel INTEGER, korpus_kanten INTEGER,
  verhaeltnis REAL,              -- Kartenzeilen / Korpuszeilen. Muss klein bleiben.
  erkundungsanteil REAL DEFAULT 0.0,   -- 0.0 = Gegenmittel gegen das Echo NICHT aktiv
  dauer_s REAL
);
CREATE TABLE IF NOT EXISTS vp_karte_region (
  version INTEGER NOT NULL, region TEXT NOT NULL,
  projekt TEXT, art TEXT, artikel_n INTEGER,
  landmarken TEXT,               -- JSON: die am staerksten vernetzten Artikel
  PRIMARY KEY(version, region)
);
CREATE TABLE IF NOT EXISTS vp_karte_wegweiser (
  version INTEGER NOT NULL, wort TEXT NOT NULL, region TEXT NOT NULL,
  staerke REAL NOT NULL,         -- Lift: wie stark zeigt dieses Wort auf die Region
  PRIMARY KEY(version, wort, region)
);
CREATE INDEX IF NOT EXISTS idx_karte_wegweiser_wort ON vp_karte_wegweiser(wort);
CREATE TABLE IF NOT EXISTS vp_erfolgsmarke (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL, frage TEXT, region TEXT, anker TEXT,
  getragen INTEGER,              -- 1 = der Eintritt hat zur Antwort gefuehrt
  quelle TEXT                    -- wer die Marke gesetzt hat
);
CREATE INDEX IF NOT EXISTS idx_erfolgsmarke_region ON vp_erfolgsmarke(region, ts);
"""

STOPP = frozenset("""der die das dem den des ein eine einer eines und oder aber auch als
am an auf aus bei bis dann dass dazu durch fuer gegen hat ist ich ihr im in ins ja jede
jeder jetzt kann kein man mehr mit muss nach nicht noch nun nur ob ohne sehr sein sich sie
sind so soll ueber um uns unter vom von vor war was weil wenn wer werden wie wird wo zu zum
zur the and for with from this that what how does why not are were has have been will can
may into out its of on at by be as or if then than there their them new old use used using
""".split())

MAX_WEGWEISER_JE_REGION = 40
MIN_LIFT = 3.0
MAX_LANDMARKEN = 5
MAX_VERHAELTNIS = 0.20        # Karte darf hoechstens ein Fuenftel des Korpus gross sein


def _worte(t: str):
    return [w for w in re.split(r"[^0-9A-Za-zÄÖÜäöüß]+", (t or "").lower())
            if len(w) > 3 and w not in STOPP]


def _conn(pfad: str = DB_PATH) -> sqlite3.Connection:
    c = sqlite3.connect(pfad, timeout=60)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=60000")
    return c


def sicherstellen(c: sqlite3.Connection) -> None:
    c.executescript(SCHEMA)



def _erkundungsanteil() -> float:
    """Wie viel der Eintritte GEGEN die Karte gewaehlt werden (F93b-Gegenmittel).

    Wird aus paket.py gelesen, nicht hier festgelegt -- eine zweite Kopie
    derselben Zahl waere die naechste Stelle, die auseinanderlaeuft. Ist der
    Wert nicht lesbar, wird 0.0 eingetragen: dann laeuft die Karte
    nachweislich ohne Gegenmittel, und das soll man der Version ansehen.
    """
    # Beim Skriptstart liegt sys.path[0] auf .../udb/abruf, die Wurzel fehlt --
    # und paket.py liest auf Modulebene selbst aus `udb`. Wurzel aus dem
    # eigenen Dateipfad ableiten, nicht fest eintragen: ein fester Pfad ist die
    # naechste Stelle, die beim Verschieben bricht.
    import sys as _sys, pathlib as _pl
    _wurzel = str(_pl.Path(__file__).resolve().parents[2])
    if _wurzel not in _sys.path:
        _sys.path.insert(0, _wurzel)

    for holen in (
        lambda: __import__("udb.abruf.paket", fromlist=["_ERKUNDUNGSANTEIL"])._ERKUNDUNGSANTEIL,
        lambda: __import__("paket", fromlist=["_ERKUNDUNGSANTEIL"])._ERKUNDUNGSANTEIL,
    ):
        try:
            return float(holen())
        except Exception as e:
            # Auf stderr, nicht verschluckt: sonst sucht der naechste Leser
            # denselben Grund noch einmal von vorn.
            import sys as _s
            print(f"karte_abruf: Erkundungsanteil nicht lesbar ({type(e).__name__}: {e})",
                  file=_s.stderr)
            continue
    # ⚠️ -1.0, NICHT 0.0. 0.0 heisst "Erkundung bewusst abgeschaltet" und ist
    # eine gueltige Einstellung. Beides auf denselben Wert abzubilden macht
    # genau den Unterschied unsichtbar, um dessentwillen das Feld existiert.
    return -1.0


def bauen(c: sqlite3.Connection | None = None, *, anlass: str = "takt") -> dict:
    """Volle Neuberechnung, versioniert. Verweigert eine Karte, die zu gross ist."""
    eigen = c is None
    c = c or _conn()
    sicherstellen(c)
    t0 = time.perf_counter()

    rows = c.execute(
        "SELECT id, titel, projekt, art FROM artikel WHERE titel IS NOT NULL").fetchall()
    korpus_artikel = len(rows)
    korpus_kanten = c.execute("SELECT COUNT(*) FROM kante WHERE COALESCE(verfallen,0)=0").fetchone()[0]

    # Wortzaehlung je Region und global -- in EINEM Durchlauf.
    je_region = collections.defaultdict(collections.Counter)
    global_zaehler = collections.Counter()
    region_groesse = collections.Counter()
    region_meta = {}
    for r in rows:
        region = f"{r['projekt'] or '-'}|{r['art'] or '-'}"
        region_meta[region] = (r["projekt"], r["art"])
        region_groesse[region] += 1
        w = set(_worte(r["titel"]))
        je_region[region].update(w)
        global_zaehler.update(w)

    # Landmarken: die am staerksten vernetzten Artikel je Region. Wer viele
    # Kanten hat, setzt den Leser nahe an vieles -- genau das ist ein guter
    # Startpunkt (F93: Vernetzung kauft Erreichbarkeit, der Eintritt kauft Tempo).
    # ⚠️ NICHT graph_kante: die nutzt gehashte Knoten (n_<hash>) aus
    # graph_knoten -- gemessen 0 von 14.235 Kanten mit Artikel-ID als Quelle.
    # Der Graph, den der Abruf BEGEHT, ist `kante` (siehe _walk in paket.py:
    # JOIN kante k ON k.von = w.node). Dort: 19.283 von 97.147 mit Artikel.
    grad = collections.Counter()
    for a, b in c.execute("SELECT von, nach FROM kante WHERE COALESCE(verfallen,0)=0"):
        grad[a] += 1
        grad[b] += 1
    landmarken_je_region = collections.defaultdict(list)
    for r in rows:
        region = f"{r['projekt'] or '-'}|{r['art'] or '-'}"
        g = grad.get(r["id"], 0)
        if g:
            landmarken_je_region[region].append((g, r["id"], r["titel"]))
    for region in landmarken_je_region:
        landmarken_je_region[region].sort(reverse=True)
        landmarken_je_region[region] = landmarken_je_region[region][:MAX_LANDMARKEN]

    gesamt_worte = sum(global_zaehler.values()) or 1
    version_zeilen_region, version_zeilen_weg = [], []
    for region, zaehler in je_region.items():
        n_region = sum(zaehler.values()) or 1
        kandidaten = []
        for wort, n in zaehler.items():
            # Lift: wie viel haeufiger ist das Wort HIER als ueberall?
            p_region = n / n_region
            p_global = global_zaehler[wort] / gesamt_worte
            lift = p_region / p_global if p_global else 0.0
            if lift >= MIN_LIFT and n >= 2:
                kandidaten.append((lift * math.log(1 + n), wort, lift))
        kandidaten.sort(reverse=True)
        for _, wort, lift in kandidaten[:MAX_WEGWEISER_JE_REGION]:
            version_zeilen_weg.append((wort, region, round(lift, 3)))
        p, a = region_meta[region]
        version_zeilen_region.append((
            region, p, a, region_groesse[region],
            json.dumps([{"id": i, "titel": ti, "grad": g}
                        for g, i, ti in landmarken_je_region.get(region, [])], ensure_ascii=False)))

    # Eine Karte ohne einen einzigen Startpunkt ist keine Karte. Der erste
    # Bau lieferte genau das -- 73 Regionen, 0 Landmarken -- und meldete Erfolg,
    # weil ein leerer Zaehler wie ein legitimes Ergebnis aussieht.
    landmarken_gesamt = sum(len(v) for v in landmarken_je_region.values())
    if landmarken_gesamt == 0:
        if eigen:
            c.close()
        return {"gebaut": False,
                "grund": "keine einzige Landmarke -- zeigt der Graph auf die Artikel-IDs?",
                "regionen": len(version_zeilen_region)}

    kartenzeilen = len(version_zeilen_region) + len(version_zeilen_weg)
    korpuszeilen = korpus_artikel + korpus_kanten
    verhaeltnis = kartenzeilen / max(1, korpuszeilen)

    if verhaeltnis > MAX_VERHAELTNIS:
        # SPERRE, keine Warnung. Eine Karte in Korpusgroesse ist eine Kopie und
        # beschleunigt nichts -- sie wuerde nur so aussehen, als taete sie es.
        if eigen:
            c.close()
        return {"gebaut": False, "grund": "Karte zu gross -- das waere eine Kopie",
                "kartenzeilen": kartenzeilen, "korpuszeilen": korpuszeilen,
                "verhaeltnis": round(verhaeltnis, 4), "grenze": MAX_VERHAELTNIS}

    dauer = time.perf_counter() - t0
    cur = c.execute(
        "INSERT INTO vp_karte_version(gebaut_am,anlass,regionen,landmarken,wegweiser,"
        "korpus_artikel,korpus_kanten,verhaeltnis,erkundungsanteil,dauer_s) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime()), anlass,
         len(version_zeilen_region), landmarken_gesamt,
         len(version_zeilen_weg), korpus_artikel, korpus_kanten,
         round(verhaeltnis, 5), _erkundungsanteil(), round(dauer, 2)))
    version = cur.lastrowid
    c.executemany("INSERT INTO vp_karte_region(version,region,projekt,art,artikel_n,landmarken) "
                  "VALUES(?,?,?,?,?,?)", [(version, *z) for z in version_zeilen_region])
    c.executemany("INSERT INTO vp_karte_wegweiser(version,wort,region,staerke) VALUES(?,?,?,?)",
                  [(version, *z) for z in version_zeilen_weg])
    c.commit()
    if eigen:
        c.close()
    return {"gebaut": True, "version": version, "regionen": len(version_zeilen_region),
            "wegweiser": len(version_zeilen_weg), "verhaeltnis": round(verhaeltnis, 4),
            "korpuszeilen": korpuszeilen, "dauer_s": round(dauer, 2)}


def neueste_version(c: sqlite3.Connection):
    r = c.execute("SELECT MAX(version) FROM vp_karte_version").fetchone()
    return r[0] if r and r[0] else None


def wohin(c: sqlite3.Connection, worte, *, version=None) -> list[dict]:
    """'Riecht die Frage nach X, beginne bei Y.' -- der eigentliche Zweck.

    Gibt Regionen mit Landmarken zurueck, absteigend nach Wegweiserstaerke.
    Billig: EIN Index-Zugriff je Wort, keine Graphsuche.
    """
    version = version or neueste_version(c)
    if not version:
        return []
    kern = [w for w in worte if len(w) > 3 and w not in STOPP]
    if not kern:
        return []
    qm = ",".join("?" for _ in kern)
    treffer = collections.defaultdict(float)
    for r in c.execute(
            f"SELECT region, staerke FROM vp_karte_wegweiser WHERE version=? AND wort IN ({qm})",
            (version, *kern)):
        treffer[r["region"]] += r["staerke"]
    if not treffer:
        return []
    beste = sorted(treffer.items(), key=lambda kv: -kv[1])[:3]
    aus = []
    for region, staerke in beste:
        r = c.execute("SELECT landmarken, artikel_n FROM vp_karte_region WHERE version=? AND region=?",
                      (version, region)).fetchone()
        aus.append({"region": region, "staerke": round(staerke, 2),
                    "artikel_n": r["artikel_n"] if r else 0,
                    "landmarken": json.loads(r["landmarken"]) if r and r["landmarken"] else []})
    return aus


if __name__ == "__main__":
    import sys
    c = _conn()
    befehl = sys.argv[1] if len(sys.argv) > 1 else "bauen"
    if befehl == "bauen":
        print(json.dumps(bauen(c, anlass="hand"), ensure_ascii=False, indent=2))
    elif befehl == "wohin":
        print(json.dumps(wohin(c, _worte(" ".join(sys.argv[2:]))), ensure_ascii=False, indent=2))
    elif befehl == "stand":
        for r in c.execute("SELECT version,gebaut_am,regionen,wegweiser,verhaeltnis,erkundungsanteil,dauer_s "
                           "FROM vp_karte_version ORDER BY version DESC LIMIT 10"):
            print(f"  v{r[0]:<4} {r[1]}  Regionen={r[2]:<4} Wegweiser={r[3]:<5} "
                  f"Verhaeltnis={r[4]:.4f}  Erkundung={r[5]}  {r[6]}s")
    c.close()
