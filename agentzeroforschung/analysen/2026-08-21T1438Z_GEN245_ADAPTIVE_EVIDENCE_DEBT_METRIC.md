# Generation 245 — Adaptive Evidence Debt als querschnittliche Lernprovenienz-Metrik

## BIND

- Research-`main` unmittelbar vor Persistierung: `56f35dbcda6c33be23714f172c3c7f212a1863b7`
- letzter gebundener AgentZero-Voll-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- AgentZero-Generation: `245`
- direkte interne Evidenz:
  - Gen244 Evidence-Epoch-Boundary: persistierendes Retrieval-Lernkapital bei unvollstaendig sichtbarer Episodenlineage
  - Gen245 Human-Feedback-Erasure: Current-State kann reale Rating-Ereignisse verlieren
  - Gen245 Revocable-Feedback-Arbeit auf aktuellem `main`: Credit muss widerrufbar/komponentengebunden behandelt werden

Diese Notiz dupliziert **nicht** die Revocable-Feedback-State-Machine. Sie fuehrt eine breitere Metrik fuer alle adaptiven AgentZero-Subsysteme ein: **Adaptive Evidence Debt (AED)**.

## 1. Problem

Gen244 zeigt einen strukturell wichtigeren Rand als bloss verlorene Chat-Historie:

- `retrieval_entrypoint_policy = 27` persistiert;
- `retrieval_feedback = 20` persistiert;
- `retrieval_policy_state = 1` persistiert;
- die sichtbaren aktuellen Retrieval-Episoden beginnen erst in der neuen Evidence-Epoche;
- aeltere Feedback-Receipts verweisen auf Retrieval-IDs aus Generationen `80..145`, deren Ursprungs-Episoden in der aktuellen Retrieval-Oberflaeche nicht sichtbar sind.

Damit existiert beobachtbar:

`adaptive state present + source episode lineage incomplete/hidden`

Noch **nicht** entschieden ist, ob die Ursprungsdaten wirklich geloescht, nur durch Query/Path verborgen oder verlustbewahrend gemappt/komprimiert wurden.

## 2. Definition

Eine aktive adaptive Zustandskomponente traegt **Evidence Debt**, wenn ihr wirksamer Credit/Debit nicht vollstaendig auf weiterhin gueltig gebundene Evidenzquellen zurueckgefuehrt werden kann.

Eine Quelle gilt mindestens als `VALID_BOUND`, wenn:

1. Source-ID eindeutig adressierbar ist;
2. Turn/Episode/Outcome-Bezug eindeutig ist;
3. Generation/Version/Provenienz gebunden ist;
4. Widerruf, Tombstone oder Invalidierung explizit typisiert ist;
5. `source -> adaptive update` reproduzierbar ist oder ein expliziter Derivation-/Compaction-Receipt existiert;
6. `ABSENT`, `ERROR`, `UNKNOWN` und `UNMEASURED` nicht kollabieren.

AED ist kein Qualitaets- und kein Bewusstseinsmass. Es misst die Auditierbarkeit und spaetere Falsifizierbarkeit von adaptivem Einfluss.

## 3. Minimalmetriken

### Adaptive Evidence Coverage

Wenn eine saubere adaptive Unit existiert, etwa Policy-Key oder Entry-Point-Prior:

`AEC = fully_bound_active_adaptive_units / all_active_adaptive_units`

`AED = 1 - AEC`

Ein numerischer AED darf **nicht** berichtet werden, solange der Nenner oder die Unit-Semantik unklar ist.

### Orphan Adaptive Capital Rate

`OACR = active_adaptive_units_without_addressable_source_lineage / all_active_adaptive_units`

Gen244 motiviert OACR, liefert aber noch keinen belastbaren Wert, weil `nicht sichtbar` nicht gleich `unmapped/deleted` ist.

### Causal Derivation Completeness

Jeder adaptive Update-Pfad wird klassifiziert als:

- `FULLY_BOUND`
- `BOUND_VIA_COMPACTION_RECEIPT`
- `SOURCE_HIDDEN_BUT_MAPPED`
- `SOURCE_REVOKED_COMPENSATED`
- `SOURCE_REVOKED_UNCOMPENSATED`
- `SOURCE_MISSING`
- `AMBIGUOUS`
- `ERROR`

Nur die ersten vier Klassen gelten als provenance-komplett.

## 4. Haupt-Hypothese

**H-AED:** Eine zentrale Langzeitgefahr selbstadaptiver Agenten ist nicht nur falsches Lernen, sondern **nicht mehr sauber falsifizierbares Lernen**: adaptiver Einfluss bleibt aktiv, waehrend die Evidenzlinie so weit erodiert, dass Gegenbeweise, Widerrufe, Rollback oder Replay den Ursprung nicht mehr sicher erreichen.

### Staerkste Gegenhypothese

Die Gen244-Luecke ist nur eine Export-/Query-Sichtbarkeitsluecke. Die alten Episoden existieren in Live-DB, Archiv oder Compaction-Mapping vollstaendig weiter.

Wenn diese Gegenhypothese stimmt, sinkt der reale AED stark oder auf null fuer die betroffenen Units.

## 5. Billigster diskriminierender Receipt

### `ADAPTIVE_EVIDENCE_DEBT_RECEIPT/v1`

Ohne Produktmutation zuerst die 20 persistierenden Gen244-Retrieval-Feedback-Receipts pruefen.

Pro Receipt/abhaengiger adaptiver Unit erfassen:

- `adaptive_unit_id`
- `adaptive_unit_type`
- `source_receipt_id`
- `retrieval_id`
- `causal_id`
- `source_status = PRESENT | MAPPED | REVOKED | MISSING | AMBIGUOUS | ERROR`
- `derivation_receipt_id`
- `compaction_receipt_id`, falls vorhanden
- `replayable = true | false | unknown`
- `behavioral_influence = measured | proxy | unknown`
- CDC-Klasse

Dann:

1. `retrieval_id` und `causal_id` direkt in aktueller Live-DB suchen;
2. Views, Archive, Replacement-/Compaction-/Tombstone-Strukturen und DB-Pfade pruefen;
3. abhaengige Policy-Keys bestimmen;
4. jeden Pfad klassifizieren;
5. AED/OACR nur berechnen, wenn Nenner und Unit-Semantik empirisch definiert sind.

## 6. Fusion mit Gen245 Human Feedback

Die neue Revocable-Feedback-Arbeit auf `main` beantwortet eine Teilfrage: ein Rating kann spaet eintreffen, geaendert/entfernt werden und darf nicht naiv irreversiblen komponentenagnostischen Credit erzeugen.

AED stellt die orthogonale Auditfrage:

> Wenn irgendein Feedback-, Retrieval-, Outcome- oder Methodenereignis adaptiven Zustand veraendert hat: bleibt die **Ableitung dieses Einflusses** spaeter noch vollstaendig adressierbar?

Ein Event-Ledger allein ist dafuer notwendig, aber nicht hinreichend. Es muss auch `event -> adaptive update -> current adaptive state` gebunden sein.

## 7. Externe methodische Fusion

- W3C PROV motiviert die Trennung von Source-Entity, Learning-Activity und daraus abgeleiteter Entity samt Derivationsbezug.
- Event Sourcing motiviert die Trennung von materialisiertem Current-State und Ereignisgeschichte.
- Selective-Labels-Forschung warnt separat davor, freiwilliges Human-Feedback als unverzerrte globale Qualitaetsstichprobe zu lesen.

Damit sind zwei Achsen strikt zu trennen:

1. **Provenienz/AED:** Kann adaptiver Einfluss kausal und revisionsfest auf seine Quellen zurueckgefuehrt werden?
2. **Selection Bias:** Ist die beobachtete Feedbackmenge ueberhaupt repraesentativ oder korrigierbar?

Perfekte Provenienz beseitigt Selection Bias nicht; Propensity-Korrektur repariert fehlende Lineage nicht.

## 8. Promotionsstatus

- persistierendes Retrieval-Lernkapital bei unvollstaendig sichtbarer Ursprungslineage: `MECHANISM_SUPPORTED_AT_OBSERVABLE_SURFACE`
- Root Cause `DELETED` vs `HIDDEN/MAPPED`: `UNRESOLVED`
- Adaptive Evidence Debt als Forschungsmetrik: `PROMOTED_TO_METRIC_CANDIDATE`
- numerischer AgentZero-AED/OACR: `NOT_YET_MEASURABLE`
- Human Feedback bereits als adaptiver Reward aktiv: `NOT_PROVEN`
- AgentZero-Gesamtqualitaet / funktionales Bewusstsein: `NOT_CLAIMED`

## 9. Naechster maximaler Informationsgewinn

Die 20 Gen244-Retrieval-Feedback-Receipts muessen gegen aktuelle Live-DB, Archive und Mapping-Strukturen vollstaendig aufgeloest werden.

Dieser eine Receipt trennt:

- `VISIBLE_LINEAGE_LOSS_ONLY` — Quellen existieren oder sind verlustbewahrend gemappt;
- `TRUE_UNMAPPED_ADAPTIVE_CAPITAL` — aktiver Lernzustand besitzt orphaned source lineage.

Erst danach ist ein numerischer AED/OACR oder eine belastbare Aussage ueber Revocation-/Influence-Echo gerechtfertigt.