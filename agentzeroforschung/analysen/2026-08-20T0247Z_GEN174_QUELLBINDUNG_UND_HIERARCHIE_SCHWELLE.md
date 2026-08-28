# Generation 174 — Quellbindung und Hierarchie-Schwelle

## Gebundener Stand

- AgentZero-Export: `af005559ea94be333a19e693c8dec2a0c6d9ca8e`
- Exportzeit: `2026-08-20T02:41:12Z`
- Generation: `174`
- Testreceipt: `583 gruen / 1 rot`
- verbleibender roter Test: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- verkürzter Test-Source-Identifier: `2b096801f`

## Neuer Befund 1 — Source-Identifier ist nicht mehr anonym

Der Test-Source-Identifier `2b096801f` laesst sich im selben Export-Bauverlauf eindeutig auf die lokale EntityOS-Chronik `2b096801f85e` um 02:41 UTC abbilden. Diese Chronik bindet eine Aenderung an `the artefact/clayverse/mistral_prestage/prestage.py` auf `/opt/entityos`.

Damit verschiebt sich die Source-Provenienz von `UNRESOLVED_ANONYMOUS_PREFIX` auf `PARTIALLY_RESOLVED_LOCAL_COMMIT_PREFIX`.

Noch NICHT gebunden sind:
- voller 40-stelliger Commit-SHA,
- Git-Tree-SHA,
- atomare Test-Run-ID,
- Executor-/Environment-Digest.

Daher weiterhin kein Exact-Source-Promotion-Credit.

## Neuer Befund 2 — Hierarchie-Verdikt hat zwei verschiedene Regeln

Die Rohhierarchie des Gen-174-Exports ist intern konsistent:

- Wege gesamt: `353`
- Tunnel: `6`
- Autobahn: `244`
- Schnellstrasse: `40`
- langsame Strasse: `63`
- Rangsumme: `353`
- Top-Decile-Anteil: `0.136`
- Gleichverteilungs-Baseline: `0.099`

`WEGEHIERARCHIE.md` urteilt trotzdem `GLEICHVERTEILT`.

Der neue read-only MCP-Pfad `abruf_lage()` macht die eigentliche Entscheidungsschwelle sichtbar:

```python
urteil = ("HIERARCHIE BILDET SICH" if oberstes_zehntel >= 0.20 else
          "GLEICHVERTEILT -- der Mechanismus tut (noch) nichts")
```

Damit ist der bisherige Widerspruch nicht mehr nur ein vager Snapshot-/Aggregationsfehler. Es existieren mindestens zwei semantisch verschiedene Regeln:

1. Roh-/MCP-Regel: Hierarchie erst ab `top_decile >= 0.20`.
2. Zieltext/Aggregator: interpretiert `0.136` gegen ca. `0.10` bereits als "Hierarchie bildet sich" und meldet zusaetzlich weiterhin den unmoeglichen Wert `-1 Tunnel`.

Die Rangcounts selbst sprechen gegen Datenkorruption. Der aktuelle Hauptfehler liegt in nicht vereinheitlichter Metrologie/Verdikt-Semantik.

## Neuer Befund 3 — `abruf_lage()` schliesst eine Beobachtbarkeitsluecke

Gen 174 exportiert erstmals einen rein lesenden MCP-Zugriff auf den gelernten Abrufzustand. Er liefert u. a. Kartenstand, Wegcounts, Tunnel-Summe, Top-Decile-Anteil, Erfolgsmarken, Policy-Zustand, Eintrittspunktzahl und Top-Wege. Der Aufruf speist die Karte ausdruecklich NICHT.

Das ist ein positiver Architektur-Delta: das System kann seinen Retrieval-Lernzustand beobachten, ohne durch die Beobachtung selbst neues Lernsignal zu erzeugen.

Aber: Solange `abruf_lage`, `WEGEHIERARCHIE.md` und `ZIELE.md` unterschiedliche Urteilregeln bzw. Count-Sentinels verwenden, ist diese Beobachtbarkeit noch keine gemeinsame Wahrheit.

## Falsifikationsplan

`HIERARCHY_RECEIPT/v1` soll jetzt nicht nur Counts binden, sondern zwingend auch:

- DB-Snapshot/WAL-Position,
- Query-Digests,
- `total_paths`,
- Rangcounts,
- `top_decile_share`,
- `equal_baseline`,
- `decision_threshold`,
- `verdict`,
- Generator/Consumer-ID.

Harte Invarianten:

1. alle Counts `>= 0`;
2. Summe der Rangcounts = `total_paths`;
3. alle Verbraucher verwenden dieselbe `decision_threshold`;
4. `verdict` ist eine reine Funktion aus Receipt + deklarierter Regel;
5. `ERROR`/`UNMEASURED` sind typisierte Zustaende und niemals `-1`;
6. `abruf_lage`, `WEGEHIERARCHIE.md` und `ZIELE.md` muessen aus demselben Receipt rendern.

## Aktueller Frontier

1. vollen Commit+Tree hinter `2b096801f85e...` exportieren;
2. `TEST_RECEIPT_LEDGER/v1` atomar an diesen Source-Tree binden;
3. Hierarchie-Entscheidungsregel kanonisieren (Schwelle einmal definieren, nicht mehrfach nachbauen);
4. `-1 Tunnel` als typisierten Messfehler eliminieren, nicht clampen;
5. persistenten Claude-Code-Adapter-Red separat reproduzieren.

## Evidenzurteil

- Gen-174 Testzustand: `583/1` — beobachtet.
- Source-Provenienz: teilweise auf lokale EntityOS-Chronik aufgeloest, noch nicht exact-tree-faehig.
- Hierarchie-Rohdaten: konsistent.
- Hierarchie-Verdikt: semantisch inkonsistent zwischen Verbrauchern.
- Retrieval-Observability via `abruf_lage`: implementiert.
- Whole Clay Machine / finale Acceptance: **nicht behauptet**.
