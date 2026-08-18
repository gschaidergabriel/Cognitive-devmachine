# Generation 33 — Messintegritaet vor Promotion

Zeitpunkt: 2026-08-18T07:45:40Z
Kanonischer Export-Head: `c304b9f902041293c9f422c17ed70eca9aff1124`

## Beobachtungen

1. Generation 33 exportiert die UnifiedDB-Schemaoberflaeche erstmals vollstaendig: 87/87 Tabellen wurden erzeugt; der vorherige `fts_index_artikel_config already exists`-Fehler ist damit im Exportpfad geschlossen.
2. Laufzeitzaehler wachsen real weiter: 45 Turns, 22 Causal Episodes, 23 Retrieval Episodes und 23 Workspace Episodes im Manifest; `active_turns.jsonl` ist erstmals nicht leer.
3. Zielmatrix: 22 erfuellt, 6 offen, 1 zurueckgestellt. Noch offen sind insbesondere vierter Clay-Dienst, MCP-Werkzeugflaeche, Retrieval-Lernen/Wegehierarchie, Provider-Erreichbarkeit und Uebersetzer.
4. Kritische Messinkonsistenz: `agentZero/tests/letzter-lauf.json` meldet am selben Export-Head `478 gruen / 15 rot`, waehrend `agentZero/ZIELE.md` `479 gruen / 14 rot` meldet. Beide Dateien werden automatisch erzeugt. Ohne gemeinsame Run-ID/Receipt darf keine der beiden Zahlen als alleinige Promotion-Wahrheit dienen.
5. Die 15 roten Tests in `letzter-lauf.json` liegen weiterhin an Kerninvarianten: Autonomy activation, causal credit, EntityOS artifact authority, EffectGate/inference/re-ingest, memory privacy, state authority, service lifecycle sowie terminal timeout/auth lease.
6. Retrieval-Lernen bleibt trotz mehr Verkehr bei `durable_memory=0`, `retrieval_entrypoint_policy=0`, `retrieval_feedback=0`.

## Kausale Einordnung

Der groesste neue Fortschritt von Gen 33 ist nicht eine hoeher bewertete Gesamtreife, sondern eine bessere Messbasis: der UnifiedDB-Schemaexport ist jetzt reproduzierbar vollstaendig. Gleichzeitig zeigt die Testzaehler-Divergenz, dass die Acceptance-Metrologie noch keine einzige atomare Quelle besitzt. Eine Verbesserung von 478/15 auf 479/14 kann real sein, kann aber auch aus zwei verschieden getakteten Messlaeufen stammen.

## Falsifizierbare Hypothese

H1: `letzter-lauf.json` und `ZIELE.md` referenzieren unterschiedliche Testlauf-Zeitpunkte bzw. unterschiedliche Run-Receipts. Wenn beide Generatoren auf dieselbe unveraenderliche `test_run_id` + Source-SHA + Ergebnis-Digest gebunden werden, verschwindet die 478/15-vs-479/14-Divergenz.

Gegenhypothese H0: Beide Dateien beziehen sich bereits auf denselben Testlauf; dann ist mindestens einer der Generatoren/Zaehler semantisch fehlerhaft.

## Naechstes hoechstwertiges Messgeraet

`TEST_RECEIPT_LEDGER/v1` als einzige atomare Quelle pro Testlauf:

- `test_run_id`
- UTC start/end
- exact source commit + tree
- suite selection digest
- green/red/skip counts
- ordered failing-test IDs
- runner/executor identity
- result digest

`ZIELE.md`, `letzter-lauf.json` und weitere Dashboards duerfen danach nur noch aus demselben Receipt rendern. Bei fehlender oder widerspruechlicher Receipt-Bindung: `UNRESOLVED`, niemals Promotion-Credit.

## Promotionsregel

Generation 33 erhaelt fuer den reparierten Schemaexport Messinstrument-Credit. Sie erhaelt keinen zusaetzlichen Whole-EntityOS-/Whole-Clay-Machine-Credit aus den widerspruechlichen 478/15 bzw. 479/14-Testzaehlern, bis die Test-Receipt-Identitaet atomar gebunden ist.

## Aktueller Frontier

1. TEST_RECEIPT_LEDGER/v1 implementieren bzw. vorhandene Run-ID-Bindung ausweisen.
2. Gen-33-Testlauf einmal aus derselben Receipt-Quelle in `letzter-lauf.json` und `ZIELE.md` rendern.
3. Erst dann den echten Red-Delta gegen Gen 32 bestimmen.
4. Danach die verbleibenden roten Kerninvarianten reparieren, ohne Tests abzuschwaechen.
5. Parallel Retrieval-Lernen und MCP-Werkzeugerreichbarkeit weiter messen; beide stehen trotz zunehmender Nutzung noch auf 0/offen.
