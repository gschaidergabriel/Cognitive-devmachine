# Generation 159 — PTY-Recovery ohne Fix-Credit und Hierarchie-Verdikt bleibt unkalibriert

## Bindung

Gebundener AgentZero-Snapshot: `a91dcc32d54848f6431e9d1d8e4254f56cafdfbf`, Exportzeit `2026-08-19T21:41:11Z`, Generation 159.

Der unmittelbar vorherige Export `d955eb081f245ef607c3ed9655274ea6b5c4a7e9` liegt 30 Minuten zuvor. Der Compare zeigt ausschließlich Export-/Messartefakte unter `agentZero/`; kein neuer Produkt-Source-Pfad ist zwischen diesen beiden Snapshots sichtbar.

## Neue Beobachtung 1 — PTY wieder gruen, aber kein Fix-Credit

`agentZero/tests/letzter-lauf.json` meldet wieder `583 gruen / 1 rot`. Einziger roter Test ist weiterhin:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Der im vorherigen Forschungszyklus erneut rote PTY-Test ist damit wieder verschwunden, ohne sichtbares Produkt-Source-Delta zwischen den beiden periodischen Exporten.

**Status:** `REPLICATED_NONDETERMINISM` fuer die PTY-Familie bleibt bestehen; `FIX_CREDIT = 0`.

### Haupthypothese

Die PTY-Reds werden durch Timing/Race, Executor-/Environment-State oder nicht atomar gebundene Testbedingungen ausgeloest.

### Gegenhypothese

Ein externer Produktfix existiert, wird aber vom Export nicht mittransportiert und ist deshalb im Research-Repo unsichtbar.

### Billigster diskriminierender Test

`TEST_RECEIPT_LEDGER/v1` plus `PTY_LEASE_TRACE/v1`: Full Commit+Tree, Environment-/Executor-Digest, monotone Eventzeiten, Session-/Lease-ID, Blocking-Read-Grenzen und mindestens 30 identische Wiederholungen baseline + kontrollierte Last. Ohne diese Bindung darf weder Rot noch Gruen als Fix-/Regression-Credit gelten.

## Neue Beobachtung 2 — Hierarchie-Rohdaten stabil, Verdict weiterhin nicht mechanisch erklaert

`agentZero/abruf/wegehierarchie.json` ist intern konsistent:

- Wege gesamt: 352
- Autobahn: 244
- Schnellstrasse: 40
- langsame Strasse: 62
- Tunnel: 6
- Rangsumme: 352
- oberes Zehntel haelt: 0.136
- Gleichverteilungs-Baseline: 0.099

Trotzdem lautet das maschinelle Urteil weiterhin:

`GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts`

Das ist kein Count-Fehler mehr. Die offene Frage ist jetzt die **Entscheidungsregel**: 0.136 liegt rund 37 % ueber 0.099, waehrend der Hilfetext selbst sagt, deutlich mehr als die Gleichverteilung sei die erwartete hierarchische Form. Ohne explizite Schwelle ist das Verdict nicht reproduzierbar.

**Status:** `MECHANISM_SUPPORTED` fuer konsistente Rangbildung; `VERIFIED_AT_SCOPE = NO` fuer die Behauptung einer nuetzlichen Hierarchie.

### Haupthypothese

Der Verdict-Code verwendet eine harte, nicht exportierte Schwelle oder eine zusaetzliche Metrik, die im Receipt fehlt.

### Gegenhypothese

Der Text/Receipt und der Verdict-Generator stammen nicht aus exakt demselben DB-Snapshot bzw. konsumieren unterschiedliche Quellen.

### Billigster diskriminierender Test

`HIERARCHY_RECEIPT/v1` muss Query-Digests, DB-Snapshot-ID, Rangcounts, Top-Decile-Wert, Baseline, explizite Schwelle und daraus deterministisch berechnetes Verdict in **einem** atomaren Receipt binden. Keine freie Textentscheidung ausserhalb dieses Receipts.

## Weitere Deltas

Zwischen den beiden juengsten Exporten wachsen Baunotizen 2786 -> 2790, Pulszeilen 7671 -> 7703, Wissenszuordnungen 17882 -> 17886 und Kanten 117404 -> 117639. Diese Zunahmen sind echte Laufzeit-/Korpusaktivitaet, aber sie liefern keinen direkten Kausalbeweis fuer PTY-Stabilitaet oder Hierarchiequalitaet.

## Fusion

1. PTY bleibt eine reproduzierte Nichtdeterminismus-Familie; aktuelles Gruen ist **kein Fixbeweis**.
2. Der Claude-Code-Adapter bleibt der einzige repliziert persistente rote Test und damit der staerkere deterministische Produkt-Frontier.
3. Die Wegehierarchie-Rohcounts sind belastbar; das Problem hat sich von negativer Count-Metrologie auf eine fehlende/unklare Verdict-Regel verschoben.
4. Der hoechste Informationsgewinn kommt jetzt von atomaren Receipts, nicht von weiteren ungeordneten Produktpatches.

## Naechste Prioritaet

1. `TEST_RECEIPT_LEDGER/v1` + Exact Source/Tree.
2. `PTY_LEASE_TRACE/v1` mit kontrollierter Wiederholungsserie.
3. `HIERARCHY_RECEIPT/v1` mit expliziter Verdict-Schwelle.
4. Claude-Code-Adapter in vier Teilinvarianten zerlegen: toolless, ephemeral, structured, env-isolated.

Whole Clay Machine: **NOT CLAIMED**.
