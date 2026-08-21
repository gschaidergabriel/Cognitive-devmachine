# Generation 245 — Retrieval-Feedback Surface-Lineage Receipt

## BIND

- Basis-`main`: `11c29d3620d35c4b8d4113a7abed76ff274b14e0`
- AgentZero-Voll-Export: Generation `245`, erzeugt `2026-08-21T14:07:17Z`
- Quellen:
  - `agentZero/abruf/retrieval_feedback.jsonl` — 20 persistente Feedback-Receipts
  - `agentZero/abruf/retrieval_episodes.jsonl` — 15 aktuell sichtbare Retrieval-Episoden
  - `agentZero/kognition/causal_episodes.jsonl` — 583 aktuell sichtbare Causal-Episoden
- Untersuchung: read-only ID-Joins auf der GitHub-Exportoberflaeche
- keine Live-DB-Abfrage; keine Produktmutation; kein ungewöhnliches Experiment

## 1. Retrieval-Source-Messung

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

## 2. Causal Counter-Join

Dieselben 20 Feedback-Receipts enthalten jeweils eine `causal_id`. Alle 20 IDs wurden gegen den aktuellen `causal_episodes`-Export geprueft.

### Ergebnis

- `feedback_receipts_with_visible_causal_id = 20`
- `feedback_receipts_without_visible_causal_id = 0`
- `feedback_causal_surface_match_rate = 20 / 20 = 1.0`
- `retrieval_vs_causal_visibility_gap = 1.0 - 0.0 = 1.0` bzw. **100 Prozentpunkte**

Damit gilt fuer exakt dieselbe persistierende Feedback-Menge:

`causal anchor visible = 20/20`

`retrieval origin visible = 0/20`

Status: `SELECTIVE_LINEAGE_RETENTION_REPLICATED_BY_DIRECT_ID_JOIN`.

## 3. Was jetzt staerker belegt ist

Gen244 hatte bereits aus Generationen und Zaehlern geschlossen, dass persistierendes Retrieval-Lernkapital seine alten sichtbaren Retrieval-Episoden ueberlebt, waehrend Causal-Historie erhalten bleibt.

Der neue Receipt ersetzt den reinen Zaehlervergleich durch zwei direkte ID-Joins:

> **Keines der 20 aktuell persistierenden Retrieval-Feedback-Receipts kann auf der aktuellen Exportoberflaeche direkt zu seiner `retrieval_id`-Quelle zurueckgejoint werden, aber alle 20 koennen weiterhin zu ihrem `causal_id`-Anker gejoint werden.**

Damit wird ein globaler Totalverlust als triviale Erklaerung deutlich geschwaecht. Die sichtbare Epochengrenze ist selektiv nach Evidenzart.

## 4. Was NICHT belegt ist

Dieser Receipt darf nicht umgedeutet werden zu:

- `20 Retrieval-Quellen sind physisch geloescht`;
- `Live-DB hat keine alten Retrieval-Episoden`;
- `Compaction-/Archiv-Mapping existiert nicht`;
- `adaptive Policy ist falsch`;
- `OACR = 100%` fuer aktive Policy-Units;
- `AgentZero lernt irreversibel falsch`.

Die aktuelle Exportoberflaeche ist nur eine Beobachtungsschicht. Die staerkste Gegenhypothese bleibt:

`OLD_RETRIEVAL_SOURCES_EXIST_IN_LIVE_DB_OR_ARCHIVE_AND_ARE_ONLY_EXPORT_HIDDEN`.

Der 20/20-Causal-Gegenjoin macht diese Gegenhypothese sogar praeziser: Falls eine Migration/Retention-Regel existiert, behandelt sie Retrieval- und Causal-Evidenz unterschiedlich.

## 5. Beziehung zu Adaptive Evidence Debt

Der Receipt definiert noch keinen numerischen AED/OACR, weil die 20 Feedback-Receipts keine vollstaendige Definition aller **aktiven adaptiven Units** sind.

Er liefert aber harte Eingangswerte fuer `ADAPTIVE_EVIDENCE_DEBT_RECEIPT/v1`:

- `retrieval_source_status_at_export_surface = MISSING` fuer 20/20 Urspruenge;
- `causal_anchor_status_at_export_surface = PRESENT` fuer 20/20 Receipts.

Die Retrieval-Klasse muss bei einer spaeteren Live-DB-/Archivsuche entweder hochgestuft werden zu:

- `PRESENT_DIRECT`
- `SOURCE_HIDDEN_BUT_MAPPED`
- `BOUND_VIA_COMPACTION_RECEIPT`

oder bestaetigt werden als:

- `SOURCE_MISSING`
- `DELETED_UNMAPPED`
- `AMBIGUOUS`
- `ERROR`.

## 6. Staerkster naechster Falsifikator

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

Zusaetzlich sollte die Retention-Regel selbst gesucht werden, weil die 20/20-vs-0/20-Asymmetrie eine evidenztyp-spezifische Grenze nahelegt.

## 7. Promotionsstatus

- Feedback-Receipts persistent: `OBSERVED`
- aktuelle Retrieval-Episoden: `OBSERVED`
- direkter Retrieval-ID-Join auf Exportoberflaeche 0/20: `OBSERVED_AT_EXACT_EXPORT_SURFACE`
- direkter Causal-ID-Gegenjoin 20/20: `OBSERVED_AT_EXACT_EXPORT_SURFACE`
- selektive Retrieval-vs-Causal-Lineage-Asymmetrie: `MECHANISM_SUPPORTED_AT_EXPORT_SURFACE`
- sichtbare Retrieval-Source-Lineage-Gap-Rate 100% fuer diese 20 Receipts: `MEASURED_AT_EXPORT_SURFACE`
- physische Loeschung der Retrieval-Ursprungs-Episoden: `NOT_PROVEN`
- vorhandenes Archiv/Mapping: `UNRESOLVED`
- numerischer AgentZero-AED/OACR: `NOT_YET_MEASURABLE`

## 8. Fusion

Der bisherige Gen244-Befund wird praezisiert:

`adaptive retrieval feedback persists; its 20/20 causal anchors remain directly visible, while 0/20 referenced retrieval origins are directly addressable on the current export surface`.

Das ist ein konkreter, falsifizierbarer Receipt fuer eine selektive Evidence-Epoch-Grenze. Der naechste Informationsgewinn liegt nicht in weiteren Snapshot-Gesamtzaehlern, sondern im direkten Live-/Archiv-ID-Resolve derselben 20 Retrieval-Quellen und der Suche nach der evidenztyp-spezifischen Retention-/Migration-Regel.