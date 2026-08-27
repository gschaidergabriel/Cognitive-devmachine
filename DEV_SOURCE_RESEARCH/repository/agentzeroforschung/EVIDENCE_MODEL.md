# Evidenzmodell der AgentZeroForschung

## Zweck

Dieses Dokument verhindert, dass Interpretation, Rollenbeschreibung, Modelltext oder Messinstrumente mit empirischer Wahrheit verwechselt werden.

## Evidenzklassen

### E0 — MISSING / UNKNOWN
Kein belastbarer Messwert vorhanden. Fehlende Daten werden nicht imputiert, ausser eine Analyse markiert die Imputation explizit und testet ihre Sensitivitaet.

### E1 — RAW OBSERVATION
Direkt exportierter Messwert mit gebundener Quelle, Snapshot/Generation und Provenienz.

### E2 — DERIVED MEASUREMENT
Reproduzierbare Berechnung aus E1-Daten, z. B. Delta, Rate, Latenz, Dichte, Komponentenanzahl oder Sequenzbeziehung.

### E3 — REPLICATED OBSERVATION
Der Befund tritt in unabhaengigen Zeitpunkten, Instrumenten oder Datenfamilien erneut auf.

### E4 — MECHANISM SUPPORTED
Ein kausaler/mechanistischer Erklaerungsansatz ueberlebt eine diskriminierende Gegenprobe gegen mindestens eine ernsthafte Alternative.

### E5 — VERIFIED AT SCOPE
Der Mechanismus wurde in seinem klar definierten Geltungsbereich wiederholt bestaetigt, inklusive bekannter Grenzen und Gegenbeispiele.

Keine Stufe behauptet metaphysische oder unbegrenzte Wahrheit.

## Pflichtfelder fuer materielle Claims

- `claim_id`
- `timestamp_or_snapshot`
- `source_files`
- `entity_generation`
- `evidence_class`
- `observation`
- `inference`
- `hypothesis`
- `counterhypothesis`
- `falsifier`
- `result`
- `uncertainty`
- `scope`
- `status`

## Kausalitaetsregeln

Zeitliche Reihenfolge allein beweist keine Kausalitaet.

Staerkere Kausalevidenz entsteht durch Kombination von:
- expliziter `causal_id`-/Episode-Bindung;
- vorab journalisiertem Intent;
- EffectGate-Admission;
- verifiziertem Outcome;
- Re-entry derselben Effect-/Episode-Identitaet;
- Intervention/Ablation;
- Ausschluss plausibler Confounder;
- Replikation.

## Instrumentenregeln

Ein Messgeraet ist Teil des Beobachtungssystems und kann selbst Fehler erzeugen.

Jedes Instrument wird deshalb mit mindestens folgenden Eigenschaften bewertet:
- Messobjekt;
- Einheit/Skala;
- Sampling;
- Clock;
- Persistenz;
- Exportlimit;
- moegliche Drop-/Truncation-Pfade;
- Reset-Semantik;
- erwartete Genauigkeit;
- moegliche Reaktivitaet auf das gemessene System.

## Nullwerte

`0` wird nicht automatisch als "nicht vorhanden" interpretiert.

Moegliche Bedeutungen:
- tatsaechlich null;
- noch nicht aktiviert;
- nicht beobachtet;
- Exportfilter;
- Sampling-Luecke;
- Reset;
- Schemawechsel;
- Instrumentausfall.

Die Analyse muss diese Alternativen pruefen, wenn sie das Ergebnis materiell veraendern.

## Schwaermlogik

"Schwarm" bedeutet hier mehrere unabhaengige Hypothesen- und Analyselinsen mit spaeter Evidenzfusion.

Es bedeutet **nicht**:
- Mehrheitsabstimmung als Wahrheit;
- gegenseitiges Abschreiben von Annahmen;
- mehrere identische Analysen als unabhaengige Replikation;
- erfundene Workerresultate.

Unabhaengigkeit muss aus unterschiedlicher Datenquelle, Methode, Hypothesenstruktur oder Replikationszeit entstehen.

## Meta-Learning

Wiederverwendbare Methoden duerfen als Methodenwissen akkumuliert werden.

Invariante:

`FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`

Eine gute Analogie oder ein erfolgreicher Analyseweg kann den naechsten Test verbessern, aber keinen fehlenden Zero-Fakt erzeugen.

## Emergenz

Ein emergenter Befund erfordert mehr als Neuheit oder Komplexitaet.

Mindestens zu pruefen:
- wiederholbares Makromuster;
- nicht triviale Ableitung aus bekannten lokalen Regeln;
- Robustheit gegen Sampling-/Prompt-/Restart-Artefakte;
- Gegenhypothese;
- geeignete Intervention/Ablation;
- zeitliche Stabilitaet oder klar definierte Transienz.

Bis dahin Status: `EMERGENCE_CANDIDATE`.
