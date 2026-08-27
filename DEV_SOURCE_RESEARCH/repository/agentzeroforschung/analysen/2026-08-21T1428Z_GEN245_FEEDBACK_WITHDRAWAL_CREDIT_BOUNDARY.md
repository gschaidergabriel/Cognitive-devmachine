# Generation 245 — Fusion-Addendum: Human-Feedback Component-Credit-Grenze

## Zweck / Duplikatbereinigung

Waehrend dieses `go` wurde parallel bereits die kanonische Reversal-/Snapshotanalyse persistiert:

- `analysen/2026-08-21T1428Z_GEN245_FEEDBACK_REVERSAL_SNAPSHOT_ALIASING.md`
- Commit `d1ef23763f6d46e0e22b80296b09825c4d8ccc0b`

Die urspruengliche Fassung dieser Datei hatte denselben `0 -> -1 -> 0`-Reversal unabhaengig noch einmal analysiert. Das waere doppelte Forschungsevidenz gewesen. Deshalb wird der ueberlappende Teil hier **nicht** als zweite Replikation gezaehlt, sondern als `DUPLICATE_FUSED` behandelt.

Dieses Addendum konserviert nur den materiellen Befund, der in der Parallelspur nicht enthalten war: **komponentenspezifische kausale Credit-Zuweisung fuer den ersten echten Downvote.**

## BIND

- AgentZero-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Generation: `245`
- Manifestzeit: `2026-08-21T14:07:17Z`
- bewerteter Assistant-Turn: `8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`
- zugehoeriger User-Turn: `e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- Rating-Commit: `92a0fb42b1e5ec9c8dc8d0c24ec2211bd8a9bf64`
- Removal-Commit: `afe252ae61277d8b26f92f13b2ffeb373ff42fb2`

## 1. Rating -> Turn ist exakt gebunden

Der Ratingrecord enthaelt:

- `wert = -1`
- `turn_id = 8bf613cd-5d3f-4224-89d7-05e1c3bcfef1`
- `frage_turn_id = e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- `session_id = session:andreas:2`
- `antwort_hash = 7d990a323c5c077bb0df628cca19a03242b1bc8759ed74f967a5f1f504331d57`

Im Gen245-Chat existieren genau diese beiden Turn-IDs als Ordinal 29/30.

Der Assistant-Turn endete um `2026-08-21T13:52:17.669245Z`; der Rating-Zeitstempel ist `2026-08-21T14:23:39.012848Z`. Das reale Feedback kam damit ca. `31.36 min` nach der Antwort.

Status:

- Rating -> Assistant-Turn: `VERIFIED_AT_SCOPE`
- Rating -> Frage-Turn: `VERIFIED_AT_SCOPE`
- verzögertes menschliches Outcome-Signal: `OBSERVED_AT_SNAPSHOT`

## 2. Turn -> Causal Episode -> Workspace ist exakt gebunden

Die letzte Gen245-Causal-Episode lautet:

- `causal_id = 832f1947-be11-41cc-890c-99dd4eba7ad0`
- `episode_id = 2fffbdd3-266c-4909-a70b-53aae22a62da`
- `observation_turn_id = e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`
- `effect_id = null`
- `reentered = 1`
- `outcome_hash = 7d990a323c5c077bb0df628cca19a03242b1bc8759ed74f967a5f1f504331d57`

Der `outcome_hash` ist exakt der `antwort_hash` des Ratingrecords.

Die Workspace-Episode mit derselben `episode_id` ist:

- `selected = respond`
- `state = COMPLETED`
- gleiche `observation_turn_id`.

Damit ist der erste echte Human-Feedback-Fall nicht nur an Text/Session gebunden, sondern bis in die persistierte Causal-/Workspace-Episode zurueckfuehrbar.

Status:

- Assistant outcome -> Causal Episode: `VERIFIED_AT_SCOPE`
- Causal Episode -> Workspace: `VERIFIED_AT_SCOPE`

## 3. Entscheidender Befund: Retrieval wurde in diesem Turn nicht benutzt

Die Retrieval-Episode fuer exakt denselben User-Turn / dieselbe Causal-/Workspace-Episode zeigt:

- `generation = 245`
- `status = UNKNOWN`
- `chars_selected = 0`
- `entry_keys = []`
- `selected_memory_ids = []`
- `shadow_memory_ids = []`
- `causal_id = 832f1947-be11-41cc-890c-99dd4eba7ad0`
- `episode_id = 2fffbdd3-266c-4909-a70b-53aae22a62da`
- `turn_id = e3cae7e1-f7b9-46de-b0c3-acccb234b8e3`.

Das ist ein harter Komponenten-Aktivierungsbefund:

> Fuer den ersten real bewerteten Downvote hat Retrieval keinen Memory-Kontext geliefert.

Daraus folgt nicht, dass Retrieval generell gut oder schlecht ist. Es folgt nur, dass **dieser konkrete Downvote kein negativer Outcome-Beleg fuer Retrieval-Ranking, Entry-Point-Policy oder einzelne Memory-IDs sein kann.**

## 4. Reale Falsifikation einer naiven Reward-Regel

Naive Regel:

`thumbs_down -> punish retrieval policy`

Vorhersage dieser Regel im ersten echten Datensatz: Retrieval wuerde negatives Credit erhalten.

Beobachtung: Retrieval war nicht aktiv (`0` Zeichen, `0` Entry-Keys, `0` Memories).

Damit ist die Regel fuer diesen Turn empirisch falsifiziert.

Saubere Typisierung:

`FEEDBACK_CAUSAL_JOIN.retrieval = NOT_USED`

Nicht:

`retrieval_reward = -1`

## 5. Neue Forschungsinvariante F96 — COMPONENT_CREDIT_GATE

**F96:** Ein menschliches Outcome darf nur an Subsysteme propagiert werden, deren Aktivierung oder Contribution im gebundenen Turn positiv nachgewiesen ist.

Minimaler Statusraum je Komponente:

- `USED`
- `NOT_USED`
- `UNKNOWN`
- `AMBIGUOUS`
- `ERROR`

Nur `USED` darf normalen komponentenspezifischen Credit erhalten. `NOT_USED` muss Credit `0 / ineligible` bedeuten. `UNKNOWN`, `AMBIGUOUS` und `ERROR` duerfen nicht still in positive oder negative Lernsignale kollabieren.

Erster realer Fall:

- Turn: `USED / TARGET`
- Causal lifecycle: `USED`
- Workspace: `USED`
- Retrieval: `NOT_USED`
- External effect: `NOT_USED` (`effect_id=null`)
- Modellidentitaet: `AMBIGUOUS/BEST_EFFORT`, weil `bewertung.py` das Modell content-basiert aus `mv_translation_log` rekonstruiert.

## 6. Starke Gegenhypothese

Gegenhypothese:

> Obwohl kein Memory selektiert wurde, kann die Retrieval-Komponente indirekt einen globalen Zustand oder Prompt beeinflusst haben und damit doch kausal beteiligt sein.

Aktueller Befund dagegen:

- Retrieval-Receipt meldet `status=UNKNOWN` und null selektierten Kontext;
- keine Entry-Keys oder Memory-IDs wurden in den Turn eingebracht.

Was noch fehlt:

- ein vollstaendiger Pipeline-/Prompt-Receipt, der auch indirekte Retrieval-Metadaten ausserhalb `chars_selected` ausschliesst.

Darum lautet die enge Promotion:

- negativer Credit auf **selektierte Retrieval-Inhalte / Memory-IDs / Entry-Points**: `FALSIFIED_FOR_THIS_TURN`
- jede denkbare indirekte Retrieval-Nebenwirkung: `NOT_FULLY_EXCLUDED`

## 7. Modell-Credit ebenfalls nicht hart zulaessig

Der Ratingrecord nennt `mistral-small-latest`, aber `bewertung.py` dokumentiert diese Zuordnung selbst als best-effort Content-Match. Identische kurze Outputs koennen aliasen.

Daher darf der erste Downvote ebenfalls nicht als harter `mistral-small-latest = bad`-Datensatz behandelt werden.

Status:

- Rating-Modellfeld vorhanden: `OBSERVED`
- eindeutige Modellkausalitaet: `UNRESOLVED`

## 8. Instrumentierung mit maximalem Informationsgewinn

Erweitere den bereits vorgeschlagenen `HUMAN_FEEDBACK_CAUSAL_JOIN_RECEIPT/v1` um eine Komponentenmatrix:

```text
component_credit = {
  turn: USED,
  causal: USED,
  workspace: USED,
  retrieval: NOT_USED,
  effect: NOT_USED,
  model: AMBIGUOUS
}
```

Fuer spaetere Komponenten koennen Toolpfad, Prestage, Translator, Web/Search, EffectGate und Memory-Kompression analog typisiert werden.

Harte Lernregel:

`feedback may update component X only if component_credit[X] == USED and source lineage is durable`

Das append-only Feedback-Event-Ledger aus der Parallelspur bleibt davon unabhaengig notwendig: **Lineage beantwortet, welches Event geschah; COMPONENT_CREDIT_GATE beantwortet, welche Mechanismen daraus lernen duerfen.**

## 9. Fusion

Die Parallelspur `...FEEDBACK_REVERSAL_SNAPSHOT_ALIASING.md` bleibt kanonisch fuer:

- SET -> ABSENT / Removal;
- Git als `SAMPLED_EVENT_SHADOW`;
- Snapshot-Aliasing;
- Feedback-Coverage-/Capture-Lag-Metrologie;
- Event-Ledger-Notwendigkeit.

Dieses Addendum liefert ausschliesslich die orthogonale Credit-Frage:

- erster echter Downvote kausal bis Episode/Workspace gebunden;
- Retrieval in diesem Turn nachweislich ohne selektierten Kontext;
- naive globale Reward-Propagation auf Retrieval empirisch falsifiziert;
- F96 `COMPONENT_CREDIT_GATE` eingefuehrt.

### Promotionsstatus

- Parallel-Reversal als zweite unabhaengige Entdeckung: `DUPLICATE_FUSED` — NICHT gezaehlt
- Rating -> Turn/Causal/Workspace: `VERIFIED_AT_SCOPE`
- Retrieval-Kontext in diesem Turn: `NOT_USED`
- Downvote als negativer Retrieval-Credit: `FALSIFIED_FOR_THIS_TURN`
- Modell-Credit: `UNRESOLVED`
- F96 COMPONENT_CREDIT_GATE: `MECHANISM_REQUIREMENT_SUPPORTED_BY_FIRST_REAL_CASE`
- Whole AgentZero / funktionales Bewusstsein: `NOT_CLAIMED`

## 10. Naechster Diskriminator

Beim naechsten echten Rating nicht zuerst die Positivquote auswerten. Zuerst denselben Komponenten-Join erzeugen und pruefen, ob mindestens ein Fall mit `retrieval=USED` auftritt. Erst dann kann Human-Feedback ueberhaupt als empirisches Retrieval-Outcome getestet werden.
