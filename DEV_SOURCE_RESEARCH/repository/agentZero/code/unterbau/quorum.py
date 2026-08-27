#!/usr/bin/env python3
"""quorum.py — DAS EINE TOR fuer kognitive Arbeit (Punkt 3 der Arbeitsschlange,
F20/F23/F24, 2026-08-15).

    mindestens ein Zwilling GESUND  ->  Kognition arbeitet
    kein Zwilling gesund            ->  COGNITIVE_QUORUM_UNAVAILABLE -> WAIT
                                     ->  "bitte warten bis kognitive Module online"

Der Vertrag steht ausfuehrlich in
/opt/clayverse/bau/KONTRAKT-KOGNITIONSTOR.md — das hier ist die einzige
STELLE, die die Frage beantwortet. Kein zweiter Aufrufer soll die
Herzschlag-Dateien selbst lesen und eigene Schwellen erfinden.

⚠️ REICHBAR IST NICHT GESUND. Diese Datei liest NICHT "kommt eine Antwort auf
ping/ssh", sondern den zuletzt EMPFANGENEN Herzschlag jedes Zwillings
(geschrieben von clay-herzschlag-empfang auf diesem Wirt) UND dessen eigenes
Selbstbild ('gesund': bool + 'module': {...}). Ein Zwilling, der erreichbar
ist, aber seinen Selbsttest nicht besteht, meldet 'gesund': false — und zaehlt
hier als offline, auch wenn ssh auf ihn noch antwortet.

⚠️ WAS 'module' HEUTE PRUEFT UND WAS NICHT: der LEANN-Index / Umsortierer
(Punkt 5 der Arbeitsschlange) ist NOCH NICHT GEBAUT. 'gesund' bedeutet daher
heute "die Infrastruktur fuer Kognition ist bereit" (clay-kognition.slice
greift, das abgeleitete Datenverzeichnis ist schreibbar) — NICHT "ein Index
antwortet richtig". Das ist eine ehrliche Zwischenstufe, keine Erfindung:
sobald Punkt 5 gebaut ist, MUSS die Selbstpruefung im Zwilling
(clay-herzschlag) um echte Modul-Antworten erweitert werden, sonst luegt das
Feld 'gesund'. Diese Datei aendert sich dafuer NICHT — sie liest nur, was der
Zwilling ehrlich meldet.

    quorum.py status    JSON auf stdout, Exit 0 = OK, Exit 2 = WAIT
    quorum.py mensch     nur der Menschsatz (oder "ok"), fuers Terminal
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ABLAGE = Path("/var/lib/clay/zwilling")

# ⭐ GEMESSEN, nicht erfunden (2026-08-15, ai-core-node -> frank-api, 8 Schlaege,
# 15 s Schlafpause + realer Laufzeit): 7 Luecken, ALLE exakt 18,0 s, stdev 0.
# -> gemessener Herzschlagtakt = 18,0 s (der langsamere der beiden Zwillinge;
#    andreas-MACO lag bei ~0,8-1,1 s SSH-Laufzeit, also schneller/enger).
# Schwelle = 3x gemessener Takt = 54 s: uebersteht EINEN verpassten oder
# verzoegerten Schlag (Netzjitter, kurzzeitig belegte SSH-Verbindung) ohne
# einen gesunden Zwilling faelschlich fuer offline zu erklaeren, meldet einen
# wirklich toten Zwilling aber immer noch innerhalb einer Minute. Nicht 90,
# nicht 60 -- 54, weil das exakt 3x der GEMESSENEN 18,0 s sind.
SCHWELLE_S = 54.0

MENSCH_SATZ = "bitte warten bis kognitive Module online"


def _jetzt() -> datetime:
    return datetime.now(timezone.utc)


def _parse_zeit(s: str):
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


def _lies_zwillinge() -> dict:
    ergebnis = {}
    if not ABLAGE.is_dir():
        return ergebnis
    for datei in sorted(ABLAGE.glob("*.json")):
        name = datei.stem
        try:
            satz = json.loads(datei.read_text(encoding="utf-8"))
        except Exception as e:
            ergebnis[name] = {"lesbar": False, "fehler": str(e), "frisch": False,
                               "gesund_gemeldet": False, "gesund": False}
            continue
        zeit = _parse_zeit(str(satz.get("zeit", "")))
        if zeit is None:
            alter_s = None
            frisch = False
        else:
            alter_s = (_jetzt() - zeit).total_seconds()
            frisch = 0 <= alter_s <= SCHWELLE_S
        gemeldet = satz.get("gesund") is True
        ergebnis[name] = {
            "lesbar": True,
            "zeit": satz.get("zeit"),
            "alter_s": round(alter_s, 1) if alter_s is not None else None,
            "frisch": frisch,
            "gesund_gemeldet": gemeldet,
            "gesund": bool(frisch and gemeldet),
            "generation": satz.get("generation"),
            "module": satz.get("module"),
        }
    return ergebnis


def status() -> dict:
    zwillinge = _lies_zwillinge()
    gesunde = [n for n, z in zwillinge.items() if z["gesund"]]
    ok = len(gesunde) > 0
    d = {
        "geprueft_utc": _jetzt().isoformat(timespec="seconds"),
        "schwelle_s": SCHWELLE_S,
        "stand": "OK" if ok else "WAIT",
        "code": None if ok else "COGNITIVE_QUORUM_UNAVAILABLE",
        "mensch_satz": None if ok else MENSCH_SATZ,
        "gesunde_zwillinge": gesunde,
        "zwillinge": zwillinge,
    }
    return d


def mensch_satz() -> str:
    """Fuer Aufrufer, die nur den Satz brauchen, keinen Zustand."""
    d = status()
    return d["mensch_satz"] or "ok"


def _main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("status", "mensch"):
        sys.stderr.write("Nutzung: quorum.py status|mensch\n")
        return 1
    d = status()
    if sys.argv[1] == "status":
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        print(d["mensch_satz"] or "ok")
    return 0 if d["stand"] == "OK" else 2


if __name__ == "__main__":
    sys.exit(_main())
