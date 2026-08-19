# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-19T12:41:10Z aus `udb/abruf/wegehierarchie.py`.

## Verdikt

> **Hierarchie bildet sich**

Das obere Zehntel der Wege haelt diesen Anteil der Gesamtguete. Bei Gleichverteilung waeren es genau 10 %. Deutlich mehr heisst: wenige Autobahnen, viele langsame Strassen -- die erwartete Form.

Wege gesamt: **75**

## Verteilung nach Rang

| Rang | Anzahl |
|---|---|
| tunnel | 6 |
| autobahn | 2 |
| schnellstrasse | 1 |
| langsame strasse | 66 |

Oberes Zehntel haelt 0.413 der Gesamtguete (bei Gleichverteilung waeren es 0.093).

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | tunnel | 1.0 | 125 | 125 |
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | tunnel | 1.0 | 125 | 125 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | tunnel | 1.0 | 120 | 120 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | tunnel | 1.0 | 115 | 115 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | tunnel | 1.0 | 105 | 105 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | tunnel | 1.0 | 98 | 98 |
| C-AUDIT-001 | C-LOOP-003 | geschwister_datei | autobahn | 0.784 | 12 | 12 |
| C-AUDIT-001 | C-CLAYCODE-001 | geschwister_datei | autobahn | 0.784 | 12 | 12 |
| C-AUDIT-001 | C-CLAYCODE-008 | geschwister_datei | schnellstrasse | 0.536 | 6 | 6 |
| runtime-tool_requests-bridge-smoke-openalex.json | runtime-tool_requests-c6-claynative-arxiv-20260808T1750.json | geschwister_verzeichnis | langsame strasse | 0.226 | 2 | 2 |
| runtime-tool_requests-bridge-smoke-openalex.json | runtime-tool_requests-c6-claynative-exa-20260808T1750.json | geschwister_verzeichnis | langsame strasse | 0.226 | 2 | 2 |
| runtime-tool_requests-bridge-smoke-openalex.json | runtime-tool_requests-c6-claynative-openalex-20260808T1750.json | geschwister_verzeichnis | langsame strasse | 0.226 | 2 | 2 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

