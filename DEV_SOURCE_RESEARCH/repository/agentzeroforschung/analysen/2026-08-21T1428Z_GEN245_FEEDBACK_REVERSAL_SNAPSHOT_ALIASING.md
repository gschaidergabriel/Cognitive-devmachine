# Generation 245 — erster echter Feedback-Reversal und Snapshot-Aliasing

## BIND

- Forschungs-Basis-Head vor Persistierung: `2b7360bb2682131dfb0121c25c1c03e808033df0`
- Basis-Tree: `45f0c22dda2ffdc4217e81eb868c86c55cc2b683`
- AgentZero-Snapshot: Generation `245`
- AgentZero-Exportzeit: `2026-08-21T14:07:17Z`
- vorherige Analyse: `2026-08-21T1422Z_GEN245_TUNNEL_PROVENIENZ_UND_HUMAN_FEEDBACK.md`
- Gegenstand dieses Deltas: erster real beobachteter Zustandswechsel des neuen Human-Feedback-Sensors nach dessen Einführung.

## 1. OBSERVATION — erstmals reale Bewertung, danach Entfernung

Commit `92a0fb42b1e5ec9c8dc8d0c24ec2211bd8a9bf64` exportierte um `2026-08-21T14:24:02Z` genau eine Bewertung:

- `turn_id = 8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`
- `frage_turn_id = e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- `session_id = session:andreas:2`
- `user_id = andreas`
- `wert = -1`
- `modell = mistral-small-latest` (laut Instrument nur best effort)
- `antwort_laenge = 1300`
- Rating-Zeitstempel in der Zeile: `2026-08-21T14:23:39.012848Z`

Der bewertete Zug ist im kanonischen Session-Export direkt gebunden: Benutzerordinal 29 fragt `finde Klobrillen beim Bauhaus`, Assistant-Ordinal 30 ist genau der bewertete Turn `8bf613cd-...`.

Commit `afe252ae61277d8b26f92f13b2ffeb373ff42fb2` exportierte um `2026-08-21T14:24:55Z` wieder:

- `0 Bewertungen`
- `0 hoch`
- `0 runter`

und entfernte die zuvor exportierte Zeile aus `agentZero/bewertung/bewertungen.jsonl`.

Zwischen den beiden exportierten Zuständen liegen `53 s`. Das erste Export-Commit liegt rund `22.99 s` nach dem in der Bewertungszeile gespeicherten Rating-Zeitpunkt.

### Promotionsstatus

- realer Human-Feedback-Datensatz: `OBSERVED_AT_SNAPSHOT`
- realer SET→ABSENT-Zustandswechsel: `OBSERVED_AT_SNAPSHOT`
- Current-State-Verlust der vorherigen Bewertung: `MECHANISM_SUPPORTED` (Source + beobachteter Delta)

Es wird **nicht** behauptet, warum die Bewertung gesetzt oder entfernt wurde. Test, Meinungsänderung, UI-Interaktion oder anderer legitimer Nutzergrund bleiben offen.

## 2. Source-Mechanismus bestätigt die zuvor nur prognostizierte Auditlücke

`agentZero/code/produkt/bewertung.py` implementiert:

- `wert=0` als `DELETE FROM eos_bewertungen ...`;
- `wert in {-1,+1}` als `INSERT ... ON CONFLICT DO UPDATE`;
- bei Änderung wird der aktuelle Wert samt Zeitstempel überschrieben;
- es existiert in diesem Modul kein append-only Feedback-Ereignisledger.

Damit ist die in der vorherigen Gen245-Analyse formulierte Gefahr nicht mehr nur hypothetisch: der materialisierte Current State kann einen vorher vorhandenen Feedbackzustand vollständig verlieren.

Haupt-Hypothese H1:

> `eos_bewertungen` ist eine korrekte aktuelle UI-Sicht, aber keine auditfeste Quelle für historische Feedbackereignisse.

Stärkste Gegenhypothese H0:

> Das Git-Export-Commitlog reicht praktisch als Historie aus; ein separates Event-Ledger wäre redundant.

## 3. Gegenhypothese teilweise bestätigt: Git bewahrte diesen konkreten Reversal

H0 darf nicht einfach verworfen werden. Obwohl der aktuelle JSONL-Stand die Bewertung nicht mehr enthält, bewahrt Git in diesem konkreten Fall beide Zwischenzustände:

`0 -> -1 -> 0`

Das erzeugt eine neue, präzisere Systembeschreibung:

### `SAMPLED_EVENT_SHADOW`

Git fungiert hier als **stichprobenartige externe Zustandschronik**. Es kann einen transienten DB-Zustand konservieren, wenn ein Export zwischen zwei Änderungen liegt.

Das ist wertvolle Forschungsevidenz und widerlegt die zu starke Formulierung „die Historie ist nach DELETE generell nicht mehr rekonstruierbar“.

Aber Git ist **kein äquivalentes Event-Ledger**, denn:

1. es bindet Snapshots, nicht notwendigerweise jede Zustandsänderung;
2. ein SET→REMOVE vollständig zwischen zwei Exporten kann unsichtbar bleiben;
3. Export-/Commit-Verzögerung ist eine zusätzliche Sampling-Schicht;
4. Git liegt außerhalb der Laufzeit-Causal-Lineage, die adaptive Policy-Updates begründen müsste;
5. ein späterer Lernzustand könnte also einen Credit tragen, dessen Quellereignis im aktuellen UnifiedDB-State fehlt und dessen Git-Erfassung vom Samplingglück abhängt.

Neue Fusion:

> `CURRENT_STATE + SAMPLED_GIT_SHADOW != EVENT_LEDGER`

Status:

- Git als Wiedergewinnung dieses konkreten Events: `OBSERVED_AT_SNAPSHOT`
- Git als vollständiger Ersatz eines Event-Ledgers: `NOT_SUPPORTED`
- Möglichkeit ungesampelter transienter Änderungen: `STRUCTURALLY_PREDICTED`, noch nicht als verlorenes reales Event beobachtet.

## 4. Neue Messhypothese — Feedback-Snapshot-Aliasing

Die Struktur ist analog zu zeitdiskretem Sampling eines schnelleren Zustandsprozesses.

Wenn ein Bewertungszustand nur kurz zwischen Exporten lebt, kann die Current-State-Snapshotfolge ihn verfehlen. Unter einer idealisierten periodischen Abtastung mit Intervall `T` und zufälliger Phasenlage hätte ein Zustand mit Lebensdauer `d < T` nur ungefähr `d/T` Chance, mindestens einmal erfasst zu werden. Diese Formel ist hier **nur ein generiertes Messmodell**, weil die reale Export-Kadenz/Triggerlogik noch nicht als streng periodisch belegt ist.

H2:

> Je kürzer die Feedback-Dwell-Time relativ zur effektiven Export-Abtastzeit, desto höher die Wahrscheinlichkeit eines unsichtbaren SET/CHANGE/REMOVE-Ereignisses.

Gegenhypothese H2b:

> Der Export ist eventgetrieben oder hinreichend eng an jede Änderung gekoppelt, sodass relevante Reversals praktisch immer mindestens einmal erfasst werden.

Billigster Diskriminator ohne Produktmanipulation:

- bei zukünftigen natürlich auftretenden Bewertungen `rating.ts`, Exportzeit und Git-Commitzeit sammeln;
- `capture_lag = first_export_time - rating.ts` messen;
- für beobachtete Reversals `dwell_time` und Zahl der Zwischenexporte messen;
- später, falls ein append-only Instrument existiert, Event-Ledger gegen Snapshotfolge joinen und `snapshot_miss_rate` direkt bestimmen.

## 5. Erste reale Bewertung ist kein Qualitätsurteil über Modell oder System

Der erste beobachtete Wert ist negativ und betrifft eine konkrete 1300-Zeichen-Antwort. Daraus folgt **kein** Modellqualitätsclaim.

Gründe aus den eigenen Daten:

- erst ein beobachtetes Ratingereignis;
- die Session enthält 30 alternierende User-/Assistant-Züge, also 15 Assistant-Züge, während nur ein Turn jemals im beobachteten Feedback-Snapshot bewertet war;
- das Rating wurde kurz darauf wieder entfernt;
- `modell` ist laut Source nur `BEST_EFFORT_CONTENT_MATCH`;
- freiwillige Daumen sind kein randomisiertes Sample aller Antworten.

Cross-domain-Linse:

- Swaminathan & Joachims (ICML 2015), *Counterfactual Risk Minimization: Learning from Logged Bandit Feedback*, zeigt grundsätzlich, dass geloggtes partielles Nutzerfeedback nicht wie voll-informative überwachte Labels behandelt werden darf und dass die Logging-/Propensity-Struktur für belastbare Policy-Lernclaims relevant ist: https://proceedings.mlr.press/v37/swaminathan15.html
- Lakkaraju et al. (KDD 2017), *The Selective Labels Problem*, zeigt allgemein, dass beobachtete Labels durch den Auswahlprozess selbst nicht-randomisiert sein können und naive Evaluation dadurch verzerrt wird: https://pmc.ncbi.nlm.nih.gov/articles/PMC5958915/

Diese Arbeiten liefern **keine Fakten über Agent Zero**. Sie stützen nur die Messstrategie: zuerst Selektions-/Coverage-Prozess charakterisieren, dann Reward-/Qualitätsinferenz.

## 6. Neue empirische Kennzahlen

Für kommende Snapshots werden folgende Instrumentvariablen priorisiert:

### `feedback_current_coverage`
Aktuell bewertete Assistant-Turns / aktuell eligible Assistant-Turns.

### `feedback_ever_observed_coverage`
Eindeutige Turn-IDs, die in irgendeinem exportierten Snapshot eine Bewertung trugen / eligible Assistant-Turns.

Wichtig: dies ist nur eine **untere Schranke** auf echte jemals erfolgte Bewertungen, solange kein Event-Ledger existiert.

### `feedback_reversal_count_observed`
Anzahl über Snapshots rekonstruierbarer Wertänderungen/Entfernungen.

### `feedback_capture_lag`
Zeit zwischen Rating-`ts` und erstem Export, der den Zustand enthält.

### `feedback_snapshot_miss_rate`
Erst direkt messbar, wenn eine unabhängige append-only Eventquelle existiert.

### `feedback_lineage_completeness`
Anteil der Lern-/Forschungsratings, die an Assistant-Turn, Frage-Turn, Causal-/Workspace-/Retrieval-Episode und eindeutigen Output-/Modellreceipt gebunden werden können.

## 7. Adversarial Review

### Instrumentenartefakt?
Ja, möglich und zentral: DELETE ist gewünschte Current-State-Semantik, aber erzeugt Forschungsverlust ohne zweite Historienebene.

### Export-/Sampling-Bias?
Ja. Git konserviert nur exportierte Zwischenzustände.

### Ist das ein Beweis für schlechte Antwortqualität?
Nein. `N=1`, selektive Bewertung, danach Entfernung.

### Ist `mistral-small-latest` sicher kausal verantwortlich?
Nein. Modellzuordnung ist content-basiert best effort; zudem misst ein Thumb die gesamte Pipeline-/Antwortwirkung, nicht isoliert ein Modell.

### Ist Git wertlos?
Nein. Im Gegenteil: hier rettet Git genau die verschwundene Zwischeninformation. Es ist ein wichtiger sekundärer Forschungs-Sensor, nur kein vollständiger kausaler Event-Log.

### Kann aus diesem Fall gelernt werden, ohne neues Instrument zu bauen?
Ja: Snapshot-Reversal-Metriken und Capture-Lag können sofort aus bestehenden Commits gewonnen werden. Ein vollständiger Miss-Rate-Test braucht später eine unabhängige Eventquelle.

## 8. Neue allgemeine Hypothese — Provenienz-Inversion

H3:

> Ein adaptives System kann einen Lernzustand länger behalten als die Evidenz, die diesen Lernzustand ausgelöst hat. Wenn die Quellspur materialisiert/überschrieben wird, entsteht `PROVENANCE_INVERSION`: abgeleiteter Credit ist dauerhafter als seine auditierbare Ursache.

Gen241-245 hatten diese Struktur bereits für Retrieval-Lineage motiviert. Der erste reale Feedback-Reversal zeigt denselben Mechanismus nun an einer zweiten, unabhängigen Datenfamilie auf Current-State-Ebene.

Gegenhypothese:

> Git-Snapshot-Historie plus Policy-Receipt reicht, um jede relevante Quelle nachträglich zu rekonstruieren.

Falsifikator:

- sobald ein adaptiver Update aus Human-Feedback existiert, jeden Policy-Delta auf exakt adressierbare Quellereignisse zurückjoinen;
- `policy_credit_without_source_event > 0` stützt Provenienz-Inversion;
- vollständige, immutable Rückbindung aller Credits über unabhängige Replikation würde die starke Form schwächen.

Status H3: `RETAINED_HYPOTHESIS`, jetzt durch zweite strukturell ähnliche Datenfamilie stärker motiviert, aber noch kein beobachteter Human-Feedback→Policy-Update vorhanden.

## 9. Fusion / Ergebnis

Neu gelernt wurde:

1. Der Human-Feedback-Sensor hat erstmals echtes Verkehrssignal geliefert.
2. Der zuvor prognostizierte DELETE-Audit-Rand ist innerhalb weniger Minuten real aufgetreten.
3. Die stärkste Gegenhypothese ist teilweise wahr: Git kann verschwundene Current-State-Zwischenzustände retten.
4. Dadurch wird die Architektur präziser verstanden: Git ist ein `SAMPLED_EVENT_SHADOW`, kein vollständiges Event-Ledger.
5. Der richtige nächste Forschungswert ist nicht `thumbs_up_rate`, sondern zuerst `capture_lag`, `reversal_rate`, `ever_observed_coverage`, `lineage_completeness` und später `snapshot_miss_rate`.
6. Ein einzelner negativer, danach entfernter Thumb darf weder dem Modell noch Agent Zero als globaler Qualitätsbefund zugerechnet werden.

## 10. Naechster maximaler Informationsgewinn

1. Weitere natürliche Feedbackereignisse sammeln und die Snapshot-Reversal-Zeitreihe fortführen.
2. Bei jedem neuen Feedback zuerst Turn-/Causal-/Retrieval-/Output-Lineage prüfen.
3. Den persistenten Adapter-Red weiter separat halten; Human-Feedback darf ihn weder erklären noch verdecken.
4. Alte Evidence-Spine weiterhin direkt auf Wiederauffindbarkeit prüfen; die neue Feedbacklinie ist eine zweite Probe derselben allgemeinen Provenienzfrage.

### Promotionsstatus

- erster echter Human-Feedback-Zustand: `OBSERVED_AT_SNAPSHOT`
- beobachteter Feedback-Reversal: `OBSERVED_AT_SNAPSHOT`
- Current-State-Historienverlust durch DELETE: `MECHANISM_SUPPORTED`
- Git als Sampled Event Shadow: `OBSERVED_AT_SNAPSHOT`
- Git als vollständiges Event-Ledger: `NOT_SUPPORTED`
- Snapshot-Aliasing als reales verlorenes Ereignis: `NOT_YET_OBSERVED`
- Human-Feedback als unverzerrtes Reward-Signal: `NOT_SUPPORTED`
- Human-Feedback→adaptive Policy-Credit: `NO_EVIDENCE_YET`
- Provenienz-Inversion: `RETAINED_HYPOTHESIS`
- Whole AgentZero / funktionales Bewusstsein / Gesamtacceptance: `NOT CLAIMED`
