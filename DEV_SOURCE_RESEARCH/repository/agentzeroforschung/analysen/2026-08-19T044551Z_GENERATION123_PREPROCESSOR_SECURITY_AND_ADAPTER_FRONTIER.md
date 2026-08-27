# Generation 123 — Vorverarbeiter-Sicherheit und persistenter Adapter-Frontier

Zeit: 2026-08-19T04:45:51Z
Gebundener Export: `8ca36c2316693a6c1e428952131ddd59c839f201`
Generation: 123

## Kanonischer Teststand

Der exportierte Receipt `agentZero/tests/letzter-lauf.json` meldet **583 gruen / 1 rot** bei weiterhin nur abgekuerzter Source-ID `1a09c7593`.

Einziger roter Test:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

Damit ist die im unmittelbar vorausgehenden Produkt-Committext genannte Behauptung `584 Tests gruen` **nicht durable belegt**. Wie schon in Generation 116 gilt: Committext ist keine Acceptance-Quelle; der exportierte Test-Receipt bleibt die staerkere Messoberflaeche. `584/0` bekommt daher weiterhin keinen Promotion-Credit.

## Neue belastbare Produktfortschritte seit Gen116

Der aktuelle Produktstand enthaelt neue Vorverarbeiter-Haertungen:

- Caveman-Ausgabe wird explizit als Englisch erzwungen, bevor die deutsche Uebersetzung erfolgt.
- Exfiltrationswuensche nach Secrets, API-Keys, Passwoertern, Geheimdateien oder Systemprompt werden in der Vorstufe fail-closed abgewiesen.
- Der interne `NEED_BETTER_PACKAGE`-Sentinel wird nicht mehr in normale `caveman_prompt`-Texte geleakt.
- Tool-Auswahl ist an die echte Managed-Tool-Liste gebunden; erfundene Tool-Namen werden ausgefiltert statt als reale Faehigkeiten behandelt.
- Mistral-Prestage rotiert ueber drei vorhandene Tokens mit Round-Robin plus Failover fuer 429/5xx.

Diese Punkte sind Mechanismus-/Source-Fortschritt. Sie duerfen nicht mit dem noch offenen Claude-Code-Adapter-Invariant vermischt werden.

## Generation-123-Laufzeitspur

Gegenueber Generation 120 waechst die aktive Entitaet weiter:

- Gabriel-Session: 56 -> 58 Zeilen
- Causal Episodes: 61 -> 62
- Workspace Episodes: 61 -> 62
- Retrieval Episodes: 61 -> 62
- Checkpoints: 183 -> 189
- Durable-Memory-Zeilen: 80 -> 82
- zugeordnete Wissensartikel: 17708 -> 17712
- Baunotizen: 2620 -> 2624
- Produktdateien im Export: 66 -> 67

Der aktuelle Zielstand bleibt `50 erfuellt / 8 offen / 1 zurueckgestellt`.

## Wichtigste Inferenz

Der persistente Adapter-Red ist jetzt **noch staerker isoliert**: Das Produkt veraendert sich in mehreren unabhaengigen Bereichen, Generation und Laufzeitdaten wachsen, aber genau derselbe Adapter-Invariant bleibt ueber viele Generationen rot. Das spricht gegen eine breite Systemregression und fuer einen eigenstaendigen, deterministischen Boundary-Fehler oder eine systematisch falsche Testannahme innerhalb genau dieser Claude-Code-Adapter-Grenze.

Aus dem exportierten `ClaudeCodeInference` sind vier zu falsifizierende Teilinvarianten sichtbar:

1. **toolless** — `--tools ""`, `--strict-mcp-config`, `--permission-mode plan` muessen jede Werkzeugautoritaet wirklich ausschliessen.
2. **ephemeral** — `--no-session-persistence` plus UnifiedDB als alleinige Persistenzautoritaet darf keine Claude-seitige Cross-Turn-Zustandsuebernahme erlauben.
3. **structured** — Ausgabe darf nur ueber `structured_output` + `parse_claude_decision_payload` akzeptiert werden.
4. **environment isolated** — `_subprocess_env()` ist eine explizite Allowlist, behaelt aber `HOME` und mehrere `ANTHROPIC_*` Variablen bewusst fuer Subscription/OAuth. Der rote Test kann daher sehr plausibel an der **Definition von Isolation** gegen die bewusst benoetigte Credential-Admission kollidieren.

Diese vier Komponenten muessen getrennt gemessen werden. Insbesondere darf ein Test, der pauschal "keine Secrets im Environment" verlangt, nicht mit der bewusst dokumentierten Notwendigkeit kollidieren, Claude-Code-Subscription/OAuth ueber HOME bzw. ANTHROPIC-Variablen nutzbar zu halten. Umgekehrt darf HOME keine unbeabsichtigten MCP-, Session- oder Projektkonfigurationen in den Lauf einschleusen.

## Naechster hoechst-informativer Versuch

Ohne Produktpatch zuerst einen atomaren Adapter-Receipt erzeugen, der fuer genau einen isolierten Exact-Source-Ubuntu-Lauf erfasst:

- Full commit + tree
- argv exakt
- Environment **nur als Key-Liste und gehashte Werteklassen**, keine Secrets loggen
- effektive Claude-Konfigurationsquellen (HOME, Projekt-CWD, MCP-Konfigpfade)
- temporale Session-/State-Artefakte vor und nach dem Lauf
- Raw-Envelope-Digest und akzeptierter `structured_output`-Digest
- Resultat der vier Teilinvarianten getrennt

Danach denselben Test mindestens zweimal mit leerem frischem HOME und zweimal mit realem credential-tragendem HOME ausfuehren. Wenn nur das reale HOME rot wird, ist der Fehler wahrscheinlich Konfigurations-/Persistenz-Ingress. Wenn beide rot werden, die argv/Output/Environment-Unterinvarianten einzeln lokalisieren.

## Evidenzgrenzen

- `584/0`: **UNVERIFIED_TRANSIENT / NO CREDIT**
- aktueller durable Teststand: **583/1**
- Exact Source `1a09c7593`: weiterhin **UNRESOLVED**
- Whole Clay Machine: **NOT CLAIMED**
- neue ungewoehnliche Experimente in diesem Forschungszyklus: **0**
