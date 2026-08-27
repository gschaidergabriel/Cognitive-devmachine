#!/usr/bin/env python3
"""Baut den Goldsatz fuer den Uebersetzer AUS ECHTEN ZUEGEN.

Quelle: mv_translation_log in /var/lib/clay/wiki.db, nur Zeilen mit turn_id
(= Produktionszug aus pipeline.py). Zeilen ohne turn_id stammen aus dem
Eval-Lauf mit handgeschriebenen Beispielen und sind hier ausdruecklich NICHT
zugelassen -- sonst misst man wieder sich selbst.

Es wird nichts erfunden und nichts umgeschrieben: caveman und deutsche
Produktionsantwort kommen Wort fuer Wort aus der Datenbank.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from uebersetzer_messen import fakten  # noqa: E402

DB = "file:/var/lib/clay/wiki.db?mode=ro"
ZIEL = Path("/opt/unifieddb/udb/abruf/uebersetzer_gold.json")

db = sqlite3.connect(DB, uri=True)
zeilen = db.execute(
    "SELECT translation_id, turn_id, caveman_original, german_translation,"
    "       translator_model, created_at "
    "FROM mv_translation_log WHERE turn_id IS NOT NULL ORDER BY created_at"
).fetchall()

proben, gesehen = [], set()
for tid, turn, cave, ger, modell, ts in zeilen:
    schluessel = cave.strip()[:400]
    if schluessel in gesehen:      # exakte Wiederholungen zaehlen nur einmal
        continue
    gesehen.add(schluessel)
    proben.append({
        "id": tid[:8],
        "turn_id": turn,
        "erzeugt": ts,
        "uebersetzer_modell": modell,
        "caveman": cave,
        "deutsch_produktion": ger,
        "fakten": fakten(cave),
    })

daten = {
    "hinweis": (
        "ECHTE Produktionszuege, nicht handgeschrieben. Quelle: Tabelle "
        "mv_translation_log in /var/lib/clay/wiki.db, ausschliesslich Zeilen mit "
        "gesetzter turn_id (die Zeilen ohne turn_id stammen aus dem Eval-Lauf mit "
        "handgeschriebenen Beispielen und sind hier bewusst ausgeschlossen). "
        "'deutsch_produktion' ist die Antwort, die der Mensch damals wirklich "
        "gesehen hat -- nicht nachtraeglich erzeugt. Die Faktenliste je Probe ist "
        "maschinell aus dem Caveman-Text gezogen und von Hand nachpruefbar. "
        "Beobachtung beim Bau: Zero spricht im Betrieb NICHT durchgehend "
        "Caveman-Englisch -- mehrere Originale sind bereits ganz oder teilweise "
        "deutsch und in reichem Markdown. Der Uebersetzer bekommt also nicht das, "
        "wofuer er geschrieben wurde."
    ),
    "mass": (
        "Verlorener Fakt = durchgefallen. Erfundener Fakt = durchgefallen "
        "(Eignerregel NICHTS erfinden). Schoenes Deutsch zaehlt hier nicht."
    ),
    "ziel": 0.95,
    "proben": proben,
}
ZIEL.write_text(json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8")
print("proben:", len(proben), "->", ZIEL)
