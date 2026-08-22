# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-22T19:06:45Z aus `udb/abruf/wegehierarchie.py`.

## Verdikt

> **GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts**

Das obere Zehntel der Wege haelt diesen Anteil der Gesamtguete. Bei Gleichverteilung waeren es genau 10 %. Deutlich mehr heisst: wenige Autobahnen, viele langsame Strassen -- die erwartete Form.

Wege gesamt: **367**

## Verteilung nach Rang

| Rang | Anzahl |
|---|---|
| tunnel | 7 |
| autobahn | 214 |
| langsame strasse | 73 |
| schnellstrasse | 73 |

Oberes Zehntel haelt 0.14 der Gesamtguete (bei Gleichverteilung waeren es 0.098).

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | tunnel | 0.963 | 784 | 784 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | tunnel | 0.963 | 642 | 642 |
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | tunnel | 0.963 | 843 | 843 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | autobahn | 0.951 | 497 | 497 |
| C-AUDIT-001 | C-CLAYCODE-003 | geschwister_datei | tunnel | 0.881 | 138 | 138 |
| C-AUDIT-001 | C-CLAYCODE-005 | geschwister_datei | autobahn | 0.854 | 58 | 58 |
| gabriel-claude-BOOT.md | gabriel-claude-4 | geschwister_verzeichnis | tunnel | 0.847 | 25 | 25 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | tunnel | 0.822 | 454 | 454 |
| C-AUDIT-001 | C-CLAYCODE-008 | geschwister_datei | autobahn | 0.822 | 88 | 88 |
| C-AUDIT-001 | C-STORAGE-002 | geschwister_datei | autobahn | 0.808 | 20 | 20 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | tunnel | 0.781 | 304 | 304 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | atomic-runs-20260810T2024p0700-chatgpt-secondary-grt-commutator-COUNTERHYPOTHESIS_RESULT.json | None | autobahn | 0.781 | 249 | 249 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

