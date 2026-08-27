# AgentZeroForschung — Inventur und Gesamtueberblick

Gebundener AgentZero-Snapshot: `2026-08-18T04:26:41Z`
Gebundener Source-Head vor Forschungswrite: `cf0f0fb63802bcbb1386ce267166f9b5b918ca8a`
Entity Generation: `31`
Quelle des Laufzeitexports: `/var/lib/clay/wiki.db`

## Scope

Diese Inventur erfasst alle aktuell exportierten Datenfamilien und ihre Messrolle. Kleine Datensaetze wurden vollstaendig gelesen; grosse Rolling-Tails, Korpus- und Bauverlaufsdateien wurden ueber Manifest/Index und strukturierte Stichproben inventarisiert. Die Inventur behauptet daher keine semantische Vollauswertung jedes einzelnen Wiki-Artikels oder jedes einzelnen der 700 Commits.

## Bestand

Der aktuelle Export umfasst 34 im Manifest registrierte Artefakte. Exportdauer: 28,29 s. Der Redaktionsfilter griff 1x.

UnifiedDB-Metrologie:
- 109 Tabellen
- 14.284 Artikel
- 12.490 Anreicherungen
- 325.357 Datei-Records
- 458.937 Fundorte
- 95.378 Kanten
- 14.235 Graph-Kanten
- 11.640 Graph-Knoten
- 22.567 WM-Lesarten

Direkter Zero-Laufzeitbestand:
- 10 Turn-Zeilen, alle in `session:gabriel`; Andreas: 0
- 5 Kausalepisoden
- 5 Workspace-Episoden
- 1 verifizierter Effect
- 39 Checkpoints
- 0 aktive Turns und 0 Leases im Snapshot
- 5 Retrieval-Episoden
- 0 gelernte Entry-Points
- 0 Retrieval-Feedback
- 0 Durable-Memory-Records

## Datenfamilien und Messrolle

### chat/
Vollstaendige Turnspur der bisher beobachteten Gabriel-Interaktion. Die zehn Zeilen decken Generationen 16, 28 und 29 ab. Zwei UserPromptSubmit-Pfade endeten als `TURN_ABORTED:user_prompt_post_admission_failure`; spaetere Gen-29-Turns liefen durch. Der letzte beobachtete Effect-Test liefert einen verifizierten `state.noop`-Outcome mit identischer causal_id zum Turn.

Wichtige Grenze: Der aktuelle Wurzelzustand ist Generation 31, aber es gibt im Export noch keinen direkten Chat-/Verhaltenszug aus Generation 31. Aussagen ueber aktuelles Gen-31-Verhalten duerfen deshalb nicht einfach aus Gen 29 extrapoliert werden.

### kognition/
Die 5 Workspace-Episoden enthalten je dieselben drei Alternativen `respond`, `request_effect`, `defer_effect`. Beobachtet: 3 COMPLETED, 2 ABORTED. Selektion: zweimal `respond`, zweimal `defer_effect`, einmal `request_effect`.

Die 5 causal_episodes sind jeweils re-entered. Der letzte bindet den verifizierten Effect an dieselbe Episode/causal_id.

39 Checkpoints bilden eine starke Restart-/Boot-Zeitreihe. Im aktuellen Export sind 30 `boot`- und 9 `shutdown`-Eintraege sichtbar. Mehrere Boot-Cluster liegen sekundenweise dicht beieinander; das ist zunaechst Entwicklungs-/Restart-Churn und kein Beweis fuer Laufzeitinstabilitaet.

### abruf/
Alle 5 beobachteten Retrieval-Episoden laufen unter `SHADOW`, Policy v1, Status `UNKNOWN`. In allen 5 Episoden wurden 0 Zeichen, 0 selected_memory_ids und 0 entry_keys ausgewaehlt. Policy-Lernen, Feedback und Durable Memory stehen noch auf 0.

Damit existiert eine implementierte Retrieval-Messspur, aber noch keine empirische Lernkurve. `ZIELE.md` meldet zugleich einen erfolgreichen 15-Treffer-Probeabruf und 11/11 Tests fuer Abfragesensitivitaet. Das ist kein Widerspruch, sondern eine wichtige Trennung: Capability-/Testnachweis ist nicht dasselbe wie beobachtete Nutzung in den bisher exportierten Zero-Turns.

### zustand/
Zwei kanonische Nutzer (`gabriel`, `andreas`) mit `rights=equal`, zwei dauerhafte Sessions, beide auf Generation 31. `meta.json` bindet kanonische Identitaet v3 an UnifiedDB.

Die exportierte Graphprojektion ist derzeit extrem klein: 5 Knoten, alle causal_episode, und 0 exportierte Kanten. Das darf nicht mit dem gesamten ClayGraph verwechselt werden, denn die UnifiedDB-Metrologie meldet gleichzeitig 11.640 Graph-Knoten und 14.235 Graph-Kanten. `zustand/graph_*` ist damit eine Teilprojektion/anderes Messobjekt.

### karten/
Persistente Snapshot-Zeitreihe. Der Verzeichnisstand zeigt sechs eigentliche Snapshot-JSONs zwischen 04:15:23Z und 04:26:41Z plus einen neuen `.meta.json`-Sidecar fuer den letzten Snapshot.

Auffaellig: `ZIELE.md` meldet 7 Momentaufnahmen. Da der Verzeichnisstand sechs Snapshot-Dateien plus einen Meta-Sidecar zeigt, ist die Hypothese naheliegend, dass der Zaehler den Sidecar als Momentaufnahme mitzaehlt. Status: UNRESOLVED bis der Zaehlercode oder ein weiterer Snapshot dies trennt.

Der neue Meta-Sidecar bindet Herkunft, Generator, SHA, Format und Feldliste, hat aber `wieso=(kein Zweck hinterlegt -- Eintrag in BEDEUTUNG fehlt)` und `gehoert_zu=(unbekannt)`. Die Provenienz-Instrumentierung ist damit vorhanden, semantisch aber noch nicht voll registriert.

### puls/
`puls-letzte500.jsonl`: Rolling Tail 500 von aktuell 4.580 Quellzeilen. In den gelesenen Bereichen ueberwiegt `art=leer` mit delta=0 im ungefaehren Minutenraster; eine Stichprobe zeigt auch `art=fehler` mit `database is locked` und stark erhoehter Laufzeit. Dieser Tail eignet sich fuer Latenz-/Fehler-/Stillstandsanalysen, aber nicht ohne Zensierungsmodell fuer Vollzeitstatistik.

`ereignisse-letzte500.jsonl`: Rolling Tail 500 von 5.613 Ereignissen. Der aktuelle Tail enthaelt u.a. GitHub-Branch-/Push-Ereignisse. Das ist Umgebungs-/Systemaktivitaet, nicht automatisch Zero-Kognition.

`tor-letzte500.jsonl`: 126/126 Quellzeilen, also aktuell vollstaendig. Enthalten sind klassifizierte Tor-Urteile fuer lesende, reversible, Rechte- und unbekannte Befehle sowie ein explizit markierter abgewiesener Befugnisversuch. Diese historische Tor-Schicht ist nicht automatisch identisch mit dem aktuellen Zero-EffectGate-Instrument.

### wiki/
Der Export trennt jetzt:
- `kern.jsonl`: 800 Volltextartikel, in deren Titel der Systemname steht, ca. 1,47 MB
- `umfeld.jsonl`: 2.635 Kontextartikel, Begriff nur im Text; Nachweis statt Volltext, ca. 1,75 MB

Der Index sagt explizit, dass eine reine Volltextsuche 4.202 Artikel / 13,1 MB treffen wuerde und deshalb nicht als Zeros unmittelbares Umfeld exportiert wird. Diese Auswahlregel ist selbst ein relevanter Forschungsfilter und muss bei Korpusstatistiken als Sampling-/Selection-Bias modelliert werden.

### architektur/
466 Architektur-/Aenderungseintraege plus automatisch abgeleitete Laufzeitskizze. Gemessen werden 36 Produktmodule / 7.697 Zeilen, 116 Testdateien, 109 DB-Tabellen und aktuell drei laufende Clay-Dienste (`kern`, `puls`, `wikiarbeit`). Gleichzeitig spricht die Beschreibung noch von "vier Diensten"; `ZIELE.md` markiert "3 von 4 laufen" korrekt als offen.

Die Skizze meldet `(keine ermittelt)` bei Werkzeugen, waehrend der echte Chatdatensatz einen erfolgreichen `mcp__clayverse__request_effect`-Pfad zeigt. `ZIELE.md` fuehrt die Werkzeugflaeche ebenfalls als offen. Das ist ein Instrumenten-/Operationalisierungsunterschied und eine hohe Forschungsprioritaet.

### bauverlauf/
700 Commits aus vier Repos, 198 mit ausgeschriebener Begruendung. Dieser Datensatz ist besonders wertvoll, weil er Intervention, Befund und Reparatur verbindet. Sichtbare Beispiele: Hook/MCP-Schreibvorgaenge landeten zeitweise in einer Shadow-DB statt `wiki.db`; ein Shell-Prefix blockierte Lifecycle-Hooks/MCP; spaetere Commits reparierten diese Pfade. Bauverlauf kann deshalb als historische Interventions-/Failure-Datenbasis benutzt werden.

### tests/
Aktueller Testlauf fuer Commit `94218cedf`: 480 gruen, 12 rot. Die roten Tests clustern in Autonomy activation, causal credit, EntityOS artifact authority/final acceptance, inference/effect/re-ingest, service shutdown/DB, state authority und tmux policy timeout.

Wichtig: `ZIELE.md` markiert "Testsuite traegt" trotz 12 roten Tests als erfuellt, weil die deklarierte Regel lautet, rote Tests nicht durch Abschwaechung zu beseitigen. Dieser Zielstatus ist daher kein globaler Health-Score.

### ZIELE.md
29 deklarierte Faehigkeitszeilen: 22 erfuellt, 6 offen, 1 zurueckgestellt. Offen sind aktuell insbesondere: vierter Clay-Dienst, MCP-Werkzeugflaeche, Entry-Point-Lernen, vollstaendige Wegehierarchie, Anbieterbahnen aus Zero-Container, Caveman->Deutsch-Uebersetzer. Gastkern-Endabnahme ist bewusst zurueckgestellt.

### agentzeroforschung/
Zentrale Forschungsablage mit Owner-Direktive, GO-Protokoll, Evidenzmodell, Messgeraeteregister, Index und bisher einer Baseline-Analyse. Diese Inventur wird als zweite Analyse dort persistiert.

## Wichtigste wissenschaftliche Befunde aus der Inventur

1. **Messreife > Verhaltensreife.** Es existieren bereits viele strukturierte Instrumente, aber der direkte Zero-Verhaltensdatensatz ist mit 5 Episoden noch sehr klein.
2. **Aktuelle Generation ohne aktuelle Verhaltensstichprobe.** Zustand/Sessions stehen auf Gen 31, beobachtete Chat-Turns nur bis Gen 29.
3. **Retrieval-Lernen ist noch empirisch null.** 5 SHADOW/UNKNOWN-Episoden, 0 Entry-Points, 0 Feedback, 0 Durable Memory.
4. **Korpus/Unterbau waechst ohne neue Zero-Turns.** Zwischen frueherem und aktuellem Export stiegen u.a. Anreicherungen und Kanten, waehrend Turn-/Episode-/Effect-Zaehler stabil blieben. Weltmodellaktivitaet und Agentenaktivitaet sind getrennte Achsen.
5. **Instrumente widersprechen sich an einigen Grenzen.** Tool-Erreichbarkeit und Kartenzaehler sind zwei konkrete Beispiele. Solche Widersprueche sind Forschungsdaten, keine Fehler, die per Interpretation glattgebuegelt werden duerfen.
6. **Bauverlauf ist ein kausaler Schatz.** 700 Commits erlauben spaeter Vorher/Nachher-Analysen von Systeminterventionen gegen Verhalten, Fehler und Performance.
7. **Graphprojektion ist nicht Vollgraph.** 5 exportierte Episode-Knoten/0 Kanten stehen neben 11.640/14.235 DB-Graphmetrik; diese Ebenen muessen getrennt bleiben.
8. **Puls ist derzeit vor allem Zustands-/Stillstands- und Unterbauinstrument.** Rolling-Tail-Zensierung und Ereignisvermischung verhindern noch naive Aktivitaetsscores.

## Naechste hochinformative Messfragen

- erster echter Gen-31-Turn und Vergleich zu Gen 29;
- erster Andreas-Turn als Cross-user-Replikation;
- warum `request_effect` empirisch erreichbar ist, aber Tool-Inventar 0 meldet;
- Kartenzaehler vs `.meta.json`-Sidecar pruefen;
- Ursache und Frequenz von `database is locked` ueber den gesamten Puls statt Stichprobe;
- 12 rote Tests als Zeitreihe verfolgen und gegen reale Zero-Episoden korrelieren;
- Entry-Point-/Feedback-Aktivierung beobachten, ohne aus 0 voreilig "funktioniert nicht" zu folgern;
- Graph-Teilprojektion gegen Vollgraph-Samplingregel spezifizieren;
- Baucommits als Interventionen mit nachfolgenden Messwerten zeitlich verbinden.

## Status

Inventurstatus: `OBSERVED_AT_SNAPSHOT` fuer Rohbestand; einzelne Ableitungen oben sind explizit als Hypothese/UNRESOLVED markiert.
