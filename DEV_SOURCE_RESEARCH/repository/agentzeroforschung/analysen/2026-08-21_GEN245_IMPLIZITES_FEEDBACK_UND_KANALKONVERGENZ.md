# Generation 245 — Implizites Korrekturfeedback und Feedback-Kanalkonvergenz

## BIND

- Forschungsrolle: `agentzeroforschung/OWNER_DIRECTIVE_2026-08-18.md`
- erster gebundener Research-Head dieser Auswertung: `2b7360bb2682131dfb0121c25c1c03e808033df0`
- Re-Entry-Head vor Persistierung: `66acef718d64062e362895d005997bc712424e4d`
- AgentZero-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Generation: `245`
- Exportzeit: `2026-08-21T14:07:17Z`
- Teststand: `1066 gruen / 1 rot`
- Andreas-Chat im gebundenen Export: `30` Zeilen
- Human-Feedback-Current-State am ersten gebundenen Head: `0` Zeilen

Diese Analyse ist reine Agent-Zero-Forschung. Sie mutiert weder Produktlogik noch Lernpolicy.

## 1. Nicht-duplizierter neuer Befund: negatives Nutzerfeedback existiert bereits im Dialogtext

Im vollstaendig exportierten Andreas-Chat steht eine klare Sequenz:

1. User Ordinal 21: `gib links immer klickbar aus`
2. Assistant Ordinal 22: behauptet, die Links seien jetzt klickbar, verwendet aber weiterhin Markdown-Linksyntax.
3. User Ordinal 23: `nein, links sind nicht klickbar`
4. Assistant Ordinal 24: erklaert, Markdown werde im Terminal klickbar gerendert und ordnet das Problem dem Client zu.

Damit existiert bereits vor dem neuen Daumen-Sensor ein natuerlichsprachiges, turngebundenes negatives Feedbacksignal.

Wichtig: `nein, links sind nicht klickbar` ist in diesem konkreten Kontext ein sehr starker Korrekturkandidat. Daraus folgt aber noch keine allgemeine Regel, dass jedes `nein`, jede Wiederholung oder jede Reformulierung negatives Feedback ist.

Status:

- konkretes textuelles Korrektursignal: `OBSERVED_AT_SNAPSHOT`
- allgemeine automatische Feedbackklassifikation aus Dialogtext: `NOT_VALIDATED`

## 2. Die Korrektur besitzt Retrieval-Lineage, aber keinen modernen Retrieval-Feedback-Credit

Der User-Turn Ordinal 23 hat:

- `turn_id = 37f41835-2b8a-4e64-9d3f-19d5972c7e1f`
- `causal_id = 5af6db4b-e401-418b-933f-3bdc9df07610`
- Generation `242`

Die zugehoerige Retrieval-Episode ist vorhanden:

- `retrieval_id = aa15b439-e975-42d8-a0ac-de3478513464`
- `status = PRESENT`
- `chars_selected = 59`
- genau eine `selected_memory_id`
- Modus `SHADOW`

Der aktuelle Export von `retrieval_feedback.jsonl` enthaelt dagegen nur die historischen Bootstrap-Signale `bootstrap:geholfen` / `bootstrap:daneben` aus deutlich aelteren Generationen. Fuer den Korrekturturn 37f41835... existiert dort kein moderner Feedbackreceipt.

Daraus folgt eng begrenzt:

`the correction is causally observable as a user turn, but it is not represented as retrieval_feedback in the exported retrieval-feedback channel`

Nicht daraus folgt:

- dass die Korrektur dem Modell unbekannt war;
- dass sie nicht im Full-Fidelity-Recent-Context vorhanden war;
- dass Retrieval an der fehlerhaften Linkdarstellung schuld war.

## 3. Spaeterer gleicher Aufgabentyp zeigt keine sichtbare Formatstrategie-Aenderung

In Generation 245 fragt der User erneut nach Produkten:

`finde Klobrillen beim Bauhaus`

Der spaetere Assistant-Turn verwendet wieder Markdown-Linksyntax. Die Retrieval-Episode dieses Gen245-Turns zeigt zugleich:

- `status = UNKNOWN`
- `chars_selected = 0`
- `entry_keys = []`
- `selected_memory_ids = []`
- `shadow_memory_ids = []`

Damit ist fuer den spaeteren Turn insbesondere keine retrieval-vermittelte Erinnerung an die fruehere Korrektur beobachtet.

Das ist noch kein Memory-Failure-Beweis, weil der aktuelle Full-Fidelity-Konversationskontext einen separaten Pfad bilden kann. Es ist aber ein sauberer negativer Befund fuer die engere Hypothese:

`a later same-domain response visibly adapted through retrieved durable memory`

Diese Hypothese wird am Gen245-Bauhaus-Turn **nicht gestuetzt**.

## 4. Kanal-Konvergenz: spaeterer expliziter Downvote trifft genau diesen Gen245-Bauhaus-Turn

Die unmittelbar parallel persistierte Gen245-Forschung hat zusaetzlich einen spaeteren, temporaer sichtbaren Daumen-runter gebunden:

- bewerteter Assistant-Turn: `8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`
- Frage-Turn: `e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- derselbe Bauhaus-Produktsuchturn wie oben
- `wert = -1`
- spaeter wieder entfernt
- Retrieval dieses Turns war nachweislich `UNKNOWN` mit 0 Memory-Treffern

Damit liegen zwei unterschiedliche negative Feedbackkanaele in derselben groben Aufgabenfamilie vor:

A. frueher expliziter Dialogtext: `nein, links sind nicht klickbar`

B. spaeter expliziter UI-Downvote auf eine weitere Produktantwort, die erneut Markdown-Links enthaelt.

### Harte Grenze

Es ist **nicht bekannt**, warum der spaetere Downvote vergeben wurde. Er darf nicht nachtraeglich als Beweis fuer das Linkproblem etikettiert werden.

Die interessante Forschungsfrage ist daher nicht `beide bedeuten dasselbe`, sondern:

`koennen unabhaengige Feedbackkanaele auf dieselbe Fehlerklasse konvergieren, und wie misst man diese Konvergenz ohne semantische Ursache zu erfinden?`

Status:

- zwei negative Feedbacksignale in verwandten Produktsuchinteraktionen: `OBSERVED`
- gleiche zugrunde liegende Ursache: `UNRESOLVED`
- Link-Rendering als Ursache des Downvotes: `UNRESOLVED`

## 5. Haupt-Hypothese H-IF1 — explizite Ratings unterdecken natuerliche Korrekturen

### Hypothese

Menschen liefern fuer AgentZero relevante Outcome-/Friction-Signale haeufig direkt im Dialogtext, ohne den separaten Daumenkanal zu benutzen. Ein reines Rating-Ledger hat deshalb systematisch geringere Verhaltens-Coverage als ein zweikanaliges Messmodell.

### Aktueller Anker

Zum gebundenen Gen245-Current-State standen 0 Ratingzeilen einem bereits sichtbaren natuerlichsprachigen Korrekturereignis gegenueber.

### Gegenhypothese GH-IF1

Die meisten Dialogreformulierungen und Negationen sind keine zuverlaessigen Qualitaetssignale; ein automatischer impliziter Feedbackkanal wuerde mehr Labelrauschen als Informationsgewinn erzeugen.

### Billigster Diskriminator

Read-only ueber bestehende Turnfolgen Kandidaten markieren, noch ohne Lernwirkung:

- direktes `nein` / `falsch` / `funktioniert nicht` nach Assistant-Turn;
- fast identische Wiederholung einer Anfrage nach Assistant-Antwort;
- explizite Formatkorrektur (`gib ...`, `nicht ...`, `nochmal ...`);
- anschliessende menschliche Stichprobenklassifikation.

Dann messen:

- Precision der Kandidaten;
- Kandidaten je 100 Assistant-Turns;
- Anteil mit spaeterem explizitem Rating;
- Anteil mit sofortiger sichtbarer Strategieaenderung;
- Anteil mit spaeterer Wiederholung desselben Problems.

H-IF1 bleibt `RETAINED_HYPOTHESIS`; ein einzelner klarer Fall reicht nicht fuer eine populationsweite Aussage.

## 6. Gegenhypothese H-IF2 — Client-Affordance statt Agent-Lernen

Die Linksequenz kann auch ein Interfaceproblem sein:

- Zero sendet syntaktisch gueltiges Markdown;
- der konkrete Client macht daraus keine klickbare UI;
- die Textantwort allein besitzt moeglicherweise keine alternative Darstellungsstrategie, die das Clientproblem behebt.

Dann waere die wiederholte Markdown-Ausgabe kein Memoryversagen, sondern eine fehlende End-to-End-Affordance zwischen Antwortformat und Clientrenderer.

Billigster Diskriminator:

`OUTPUT_AFFORDANCE_RECEIPT/v1`

pro Client/Session:

- output_format_sent
- renderer_capabilities_observed
- hyperlink_activation_supported = YES | NO | UNKNOWN
- alternate_plain_url_supported
- user_reported_failure bound to assistant turn

Ohne solche Clientdaten bleibt `memory failure` fuer diesen Fall zu stark.

## 7. Forschungsinstrument-Kandidat: IMPLICIT_FEEDBACK_CANDIDATE/v1

Das Instrument darf **kein automatischer Rewardkanal** sein.

Minimalfelder:

- `candidate_id`
- `user_turn_id`
- `preceding_assistant_turn_id`
- `session_id`
- `causal_id`
- `candidate_class = CORRECTION | REPEAT_AFTER_FAILURE | FORMAT_REJECT | CLARIFICATION | UNKNOWN`
- `evidence_hash`
- `detector_version`
- `detector_basis`
- `review_status = UNREVIEWED | CONFIRMED | REJECTED | AMBIGUOUS`
- `linked_rating_event_id` falls vorhanden
- `component_activity_mask` falls kausal bindbar

Harte Invariante:

`implicit feedback candidate != reward != truth`

Ein Kandidat darf zunaechst nur Forschung, Routing und spaetere manuelle/kausale Klassifikation speisen.

## 8. Zweites Instrument: FEEDBACK_CHANNEL_CONVERGENCE/v1

Ziel: explizite UI-Ratings und natuerlichsprachige Korrekturen gemeinsam beobachten, ohne Ursachen zu erfinden.

Kennzahlen:

- `rating_coverage`
- `implicit_candidate_coverage`
- `channel_overlap`
- `channel_disagreement`
- `feedback_latency`
- `post_feedback_behavior_delta`
- `same_task_recurrence`
- `causal_join_completeness`

Nur wenn zwei Kanaele auf denselben Assistant-Turn oder eine sauber definierte Fehlerklasse gebunden werden koennen, darf von `CONVERGENCE` gesprochen werden.

## 9. Cross-domain-Fusion

Wang et al., EMNLP 2021, `Contextual Rephrase Detection for Reducing Friction in Dialogue Systems`, DOI `10.18653/v1/2021.emnlp-main.143`, behandeln Nutzerreformulierungen und Interaktionskontext explizit als implizites Feedbacksignal fuer Dialogue Friction.

Transfer auf AgentZero:

- Reformulierung/Korrektur ist ein sinnvoller **Messkandidat**;
- Kontext und zeitliche Naehe sind wichtig;
- das Paper legitimiert nicht, jeden Repeat als Fehler oder Reward zu etikettieren;
- Zero braucht deshalb erst Kandidatenerkennung + kausale Bindung + Validierung, nicht unmittelbares Online-Lernen.

## 10. Persistenter roter Adaptertest — Nebenbefund

Gen245 steht weiterhin bei `1066 gruen / 1 rot` mit

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`.

Aktueller Source des Tests und des `ClaudeCodeInference`-Adapters sind auf der sichtbaren Ebene semantisch konsistent: Tooldisablement, `plan`, `--no-session-persistence`, striktes MCP und Environment-Allowlist sind im Source vorhanden. Der Export enthaelt aber keinen exakten Assertion-/Trace-Receipt des roten Laufs.

Daher bleibt die Fehlerursache `UNKNOWN`; aus dem roten Summary allein darf weder CLI-Drift noch ein echter Secret-Leak behauptet werden.

Naechster Messbedarf bleibt ein atomarer Red-Test-Detailreceipt mit Source-/Environment-Bindung und typisiertem Assertion-/Exception-Ergebnis.

## 11. Promotionsstatus

- natuerlichsprachige Link-Korrektur als konkreter negativer Feedbackfall: `OBSERVED_AT_SNAPSHOT`
- Korrekturturn besitzt Retrieval-Episode: `VERIFIED_AT_SCOPE`
- moderner Retrieval-Feedbackreceipt fuer diesen Korrekturturn im Export: `ABSENT`
- spaeterer Gen245-Bauhaus-Retrievaltreffer: `NONE / UNKNOWN`
- sichtbare Formatstrategie-Aenderung im spaeteren Bauhaus-Output: `NOT_OBSERVED`
- spaeterer expliziter Downvote auf Bauhaus-Turn: `VERIFIED_AT_SCOPE` durch Parallelforschung
- gemeinsame Ursache von Textkorrektur und Downvote: `UNRESOLVED`
- H-IF1 Rating-Unterdeckung natuerlicher Korrekturen: `RETAINED_HYPOTHESIS`
- H-IF2 Client-Affordance als alternative Ursache: `RETAINED_HYPOTHESIS`
- automatisches Lernen aus implizitem Feedback: `NOT_ADMITTED`

## 12. Wichtigstes neues Ergebnis

Der neue Daumenkanal ist nicht die einzige reale Feedbackquelle von AgentZero. Im bereits exportierten Dialog existiert ein klar turngebundener negativer Korrekturfall, fuer den keine moderne Retrieval-Feedbackspur sichtbar ist. Spaeter antwortet Zero in derselben groben Produktsuchfamilie erneut mit derselben Linksyntax; genau dieser spaetere Turn erhielt danach temporaer einen echten Downvote, dessen Ursache aber unbekannt bleibt.

Damit entsteht eine neue Forschungsfront:

`explizites Rating + natuerliche Korrektur + Komponenten-Lineage + Client-Affordance`

muessen als getrennte, spaeter fusionierbare Sensoren behandelt werden.

Der billigste naechste Informationsgewinn ist **nicht**, implizite Korrekturen sofort als Reward zu verwenden, sondern sie append-only als Kandidaten zu erfassen und gegen echte Ratings, Wiederholungen, Komponentenaktivitaet und nachfolgende Verhaltensdeltas zu validieren.