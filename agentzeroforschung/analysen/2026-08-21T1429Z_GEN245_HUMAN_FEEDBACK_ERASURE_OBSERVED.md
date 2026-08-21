# Generation 245 — Human-Feedback-Erasure erstmals live beobachtet

## BIND

- gebundener Repo-Head vor Persistierung: `2b7360bb2682131dfb0121c25c1c03e808033df0`
- letzter AgentZero-Voll-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- AgentZero-Generation: `245`
- Exportzeit: `2026-08-21T14:07:17Z`
- vorausgehende Forschungsanalyse: `agentzeroforschung/analysen/2026-08-21T1422Z_GEN245_TUNNEL_PROVENIENZ_UND_HUMAN_FEEDBACK.md`
- neue Evidenzfamilie: zwei unmittelbar aufeinanderfolgende `eos-bewertung-export`-Commits nach Abschluss des Gen245-Voll-Exports

Diese Analyse ist ein enger Nachtrag zur Gen245-Human-Feedback-Metrologie. Sie bewertet nicht die inhaltliche Qualität einer Agent-Zero-Antwort, sondern die historische/auditierbare Semantik des neuen Feedback-Sensors.

## 1. Beobachtung: ein reales negatives Feedbackereignis erschien und verschwand wieder

Commit `92a0fb42b1e5ec9c8dc8d0c24ec2211bd8a9bf64` um `2026-08-21T14:24:02Z` exportierte:

- `1` Bewertung;
- `0` hoch;
- `1` runter.

Die exportierte Zeile war eindeutig gebunden an:

- Assistant-Turn `8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`;
- Frage-Turn `e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`;
- Session `session:andreas:2`;
- User `andreas`;
- `wert=-1`;
- best-effort Modellzuordnung `mistral-small-latest`;
- stabile Frage-/Antwort-Hashes.

Der direkt folgende Export-Commit `afe252ae61277d8b26f92f13b2ffeb373ff42fb2` um `2026-08-21T14:24:55Z` exportierte:

- `0` Bewertungen;
- `0` hoch;
- `0` runter.

Dabei wurde exakt die vorher vorhandene JSONL-Zeile wieder entfernt.

Zeit zwischen den beiden Exportzuständen: **53 Sekunden**.

Status: `OBSERVED_AT_SNAPSHOT`.

## 2. Was damit jetzt empirisch gezeigt ist

Die Gen245-Analyse hatte aus dem Source-Verhalten bereits vorhergesagt, dass `eos_bewertungen` ein materialisierter Current-State und kein Event-Ledger ist. Die neue Sequenz zeigt diesen Informationsverlust nun real im Export:

`0 Bewertungen -> 1 negative Bewertung -> 0 Bewertungen`

Ein einzelner aktueller Snapshot nach `14:24:55Z` ist semantisch mit mindestens zwei verschiedenen Geschichten kompatibel:

1. es wurde nie bewertet;
2. es wurde bewertet und die Bewertung danach entfernt.

Die beiden Geschichten sind im aktuellen `bewertungen.jsonl` nicht unterscheidbar.

Damit ist die vorherige Audit-Risiko-Hypothese nicht mehr nur Source-Inferenz. Die Kombination aus dokumentiertem Current-State-Mechanismus und beobachteter Zustandsfolge stuft den Befund hoch zu:

- Current-State-Erasure im Export: `MECHANISM_SUPPORTED`;
- historisch vollständige Feedback-Provenienz im Sensor: `FALSIFIED_AT_SCOPE`;
- UI-Materialized-State-Funktion: nicht falsifiziert und weiterhin kompatibel mit dem beobachteten Verhalten.

## 3. Wichtige Abgrenzung: dies ist KEIN Qualitätsurteil über Agent Zero oder Mistral

Die eine negative Bewertung darf nicht als belastbare Schätzung von Antwortqualität interpretiert werden.

Gruende:

- Stichprobe `n=1`;
- Rating wurde anschliessend entfernt;
- Bewertungspropensität unbekannt;
- keine Coverage-Baseline;
- Modellzuordnung ist laut Gen245-Analyse best-effort content-basiert;
- keine kontrollierte Vergleichsgruppe;
- die Motivation der Entfernung ist unbekannt.

Daher:

- `AgentZero quality decreased`: `NOT_SUPPORTED`;
- `mistral-small-latest caused dissatisfaction`: `NOT_SUPPORTED`;
- `a negative human feedback event occurred`: `OBSERVED_AT_SNAPSHOT`;
- `that event later disappeared from the current-state export`: `OBSERVED_AT_SNAPSHOT`.

## 4. Haupt-Hypothese und Gegenhypothesen

### H1 — Current-State-Sensor verliert Ereignisgeschichte

Der Sensor implementiert absichtlich den aktuellen Bewertungszustand. Eine Entfernung loescht die Zeile; deshalb kann eine spaetere Forschungsauswertung die Ereignisgeschichte aus dem aktuellen Sensor allein nicht rekonstruieren.

**Vorhersage:** SET/CHANGE/REMOVE koennen im Materialized State historische Zwischenzustaende verschwinden lassen.

### H2 — Git-Export-Historie ist bereits ein ausreichendes Event-Ledger

Gegenhypothese: Da jeder Export committed wird, koennte Git die verlorene Historie faktisch konservieren.

**Starker Falsifikator:** Eine Bewertung setzen und wieder entfernen, bevor der naechste Exporttimer laeuft. Wenn beide Operationen zwischen zwei Exporten stattfinden, bleibt in Git kein Bewertungsereignis erhalten.

Da Export und Bewertungsoperation nicht dieselbe atomare Ereignisquelle sind, ist H2 bereits strukturell schwach. Die aktuelle 53-Sekunden-Sequenz wurde nur deshalb sichtbar, weil ein Export zufaellig zwischen SET und REMOVE lag.

### H3 — Entfernung ist nur normales UI-Verhalten, daher kein Messfehler

Fuer die UI ist diese Gegenhypothese korrekt: ein Nutzer darf seine Bewertung entfernen und der aktuelle Zustand soll danach `0` sein.

Sie widerlegt aber den Forschungsbefund nicht. Der Fehler liegt nicht in der UI-Semantik, sondern darin, denselben verlustbehafteten Current-State spaeter als historische Reward-/Audit-Evidenz zu verwenden.

Daher muessen zwei Semantiken getrennt bleiben:

- `CURRENT_RATING_STATE`: materialisiert, aenderbar, UI-geeignet;
- `RATING_EVENT_HISTORY`: append-only, auditierbar, Forschungs-/Lernquelle.

## 5. Causality / Learning-Risiko

Die kritische Gegenrealitaet lautet:

1. Feedback `-1` wird gesetzt;
2. ein adaptiver Mechanismus veraendert Retrieval-/Routing-/Modellpolicy;
3. Nutzer entfernt das Feedback;
4. `eos_bewertungen` zeigt wieder keinen Eintrag;
5. die adaptive Zustandsaenderung bleibt bestehen;
6. spaetere Auditoren finden keine Quelle fuer diesen Credit/Debit.

Das waere dieselbe strukturelle Provenienzschuld wie bei der Gen241/244 Evidence-Spine-Luecke: abgeleiteter Zustand kann fortbestehen, waehrend die urspruengliche Evidenzlinie unsichtbar wird.

Harte Invariante bleibt deshalb:

`adaptive state change from human feedback => immutable source event or explicit reversible provenance mapping`

Bis diese Invariante instrumentell erfuellt ist, darf Current-State-Feedback kein auditpflichtiger automatischer Reward werden.

## 6. Billigste diskriminierende Messungen

### D1 — Append-only Event-Ledger

Instrumentiere `HUMAN_FEEDBACK_EVENT_LEDGER/v1` direkt am Schreibpfad mit:

- `event_id`;
- `turn_id`;
- `session_id`;
- `user_id`;
- `event_type = SET | CHANGE | REMOVE`;
- `old_value`;
- `new_value`;
- `ts`;
- Frage-/Antwort-Hash;
- direkte Output-/Model-Receipt-ID, falls vorhanden;
- Schema-/Source-Version.

Danach pruefen, ob die beobachtete `-1 -> REMOVE`-Sequenz als zwei unveraenderliche Events sichtbar bleibt, waehrend `eos_bewertungen` weiterhin korrekt `0` aktuellen Zustand zeigt.

### D2 — Between-export lesion

Gezielter Messfalsifikator fuer die Gegenhypothese, Git sei als Ledger ausreichend:

- SET einer Testbewertung;
- REMOVE vor dem naechsten Export;
- danach pruefen, ob irgendein Export-/Git-Artefakt das Zwischenereignis enthaelt.

Erwartung unter H1: keine Spur im Current-State-Export/Git-Exportpfad.

### D3 — Causal Join Completeness

Fuer jedes kuenftige Feedbackereignis messen:

- Assistant-Turn vorhanden/eindeutig;
- Frage-Turn vorhanden/eindeutig;
- passende Causal-/Workspace-/Retrieval-Episode;
- eindeutiger Output-/Model-Receipt;
- Ergebnis `FULLY_BOUND | NO_RETRIEVAL_EXPECTED | AMBIGUOUS_MODEL | MISSING_CAUSAL | MISSING_SOURCE_TURN | ERROR`.

Kein adaptives Lernen aus Feedback bei nicht ausreichend gebundener Provenienz.

## 7. Neue Forschungsmetrik

Sobald genug Ereignisse existieren, nicht nur `hoch/runter` berichten, sondern getrennt:

- `rating_event_count`;
- `current_rated_turn_count`;
- `set_count`;
- `change_count`;
- `remove_count`;
- `rating_coverage`;
- `median_feedback_latency`;
- `causal_join_complete_rate`;
- `model_binding_exact_rate`;
- `feedback_events_missing_from_materialized_state`.

Der aktuelle Snapshot liefert erstmals einen konkreten Beleg fuer die letzte Kategorie: mindestens ein Ratingereignis war in einem Export sichtbar und ist im spaeteren Current-State nicht mehr enthalten.

## 8. Promotionsstatus

- Human-Feedback-Sensor vorhanden: `SOURCE_CONFIRMED_INSTRUMENT`
- erstes reales negatives Feedbackereignis: `OBSERVED_AT_SNAPSHOT`
- anschliessende Entfernung desselben Current-State-Eintrags: `OBSERVED_AT_SNAPSHOT`
- Current-State-Erasure als Mechanismus: `MECHANISM_SUPPORTED`
- Current-State-Export als vollstaendige Ereignishistorie: `FALSIFIED_AT_SCOPE`
- Git-Exportfolge als gelegentliche Hilfsevidenz: `OBSERVED`, aber `NOT_A_CAUSAL_LEDGER`
- Human-Feedback als auditfestes automatisches Lernsignal: `NOT_READY`
- AgentZero-/Modellqualitaetsclaim aus diesem einen Rating: `NOT_SUPPORTED`

## 9. Naechster maximaler Informationsgewinn

Der wichtigste naechste Schritt ist **nicht** eine Positivquote und auch nicht ein weiteres Modellranking. Es ist die Trennung von Materialized State und Ereignisprovenienz.

Sobald das Event-Ledger existiert, kann die Forschung erstmals sauber messen:

`Feedbackereignis -> Turn -> Retrieval/Workspace/Causal-Spine -> Modell/Output -> spaetere Nutzerreaktion -> eventuelle adaptive Aenderung`

Erst diese Kette macht Human-Feedback fuer AgentZero wissenschaftlich und spaeter lerntechnisch belastbar.
