# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-20T14:11:16Z aus `udb/abruf/wegehierarchie.py`.

## Verdikt

> **GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts**

Das obere Zehntel der Wege haelt diesen Anteil der Gesamtguete. Bei Gleichverteilung waeren es genau 10 %. Deutlich mehr heisst: wenige Autobahnen, viele langsame Strassen -- die erwartete Form.

Wege gesamt: **361**

## Verteilung nach Rang

| Rang | Anzahl |
|---|---|
| tunnel | 6 |
| autobahn | 248 |
| langsame strasse | 69 |
| schnellstrasse | 38 |

Oberes Zehntel haelt 0.138 der Gesamtguete (bei Gleichverteilung waeren es 0.1).

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | tunnel | 1.0 | 717 | 717 |
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | tunnel | 1.0 | 648 | 648 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | tunnel | 1.0 | 506 | 506 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | tunnel | 1.0 | 434 | 434 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | tunnel | 1.0 | 304 | 304 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | tunnel | 1.0 | 437 | 437 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | atomic-runs-20260810T2024p0700-chatgpt-secondary-grt-commutator-COUNTERHYPOTHESIS_RESULT.json | None | autobahn | 1.0 | 249 | 249 |
| trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-RUN_MANIFEST.json | trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-NEGATIVE_RESULTS.md | None | autobahn | 1.0 | 140 | 140 |
| andreas-claude-wissen-leihmich.md | andreas-claude-wissen-README.md | geschwister_verzeichnis | autobahn | 1.0 | 120 | 120 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | H1-ALIEN-SYMPLECTIC | None | autobahn | 1.0 | 96 | 96 |
| C-AUDIT-001 | C-CLAYCODE-003 | geschwister_datei | autobahn | 1.0 | 95 | 95 |
| H-Q23-PAR-004 | CH-Q23-PAR-004 | attacks | autobahn | 1.0 | 90 | 90 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

