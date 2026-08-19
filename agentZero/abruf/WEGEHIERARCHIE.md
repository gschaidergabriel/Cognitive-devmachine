# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-19T13:41:11Z aus `udb/abruf/wegehierarchie.py`.

## Verdikt

> **GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts**

Das obere Zehntel der Wege haelt diesen Anteil der Gesamtguete. Bei Gleichverteilung waeren es genau 10 %. Deutlich mehr heisst: wenige Autobahnen, viele langsame Strassen -- die erwartete Form.

Wege gesamt: **321**

## Verteilung nach Rang

| Rang | Anzahl |
|---|---|
| tunnel | 6 |
| autobahn | 151 |
| schnellstrasse | 102 |
| langsame strasse | 62 |

Oberes Zehntel haelt 0.165 der Gesamtguete (bei Gleichverteilung waeren es 0.1).

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | tunnel | 1.0 | 449 | 449 |
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | tunnel | 1.0 | 378 | 378 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | tunnel | 1.0 | 300 | 300 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | tunnel | 1.0 | 292 | 292 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | tunnel | 1.0 | 375 | 375 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | tunnel | 1.0 | 239 | 239 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | atomic-runs-20260810T2024p0700-chatgpt-secondary-grt-commutator-COUNTERHYPOTHESIS_RESULT.json | None | autobahn | 1.0 | 90 | 90 |
| C-AUDIT-001 | C-LOOP-003 | geschwister_datei | autobahn | 0.998 | 48 | 48 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | H1-ALIEN-SYMPLECTIC | None | autobahn | 0.995 | 42 | 42 |
| CH-Q23-DUPLICATE-ENCODER-WINS-01 | CH-Q23-MERGER-LOSS-01 | geschwister_datei | autobahn | 0.994 | 40 | 40 |
| CH-Q23-PAR-004 | CH-Q23-RECOVERY-005 | geschwister_datei | autobahn | 0.994 | 40 | 40 |
| trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-RUN_MANIFEST.json | trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-NEGATIVE_RESULTS.md | None | autobahn | 0.994 | 40 | 40 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

