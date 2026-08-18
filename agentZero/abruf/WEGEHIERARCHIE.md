# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-18T23:41:08Z aus `udb/abruf/wegehierarchie.py`.

## Verdikt

> **zu wenige Wege fuer ein Urteil**

Eine Hierarchie aus weniger als zehn Wegen ist Rauschen.

Wege gesamt: **9**

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | autobahn | 1.0 | 80 | 80 |
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | autobahn | 1.0 | 80 | 80 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | autobahn | 1.0 | 77 | 77 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | autobahn | 1.0 | 74 | 74 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | autobahn | 1.0 | 65 | 65 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | autobahn | 1.0 | 60 | 60 |
| C-AUDIT-001 | C-CLAYCODE-001 | geschwister_datei | autobahn | 0.784 | 12 | 12 |
| C-AUDIT-001 | C-LOOP-003 | geschwister_datei | schnellstrasse | 0.64 | 8 | 8 |
| C-AUDIT-001 | C-CLAYCODE-008 | geschwister_datei | schnellstrasse | 0.4 | 4 | 4 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

