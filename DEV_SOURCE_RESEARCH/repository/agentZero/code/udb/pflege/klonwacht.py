#!/usr/bin/env python3
"""klonwacht.py — faengt den naechsten Klon ab, bevor er entsteht.

Warum es das gibt: /opt/unifieddb/udb/ war eine KOPIE von
/opt/clayverse/werkzeug/. 9 Module byte-identisch, 4 binnen EINES Tages
auseinandergelaufen. Der Klon ist nicht aus Absicht entstanden, sondern
weil ihn nichts verhindert hat. Ein Klon, der driftet, ist in einem Monat
ein zweites System.

Diese Wacht kostet Sekunden und laeuft als pre-commit-Haken in beiden
Repos. Sie meldet:

  KLON    gleicher Inhalt an zwei Orten          -> muss ein Verweis werden
  DRIFT   fast gleicher Inhalt an zwei Orten     -> muss entschieden werden
  BEKANNT steht in klonwacht-bekannt.txt         -> Entscheidung laeuft, ok

⚠️ Namen helfen nicht. Der gefaehrlichste gefundene Fall hiess auf der
einen Seite artikel.py und auf der anderen wiki.py. Deshalb wird NICHT
ueber Dateinamen gepaart, sondern ueber die Menge der Top-Level-Namen
(ast) und erst danach ueber den echten Textabgleich.

Aufruf:
    python3 klonwacht.py            # prueft, Rueckgabe 1 bei neuem Fund
    python3 klonwacht.py --alle     # zeigt auch die bekannten
    KLONWACHT=aus git commit ...    # Haken einmalig uebergehen
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import os
import sys

BAEUME = (
    ("udb", "/opt/unifieddb/udb"),
    ("werkzeug", "/opt/clayverse/werkzeug"),
)
BEKANNT_DATEI = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "klonwacht-bekannt.txt")
# Ab wieviel Namensueberschneidung zwei Dateien ueberhaupt verglichen werden.
# Darunter lohnt der teure Textabgleich nicht.
NAMEN_SCHWELLE = 0.6
# Ab wieviel Textaehnlichkeit es ein Drift-Fund ist.
DRIFT_SCHWELLE = 0.80


def _lies(p: str) -> str:
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def _namen(quelle: str) -> set:
    """Top-Level-Namen einer Datei. ast, nicht grep -- zuverlaessiger."""
    try:
        baum = ast.parse(quelle)
    except SyntaxError:
        return set()
    aus = set()
    for n in baum.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            aus.add(n.name)
        elif isinstance(n, ast.Assign):
            for z in n.targets:
                if isinstance(z, ast.Name):
                    aus.add(z.id)
    return aus


def _ist_verweis(quelle: str) -> bool:
    """Eine bereits aufgeloeste Kopie -- die soll die Wacht nicht melden."""
    return "uebernehmen(__name__" in quelle or "from udb._quelle" in quelle


def _bekannt() -> set:
    aus = set()
    try:
        for z in open(BEKANNT_DATEI, encoding="utf-8"):
            z = z.split("#")[0].strip()
            if z:
                aus.add(frozenset(t.strip() for t in z.split("<->")))
    except OSError:
        pass
    return aus


def sammeln() -> list:
    dateien = []
    for _marke, wurzel in BAEUME:
        for pfad, _dirs, namen in os.walk(wurzel):
            if "__pycache__" in pfad or "/.git" in pfad:
                continue
            for n in namen:
                if not n.endswith(".py") or n == "__init__.py":
                    continue
                voll = os.path.join(pfad, n)
                q = _lies(voll)
                if not q.strip() or _ist_verweis(q):
                    continue
                dateien.append((voll, q, _namen(q),
                                hashlib.sha256(q.encode()).hexdigest()))
    return dateien


def pruefen(alle: bool = False) -> list:
    links = [d for d in sammeln() if d[0].startswith(BAEUME[0][1])]
    rechts = [d for d in sammeln() if d[0].startswith(BAEUME[1][1])]
    bekannt = _bekannt()
    funde = []
    for lp, lq, ln, lh in links:
        for rp, rq, rn, rh in rechts:
            if lh == rh:
                art, wert = "KLON", 1.0
            else:
                if not ln or not rn:
                    continue
                ueber = len(ln & rn) / max(len(ln), len(rn))
                if ueber < NAMEN_SCHWELLE:
                    continue
                wert = difflib.SequenceMatcher(None, lq, rq).ratio()
                if wert < DRIFT_SCHWELLE:
                    continue
                art = "DRIFT"
            paar = frozenset((lp, rp))
            if paar in bekannt:
                art = "BEKANNT"
                if not alle:
                    continue
            funde.append((art, wert, lp, rp))
    return funde


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--alle", action="store_true",
                    help="auch die bekannten Faelle zeigen")
    a = ap.parse_args()
    if os.environ.get("KLONWACHT") == "aus":
        print("klonwacht: uebergangen (KLONWACHT=aus)")
        return 0
    funde = pruefen(a.alle)
    neu = [f for f in funde if f[0] != "BEKANNT"]
    for art, wert, lp, rp in sorted(funde, key=lambda f: -f[1]):
        print("%-7s %.3f  %s\n              %s" % (art, wert, lp, rp))
    if not funde:
        print("klonwacht: kein Klon, kein Drift.")
    if neu:
        print("\n%d NEUE(R) FUND(E). Eine Kopie ist kein Modul.\n"
              "  KLON  -> in einen Verweis aufloesen (udb/_quelle.py:"
              "uebernehmen)\n"
              "  DRIFT -> entscheiden, welche Seite die Quelle ist, DANN "
              "abgleichen\n"
              "Wenn die Entscheidung laeuft: Paar in %s eintragen.\n"
              "Einmalig uebergehen: KLONWACHT=aus git commit ..."
              % (len(neu), BEKANNT_DATEI))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
