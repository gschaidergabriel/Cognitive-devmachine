# Generation 245 — Epistemische Quellenrolle und Korrekturadmission

## BIND

- Forschungsrolle: `agentzeroforschung/OWNER_DIRECTIVE_2026-08-18.md`
- gebundener AgentZero-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Generation: `245`
- Manifestzeit: `2026-08-21T14:07:17Z`
- Research-Head vor diesem Write: `56f35dbcda6c33be23714f172c3c7f212a1863b7`
- relevante parallele Vorarbeit: `2026-08-21T1428Z_GEN245_FEEDBACK_WITHDRAWAL_CREDIT_BOUNDARY.md`

Diese Analyse dupliziert den bereits gebundenen Human-Feedback-/Credit-Befund nicht. Sie isoliert einen anderen Mechanismus: **epistemische Admission in `durable_memory`**.

## 1. Beobachtung — eine Assistant-Behauptung wurde als `fact` persistiert

Im Gen245-Chat folgt aufeinander:

1. Nutzer: `gib links immer klickbar aus`
2. Nutzer: `nein, links sind nicht klickbar`
3. Assistant erklaert danach sinngemaess, Markdown rendere im Terminal klickbar; falls Links als Plaintext erscheinen, liege es am Client.

Der dritte Zug ist eine **Assistant-Erklaerung nach direkter menschlicher Gegenbeobachtung**. Aus den vorhandenen Daten laesst sich nicht entscheiden, welche Seite technisch recht hat. Der Sachverhalt ist daher epistemisch `UNRESOLVED/CONFLICT_PRESENT`.

Trotzdem steht in `agentZero/abruf/durable_memory.jsonl` fuer genau den Assistant-Turn `0c235334-b595-4170-a085-a4565ebdce2d`:

- `kind = fact`
- `memory_id = 068c281f-25cd-4577-be45-d51e5ddf370d`
- `provenance.rolle = assistant`
- `provenance.extractor = bahn-extraktor-v1`
- `provenance.modell = openai/gpt-oss-20b`
- `provenance.regel = beleg zeichengenau im Quelltext verifiziert`
- gespeicherter Inhalt: die Assistant-Erklaerung ueber Markdown-/Client-Rendering.

**Klassifikation:** `ASSISTANT_ASSERTION_LAUNDERING` / `ROLE_BLIND_FACT_ADMISSION`.

Wichtig: Das beweist **nicht**, dass der gespeicherte Satz sachlich falsch ist. Es beweist, dass ein im Chat ungelöster Widerspruch als unqualifizierter `fact` persistiert wurde.

## 2. Source-Mechanismus — die Anti-Halluzinationsabwehr prueft Zitattreue, nicht Wahrheit

`agentZero/code/produkt/gedaechtnis.py` benennt die Gefahr selbst korrekt: ein erfundener Fakt im dauerhaften Gedächtnis sei schlimmer als keiner. Die eingebaute Hauptabwehr ist deshalb `WOERTLICHKEIT`:

- Extraktor liefert `art`, `inhalt`, `beleg`;
- `beleg` muss zeichengenau im Quelltext vorkommen;
- fehlt der Beleg oder steht er nicht im Text, wird der Kandidat verworfen;
- besteht die Pruefung, wird `db.add_memory(art, ...)` mit derselben semantischen Art ausgefuehrt;
- die Quellenrolle (`rolle`) wird zwar in Provenienz gespeichert, aber in dieser Admission nicht als Autoritaetsgate benutzt.

Das stoppt einen wichtigen Fehler:

`EXTRACTOR_ERFINDET_ZITAT -> REJECT`

Es stoppt aber nicht:

`ASSISTANT_SAGT_UNVERIFIZIERTE_BEHAUPTUNG -> EXTRAKTOR_ZITIERT_SIE_EXAKT -> FACT`

Die bisherige Schutzregel beweist also nur:

`SOURCE_VERBATIM`

nicht:

`CLAIM_VERIFIED`.

## 3. Retrieval-Pruefung — keine spaetere Quellenrollen-Korrektur im MicroClay-Scoring sichtbar

`agentZero/code/produkt/microclay_retrieval.py` liest fuer Kandidaten `kind`, `subject`, `value`, `ts` und `provenance`. Das Ranking benutzt aber sichtbar:

- lexikalische Ueberlappung;
- Recency;
- einen Strukturbonus fuer u. a. `fact`, `decision`, `task`, `preference`;
- gelernte Entry-Point-Capitals.

Die Kandidatenmenge filtert nach Memory-Kind, User und aktuellem Source-Turn. Ein Gate wie

- `rolle=assistant -> claim statt fact`,
- `source_authority`,
- `conflict_status`,
- `verified_outcome`,
- `human_correction`

ist im gebundenen Retrievalpfad nicht beobachtet.

Damit kann der Typ `fact`, den die Admission vergeben hat, spaeter sogar den normalen `structured`-Bonus erhalten. MicroClay selbst behauptet zwar korrekt `truth_authority=False`; dennoch erbt es die bereits vorher semantisch aufgewertete Memory-Zeile.

## 4. Wichtige Scope-Korrektur zur parallelen Feedback-Analyse

Der Gen245-Turn `finde Klobrillen beim Bauhaus` besitzt eine Retrieval-Episode mit:

- `status = UNKNOWN`
- `selected_memory_ids = []`
- `chars_selected = 0`.

Das beweist: **kein MicroClay-Durable-Memory wurde fuer diesen Turn selektiert.**

Es beweist nicht: **Zero hatte keinen laufenden Gespraechskontext.**

Der exportierte `agentZero/code/produkt/retrieval.py` baut getrennt:

- `own = recent_turns_alle(30)` als laufenden Gespraechskontext;
- `durable_memory = MicroClayRetrieval.retrieve(...)` als separaten Langzeit-/Memory-Pfad.

Daher bleibt die parallele Credit-Grenze korrekt — dieser konkrete Downvote darf MicroClay nicht negativ belohnen —, aber die Formulierung muss kausal eng bleiben:

`NO_MICROCLAY_DURABLE_MEMORY_SELECTED`

statt

`NO_MEMORY_OR_CONTEXT_USED`.

## 5. Hypothesen und Gegenhypothesen

### H1 — Verbatim-Guard schützt Provenienztreue, nicht epistemische Wahrheit

Vorhersage: Assistant-Aussagen koennen als `fact` persistieren, wenn der Extraktor sie exakt zitiert, auch ohne externe Verifikation.

Beobachtung: genau ein realer Gen245-Fall ist gebunden.

Status: `MECHANISM_SUPPORTED`.

### GH1 — `fact` bedeutet nur "fact-like utterance", nicht Wahrheit

Wenn das die beabsichtigte Semantik waere, waere das Risiko kleiner. Dagegen sprechen jedoch:

- die Modulbegruendung selbst warnt, ein erfundener "Fakt" werde spaeter abgerufen und geglaubt;
- `fact` erhaelt im Retrieval einen strukturierten Bonus;
- es gibt in der sichtbaren Admission keinen getrennten Typ `assistant_assertion` oder `unverified_claim`.

Status: `WEAKENED`, aber durch einen expliziten Schema-Vertrag falsifizierbar.

### GH2 — Der Assistant koennte technisch recht haben

Ja. Der Nutzer beobachtet nicht-klickbare Links; der Assistant bietet eine Client-Erklaerung. Ohne Browser-/Renderer-Receipt ist die Sachwahrheit nicht entscheidbar.

Das widerlegt den Designbefund nicht, sondern schaerft ihn: **gerade weil die Wahrheit offen ist, darf der Konflikt nicht allein durch Zitattreue zu `fact` kollabieren.**

Status: `RETAINED_COUNTERHYPOTHESIS`; Claim-Wahrheit bleibt `UNRESOLVED`.

### GH3 — `provenance.rolle=assistant` erlaubt spaeteres Discounting

Die Information ist vorhanden und damit reparierbar. Im gebundenen MicroClay-Scoring ist aber kein Rollen-/Autoritaetsdiscount sichtbar.

Status: `NOT_OBSERVED_IN_RETRIEVAL_PATH`.

### GH4 — `own_recent` enthaelt die menschliche Korrektur und neutralisiert den falschen Memory-Typ

Kurzfristig moeglich. Der aktuelle World-Assembler liefert den laufenden Kontext separat aus. Das ist ein Schutz gegen sofortige Vergessenheit.

Offen bleibt, was nach Alterung/Verdichtung geschieht und ob eine langlebige `fact`-Zeile spaeter ohne die alte Korrektur selektiert wird.

Status: `RISK_NOT_YET_MEASURED`.

## 6. Neue Forschungsinvarianten

1. `VERBATIM_PROVENANCE != TRUTH_PROVENANCE`
2. `ASSISTANT_ASSERTION + EXACT_QUOTE != FACT`
3. `CONFLICT_PRESENT -> NO_UNQUALIFIED_FACT_PROMOTION`
4. `RECENT_CONTEXT != DURABLE_RETRIEVAL`
5. Quellenrolle muss nicht nur gespeichert, sondern vor semantischer Promotion kausal ausgewertet werden.

## 7. Billigster hoher Informationsgewinn — `MEMORY_EPISTEMIC_ADMISSION_RECEIPT/v1`

Observer-only Receipt pro semantischem Memory-Kandidaten:

- `memory_id`
- `source_turn_id`
- `source_role`
- `source_quote`
- `extracted_kind`
- `proposed_kind`
- `source_authority_class`
- `nearby_counterevidence_turn_ids`
- `conflict_status = NONE|PRESENT|UNKNOWN`
- `verification_status = VERIFIED|UNVERIFIED|CONFLICTED`
- `admission_verdict`
- `reason`

Minimaler Quellenklassenraum:

- `USER_SELF_REPORT`
- `USER_PREFERENCE`
- `ASSISTANT_ASSERTION`
- `EXTERNAL_SOURCE_CLAIM`
- `VERIFIED_EFFECT_OUTCOME`
- `SYSTEM_RECEIPT`

Der Receipt soll **nicht** Wahrheit erraten. Er soll verhindern, dass fehlende Autoritaet unsichtbar wird.

## 8. Kontrollierter Falsifikator

Kleine feste Matrix, ohne Produktwirkung:

1. Nutzer: `Ich bevorzuge X.` -> `preference`, zulässig.
2. Assistant: `X ist Y.` ohne Beleg -> `assistant_assertion/unverified_claim`, nicht `fact`.
3. Nutzer widerspricht direkt einer Assistant-Aussage -> `CONFLICT_PRESENT`, keine `fact`-Promotion.
4. Verifizierter Effect-Receipt bestaetigt X -> Fact-Promotion darf moeglich werden.
5. Externe Quelle A sagt X, Quelle B widerspricht -> `CONFLICTED`, keine stille Kollapsbildung.
6. Exakter, aber erfundener Extraktor-Beleg -> bestehender Verbatim-Guard muss weiterhin rejecten.

Danach ueber alle aktuell 1.193 Durable-Memory-Zeilen messen:

- Anteil `fact` mit `provenance.rolle=assistant`;
- Anteil mit zeitnaher menschlicher Korrektur/Gegenbeobachtung;
- spaetere Retrieval-Selektion dieser Zeilen;
- ob Gegenbelege gleichzeitig im Kontext vorhanden waren;
- Ergebnis getrennt nach `kind` und Quellenrolle.

## 9. Forschungsstatus

- Verbatim-Anti-Halluzinationsmechanismus: `MECHANISM_SUPPORTED`
- Assistant-Assertion als `fact` persistiert: `OBSERVED_AT_SNAPSHOT`
- Wahrheit der konkreten Markdown-/Client-Erklaerung: `UNRESOLVED`
- direkter menschlicher Gegenbefund im Chat: `OBSERVED_AT_SNAPSHOT`
- rollen-/autoritaetsbewusstes Admission-Gate in `gedaechtnis.py`: `NOT_OBSERVED`
- rollen-/autoritaetsbewusstes Gate im gebundenen MicroClay-Scoring: `NOT_OBSERVED`
- konkrete spaetere Kontamination durch diesen Memory: `NOT_MEASURED`
- kurzfristiger kompletter Kontextverlust im Bauhaus-Turn: `NOT_SUPPORTED`; `own_recent` ist separater Pfad
- Whole AgentZero / funktionales Bewusstsein: `NOT_CLAIMED`

## 10. Wichtigstes Ergebnis

Der neue Befund ist **kein weiterer Retrieval-Miss**. Er liegt eine Stufe davor:

> Zero besitzt eine sinnvolle Anti-Halluzinationsregel, die exakt prueft, ob ein Memory-Beleg wirklich im Quelltext steht. Aber diese Regel verwechselt Quelltreue mit epistemischer Autoritaet. Dadurch kann eine Assistant-Behauptung — sogar in unmittelbarer Naehe menschlicher Gegenbeobachtung — sauber zitiert und trotzdem als `fact` persistiert werden.

Das ist besonders relevant, weil der Fehler nicht wie eine Halluzination aussieht: Provenienz, exaktes Zitat und Memory-ID sind alle korrekt. **Gerade diese formale Sauberkeit kann die ungeklaerte Behauptung spaeter glaubwuerdiger machen.**

Naechster hoechster Informationsgewinn: `MEMORY_EPISTEMIC_ADMISSION_RECEIPT/v1` plus Vollscan der 1.193 Memories auf `assistant fact -> correction/conflict -> later retrieval`.