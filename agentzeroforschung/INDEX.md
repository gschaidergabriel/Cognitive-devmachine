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

## Offene Forschungsfront

- ersten echten Gen-31-Turn gegen Gen 29 vergleichen;
- ersten Andreas-Turn als Cross-user-Replikation binden;
- Tool-Erreichbarkeit zwischen Chat, Laufzeitskizze, Messwerk und Zielpruefer operational trennen;
- Snapshot-Zaehler gegen `.meta.json`-Sidecars pruefen;
- Pulsfehler (`database is locked`) ueber Vollzeitaggregate statt nur Rolling-Tail-Stichprobe messen;
- rote Tests als Zeitreihe gegen reale Zero-Episoden korrelieren;
- Retrieval-Feedback/Entry-Point-Lernen als Zeitreihe verfolgen;
- Graph-Teilprojektion gegen Vollgraph-Samplingregel spezifizieren;
- Baucommits als Interventionen mit nachfolgenden Messwerten zeitlich verbinden;
- jede neue Messdatenfamilie registrieren und auf Sampling-/Instrumentenbias pruefen.
