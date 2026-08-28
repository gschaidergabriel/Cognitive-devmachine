# Generation 244 — Evidenz-Epochengrenze und persistierendes Lernen ohne sichtbare Episodenlinie

## BIND

- Research/Main: `36b502cf99fa9037da0a4a3da9e950ba21440f9d`
- Tree: `9f31e9eb3e640079e576719385b415eaa0004a6e`
- AgentZero Export: Generation `244`
- Exportzeit: `2026-08-21T13:07:17Z`
- direkter Test-Receipt: `1052 gruen / 1 rot`
- persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Diese Analyse erweitert die bereits gebundene Gen241-Evidence-Spine-Kollapsanalyse und die Gen243-Teilwiederkehr. Sie behauptet keine neue Root Cause, sondern bindet einen neuen Zeitreihenmechanismus.

## 1. Neue Beobachtung: exakte Evidenz-Epochengrenze

Unmittelbar vor dem Gen241-Kollaps waren die drei zentralen Episodenzaehler gleich:

- causal episodes: `568`
- workspace episodes: `568`
- retrieval episodes: `568`

Der naechste gebundene Gen241-Stand zeigte:

- causal: `568`
- workspace: `0`
- retrieval: `0`
- Andreas-Chat: `0`
- Gabriel-Chat: `0`

Gen243 und Gen244 zeigen anschliessend:

- causal: `582`
- workspace: `14`
- retrieval: `14`
- Andreas-Chat: `28`
- Gabriel-Chat: `0`

Damit gilt auf Zaehlerniveau exakt:

`582 causal = 568 vor der Grenze erhaltene causal + 14 neue causal`

und gleichzeitig:

`workspace = retrieval = 14`

Die neue Workspace-/Retrieval-Spur entspricht numerisch exakt nur dem post-collapse Zuwachs der Causal-Spur. Die alten `568` Causal-Episoden bleiben sichtbar, waehrend die zuvor gleichzahligen Workspace-/Retrieval-Episoden im aktuellen Export nicht wieder auftauchen.

Status: `REPLICATED_TIME_SERIES_PATTERN`.

## 2. Session-Neustart als triviale Erklaerung wird deutlich geschwaecht

Die vier Session-IDs bleiben ueber Gen234, Gen241 und Gen243 identisch:

- `session:gabriel`
- `session:andreas`
- `session:andreas:2`
- `session:gabriel:2`

Auch ihre `created_at`-Werte bleiben erhalten; lediglich Generation/updated_at laufen weiter.

Damit passt ein einfacher "neue Sessions, deshalb leere Historie"-Mechanismus schlecht zu den Daten. Die Identitaetszeiger ueberleben die Grenze, waehrend ausgewaehlte Evidenztabellen ihre sichtbare Historie verlieren.

Status: Session-Fork/Session-Replacement als Hauptursache `DOWNWEIGHTED`, nicht vollstaendig falsifiziert.

## 3. Haupt-Hypothese und Gegenhypothese

### H1 — selektiver destruktiver Reset / neue Evidenz-Epoche

Turn-/Workspace-/Retrieval-Historie wurde an der Grenze geloescht, geleert, ersetzt oder auf neue leere Tabellen/DB-Bereiche umgeschaltet; Causal-, Session-, Durable-Memory- und andere Zustaende blieben erhalten. Danach funktionieren neue Turnketten wieder normal und akkumulieren ab Null.

Vorhersage:
- bekannte pre-collapse Workspace-/Retrieval-IDs sind in der Live-DB nicht mehr direkt auffindbar;
- keine verlustfreie Archiv-/Mapping-Tabelle verbindet sie mit Ersatzdaten;
- aktuelle Episoden beginnen zeitlich nach der Grenze und gehoeren zur erhaltenen Sessionidentitaet.

### H2 — Sichtbarkeits-/Query-/Export-Epochenfilter

Die historischen Zeilen existieren noch, aber Runtime-/Exportabfragen fuer Chat, Workspace und Retrieval erhielten an der Grenze einen Filter, View-, Schema- oder DB-Pfadwechsel. Causal wird weiterhin global exportiert.

Vorhersage:
- bekannte pre-collapse IDs sind in der Live-DB oder einer Alt-/Archivstruktur vorhanden;
- direkte SQL-Abfrage findet mehr Zeilen als die aktuelle Exportoberflaeche;
- Query-/View-/DB-Pfad-Diff erklaert die exakt abgrenzbare Sichtbarkeit.

### H3 — Privacy-Redaction nur im GitHub-Export

Diese Erklaerung ist deutlich schwaecher, weil der bereits gebundene Gen241-Ziel-/Runtime-Messpfad ebenfalls `keine Historie`, 0 Turns und 0 Workspace-Episoden meldete. Sie bleibt formal offen, falls jener Messpfad dieselbe gefilterte Quelle verwendet.

## 4. Neuer Meta-Learning-/Retrieval-Befund: Policy ueberlebt ihre sichtbare Episode-Lineage

Vor Gen241 und danach bleiben erhalten:

- `retrieval_entrypoint_policy`: `27` Zeilen
- `retrieval_feedback`: `20` Zeilen
- `retrieval_policy_state`: `1` Zeile

Die aktuellen 14 Retrieval-Episoden stammen ausschliesslich aus Generation `241/242`.

Die 20 persistierenden Feedback-Receipts referenzieren dagegen Retrieval-IDs aus deutlich aelteren Generationen `80..145` und tragen positiven wie negativen Credit. Diese historischen Retrieval-Episoden sind in der aktuellen `retrieval_episodes`-Oberflaeche nicht mehr sichtbar, waehrend das daraus entstandene adaptive Kapital/Policy weiterhin vorhanden ist.

Das ist kein Beweis, dass Lernen falsch ist. Es ist jedoch ein Audit-/Replay-Bruch, solange kein explizites Archiv-/Compaction-Mapping existiert:

**learned state remains durable while the observable source-episode lineage is incomplete.**

Fuer ein selbstadaptives Retrievalsystem ist das wesentlich: ohne erhaltene oder explizit verdichtete Provenienz koennen Reward-Credit, Fehlanpassungen, Rollback und spaetere Gegenbeweise nicht vollstaendig rekonstruiert werden.

Status: `MECHANISM_SUPPORTED` fuer die beobachtbare Lineage-Luecke; Ursache/Absicht `UNRESOLVED`.

## 5. Billigster diskriminierender Falsifikator

### `EVIDENCE_SPINE_RETENTION_RECEIPT/v2`

Bestehenden v1-Plan um eine ID- und Lineage-Pruefung erweitern:

1. aus einem pre-collapse Export je 20 bekannte IDs ziehen aus
   - turns,
   - workspace_episodes,
   - retrieval_episodes,
   - causal_episodes;
2. dieselben IDs direkt in der aktuellen Live-DB suchen;
3. zusaetzlich alle Views, Archive, Compaction-/Tombstone-/Replacement-Tabellen und DB-Pfade durchsuchen;
4. fuer jeden Datensatz exakt klassifizieren:
   - `PRESENT_DIRECT`,
   - `PRESENT_BUT_EXPORT_HIDDEN`,
   - `MOVED_WITH_MAPPING`,
   - `DELETED_WITH_RECEIPT`,
   - `DELETED_UNMAPPED`,
   - `UNKNOWN`;
5. DB-Inode/File-Digest, `PRAGMA user_version`, WAL-/Checkpoint-Identitaet, min/max IDs/Timestamps und Query-/View-Digests binden;
6. mindestens 20 erhaltene historische `causal_id` gegen Turn/Workspace/Retrieval-Provenienz joinen und `causal_orphan_rate` messen.

Harte Invariante:

`retained causal or learned policy state => source evidence remains addressable OR an explicit typed loss-preserving provenance mapping exists`

Ein blosses "komprimiert" ohne Mapping reicht nicht.

### `RETRIEVAL_LEARNING_LINEAGE_RECEIPT/v1`

Fuer alle 20 aktuellen Feedback-Receipts:

- `receipt_id`
- `retrieval_id`
- `causal_id`
- Generation
- Credit/Signal
- Existenz des Retrieval-Ursprungs oder archivalische Replacement-ID
- Policy-Keys, die daraus aktualisiert wurden

messen. Zielwert:

`unmapped_feedback_source_rate == 0`

## 6. Weitere Gen244-Deltas

### Tests

Die Suite waechst von Gen234 `976/1` auf Gen244 `1052/1`, waehrend derselbe Claude-Code-Adapter-Test rot bleibt. Das verstaerkt die Langzeit-Replikation dieses Boundary-Frontiers, liefert aber ohne Exact-Source-/Environment-Receipt weiterhin keine Root Cause.

### Wegehierarchie

Die Wegehierarchie bleibt ueber viele Generationen unter der kanonisierten `0.20`-Schwelle: Gen159/174 ca. `0.136`, Gen244 `0.139`. Dies ist eine weitere longitudinale Replikation von "keine starke Konzentration", kein neuer Mechanismusnachweis. F94 darf daraus weiterhin keinen Hierarchie-PASS erhalten.

### Gen243 -> Gen244

Zwischen Gen243 und Gen244 wachsen Produkt-/Autonomie-/Effect-nahe Source-Artefakte und Testabdeckung; Chat-, Workspace-, Retrieval- und Causal-Zaehler bleiben jedoch unveraendert bei `28 / 14 / 14 / 582`. Deshalb bekommt dieser Source-Delta keinen Live-Behavior-Credit aus Gen244. Die einfachste Erklaerung ist fehlender neuer User-Turn-Verkehr; ein Lifecycle-Ausfall wird daraus nicht abgeleitet.

## 7. Fusion

### Beobachtung

Die Evidenzspine zeigt eine scharfe Epochengrenze: alte Causal-Spuren ueberleben, alte Workspace-/Retrieval-/Chat-Historie wird nicht mehr sichtbar, und neue vollstaendige Episoden akkumulieren danach wieder ab Null.

### Ableitung

Das Muster ist selektiv, nicht global. Sessionidentitaeten, Causal-Historie, Durable Memory, Retrieval-Feedback und adaptive Policy ueberleben. Daher ist ein kompletter DB-/Identitaetsverlust unwahrscheinlicher als selektive Retention/Deletion/Query-/Path-Migration.

### Staerkste Gegenhypothese

Historische Daten sind nicht geloescht, sondern durch eine neue View-/Query-/DB-Pfad-Semantik verborgen. Diese Gegenhypothese ist mit den bisherigen Exporten nicht entscheidbar.

### Neues Forschungsresultat

Die kritischste Folge ist nicht nur verlorene Chat-Historie, sondern **persistierendes adaptives Retrievalkapital ohne aktuell sichtbare vollstaendige Trainings-/Feedback-Episodenlinie**. Das betrifft Reproduzierbarkeit, Credit-Audit, Rollback und spaetere Falsifikation.

### Promotionsstatus

- Evidence-Epochengrenze im Exportzeitstrahl: `MECHANISM_SUPPORTED`
- Session-Replacement als triviale Ursache: `DOWNWEIGHTED`
- destruktive Loeschung: `RETAINED_HYPOTHESIS`
- Query-/Visibility-Shift: `RETAINED_COUNTERHYPOTHESIS`
- historische Wiederherstellung: `NOT_PROVEN`
- Retrieval-Learning-Lineage voll auditierbar: `NOT_PROVEN`
- Whole AgentZero / funktionales Bewusstsein / Gesamtacceptance: `NOT CLAIMED`

## 8. Naechster maximaler Informationsgewinn

Nicht weiter anhand von Gesamtzaehlern spekulieren. Der naechste Run soll zuerst bekannte pre-collapse IDs direkt in der Live-DB suchen und `causal_orphan_rate` plus `unmapped_feedback_source_rate` messen. Ein einziger solcher Receipt trennt "wirklich geloescht" von "nur unsichtbar" wesentlich staerker als weitere Snapshot-Zaehler.
