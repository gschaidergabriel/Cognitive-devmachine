# Generation 247 — Bug-Hypothesen: Closure-Provenienz und revisionsfeste Evidenz

## BIND

- kanonischer AgentZero-Export: `cdb4aa948262f1ed8259c969082666d8e286756b`
- Generation: `247`
- Exportzeit: `2026-08-21T16:37:19Z`
- Gen246-Vergleich: `f56913ac50e5b3539d6279ab3ee9ee482f024d75`, `2026-08-21T15:37:18Z`
- Gen247 Teststand: `1170 gruen / 1 rot`, einziger roter Test weiterhin `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- untersuchte Produktquellen:
  - `agentZero/code/produkt/bug_meldung.py`, Blob `854c1794bd225c98903a2a85a76b07b048ee5d07`
  - `agentZero/code/produkt/terminal_gateway.py`, Blob `29afc2e7755a0fc6bffc7a3f48680e90ec601e59`
- keine Produktmutation, kein Training, kein Whole-Agent-/Bewusstseinsclaim

## 1. Neues beobachtetes Gen247-Delta

Zwischen Gen246 und Gen247 waechst der exportierte UnifiedDB-Rebuild von `131` auf `132` Tabellen. Die neue Tabelle ist:

`eos_bug_hypothesen`

Schema:

- `bug_id`
- `user_id`
- `ts`
- `beschreibung`
- `wo`
- `status = OFFEN | REPRODUZIERT | WIDERLEGT | BEHOBEN`
- `befund`

Die Tabelle ist in Gen246 noch nicht materialisiert, in Gen247 aber im kanonisch exportierten DB-Schema vorhanden. Das beweist die Materialisierung des Bug-Hypothesenkanals im Live-DB-Schema. Es beweist **nicht**, dass bereits eine echte Nutzer-Bugmeldung existiert: `sicherstellen()` erzeugt die Tabelle auch bei Lese-/Architektenzugriffen.

Status:

- Tabelle neu materialisiert: `OBSERVED_AT_SCHEMA_DELTA`
- reale Bug-Hypothesen-Zeile: `NOT_EXPORTED / UNRESOLVED`

## 2. Positive Architekturgrenze: Nutzer koennen Closure nicht ueber HTTP faelschen

`terminal_gateway.py` bietet fuer den Bugkanal nur:

- `POST /api/bug` — neue Meldung
- `GET /api/bug` — eigene Meldungen lesen
- `GET /api/bug/{bug_id}` — eigene Meldung lesen

Der HTTP-Pfad bietet bewusst **keinen** Writer fuer `status` oder `befund`. Die Benutzeridentitaet wird aus dem verifizierten Clerk-Kontext gebunden und nicht aus dem Request-Body uebernommen.

Damit ist folgende einfache Gegenhypothese nicht gestuetzt:

`a human can self-certify REPRODUZIERT/BEHOBEN through the public bug endpoint`.

Status: `HTTP_CLOSURE_AUTHORITY_SEPARATED_AT_SOURCE`.

## 3. Neuer epistemischer Rand: Current-State-Closure ist staerker als ihr API-Beleg

Die host-/architektseitige Funktion

`status_setzen(db, bug_id, status, befund=None)`

prueft nur:

- `status` liegt in der Enum;
- `bug_id` existiert.

Sie prueft **nicht**:

- den bisherigen Status;
- eine erlaubte Transition;
- dass `REPRODUZIERT`, `WIDERLEGT` oder `BEHOBEN` einen neuen nicht-leeren gemessenen Befund besitzen;
- eine Receipt-/Messungs-ID;
- den Architekt-/Executor-/Source-Stand, der die Entscheidung erzeugte.

Der Updatepfad lautet sinngemaess:

`SET status=?, befund=COALESCE(neuer_befund, alter_befund)`.

Daraus sind auf API-Ebene unter anderem folgende Zustaende legal:

1. `OFFEN -> BEHOBEN` mit `befund=NULL`;
2. `OFFEN -> WIDERLEGT` mit `befund=NULL`;
3. `BEHOBEN -> OFFEN` unter Beibehaltung eines alten Befunds;
4. `WIDERLEGT -> REPRODUZIERT` unter Beibehaltung eines Befunds, der semantisch zur vorherigen Widerlegung gehoeren kann;
5. beliebige weitere Statuswechsel ohne erhaltene Transition-Historie.

Das ist **kein Beweis**, dass der reale Architekt diese schlechten Sequenzen ausfuehrt. Es ist ein source-confirmed Admission-/Metrologie-Rand: Der kanonische API-Vertrag selbst verhindert sie nicht.

Klassifikation:

`HYPOTHESIS_CLOSURE_STATE_UNDERCONSTRAINED_AT_SOURCE`.

## 4. Warum das mehr ist als ein normaler State-Machine-Bug

`eos_bug_hypothesen` ist laut Modul explizit der Eingang des inneren Architekten. Die Statuswerte tragen deshalb epistemische Bedeutung:

- `REPRODUZIERT` behauptet erfolgreiche Reproduktion;
- `WIDERLEGT` behauptet Gegenbeleg;
- `BEHOBEN` behauptet geschlossene Ursache/Reparatur.

Wenn solche Klassen ohne gebundenen Messbeleg gesetzt werden koennen, ist das Problem nicht nur Workflow-Korrektheit, sondern **Evidence Admission**.

Harte Trennung:

`STATUS_ENUM_VALID != EPISTEMIC_CLAIM_VALID`.

und:

`CURRENT_HYPOTHESIS_STATE != HYPOTHESIS_EVENT_HISTORY`.

Das ist strukturell verwandt mit dem in Gen245 beobachteten Human-Feedback-Current-State-Problem, aber nicht dieselbe Evidenz: Hier geht es um wissenschaftliche Hypothesen-/Bug-Closure statt Nutzer-Rating.

## 5. Cross-Domain-Fusion

W3C PROV trennt Entity, Activity, Derivation, Revision und Invalidation. Methodischer Transfer auf Zero:

- eine Bug-Hypothese ist eine provenance-tragende Entity;
- Reproduktion/Widerlegung/Behebung sind Activities bzw. revisionsartige Ereignisse;
- der aktuelle Status ist eine abgeleitete Sicht;
- eine Revision sollte die vorherige Evidenz nicht unsichtbar ueberschreiben.

Das stuetzt kein konkretes Produktdesign als einzig richtige Loesung. Es stuetzt aber die Forschungsregel, Closure als Ereignis + Ableitung statt bloss mutablem Label zu messen.

## 6. Neue Forschungsinvarianten

### F-BUG-1 — Terminale epistemische Klassen brauchen Evidenz

`REPRODUZIERT | WIDERLEGT | BEHOBEN => nonempty measured finding + addressable evidence receipt`.

### F-BUG-2 — Transitionen muessen typisiert sein

Mindestens:

- `OFFEN -> REPRODUZIERT`
- `OFFEN -> WIDERLEGT`
- `REPRODUZIERT -> BEHOBEN`

Andere Pfade brauchen eine explizite Reopen-/Revision-Semantik statt stiller Mutation.

### F-BUG-3 — Alte Befunde duerfen nicht semantisch auf neue Status "durchrutschen"

`COALESCE(new_finding, old_finding)` ist nur sicher, wenn Status und Befund dieselbe Evidenzgeneration repraesentieren. Bei Revision muss entweder ein neues Finding gebunden oder die alte Evidence-Version explizit referenziert werden.

### F-BUG-4 — Current State ist Projektion, nicht Ledger

Statuswechsel brauchen append-only History oder einen aequivalenten revisionsfesten Derivation-Receipt.

## 7. Instrumentkandidat: BUG_HYPOTHESIS_CLOSURE_RECEIPT/v1

Pro Transition:

- `transition_id`
- `bug_id`
- `from_status`
- `to_status`
- `ts`
- `actor_class = ARCHITECT | SYSTEM | OTHER`
- `actor_version`
- `source_generation`
- `finding_text_hash`
- `finding_present`
- `evidence_receipt_ids`
- `reproduction_run_id`, falls anwendbar
- `fix_commit_or_artifact`, falls anwendbar
- `prior_transition_id`
- `verdict = ADMITTED | REJECTED`
- `reason`

Materialisierte Tabelle darf weiter eine schnelle Current-State-Sicht liefern; der Receipt muss die epistemische Historie tragen.

## 8. Billigster Falsifikator

In einer isolierten Temp-DB ohne Produktwirkung:

1. Bug `OFFEN` anlegen.
2. `BEHOBEN` ohne Befund versuchen.
3. `WIDERLEGT` ohne Befund versuchen.
4. `REPRODUZIERT` mit gebundenem Befund setzen.
5. `BEHOBEN` mit zweitem gebundenen Befund setzen.
6. Reopen/Revision versuchen.
7. pruefen, ob jede Transition unveraenderlich rekonstruierbar bleibt.

Aktueller Source-Vertrag sagt fuer Schritte 2/3 voraussichtlich `accepted`, weil kein Evidenzgate existiert. Ein spaeterer gehärteter Vertrag muss fail-closed sein.

## 9. Hypothesen / Gegenhypothesen

### H-BUG1 — Architekt setzt ohnehin immer einen Befund

Moeglich. Dann ist der aktuelle Rand latent und der reale Fehlerrate nahe null.

Falsifikator: alle existierenden/kommenden `eos_bug_hypothesen`-Transitions mit Architekt-Logs/Receipts joinen; terminale Klassen ohne frischen Messbeleg = 0.

### H-BUG2 — Mutable Current-State reicht, weil Bauverlauf/Logs Historie retten

Moeglich, falls ein exakter, verlustfreier und adressierbarer externer Ledger jede Transition bindet.

Falsifikator: fuer jede Statusaenderung existiert ein eindeutiger externer Event-/Derivation-Receipt mit vorherigem und neuem Zustand. Ein allgemeines Bauprotokoll ohne `bug_id`-/Transition-Bindung reicht nicht.

### H-BUG3 — `befund` darf absichtlich optional sein

Moeglich fuer `OFFEN`. Fuer `REPRODUZIERT/WIDERLEGT/BEHOBEN` wuerde dies aber die Modulsemantik "gemessener Befund" schwaechen. Ein expliziter Owner-/Schema-Vertrag koennte diese Interpretation superseden; aktuell ist kein solcher Vertrag im gebundenen Source sichtbar.

## 10. Promotionsstatus

- Gen247 neue Tabelle `eos_bug_hypothesen`: `OBSERVED_AT_SCHEMA_DELTA`
- Bugkanal Produktmodul: `SOURCE_CONFIRMED`
- HTTP darf nur melden/lesen, nicht Closure schreiben: `SOURCE_CONFIRMED`
- `status_setzen` erlaubt terminale Status ohne neuen Befund: `SOURCE_CONFIRMED`
- Transition-Graph im API-Vertrag: `NOT_ENFORCED`
- append-only Hypothesen-Transition-Ledger: `NOT_OBSERVED`
- reale fehlerhafte Closure im Livebetrieb: `NOT_PROVEN`
- `BUG_HYPOTHESIS_CLOSURE_RECEIPT/v1`: `PROMOTED_TO_INSTRUMENT_CANDIDATE`

## 11. Wichtigstes Ergebnis

Gen247 fuehrt nicht nur eine neue Tabelle ein. Es oeffnet einen neuen Forschungsregelkreis zwischen Mensch und innerem Architekten. Dessen Eingangsgrenze ist sauberer als der erste Blick vermuten laesst: Menschen koennen ueber HTTP keine eigene Reproduktion oder Behebung zertifizieren. Aber die interne Closure-API ist epistemisch noch zu schwach, weil sie Status, Messbefund und Revision nicht hart aneinander bindet.

Kernregel:

> **Eine Hypothese ist erst dann reproduziert, widerlegt oder behoben, wenn nicht nur das Label gesetzt wurde, sondern der Uebergang selbst mit adressierbarer Evidenz gebunden ist.**
