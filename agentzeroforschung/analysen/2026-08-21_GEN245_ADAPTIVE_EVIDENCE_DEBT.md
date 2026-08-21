# Generation 245 — Adaptive Evidence Debt

## BIND

- Research-`main` bei Branch-Bildung: `697628567d84f9a39f7bc683047b832626f06335`
- letzter gebundener AgentZero-Voll-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- AgentZero-Generation: `245`
- direkte lokale Basisanalysen:
  - `2026-08-21T1314Z_GEN244_EVIDENCE_EPOCH_BOUNDARY.md`
  - `2026-08-21T1422Z_GEN245_TUNNEL_PROVENIENZ_UND_HUMAN_FEEDBACK.md`
  - `2026-08-21T1429Z_GEN245_HUMAN_FEEDBACK_ERASURE_OBSERVED.md`
- keine neue AgentZero-Laufzeitmutation und kein ungewöhnliches `go`-Experiment in dieser Analyse

Diese Notiz baut bewusst **nicht** noch ein zweites Event-Ledger-Konzept. Der Gen245-Stand hat bereits gezeigt, dass Human-Feedback als Current-State nicht als vollständige Ereignisprovenienz taugt. Der neue Delta ist eine quantitative Forschungsgröße für den allgemeineren Zustand, der in Gen244 und Gen245 sichtbar wird:

> Ein adaptiver Zustand kann weiterwirken, obwohl seine auslösende Evidenz nicht mehr vollständig adressierbar, gültig oder reversibel gebunden ist.

Diesen Zustand nennen wir **Adaptive Evidence Debt (AED)**.

## 1. Beobachtete Anker

### A1 — persistierendes Retrieval-Kapital ohne vollständig sichtbare Ursprungs-Episoden

Gen244 bindet:

- `retrieval_entrypoint_policy = 27` Zeilen;
- `retrieval_feedback = 20` Zeilen;
- `retrieval_policy_state = 1` Zeile;
- aktuelle sichtbare Retrieval-Episoden stammen nur aus der neuen Epoche;
- ältere Feedback-Receipts referenzieren Retrieval-IDs aus Generationen `80..145`, deren Ursprungs-Episoden in der aktuellen `retrieval_episodes`-Oberfläche nicht sichtbar sind.

Damit ist mindestens auf Beobachtungsebene belegt:

`adaptive state present + source episode lineage incomplete/hidden`

Ob die Quellen wirklich gelöscht, nur verborgen oder mit einem noch unbekannten Mapping verdichtet wurden, bleibt offen.

### A2 — reales Human-Feedback kann aus dem Current-State verschwinden

Gen245 bindet einen realen Verlauf:

`0 -> 1 negative Bewertung -> 0`

Der Current-State ist danach kompatibel sowohl mit „nie bewertet“ als auch mit „bewertet und entfernt“. Damit ist die UI-Sicht korrekt, aber als alleinige historische Lernprovenienz unzureichend.

### A3 — noch kein Beleg, dass Human-Feedback bereits adaptiven Zustand verändert

Aus A2 folgt **nicht**, dass aktuell Human-Feedback in Retrieval-/Routing-/Modellpolicy einfließt. Für Human-Feedback ist AED daher derzeit ein Forschungsrisiko und Messziel, kein beobachteter Reward-Schaden.

## 2. Begriff: Adaptive Evidence Debt

Für einen aktiven adaptiven Zustand `s` seien seine kausalen Evidenzquellen `E(s)`.

Eine Quelle gilt als `VALID_BOUND`, wenn mindestens gilt:

1. eindeutige Source-ID;
2. unverwechselbarer Turn/Episode-/Outcome-Bezug;
3. Herkunft und Generation/Version sind adressierbar;
4. Änderung, Widerruf oder Tombstone ist explizit typisiert;
5. die Ableitung `source -> adaptive update` ist reproduzierbar oder durch einen expliziten Compaction-/Derivation-Receipt ersetzt;
6. Fehler/Abwesenheit/Unmeasured sind nicht semantisch zusammengefallen.

Eine aktive adaptive Zustandskomponente trägt **Evidence Debt**, wenn ihr wirksamer Credit/Debit nicht vollständig auf solche gültig gebundenen Quellen zurückgeführt werden kann.

Wichtig:

- AED ist **kein Qualitätsmaß** des Agenten;
- AED ist **kein Bewusstseinsmaß**;
- AED sagt nicht, ob der gelernte Zustand richtig oder falsch ist;
- AED misst Auditierbarkeit/Falsifizierbarkeit adaptiver Wirkung.

## 3. Metriken

### 3.1 Adaptive Evidence Coverage (AEC)

Ungewichtete Minimalform:

`AEC = fully_bound_active_adaptive_units / all_active_adaptive_units`

`AED = 1 - AEC`

Diese Form ist nur brauchbar, wenn eine „adaptive unit“ sauber definiert ist, z. B. Policy-Key, Entry-Point-Prior oder persistierter Heuristikzustand.

### 3.2 Weighted Adaptive Evidence Debt (wAED)

Nicht jede Policy-Komponente wirkt gleich stark. Sobald ein reproduzierbares Einflussgewicht `w_i` existiert:

`wAEC = sum(w_i for fully_bound i) / sum(w_i for active i)`

`wAED = 1 - wAEC`

Ohne belastbares Einflussgewicht darf nicht so getan werden, als sei die gewichtete Variante messbar. Dann bleibt die ungewichtete Coverage die konservative Basis.

### 3.3 Revocation Debt (RD)

Für Evidenzquellen, die geändert, entfernt, invalidiert oder als falsch markiert wurden:

`RD = active_adaptive_influence_from_revoked_sources_without_compensation / active_adaptive_influence_from_all_revoked_sources`

Wenn Einfluss nicht quantitativ messbar ist, zuerst nur zählen:

- `revoked_source_count`;
- `revoked_sources_with_active_dependents`;
- `revoked_sources_with_compensation_or_replay_receipt`;
- `revoked_sources_unmapped`.

### 3.4 Orphan Adaptive Capital Rate (OACR)

`OACR = active_adaptive_units_with_no_addressable_source_lineage / all_active_adaptive_units`

Gen244 motiviert genau diese Größe. Der aktuelle Stand erlaubt noch **keinen belastbaren numerischen OACR**, weil `nicht sichtbar` nicht gleich `gelöscht/unmapped` ist.

### 3.5 Causal Derivation Completeness (CDC)

Für jeden adaptiven Update-Receipt:

`source event -> user/assistant turn -> causal/retrieval/workspace episode -> outcome/feedback -> adaptive update -> current state`

Klassifikation:

- `FULLY_BOUND`
- `BOUND_VIA_COMPACTION_RECEIPT`
- `SOURCE_HIDDEN_BUT_MAPPED`
- `SOURCE_REVOKED_COMPENSATED`
- `SOURCE_REVOKED_UNCOMPENSATED`
- `SOURCE_MISSING`
- `AMBIGUOUS`
- `ERROR`

Nur die ersten vier Klassen dürfen als provenance-komplett gelten.

## 4. Neue Hypothese H-AED

**H-AED:** Die kritischste Langzeitgefahr selbstadaptiver Agenten ist nicht nur „falsches Lernen“, sondern **nicht mehr falsifizierbares Lernen**: adaptiver Einfluss bleibt aktiv, während die Evidenzlinie so weit erodiert, dass spätere Gegenbeweise, Widerrufe oder Replay den Ursprung nicht mehr sicher erreichen.

### Vorhersagen

Wenn H-AED für AgentZero relevant ist, sollten wir mindestens einen dieser Fälle beobachten:

1. aktive Retrieval-/Routing-Policy referenziert Source-Receipts, deren Episode nicht direkt oder über Mapping auffindbar ist;
2. ein Source-Event wird widerrufen, aber abhängige Policy-Einträge bleiben ohne Compensation-/Replay-Receipt aktiv;
3. aktuelle Policy kann nicht aus einer gebundenen Evidence-Epoche deterministisch oder semideterministisch rekonstruiert werden;
4. zwei Systeme mit gleichem Current-State, aber unterschiedlicher Evidenzgeschichte sind im Audit nicht unterscheidbar.

## 5. Stärkste Gegenhypothesen

### H0a — nur Export-Sichtbarkeit ist kaputt

Die gesamte Lineage existiert in der Live-DB oder in Archiv-/Compaction-Strukturen. Dann ist AED deutlich kleiner als es die Exporte suggerieren.

**Falsifikator gegen H-AED:** bekannte pre-collapse IDs werden vollständig oder über verlustbewahrende Mappings gefunden; alle aktiven Policy-Updates lassen sich auf gültige Quellen zurückführen.

### H0b — Policy ist vollständig deterministisch aus aktuellem State ableitbar

Wenn keine historische Evidenz für Reproduktion, Widerruf oder Falsifikation benötigt wird, wäre fehlende Ereignisgeschichte weniger kritisch.

Diese Gegenhypothese ist nur dann stark, wenn die Policy wirklich verlustfrei aus kanonischem aktuellem State reproduzierbar ist und Änderungen alter Evidenz keine semantische Rolle mehr spielen.

### H0c — adaptive Wirkung ist vernachlässigbar

Es könnte persistierende Policy-Strukturen geben, die real kaum oder gar nicht in den Outputpfad eingreifen. Dann wäre hohe AED-Metrologie zwar formal unsauber, aber behavioraler Schaden klein.

Daher muss AED später mit echter **behavioraler Einflussstärke** verbunden werden; bloße Zeilenzahl ist kein Wirkungsbeweis.

## 6. Cross-domain-Fusion

### Provenance-Systeme

W3C PROV trennt Entities, Activities, Agents und Derivationen und definiert Validitäts-/Ordnungsbedingungen für Provenienz. Für AgentZero ist die nützliche Übertragung nicht ein 1:1-Ontologieimport, sondern der Grundsatz:

`adaptive state = derived entity`

`feedback/outcome/retrieval episode = source entity`

`learning update = activity`

`user/model/runtime = agents with distinct roles`

Damit kann ein Derivation-Receipt strukturell geprüft werden, statt Provenienz nur als freie Metadaten zu speichern.

### Event Sourcing

Event Sourcing trennt Current-State von der Ereignisfolge. Gen245 zeigt empirisch, warum dieselbe Trennung für Ratings notwendig ist. AED erweitert dies: selbst ein perfektes Event-Ledger reicht nicht, wenn die **Ableitung vom Event in adaptiven Zustand** nicht ebenfalls gebunden wird.

### Selective Labels

Freiwillige Daumenbewertungen sind selektiv beobachtete Labels. Das heißt: selbst bei perfekter Provenienz ist `thumbs_up_rate` keine unverzerrte globale Qualitätswahrscheinlichkeit. AED und Selection Bias sind orthogonal:

- AED fragt: „Kann ich den Einfluss dieses Labels kausal/auditierbar verfolgen?“
- Selective-Label-Analyse fragt: „Ist die Menge der beobachteten Labels repräsentativ bzw. korrigierbar?“

Beides muss getrennt gemessen werden.

### Machine Unlearning / Influence Echo

Unlearning-Forschung zeigt den allgemeinen Rand, dass das Entfernen einer Quelle nicht automatisch bedeutet, dass ihr Einfluss aus einem adaptiven Modell verschwunden ist. Für AgentZero wird daraus kein Anspruch, dieselben Algorithmen zu verwenden. Der nützliche Transfer ist der Falsifikator **Influence Echo**:

`source revoked -> dependent adaptive influence should be removed, compensated, quarantined or explicitly remain as unresolved debt`

## 7. Billigster neuer Discriminator: ADAPTIVE_EVIDENCE_DEBT_RECEIPT/v1

Kein neuer Produktmechanismus ist nötig, um zuerst zu messen.

Für jede aktive adaptive Policy-/Memory-Komponente erfassen:

- `adaptive_unit_id`
- `adaptive_unit_type`
- `current_generation`
- `source_receipt_ids[]`
- `source_episode_ids[]`
- `source_status[] = PRESENT | MAPPED | REVOKED | MISSING | AMBIGUOUS | ERROR`
- `derivation_receipt_id`
- `compaction_receipt_id`, falls verwendet
- `replayable = true|false|unknown`
- `behavioral_influence = measured|proxy|unknown`
- `debt_class`

Erste Tests ohne Mutation:

1. alle 20 Gen244-Retrieval-Feedback-Receipts nehmen;
2. ihre `retrieval_id` und `causal_id` in aktuellem DB-/Archiv-/Mappingraum auflösen;
3. abhängige Policy-Keys bestimmen;
4. jeden Pfad in CDC-Klasse einordnen;
5. `OACR` und ungewichtete `AED` nur dort berechnen, wo Nenner und Unit-Semantik tatsächlich definiert sind.

Das ist der momentan höchste Informationsgewinn, weil es die Gegenhypothese „nur Export-Sichtbarkeit“ direkt gegen echte Provenienzschuld trennt.

## 8. Späterer Revocation-/Influence-Echo-Falsifikator

Erst wenn ein append-only Feedback-Event-Ledger und explizite adaptive Ableitungen existieren:

1. einen bereits bewerteten, adaptiv wirksamen Source-Event in einer autorisierten isolierten Kopie als `REVOKED` markieren;
2. Current Policy vor und nach definierter Compensation/Rebuild erfassen;
3. alle abhängigen Units verfolgen;
4. prüfen, ob aktive Wirkung ohne gültigen Source-/Compensation-Receipt fortbesteht.

PASS:

- abhängiger Einfluss entfernt/kompensiert/reproduzierbar neu berechnet; oder
- Restwirkung explizit als unresolved debt quarantiniert.

FAIL:

- Source widerrufen/entfernt;
- adaptive Wirkung bleibt aktiv;
- keine adressierbare Derivation-/Compensation-Lineage erklärt sie.

Dieser Falsifikator ist **nur vorgeschlagen**; er wurde in diesem `go` nicht ausgeführt.

## 9. Forschungsstatus nach Fusion

- Gen244 persistierendes adaptives Retrievalkapital bei unvollständiger sichtbarer Episodenlineage: `MECHANISM_SUPPORTED_AT_OBSERVABLE_SURFACE`
- Root Cause `DELETED` vs `HIDDEN/MAPPED`: `UNRESOLVED`
- Gen245 Feedback-Erasure im Current-State: `MECHANISM_SUPPORTED`
- Human-Feedback bereits als adaptiver Reward aktiv: `NOT_PROVEN`
- Adaptive Evidence Debt als Messbegriff: `PROMOTED_TO_RESEARCH_METRIC_CANDIDATE`
- numerischer AgentZero-AED-Wert: `NOT_YET_MEASURABLE`
- Revocation/Influence Echo bei AgentZero: `NOT_TESTED`
- AgentZero-Gesamtqualität oder funktionales Bewusstsein: `NOT_CLAIMED`

## 10. Nächster maximaler Informationsgewinn

Nicht weitere Snapshot-Gesamtzahlen sammeln, sondern die **20 persistierenden Retrieval-Feedback-Receipts aus Gen244 vollständig in die aktuelle Live-DB/Archive/Mapping-Struktur auflösen**.

Das trennt zwei Welten:

- `VISIBLE LINEAGE LOSS ONLY` — Quellen existieren/mappen noch, AED sinkt;
- `TRUE UNMAPPED ADAPTIVE CAPITAL` — wirksamer Lernzustand besitzt orphaned source lineage, AED wird empirisch real.

Erst danach lohnt es sich, AED mit behavioraler Einflussstärke oder Human-Feedback-Selection-Bias zu koppeln.

## Externe methodische Anker

- W3C PROV-DM / PROV Constraints — Provenienz als Entities, Activities, Agents, Derivationen plus Validitätsbedingungen.
- Martin Fowler, Event Sourcing — Current-State getrennt von vollständiger Ereignisfolge.
- Lakkaraju et al., KDD 2017, *The Selective Labels Problem* — selektiv beobachtete Outcomes/Labels sind keine zufällige Stichprobe.
- Chourasia & Shah, 2022, *Forget Unlearning: Towards True Data-Deletion in Machine Learning* — Entfernen von Daten und Entfernen ihres Modell-Einflusses sind unterschiedliche Anforderungen.
- Ding, Huang & Dong, 2026, *When Unlearning Fails: Reliable Data Deletion under Post-Training in Agent Networks* — aktuelle externe Hypothesenquelle für nachlaufende Einfluss-Echos in weiterlernenden Agentennetzen; hier nur als Gegenrealitäts-/Falsifikator-Inspiration verwendet, nicht als AgentZero-Evidenz.