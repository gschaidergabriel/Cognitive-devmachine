# Generation 159 — Export-Latenzspitze bei stabilem Produkt-Frontier

## Bind

- Snapshot: `150c3766dcdeae16df711cd306d4f21ab4d07f0e`
- Tree: `f24e280efdcdcc2a378fbeafd296857dd03fc846`
- Exportzeit: `2026-08-19T22:41:11Z`
- Generation: 159
- direkter Vorgaenger: `3c5f8b6b098f207551cf53a57b2dae10d6309fde` (`2026-08-19T22:11:12Z`)

## Beobachtung

Der AgentZero-Export benoetigte im aktuellen Snapshot `168.79 s`; im unmittelbar vorherigen Snapshot waren es `52.47 s`. Das ist Faktor `3.217` bzw. +`116.32 s` ohne proportionalen Datenzuwachs.

Gleichzeitig bleibt der harte Produkt-Frontier stabil:

- Tests: `583 gruen / 1 rot`
- einziger Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt-Source weiterhin nur `b1c7e0383`
- Wegehierarchie weiterhin 352 Wege = 244 Autobahn + 40 Schnellstrasse + 62 langsame Strasse + 6 Tunnel
- Hierarchie-Verdikt weiterhin `GLEICHVERTEILT`, obwohl Top-Decile `0.136` gegen Baseline `0.099`
- ZIELE-Aggregator weiterhin mit `-1 Tunnel`; Aggregations-/Verdiktproblem bleibt offen.

Der eigentliche Datenzuwachs im 30-Minuten-Delta ist klein: Baunotizen `2792 -> 2798`, Artikel `17885 -> 17891`, zugeordnete Artikel `17888 -> 17894`, Puls-Gesamtzeilen `7736 -> 7768`, Bauverlauf `889 -> 890`.

## Ableitung

Die Export-Latenzspitze ist prima facie kein einfacher O(N)-Effekt aus dem Datenwachstum. Ein Zuwachs im Promillebereich erklaert keine 3.2x Laufzeitsteigerung, sofern der Exportpfad und seine asymptotische Arbeit unveraendert sind.

Status: `OBSERVED_AT_SNAPSHOT`.

## Haupt-Hypothese H1 — I/O-/Lock-/Concurrent-Load-Spike

Der Exporter konkurrierte waehrend dieses Laufs mit einer anderen DB-/Filesystem-Last, wartete auf SQLite-/Storage-I/O oder traf einen langsamen Mount-/Cache-Zustand.

### Erwartete Beobachtungen unter H1

- starke Laufzeitschwankung zwischen benachbarten Exporten bei nahezu gleichem Datenvolumen;
- einzelne Exportphasen dominieren die Zusatzzeit;
- erhoehte SQLite-busy/wait-Zeit, iowait oder Storage-Latenz waehrend langsamer Exporte;
- spaetere Exporte koennen ohne Produktcodeaenderung wieder nahe Baseline fallen.

## Gegenhypothese H2 — datenabhaengiger Superlinear-/Hotspot-Pfad

Ein bestimmter Exportteil skaliert nicht mit Gesamtzahl der neuen Datensaetze, sondern z. B. mit Full-Scan, FTS-Rebuild, Graphprojektion, Sortierung oder Snapshot-Serialisierung. Ein kleiner Delta kann dann einen Schwellenwert oder Cache-Miss ausloesen.

### Erwartete Beobachtungen unter H2

- dieselbe Phase ist reproduzierbar langsam, auch ohne konkurrierende Last;
- Laufzeit korreliert mit einem spezifischen Volumenindikator (z. B. Dateikorpus, Graphkanten, FTS, Wiki-Umfeld) statt mit dem 30-Minuten-Delta;
- Warm-/Cold-Cache-Wiederholungen zeigen strukturierten Unterschied.

## Versteckte Annahmen

1. `dauer_sekunden` misst denselben Start-/Endpunkt in beiden Exporten.
2. Zwischen den beiden Snapshots wurde der Exporter selbst nicht wesentlich veraendert.
3. Der aktuelle Snapshot ist kein absichtlich erweiterter Vollscan.
4. Die 3.2x-Latenz ist nicht nur Scheduler-/Provider-Jitter.

## Billigster diskriminierender Falsifikator

Nicht Produktcode aendern. Die naechsten mindestens 6 regulaeren Exporte instrumentieren und pro Phase monotone Laufzeiten binden:

`EXPORT_RECEIPT/v1`

Pflichtfelder:

- export_run_id
- source commit/tree
- generation
- monotonic start/end
- phase durations: DB-open, schema, counters, tests, ZIELE, hierarchy, wiki, file corpus, graph, cards, manifest, git/write
- rows/files/bytes per phase
- SQLite busy/locked count + wait duration
- process CPU time, max RSS
- host iowait/read/write bytes soweit verfuegbar
- cache mode / cold-vs-warm marker, falls messbar
- terminal state: COMPLETE | INCOMPLETE | ERROR

### Entscheidungsregel

- Wenn die Zusatzzeit in Wait/I/O/Lock konzentriert ist und spaetere Exporte zur Baseline zurueckkehren: H1 gewinnt (`REPLICATED` erst nach mindestens 2 langsamen oder 2 schnellen Gegenbelegen).
- Wenn dieselbe Exportphase dauerhaft dominiert und mit einem Volumenindikator waechst: H2 gewinnt und bekommt einen gezielten Performance-Falsifikator.
- Ohne Phasenreceipt keine Optimierung und kein Produktregressions-Credit.

## Adversarial Review

- Ein langsamer Export beweist keine langsamere EntityOS-/Zero-Kognition.
- Exportdauer darf nicht mit Turn-Latenz oder Inference-Latenz vermischt werden.
- Die stabile `583/1`-Suite ist unabhaengige Evidenz dafuer, dass der bekannte funktionale Frontier in diesem Snapshot nicht sichtbar degradierte.
- Der Hierarchie-Widerspruch bleibt ein separater Mess-/Verdiktfehler und wird nicht durch die Exportlatenz erklaert.

## Fusion

### Neu gelernt

Die aktuelle Forschungsoberflaeche hat jetzt neben Test-/Aggregations-Metrologie einen eigenstaendigen Performance-Messbedarf: Der Exporter selbst kann in einen >3x langsameren Zustand geraten, ohne dass ein proportionaler Systemdelta sichtbar ist.

### Naechster hoechster Informationsgewinn

`EXPORT_RECEIPT/v1` mit Phasenzeiten ueber mehrere regulaere Exporte. Erst damit laesst sich Lock/I/O-Jitter von einem datenabhaengigen Hotspot trennen.

### Status

- Export-Latenzspitze: `OBSERVED_AT_SNAPSHOT`
- H1 I/O/Lock/Load: `RETAINED_HYPOTHESIS`
- H2 superlinearer Hotspot: `RETAINED_HYPOTHESIS`
- funktionaler Testfrontier: weiter `583/1`
- Whole Clay Machine: nicht behauptet
