# Generation 159 — Aggregationsfehler der Wegehierarchie lokalisiert

## Bindung

- AgentZero-Export: `0ece040dec22750b9c7e14c050ade5ee96afaca4`
- Exportzeit: `2026-08-19T17:41:10Z`
- Generation: `159`
- Test-Receipt: `583 gruen / 1 rot`
- Receipt-Source: `b1c7e0383` (weiterhin nicht als vollstaendiger Commit+Tree gebunden)

## Beobachtung

Der rohe Hierarchie-Receipt `agentZero/abruf/wegehierarchie.json` ist intern zaehlbar und nicht negativ:

- Gesamtwege: `352`
- Autobahn: `244`
- Schnellstrasse: `40`
- Langsame Strasse: `62`
- Tunnel: `6`
- Summe der Rangzahlen: `352`
- oberes Zehntel haelt: `0.136`
- Gleichverteilungs-Baseline: `0.099`
- Rohurteil: `GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts`

Der Zielaggregator `agentZero/ZIELE.md` beschreibt denselben Zustand dagegen als:

- `352 Wege`
- `-1 Tunnel`
- gleichzeitig textuell: `Hierarchie bildet sich`

Damit liegen drei voneinander getrennte Widersprueche vor:

1. **Count-Widerspruch:** Rohdaten `6 Tunnel` vs Aggregator `-1 Tunnel`.
2. **Invariantenbruch:** Ein Rang-Count darf nie negativ sein.
3. **Verdikt-Widerspruch:** Rohpruefer sagt `GLEICHVERTEILT`, Zielaggregator behauptet `Hierarchie bildet sich`.

## Kausallinse

### Haupt-Hypothese H1

Der Fehler liegt im Aggregations-/Messpfad von `ZIELE.md`, nicht in den Rohdaten. Ein Fehler-/Missing-Sentinel (`-1`) wird als numerischer Count weitergereicht und ein separater Textpfad entscheidet das Zielurteil anhand anderer Kriterien.

Erwartung unter H1:
- direkte SQL-/Raw-Counts bleiben nichtnegativ;
- Roh-Receipt bleibt bei 6 Tunneln;
- `ZIELE.md` kann trotz identischem Rohzustand `-1` anzeigen;
- der Generator besitzt getrennte Count- und Verdict-Pfade oder eine fehlerhafte Fallback-Semantik.

### Gegenhypothese H2

`wegehierarchie.json` und `ZIELE.md` messen nicht denselben logischen Zeitpunkt oder nicht dieselbe Datenquelle; `-1` markiert bewusst einen fehlenden/inkompatiblen Messpfad.

Erwartung unter H2:
- unterschiedliche Timestamps/DB-Snapshots oder Tabellenquellen sind nachweisbar;
- `-1` ist dokumentierte Missing-Semantik und nicht versehentlich numerisch;
- eine atomare gemeinsame Messung beseitigt den Widerspruch ohne Produktcodeaenderung.

## Adversarial Review

Der Roh-Receipt allein beweist noch keine nuetzliche Hierarchie. Obwohl `0.136 > 0.099`, ist die Klassifikationsschwelle fuer `deutlich mehr` nicht explizit als maschinenlesbare Regel gebunden. Ein blosser Vergleich `> baseline` waere Goodhart-anfaellig und koennte Rauschen als Hierarchie ausgeben.

Deshalb darf weder das rohe `GLEICHVERTEILT` noch das Zielbild `Hierarchie bildet sich` Promotionscredit erhalten, solange die Entscheidungsregel nicht in einem gemeinsamen Receipt gebunden ist.

## Neuer Messbedarf

### `HIERARCHY_RECEIPT/v1`

Ein atomarer Receipt soll enthalten:

- `source_commit_full`
- `source_tree`
- DB-/Snapshot-ID und Zeit
- SQL-/Query-Digests
- `wege_total`
- Rangcounts je Kategorie
- harte Invariante `sum(rank_counts) == wege_total`
- harte Invariante `all(count >= 0)`
- Top-Decile-Inputdaten und Ergebnis
- Gleichverteilungs-Baseline
- explizite Schwelle/Entscheidungsregel
- maschinenberechnetes Verdict
- Result-Digest

`ERROR` und `UNMEASURED` muessen typisierte Zustaende sein und duerfen nie als `-1` in einen Count gelangen.

## Billigster diskriminierender Falsifikator

Ohne Produktveraenderung denselben DB-Snapshot einmal durch beide aktuellen Messpfade und zusaetzlich durch einen direkten Roh-Count laufen lassen. Wenn Raw/JSON `6` und `ZIELE` erneut `-1` liefern, ist H1 stark bestaetigt. Wenn unterschiedliche Snapshot-/Query-Bindungen sichtbar werden, gewinnt H2.

## Testfrontier

Der Test-Receipt bleibt `583 gruen / 1 rot`; einzig rot ist weiterhin:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Dieser stabile rote Frontier ist getrennt vom Hierarchie-Messfehler zu behandeln.

## Status

- Hierarchie-Count-Widerspruch: `REPLICATED`
- Fehlerlokalisierung auf Aggregations-/Messpfad: `MECHANISM_SUPPORTED`
- Nuetzliche Hierarchie: `UNRESOLVED`
- Test-Acceptance: `BLOCKED` durch fehlende Exact-Source-Bindung und 1 persistenten Red
- Whole Clay Machine: `NOT CLAIMED`
