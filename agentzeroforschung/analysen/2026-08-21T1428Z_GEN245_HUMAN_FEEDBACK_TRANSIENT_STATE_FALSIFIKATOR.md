# Generation 245 — Human-Feedback: transienter Current-State-Falsifikator

## BIND

- Research-`main` vor dieser Persistierung: `2b7360bb2682131dfb0121c25c1c03e808033df0`
- neuester AgentZero-Export bleibt: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- AgentZero-Generation: `245`
- AgentZero-Exportzeit: `2026-08-21T14:07:17Z`
- letzter vollstaendiger Forschungsbericht: `2026-08-21T1422Z_GEN245_TUNNEL_PROVENIENZ_UND_HUMAN_FEEDBACK.md`

Seit diesem Bericht ist kein neuer AgentZero-Messstand eingetroffen. Der neue auswertbare Delta liegt im separat getakteten Human-Feedback-Export.

## OBSERVATION

Die Git-Historie zeigt fuer exakt dieselbe Rating-Zeile drei aufeinanderfolgende Current-State-Zustaende:

1. `2026-08-21T14:18:46Z`: `0 Bewertungen`.
2. `2026-08-21T14:24:02Z`: `1 Bewertungen`, `0 hoch / 1 runter`; eine konkrete, turn- und sessiongebundene Zeile mit `wert=-1` wurde exportiert.
3. `2026-08-21T14:24:55Z`: `0 Bewertungen`; exakt diese Zeile wurde wieder aus `bewertungen.jsonl` entfernt.

Der in der Zeile gespeicherte Bewertungszeitpunkt ist `2026-08-21T14:23:39.012848Z`. Unter der Annahme gleicher UTC-Clock wurde der negative Zustand somit rund 23 Sekunden nach Setzen erstmals exportiert und war spaetestens rund 76 Sekunden nach Setzen wieder aus dem Current-State-Export verschwunden.

Aktuelles `bewertungen.jsonl.meta.json` bestaetigt erneut `zeilen=0`, `hoch=0`, `runter=0` und deklariert den Export explizit als Vollabbild, nicht Append-Log.

## WAS DADURCH NEU GELERNT WURDE

Der Gen245-Bericht hatte den Verlust historischer Feedbackaenderungen aus Source-Semantik abgeleitet. Dieser Mechanismus ist nun erstmals an realem Betrieb beobachtet:

`SET(-1) -> Current-State sichtbar -> REMOVE -> Current-State leer`

Damit wird die Aussage hochgestuft von reinem Source-Risiko zu:

`CURRENT_STATE_FEEDBACK_HISTORY_LOSS = OBSERVED_AT_SNAPSHOT_TRANSITION`

Gleichzeitig ist `reale Human-Feedback-Daten = NO_DATA_YET` fuer die Forschungshistorie nicht mehr korrekt. Praeziser ist:

- aktueller Materialized State: `NO_CURRENT_RATINGS`;
- mindestens ein realer negativer Rating-Zustand: `OBSERVED_TRANSIENT_EVENT`;
- dauerhafte kanonische Event-Lineage: `NOT_PRESENT / NOT_PROVEN`.

Aus einem einzelnen Daumen-runter folgt keinerlei Antwortqualitaets-, Modellqualitaets- oder Nutzerzufriedenheitsclaim.

## HYPOTHESE H1 — Runtime-Historie geht verloren

**Mechanismus:** `eos_bewertungen` ist Materialized Current State. Aendern/Entfernen ersetzt den Zustand. Ein spaeterer Leser der UnifiedDB bzw. des aktuellen Exports kann das fruehere Ereignis nicht rekonstruieren.

**Vorhersage:** Nach Entfernung steht in der aktuellen Tabelle/Exportdatei kein Beleg mehr, dass die Bewertung existiert hat.

**Beobachtung:** erfuellt.

Status: `MECHANISM_SUPPORTED` fuer den beobachteten SET/REMOVE-Pfad.

## GEGENHYPOTHESE H2 — Git-Historie reicht als Event-Ledger

Die Repo-Historie hat in diesem Fall beide Snapshot-Zustaende erhalten. Daher ist die starke Behauptung "das Ereignis ist ueberall unwiederbringlich verloren" falsch: als Forschungs-Forensik konnte der transiente Zustand rekonstruiert werden.

Aber Git ist kein kanonisches Feedback-Event-Ledger:

- es beobachtet nur Exportzeitpunkte;
- ein SET+REMOVE zwischen zwei Exportlaeufen kann komplett unsichtbar bleiben;
- Export-/Commit-Ausfall erzeugt Missingness;
- Snapshot-Commitzeit ist nicht gleich Eventzeit;
- Lernzustand in UnifiedDB kann sich bereits geaendert haben, waehrend die forensische Git-Spur fehlt;
- Git-Snapshotprovenienz ist nicht automatisch kausal an jede adaptive Policy-Aenderung gebunden.

Daher wird H2 nur teilweise behalten:

`GIT_HISTORY = USEFUL_SAMPLED_FORENSIC_SIDE_CHANNEL`, nicht `CANONICAL_EVENT_LEDGER`.

## NEUER MESSFEHLER: TEMPORAL ALIASING

Der beobachtete Rating-Zustand lebte kuerzer als 76 Sekunden. Damit ist der relevante Fehler nicht nur "historische Zeile wird geloescht", sondern auch Sampling-Aliasing:

`event lifetime < export interval => event can be completely unobserved`

Bei unregelmaessigem Exporttakt kann selbst die Anzahl der SET/CHANGE/REMOVE-Ereignisse aus Git-Diffs nicht verlaesslich bestimmt werden.

Das ist strukturell derselbe Messfehler wie bei anderen getakteten AgentZero-Tails: ein sauberer Snapshot ist kein vollstaendiger Ereignisstrom.

## BILLIGSTER DISKRIMINIERENDER TEST

Hoechster Informationsgewinn ist jetzt nicht eine weitere Positivquote, sondern ein Coverage-/Capture-Test:

### `HUMAN_FEEDBACK_EVENT_LEDGER/v1`

Append-only, monotone `event_seq` pro SET/CHANGE/REMOVE mit mindestens:

- `event_id`, `event_seq`;
- `turn_id`, `session_id`, `user_id`;
- `event_type`;
- `old_value`, `new_value`;
- Eventzeit;
- direkte Output-/Model-Receipt-ID oder explizit typisierte Ambiguitaet;
- Source-/Schema-Version.

Dann ueber mindestens mehrere regulaere Exportintervalle vergleichen:

- `runtime_event_count` aus Ledger;
- `snapshot_transition_count` aus Git/Export;
- `capture_ratio = snapshot_transition_count / runtime_event_count`;
- Event-Lebensdauer gegen Exportintervall;
- Anteil komplett unsichtbarer transienter Events.

Ein besonders billiger Falsifikator ist ein kontrollierter SET->REMOVE-Zyklus, der vollstaendig zwischen zwei regulaeren Snapshot-Exporten liegt. Wenn Git danach weiterhin 0->0 zeigt, ist die Sampling-Grenze direkt demonstriert. Dies ist ein vorgeschlagener Forschungsfalsifikator, in diesem `go` wurde keine Produktmutation oder kontrollierte Nutzereingabe ausgefuehrt.

## KAUSALER LERNRAND

Bis ein Event-Ledger und ein vollstaendiger Causal-Join existieren, darf Human-Feedback nicht als auditfester Reward fuer irreversible adaptive Policy-Aenderungen gelten.

Harte Forschungsinvariante:

`adaptive update from human feedback => immutable feedback event + causal source lineage must remain addressable`

Ein materialisierter UI-Zustand darf daneben weiter existieren, aber nicht die alleinige Provenienzquelle fuer Lernen sein.

## FUSION / STATUS

- Gen245 AgentZero-Hauptsnapshot: `UNCHANGED`.
- post-collapse Turnkette: unveraendert `REPLICATED` aus dem vorherigen Bericht.
- F94-Tunnel/Hierarchie: kein neuer AgentZero-Delta; keine neue Promotion.
- Human-Feedback-Sensor: `SOURCE_CONFIRMED_INSTRUMENT`.
- realer negativer Feedback-Zustand: `OBSERVED_TRANSIENT_EVENT`.
- reale Entfernung desselben Current-State-Eintrags: `OBSERVED_AT_SNAPSHOT_TRANSITION`.
- Current-State-Verlust historischer Rating-Zustaende: `MECHANISM_SUPPORTED` am beobachteten SET/REMOVE-Pfad.
- Git als forensische Rekonstruktion: `USEFUL_BUT_SAMPLED`.
- Git als kanonisches Event-Ledger: `REJECTED`.
- Human-Feedback als auditfester Lernreward: `NOT_READY`.
- Antwort-/Modellqualitaet aus dem einzelnen `-1`: `NOT_INFERRED`.

## NAECHSTER MAXIMALER INFORMATIONSGEWINN

1. ersten append-only Feedback-Eventstrom gegen die Snapshot-Transitionen messen;
2. danach Rating -> Assistant-Turn -> User-Turn -> Causal/Workspace/Retrieval -> Output/Model direkt joinen;
3. erst nach Capture-/Join-Coverage und Selection-Bias-Messung Qualitaets- oder Lernclaims bilden.

Dieser `go` erzeugt bewusst nur Forschungsanalyse und keine ClayVerse-/EntityOS-Produktentwicklung.