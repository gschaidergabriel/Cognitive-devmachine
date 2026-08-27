#!/usr/bin/env python3
"""namen.py — Namensgleichungen für den Omni-Graphen.

`wirt` ist Overlay-Schlüssel: (wirt, instanz, organ). Wird ein Rechner
umbenannt, entsteht ein **neuer Knoten** — und jede Zeitreihe bricht an
dieser Stelle entzwei, ohne dass es jemandem auffällt. Die Messung beginnt
still bei null.

Deshalb wird hier **nicht umgeschrieben**. Die Historie ist anhängend; ein
alter Eintrag bleibt, wie er war. Stattdessen führt diese Datei eine
Gleichung: `digital-retina` **ist** `clayverse`. Wer die Historie liest,
liest sie durch diese Brille.

    namen.py setzen <alt> <neu> [grund]
    namen.py aufloesen <name>        -> heutiger Name
    namen.py zeigen
    namen.py pruefen <strom.jsonl>   -> wie viele Einträge tragen alte Namen?
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

TABELLE = Path("/var/lib/clay/namensgleichungen.json")


def _laden() -> dict:
    if TABELLE.exists():
        try:
            return json.loads(TABELLE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"gleichungen": []}


def _sichern(d: dict) -> None:
    TABELLE.parent.mkdir(parents=True, exist_ok=True)
    TABELLE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def setzen(alt: str, neu: str, grund: str = "") -> int:
    d = _laden()
    if any(g["alt"] == alt and g["neu"] == neu for g in d["gleichungen"]):
        print(f"  {alt} = {neu} steht schon")
        return 0
    d["gleichungen"].append({
        "alt": alt, "neu": neu, "grund": grund,
        "gesetzt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    _sichern(d)
    print(f"  {alt} = {neu}")
    return 0


def aufloesen(name: str) -> str:
    """Folgt der Kette: a→b→c gibt c. Schleifen brechen ab."""
    d = _laden()
    karte = {g["alt"]: g["neu"] for g in d["gleichungen"]}
    gesehen = {name}
    while name in karte:
        name = karte[name]
        if name in gesehen:
            break
        gesehen.add(name)
    return name


def zeigen() -> int:
    d = _laden()
    if not d["gleichungen"]:
        print("  Keine Gleichungen.")
        return 0
    print()
    for g in d["gleichungen"]:
        print(f"  {g['alt']:<26} = {g['neu']:<20} seit {g['gesetzt'][:10]}")
        if g.get("grund"):
            print(f"    {g['grund']}")
    print()
    return 0


def pruefen(pfad: str) -> int:
    """Wie viele Einträge im Strom tragen einen alten Namen? Das ist die Zahl,
    die ohne Gleichung unsichtbar aus der Auswertung fiele."""
    p = Path(pfad)
    if not p.exists():
        print(f"  {pfad} gibt es nicht")
        return 1
    d = _laden()
    alte = {g["alt"] for g in d["gleichungen"]}
    zaehler: dict[str, int] = {}
    gesamt = 0
    for z in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not z.strip():
            continue
        try:
            e = json.loads(z)
        except Exception:
            continue
        gesamt += 1
        w = e.get("wirt")
        if w in alte:
            zaehler[w] = zaehler.get(w, 0) + 1
    print(f"  {gesamt} Einträge geprüft")
    if not zaehler:
        print("  Kein alter Name im Strom — die Gleichung schadet nicht, sie schützt.")
    for w, n in sorted(zaehler.items(), key=lambda x: -x[1]):
        print(f"    {n:>6} × '{w}'  →  wird gelesen als '{aufloesen(w)}'")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "setzen" and len(a) >= 3:
        sys.exit(setzen(a[1], a[2], " ".join(a[3:])))
    if a and a[0] == "aufloesen" and len(a) >= 2:
        print(aufloesen(a[1])); sys.exit(0)
    if a and a[0] == "pruefen" and len(a) >= 2:
        sys.exit(pruefen(a[1]))
    sys.exit(zeigen())
