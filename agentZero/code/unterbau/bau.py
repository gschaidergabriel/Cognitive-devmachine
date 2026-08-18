#!/usr/bin/env python3
"""bau.py — ClayVerse schreibt seinen eigenen Bau mit.

Jeder Bauschritt wird hier verzeichnet: was, warum, mit welchem gemessenen
Ergebnis. Anhängend, versioniert, sofort auf das Bare-Repo geschoben.

    bau.py schritt B1 "SSH gehaertet" --ergebnis "passwordauth aus, geprueft" \\
           --bauteil B1 --wirt clayverse --status fertig

    bau.py stand                 zeigt den Fortschritt je Bauteil
    bau.py bericht               kurzer Text fuer Menschen

Grundsatz: **kein Eintrag ohne Messung.** Das Feld `ergebnis` ist Pflicht und
soll eine Zahl oder eine Pruefung nennen, keine Absicht.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/opt/clayverse")
LOG = REPO / "bau" / "protokoll.jsonl"

# Die Bauteile aus dem Plan. Reihenfolge = Abhaengigkeit, nicht Nummer.
BAUTEILE = {
    "B0":  ("Zweite Tuer und Vollsicherung", []),
    "B1":  ("Sofort-Haertung", ["B0"]),
    "B12": ("Der Wirt heisst ClayVerse", ["B0"]),
    "B2":  ("Alles auf ClayVerse", ["B0", "B1", "B12"]),
    "B3":  ("GitHub-Umbau", []),
    "B4":  ("Zentralrepo und Ereignisstrom", ["B2", "B3"]),
    "B5":  ("Frontend: zehn Ansichten", ["B2", "B4"]),
    "B6":  ("Kartographie und Moeglichkeitsraum", ["B4"]),
    "B7":  ("EffectGate", ["B4"]),
    "B8":  ("Firewall-Guertel", ["B0", "B4"]),
    "B9":  ("Bauleiter Frank v0.1", ["B3", "B4", "B7"]),
    "B10": ("Mail", ["B2", "B8"]),
    "B11": ("Retina wird Franks Auge", ["B2", "B4", "B7", "B9"]),
    "B13": ("Identitaet, Blasen und Rechte", ["B4", "B5", "B7"]),
    "B14": ("Fortschritt, Bugs und Worklog", ["B4", "B13"]),
    "B15": ("Alles Neue ueber die Forschungsentitaet", ["B4", "B9", "B13"]),
    "B16": ("Oertliches Gedaechtnis", ["B4", "B6", "B13"]),
    "B17": ("Das Kontingentbuch", ["B2", "B13"]),
    "B18": ("ClayVerse ist die Forschungsentitaet", ["B4", "B9", "B15", "B17"]),
    "B19": ("Forschungsentitaet je Projekt", ["B9", "B15"]),
    "B20": ("/recursive", ["B6", "B15", "B17", "B18"]),
    "B21": ("Die Methode verbessert sich selbst", ["B15", "B18", "B20"]),
    "B22": ("Alles zuruecksetzbar", ["B4", "B7", "B13", "B17"]),
    "B23": ("Web-Werkzeuge", ["B7", "B17", "B20"]),
    "B24": ("Quarantaene fuer Downloads", ["B4", "B7", "B13", "B22"]),
    "B25": ("Auslastung, Fehler, Selbstheilung", ["B4", "B6", "B14", "B17"]),
    "B26": ("Der Tresor", []),
    "B27": ("ClayWiki und ClaySearch", ["B4", "B6", "B13", "B17"]),
    "B28": ("Der Anker bei Andreas", ["B6", "B13", "B16"]),
}
# „abgeschlossen" ist bewusst von „geprueft" getrennt. Ein geprüfter Schritt
# sagt: DIESES Stück wurde gemessen. Ein abgeschlossenes Bauteil sagt: der
# ganze Umfang des Bauteils ist abgedeckt. Ohne die Trennung zählt der erste
# geprüfte Teilschritt das ganze Bauteil als fertig — so stand B5 auf ✓,
# während die zehn Ansichten nicht existierten. Eine Fortschrittsanzeige, die
# zu hoch zeigt, ist schlimmer als keine: sie hört auf, nach dem Rest zu fragen.
ZUSTAENDE = ("begonnen", "fertig", "geprueft", "abgeschlossen",
             "blockiert", "verworfen")
ABGESCHLOSSEN = ("abgeschlossen",)


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True).stdout.strip()


def _eintraege() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(z) for z in LOG.read_text(encoding="utf-8").splitlines() if z.strip()]


def schritt(a) -> None:
    if a.bauteil not in BAUTEILE:
        sys.exit(f"Unbekanntes Bauteil {a.bauteil}. Bekannt: {' '.join(BAUTEILE)}")
    if a.status not in ZUSTAENDE:
        sys.exit(f"Unbekannter Zustand. Erlaubt: {' '.join(ZUSTAENDE)}")
    if not a.ergebnis.strip():
        sys.exit("Ohne gemessenes Ergebnis kein Eintrag. Das ist der Sinn dieser Datei.")
    if a.status == "abgeschlossen" and not (a.beleg or []):
        sys.exit("Ein Bauteil wird nur mit --beleg abgeschlossen: womit ist "
                 "geprueft, dass der GANZE Umfang abgedeckt ist?")

    e = {
        "zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "bauteil": a.bauteil,
        "titel": a.titel,
        "status": a.status,
        "ergebnis": a.ergebnis,
        "wirt": a.wirt or os.uname().nodename,
        "instanz": a.instanz,
        "belege": a.beleg or [],
    }
    if a.offen:
        e["offen"] = a.offen

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

    _git("add", "-A")
    subprocess.run(["git", "-C", str(REPO), "commit", "-q", "-m",
                    f"{a.bauteil} {a.status}: {a.titel}\n\n{a.ergebnis}"],
                   capture_output=True)
    p = subprocess.run(["git", "-C", str(REPO), "push", "-q", "origin", "HEAD"],
                       capture_output=True, text=True)
    ok = "geschoben" if p.returncode == 0 else f"NICHT geschoben: {p.stderr.strip()[:120]}"
    print(f"{a.bauteil} · {a.status} · {a.titel}  [{ok}]")


def stand(_a) -> None:
    ein = _eintraege()
    letzte: dict[str, dict] = {}
    for e in ein:
        letzte[e["bauteil"]] = e
    zaehler: dict[str, int] = {}
    for e in ein:
        zaehler[e["bauteil"]] = zaehler.get(e["bauteil"], 0) + 1
    zeichen = {"begonnen": "◐", "fertig": "◐", "geprueft": "◐",
               "abgeschlossen": "✓", "blockiert": "✗", "verworfen": "–"}
    fertig = sum(1 for e in letzte.values() if e["status"] in ABGESCHLOSSEN)
    inarbeit = sum(1 for e in letzte.values() if e["status"] not in ABGESCHLOSSEN)
    print(f"\nClayVerse — {fertig} von {len(BAUTEILE)} Bauteilen abgeschlossen, "
          f"{inarbeit} in Arbeit, {len(ein)} Schritte\n")
    for b, (titel, braucht) in BAUTEILE.items():
        e = letzte.get(b)
        z = zeichen.get(e["status"], "?") if e else "·"
        offen = [x for x in braucht
                 if letzte.get(x, {}).get("status") not in ABGESCHLOSSEN]
        if offen and not e:
            hinweis = f"  wartet auf {' '.join(offen)}"
        elif e and e["status"] not in ABGESCHLOSSEN:
            hinweis = f"  {zaehler.get(b, 0)} Schritte, nicht abgeschlossen"
        else:
            hinweis = ""
        print(f"  {z} {b:<4} {titel[:44]:<44}{hinweis}")
        if e and e.get("offen"):
            print(f"        offen: {e['offen']}")
    print()


def bericht(_a) -> None:
    ein = _eintraege()
    if not ein:
        print("Noch kein Schritt verzeichnet.")
        return
    print(f"\nBauprotokoll ClayVerse — {len(ein)} Schritte\n")
    for e in ein[-25:]:
        print(f"  {e['zeit'][:16]}  {e['bauteil']:<4} {e['status']:<10} {e['titel']}")
        print(f"        {e['ergebnis']}")
        if e.get("offen"):
            print(f"        offen: {e['offen']}")
    print()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    u = p.add_subparsers(dest="befehl", required=True)

    s = u.add_parser("schritt", help="einen Bauschritt verzeichnen")
    s.add_argument("bauteil")
    s.add_argument("titel")
    s.add_argument("--ergebnis", required=True,
                   help="was GEMESSEN wurde, nicht was beabsichtigt war")
    s.add_argument("--status", default="fertig", choices=ZUSTAENDE)
    s.add_argument("--wirt", default="")
    s.add_argument("--instanz", default="clayverse-bau")
    s.add_argument("--beleg", action="append", help="Pfad, Befehl oder Messwert")
    s.add_argument("--offen", default="", help="was danach noch fehlt")
    s.set_defaults(fn=schritt)

    u.add_parser("stand", help="Fortschritt je Bauteil").set_defaults(fn=stand)
    u.add_parser("bericht", help="die letzten Schritte im Klartext").set_defaults(fn=bericht)

    a = p.parse_args()
    a.fn(a)
