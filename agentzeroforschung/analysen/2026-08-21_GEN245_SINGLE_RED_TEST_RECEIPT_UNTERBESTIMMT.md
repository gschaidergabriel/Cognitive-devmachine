# Generation 245 — Der letzte rote Test ist derzeit nicht klassifizierbar

## BIND

- Research-`main` unmittelbar vor dieser Analyse beobachtet bei `4e1f71981fcdd4c6a65beb5977e07bf93442afcb`.
- letzter AgentZero-Voll-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`, Generation `245`, Exportzeit `2026-08-21T14:07:17Z`.
- aktueller exportierter Teststand: `agentZero/tests/letzter-lauf.json`, erzeugt `2026-08-21T14:08:00Z`, `1066 gruen / 1 rot`.
- einziger roter Test: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`.
- im Teststand angegebene Source-ID: nur der Kurzbezeichner `ab185bcd1`.

Diese Analyse veraendert keinen Test und keine Produktbytes. Sie klassifiziert nur, was aus dem vorhandenen Messstand belastbar folgt.

## 1. Beobachtete Evidenz

Der aktuelle Research-Baum enthaelt den betreffenden Test unter `the artefact/tests/test_runtime_adapters.py`. Er verlangt fuer `ClaudeCodeInference` gleichzeitig:

- `-p`/einmalige Inferenz;
- `--max-turns 1`;
- `--tools ""`;
- `--permission-mode plan`;
- `--strict-mcp-config`;
- `--no-session-persistence`;
- JSON-Schema-Ausgabe;
- nur `entityos.exec` oder `state.noop` als Effect-Intent;
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1`;
- eine Environment-Allowlist, in der Claude-Auth erhalten bleibt, Clerk-/DB-Geheimnisse aber nicht an den Cognition-Subprozess weitergegeben werden;
- keine Shell-Interpretation des Observation-Strings.

Der exportierte Live-Produktquelltext `agentZero/code/produkt/adapters.py` und der kanonische Research-Pfad `the artefact/clayverse/adapters.py` tragen aktuell denselben Git-Blob `6dfaa81d0ad0fb57acb1dcc69d45009538b8c507` und implementieren genau diese tool-less/ephemeral/schema/env-isolated Grenze.

Auch `agentZero/code/produkt/inference_protocol.py` passt zur vom Test erwarteten `respond`/`request_effect`-Normalisierung.

Damit ist folgende einfache Erklaerung **nicht** ausreichend:

> "Der Test ist rot, weil der aktuelle Adapter absichtlich Tools erlaubt."

Der aktuell exportierte `ClaudeCodeInference`-Adapter erlaubt in diesem Pfad gerade keine Tools.

## 2. Wichtige Pfadtrennung: interaktiver Zero != ClaudeCodeInference-Adapter

Der aktuelle AgentZero-Zielstand beschreibt zugleich einen interaktiven Zero-Pfad mit freigegebenen nativen Claude-Werkzeugen und einer duennen PreToolUse-Schranke fuer irreparable Bereiche.

Das ist kein automatischer Widerspruch zum roten Test. Es sind zwei unterschiedliche Semantikpfade:

1. interaktiver Zero / Produktterminal: Werkzeuggebrauch kann absichtlich zugelassen sein;
2. `ClaudeCodeInference`: begrenzter Inferenzadapter, dessen Source-Vertrag weiterhin explizit tool-less ist und Effect-Intent nur an EffectGate weiterreichen soll.

Deshalb darf die spaetere Native-Tools-Entscheidung den roten Adaptertest **nicht ohne direkten Source-/Owner-Beleg** zu einem "stale test" degradieren.

## 3. Der eigentliche neue Befund: der Test-Receipt ist unterbestimmt

`letzter-lauf.json` nennt nur:

- `1066/1`;
- den Namen des roten Tests;
- den Kurzbezeichner `ab185bcd1`.

Der Kurzbezeichner `ab185bcd1` liess sich ueber die verbundenen GitHub-Suchen weder im Research-Repo noch in `gschaidergabriel/Dr.-Unterweger` auf einen vollstaendigen Commit aufloesen.

Der Export enthaelt ausserdem **nicht**:

- volle Source-Commit-ID plus Tree-ID;
- Blob-ID des tatsaechlich ausgefuehrten `tests/test_runtime_adapters.py`;
- Blob-ID des tatsaechlich importierten `clayverse/adapters.py` im Testlauf;
- welche einzelne Assertion im zusammengesetzten Test fehlschlug;
- Exception-/Failure-Signatur oder deren Digest;
- Executor-/Python-/pytest-/Claude-CLI-Identitaet fuer den Lauf;
- Suite-Digest bzw. eine unveraenderliche Run-ID.

Damit kann aus dem aktuellen Forschungs-Export **nicht diskriminiert** werden zwischen:

- echtem Adapter-Semantikfehler;
- anderem/nicht exportiertem Teststand;
- Source-Test-Drift;
- Executor-/Dependency-/CLI-Drift;
- einem spaeter reparierten Adapter bei noch altem Test-Receipt;
- einem Fehler in nur einem der vielen im selben Test gebuendelten Invarianten.

Status:

`PERSISTENT_SINGLE_RED = OBSERVED`

aber

`FAILURE_MECHANISM = UNDERDETERMINED_FROM_EXPORTED_RECEIPT`.

## 4. Hypothesen

### H1 — Source/Test-Identity-Drift

Der ausgefuehrte Test oder Adapter hinter `ab185bcd1` ist nicht byte-identisch zum heute exportierten/canonically visible Paar.

**Falsifikator:** Voll-SHA/Tree und beide Git-Blob-IDs des ausgefuehrten Laufs stimmen mit dem sichtbaren Stand ueberein.

### H2 — Environment-/Dependency-Drift

Die Source ist identisch, aber eine Laufzeit-/Dependency-Eigenschaft verursacht den roten Test.

**Falsifikator:** Derselbe exakt gebundene Source-Tree laeuft mit dokumentierter Executor-/Dependency-Identitaet reproduzierbar gruen; oder der Failure zeigt rein eine Source-Assertion.

### H3 — Echter zusammengesetzter Adapterdefekt

Mindestens eine der Invarianten Toollessness, Ephemerality, strukturierte Ausgabe oder Environment-Isolation ist im tatsaechlich ausgefuehrten Pfad verletzt.

**Falsifikator:** Ein exakter Einzeltestlauf publiziert jede relevante Assertion/Teilmetrik und alle sind gruen.

### H4 — Testvertrag wurde absichtlich superseded

Der Owner hat auch fuer `ClaudeCodeInference` die tool-less Grenze aufgehoben.

Diese Hypothese ist gegenwaertig schwach, weil der aktuelle Adapter selbst weiterhin explizit `Tool-less Claude Code cognition boundary` dokumentiert und `--tools ""` setzt.

**Falsifikator:** aktueller Owner-/Source-Vertrag fordert fuer genau diesen Adapter direkte native Tool-Autoritaet.

## 5. Messinstrument, das jetzt fehlt

### `TEST_RECEIPT_LEDGER/v1`

Jeder Suite-Lauf sollte unveraenderlich binden:

- `run_id`;
- voller Source-Commit und Tree;
- Suite-/Testdatei-Digest;
- Digests der direkt untersuchten Produktmodule;
- Executor-Identitaet;
- Python-/pytest-/relevante Runtime-Versionen;
- geordnete Testliste;
- pro rotem Test `failure_phase`, `failure_signature_sha256`, failing assertion/node id;
- stdout/stderr nur redigiert bzw. als Digest/Bytezahl;
- Start/Ende und Exit-Code;
- Result-Digest ueber den gesamten Receipt.

`letzter-lauf.json` und `ZIELE.md` sollten dann aus exakt derselben unveraenderlichen Run-ID rendern, statt nur Zaehler plus Kurz-SHA zu tragen.

Der wichtigste Zusatz fuer zusammengesetzte Tests ist die **Failure-Phase**. Ein Testname wie `toolless_ephemeral_structured_and_env_isolated` kodiert vier bis sechs verschiedene Mechanismen in einem einzigen roten Bit. Ohne failing assertion ist dieses Bit diagnostisch zu breit.

## 6. Billigster naechster Diskriminator

Vor jeder Test- oder Produktmutation:

1. den tatsaechlichen Source-Tree hinter dem naechsten Lauf voll binden;
2. genau den einzelnen roten Test erneut ausfuehren;
3. Adapter-Blob + Test-Blob + Executor-Identitaet speichern;
4. failing assertion/Phase als redigierte Signatur persistieren;
5. erst dann klassifizieren als `SOURCE_DEFECT | TEST_STALE | ENVIRONMENT_DRIFT | FLAKE | FIXED`;
6. danach erst die volle Suite erneut laufen lassen.

Keinen Test abschwaechen, um `1067/0` zu erhalten. Ein gruener Zaehler ohne Mechanismenbindung waere weniger Information als das aktuelle ehrliche Rot.

## 7. Fusion / Forschungsstatus

- `1066 gruen / 1 rot`: `OBSERVED`.
- einzelner roter Testname: `OBSERVED`.
- aktueller exportierter Adapter-Blob == aktueller Research-Adapter-Blob: `OBSERVED_SOURCE_EQUIVALENCE_AT_MODULE_SCOPE`.
- aktueller sichtbarer Adaptervertrag ist tool-less: `SOURCE_CONFIRMED`.
- interaktiver Zero darf native Werkzeuge haben: separater Pfad; kein Beleg fuer Supersession dieses Adapters.
- `ab185bcd1` als voll gebundene Source-Identitaet: `UNRESOLVED`.
- konkrete Ursache des roten Tests: `UNDERDETERMINED`.
- Test als veraltet: `NOT_PROVEN`.
- Adapter als defekt: `NOT_PROVEN`.
- Testreceipt-Metrologie: `INSUFFICIENT_FOR_CAUSAL_FAILURE_CLASSIFICATION`.

## 8. Allgemeine Lehre

Ein Testzaehler ist Zustand, kein Ursachenbeleg.

`red test name + short source id != reproducible failure mechanism`

Das ist dieselbe Provenienzklasse wie beim Human-Feedback-Current-State: materialisierte Zusammenfassungen duerfen fuer Bedienung und Status nuetzlich sein, aber wissenschaftliche Kausalzuordnung braucht die adressierbare Ereignis-/Source-Linie.
