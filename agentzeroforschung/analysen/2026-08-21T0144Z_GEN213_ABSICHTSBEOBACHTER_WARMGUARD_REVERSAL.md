# Generation 213 — Absichtsbeobachter, Echo-Sperre und Warmguard-Gegenmessung

## Gebundener Export

- AgentZero-Export: `b2f47c88f860ea888ff5a3803a54eb7abb106974`
- Generation: 213
- direkter Test-Receipt: `dd90b24d4`, erzeugt 2026-08-21T01:41:42Z
- Tests: 747 gruen / 1 rot
- roter Frontier: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Forschungsrouting: clayresearch, frank, gwt, emergenz, claycode, hyperposition, claygraph, unifieddb, harness
- Training: keines

## Substanzielle Mechanismusdeltas

1. **Werkzeugspur fuer Kalt- und Warmweg.** Der Kaltweg nutzt jetzt `stream-json`; beide Pfade liefern Werkzeugliste, Aussenwirkung und Fremdtextmarker. Neue Gedächtniseinträge können damit an die Werkzeugspur ihres Entstehungszugs gebunden werden. Das ist ein echter Provenienzmechanismus, noch kein Nachweis korrekter Attribution.
2. **Post-hoc-Absichtsbeobachter.** `absicht.py` protokolliert Verdacht, wenn nach aussen wirkende Werkzeuge nicht angekündigt waren oder bei einer Nachricht mit weniger als zwei Inhaltswörtern liefen. Er blockiert ausdrücklich nichts.
3. **Echo-Sperre im GWT-Wettbewerb.** Ein Bewerber braucht `eigenanteil >= 0.30`; damit soll ein früherer, wortgleicher Nutzerzug nicht länger echte Antwortträger über die relative Schwelle verdrängen.
4. **Breiter Arbeitsraum ist nur ein Vergleichsarm.** Gedächtnis, Verlauf, Kollisionen und Teile des Selbstbilds können gemeinsam konkurrieren, aber kanonische Vorgabe bleibt `CLAYVERSE_ARBEITSRAUM=korpus`; `CLAYVERSE_RAHMEN=voll` bleibt ebenfalls Vorgabe. Der globale Engpass ist damit nicht kanonisch aktiviert.
5. **Gen-212-Warmpool-Bremse verworfen.** Die neue Quellkommentierung berichtet 23,9 s mit Bremse gegen 7,8 s ohne Bremse und 6/11 gegen 10/12 Warmtreffer. Die Zähler bleiben, der Schalter ist aus. Das ist wertvolle Gegenevidenz zum Gen-212-Mechanismuscredit, aber ohne atomaren Rohreceipt noch kein kausaler Performancebeleg.
6. **Zaun erweitert.** Zwei konkrete private Env-Dateien und verändernde SQL-Verben einschließlich UPDATE/REPLACE/ALTER/ATTACH werden erkannt. Der Code benennt ehrlich den verbleibenden Interpreter-Bypass über ein vorher geschriebenes Skript.

## Quellseitig harter Gegenbefund: Native-Announcement Blindness

`selected_tools` wird in `pipeline.py` auf Namen mit Präfix `mcp__clayverse__` reduziert. Genau diese Liste wird später an `absicht.pruefen(..., angekuendigt=selected_tools)` übergeben. `_AUSSENWIRKUNG` enthält dagegen auch native Werkzeuge wie `Write`, `Edit`, `Bash`, `WebSearch` und `WebFetch`.

Daraus folgt deterministisch: **Jede native Aussenwirkung ist für diesen Beobachter per Konstruktion „unangekündigt“**, auch wenn die Vorstufe sie semantisch verlangt oder Zero sie zur ausdrücklich erbetenen Aufgabe benötigt. Der neue Zähler misst damit mindestens teilweise einen Namensraumfehler, nicht Absichtsabweichung.

Die Literaturvorlage trägt diesen Schluss nicht: LlamaFirewall beschreibt Agent Alignment Checks als experimentellen Echtzeit-Auditor der Handlungskette gegen Zielabweichung und als präventive letzte Verteidigungsschicht. Gen 213 protokolliert dagegen nach erfolgter Wirkung und vergleicht Werkzeugnamen aus nicht deckungsgleichen Mengen. Quelle: https://arxiv.org/abs/2505.03574

## Hypothesen und Gegenhypothesen

### H1 — Native-Announcement Blindness

**Hypothese:** Der Anteil `unangekuendigt` nähert sich bei nativen Wirkungen 100 %, unabhängig von echter Zieltreue.

**Gegenhypothese:** Ein nicht sichtbarer Upstream-Pfad liefert native Namen doch in `selected_tools`.

**Falsifikator `INTENT_NAMESPACE_MATRIX/v1`:** 40 gepaarte Züge: je 10 explizit erbetene und nicht erbetene Write-, Bash-, WebSearch- und MCP-Wirkungen. Receipt pro Zug: rohe Vorstufen-`tool_selection`, gefilterte `selected_tools`, ausgeführte Spur, Frage, Urteil. Metriken: TPR/FPR getrennt nach Namespace. H1 fällt, wenn explizit erbetene native Wirkungen überwiegend nicht als unangekündigt markiert werden.

### H2 — Post-hoc Safety Substitution

**Hypothese:** Der neue Beobachter verbessert Auditierbarkeit, aber nicht Schutz; eine unerbetene irreversible Wirkung wird vollständig ausgeführt, bevor `gw_absicht` entsteht.

**Gegenhypothese:** Der dünne Zaun oder EffectGate blockiert alle relevanten Schäden unabhängig vom Beobachter.

**Falsifikator `VERIFY_BEFORE_COMMIT_ABLATION/v1`:** reversible Sandboxwirkung mit Kontrollmarker; Arme: Beobachter aus, nur post-hoc, pre-commit deny/confirm. Prüfe Zustand vor/nach Handlung, Logzeitpunkt und Blockquote. Kein Produktionsziel und keine Geheimnisse verwenden.

### H3 — Greeting-Length Confound

**Hypothese:** `len(_worte(frage)) < 2` trennt Sachauftrag und Smalltalk nicht. Kurze Imperative wie „Datei löschen“ können unmarkiert bleiben; längere harmlose Nachrichten können markiert werden, sobald eine normale externe Lesehandlung stattfindet.

**Gegenhypothese:** Die Vorstufe verhindert diese Fälle vollständig.

**Falsifikator:** deutschsprachiger Held-out-Satz von mindestens 100 Paaren, stratifiziert nach Wortzahl, Imperativ, expliziter Wirkungserlaubnis und Tooltyp; keine Kalibrierung auf dem Testsatz.

### H4 — Echo-Sperre vs. Contribution Inflation

**Hypothese:** `eigenanteil` entfernt wortgleiche Frage-Echos, bevorzugt aber lange Kandidaten mit vielen beliebigen Zusatzwörtern. Dadurch kann irrelevanter Wortreichtum die Hürde leichter nehmen als ein knapper, präziser Beleg.

**Gegenhypothese:** Relevanz-, Boden- und Relativhürde verhindern diesen Leakage-Pfad.

**Falsifikator `ECHO_CONTRIBUTION_FACTORIAL/v1`:** identische zwei Frageworttreffer, faktoriell variiert: korrekte Antwort, irrelevante Zusatzwörter, Länge, Quelle, Position. Miss Zulassung, Auswahl, Antwortkorrektheit und Quellenstützung. Echo-Sperre erhält Credit nur bei verbessertem Held-out-Recall ohne FPR-Anstieg.

### H5 — Guard-Reversal ist Lastverschiebung, nicht allgemeines Gesetz

**Hypothese:** Die Bremse verschlechtert den getesteten sequentiellen Lastfall durch Pool-Aushungerung; bei parallelen Sitzungen oder längeren Zügen kann ungebremstes Refill weiterhin Tail-Latenz und Erwartungsfeld-Zombies erhöhen.

**Gegenhypothese:** Ungebremstes Refill dominiert in allen realistischen Lastprofilen.

**Falsifikator `WARM_REFILL_POLICY_MATRIX/v2`:** identischer Source und feste Prompts, 1/2/4 gleichzeitige Sessions, kurze/lange Züge, Bremse aus/20-s-Notausgang/adaptive Queue-Policy; p50/p95/p99, Warmhit, CPU, runnable Prozesse, late Futures. Raw rows, Prozess-IDs und monotone Zeitpunkte binden.

## Unveränderte offene Negativergebnisse

- Session-Prompt-Datei-Alias bleibt unverändert: Cache-Key `(user, session)`, physisch weiterhin `/tmp/zero-warm-sys-{user}.md`. Kein Fix-Credit.
- Der 2,5-s-`Future.result`-Deckel beendet laufende Futures nicht. Kein Arbeitsabbau-Credit.
- Breiter GWT-Arbeitsraum und gekürzter Identitätsrahmen sind nicht kanonische Defaults; Gleichstand der bisherigen Arme belegt keinen Vorteil.
- Die 5/8-vs-1/8-vs-0/8-Kausalzahl, AUROC 0,88 und die neue Warmguard-Gegenmessung besitzen im Export keinen gemeinsam gebundenen Rohmatrix-/Executor-Receipt.
- `gw_absicht`, GWT-Buchung und Provenienzschreibungen schlucken DB-Fehler; fehlende Zeilen sind daher nicht von „kein Ereignis“ unterscheidbar.
- BASE/Whole bleibt NOT_PASS; keine Promotion, kein Training und keine Harness-Mutation behauptet.

## Routing

- **claycode / harness / frank:** `INTENT_NAMESPACE_MATRIX/v1`, `VERIFY_BEFORE_COMMIT_ABLATION/v1`, Adapter-Frontier getrennt halten.
- **gwt / emergenz / clayresearch:** `ECHO_CONTRIBUTION_FACTORIAL/v1`, kanonisch eng gegen weit, Modellwahl gegen mechanisches Nachziehen.
- **unifieddb / claygraph:** fehlersichtbare, idempotente Receipts für `gw_absicht`, Werkzeugspur, Quellmarke und Outcome; native Namespace-Kanonisierung.
- **hyperposition:** globaler Channel-Lesion-Test einschließlich Profil, Identitätsrest, Erwartungsfeld und Titelkanal.
- **warm/harness:** `WARM_REFILL_POLICY_MATRIX/v2` plus bestehender `WARM_SESSION_PROMPT_IDENTITY_RECEIPT/v2`.

Ausführung dieser Impulse ist offen. Promotion oder PASS werden nicht behauptet.
