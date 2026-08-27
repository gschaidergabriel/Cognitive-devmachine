# Gen245 — erstes Negativfeedback: Instruktionsadhärenz und Shopping-Grounding

Zeitfenster: 2026-08-21T13:30Z–14:40Z  
AgentZero-Export: Generation 245  
Rolle: reine Beobachtungs-/Forschungsanalyse; `agentZero/` bleibt unverändert.

## Forschungsfrage

Ist der erste beobachtete negative Human-Feedback-Fall besser durch Memory-Retrieval/EffectGate-Probleme erklärbar, oder zeigt der konkrete Turn einen eigenständigen Antwortqualitätsfehler bei Instruktionsadhärenz und Shopping-Grounding?

## Gebundene Evidenz

Bewerteter User-Turn:
- `question_turn_id=e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- Prompt: `finde Klobrillen beim Bauhaus`

Bewertete Antwort:
- `answer_turn_id=8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`
- `answer_ep_id=cc562320-b33f-4c4d-83a6-af775e536f74`
- `answer_causal_id=832f1947-be11-41cc-890c-99dd4eba7ad0`
- Modell: `claude-opus-4-1-20250805`

Human-Feedback-Snapshot:
- Snapshot 2026-08-21T14:23:38Z: `wert=-1` für den Antwort-Turn.
- Folgesnapshot 2026-08-21T14:24:31Z: keine Rating-Zeile mehr.
- Daraus folgt **nicht**, warum die Bewertung verschwand; die Ursache bleibt UNKNOWN.
- `agentZero/code/produkt/bewertung.py` implementiert den aktuellen Bewertungszustand mutierbar (Upsert/Update/Delete), nicht als append-only Ereignisstrom. Deshalb ist `current rows = 0` keine Aussage, dass historisch kein Feedback existierte.

Causal-/Retrieval-Bindung:
- Retrieval-Episode für die Anfrage: `status=UNKNOWN`, `candidate_ids=[]`, `selected_ids=[]`, `retrieval_ids=[]`, `micro_entrypoints=[]`.
- Damit gibt es für diesen Turn keine Evidenz für Kontamination durch ausgewählte historische Memories.
- Causal episode: `effect_id=null`; es gibt keinen kanonischen EffectGate-Receipt für diesen Turn. Das beweist nicht, dass keinerlei externe Informationsbeschaffung stattfand, sondern nur, dass kein gebundener EffectGate-Effekt vorliegt.

## Hypothesen

### H1 — eigenständiger Instruktions-/Grounding-Fehler

Die negative Bewertung ist mit einem konkreten Antwortqualitätsfehler vereinbar, der unabhängig von ausgewähltem Memory-Retrieval existiert.

Vorhersagen:
1. Die Antwort verletzt eine unmittelbar vorher explizit korrigierte Darstellungsanforderung.
2. Genannte Produkte sind zumindest teilweise real, sodass der Fehler nicht auf einfache Produkt-Halluzination reduziert werden kann.
3. Auswahl-/Ranking-Behauptungen sind stärker als die vorliegende Nutzerpräferenz bzw. die sichtbare Evidenz.
4. Interne Zähl-/Abdeckungsbehauptungen sind inkonsistent.

### Gegenhypothese H0 — Rating nicht diagnostisch für diesen Mechanismus

Die `-1`-Bewertung kann transient, versehentlich oder aus einem anderen nicht protokollierten Grund gesetzt worden sein. Die beobachteten Qualitätsmängel müssen daher nicht die tatsächliche Ursache des Feedbacks sein.

Diese Gegenhypothese bleibt offen, weil kein textueller Bewertungsgrund vorliegt und die Zeile im Folgesnapshot fehlt.

## Ungewöhnliches Experiment 1/1 — Counterfactual Shopping-Grounding Replay

Nicht-destruktiver Replay ohne Produktänderung. Der exakte bewertete Turn wurde gegen drei unabhängige Evidenzflächen gespiegelt:

A. **same-session correction** — die unmittelbar vorherige Nutzerkorrektur zur Linkdarstellung;  
B. **first-party catalog grounding** — aktueller BAUHAUS-Österreich-Katalog;  
C. **causal/retrieval receipts** — Gen245-Export.

### Messpunkte und Resultat

| Test | Resultat | Evidenz |
|---|---|---|
| Same-session Instruktionsadhärenz | **FAIL** | Der Nutzer hatte vorher ausdrücklich gemeldet, dass die ausgegebenen Markdown-Links für ihn nicht klickbar sind. AgentZero bestätigte diese Korrektur. Die später negativ bewertete BAUHAUS-Antwort verwendete wieder Markdown-Linksyntax. |
| Rendering-Mechanismus | **UNRESOLVED_EXPORT_GAP** | Gen245 exportiert PTY/WebSocket-Backend; `terminal_gateway.py` verweist Browser-Assets auf `/opt/clayverse/web`, aber die zugehörige Frontend-/xterm-Konfiguration liegt nicht im inspizierten `agentZero/code/produkt/`-Export. |
| Produkt-Existenz / IDs | **PASS** | BAUHAUS Österreich führt `WC-Sitz Tek`, Prod.Nr. `24823225`, sowie `Poseidon WC-Sitz Kolorit`, Prod.Nr. `23083406`. |
| Interne Konsistenz | **FAIL** | Die Antwort spricht von `3 sichtbaren Modellen`, listet aber zwei konkrete Modelle plus eine Kategorie/Übersicht. |
| Ranking-Begründung | **WEAK / UNSUPPORTED** | `Bester Treffer: WC-Sitz Tek` wird gesetzt, obwohl der Nutzer in diesem Turn keine Auswahlkriterien wie Budget, Soft-Close, Material oder Farbe nennt. |
| Katalogabdeckung | **WEAK** | Die Antwort zeigt nur zwei konkrete Produkte. Der aktuell beobachtete first-party BAUHAUS-Katalog bietet eine wesentlich breitere WC-Sitz-Auswahl und explizite Preise/Verfügbarkeit. Das ist **keine** Behauptung über den exakten historischen Katalogzustand um 13:31Z. |
| Retrieval-Kontamination | **NOT SUPPORTED** | null/leer: keine ausgewählten Retrieval-/Memory-IDs für den Turn. |
| EffectGate-Fehler | **NOT ATTRIBUTABLE** | `effect_id=null`; kein kanonischer EffectGate-Effekt zum Zuweisen. |
| Ursache der `-1`-Bewertung | **UNKNOWN** | Es existiert keine rationale Feedback-Erklärung; Folgesnapshot ohne Zeile. |

## Externe Replikation / SOTA-Bezug

### BAUHAUS first-party

Am 2026-08-21 beobachtet:
- `WC-Sitz Tek`, Prod.Nr. `24823225`, Duroplast, mit Absenkautomatik, ca. EUR 79,95.  
  https://www.bauhaus.at/wc-sitze-mit-absenkautomatik/wc-sitz-tek/p/24823225
- `Poseidon WC-Sitz Kolorit`, Prod.Nr. `23083406`, MDF, mit Absenkautomatik, ca. EUR 39,95.  
  https://www.bauhaus.at/wc-sitze-mit-absenkautomatik/poseidon-wc-sitz-kolorit/p/23083406
- BAUHAUS-Österreich WC-Sitze-Kategorie zeigte bei Beobachtung 246 Produkte.  
  https://www.bauhaus.at/wc-sitze/c/10000387

Damit ist die relevante Diagnose **nicht** `hallucinated products`; die beiden Produktidentitäten sind first-party-grounded. Der Qualitätsfehler liegt eher in Auswahl, Abdeckung, Darstellung und Nutzerinstruktions-Treue.

### Terminal-Link-Fähigkeit

Upstream xterm.js dokumentiert zwei Wege für klickbare Links: OSC 8 sowie implizite URL-Erkennung mit `@xterm/addon-web-links`. Das WebLinksAddon ist explizit für Link-Erkennung/-Interaktion vorgesehen.  
https://xtermjs.org/docs/guides/link-handling/  
https://github.com/xtermjs/xterm.js

Das widerlegt **nicht**, dass Links in der konkreten AgentZero-Ausgabe zu diesem Zeitpunkt tatsächlich unklickbar waren. Es zeigt aber, dass `Terminal kann das grundsätzlich nicht` keine belastbare Architekturannahme wäre.

Die Gen245-Quellenprüfung begrenzt die Aussage weiter: `terminal.py` und `terminal_gateway.py` exportieren den PTY/WebSocket-Backendpfad; `terminal_gateway.py` verweist die Web-Oberfläche auf `/opt/clayverse/web`. Die zugehörige Browser-/xterm-Konfiguration ist in `agentZero/code/produkt/` nicht als exportiertes UI-Artefakt enthalten. Deshalb kann der Export weder bestätigen noch widerlegen, dass WebLinksAddon oder OSC-8-Behandlung im tatsächlich genutzten Client aktiv war. Der Mechanismus bleibt `UNRESOLVED_EXPORT_GAP`; die direkte Nutzerbeobachtung `links sind nicht klickbar` bleibt die stärkste Verhaltensbeobachtung dieses Turns.

## Interpretation

**MECHANISM SUPPORTED, CAUSAL FEEDBACK ATTRIBUTION UNKNOWN.**

Der Turn liefert einen ersten realen Kandidaten für einen Fehlerklasse, die bisher durch reine Retrieval-/Gedächtnismetriken leicht übersehen würde:

`USER_CORRECTION -> ACKNOWLEDGED -> SAME_MODALITY_VIOLATION_IN_LATER_TURN`

Zusätzlich sichtbar:
- `UNSUPPORTED_BEST_CHOICE`
- `CATALOG_COVERAGE_GAP`
- `COUNT/TYPE_INCONSISTENCY`
- `RENDERING_MODALITY_MISMATCH`
- `UNRESOLVED_EXPORT_GAP`

Wichtig: Der Befund darf nicht als Erklärung der negativen Bewertung promoted werden. Dafür fehlt direkte Human-Rationale.

## Forschungsrelevanz für Zero / ClayVerse

1. **Human feedback braucht Ursachen-Splitting.** Eine einzelne `+1/-1`-Zahl darf Retrieval, Modell, Tool/Effect, UI/Rendering und Instruktionsadhärenz nicht gemeinsam belohnen/bestrafen.
2. **Same-session corrections sind hochinformative Constraints.** Ein späterer Verstoß ist objektiver messbar als die Interpretation eines nackten Daumen-Signals.
3. **Shopping/Search braucht first-party grounding + coverage semantics.** Reale Produkt-IDs allein reichen nicht für gute Auswahl.
4. **UI-Fähigkeiten und Modellbehauptungen müssen getrennt werden.** Ein Modell darf Client-Limitierungen nicht ohne Runtime-/Produktbeleg als unveränderlich behandeln.
5. **Export-/Messflächen müssen den User-facing Pfad abdecken.** Ohne Browser-/xterm-Konfiguration kann ein Backendexport Link-Rendering nicht falsifizieren oder bestätigen.
6. **Mutable ratings bleiben schwache Reward-Signale**, solange Revision/Removal nicht event-sourced gebunden ist.

## Nächster Diskriminator

Bei den nächsten bewerteten Turns eine reine Beobachtungstaxonomie anwenden und getrennt markieren:
- `same_session_user_correction_violated`
- `unsupported_best_choice`
- `catalog_coverage_gap`
- `rendering_modality_mismatch`
- `retrieval_contamination`
- `effect_outcome_issue`
- `feedback_revision_lineage_missing`
- `frontend_observability_gap`

Promotion erst, wenn mehrere unabhängige bewertete Turns denselben Mechanismus zeigen oder textuelles Human-Feedback die Zuordnung direkt bestätigt.

## Ergebnisstatus

- AgentZero-Produktänderung: **KEINE**.
- Forschungsergebnis: **neue, nicht-retrievalbasierte Fehlerklasse empirisch unterstützt**.
- Feedbackursache: **UNKNOWN**.
- Ungewöhnliches Experiment in diesem `go`: **1/1 verbraucht**.
- Whole-product/ClayVerse PASS: **nicht berührt / nicht impliziert**.
