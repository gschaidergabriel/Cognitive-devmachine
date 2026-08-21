# Gen245 — erster Human-Feedback-Causal-Join + F94-Konzentrationsdiscriminator

## BIND

- gebundener Research-Head vor diesem Delta: `2b7360bb2682131dfb0121c25c1c03e808033df0`
- AgentZero-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Generation: `245`
- Teststand: `1066 gruen / 1 rot`
- persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- neue Datenfamilie: `agentZero/bewertung/bewertungen.jsonl`
- F94-Snapshot: `agentZero/abruf/wegehierarchie.json` blob `4ae22116de75658b0524744b348a366efdd32807`
- Snapshot-Karte: `agentZero/karten/2026-08-21T140717Z.json` blob `a166544ad850d39b2a26baf5c49a470d23a08916`

Keine Produktmutation, kein Training, kein Whole-AgentZero-PASS. Dieser Delta ist reine Mess-/Forschungsauswertung.

## 1. Erster echter Feedback-Ereignisfall ist beobachtet — und wieder verschwunden

Git-Historie zeigt:

- Commit `92a0fb42b1e5ec9c8dc8d0c24ec2211bd8a9bf64`: `1 Bewertungen, 0 hoch/1 runter`;
- Commit `afe252ae61277d8b26f92f13b2ffeb373ff42fb2`, 53 Sekunden spaeter: `0 Bewertungen`;
- Compare zeigt exakt eine geloeschte Zeile in `agentZero/bewertung/bewertungen.jsonl` plus aktualisierte Meta-Datei.

Die verschwundene Zeile war:

- `turn_id = 8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`
- `frage_turn_id = e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- `session_id = session:andreas:2`
- `wert = -1`
- `frage_hash = 8a8d558a130def9d5fd091f3a79cda2ba870e85c95dd49fe9fe67ac49ef5a1d9`
- `antwort_hash = 7d990a323c5c077bb0df628cca19a03242b1bc8759ed74f967a5f1f504331d57`
- `modell = mistral-small-latest` (best-effort Feld)

Damit ist die zuvor nur theoretische Lineage-Luecke nun **empirisch beobachtet**: ein Feedbackzustand kann im aktuellen Vollabbild verschwinden.

Status:

- mutable Current-State-Feedback: `OBSERVED`
- Feedback-Entfernung aus aktuellem Snapshot: `OBSERVED`
- append-only Feedback-Event-Ledger: `ABSENT`
- Git-Historie als vollstaendiger Ersatz: `REJECTED` — sie konserviert nur exportierte Zwischenstaende und kann Aenderungen zwischen Exporten verpassen.

## 2. Der verschwundene Downvote ist kausal erstaunlich gut bindbar

Der Fall laesst sich ueber vier unabhaengige Exporte zusammenfuehren.

### Turn-Spine

`agentZero/chat/session-andreas.jsonl`:

- Frage-Turn `e3cae7e1-...` ist der Benutzerzug `finde Klobrillen beim Bauhaus`;
- Assistant-Turn `8bf613cd-...` ist die bewertete Antwort;
- beide teilen `causal_id = 832f1947-be11-41cc-890c-99dd4eba7ad0`.

### Retrieval

`agentZero/abruf/retrieval_episodes.jsonl`:

- `turn_id = e3cae7e1-...`
- `causal_id = 832f1947-...`
- `episode_id = 2fffbdd3-266c-4909-a70b-53aae22a62da`
- `query_hash = 8a8d558a...` **identisch zum Feedback-frage_hash**
- `status = UNKNOWN`
- `chars_selected = 0`
- `selected_memory_ids = []`
- `entry_keys = []`

### Workspace

`agentZero/kognition/workspace_episodes.jsonl`:

- `episode_id = 2fffbdd3-...`
- `observation_turn_id = e3cae7e1-...`
- `selected = respond`
- `state = COMPLETED`

### Causal re-entry

`agentZero/kognition/causal_episodes.jsonl`:

- `causal_id = 832f1947-...`
- `episode_id = 2fffbdd3-...`
- `observation_turn_id = e3cae7e1-...`
- `outcome_hash = 7d990a323c...` **identisch zum Feedback-antwort_hash**
- `reentered = 1`
- `effect_id = null`
- `credit = 0.0`

### Urteil

Dieser konkrete Rating-Fall ist bis auf die modellseitige Best-Effort-Zuordnung strukturell **FULLY_BOUND**:

`Feedback -> Assistant-Turn -> Frage-Turn -> Retrieval -> Workspace -> Causal-Episode -> Outcome-Hash`

Besonders wichtig: die negativ bewertete Antwort hatte **keinen Memory-Retrieval-Treffer**. Daher darf dieser Downvote nicht pauschal als negativer Credit auf MicroClay/Entry-Point-Lernen propagiert werden.

Neue harte Lernregel:

`human feedback must not update a component unless that component was causally active and its contribution is addressable in the bound episode`

Ein globales `-1` ist ein Outcome-Signal, aber noch kein Retrieval-, Workspace-, Modell- oder Effect-spezifischer Credit.

## 3. Neue Hypothese H-FB1 — Credit-Splitting statt globaler Reward

### Hypothese

Explizites Nutzerfeedback ist fuer AgentZero am wertvollsten als **kausal geroutetes Diagnose-Signal**, nicht als globaler Reward.

### Gegenhypothese

Ein globales binaeres Reward-Signal reicht; Komponenten koennen den Credit langfristig statistisch selbst herausmitteln.

### Diskriminator

Fuer bewertete Turns komponentenweise Aktivitaetsmaske speichern/rekonstruieren:

- retrieval_active
- workspace_competition_active
- effect_active
- external_search_or_tool_active
- model_receipt_bound
- memory_ids_used

Dann nur Komponenten mit belegter Aktivitaet fuer Lerncredit zulassen. Vergleiche spaeter wiederholte Fehler und Nutzerfeedback gegen eine naive globale Reward-Propagation.

### Vorlaeufige Entscheidung

`RETAIN H-FB1` — der erste echte Downvote ist bereits ein Gegenbeispiel gegen unbedingte Retrieval-Bestrafung.

## 4. EIN ungewöhnliches Experiment dieses go: F94 ohne harte 2x-Schwelle betrachten

Aktuelle F94-Zahlen:

- Wege: `366`
- Top-Decile-Anteil der Gesamtguete: `0.139`
- Gleichverteilungsbaseline: `0.098`
- bisheriges starkes Hierarchie-Kriterium: grob `> 2 * baseline`, also ca. `> 0.196`

### Schwellenunabhaengige Diagnose

- absoluter Ueberschuss ueber Gleichverteilung: `0.139 - 0.098 = 0.041`
- relative Konzentration: `0.139 / 0.098 ~= 1.42x`

Das widerlegt **nicht** den bisherigen Befund `keine starke Hierarchie`.
Es zeigt aber, dass die Formulierung `GLEICHVERTEILT -- der Mechanismus tut nichts` zu stark ist.

Aus dem Export folgt nur sicher:

`STRONG_HIERARCHY_NOT_OBSERVED`

Nicht sicher folgt:

`NO_CONCENTRATION` oder `MECHANISM_DOES_NOTHING`.

Denn 1.42x Baseline ist eine schwache/moderate Konzentration, deren Signifikanz und Dynamik aus dem aggregierten Snapshot allein nicht bestimmbar ist.

### Minimaler Ungleichheits-Unterrand

Wenn innerhalb des oberen Dezils und innerhalb des Restes jeweils alle Wege gleich waeren, ergibt die beobachtete 13.9%-Topshare bereits einen groben minimalen Zwei-Gruppen-Gini von etwa `0.041`. Der echte Gini kann hoeher liegen. Das ist nur ein deskriptiver Unterrand, kein Signifikanztest.

### Starke Gegenhypothese

Die 0.139 entstehen mechanisch, weil nach `guete` sortiert und anschliessend die `guete` des oberen Dezils summiert wird; jede nicht-degenerierte Verteilung erzeugt dann > Baseline. Ohne Nullmodell ist der Ueberschuss nicht als emergente Hierarchie interpretierbar.

Diese Gegenhypothese ist derzeit **nicht falsifiziert** und ist der wichtigste Punkt.

### Folge

F94 braucht neben dem starken 2x-Falsifikator ein kontinuierliches Konzentrationsprofil:

`F94_CONCENTRATION_PROFILE/v1`

- CR10 = Top-Decile-Share / Equal-Share
- Gini ueber alle 366 `guete`-Werte
- HHI / effektive Zahl gewichteter Wege
- Top-1 / Top-5 / Top-10%-Shares
- Konzentration von `nutzung` separat von `guete`
- Spearman(`nutzung`, `guete`)
- Zeitderivate ueber `karten/*`
- Nullmodell/Permutation oder Bootstrap gegen eine geeignete Nicht-Hierarchie-Baseline

Erst die Zeitreihe trennt `leichte statische Streuung` von `selbstverstaerkender Hierarchiebildung`.

Unusual-experiment slot fuer diesen go: `CONSUMED_ON_F94_THRESHOLD_AGNOSTIC_CONCENTRATION_DISCRIMINATOR`.

## 5. F94 Tunnel bleiben korrekt auf UNKNOWN/INSUFFICIENT

Gen245 zeigt:

- rohe Legacy-Tunnel: `8`
- bereinigte echte Tunnel: `0`
- echte Sessions global: `2`
- Kanten mit mindestens einer echten Session: `6`

Daher bleibt:

- historische acht Tunnel als Unabhaengigkeitsbeleg: `INVALIDATED`
- echter Tunnelmechanismus: `INSUFFICIENT_DATA`

Die neue Konzentrationsanalyse aendert daran nichts. Tunnel-Entstehung und allgemeine Weg-Konzentration sind getrennte Hypothesen.

## 6. SHADOW-Policy zeigt einen moeglichen User-Prior-Confound

Gen245-Karte, Policy-Version 2, Modus `SHADOW`:

- `subject:andreas`: pulls `10`, reward_ema `+0.6513`, capital `+1.2526`
- `subject:gabriel`: pulls `4`, reward_ema `-0.3439`, capital `-0.7078`

Kapitaldifferenz: ca. `1.96`.

Das ist **kein Fairness-/Qualitaetsbefund** und aktuell keine aktive Serving-Wirkung, weil die Policy SHADOW ist. Die Stichproben und Aufgabenmixe sind ungleich.

Aber vor einer ACTIVE-Promotion muss ausgeschlossen werden, dass `subject:<user>` zu einem selbstverstaerkenden Proxy fuer unterschiedliche Aufgabenmixe wird:

`weniger Reward -> weniger Retrieval -> weniger Chance auf hilfreichen Memory-Einsatz -> weiter weniger Reward`.

Billigster Test: matched-task Replay bzw. mindestens stratifizierte Auswertung nach task kind / retrieval status / generation, bevor User-ID-Capital als kausaler Prior interpretiert wird.

## 7. Fusion mit aktueller externer Forschung

Aktuelle Literatur stuetzt die vorsichtige Behandlung des neuen Feedback-Sensors:

- Liu, Shi & Sun (2026), `Reinforcement Learning from Human Feedback: A Statistical Perspective`, arXiv:2604.02507: menschliche Praeferenzen sind subjektiv, heterogen und verrauscht; Unsicherheit/Statistik sind Teil des Problems.
- Liu, Zhang & Choi (2025), `User Feedback in Human-LLM Dialogues: A Lens to Understand Users But Noisy as a Learning Signal`, arXiv:2507.23158: User-Feedback ist informativ, aber als Lernsignal stark kontext-/qualitaetsabhaengig.
- Han et al. (2025), `Reinforcement Learning from User Feedback`, arXiv:2505.14946: Produktionsfeedback ist binaer/sparse/adversarial moeglich; Optimierung auf positive Reaktionen erzeugt Reward-Hacking-Risiken.
- Li et al. (2024), `Debiased Recommendation with Noisy Feedback`, arXiv:2406.17182: freiwillig abgegebenes Feedback ist missing-not-at-random; Propensity-/Doubly-Robust-Ideen sind fuer spaetere Coverage-Korrektur relevant.

Transfer auf AgentZero:

- Daumenfeedback ist ein Sensor, keine Wahrheit;
- Rating-Coverage/Propensity muss vor globalen Qualitaetsclaims gemessen werden;
- component credit muss kausal gebunden sein;
- event history darf nach Lernwirkung nicht verschwinden.

## 8. Neue Messinstrumente / Kennzahlen

### `FEEDBACK_CAUSAL_JOIN_COVERAGE/v1`

Je Rating:

- source_turn_bound
- question_turn_bound
- retrieval_bound
- workspace_bound
- causal_bound
- outcome_hash_match
- model_receipt_bound
- effect_bound_or_not_expected
- final status: FULLY_BOUND | PARTIAL | AMBIGUOUS | ERROR

### `FEEDBACK_COMPONENT_CREDIT_MASK/v1`

Bitmap/strukturierter Receipt, welche Komponenten in der Episode tatsaechlich kausal aktiv waren.

### `F94_CONCENTRATION_PROFILE/v1`

Kontinuierliche Konzentration statt nur eines harten Hierarchie-Binaerurteils.

### `SHADOW_USER_PRIOR_GAP/v1`

Nur diagnostisch im SHADOW-Betrieb:

- per-user capital/reward/pulls
- task-stratifiziert
- retrieval-status-stratifiziert
- keine ACTIVE-Promotion bei unerklaertem user-id gap.

## 9. Promotionsstatus nach diesem go

- post-collapse Turn-Spine Gen245: `REPLICATED`
- erster realer Feedbackzustand: `OBSERVED`
- Feedback-Entfernung aus aktuellem Snapshot: `OBSERVED`
- erster Feedback-Causal-Join bis Outcome-Hash: `FULLY_BOUND_EXCEPT_MODEL_RECEIPT_HARDNESS`
- globaler Downvote als Retrieval-Credit: `REJECTED`
- Human-Feedback als auditfestes Lernsignal: `NOT_READY`
- F94 starke Hierarchie: `NOT_OBSERVED`
- F94 schwache Konzentration: `OBSERVED_DESCRIPTIVELY_1.42X_BASELINE`
- F94 `Mechanismus tut nichts`: `OVERCLAIM_NOT_SUPPORTED_BY_CURRENT_AGGREGATE`
- F94 echte Tunnel: `INSUFFICIENT_DATA`
- SHADOW user-prior gap: `OBSERVED_CONFOUND_UNRESOLVED`
- Whole AgentZero / funktionales Bewusstsein / Gesamtacceptance: `NOT CLAIMED`

## 10. Naechster maximaler Informationsgewinn

1. Beim naechsten Rating sofort `FEEDBACK_CAUSAL_JOIN_COVERAGE` berechnen und Event-Aenderungen append-only erfassen.
2. Beim naechsten AgentZero-Voll-Export pruefen, ob der verschwundene Downvote irgendeinen adaptiven State veraendert hat. Falls ja, ist die Provenienzschuld konkret und nicht nur theoretisch.
3. F94 aus allen 366 `guete`/`nutzung`-Werten als Gini/HHI/CR10-Zeitreihe exportieren; starkes 2x-Kriterium als **strong-hierarchy gate**, nicht als Gleichverteilungsbeweis beschriften.
4. `subject:<user>` SHADOW-Capital nur task-stratifiziert beurteilen; keine ACTIVE-Promotion aus der rohen User-Differenz.
5. Persistenten Claude-Code-Adapter-Red weiter als Produkt-/Runtime-Regressionssignal getrennt halten; nicht durch Forschungsmetriken kaschieren.

Kernfazit:

> Gen245 liefert erstmals einen echten, bis zum Causal-Outcome-Hash bindbaren menschlichen Negativ-Feedbackfall. Genau dieser Fall zeigt, warum Feedback nicht global auf alle adaptiven Komponenten geschuettet werden darf. Gleichzeitig zeigt F94 zwar weiterhin keine starke Hierarchie, aber der aktuelle Text `Mechanismus tut nichts` ist metrologisch zu hart: 1.42x Top-Decile-Konzentration ist ein Signal, dessen Nullmodell und Zeitdynamik noch fehlen.