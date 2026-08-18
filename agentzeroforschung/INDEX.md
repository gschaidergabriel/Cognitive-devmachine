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

5. `analysen/2026-08-18T071856Z_ENTITYOS_NEUBEWERTUNG.md`
   - Snapshot 07:18:56Z / Generation 32
   - aktive Zielmatrix 22/28 = 78,6 %
   - funktionaler Systemkern geschaetzt ca. 84–88 %, finale Acceptance-Reife ca. 62–70 %
   - Tests vom Tief 475/18 auf 478/15 verbessert und ueber mehrere Laeufe stabil
   - Zero-Verkehr 14 -> 24 Turns; Kausal-/Workspace-/Retrieval-Episoden 7 -> 12; Checkpoints 39 -> 41
   - Messwerk 8 direkt GEMESSEN; Causal Credit Horizon erstmals ueber Verkehrsschwelle
   - Restblocker: MCP-Werkzeuge, Retrieval-Lernen/Wegehierarchie, Provider-Erreichbarkeit, 4. Clay-Dienst, Uebersetzer und 15 rote Kerninvarianten

6. `analysen/2026-08-18T072700Z_TOKEN_EFFIZIENZ_PIPELINE.md`
   - Mistral-Vorstufe -> Zero/Caveman -> Mistral-Small-Uebersetzer als aktueller Headless-Pfad bewertet
   - harte Befunde: Hook-/Identitaetsanker 5550 -> 206 Zeichen = 96,29 % Reduktion dieses Bestandteils; Retrieval-Paket ca. 21 % weniger Tokens je gleicher Faktenmenge
   - Uebersetzer-Eval: 96-98 % Pass, 99,1-99,6 Faithfulness, 0 Fabrications im 50er-Set
   - ordinary Claude/Zero-Tokenlast vorsichtig als ca. 35-60 % niedriger INFERIERT; globale Pipeline-Tokenersparnis bleibt ohne provider-native Usage-Zaehlung UNRESOLVED
   - vorgeschlagenes hoechstwertiges Messgeraet: TOKEN_LEDGER + kontrollierter Direct-vs-Pipeline-Shadow-Vergleich

7. `analysen/2026-08-18T074540Z_GENERATION33_MESSINTEGRITAET.md`
   - Generation 33; UnifiedDB-Schemaexport erstmals vollstaendig 87/87
   - Laufzeitzaehler steigen auf 45 Turns / 22 Causal / 23 Retrieval / 23 Workspace Episodes
   - harte Messinkonsistenz: `letzter-lauf.json` 478/15 vs `ZIELE.md` 479/14 am selben Export-Head
   - keine Promotion aus widerspruechlichen Testzaehlern
   - naechstes hoechstwertiges Instrument: atomarer `TEST_RECEIPT_LEDGER/v1` mit Run-ID, Source-SHA, Suite-/Result-Digest und Fail-Liste

8. `analysen/2026-08-18T074200Z_CLAUDE_TOKEN_ERSPARNIS.md`
   - Kostenlinse explizit auf Claude-Code-Tokens eingeschraenkt; Mistral unter der Eignerannahme kostenlos
   - Quellcode bestaetigt: voller World-/Recent-Kontext geht an Mistral, nur der verdichtete `caveman_prompt` an `claude -p`; Toolauswahl separat
   - Headless Claude deaktiviert Prompt-History, Auto-Memory, CLAUDE.md-Autoloading, Background Tasks und Session-Persistenz
   - aktuelle Planungs-Schaetzung: normale Turns ca. 50-70 % weniger Claude-Tokens, schwere Build-/Toolturns ca. 35-55 %; Arbeitswert ~60 % bzw. ~2,5x Arbeit je Claude-Tokenbudget
   - Gesamtquote bleibt INFERENCE bis `CLAUDE_TOKEN_LEDGER` + Direct-vs-Pipeline-A/B vorliegt; `outsourced`-Feld allein wird nicht als realisierte Ersparnis gezaehlt

## Offene Forschungsfront

- Generation 31 gegen Generation 32 auf Recovery-/Verhaltensdivergenz vergleichen;
- Andreas- und Gabriel-Verhalten als Cross-user-Replikation untersuchen, ohne private Inhalte zu vermischen;
- Tool-Erreichbarkeit zwischen Chat, Laufzeitskizze, Messwerk und Zielpruefer operational trennen;
- provider-native TOKEN_LEDGER je Pipeline-Stufe bauen/messen und Direct-vs-Pipeline-Shadow-Baseline etablieren;
- `TEST_RECEIPT_LEDGER/v1` als atomare Quelle fuer `letzter-lauf.json`, `ZIELE.md` und Acceptance-Zaehler etablieren;
- Pulsfehler (`database is locked`) ueber Vollzeitaggregate statt nur Rolling-Tail-Stichprobe messen;
- rote Tests als Zeitreihe gegen reale Zero-Episoden und Bauinterventionen korrelieren;
- Retrieval-Feedback/Entry-Point-Lernen als Zeitreihe verfolgen;
- Graph-Teilprojektion gegen Vollgraph-Samplingregel spezifizieren;
- Baucommits als Interventionen mit nachfolgenden Messwerten zeitlich verbinden;
- jede neue Messdatenfamilie registrieren und auf Sampling-/Instrumentenbias pruefen.
