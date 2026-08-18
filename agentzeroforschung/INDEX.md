# AgentZeroForschung — Zentraler Index

## Direktiven und Methoden

- `README.md` — aktive Forschungsrolle und zentrale Ablage
- `GO_PROTOCOL.md` — einzige Bedeutung des Triggers `go`
- `EVIDENCE_MODEL.md` — Evidenzklassen, Kausalitaet, Replikation, Emergenz
- `MESSGERAETE_REGISTER.md` — aktuelle und zukuenftige Messkanaele

## Analysen

1. `analysen/2026-08-18T041853Z_BASELINE.md`
   - Generation 31
   - Vergleich 04:15:21Z -> 04:18:53Z
   - kognitive Kernzaehler stabil
   - Export-/Instrumentierungsdelta klar sichtbar
   - erste Hypothesen zu Puls, Retrieval-Lernen und Tabellenzuwachs

2. `analysen/2026-08-18T042641Z_INVENTUR_UEBERBLICK.md`
   - Vollinventur aller aktuellen Datenfamilien auf Snapshot 04:26:41Z
   - 34 Manifest-Artefakte; UnifiedDB-Metrologie und direkter Zero-Laufzeitbestand getrennt
   - neue Instrumente `bauverlauf/`, `tests/`, `ZIELE.md`, `karten/*.meta.json` aufgenommen
   - aktuelle Forschungsgrenzen: keine Gen-31-Verhaltensstichprobe, Andreas 0 Turns, Retrieval-Lernen 0
   - Instrumentenwidersprueche bei Tool-Erreichbarkeit und Kartenzaehler als UNRESOLVED markiert

3. `analysen/2026-08-18T044854Z_ENTITYOS_FERTIGSTELLUNG.md`
   - neue Fertigstellungsbewertung auf Snapshot 04:48:54Z / Generation 31
   - aktive Zielmatrix: 21/28 = 75 % (Gastkern bewusst zurueckgestellt)
   - funktionaler Systemkern geschaetzt ca. 80–85 %, finale Acceptance-Reife ca. 60–70 %
   - aktueller Testlauf: 479 gruen / 13 rot; rote Tests betreffen mehrere Kerninvarianten
   - kritischer Restpfad: Effect/Causal/Re-ingest/State-Authority/Fail-closed, MCP-Werkzeugpfad, reale Autonomie, Retrieval-Lernen
   - neues `messwerk/` als Forschungsinstrument beruecksichtigt

4. `analysen/2026-08-18T051855Z_ENTITYOS_FERTIGSTELLUNG_UPDATE.md`
   - Snapshot 05:18:55Z / Generation 31
   - aktive Zielmatrix unveraendert 21/28 = 75 %
   - funktionaler Systemkern weiter ca. 80–85 %, finale Acceptance-Reife vorsichtiger ca. 55–65 %
   - Tests 475 gruen / 18 rot
   - Zero-Verkehr 10 -> 14 Turns; erstmals 4 Andreas-Turns; Kausal-/Workspace-/Retrieval-Episoden 5 -> 7
   - Retrieval-Lernen weiterhin 0 Entry-Points / 0 Feedback / 0 durable memory

## Offene Forschungsfront

- Gen-31-Turns gegen Gen 29 vergleichen;
- Andreas-Turns als Cross-user-Replikation gegen Gabriel binden;
- Tool-Erreichbarkeit zwischen Chat, Laufzeitskizze, Messwerk und Zielpruefer operational trennen;
- Snapshot-Zaehler gegen `.meta.json`-Sidecars pruefen;
- Pulsfehler (`database is locked`) ueber Vollzeitaggregate statt nur Rolling-Tail-Stichprobe messen;
- rote Tests als Zeitreihe gegen reale Zero-Episoden korrelieren;
- Retrieval-Feedback/Entry-Point-Lernen als Zeitreihe verfolgen;
- Graph-Teilprojektion gegen Vollgraph-Samplingregel spezifizieren;
- Baucommits als Interventionen mit nachfolgenden Messwerten zeitlich verbinden;
- jede neue Messdatenfamilie registrieren und auf Sampling-/Instrumentenbias pruefen.
