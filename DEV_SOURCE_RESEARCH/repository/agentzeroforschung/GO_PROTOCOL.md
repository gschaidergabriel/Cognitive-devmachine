# GO-Protokoll — AgentZeroForschung

## Exakter Trigger

`go`

Ab 2026-08-18 ist dies fuer dieses Forschungsorgan der einzige `go`-Makrozyklus.

## Ziel

Den neuesten Agent-Zero-Messstand maximal informationsreich auswerten, gegen alternative Erklaerungen testen, mit historischen und externen Forschungsdaten verbinden und neue belastbare Erkenntnisse unter `agentzeroforschung/` persistieren.

## Pflichtzyklus

### 0. BIND
- aktuellen `main`-Head erfassen;
- neuestes `agentZero/MANIFEST.json` binden;
- Generation, Exportzeit, Dateipruefsummen und neue/fehlende Datenfamilien erfassen;
- vorherigen Forschungsstand aus `agentzeroforschung/` laden;
- keine Aussage aus einem alten Snapshot als aktuell behandeln.

### 1. DELTA
- seit dem letzten ausgewerteten Snapshot geaenderte Dateien/Zaehler/Zeitraster bestimmen;
- neue Instrumente automatisch registrieren;
- Nullwerte, Sampling-Luecken, Reset-/Restart-Grenzen und Exportbegrenzungen markieren;
- unterscheiden: echter System-Delta vs Export-/Instrumentierungs-Delta.

### 2. SCHWARM-LINSEN
Materielle Daten werden aus mehreren voneinander getrennten Analyseperspektiven betrachtet. Die Linsen duerfen sich widersprechen.

Pflichtlinsen, sofern Daten vorhanden:
1. **Kausalitaet** — Turn/Episode/Effect/Re-entry-Ketten, Temporalitaet, Interventionen;
2. **Kognition** — Workspace, Auswahl, Konflikt, Kontext, Zustandsuebergaenge;
3. **Memory/Retrieval** — Treffer, Misses, Entry-Points, Feedback, Kompression, Provenienz;
4. **Autonomie** — Puls, Initiative, Zielpersistenz, Wiederplanung, Stillstand;
5. **EffectGate/Handlung** — Intent, Admission, Outcome, Replay, Unsicherheit;
6. **Graph/Struktur** — Knoten/Kanten, Vernetzung, Komponenten, Dynamik, Projektion;
7. **Identitaet/Continuity** — Generation, Sessions, Benutzerperspektiven, Restart/Drift;
8. **Robustheit/Sicherheit** — Fail-closed, Anomalien, stale state, Leakage, Doppelwirkung;
9. **Performance/Ressourcen** — Latenz, Durchsatz, Last, Queueing, Sampling sofern messbar;
10. **Meta-Learning/Emergenz** — wiederkehrende Methoden, Transfer, Neuheit, Gegenbeispiele;
11. **Domänenoffene Forschung** — neue Muster, die keiner vorgegebenen Kategorie folgen.

### 3. HYPOTHESENRAUM
Fuer jeden starken Befund:
- mindestens eine Haupt-Hypothese;
- mindestens eine strukturell andere Gegenhypothese;
- versteckte Annahmen;
- erwartete Beobachtungen unter beiden;
- billigster diskriminierender Falsifikator.

### 4. EMPIRISCHE PRUEFUNG
Prioritaet:
1. bereits vorhandene Messdaten;
2. Zeitreihen/Deltas;
3. unabhaengige Datenfamilie;
4. Replikation in spaeterem Snapshot;
5. gezielte neue Messinstrumentierung, falls Beobachtungsluecke verbleibt.

Ein neues Messgeraet muss dokumentieren:
- Variable/Einheit;
- Sampling/Trigger;
- Clock/Zeitzone;
- Quelle und Provenienz;
- moegliche Messverzerrung;
- Ausfall-/Missing-Semantik;
- erwarteten Informationsgewinn.

### 5. CROSS-DOMAIN
Wenn strukturelle Aehnlichkeiten zu etablierten Forschungsdomaenen bestehen, koennen externe Primaerquellen herangezogen werden, z. B.:
- dynamische Systeme;
- Kontrolltheorie;
- Kognitionswissenschaft;
- Gedächtnis-/Retrievalforschung;
- Graphentheorie/Netzwerkwissenschaft;
- Informationstheorie;
- Kausalitaetsforschung;
- verteilte Systeme;
- Sicherheits-/Reliability-Engineering;
- Meta-Learning/Continual Learning;
- Human-Computer Interaction.

Externe Theorie darf die internen Messdaten erklaeren oder neue Tests motivieren, aber nie fehlende Zero-Fakten ersetzen.

### 6. ADVERSARIAL REVIEW
Vor Promotion eines Befunds pruefen:
- Instrumentenartefakt?
- Exportlimit oder Sampling-Bias?
- Scheinkorrelation?
- Restart/Generation als Confounder?
- Prompt-/Modellartefakt statt Systemverhalten?
- Selbstauswahl-/Feedback-Schleife?
- Goodhart-Effekt?
- duplizierte oder nicht unabhaengige Evidenz?
- alternative triviale Erklaerung?

### 7. FUSION
Ergebnisse zusammenfuehren als:
- Beobachtung;
- Ableitung;
- Hypothese/Gegenhypothese;
- Test/Falsifikator;
- Ergebnis;
- Unsicherheit;
- naechster Messbedarf;
- Status.

Keine Mehrheitsabstimmung ersetzt Evidenz. Bei Widerspruch bleibt Hyperposition/UNRESOLVED erhalten.

### 8. PERSIST
Jeder substantielle `go` erzeugt mindestens eines:
- neue Analyse unter `agentzeroforschung/analysen/`;
- Aktualisierung des Messgeraeteregisters;
- aktualisierte Hypothesen-/Falsifikatorlage;
- dokumentiertes negatives Resultat;
- explizites `NO_NEW_EVIDENCE`, falls wirklich kein auswertbarer Delta existiert.

### 9. RE-ENTRY
Nach Persistierung:
- aktuellen Head erneut erfassen;
- pruefen, ob waehrend der Analyse ein neuer agentZero-Export eingetroffen ist;
- wenn ja, dessen relevante Deltas noch im selben `go` einbeziehen, soweit praktisch;
- offene Hypothesen fuer den naechsten Snapshot priorisieren.

## Promotionsstufen

- `OBSERVED_AT_SNAPSHOT`
- `RETAINED_HYPOTHESIS`
- `REPLICATED`
- `MECHANISM_SUPPORTED`
- `VERIFIED_AT_SCOPE`

Nie aus einem einzelnen Snapshot direkt zu allgemeiner Wahrheit springen.

## Abschluss eines `go`

Ein `go` endet mit einer kompakten Forschungsbilanz:
- gebundener Snapshot/Head;
- wichtigste neue Beobachtung;
- staerkste Gegenhypothese;
- was dadurch neu gelernt wurde;
- welcher Messwert/Test als naechstes am meisten Information bringt;
- welche Datei(en) unter `agentzeroforschung/` aktualisiert wurden.
