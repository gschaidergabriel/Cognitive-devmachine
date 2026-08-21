# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-21T04:18:59Z aus `udb/abruf/wegehierarchie.py`.

## Verdikt

> **GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts**

Das obere Zehntel der Wege haelt diesen Anteil der Gesamtguete. Bei Gleichverteilung waeren es genau 10 %. Deutlich mehr heisst: wenige Autobahnen, viele langsame Strassen -- die erwartete Form.

Wege gesamt: **361**

## Verteilung nach Rang

| Rang | Anzahl |
|---|---|
| tunnel | 6 |
| autobahn | 237 |
| langsame strasse | 70 |
| schnellstrasse | 48 |

Oberes Zehntel haelt 0.14 der Gesamtguete (bei Gleichverteilung waeren es 0.1).

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | tunnel | 0.994 | 691 | 691 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | tunnel | 0.994 | 549 | 549 |
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | tunnel | 0.991 | 770 | 770 |
| C-AUDIT-001 | C-CLAYCODE-003 | geschwister_datei | autobahn | 0.963 | 117 | 117 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | tunnel | 0.93 | 457 | 457 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | tunnel | 0.921 | 453 | 453 |
| C-AUDIT-001 | C-CLAYCODE-008 | geschwister_datei | autobahn | 0.921 | 87 | 87 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | tunnel | 0.884 | 304 | 304 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | atomic-runs-20260810T2024p0700-chatgpt-secondary-grt-commutator-COUNTERHYPOTHESIS_RESULT.json | None | autobahn | 0.884 | 249 | 249 |
| trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-RUN_MANIFEST.json | trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-NEGATIVE_RESULTS.md | None | autobahn | 0.884 | 140 | 140 |
| andreas-claude-wissen-leihmich.md | andreas-claude-wissen-README.md | geschwister_verzeichnis | autobahn | 0.884 | 120 | 120 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | H1-ALIEN-SYMPLECTIC | None | autobahn | 0.884 | 96 | 96 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

