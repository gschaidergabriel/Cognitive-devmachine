"""Goldsatz v2 -- nur EINDEUTIG beantwortbare Fragen.

⚠️ WARUM v1 ALS MESSGERAET UNTAUGLICH WAR

v1 zog Fragen wie "Was steht zu test clayverse make?" aus Baunotizen. Im Korpus
liegen Dutzende fast gleicher Baunotizen ("test(clayverse): make QEMU ...",
"test(clayverse): fence ..."). Die Frage hat dort gar keine eindeutige Antwort --
und ein Messgeraet, dessen Sollwert mehrdeutig ist, misst das falsche.
Auffindbar 1,7 % waere zum Teil MEIN Fehler gewesen, nicht der der Entitaet.

v2 nimmt deshalb nur Artikel, deren Titel mindestens ein SELTENES Wort enthaelt
-- eines, das in hoechstens 3 Titeln des ganzen Korpus vorkommt. Dann ist die
Frage per Konstruktion beantwortbar, und ein Fehlschlag ist wirklich einer.

Die Frage wird aus dem seltenen Wort PLUS zwei tragenden Woertern gebaut, nicht
aus dem Titel abgeschrieben: sonst misst man Zeichenkettenvergleich, nicht Abruf.
"""
import sys, json, re, random, collections
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

random.seed(20260818)

STOPP = set("""der die das dem den des ein eine einer eines und oder aber auch als am an auf aus
bei bis dann dass dazu dich dir doch dort durch eben eher es fuer gegen habe haben hat hatte hier
ich ihr im in ins ist ja jede jeder jetzt kann kein man mehr mit muss nach nicht noch nun nur ob
ohne sehr sein sich sie sind so soll ueber um uns unter vom von vor war was weil wenn wer werden
wie wird wo zu zum zur the and for with from this that what how does why not are was were has have
been will can may test feat fix docs chore refactor build ci perf style revert""".split())


def _worte(t: str) -> list[str]:
    return [w for w in re.split(r"[^0-9A-Za-zÄÖÜäöüß]+", t.lower()) if len(w) > 3 and w not in STOPP]


def baue(n: int = 120) -> list[dict]:
    c = P._ro()
    rows = c.execute(
        "SELECT id, titel FROM artikel WHERE titel IS NOT NULL AND length(titel) BETWEEN 18 AND 100"
    ).fetchall()

    # Wie oft kommt jedes Wort in IRGENDEINEM Titel vor? Das ist der Seltenheitsmassstab.
    haeufig = collections.Counter()
    pro_artikel = {}
    for r in rows:
        w = set(_worte(r["titel"]))
        pro_artikel[r["id"]] = (r["titel"], w)
        haeufig.update(w)
    c.close()

    kand = []
    for aid, (titel, w) in pro_artikel.items():
        selten = sorted((x for x in w if haeufig[x] <= 3), key=lambda x: haeufig[x])
        if not selten:
            continue
        rest = [x for x in sorted(w, key=lambda y: haeufig[y]) if x != selten[0]][:2]
        if not rest:
            continue
        kand.append({
            "frage": f"Was ist zu {selten[0]} {' '.join(rest)} bekannt?",
            "erwartet": aid,
            "titel": titel,
            "seltenheit": haeufig[selten[0]],
        })
    random.shuffle(kand)
    # Nach Seltenheit sortieren waere Rosinenpickerei -- gemischt lassen,
    # aber die haerteren (Seltenheit 2-3) bewusst mit drin.
    return kand[:n]


if __name__ == "__main__":
    satz = baue(120)
    ziel = "/opt/unifieddb/udb/abruf/goldsatz.json"
    json.dump(satz, open(ziel, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    verteilung = collections.Counter(e["seltenheit"] for e in satz)
    print(f"{len(satz)} Fragen -> {ziel}")
    print("  Seltenheit des Ankerworts:", dict(sorted(verteilung.items())))
    for e in satz[:6]:
        print(f"  [{e['seltenheit']}] {e['frage'][:56]:<56} -> {e['titel'][:40]}")
