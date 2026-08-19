# Wegehierarchie (F94)

Automatisch erzeugt 2026-08-19T14:11:11Z aus `udb/abruf/wegehierarchie.py`.

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

Oberes Zehntel haelt 0.161 der Gesamtguete (bei Gleichverteilung waeren es 0.1).

## Staerkste Wege

| von | nach | Art | Rang | Guete | Nutzung | getragen |
|---|---|---|---|---|---|---|
| C-AUDIT-001 | C-AUDIT-002 | geschwister_datei | tunnel | 1.0 | 461 | 461 |
| C-AUDIT-001 | C-AUDIT-003 | geschwister_datei | tunnel | 1.0 | 390 | 390 |
| C-AUDIT-001 | C-AUDIT-004 | geschwister_datei | tunnel | 1.0 | 304 | 304 |
| C-AUDIT-001 | C-AUDIT-005 | geschwister_datei | tunnel | 1.0 | 296 | 296 |
| C-AUDIT-001 | ledgers-NEGATIVE_RESULTS.jsonl | geschwister_verzeichnis | tunnel | 1.0 | 375 | 375 |
| C-AUDIT-001 | C-AUDIT-007 | geschwister_datei | tunnel | 1.0 | 243 | 243 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | atomic-runs-20260810T2024p0700-chatgpt-secondary-grt-commutator-COUNTERHYPOTHESIS_RESULT.json | None | autobahn | 1.0 | 125 | 125 |
| C-AUDIT-001 | C-LOOP-003 | geschwister_datei | autobahn | 0.999 | 54 | 54 |
| trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-RUN_MANIFEST.json | trigger_runs-claygraph-claygraph-20260809T0149p0700-chatgpt-secondary-sol-04-NEGATIVE_RESULTS.md | None | autobahn | 0.999 | 52 | 52 |
| 20260810T2024p0700-chatgpt-secondary-grt-commutator | H1-ALIEN-SYMPLECTIC | None | autobahn | 0.999 | 52 | 52 |
| trigger_runs-q23-q23-20260810T224100p0700-chatgpt-secondary-RUN_MANIFEST.json | CH-Q23-DUPLICATE-ENCODER-WINS-01 | None | autobahn | 0.997 | 46 | 46 |
| CH-Q23-DUPLICATE-ENCODER-WINS-01 | CH-Q23-MERGER-LOSS-01 | geschwister_datei | autobahn | 0.994 | 40 | 40 |

## Warum das Verdikt so bleibt, wie es ist

`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den aktuellen Stand so, wie er ist.

