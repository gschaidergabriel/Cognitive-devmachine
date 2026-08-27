# Generation 159 — Export-Latenz normalisiert, Spike vorerst transient

Gebundener AgentZero-Export: `abe9855e0ebb4b7bc4ae6dc98ad65190429fdcb7`
Tree: `fa738c41a90b69cf23f5d1ed4991c32f3fd84af8`
Vergleichsexport: `fd9ad8ab49b0180e5a493589786c63c6c5ac164c`

## Befund

Der zuvor beobachtete Export-Latenzsprung auf ca. 168.79 s repliziert sich in den beiden danach beobachteten regulären Exporten nicht. Der Export um 23:11 UTC dauerte 47.8 s, der Export um 23:41 UTC 43.03 s. Damit ist der einzelne 168.79-s-Wert aktuell besser als transienter I/O-/Lock-/Host-Load-Spike klassifiziert als als bereits bewiesener struktureller Skalierungsfehler.

Diese Klassifikation bleibt vorläufig: Ein einzelner Ausreißer plus zwei Normalwerte reichen nicht, um einen datenabhängigen Hotspot endgültig auszuschließen. `EXPORT_RECEIPT/v1` bleibt sinnvoll; mindestens sechs normale Läufe mit Phasenzeiten, SQLite-Wait/Lock-Zeit, CPU/RSS/I/O und COMPLETE/INCOMPLETE/ERROR-Zustand sollten gesammelt werden.

## Testfrontier

Der aktuelle Test-Receipt auf dem neuesten Export bleibt stabil bei 583 grün / 1 rot. Der einzige rote Test ist weiterhin:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Der verkürzte Source-Identifier bleibt `b1c7e0383`; vollständiger Commit+Tree sind damit weiterhin nicht gebunden. Deshalb kein Promotion-Credit.

## Hierarchie

Die Wegehierarchie bleibt unverändert widersprüchlich: 352 Wege, davon 6 Tunnel; Top-Decile-Qualitätsanteil 0.136 gegenüber 0.099 Gleichverteilungs-Baseline, aber Verdict weiterhin `GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts`. Die Rohcounts sind intern konsistent; offen bleibt die Verdict-Regel bzw. Snapshot-/Aggregator-Bindung.

## Bewertung

- Export-Latenz-Spike: `TRANSIENT_CANDIDATE`, nicht als struktureller Fehler bewiesen.
- Testoberfläche: stabil 583/1.
- Persistenter deterministischer Frontier: Claude-Code-Runtime-Adapter-Isolation.
- Hierarchie-Metrologie: weiter offen.
- Whole Clay Machine: nicht beansprucht.

## Nächster höchster Informationsgewinn

1. `EXPORT_RECEIPT/v1` über mindestens sechs reguläre Läufe sammeln.
2. Vollständigen Commit+Tree hinter `b1c7e0383` binden und `TEST_RECEIPT_LEDGER/v1` herstellen.
3. Den Adapter-Test in die vier Teilinvarianten toolless / ephemeral / structured / environment-isolated zerlegen und wiederholt auf identischem isoliertem Ubuntu ausführen.
4. `HIERARCHY_RECEIPT/v1` mit expliziter Verdict-Schwelle an denselben DB-Snapshot binden.
