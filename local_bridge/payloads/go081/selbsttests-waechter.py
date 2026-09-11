#!/usr/bin/env python3
"""Laesst selbsttests.sh laufen, fuehrt Verlauf, meldet nur bei AENDERUNG.

WARUM ES DAS GIBT (Eintrag 076, 2026-09-11):

In 074 habe ich selbsttests.sh gebaut und selbst notiert: "haengt in keinem
Timer". 075 hat den Punkt liegen lassen. Der Satz lief also weiter genau
dann, wenn ich in einem Architektenlauf daran dachte -- und der Satz von
074 gilt gegen sich selbst: ein Test, den niemand startet, unterscheidet
sich nicht von einem, den es nicht gibt.

Der Regressionswaechter deckt das NICHT ab. Er laesst die Pruefer laufen und
meldet, wenn sich deren BEFUND aendert. Ob ein Pruefer noch seinen eigenen
Selbsttest besteht, sieht er nicht: ein Pruefer, der still kaputtgeht und
dabei dieselbe Zahl ausgibt, bleibt dort unauffaellig. Das ist die andere
Achse, und dafuer ist diese Datei da.

WAS SIE BEWUSST NICHT TUT: die Selbsttests neu erfinden. Sie startet den
vorhandenen Satz und schreibt eine Spur. Der ganze Wert liegt im Vergleich
mit der Vorzeile -- deshalb steht in der Spur NUR, was stabil bleibt, wenn
sich nichts aendert. Laufzeiten stehen nicht drin; sie schwanken bei jedem
Lauf und wuerden aus der Meldung ein Dauerrauschen machen, das man nach
zwei Tagen wegklickt.

SPALTEN:
  zeit    Zeitstempel
  satz    "10/10" -- die Gesamtzahl. Sie ist da, damit der schlimmste Fall
          nicht still bleibt: wenn der Glob in selbsttests.sh nichts mehr
          findet, verschwinden ALLE Testspalten, und die Migration ruehrt
          dann bewusst nichts an (Regel 3 in verlaufsdatei.py). Ohne eine
          Spalte, die immer da ist, waere "0/0" die leiseste Zeile von allen.
  laeufer  "ok" oder "rc<N>" -- Prozessstatus des ganzen Satzes;
           bleibt auch dann sichtbar, wenn #ERG und #SATZ gleich bleiben
  je ein Test  "ok" oder "rc<N>"

EXIT-CODES, dieselbe Unterscheidung wie beim Regressionswaechter (073):
  0  gelaufen, nichts Auffaelliges
  1  WERKZEUGFEHLER -- der Satz war nicht startbar/lesbar. Ich weiss nichts.
  2  BEFUND -- ein Selbsttest ist gefallen (oder der Satz endete != 0).
     Das heisst: dieses Werkzeug arbeitet richtig.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WERKZEUG = Path(__file__).resolve().parent
sys.path.insert(0, str(WERKZEUG))
from verlaufsdatei import (aenderungen, anhaengen,  # noqa: E402,F401
                           kopf_lesen, letzte_zeile, migrieren, nicht_gemessen)

LAEUFER_STANDARD = WERKZEUG / "selbsttests.sh"
VERLAUF_STANDARD = Path.home() / "architekt" / "selbsttestverlauf.tsv"
MELDUNG_STANDARD = Path.home() / "architekt" / "selbsttest-meldung.txt"
ZEITGRENZE_STANDARD = 600   # gemessen 17-19 s; die Grenze faengt Haenger


class Unlesbar(Exception):
    """Der Satz lief nicht oder sagte nichts Auswertbares -- rc=1, nicht 2.

    Der Unterschied ist der Kern: 'ich habe nicht gemessen' darf nie wie
    'ich habe gemessen und es war gut' aussehen (071), aber auch nicht wie
    ein echter Fehlschlag -- sonst sucht der naechste Leser am falschen Ort.
    """


def satz_laufen(laeufer: Path, zeitgrenze: int) -> tuple[dict[str, str], str, int]:
    """Startet den Satz. Gibt (Ergebnisse, satz-Zelle, rc) zurueck."""
    if not laeufer.is_file():
        raise Unlesbar(f"{laeufer} gibt es nicht")
    try:
        p = subprocess.run(["bash", str(laeufer)], capture_output=True,
                           text=True, timeout=zeitgrenze)
    except subprocess.TimeoutExpired:
        raise Unlesbar(f"{laeufer.name} lief laenger als {zeitgrenze}s")
    except OSError as e:
        raise Unlesbar(f"{laeufer.name} nicht startbar: {e}")

    ergebnisse: dict[str, str] = {}
    satz = ""
    for zeile in p.stdout.splitlines():
        teile = zeile.split("\t")
        if teile[0] == "#ERG" and len(teile) == 3:
            ergebnisse[teile[1]] = "ok" if teile[2] == "0" else f"rc{teile[2]}"
        elif teile[0] == "#SATZ" and len(teile) == 2:
            satz = teile[1]

    if not satz:
        raise Unlesbar(
            f"keine #SATZ-Zeile in der Ausgabe von {laeufer.name} "
            f"(rc={p.returncode}); letzte Zeile: "
            f"{(p.stdout.strip().splitlines() or ['<leer>'])[-1][:120]}")
    return ergebnisse, satz, p.returncode


def melden(text: str, ziel: Path) -> str:
    zeit = datetime.now().astimezone().isoformat(timespec="seconds")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("a", encoding="utf-8") as f:
        f.write(f"{zeit}\tdatei\t{text}\n")
    return str(ziel)


def lauf(laeufer: Path, verlauf: Path, meldung: Path, melden_fn,
         zeitgrenze: int, still: bool) -> int:
    try:
        ergebnisse, satz, rc = satz_laufen(laeufer, zeitgrenze)
    except Unlesbar as e:
        weg = melden_fn(f"Selbsttestsatz nicht auswertbar -- {e}", meldung)
        print(f"WERKZEUGFEHLER (gemeldet: {weg})\n  {e}")
        return 1

    jetzt = {"satz": satz,
             "laeufer": "ok" if rc == 0 else f"rc{rc}"}
    jetzt.update(ergebnisse)
    namen = list(jetzt)
    spalten = ["zeit"] + namen

    zeile = {"zeit": datetime.now().astimezone().isoformat(timespec="seconds")}
    zeile.update(jetzt)

    umzug = migrieren(verlauf, spalten)
    kopf = kopf_lesen(verlauf)
    vorher = letzte_zeile(verlauf)
    anhaengen(verlauf, zeile, spalten)
    geaendert, hinweis = aenderungen(vorher, jetzt, namen)
    fehlen = nicht_gemessen(kopf, namen)

    gefallen = [n for n, w in ergebnisse.items() if w != "ok"]

    teile = satz.split("/")
    gefunden = int(teile[1]) if len(teile) == 2 and teile[1].isdigit() else None
    stimmig = gefunden is not None and gefunden == len(ergebnisse)

    if fehlen:
        neu = [n for n in fehlen if vorher and vorher.get(n)]
        if neu and not stimmig:
            weg = melden_fn(
                "Spalten ohne Messung -- " + ", ".join(neu) +
                f". Der Satz meldet '{satz}', geliefert hat er "
                f"{len(ergebnisse)} Einzelergebnis(se).",
                meldung)
            print(f"WERKZEUGFEHLER (gemeldet: {weg})")
        print("  nicht gemessen: " + ", ".join(fehlen) +
              ("" if stimmig else f"  (Satz meldet '{satz}')"))

    if geaendert:
        text = "Selbsttest-Befund geaendert -- " + "; ".join(geaendert)
        weg = melden_fn(text, meldung)
        print(f"AENDERUNG (gemeldet: {weg})")
        for g in geaendert:
            print(f"  {g}")
    if umzug:
        print(f"  {umzug}")
    if not still and not geaendert:
        print(f"  satz  {satz}")
        for n, w in ergebnisse.items():
            print(f"  {w:<6} {n}")
        print(f"  {hinweis}" if hinweis else "  unveraendert gegenueber der Vorzeile")

    if fehlen and not stimmig:
        return 1
    if gefallen or rc != 0:
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--laeufer", type=Path, default=LAEUFER_STANDARD)
    ap.add_argument("--verlauf", type=Path, default=VERLAUF_STANDARD)
    ap.add_argument("--meldung", type=Path, default=MELDUNG_STANDARD)
    ap.add_argument("--zeitgrenze", type=int, default=ZEITGRENZE_STANDARD)
    ap.add_argument("--still", action="store_true",
                    help="nur bei Aenderung etwas sagen (fuer den Timer)")
    a = ap.parse_args()
    return lauf(a.laeufer, a.verlauf, a.meldung, melden, a.zeitgrenze, a.still)


if __name__ == "__main__":
    sys.exit(main())
