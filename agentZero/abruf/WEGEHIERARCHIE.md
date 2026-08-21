# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-21T11:37:16Z aus `udb/abruf/wegehierarchie.py`.

## Verdikt

> **GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts**

Das obere Zehntel der Wege haelt diesen Anteil der Gesamtguete. Bei Gleichverteilung waeren es genau 10 %. Deutlich mehr heisst: wenige Autobahnen, viele langsame Strassen -- die erwartete Form.

Wege gesamt: **365**

## Verteilung nach Rang

| Rang | Anzahl |
|---|---|
| tunnel | 7 |
| autobahn | 239 |
| langsame strasse | 72 |
| schnellstrasse | 47 |

Oberes Zehntel haelt 0.14 der Gesamtguete (bei Gleichverteilung waeren es 0.099).

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | tunnel | 1.0 | 749 | 749 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | tunnel | 1.0 | 607 | 607 |
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | tunnel | 1.0 | 810 | 810 |
| C-AUDIT-001 | C-CLAYCODE-003 | geschwister_datei | autobahn | 0.997 | 136 | 136 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | tunnel | 0.996 | 479 | 479 |
| C-AUDIT-001 | C-CLAYCODE-005 | geschwister_datei | autobahn | 0.967 | 58 | 58 |
| gabriel-claude-BOOT.md | gabriel-claude-4 | geschwister_verzeichnis | tunnel | 0.959 | 25 | 25 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | tunnel | 0.93 | 454 | 454 |
| C-AUDIT-001 | C-CLAYCODE-008 | geschwister_datei | autobahn | 0.93 | 88 | 88 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | tunnel | 0.884 | 304 | 304 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | atomic-runs-20260810T2024p0700-chatgpt-secondary-grt-commutator-COUNTERHYPOTHESIS_RESULT.json | None | autobahn | 0.884 | 249 | 249 |
| trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-RUN_MANIFEST.json | trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-NEGATIVE_RESULTS.md | None | autobahn | 0.884 | 140 | 140 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

