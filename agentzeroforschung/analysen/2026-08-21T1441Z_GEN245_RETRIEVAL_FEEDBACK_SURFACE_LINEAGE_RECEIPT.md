# Generation 245 — Retrieval-Feedback Surface-Lineage Receipt

## BIND

- Basis-`main`: `11c29d3620d35c4b8d4113a7abed76ff274b14e0`
- AgentZero-Voll-Export: Generation `245`, erzeugt `2026-08-21T14:07:17Z`
- Quellen:
  - `agentZero/abruf/retrieval_feedback.jsonl` — 20 persistente Feedback-Receipts
  - `agentZero/abruf/retrieval_episodes.jsonl` — 15 aktuell sichtbare Retrieval-Episoden
- Untersuchung: read-only ID-Join auf der GitHub-Exportoberflaeche
- keine Live-DB-Abfrage; keine Produktmutation; kein ungewöhnliches Experiment

## 1. Messung

Alle `retrieval_id` aus den 20 persistierenden Feedback-Receipts wurden gegen alle 15 im aktuellen Export sichtbaren `retrieval_id` verglichen.

Feedback-Receipts stammen aus Generationen:

`80, 83, 91, 92, 98, 116, 117, 118, 129, 130, 134, 142, 145`

Die 15 aktuell sichtbaren Retrieval-Episoden stammen aus:

- Generation 241: 6 Episoden
- Generation 242: 8 Episoden
- Generation 245: 1 Episode

Der direkte `retrieval_id`-Schnitt ist leer.

### Ergebnis

- `feedback_receipts_total = 20`
- `visible_retrieval_episodes_total = 15`
- `feedback_receipts_with_visible_source_retrieval_id = 0`
- `feedback_receipts_without_visible_source_retrieval_id = 20`
- `feedback_source_surface_match_rate = 0 / 20 = 0.0`
- `feedback_source_surface_gap_rate = 20 / 20 = 1.0`

Status: `OBSERVED_AT_EXACT_EXPORT_SURFACE`.

## 2. Was jetzt staerker belegt ist

Gen244 hatte bereits aus Generationen und Zaehlern geschlossen, dass persistierendes Retrieval-Lernkapital seine alten sichtbaren Episoden ueberlebt.

Der neue Receipt ersetzt den reinen Zaehlervergleich durch einen direkten ID-Join:

> **Keines der 20 aktuell persistierenden Retrieval-Feedback-Receipts kann auf der aktuellen Exportoberflaeche direkt zu seiner `retrieval_id`-Quelle zurueckgejoint werden.**

Damit ist `VISIBLE_RETRIEVAL_FEEDBACK_SOURCE_LINEAGE_GAP` auf der aktuellen Exportoberflaeche nicht nur plausibel, sondern direkt gemessen.

## 3. Was NICHT belegt ist

Dieser Receipt darf nicht umgedeutet werden zu:

- `20 Quellen sind physisch geloescht`;
- `Live-DB hat keine alten Retrieval-Episoden`;
- `Compaction-/Archiv-Mapping existiert nicht`;
- `adaptive Policy ist falsch`;
- `OACR = 100%` fuer aktive Policy-Units;
- `AgentZero lernt irreversibel falsch`.

Die aktuelle Exportoberflaeche ist nur eine Beobachtungsschicht. Die staerkste Gegenhypothese bleibt:

`OLD_RETRIEVAL_SOURCES_EXIST_IN_LIVE_DB_OR_ARCHIVE_AND_ARE_ONLY_EXPORT_HIDDEN`.

## 4. Beziehung zu Adaptive Evidence Debt

Der Receipt definiert noch keinen numerischen AED/OACR, weil die 20 Feedback-Receipts keine vollstaendige Definition aller **aktiven adaptiven Units** sind.

Er liefert aber einen harten Eingangswert fuer `ADAPTIVE_EVIDENCE_DEBT_RECEIPT/v1`:

`source_status_at_export_surface = MISSING` fuer 20/20 Retrieval-Feedback-Urspruenge.

Diese Klasse muss bei einer spaeteren Live-DB-/Archivsuche entweder hochgestuft werden zu:

- `PRESENT_DIRECT`
- `SOURCE_HIDDEN_BUT_MAPPED`
- `BOUND_VIA_COMPACTION_RECEIPT`

oder bestaetigt werden als:

- `SOURCE_MISSING`
- `DELETED_UNMAPPED`
- `AMBIGUOUS`
- `ERROR`.

## 5. Staerkster naechster Falsifikator

Fuer exakt diese 20 `retrieval_id` in der aktuellen Live-DB und allen expliziten Archiv-/Replacement-/Compaction-Strukturen suchen.

Pro ID ausgeben:

- `retrieval_id`
- `causal_id`
- `generation`
- `direct_live_match`
- `archive_match`
- `replacement_id`
- `compaction_receipt_id`
- `dependent_policy_keys`
- `classification`

Kanonische Klassen:

`PRESENT_DIRECT | PRESENT_BUT_EXPORT_HIDDEN | MOVED_WITH_MAPPING | DELETED_WITH_RECEIPT | DELETED_UNMAPPED | UNKNOWN | ERROR`

Der Test trennt unmittelbar:

- **Export-Sichtbarkeitsproblem** von
- **echter ungemappter Lernprovenienzschuld**.

## 6. Promotionsstatus

- Feedback-Receipts persistent: `OBSERVED`
- aktuelle Retrieval-Episoden: `OBSERVED`
- direkter ID-Join auf Exportoberflaeche 0/20: `OBSERVED_AT_EXACT_EXPORT_SURFACE`
- sichtbare Source-Lineage-Gap-Rate 100% fuer diese 20 Receipts: `MEASURED_AT_EXPORT_SURFACE`
- physische Loeschung der Ursprungs-Episoden: `NOT_PROVEN`
- vorhandenes Archiv/Mapping: `UNRESOLVED`
- numerischer AgentZero-AED/OACR: `NOT_YET_MEASURABLE`

## 7. Fusion

Der bisherige Gen244-Befund wird praezisiert:

`learned/adaptive retrieval feedback persists while 20/20 referenced retrieval origins are not directly addressable on the current export surface`.

Das ist nun ein konkreter, falsifizierbarer Receipt statt nur eine qualitative Provenienzwarnung. Der naechste Informationsgewinn liegt nicht in weiteren Snapshots, sondern im direkten Live-/Archiv-ID-Resolve derselben 20 Quellen.