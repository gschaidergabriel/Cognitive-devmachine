# Generation 245 — Erstes reales Human-Feedback: Withdrawal, Audit-Luecke und Credit-Grenze

## BIND

- Forschungsrolle: `agentzeroforschung/OWNER_DIRECTIVE_2026-08-18.md`
- gebundener AgentZero-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Generation: `245`
- Manifestzeit: `2026-08-21T14:07:17Z`
- Repo-Head vor dieser Auswertung: `2b7360bb2682131dfb0121c25c1c03e808033df0`
- direkte Vorgaengeranalyse: `2026-08-21T1422Z_GEN245_TUNNEL_PROVENIENZ_UND_HUMAN_FEEDBACK.md`

Die Vorgaengeranalyse hatte den fehlenden append-only Verlauf des neuen Human-Feedback-Sensors nur als Audit-Risiko aus Source-Inspektion abgeleitet. Unmittelbar danach trat genau der diskriminierende Live-Fall ein.

## 1. DELTA — erstes reales negatives Feedback und anschliessendes Entfernen

Commit `92a0fb42b1e5ec9c8dc8d0c24ec2211bd8a9bf64` exportierte um `2026-08-21T14:24:02Z` erstmals:

- Bewertungen: `1`
- hoch: `0`
- runter: `1`
- `wert = -1`
- `turn_id = 8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`
- `frage_turn_id = e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- `session_id = session:andreas:2`
- Antwort-Hash `7d990a323c5c077bb0df628cca19a03242b1bc8759ed74f967a5f1f504331d57`
- Modellfeld `mistral-small-latest` (weiter nur best-effort content-basiert, keine harte Modell-Ground-Truth)

Commit `afe252ae61277d8b26f92f13b2ffeb373ff42fb2` exportierte um `2026-08-21T14:24:55Z` wieder:

- Bewertungen: `0`
- hoch: `0`
- runter: `0`
- die konkrete vorherige Rating-Zeile wurde aus `bewertungen.jsonl` entfernt.

Der Source in `agentZero/code/produkt/bewertung.py` bestaetigt die beabsichtigte Semantik: `wert=0` fuehrt `DELETE FROM eos_bewertungen WHERE turn_id=? AND user_id=?` aus. Der Export beschreibt sich selbst als Vollabbild, nicht als Append-Log.

### Status

Der vorher nur theoretische Befund

`current-state feedback can erase its own historical source event`

ist damit jetzt **OBSERVED_AT_SNAPSHOT** und durch Source + zwei aufeinanderfolgende Exportcommits mechanistisch gestuetzt.

Was NICHT bekannt ist: warum die Bewertung entfernt wurde. Moeglich sind Meinungsrevision, versehentlicher Klick, UI-Korrektur oder ein anderer legitimer Nutzergrund. Diese Semantik bleibt `UNKNOWN`.

## 2. Der bewertete Turn ist stark kausal gebunden

Der negative Record ist kein verwaister Ratingzaehler.

Im gebundenen Gen245-Chat stehen exakt:

- User-Turn `e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`, Ordinal 29, Frage-Hash identisch zum Rating;
- Assistant-Turn `8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`, Ordinal 30;
- dessen Antwort-Hash ist identisch mit `outcome_hash` der Causal Episode.

Causal Episode:

- `causal_id = 832f1947-be11-41cc-890c-99dd4eba7ad0`
- `episode_id = 2fffbdd3-266c-4909-a70b-53aae22a62da`
- `observation_turn_id = e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- `reentered = 1`
- `effect_id = null`
- `credit = 0.0`

Workspace:

- gleiche `episode_id`
- `selected = respond`
- `state = COMPLETED`

Die Bewertung wurde laut Rating-`ts` ca. `31.36 min` nach dem Assistant-Turn gesetzt. Damit ist erstmals ein reales **verzoegertes menschliches Outcome-Signal** auf eine bereits persistierte Zero-Episode beobachtet.

### Promotion

- Rating -> Assistant-Turn: `VERIFIED_AT_SCOPE`
- Rating -> Frage-Turn: `VERIFIED_AT_SCOPE`
- Frage -> Causal Episode: `VERIFIED_AT_SCOPE`
- Causal -> Workspace: `VERIFIED_AT_SCOPE`
- harte Modellidentitaet: `NOT_VERIFIED` (bestehender content-basierter Alias-Rand)

## 3. Entscheidende Credit-Grenze: dieses Downvote ist KEIN Retrieval-Fehlerbeleg

Die Retrieval Episode fuer genau denselben User-Turn zeigt:

- `generation = 245`
- `status = UNKNOWN`
- `chars_selected = 0`
- `entry_keys = []`
- `selected_memory_ids = []`
- `shadow_memory_ids = []`
- gleiche `causal_id` und `episode_id`.

Damit wurde fuer diesen Turn **kein Memory-Kontext benutzt**.

Folge:

`human_feedback = -1` darf fuer diesen Fall NICHT als negativer Reward auf MicroClay/Retrieval-Entry-Points, Memory-IDs oder Retrieval-Ranking propagiert werden.

Die saubere Klassifikation ist:

`FEEDBACK_CAUSAL_JOIN = NO_RETRIEVAL_USED`

Der Downvote betrifft die Gesamtantwort bzw. irgendeinen ihrer anderen Entstehungsfaktoren. Welche Komponente verantwortlich war, ist aus diesen Daten allein nicht identifizierbar.

Das ist ein konkreter Falsifikator gegen eine naive Lernregel wie:

`if thumbs_down: punish retrieval policy`

Eine solche Regel wuerde in diesem realen ersten Datensatz Credit an einen Mechanismus vergeben, der gar nicht aktiv war.

## 4. Evidence-Epochengrenze: Rating-Sensor ist nicht atomar im Gen245-MANIFEST

`agentZero/MANIFEST.json` ist auf `2026-08-21T14:07:17Z` gebunden. Die spaeter separat exportierten `agentZero/bewertung/*`-Dateien sind darin nicht als Manifestartefakte enthalten.

Das bedeutet nicht, dass die Ratingdaten unbrauchbar sind. Ihre eigenen Commit-/Exportzeiten sind klar. Aber ein Repo-Head nach 14:24 enthaelt eine **gemischte Evidence-Epoche**:

- Causal/Workspace/Retrieval/Chat: atomarer Gen245-Exportstand um 14:07:17Z;
- Human-Feedback: separater aktueller Zustands-Snapshot um 14:24:xxZ.

Causal Joins sind nur dann zulaessig, wenn die referenzierten IDs tatsaechlich im aelteren gebundenen Snapshot existieren — wie in diesem Fall. `same Git head` darf nicht mit `same measurement instant` verwechselt werden.

## 5. Hypothesen und Gegenhypothesen

### H1 — History-destructive Feedback ist real

Hypothese: Das Current-State-Schema verliert bei `REMOVE` das urspruengliche Ratingereignis.

Vorhersage: Git-Historie kann SET -> REMOVE zeigen, aktueller Sensorzustand danach aber nur `0 Zeilen`.

Beobachtung: genau eingetreten.

Status: `MECHANISM_SUPPORTED`.

### GH1 — Nur Exportfehler / transient leere Datei

Gegenhypothese: Der zweite Export war wegen DB-/Lock-/I/O-Problemen leer, nicht wegen einer echten Removal-Semantik.

Dagegen spricht:

- Source definiert `wert=0` explizit als DELETE;
- Exportmetadaten deklarieren Vollabbild und Entfernbarkeit;
- zweiter Commit entfernt exakt die vorherige Zeile und aktualisiert Counts konsistent auf 0/0/0.

Aber ohne append-only Runtime-Event ist der konkrete ausloesende API-Aufruf selbst nicht separat konserviert. Daher wird `user executed REMOVE` nicht ueber die Source/Exports hinaus zu absoluter Ground Truth promoviert.

### H2 — Human feedback kann brauchbares Outcome-Signal sein, wenn Credit komponentenspezifisch gated ist

Vorhersage: Feedback laesst sich auf Turn/Episode binden, waehrend inaktive Subsysteme explizit `NO_*_USED` erhalten.

Beobachtung im ersten Fall: Turn/Causal/Workspace stark gebunden; Retrieval klar nicht benutzt.

Status: `RETAINED_HYPOTHESIS`, erster positiver Fall fuer die Join-Architektur.

### GH2 — Ein Downvote beweist Antwort-/Modellschwaeche

Nicht gestuetzt. Ein einzelner selektiver Daumen-runter hat weder Randomisierung noch Vergleichsbaseline; zudem wurde er spaeter entfernt. Modellzuordnung ist best effort. Ursache der Unzufriedenheit bleibt `UNKNOWN`.

Status: `REJECT_AS_CURRENT_CLAIM`.

## 6. Cross-domain Fusion

Externe Forschung wird hier nur als Methodenevidenz verwendet, nicht als Ersatz fuer Zero-Daten.

1. Nakajima, **The Log is the Agent: Event-Sourced Reactive Graphs for Auditable, Forkable Agentic Systems**, arXiv:2605.21997 (2026): beschreibt append-only Ereignislogs und daraus abgeleitete Arbeitszustaende als Weg zu Replay und end-to-end Lineage. Das stuetzt die vorgeschlagene Trennung `immutable feedback events -> materialized current rating state`, beweist aber nichts ueber Zero selbst.

2. Morandi & Viswanathan, **Correcting Selection Bias in Sparse User Feedback for Large Language Model Quality Estimation**, arXiv:2605.12177 (2026): behandelt nicht-zufaellige, sparse User-Feedback-Selektion und zeigt, dass naive Aggregation stark verzerrt sein kann. Das stuetzt die Pflicht, Coverage/Selection zuerst zu messen, nicht die Downvote-Quote als globale Qualitaet zu lesen.

## 7. Neue harte Forschungsinvarianten

### F95 — FEEDBACK_EVENT_LINEAGE

Wenn menschliches Feedback adaptiven Zustand veraendern darf, muss das konkrete SET/CHANGE/REMOVE-Ereignis dauerhaft adressierbar bleiben.

`materialized current rating != immutable learning evidence`

### F96 — COMPONENT_CREDIT_GATE

Feedback darf nur an Subsysteme propagiert werden, fuer die im gebundenen Turn eine nachweisbare Aktivierung/Contribution vorliegt.

Beispiel erster realer Fall:

- Turn: YES
- Causal: YES
- Workspace: YES
- Retrieval: NO
- Modell: AMBIGUOUS/BEST_EFFORT

Daher kein Retrieval-Penalty.

### F97 — EVIDENCE_EPOCH_TYPED_JOIN

Ein Join zwischen separat exportierten Sensorfamilien braucht explizite Zeit-/Snapshotsemantik. Repo-Koexistenz reicht nicht als Simultanitaetsbeweis.

## 8. Billigste naechste diskriminierende Messungen

1. `HUMAN_FEEDBACK_EVENT_LEDGER/v1` append-only mit `SET|CHANGE|REMOVE`, `event_id`, alter/neuer Wert, Turn/User/Session, Source-/Schema-Version.
2. `HUMAN_FEEDBACK_CAUSAL_JOIN_RECEIPT/v1` fuer jeden Ratingevent mit typisiertem Komponentenstatus: `USED | NOT_USED | UNKNOWN | AMBIGUOUS | ERROR`.
3. Separate Felder fuer `rating_event_ts`, `source_turn_ts`, `latency_s`, `sensor_export_ts`, `source_snapshot_id`.
4. Erst nach mehreren Ratings: `rating_coverage`, Removal-/Change-Rate, User-/Session-Propensity und Feedback-Latenzverteilung.
5. Modell-Credit erst nach direkter Output-Receipt-ID, nicht content-basierter Zuordnung.

## 9. Fusion / Forschungsstatus

- erster realer Human-Feedback-Datensatz: `OBSERVED_AT_SNAPSHOT`
- negativer Ratingevent auf Gen245-Turn: `VERIFIED_AT_SCOPE`
- anschliessender Current-State-Verlust der Zeile: `OBSERVED_AT_SNAPSHOT`
- history-destructive Current-State-Mechanismus: `MECHANISM_SUPPORTED`
- Grund der Entfernung: `UNKNOWN`
- Turn/Causal/Workspace-Lineage: `VERIFIED_AT_SCOPE`
- Retrieval als Ursache dieses Downvotes: `FALSIFIED_FOR_THIS_TURN`
- direkte Modellursache: `UNRESOLVED`
- Feedback als auditfestes Lernsignal: `NOT_READY`
- append-only Feedbackledger: `HIGH_PRIORITY_INSTRUMENT`
- Whole AgentZero / funktionales Bewusstsein: `NOT_CLAIMED`

## 10. Wichtigstes neues Ergebnis

Der erste reale Human-Feedback-Fall bestaetigt zwei Dinge gleichzeitig:

1. Das neue Feedbackinstrument ist **kausal wertvoll**, weil ein Rating bis in eine konkrete persistierte Zero-Episode zurueckgebunden werden kann.
2. Es ist **noch nicht lernfaehig-auditfest**, weil Removal die sichtbare Quellzeile zerstoert und weil Credit ohne Komponenten-Gating sofort falsch verteilt wuerde.

Der besonders starke Befund ist nicht `Zero bekam einen Daumen runter`, sondern:

> Ein realer Daumen-runter traf einen Turn mit nachweislich unbenutztem Retrieval und verschwand danach aus dem Current-State-Sensor. Damit sind sowohl die Notwendigkeit eines immutable Event-Ledgers als auch eines komponentenspezifischen Causal-Credit-Gates erstmals an demselben echten Zero-Fall empirisch demonstriert.
