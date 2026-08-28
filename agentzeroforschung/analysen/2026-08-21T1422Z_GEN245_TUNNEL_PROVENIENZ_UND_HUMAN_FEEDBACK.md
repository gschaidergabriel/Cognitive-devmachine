# Generation 245 — Tunnel-Provenienz korrigiert und Human-Feedback als neues Messinstrument

## BIND

- AgentZero-Export-Commit: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Export-Tree: `7774f4d375bda1df3c346da530a3c217d6613012`
- Generation: `245`
- Exportzeit: `2026-08-21T14:07:17Z`
- aktueller Repo-Head bei Abschluss der Bindung: `581428f0f11de923e3281e5418ee87c76736487e`
- Test-Receipt: `1066 gruen / 1 rot`
- persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Diese Analyse setzt die Gen244-Evidenz-Epochengrenze fort und nimmt zwei neue Evidenzfamilien auf: die korrigierte F94-Sitzungsmetrologie und das neue explizite Human-Feedback-Instrument `eos_bewertungen`.

## 1. Evidence-Spine: neue Epoche waechst weiter synchron

Gen244:

- causal: `582`
- workspace: `14`
- retrieval: `14`
- Andreas-Chat: `28`

Gen245:

- causal: `583`
- workspace: `15`
- retrieval: `15`
- Andreas-Chat: `30`

Damit setzt sich das nach Gen241 beobachtete Muster fort: pro neuem Benutzerzug entsteht wieder genau eine neue Causal-, Workspace- und Retrieval-Episode sowie ein Benutzer-/Assistentenpaar im Chat.

Das ist positiver Live-Mechanismus-Credit fuer die post-collapse Turnkette. Es ist KEIN Beweis, dass die verlorene pre-collapse Historie wiederhergestellt wurde.

Status:

- post-collapse Turnkette: `REPLICATED`
- historische Spine-Wiederherstellung: `NOT_PROVEN`
- destruktiver Reset vs Query/Visibility-Shift: weiterhin `UNRESOLVED`

## 2. F94: alle acht gespeicherten Tunnel sind als Alt-Kontamination entlarvt

Gen244 zeigte im Rohzustand weiterhin `8` Tunnel bei `366` Wegen und `top_decile=0.139`.

Gen245 fuehrt eine entscheidende Provenienzkorrektur ein: fuer Bedingung 3 (Tunnel braucht wiederholte unabhaengige Mitbenutzung) zaehlen nur noch kanonische menschliche Session-IDs der Form `session:<user>` bzw. `session:<user>:<platz>`.

Der Source-Kommentar bindet die konkrete Alt-Kontamination:

- `304` Wege trugen die alte Kennung `unbekannt`;
- `76` Wege trugen Diagnose-/Prueflabels wie `breite-befahrung`, `diag`, `latenzmessung` oder `pruefung-<Datum>`;
- acht Wege konnten dadurch `tunnel=1` erreichen, obwohl verschiedene Strings keine unabhaengigen menschlichen Wiederverwendungen belegen.

Der neue Gen245-Receipt trennt deshalb:

- `tunnel_roh_gespeichert = 8`
- `tunnel_bereinigt = 0`
- `verschiedene_echte_sitzungen_insgesamt = 2`
- `wege_mit_mind_einer_echten_sitzung = 6`
- Bedingung-3-Status: `NOCH_ZU_WENIG_DATEN`

### Neue Evidenzkorrektur

Die acht historischen Tunnel duerfen nicht mehr als Emergenz-/Shortcut-Beleg verwendet werden. Sie sind Legacy-State aus einer fehlerhaften Unabhaengigkeitsdefinition.

Gleichzeitig ist `tunnel_bereinigt=0` KEIN negativer Befund gegen die Tunnelhypothese, weil mit nur zwei verschiedenen echten Sessions die Mindestbedingung von drei Sessions global noch nicht einmal erreichbar ist.

Daher:

- historische `8 Tunnel`: `INVALIDATED_AS_INDEPENDENCE_EVIDENCE`
- echter Tunnelmechanismus im Live-Verkehr: `INSUFFICIENT_DATA`
- neuer Session-Allowlist-Mechanismus: `SOURCE_CONFIRMED_METROLOGY_REPAIR`

## 3. F94-Hierarchie bleibt negativ

Die Konzentrationsmetrik bleibt bei:

- Wege: `366`
- Top-Decile-Anteil: `0.139`
- Gleichverteilungsbaseline: `0.098`
- Urteil: `GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts`

Die aktuelle Entscheidung verwendet mechanisch `anteil > 2 * gleich`. Bei 366 Wegen liegt die Schwelle damit knapp unter `0.20` und ist semantisch konsistent mit der bisherigen ca.-0.20-Regel.

Die neue Tunnel-Korrektur aendert also NICHT den Hauptbefund: eine starke emergente Wegehierarchie ist weiterhin nicht beobachtet.

## 4. Neues Messinstrument: explizites Human-Feedback pro Zero-Antwort

Nach dem Gen245-Export wurde ein neuer Datenkanal angelegt:

- Tabelle: `eos_bewertungen` in derselben UnifiedDB `/var/lib/clay/wiki.db`
- Export: `agentZero/bewertung/bewertungen.jsonl`
- aktueller Stand: `0` Bewertungen, `0` hoch, `0` runter
- Trigger: expliziter Daumen hoch/runter auf eine konkrete Zero-Antwort

Je aktuellem Bewertungszustand werden gespeichert:

- `turn_id`
- `session_id`
- `user_id`
- `wert` in `{-1,+1}`
- `frage_turn_id`
- Frage-Hash und -Laenge
- Antwort-Hash und -Laenge
- Modell (best effort)
- Bewertungszeitpunkt

Positiv:

1. Feedback ist an einen konkreten Assistant-Turn gebunden, nicht nur global gezaehlt.
2. Session-Eigentum wird serverseitig geprueft; ein Mensch kann nicht fremde Sessions bewerten.
3. `UNIQUE(turn_id,user_id)` verhindert doppelte parallele Stimmen fuer denselben Antwortzustand.
4. Frage-/Antworttext wird nicht dupliziert; kanonischer Klartext bleibt in `turns`.
5. Die Tabelle liegt in derselben UnifiedDB wie die Turns, wodurch Join- und WAL-Provenienz besser sind als bei einer zweiten DB-Datei.

Das ist ein substanzieller Observability-Fortschritt: erstmals existiert ein explizites menschliches Outcome-Signal, das spaeter mit Retrieval, Workspace, Modellpfad und Antwortqualitaet verbunden werden kann.

Aber: `0` aktuelle Bewertungen bedeutet noch keinerlei Verhaltens-/Qualitaetsbefund.

## 5. Neuer harter Audit-Rand: Current-State-Feedback ohne Event-Ledger

`setzen()` fuehrt bei einer Meinungsveraenderung ein `ON CONFLICT ... DO UPDATE` aus und ersetzt unter anderem `wert` und `ts`. `wert=0` loescht die Zeile vollstaendig.

Der Export ist ausdruecklich ein Vollabbild, kein Append-Log.

Damit kann ein spaeterer Snapshot nicht unterscheiden:

- nie bewertet;
- frueher positiv, spaeter negativ;
- frueher negativ, spaeter positiv;
- bewertet und danach entfernt.

Fuer reine aktuelle UI-Anzeige ist das korrekt. Fuer Forschung oder Lernen ist es jedoch nicht auditfest, sobald historische Feedbackaenderungen kausale Wirkung auf eine Policy haben duerfen.

### Cross-domain-Verbindung zur Gen241/244-Lineage-Luecke

Gen244 zeigte bereits: adaptives Retrievalkapital kann erhalten bleiben, obwohl seine sichtbaren Ursprungs-Episoden fehlen.

Ein direktes Lernen aus `eos_bewertungen` koennte denselben Fehler erneut erzeugen:

1. positive Bewertung aktualisiert eine Policy;
2. Bewertung wird spaeter geaendert oder geloescht;
3. alter Policy-Credit bleibt bestehen;
4. das urspruengliche Feedbackereignis ist im aktuellen Vollabbild nicht mehr sichtbar.

Daher muss gelten:

`learned state derived from human feedback => immutable source-feedback event remains addressable OR an explicit reversible provenance mapping exists`

## 6. Zweiter Audit-Rand: Modellzuordnung ist content-basiert und potentiell aliasend

`_modell_fuer_zug()` kann die Uebersetzungs-/Modellzeile nicht direkt ueber den bewerteten Assistant-Turn joinen, weil `mv_translation_log.turn_id` auf den Benutzerzug zeigt. Deshalb wird das Modell ueber identischen `caveman_original`-Antwortinhalt innerhalb derselben Sitzung gesucht und bei Mehrdeutigkeit die juengste Uebersetzung genommen.

Das Modul dokumentiert selbst den Randfall identischer kurzer Antworten.

Folge:

- `turn_id -> Bewertung` ist stark gebunden;
- `turn_id -> Modell` ist nur `BEST_EFFORT_CONTENT_MATCH`.

Fuer allgemeine Zufriedenheitsanalyse ist das tolerierbar. Fuer Modellvergleich, A/B-Auswertung oder modellbezogene Credit-Zuweisung darf dieses Feld nicht als harte Ground Truth behandelt werden.

Billigster Fix fuer spaetere Metrologie: der Output-/Translation-Receipt muss die tatsaechliche Assistant-Turn-ID oder eine eindeutige Output-Receipt-ID speichern, damit Modellzuordnung direkt und nicht inhaltsbasiert erfolgt.

## 7. Dritter Audit-Rand: OperationalError wird als Modell-NULL verschluckt

`_modell_fuer_zug()` behandelt jeden `sqlite3.OperationalError` gleich und gibt `None` zurueck. Der Kommentar begruendet dies mit dem legitimen Fall, dass `mv_translation_log` noch nicht existiert.

`OperationalError` umfasst aber auch andere Ursachen wie Lock-, Schema- oder I/O-nahe Fehler.

Damit kollabieren:

- legitime instrumentelle Abwesenheit (`table absent / no translated chat yet`)
- echte Messfehler (`lock/schema/query failure`)

zu derselben Semantik `modell = NULL`.

Das repliziert strukturell den bereits bekannten Omnimind-Messfehler: `ABSENT`, `EMPTY`, `ERROR` und `UNMEASURED` duerfen nicht untypisiert zusammenfallen.

Gefahr: Unter Last koennte Modell-Missingness systematisch ansteigen und spaetere Modellqualitaetsstatistiken verzerren, ohne als Instrumentenausfall sichtbar zu sein.

## 8. Human-Feedback ist kein unverzerrter Reward

Selbst mit perfekter Speicherung ist Daumenfeedback ein selektives Signal. Menschen bewerten typischerweise nicht jede Antwort zufaellig.

Moegliche Bias-Quellen:

- besonders gute/schlechte Antworten werden eher bewertet;
- Benutzer unterscheiden sich in Strenge und Bewertungsfrequenz;
- lange/auffaellige Antworten koennen mehr Feedback ausloesen;
- Bewertungen koennen zeitverzoegert und nach Folgeereignissen erfolgen;
- dieselbe Person kann ihre Meinung revidieren.

Deshalb darf `P(thumbs_up)` nicht ohne Coverage-/Propensity-Kontext als globale Antwortqualitaet gelesen werden.

## 9. Neue Messinstrumente

### `HUMAN_FEEDBACK_EVENT_LEDGER/v1`

Append-only Ereignisspur neben dem aktuellen Materialized State:

- `event_id`
- `turn_id`
- `session_id`
- `user_id`
- `event_type = SET | CHANGE | REMOVE`
- `old_value`
- `new_value`
- `ts`
- Frage-/Antwort-Hash
- direkte Output-/Model-Receipt-ID, falls vorhanden
- Source-/Schema-Version

`eos_bewertungen` kann als aktuelle Sicht bestehen bleiben; Forschung/Lernen bindet dagegen an das Event-Ledger.

### `HUMAN_FEEDBACK_CAUSAL_JOIN_RECEIPT/v1`

Fuer jede Bewertung, die in Forschung oder Lernen eingeht:

1. Rating -> bewerteter Assistant-Turn;
2. Rating.frage_turn_id -> genau ein Benutzerturn;
3. Benutzerturn -> genau eine passende Causal-/Workspace-/Retrieval-Episode, soweit der Turn diese Mechanismen durchlief;
4. Output -> eindeutiger Modell-/Pipeline-Receipt;
5. Ergebnis als Join-Status:
   - `FULLY_BOUND`
   - `NO_RETRIEVAL_EXPECTED`
   - `AMBIGUOUS_MODEL`
   - `MISSING_CAUSAL`
   - `MISSING_SOURCE_TURN`
   - `ERROR`

Harte Invariante fuer spaeteres Lernen:

`human feedback may update adaptive state only if its causal source lineage is FULLY_BOUND (or explicitly typed NO_RETRIEVAL_EXPECTED)`

## 10. Billigste diskriminierende Messungen

### Evidence-Spine

Weiterhin zuerst bekannte pre-collapse IDs direkt in der Live-DB suchen und messen:

- `causal_orphan_rate`
- `unmapped_feedback_source_rate`

### F94 Tunnel

Nicht weiter aus den acht Legacy-Tunneln schliessen. Erst dann erneut testen, wenn mindestens drei kanonische echte Sessions auf denselben Wegen ausreichend Verkehr erzeugt haben. Dann `tunnel_bereinigt` statt `tunnel_roh` als Forschungsmetrik verwenden.

### Human Feedback

Sobald die ersten echten Bewertungen eintreffen, NICHT zuerst die Positivquote berichten. Zuerst messen:

- `rating_coverage = rated_assistant_turns / eligible_assistant_turns`
- Bewertungen je User/Session
- Feedback-Latenz
- Aenderungs-/Entfernungsrate
- Modell-Missingrate getrennt nach `ABSENT` vs `ERROR`
- Causal-Join-Completeness
- Verteilung nach Antwortlaenge / Modell / Retrieval-Status

Erst danach Qualitaetsclaims bilden.

## 11. Fusion / Promotionsstatus

- Gen245 post-collapse Turnkette: `REPLICATED`
- historische Evidence-Spine: `NOT_RECOVERED`
- 8 rohe F94-Tunnel als unabhaengige Wiederverwendung: `INVALIDATED`
- echte F94-Tunnel: `INSUFFICIENT_DATA`
- starke Wegehierarchie: `NOT_OBSERVED` (`0.139` vs ca. `0.196` Schwelle)
- F94 Session-Provenienz-Reparatur: `SOURCE_CONFIRMED_METROLOGY_REPAIR`
- Human-Feedback-Sensor vorhanden: `SOURCE_CONFIRMED_INSTRUMENT`
- reale Human-Feedback-Daten: `NO_DATA_YET`
- Human-Feedback als auditfestes Lernsignal: `NOT_READY`
- Human-Feedback als aktuelle UI-Zustandsanzeige: `MECHANISM_PRESENT`
- persistenter Claude-Code-Adapter-Red: `REPLICATED`
- Whole AgentZero / funktionales Bewusstsein / Gesamtacceptance: `NOT CLAIMED`

## 12. Naechster maximaler Informationsgewinn

Prioritaet bleibt zweigleisig:

1. **alte Evidenzspine direkt in der Live-DB aufloesen**, weil dies entscheidet, ob historische Provenienz geloescht oder nur unsichtbar ist;
2. **den ersten echten Human-Feedback-Datensatz nur mit Causal-/Output-Lineage auswerten**, damit der neue Sensor nicht sofort dieselbe Provenienzschuld erzeugt wie die bestehende Retrieval-Policy.

Der wichtigste neue allgemeine Architekturgrundsatz aus Gen241-245 lautet:

> Adaptive Systeme duerfen komprimieren und aktuelle Sichten materialisieren, aber jede adaptive Zustandsaenderung braucht eine dauerhafte, eindeutig adressierbare Evidenzlinie oder einen expliziten verlustbewahrenden Ersatz-Receipt.
