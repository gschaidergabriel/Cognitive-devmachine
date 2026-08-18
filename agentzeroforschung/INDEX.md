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

## Offene Forschungsfront

- ersten echten Gen-31-Turn gegen Gen 29 vergleichen;
- ersten Andreas-Turn als Cross-user-Replikation binden;
- Tool-Erreichbarkeit zwischen Chat, Laufzeitskizze und Zielpruefer operational trennen;
- Snapshot-Zaehler gegen `.meta.json`-Sidecars pruefen;
- Pulsfehler (`database is locked`) ueber Vollzeitaggregate statt nur Rolling-Tail-Stichprobe messen;
- rote Tests als Zeitreihe gegen reale Zero-Episoden korrelieren;
- Retrieval-Feedback/Entry-Point-Lernen als Zeitreihe verfolgen;
- Graph-Teilprojektion gegen Vollgraph-Samplingregel spezifizieren;
- Baucommits als Interventionen mit nachfolgenden Messwerten zeitlich verbinden;
- jede neue Messdatenfamilie registrieren und auf Sampling-/Instrumentenbias pruefen.
