# Generation 245 — Revocable Human Feedback: reversible Evidence-Credit-Semantik

## BIND

- Forschungsrolle: `agentzeroforschung/OWNER_DIRECTIVE_2026-08-18.md`
- letzter gebundener AgentZero-Voll-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- AgentZero-Generation: `245`
- Exportzeit: `2026-08-21T14:07:17Z`
- empirischer Trigger: erster real beobachteter Human-Feedback-Zustand `-1`, danach Entfernung desselben Ratings
- direkte interne Vorarbeiten:
  - `2026-08-21T1422Z_GEN245_TUNNEL_PROVENIENZ_UND_HUMAN_FEEDBACK.md`
  - `2026-08-21T1428Z_GEN245_FEEDBACK_WITHDRAWAL_CREDIT_BOUNDARY.md`
  - `2026-08-21T1429Z_GEN245_HUMAN_FEEDBACK_ERASURE_OBSERVED.md`

Diese Analyse baut **keine Produktfunktion**. Sie formuliert eine falsifizierbare Forschungssemantik fuer spaeteres Lernen aus widerrufbarem Human-Feedback.

## 1. Interner empirischer Anker

Im ersten real beobachteten Ratingfall gilt:

- ein konkreter Assistant-Turn erhielt `wert=-1`;
- das Rating traf deutlich nach Abschluss/Persistierung der Episode ein;
- der Ratingzustand wurde danach wieder entfernt;
- Rating -> Assistant-Turn -> User-Turn -> Causal Episode -> Workspace -> Retrieval -> Outcome-Hash ist am gebundenen Snapshot stark verknuepfbar;
- fuer genau diesen Turn war Retrieval `UNKNOWN`, `chars_selected=0`, keine Memory-IDs wurden benutzt;
- `effect_id=null`, `credit=0.0`.

Damit sind zwei voneinander verschiedene Forschungsfragen sichtbar:

1. **Temporalitaet:** Feedback kann spaeter als die Handlung eintreffen.
2. **Revision:** ein spaeter eingetroffenes Feedback kann selbst spaeter wieder verschwinden/geaendert werden.

Der zweite Punkt ist fuer Credit-Zuweisung strenger als normales delayed feedback.

## 2. Externe Primaerforschung — was sie stuetzt und was nicht

### Delayed feedback

Howson, Pike-Burke & Filippi, *Delayed Feedback in Generalised Linear Bandits Revisited* (2022), arXiv:2207.10786, behandelt Lernen bei zufaellig verzoegert eintreffendem Reward.

Wang et al., *Linear and Neural Dueling Bandits with Delayed Feedback* (2026), arXiv:2605.26554, uebertraegt die Delay-Frage direkt auf praferenzbasiertes Lernen.

**Transfer zu Zero:** Der Zeitpunkt eines Feedbacksignals ist selbst Teil des Lernproblems. Ein spaet eintreffender Daumen darf nicht so behandelt werden, als sei er synchron mit der Antwort entstanden.

**Nicht durch diese Arbeiten belegt:** dass ein bereits beobachtetes Reward-/Praferenzsignal spaeter widerrufen werden kann oder welche exakte Zero-Lernregel daraus folgen soll.

### Nichtstationaere Praeferenzen

Kolpaczki, Bengs & Huellermeier, *Non-Stationary Dueling Bandits* (2022), arXiv:2202.00935, modelliert Praeferenzmatrizen, die sich ueber die Zeit veraendern.

Saha & Gupta, *Optimal and Efficient Dynamic Regret Algorithms for Non-Stationary Dueling Bandits* (2021), arXiv:2111.03917, behandelt zeitvariable Praeferenzrelationen und dynamischen Regret.

**Transfer zu Zero:** Ein menschliches Praeferenzsignal muss nicht zeitinvariant sein. Historische und aktuelle Praeferenz sind unterschiedliche Variablen.

**Nicht belegt:** dass die konkrete Entfernung des ersten Zero-Downvotes eine echte Praeferenzveraenderung war. Der Grund bleibt `UNKNOWN`.

### Inkonsistenz / Subjektivitaet von Human Preferences

Christiano et al., *Deep Reinforcement Learning from Human Preferences* (2017), arXiv:1706.03741, etabliert Lernen aus menschlichen Praeferenzurteilen als Rewardquelle.

Zhang et al., *Diverging Preferences: When do Annotators Disagree and do Models Know?* (2024), arXiv:2410.14632, zeigt, dass Praeferenzdifferenzen nicht pauschal als blosses Labelrauschen verstanden werden sollten.

Huang et al., *Reliability-Aware LLM Alignment from Inconsistent Human Feedback* (2026), arXiv:2607.20515, motiviert reliability-aware Behandlung inkonsistenter Human-Feedback-Signale.

**Transfer zu Zero:** Ein einzelner menschlicher Daumen ist Evidenz, nicht Ground Truth.

**Wichtige Grenze:** Diese Arbeiten betreffen ueberwiegend mehrere Labels/Annotatoren oder Praeferenzverteilungen. Der beobachtete Zero-Fall ist eine intra-sessionale Revision/Entfernung eines einzelnen Nutzers und darf nicht einfach mit Inter-Annotator-Disagreement gleichgesetzt werden.

## 3. Neue Problemklasse: DELAYED + REVOCABLE FEEDBACK

Zero zeigt mindestens einen Fall, der mit folgender Zustandsfolge kompatibel ist:

`UNRATED -> RATED(-1) -> UNRATED/WITHDRAWN`

Der beobachtbare Current-State allein kann aber nicht entscheiden, **warum** die zweite Transition geschah.

Mindestens drei Gegenrealitaeten bleiben offen:

### H1 — Korrektur eines versehentlichen Ratings

Der erste `-1` war ein Bedien-/Bewertungsfehler; Removal macht ihn fuer langfristiges Lernen ungueltig.

### H2 — echte Praeferenzrevision

Der `-1` war zum Zeitpunkt t1 valide; spaeter aenderte sich die Bewertung/Praeferenz. Historisch bleibt das Ereignis real, fuer den aktuellen Praeferenzzustand ist es aber nicht mehr aktiv.

### H3 — Entfernung ohne semantische Gegenbewertung

Removal bedeutet lediglich "keine aktuelle Bewertung". Es ist weder `+1` noch zwingend eine Widerlegung des frueheren `-1`.

Mit den aktuellen Daten sind H1/H2/H3 nicht unterscheidbar.

**Folge:** `REMOVE` darf semantisch weder automatisch als `reward=0`, noch als `reward=+1`, noch als Beweis gelesen werden, dass das alte `-1` falsch war.

## 4. Kandidat: REVOCABLE_FEEDBACK_STATE_MACHINE/v1

Forschungsinstrument, nicht Produktautoritaet.

Ereignisse bleiben append-only:

- `SET(+1|-1)`
- `CHANGE(+1<->-1)`
- `REMOVE`

Materialisierte aktuelle Sicht wird separat abgeleitet:

- `UNRATED`
- `RATED_POSITIVE`
- `RATED_NEGATIVE`

Zusaetzlicher Lernstatus:

- `PENDING_EVIDENCE`
- `ACTIVE_EVIDENCE`
- `REVOKED_EVIDENCE`
- `AMBIGUOUS_LINEAGE`

Keine dieser Klassen behauptet den unbekannten psychologischen Grund der Nutzeraktion.

## 5. Drei konkurrierende Credit-Mechanismen

### M0 — immediate irreversible credit

Bei SET wird sofort ein permanenter Policy-Delta geschrieben. CHANGE/REMOVE haben keine exakte Rueckwirkung.

**Vorhersage:** Nach `SET(-1) -> REMOVE` bleibt ein residualer Policy-Delta bestehen.

**Risiko:** abgeleiteter Zustand ueberlebt seine aktive Evidenzlinie.

### M1 — stability-window / deferred credit

Feedback wird fuer ein empirisch bestimmtes Zeitfenster nur als `PENDING_EVIDENCE` gehalten. Erst danach darf es adaptiven Credit erzeugen.

**Vorhersage:** Wird ein Rating vor Ablauf des Fensters entfernt, entsteht kein Policy-Delta.

**Trade-off:** bessere Robustheit gegen schnelle Revisionen, aber langsamere Lernreaktion. Ein fixes Fenster ist ohne Withdrawal-Latenzverteilung willkuerlich und darf jetzt noch nicht festgelegt werden.

### M2 — immediate reversible contribution credit

SET darf sofort eine exakt adressierbare, reversible Evidenz-Contribution erzeugen. Adaptive Zustandsaenderung ist aus Contribution-IDs abgeleitet.

Bei CHANGE/REMOVE wird nicht Historie geloescht, sondern die aktive Contribution deaktiviert/kompensiert und der abgeleitete Zustand deterministisch neu materialisiert.

**Vorhersage:** Nach `SET(-1) -> REMOVE` kehrt der feedback-abhaengige Anteil des adaptiven Zustands exakt zur feedback-freien Baseline zurueck.

**Harte Voraussetzung:** exakte Source-Event-ID, komponentenspezifischer Credit, deterministische Reversibilitaet oder rebuildbarer abgeleiteter Lernzustand.

## 6. Warum M2 strukturell interessant ist

M2 verbindet zwei bereits beobachtete AgentZero-Probleme:

1. Gen241/244: abgeleiteter adaptiver Zustand kann seine sichtbare Ursprungsprovenienz ueberleben.
2. Gen245: Human-Feedback kann im Current-State wieder verschwinden.

Ein gemeinsamer Architektur-/Forschungsgrundsatz lautet daher:

`adaptive state should be derivable from still-addressable evidence contributions`

Das ist **eine Hypothese**, noch kein verifizierter Mechanismus.

## 7. Component Credit Mask bleibt zwingend

Der erste reale Downvote demonstriert bereits einen separaten Credit-Falsifikator:

- Retrieval war nicht aktiv (`0` Memories);
- kein Effect war aktiv;
- dennoch existierte Human-Feedback `-1`.

Daher muss ein spaeterer Feedback-Credit vor jeder Komponentenaktualisierung eine Activity-Maske anwenden.

Beispiel:

`thumbs_down` + `retrieval_used=false` => `retrieval_credit = NOT_APPLICABLE`, nicht `-1`.

Dasselbe Prinzip gilt fuer Effects, Modellpfad, Web-/Toolpfad und andere Komponenten: Credit nur an kausal aktive, ausreichend gebundene Mechanismen.

## 8. Billigster diskriminierender Replay-Test

Sobald ein append-only Feedback-Eventstrom als Forschungsinstrument vorhanden ist, drei identische Replay-Sequenzen gegen M0/M1/M2 fahren:

`baseline -> SET(-1) -> REMOVE`

Messen:

- `policy_delta_after_set`
- `residual_policy_delta_after_remove`
- `rollback_exactness`
- `event_to_policy_lineage_coverage`
- `credit_latency`
- `component_misattribution_count`

Erwartete Trennung:

- M0: residualer Delta > 0 moeglich/erwartet;
- M1: bei Remove vor Aktivierung residualer Delta = 0, aber Lernlatenz > 0;
- M2: sofortiger Delta moeglich, nach Remove exakt kompensiert/rebuilt.

Dies ist ein **Forschungsreplay**; kein echtes Nutzerfeedback soll dafuer kuenstlich erzeugt oder manipuliert werden.

## 9. Neue Messwerte vor jeder Promotion

- `feedback_set_count`
- `feedback_change_count`
- `feedback_remove_count`
- `withdrawal_latency_distribution`
- `revision_rate`
- `current_state_vs_event_history_gap`
- `feedback_lineage_complete_rate`
- `component_credit_applicable_rate`
- `residual_policy_delta_after_revocation`
- `rebuild_equivalence_after_revocation`

Mit `n=1` beobachtetem transienten Rating duerfen weder Withdrawal-Rate noch optimales Stability-Window geschaetzt werden.

## 10. Adversarial Review

### Gegenargument A — Removal sollte alte Evidenz komplett annullieren

Moeglich unter H1, aber nicht unter H2. Ohne expliziten Removal-Grund bleibt dies unidentifizierbar. Eventgeschichte muss erhalten bleiben; nur ihre aktuelle Lernaktivitaet darf typisiert werden.

### Gegenargument B — Event-Ledger allein loest das Problem

Nein. Ein Ledger loest Auditierbarkeit, aber nicht Credit-Semantik. Es sagt, **dass** SET/REMOVE geschah, nicht welcher Algorithmus den daraus resultierenden Policy-Credit korrekt behandelt.

### Gegenargument C — einfach jeden Daumen als Reward nutzen

Der erste reale Fall falsifiziert zumindest komponentenagnostischen Credit: Retrieval war inaktiv. Ausserdem zeigt die Entfernung, dass Feedbackzustand zeitlich revidierbar ist.

### Gegenargument D — Git ist ausreichend

Git ist ein getakteter forensischer Side-Channel. Zwischen Exporten koennen Events aliasen; es ist kein atomarer Runtime-Eventstrom.

## 11. Promotionsstatus

- delayed human feedback im ersten realen Fall: `OBSERVED_AT_SNAPSHOT`
- feedback withdrawal/current-state erasure: `MECHANISM_SUPPORTED`
- konkreter Grund des Removals: `UNKNOWN`
- Human Feedback als zeitinvariante Ground Truth: `NOT_SUPPORTED`
- naive komponentenagnostische negative Credit-Regel: `FALSIFIED_AT_SCOPE` fuer Retrieval dieses Falls
- `REVOCABLE_FEEDBACK_STATE_MACHINE/v1`: `RETAINED_HYPOTHESIS`
- M0 immediate irreversible: `NEGATIVE_BASELINE_CANDIDATE`
- M1 stability-window: `RETAINED_HYPOTHESIS`
- M2 reversible contribution credit: `RETAINED_HYPOTHESIS`
- optimale Lernsemantik: `UNRESOLVED`

## 12. Naechster maximaler Informationsgewinn

1. append-only Feedback-Events messen;
2. reale Withdrawal-/Change-Latenzverteilung sammeln;
3. M0/M1/M2 nur in deterministischem Research-Replay gegeneinander testen;
4. Activity-/Causal-Mask je Komponente erzwingen;
5. erst danach irgendeinen Human-Feedback-Credit fuer adaptives Lernen promoten.

Der Kernbefund dieses Zyklus lautet:

> **Widerrufbares Human-Feedback ist keine statische Rewardzahl, sondern versionierte Evidenz. Auditierbarkeit und Credit-Semantik sind zwei getrennte Forschungsprobleme.**
