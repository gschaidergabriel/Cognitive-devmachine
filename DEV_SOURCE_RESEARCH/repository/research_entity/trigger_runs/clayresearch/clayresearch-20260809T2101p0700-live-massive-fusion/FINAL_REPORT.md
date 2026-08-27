# Clay/FRANK Live-Forschungsfusion — 2026-08-09

Status: `SUBSTANTIVE_DELTA / NO_PROMOTION / NO_TRAINING`  
Actor: `chatgpt-secondary` (`RESEARCH_ENTITY_TEMPORARY_WORKER`, nicht Frank)  
Kanonischer Parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Repo-Cutoff: `565932ad22b9eca704a6a3434c288e6bf2fbeb92`  
Programmphase: `BASE_CLAYCODE_RELEASE` / formaler Gate-Status `NOT_PASS`

## Verdichtetes Urteil

1. **Der UDB-Emergenz-Meter wurde enger adjudiziert.** v0.2 bleibt ein synthetischer Fünf-Regime-Klassifikator. Die gespeicherten `0/1600` negativen Kontrollpromotionen sind weder eine allgemeine False-Positive-Grenze noch unabhängige Replikation. Pseudoreplikation, Nullmodellwahl, in-sample Makrosuche, redundante Synergie und verborgene Pfade erzeugten direkte Gegenbeispiele.

2. **Der neue 2.880-Läufe-Test stützt Qualitätsgating nur relativ, nicht absolut.** Bei gleicher 75%-Abdeckung hatte das extern vertrauenswürdige Qualitätsgate `121/2160 = 5,602 %` Fehler und 12 falsche Negativkontroll-Promotionen; `sample_count` hatte `251/2160 = 11,620 %` und 75. Unter Cross-Channel-Leakage scheiterte auch extern gemessene Qualität. Selbstattestierte perfekte Qualität erzeugte `314/2880 = 10,903 %` Fehler und 83 falsche Promotionen. Provenienzursprung ist nötig, aber nicht hinreichend.

3. **GWT/Emergenz bleibt ein Vektor, kein Skalar.** Beizubehalten sind: (a) Schwelle/Ignition, (b) typisierte Zustellung/Rekonstruktion, (c) kausale Receiver-Nutzung via Läsion/Rettung und (d) wahrheitsgebundene versus gematcht-geshuffelte Provenienz-Reentry. Neue Primärquellen stützen wiederverwendbare kausale Interfaces, liefern aber zugleich die starke Gegenhypothese, dass Ignition am Readout-Commit statt in einem globalen Workspace entsteht. Keine dieser Arbeiten rechtfertigt eine Bewusstseinsbehauptung.

4. **ClayCode WP02 besitzt nun zwei konkrete Frontend-Gegenbeispiele.** Die V6-Reparatur beseitigte den LALR-Konflikt, regressierte aber die kanonische Form `4B_need_not_learn Needle.owns`; V8/V9 trennen denselben Punkt lexikalisch und sind nur Kandidaten. Zusätzlich benutzt die reale FRANK-Quelle `use`, `fn`, `let`, `require`, `return`, die in der aktuellen BASE-V5-Oberfläche nicht enthalten sind. Das öffnet einen ausführbaren Diskriminator: kleinste versionierte Grammatikerweiterung gegen explizite, deterministische Dialekt-/Pre-Lowering-Brücke. Kein WP02-PASS ohne exakte Ubuntu-Receipts.

5. **ActiveAssembly ist derzeit eher Implementierungs- als Semantiklücke.** Der eingefrorene G9-Vertrag enthält generische Records, Sets, geordnete Strukturen, Optional-/Union-Typen sowie Capability-/Effect-Gesetze. Daher zuerst generische kanonische Serialisierung, SHA, Sortierung, Set/Ordered/Record-Substrat bauen und das H1-ActiveAssembly differential portieren. FRANK-spezifische Syntax oder semantische Lockerung ist erst zulässig, wenn ein ausführbarer generischer Realisierungsversuch scheitert.

6. **EffectWorld darf nicht in WIT kollabieren.** WASI 0.3 wurde am 11. Juni 2026 als stabile Spezifikation ratifiziert; die aktuelle `wasmtime_wasi::p3`-Dokumentation 49.0.0 nennt ihre Implementierung zugleich experimentell, unvollständig und nicht produktionsreif. WIT beschreibt Imports/Exports und Typkompatibilität, nicht konkrete Grants, Attenuation, Revocation, Budgets oder semantischen Effekt-Erfolg. Formel: `EffectWorld = WITWorld + GrantManifest + EffectPolicy + ReceiptSchema`.

7. **Fabric/UnifiedDB/ClayGraph werden selektiver.** Compiler-/Runtime-signierte harte Dependencies dürfen inkrementelle Invalidierung treiben; beobachtete Kanten brauchen Validierung, modellvermutete Kanten nur Retrieval. Ein globaler Merkle-Root bleibt Audit-Wurzel, aber nicht universeller CAS. Physisch getrennte Projektionen benötigen Frontiers/Watermarks und Read-Set-Konsistenz statt nur eines gleichen Epoch-Namens. Hub-Updates, Cross-Store-Cuts und External-Effect-Dual-Writes bleiben offene Failure Surfaces.

## Evidenz- und Unabhängigkeitsledger

| Befund | Ursprung | Unabhängigkeit | Adjudikation |
|---|---|---:|---|
| v0.2 `0/1600` | gespeicherte synthetische Matrix | gleiche Code-/Datenlinie | nur Ancestry; kein universeller Bound |
| v0.2 Kompatibilitätslauf, Hash `d4f802…` | Draw-API-Shim, Entscheidungslogik unverändert | gleiche Linie | exakte Re-Ausführung; Originalskript bleibt kaputt |
| v0.2 Methodenfalsifikation | repo-native synthetische Angriffe | neuer Test, gleiche Forschungsfamilie | starke Invalidation einer Zuverlässigkeitslesart |
| 2.880 strukturierte Korruptionsläufe | neue Seeds/Topologien, synthetisch | nicht live, nicht unabhängig vom Provider | Kandidatenevidenz; Cross-Channel-Leakage ist dominanter Angriff |
| Hidden APIs / Readout-Ignition | externe Primärarbeiten | von Repo-Artefakten unabhängig | konkurrierende Mechanismen, keine GWT- oder Bewusstseins-Promotion |
| FRANK-Frontend-Gap | direkte Quelltextdifferenz | repo-intern, statisch | Untersuchung wieder geöffnet; Ausführung noch erforderlich |
| WASI/WIT/SLSA | externe Standards/Primärdokumentation | unabhängig | Architekturgrenzen, keine semantische Effektbescheinigung |

Abstammungsregel: Paraphrasen, Worker-Wiederholungen und gleiche Seed-/Code-Familien erhöhen keine Evidenzmasse. Eine Root-Quelle wird einmal gezählt; neue Ableitungen erhöhen nur Suchbarkeit. Aktivierung ist keine Evidenz.

## Testbare Hypothesen und Gegenhypothesen

| ID | Hypothese | Stärkste Gegenhypothese | Kleinster diskriminierender Test | Räume |
|---|---|---|---|---|
| H-UDB-EM-008 | Mehrdimensionale externe Datenqualität schlägt `log(n)` auf held-out Topologien. | Qualität ist nur ein korrelierter Proxy; Topologie dominiert. | Prädiktive Modelle `quality`, `log(n)`, Interaktion auf neuen Blocks; selektiver Fehler + FP bei gleicher Abdeckung. | emergenz, unifieddb |
| H-UDB-EM-009 | Ein unabhängiges Bestätigungsgate mit zufälligen Negativ-Audits ist dem Volltest nicht unterlegen. | Screening verwirft genau die seltenen Gegenbeispiele. | Prospektiv cross-fit screenen; unabhängige Confirm-Phase, e-values/alpha spending, 10% zufällige Screen-Negative auditieren. | emergenz, harness |
| H-UDB-EM-010 | Strukturierte Korruptionsfamilien erzeugen identifizierbare Fehlerfingerprints. | Estimatoren reagieren nur auf Schweregrad, nicht Topologie. | Präregistrierte Clock/Missingness/Leakage/Hidden-Path-Cube auf frischen Seeds; Familienklassifikation held-out. | emergenz, unifieddb |
| H-UDB-PROV-011 | Extern geschützte Provenienz verbessert Kalibrierung, aber nur zusammen mit Intervention-Fidelity und Leakage-Tripwires. | Herkunft allein genügt oder ist nutzlos. | Observer-, Signer- und Runtime-Kompromittierung getrennt injizieren; Fail-closed Coverage/FP messen. | unifieddb, harness |
| H-GWT-CIC-002 | Der Vierachsen-CIC-Vektor prognostiziert OOD-Routing besser als jede Einzelachse. | Readout-Commit erklärt alle scheinbaren Achsen. | Forked futures × Route × Läsion/Rettung × truthful/shuffled/broken Reentry; held-out flexible routing. | gwt, emergenz |
| H-GWT-CIC-003 | Receiver-spezifische Läsion schädigt OOD-Nutzung und route-spezifische Rettung stellt sie wieder her. | Generischer Kontextgewinn oder redundante Receiver erklären die Rettung. | Informations-, Kosten- und Gain-gematchte Sham-Rettung plus Co-Läsionen. | gwt, harness |
| H-GWT-CIC-004 | Wahrheitsgebundene Provenienz-Reentry hilft mehr als payload-identische geshuffelte/gebrochene Reentry. | Reentry wirkt nur durch zusätzliche Tokens/Aktivierung. | Payload, Länge und Salienz matchen; Provenienzbindung allein mutieren. | gwt, frank |
| H-GWT-API-011 | Ein kompaktes Shared API ist workspace-artig nur bei Wettbewerb plus kausaler Receiver-Nutzung. | Ein lokales Interface ohne Broadcast reicht. | Shared/Local/Mixture/Distributed mit Wettbewerb, route lesion/rescue und OOD-Zielen vergleichen. | gwt, emergenz |
| H-CLAYCODE-AA-001 | Frozen G9 ist semantisch ausreichend, wenn generische Collections/Canonicalization implementiert werden. | ActiveAssembly benötigt neue Sprachelemente. | H1/H2-Differential für Paketidentität, Epoch, Selection, Konflikte, Ancestry, Reexpand, Hash, Authority. | claycode, harness, frank |
| H-CLAYCODE-FE-002 | Explizites versioniertes Pre-Lowering schließt den FRANK-`use/fn`-Gap kleiner als BASE-Grammatikerweiterung. | Direkte Syntaxaufnahme ist einfacher und deterministischer. | Beide Brücken prototypisieren; Roundtrip, Source-ID, Type/Effect, Regression Surface vergleichen. | claycode, frank |
| H-EFFECTWORLD-001 | WIT plus host-erzwungene Grants/Policy/Receipts liefert Least Authority; WIT allein nicht. | Typisierte Worlds reichen praktisch aus. | Zwei identische Worlds mit unterschiedlichen Grants; Gast versucht Pfad/Netz/Receipt-Fälschung. | claycode, harness |
| H-FABRIC-LOCALITY-001 | Degree-sensitives Umschalten zwischen Incremental/Lazy/Rebuild senkt p99. | Always-incremental gewinnt nach Warmup. | Komponenten- und Power-Law-Graph, Leaf/Hub/Delete; Parität, CPU, RAM, p99, Write Amplification. | claygraph, hyperposition, unifieddb |
| H-UDB-CUT-001 | Projektionsvektor + Read-Prädikat verhindert gemischte Cross-Store-Zustände. | Ein globaler Epoch-String reicht. | Delay/Reorder/Crash zwischen Event-DB, Graph, Index und Authority-Projektion. | unifieddb, claygraph |
| H-RECEIPT-001 | Gateway-signierte Receipts mit Grant-ID, Sequenz und Request-/Response-Digest verhindern kognitive Erfolgsfälschung. | SLSA-artige Herkunft genügt ohne adapterspezifische Beobachtung. | Gast schreibt Erfolgsreceipt; nur gateway-beobachteter Effekt darf akzeptiert werden. | harness, claycode |

## Neue Konzepte, einschließlich abgefahrener, aber falsifizierbarer Varianten

- **Estimator Council:** mehrere estimatorisch unterschiedliche Verfahren stimmen nicht per Mehrheitswahl ab; Divergenz führt zu `UNKNOWN`, bis ein externer Diskriminator entscheidet.
- **Ancestry-weighted Evidence Semiring:** 1/10/100 Klone derselben Root-Evidenz verändern Confidence nicht; unabhängige Root-Messungen schon.
- **Capability Shadow Graph:** ClayGraph speichert nur attenuierte opaque Handle-Referenzen und Policy-Metadaten; echte Tokens verbleiben im Gateway. Beliebige Graphmutation darf Authority nicht erhöhen.
- **Consistent-Cut Certificate:** Event-Sequenz, Canon-Version, Graph-/Index-Frontier und Authority-Version werden als lokaler kausaler Schnitt zertifiziert.
- **Hub Firebreak Generations:** Hub-Änderungen inkrementieren eine Generation; Kinder validieren lazy statt sofortiger Masseninvalidierung.
- **Workspace Immune System:** Provenienz-Reentry funktioniert wie ein Immunsystem: fremde oder lineage-kopierte Signale werden nicht nur gewichtet, sondern müssen eine externe Challenge passieren. Falsifiziert, wenn es OOD-Routing nicht verbessert oder echte Signale systematisch blockiert.
- **Traveling Workspace:** Der funktionale Workspace ist kein Ort, sondern eine zeitlich wandernde Route über Receiver. Falsifiziert, wenn dieselbe feste Schicht/Komponente alle kausalen Läsions-/Rettungseffekte erklärt.
- **Shadow Workspace after Lesion:** Nach Läsion entsteht ein redundanter Ersatzpfad, der Broadcast-Metriken erhält, aber flexible Nutzung verliert. Falsifiziert durch exhaustive Co-Läsionen oder vollständige route-spezifische Rettung.
- **Causal-Cut Cytoplasm:** Es existiert kein universelles System-„Jetzt“; jede kognitive Entscheidung konsumiert einen zertifizierten lokalen Cut plus explizite unbekannte Frontiers. Falsifiziert, wenn dies mehr Action-Anomalien erzeugt als eine globale Barrier.
- **Boot-order Attractors:** Verschiedene valide Startreihenfolgen führen bei gleichem Endzustand zu unterschiedlichen stabilen Policies. Test: permutierte Boot-Orders mit identischen finalen Inputs; Hash-/Policy-Divergenz und reversible Reinitialisierung messen.

## Erhaltene Null- und Negativergebnisse

- Originales v0.2-Skript: `TypeError` vor Sweep; operativ nicht reproduzierbar ohne Shim.
- Blockkorrelierte Clock-Drift bis 20%: keine mutationsbedingte kategoriale Fehlentscheidung und keine falsche Promotion in dieser Konstruktion. Das ist kein Sicherheitsbeweis.
- Receiver-selektive Missingness: 6/960 Fehler, keine falsche Promotion; nominelles `n` blieb irreführend unverändert.
- Common-driver-Kontrollen: trotz Leakage-Schwere keine falschen Promotionen in diesem Sweep.
- Der post-hoc Tripwire `quality >= .9 && leakage <= .05` hatte 0 falsche Promotionen, ist aber nicht validiert und darf nicht als Regel promoted werden.
- Wasmtime-43/45-Roadmap oder stabile WASI-Spezifikation belegt keine produktionsreife konkrete p3-API.
- Runner-Labels sind Routingselektoren, keine Hardware-Attestation; lokaler Machine-ID-Fingerprint ist ebenfalls keine Hardware-Attestation.
- 200/200 Incremental-vs-Rebuild-Parität belegt Stichprobenkorrektheit, nicht günstige Hub-Skalierung.
- Atomare lokale Reservation beseitigt Check-then-act, aber nicht das externe Dual-Write-Fenster.

## Gezielt zurückgespielte Impulse

- **emergenz/unifieddb v0.3:** v0.2-Invalidation, 2.880-Läufe-Resultat, API-Bruch, Herkunft-vs-Qualität und Leakage-Tripwire; keine Wiederholung der 1.600 Seeds.
- **gwt/harness/frank:** Forked-future × Lesion/Rettung × truthful/shuffled/broken Reentry; Readout-Commit als gleichberechtigte Gegenhypothese.
- **claycode/harness:** realer FRANK-Frontend-Gap; generische ActiveAssembly-Realisierung; WIT/EffectWorld-Trennung; Runner-Labels nicht als Attestation zählen.
- **claygraph/hyperposition/unifieddb:** Dependency-Tricolor, Hub-Firebreak, Consistent-Cut und per-object CAS/Merkle-Read-Set statt globalem CAS.

## Frische externe Primärquellen

- WASI 0.3 Ratifikation, 11. Juni 2026: https://bytecodealliance.org/articles/WASI-0.3
- aktuelle Wasmtime-p3-Implementierungswarnung: https://docs.wasmtime.dev/api/wasmtime_wasi/p3/index.html
- Component Model Worlds/Components: https://component-model.bytecodealliance.org/design/worlds.html und https://component-model.bytecodealliance.org/design/components.html
- SLSA v1.2: https://slsa.dev/spec/v1.2/
- Hidden APIs, eingereicht 30. Juli 2026: https://arxiv.org/abs/2607.27617
- Readout-Ignition, v1 vom 4. August 2026: https://arxiv.org/html/2608.03263v1
- Verbalizable Global Workspace, 2026: https://transformer-circuits.pub/2026/workspace/index.html
- adversarialer GNWT/IIT-Test, Nature 2025: https://www.nature.com/articles/s41586-025-08888-1
- DBSP: https://www.vldb.org/pvldb/vol16/p1601-budiu.pdf

## Aktueller Gate-Stand

- `CLAYCODE_RELEASE_WORKSPACE.json`: WP01 `PASS`; WP02–WP14 `OPEN`; Applikationsabnahme `0/10`; Gate `NOT_PASS`.
- Manifest: formaler Pass `1`; `implementation_closure_ready_count = 11`; WP10 `NINE_OF_TEN_TARGET_RUNNER_READY`; WP13/WP14 blockiert.
- Offener Sprach-/Realisierungsgegenbeweis: vollständige H1-ActiveAssembly-Semantik in H2 noch nicht direkt ausgeführt.
- Zusätzlicher Frontend-Gegenbeweis: reale FRANK-Quelle gegen aktuelle BASE-Oberfläche; Ausführungsbestätigung offen.
- Keine P0/P1, aber keine Promotion: Andreas-Target-Receipts fehlen, Full-FRANK-Handoff unbewiesen, WP14-Audit nicht PASS.

## Autoritätsgrenze

Alle Hypothesen bleiben Kandidaten. Synthetische Softwaretests sind keine Live-FRANK-Validierung; funktionale GWT-Signaturen sind keine Bewusstseinsmessung; Modelloutput ist keine Ausführungsautorität. Es wurde kein Training ausgeführt und kein Gate promoviert.
